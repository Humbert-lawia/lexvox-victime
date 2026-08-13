#!/usr/bin/env python3
"""Moteurs d'execution ffmpeg : binaire local ou service HTTP distant.

`podcast_montage.py` ne connait que l'interface `Moteur.executer(arguments)`
qui rend (code, stdout, stderr) : toute la chaine de traitement est donc
identique, que ffmpeg tourne sur le poste ou derriere une API.

CONTRAT MINIMAL EXIGE D'UNE API FFMPEG
--------------------------------------
1. accepter une **ligne de commande ffmpeg arbitraire** (filtres compris :
   loudnorm, alimiter, concat, anullsrc) ;
2. accepter des **fichiers en entree** et rendre le **fichier produit** ;
3. **renvoyer le journal d'execution** (le flux d'erreur de ffmpeg).

Le point 3 n'est pas un confort : loudnorm en deux passes lit les mesures
que ffmpeg ecrit dans ce journal a la premiere passe pour les injecter a la
seconde. Sans journal :
  - la normalisation retombe en une seule passe (precision ~1 LU au lieu
    de 0,1) ;
  - les controles 11 (loudness) et 12 (vrai pic) deviennent invérifiables.
`MoteurAPI` le detecte et le signale au lieu d'inventer des mesures.

CONFIGURATION (podcasts/ffmpeg-api.json, jamais de secret en dur)
-----------------------------------------------------------------
{
  "nom": "nom du service",
  "base_url": "https://api.exemple.com",
  "cle_env": "FFMPEG_API_KEY",        # nom de la variable d'environnement
  "entete_auth": "Authorization",
  "prefixe_auth": "Bearer ",
  "televersement": {"chemin": "/files", "champ_fichier": "file",
                    "champ_reference": "id"},
  "soumission":    {"chemin": "/jobs", "champ_args": "args",
                    "champ_entrees": "inputs", "champ_id": "id"},
  "etat":          {"chemin": "/jobs/{id}", "champ_statut": "status",
                    "valeurs_fin": ["done"], "valeurs_echec": ["error"],
                    "champ_journal": "stderr", "champ_sortie": "output_url"},
  "delai_max_s": 900,
  "journal_disponible": true
}
"""

import json
import mimetypes
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

DELAI_SONDAGE = 3       # s entre deux interrogations d'etat
DELAI_MAX_DEFAUT = 900  # s


class ErreurMoteur(RuntimeError):
    """Panne du moteur d'execution, distincte d'une erreur de traitement."""


# --- Moteur local -------------------------------------------------------------
class MoteurLocal:
    """Appelle les binaires ffmpeg / ffprobe installes sur le poste."""

    nom = "local"
    journal_disponible = True

    def verifier(self):
        manquants = [b for b in ("ffmpeg", "ffprobe") if shutil.which(b) is None]
        if manquants:
            raise ErreurMoteur(
                f"{' et '.join(manquants)} introuvable(s) sur ce poste — "
                "installer ffmpeg, ou utiliser --moteur api")

    def executer(self, arguments):
        commande = [str(a) for a in arguments]
        resultat = subprocess.run(commande, capture_output=True, text=True)
        return resultat.returncode, resultat.stdout, resultat.stderr


# --- Moteur distant -----------------------------------------------------------
class MoteurAPI:
    """Delegue chaque commande a un service HTTP exposant ffmpeg.

    Convention de lecture des arguments, respectee par podcast_montage.py :
      - toute valeur suivant un `-i` est un fichier d'ENTREE ;
      - le dernier argument est le fichier de SORTIE (sauf `-` : pas de
        sortie a recuperer, cas des passes de mesure `-f null -`).
    """

    nom = "api"

    def __init__(self, config: dict):
        self.config = config
        self.base = config["base_url"].rstrip("/")
        self.journal_disponible = bool(config.get("journal_disponible", True))
        self.delai_max = int(config.get("delai_max_s", DELAI_MAX_DEFAUT))
        self._references = {}   # chemin local -> reference distante

        cle_env = config.get("cle_env")
        self.cle = os.environ.get(cle_env) if cle_env else None
        if cle_env and not self.cle:
            raise ErreurMoteur(
                f"variable d'environnement {cle_env} absente — la cle de "
                "l'API ne doit jamais figurer dans le depot (regle 5 du "
                "CLAUDE.md)")

    # -- transport ------------------------------------------------------------
    def _entetes(self, supplementaires=None):
        entetes = dict(supplementaires or {})
        if self.cle:
            entetes[self.config.get("entete_auth", "Authorization")] = (
                self.config.get("prefixe_auth", "Bearer ") + self.cle)
        return entetes

    def _appeler(self, chemin, donnees=None, methode=None, brut=False):
        url = chemin if chemin.startswith("http") else self.base + chemin
        corps = None
        entetes = {}
        if donnees is not None:
            corps = json.dumps(donnees).encode("utf-8")
            entetes["Content-Type"] = "application/json"
        requete = urllib.request.Request(
            url, data=corps, headers=self._entetes(entetes),
            method=methode or ("POST" if donnees is not None else "GET"))
        try:
            with urllib.request.urlopen(requete, timeout=120) as reponse:
                charge = reponse.read()
        except urllib.error.HTTPError as erreur:
            detail = erreur.read().decode("utf-8", "replace")[:300]
            raise ErreurMoteur(f"{methode or 'GET'} {url} → HTTP "
                               f"{erreur.code} : {detail}") from erreur
        except urllib.error.URLError as erreur:
            raise ErreurMoteur(f"{url} injoignable : {erreur.reason}") from erreur
        return charge if brut else json.loads(charge or b"{}")

    def _televerser(self, fichier: Path) -> str:
        """Envoie un fichier en multipart et retourne sa reference distante."""
        cle_cache = str(fichier.resolve())
        if cle_cache in self._references:
            return self._references[cle_cache]

        reglages = self.config.get("televersement", {})
        frontiere = f"----lexvox{uuid.uuid4().hex}"
        type_mime = (mimetypes.guess_type(fichier.name)[0]
                     or "application/octet-stream")
        corps = b"".join([
            f"--{frontiere}\r\n".encode(),
            f'Content-Disposition: form-data; name="'
            f'{reglages.get("champ_fichier", "file")}"; '
            f'filename="{fichier.name}"\r\n'.encode(),
            f"Content-Type: {type_mime}\r\n\r\n".encode(),
            fichier.read_bytes(),
            f"\r\n--{frontiere}--\r\n".encode(),
        ])
        requete = urllib.request.Request(
            self.base + reglages.get("chemin", "/files"), data=corps,
            headers=self._entetes(
                {"Content-Type": f"multipart/form-data; boundary={frontiere}"}),
            method="POST")
        try:
            with urllib.request.urlopen(requete, timeout=600) as reponse:
                resultat = json.loads(reponse.read() or b"{}")
        except urllib.error.HTTPError as erreur:
            detail = erreur.read().decode("utf-8", "replace")[:300]
            raise ErreurMoteur(
                f"televersement de {fichier.name} → HTTP {erreur.code} : "
                f"{detail}") from erreur
        reference = resultat.get(reglages.get("champ_reference", "id"))
        if not reference:
            raise ErreurMoteur(
                f"le service n'a pas rendu de reference pour {fichier.name} "
                f"(champ attendu : {reglages.get('champ_reference', 'id')})")
        self._references[cle_cache] = reference
        return reference

    def _recuperer(self, url: str, destination: Path):
        requete = urllib.request.Request(url, headers=self._entetes(),
                                         method="GET")
        try:
            with urllib.request.urlopen(requete, timeout=600) as reponse:
                destination.write_bytes(reponse.read())
        except urllib.error.URLError as erreur:
            raise ErreurMoteur(f"telechargement du resultat : "
                               f"{erreur}") from erreur

    # -- interface commune ----------------------------------------------------
    def verifier(self):
        self._appeler(self.config.get("etat", {}).get("chemin_sante", "/"))

    def executer(self, arguments):
        arguments = [str(a) for a in arguments]
        entrees, sortie = self._reperer_fichiers(arguments)
        sondage = Path(arguments[0]).name.startswith("ffprobe")

        traduits = list(arguments)
        references = {}
        for indice, chemin in entrees.items():
            reference = self._televerser(Path(chemin))
            references[reference] = chemin
            traduits[indice] = reference
        if sortie is not None:
            traduits[sortie] = Path(arguments[sortie]).name

        soumission = self.config.get("soumission", {})
        reponse = self._appeler(soumission.get("chemin", "/jobs"), donnees={
            soumission.get("champ_args", "args"): traduits[1:],
            soumission.get("champ_entrees", "inputs"): list(references),
        })
        identifiant = reponse.get(soumission.get("champ_id", "id"))
        if not identifiant:
            raise ErreurMoteur("le service n'a pas rendu d'identifiant de "
                               "tache a la soumission")

        etat = self._attendre(identifiant)
        reglages = self.config.get("etat", {})
        journal = etat.get(reglages.get("champ_journal", "stderr"), "") or ""
        standard = etat.get(reglages.get("champ_stdout", "stdout"), "") or ""
        if etat.get(reglages.get("champ_statut", "status")) in \
                reglages.get("valeurs_echec", ["error", "failed"]):
            return 1, standard, journal or "tache en echec, sans journal"

        if sondage:
            # ffprobe ne produit pas de fichier : son resultat est le JSON
            # ecrit sur la sortie standard.
            if not standard.strip():
                raise ErreurMoteur(
                    "le service n'a pas rendu la sortie standard de ffprobe "
                    f"(champ attendu : {reglages.get('champ_stdout', 'stdout')})"
                    " — le sondage des fichiers est impossible")
            return 0, standard, journal

        if sortie is not None:
            url_sortie = etat.get(reglages.get("champ_sortie", "output_url"))
            if not url_sortie:
                raise ErreurMoteur("tache terminee sans fichier de sortie")
            self._recuperer(url_sortie, Path(arguments[sortie]))
        return 0, "", journal

    def _attendre(self, identifiant):
        reglages = self.config.get("etat", {})
        chemin = reglages.get("chemin", "/jobs/{id}").replace("{id}",
                                                              str(identifiant))
        limite = time.monotonic() + self.delai_max
        while time.monotonic() < limite:
            etat = self._appeler(chemin)
            statut = etat.get(reglages.get("champ_statut", "status"))
            if statut in reglages.get("valeurs_fin", ["done", "completed"]):
                return etat
            if statut in reglages.get("valeurs_echec", ["error", "failed"]):
                return etat
            time.sleep(DELAI_SONDAGE)
        raise ErreurMoteur(f"tache {identifiant} toujours en cours apres "
                           f"{self.delai_max} s")

    @staticmethod
    def _reperer_fichiers(arguments):
        """-> ({indice: chemin} des entrees, indice de la sortie ou None).

        ffmpeg : les valeurs suivant `-i` sont des entrees, le dernier
        argument est la sortie (sauf `-`, cas des passes de mesure).
        ffprobe : AUCUNE sortie de fichier — le dernier argument est le
        fichier a sonder, donc une ENTREE, et le resultat part sur la
        sortie standard.
        """
        entrees = {}
        for indice, valeur in enumerate(arguments):
            if valeur == "-i" and indice + 1 < len(arguments):
                entrees[indice + 1] = arguments[indice + 1]

        dernier = len(arguments) - 1
        if Path(arguments[0]).name.startswith("ffprobe"):
            if dernier not in entrees and not arguments[dernier].startswith("-"):
                entrees[dernier] = arguments[dernier]
            return entrees, None

        sortie = None if arguments[dernier] == "-" else dernier
        if sortie in entrees:
            sortie = None
        return entrees, sortie


# --- Fabrique -----------------------------------------------------------------
def charger(nom: str, chemin_config: str = None):
    if nom == "local":
        moteur = MoteurLocal()
    elif nom == "api":
        chemin = Path(chemin_config or "podcasts/ffmpeg-api.json")
        if not chemin.is_file():
            raise ErreurMoteur(
                f"configuration d'API absente : {chemin}. La creer a partir "
                "du gabarit podcasts/ffmpeg-api.exemple.json, et exporter la "
                "cle dans la variable d'environnement qu'elle designe.")
        moteur = MoteurAPI(json.loads(chemin.read_text(encoding="utf-8")))
    else:
        raise ErreurMoteur(f"moteur inconnu : {nom}")
    return moteur


# --- Diagnostic d'un service ------------------------------------------------
def _wav_de_test(destination: Path, secondes=1, frequence=440):
    """Ecrit un WAV mono de test, sans dependance ni ffmpeg."""
    import array
    import math
    import wave

    taux = 44100
    echantillons = array.array("h", (
        int(12000 * math.sin(2 * math.pi * frequence * n / taux))
        for n in range(taux * secondes)))
    with wave.open(str(destination), "wb") as flux:
        flux.setnchannels(1)
        flux.setsampwidth(2)
        flux.setframerate(taux)
        flux.writeframes(echantillons.tobytes())


def diagnostiquer(moteur) -> int:
    """Confronte un moteur aux quatre exigences du contrat.

    A executer AVANT de monter le premier episode : il vaut mieux decouvrir
    ici qu'un service ne rend pas les journaux qu'apres 72 montages non
    verifiables.
    """
    import tempfile

    resultats = []
    with tempfile.TemporaryDirectory() as dossier:
        atelier = Path(dossier)
        source = atelier / "test-lexvox.wav"
        produit = atelier / "test-lexvox.mp3"
        _wav_de_test(source)

        # Exigence 4 — sortie standard de ffprobe
        try:
            code, standard, _ = moteur.executer(
                ["ffprobe", "-v", "error", "-print_format", "json",
                 "-show_format", "-show_streams", str(source)])
            donnees = json.loads(standard or "{}")
            ok = code == 0 and bool(donnees.get("streams"))
            detail = (f"{len(donnees.get('streams', []))} flux decrit(s)"
                      if ok else "sortie standard vide ou illisible")
        except Exception as erreur:                       # noqa: BLE001
            ok, detail = False, str(erreur)[:160]
        resultats.append(("4. sortie standard de ffprobe", ok, detail))

        # Exigence 3 — journal d'execution (mesures loudnorm)
        try:
            _, _, journal = moteur.executer(
                ["ffmpeg", "-hide_banner", "-nostats", "-i", str(source),
                 "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
                 "-f", "null", "-"])
            debut, fin = journal.rfind("{"), journal.rfind("}")
            mesures = (json.loads(journal[debut:fin + 1])
                       if debut != -1 and fin > debut else {})
            ok = "input_i" in mesures
            detail = (f"input_i = {mesures.get('input_i')} LUFS" if ok else
                      "aucune mesure loudnorm dans le journal")
        except Exception as erreur:                       # noqa: BLE001
            ok, detail = False, str(erreur)[:160]
        resultats.append(("3. journal d'execution (loudnorm 2 passes)", ok,
                          detail))

        # Exigences 1 et 2 — filtres arbitraires et fichier produit
        try:
            code, _, erreur_ff = moteur.executer(
                ["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", str(source),
                 "-af", "alimiter=limit=-1.5dB:level=disabled",
                 "-c:a", "libmp3lame", "-b:a", "192k", "-ar", "44100",
                 "-ac", "1", "-id3v2_version", "3", str(produit)])
            ok = code == 0 and produit.is_file() and produit.stat().st_size > 0
            detail = (f"{produit.stat().st_size} octets recuperes" if ok
                      else (erreur_ff or "aucun fichier produit")[:160])
        except Exception as erreur:                       # noqa: BLE001
            ok, detail = False, str(erreur)[:160]
        resultats.append(("1+2. filtres arbitraires et fichier rendu", ok,
                          detail))

    print(f"\nDiagnostic du moteur « {moteur.nom} »")
    for exigence, ok, detail in sorted(resultats):
        print(f"  [{'OK' if ok else '!!'}] {exigence} — {detail}")
    manques = [e for e, ok, _ in resultats if not ok]
    if manques:
        print("\nCe moteur ne satisfait pas le contrat : "
              + " ; ".join(manques))
        print("Sans le journal, la normalisation retombe a une passe et les "
              "controles 11 et 12 sont inverifiables — voir "
              "PROMPT-MONTAGE-DIFFUSION.md §3.")
        return 1
    print("\nContrat satisfait : ce moteur peut monter les episodes.")
    return 0


# --- Auto-test de la convention de lecture des arguments ----------------------
def self_test() -> int:
    essais, echecs = 0, []

    def verifier(libelle, obtenu, attendu):
        nonlocal essais
        essais += 1
        if obtenu != attendu:
            echecs.append(f"{libelle} : obtenu {obtenu!r}, attendu {attendu!r}")

    reperer = MoteurAPI._reperer_fichiers

    # passe de mesure : une entree, aucune sortie a recuperer (« -f null - »)
    mesure = ["ffmpeg", "-i", "a.mp3", "-af", "loudnorm", "-f", "null", "-"]
    verifier("mesure : entrees", reperer(mesure)[0], {2: "a.mp3"})
    verifier("mesure : sortie", reperer(mesure)[1], None)

    # encodage : une entree, une sortie
    encodage = ["ffmpeg", "-y", "-i", "a.wav", "-c:a", "libmp3lame", "b.mp3"]
    verifier("encodage : entrees", reperer(encodage)[0], {3: "a.wav"})
    verifier("encodage : sortie", reperer(encodage)[1], 6)

    # assemblage : trois entrees, une sortie
    assemblage = ["ffmpeg", "-i", "1.wav", "-i", "2.wav", "-i", "3.wav",
                  "-filter_complex", "concat", "out.wav"]
    verifier("assemblage : entrees", reperer(assemblage)[0],
             {2: "1.wav", 4: "2.wav", 6: "3.wav"})
    verifier("assemblage : sortie", reperer(assemblage)[1], 9)

    # ffprobe : le dernier argument est une ENTREE, jamais un fichier produit
    sondage = ["ffprobe", "-v", "error", "-show_format", "a.mp3"]
    verifier("ffprobe : fichier sonde en entree", reperer(sondage)[0],
             {4: "a.mp3"})
    verifier("ffprobe : aucune sortie", reperer(sondage)[1], None)
    verifier("ffprobe : chemin absolu", reperer(
        ["/usr/bin/ffprobe", "-v", "error", "/tmp/a.mp3"])[1], None)

    # une cle absente de l'environnement doit etre signalee, pas ignoree
    essais += 1
    os.environ.pop("_CLE_ABSENTE_TEST", None)
    try:
        MoteurAPI({"base_url": "https://x", "cle_env": "_CLE_ABSENTE_TEST"})
        echecs.append("cle manquante non detectee")
    except ErreurMoteur:
        pass

    for echec in echecs:
        print(f"  !! {echec}")
    print(f"auto-test moteur : {essais - len(echecs)}/{essais} verifications "
          "passees")
    return 1 if echecs else 0


def main() -> int:
    import argparse
    import sys

    analyseur = argparse.ArgumentParser(
        description="Auto-test de la convention, ou diagnostic d'un moteur.")
    analyseur.add_argument("--diagnostic", action="store_true",
                           help="confronte un moteur aux 4 exigences")
    analyseur.add_argument("--moteur", choices=("local", "api"),
                           default="local")
    analyseur.add_argument("--config", default="podcasts/ffmpeg-api.json")
    options = analyseur.parse_args()

    if not options.diagnostic:
        return self_test()
    try:
        moteur = charger(options.moteur, options.config)
        moteur.verifier()
        return diagnostiquer(moteur)
    except ErreurMoteur as erreur:
        print(f"moteur indisponible : {erreur}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    import sys
    sys.exit(main())
