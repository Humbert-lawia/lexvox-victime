#!/usr/bin/env python3
"""Synthese vocale LOCALE via Voicebox — remplace ElevenLabs.

Voicebox (voicebox.sh) est une application libre qui tourne sur le poste du
cabinet et expose une API REST locale. Trois consequences qui comptent ici :
aucun texte ne sort de la machine, aucun abonnement, aucun quota de
caracteres. Pour un cabinet d'avocats, le premier point n'est pas un detail.

Contrat utilise (docs.voicebox.sh) :
    POST /generate   {profile_id, text, language, seed, engine, model_size,
                      max_chunk_chars, instruct} -> {id, audio_path, duration}
    GET  /audio/{id} -> le fichier audio
    GET  /profiles   -> les profils de voix, dont la voix clonee de l'avocat
    GET  /openapi.json -> le schema REEL de l'instance installee

⚠️ Piege documente : la page publique de /generate annonce
« language: ^(en|zh)$ » alors que l'application revendique 23 langues et
embarque des moteurs multilingues (Chatterbox Multilingual, LuxTTS). La
verite est dans le /openapi.json de VOTRE instance, pas dans la doc du site.
`--diagnostic` la lit et refuse d'aller plus loin si le francais n'est pas
accepte : mieux vaut le savoir avant d'avoir monte 72 episodes.

Deux moteurs, une seule interface — meme principe que ffmpeg_moteur.py :

    MoteurVoicebox : parle a l'API locale, rend un fichier audio.
    MoteurManuel   : n'appelle rien, ecrit le .txt a coller dans l'interface
                     graphique. C'est le repli si l'API n'est pas joignable,
                     et le mode par defaut tant que les profils ne sont pas
                     renseignes.

Usage :
    python3 tools/voix_moteur.py --diagnostic
    python3 tools/voix_moteur.py --self-test
"""

import argparse
import json
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CONFIG_DEFAUT = "podcasts/voicebox.json"

# Moteurs livres avec Voicebox (docs.voicebox.sh/developer/tts-generation).
# Seuls les multilingues nous interessent : le corpus est en francais.
MOTEURS_TTS = ("qwen", "qwen_custom_voice", "luxtts", "chatterbox",
               "chatterbox_turbo", "tada", "kokoro")
MOTEURS_MULTILINGUES = ("chatterbox", "luxtts", "qwen_custom_voice", "qwen")

# /generate refuse un texte de plus de 5000 caracteres. Nos segments font
# quelques centaines de caracteres : la marge est confortable, mais un
# gabarit modifie sans precaution pourrait la franchir.
TEXTE_MAX = 5000

# Au-dela de max_chunk_chars, Voicebox decoupe le texte et RACCORDE les
# morceaux par un fondu. Sur une signature sonore, ce raccord s'entend. Nos
# segments etant courts, on releve simplement le seuil pour qu'aucun segment
# ne soit jamais coupe.
CHUNK_DEFAUT = 1200


class ErreurVoix(RuntimeError):
    """Panne de synthese : configuration, reseau ou refus de l'API."""


def _http(url: str, donnees=None, timeout=600, brut=False):
    """Appel HTTP minimal (bibliotheque standard, aucune dependance)."""
    corps = None
    entetes = {"Accept": "application/json"}
    if donnees is not None:
        corps = json.dumps(donnees).encode("utf-8")
        entetes["Content-Type"] = "application/json"
    requete = urllib.request.Request(url, data=corps, headers=entetes,
                                     method="POST" if corps else "GET")
    try:
        with urllib.request.urlopen(requete, timeout=timeout) as reponse:
            charge = reponse.read()
    except urllib.error.HTTPError as erreur:
        detail = erreur.read().decode("utf-8", "replace")[:400]
        raise ErreurVoix(f"{url} -> HTTP {erreur.code} : {detail}") from erreur
    except urllib.error.URLError as erreur:
        raise ErreurVoix(
            f"{url} injoignable ({erreur.reason}). Voicebox est-il lance sur "
            "ce poste, et le serveur demarre ?") from erreur
    if brut:
        return charge
    try:
        return json.loads(charge.decode("utf-8", "replace"))
    except json.JSONDecodeError as erreur:
        raise ErreurVoix(f"{url} : reponse non JSON") from erreur


def charger_config(chemin: str) -> dict:
    fichier = Path(chemin)
    if not fichier.is_file():
        raise ErreurVoix(
            f"configuration absente : {fichier}. Copier "
            "podcasts/voicebox.exemple.json et y mettre les identifiants de "
            "profil rendus par « python3 tools/voix_moteur.py --diagnostic ».")
    try:
        return json.loads(fichier.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erreur:
        raise ErreurVoix(f"{fichier} : JSON invalide — {erreur}") from erreur


class MoteurManuel:
    """Aucun appel : ecrit le texte a coller dans l'interface Voicebox."""

    nom = "manuel"
    automatique = False

    def __init__(self, config=None):
        self.config = config or {}

    def verifier(self):
        return True

    def synthetiser(self, texte: str, sortie: Path, chaine: str,
                    segment: str = "") -> dict:
        cible = sortie.with_suffix(".txt")
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(texte + "\n", encoding="utf-8")
        return {"mode": "manuel", "texte": str(cible), "audio": None,
                "consigne": f"coller {cible.name} dans Voicebox, voix clonee "
                            f"de la chaine {chaine}, puis enregistrer sous "
                            f"{sortie.name}"}


class MoteurVoicebox:
    """Synthese par l'API REST locale de Voicebox."""

    nom = "voicebox"
    automatique = True

    def __init__(self, config: dict):
        self.config = config
        self.base = str(config.get("base_url", "http://localhost:8000")).rstrip("/")
        self.profils = config.get("profils", {}) or {}
        self.moteur = config.get("engine", "chatterbox")
        self.langue = config.get("language", "fr")
        self.taille = config.get("model_size")
        self.chunk = int(config.get("max_chunk_chars", CHUNK_DEFAUT))
        self.instruct = config.get("instruct") or ""
        self.graines = config.get("graines", {}) or {}
        self.delai = int(config.get("timeout_s", 600))

    # -- verifications ---------------------------------------------------
    def verifier(self):
        if self.moteur not in MOTEURS_TTS:
            raise ErreurVoix(
                f"moteur « {self.moteur} » inconnu de Voicebox. Choisir parmi "
                f"{', '.join(MOTEURS_TTS)}.")
        if not self.profils:
            raise ErreurVoix(
                "aucun profil de voix configure. Lancer « --diagnostic » pour "
                "lister les profils de votre instance, puis renseigner leur "
                "identifiant par chaine dans la configuration.")
        _http(f"{self.base}/profiles", timeout=30)
        return True

    def profil_de(self, chaine: str) -> str:
        profil = self.profils.get(chaine)
        if not profil:
            raise ErreurVoix(
                f"aucun profil de voix pour la chaine « {chaine} ». La voix "
                "qui parle doit etre celle de l'avocat qui signe les articles "
                "de cette chaine — ne pas prendre celle d'une autre.")
        return profil

    # -- synthese --------------------------------------------------------
    def synthetiser(self, texte: str, sortie: Path, chaine: str,
                    segment: str = "") -> dict:
        if not texte.strip():
            raise ErreurVoix("texte vide")
        if len(texte) > TEXTE_MAX:
            raise ErreurVoix(
                f"texte de {len(texte)} caracteres : /generate refuse au-dela "
                f"de {TEXTE_MAX}. Decouper en segments.")

        demande = {
            "profile_id": self.profil_de(chaine),
            "text": texte,
            "language": self.langue,
            "max_chunk_chars": max(self.chunk, len(texte) + 1),
        }
        if self.moteur:
            demande["engine"] = self.moteur
        if self.taille:
            demande["model_size"] = self.taille
        if self.instruct:
            demande["instruct"] = self.instruct
        # Une graine fixe rend la prise REPRODUCTIBLE : c'est ce qui permet de
        # refabriquer a l'identique un bloc invariant (jingle, relance) si le
        # fichier est perdu, sans que la signature de la serie ne derive.
        graine = self.graines.get(segment, self.graines.get("defaut"))
        if graine is not None:
            demande["seed"] = int(graine)

        reponse = _http(f"{self.base}/generate", donnees=demande,
                        timeout=self.delai)
        identifiant = reponse.get("id")
        if not identifiant:
            raise ErreurVoix(f"/generate n'a pas rendu d'identifiant : "
                             f"{str(reponse)[:200]}")

        sortie.parent.mkdir(parents=True, exist_ok=True)
        audio = _http(f"{self.base}/audio/{urllib.parse.quote(str(identifiant))}",
                      timeout=self.delai, brut=True)
        if len(audio) < 1024:
            raise ErreurVoix(
                f"audio rendu par /audio/{identifiant} suspect "
                f"({len(audio)} octets) — generation probablement echouee")
        sortie.write_bytes(audio)
        return {"mode": "voicebox", "audio": str(sortie),
                "id": identifiant, "duree_s": reponse.get("duration"),
                "graine": demande.get("seed"),
                "moteur": self.moteur, "langue": self.langue}


def charger(nom: str, chemin_config: str = CONFIG_DEFAUT):
    if nom == "manuel":
        return MoteurManuel()
    if nom == "voicebox":
        return MoteurVoicebox(charger_config(chemin_config))
    raise ErreurVoix(f"moteur de voix inconnu : {nom}")


# --- Diagnostic ---------------------------------------------------------------
def _langues_acceptees(schema: dict):
    """Extrait du schema OpenAPI la contrainte reelle sur `language`."""
    composants = schema.get("components", {}).get("schemas", {})
    for nom, corps in composants.items():
        if "generation" not in nom.lower() and "request" not in nom.lower():
            continue
        champ = (corps.get("properties", {}) or {}).get("language")
        if not champ:
            continue
        for cle in ("pattern", "enum"):
            if cle in champ:
                return nom, cle, champ[cle]
        for variante in champ.get("anyOf", []) or []:
            for cle in ("pattern", "enum"):
                if cle in variante:
                    return nom, cle, variante[cle]
        return nom, "libre", None
    return None, None, None


def diagnostiquer(chemin_config: str) -> int:
    """Confronte l'instance Voicebox installee aux besoins du projet."""
    print("=== DIAGNOSTIC VOICEBOX ===\n")
    try:
        config = charger_config(chemin_config)
    except ErreurVoix as erreur:
        print(f"[!!] {erreur}")
        config = {}
    base = str(config.get("base_url", "http://localhost:8000")).rstrip("/")
    print(f"instance : {base}\n")

    constats, bloquants = [], []

    def point(libelle, ok, detail, bloquant=False):
        constats.append((libelle, ok, detail))
        if not ok and bloquant:
            bloquants.append(libelle)

    try:
        schema = _http(f"{base}/openapi.json", timeout=30)
        point("serveur joignable", True, base)
    except ErreurVoix as erreur:
        point("serveur joignable", False, str(erreur)[:200], bloquant=True)
        schema = None

    if schema:
        chemins = set(schema.get("paths", {}))
        for route in ("/generate", "/profiles"):
            point(f"route {route} exposee", route in chemins,
                  "presente" if route in chemins else "absente", bloquant=True)
        audio = [c for c in chemins if c.startswith("/audio/")]
        point("route /audio/{id} exposee", bool(audio),
              audio[0] if audio else "absente", bloquant=True)

        nom, forme, valeur = _langues_acceptees(schema)
        langue = config.get("language", "fr")
        if forme == "pattern":
            import re as _re
            accepte = bool(_re.match(valeur, langue))
            point(f"langue « {langue} » acceptee par {nom}", accepte,
                  f"contrainte {valeur}", bloquant=True)
        elif forme == "enum":
            accepte = langue in valeur
            point(f"langue « {langue} » acceptee par {nom}", accepte,
                  f"valeurs {valeur}", bloquant=True)
        elif forme == "libre":
            point(f"langue « {langue} »", True,
                  "aucune contrainte declaree dans le schema")
        else:
            point("contrainte de langue lisible", False,
                  "champ `language` introuvable dans le schema")

    try:
        profils = _http(f"{base}/profiles", timeout=30)
        liste = profils if isinstance(profils, list) else profils.get("profiles", [])
        point("profils de voix disponibles", bool(liste),
              f"{len(liste)} profil(s)", bloquant=True)
        if liste:
            print("Profils declares sur cette instance :")
            for profil in liste:
                if isinstance(profil, dict):
                    print(f"   - {profil.get('id', '?')}  "
                          f"{profil.get('name', '(sans nom)')}")
            print()
        declares = {c: p for c, p in (config.get("profils") or {}).items() if p}
        connus = {p.get("id") for p in liste if isinstance(p, dict)}
        for chaine, identifiant in declares.items():
            point(f"profil de la chaine {chaine} reconnu",
                  identifiant in connus, identifiant, bloquant=True)
        if not declares:
            point("profils renseignes dans la configuration", False,
                  "aucun — recopier ci-dessus l'identifiant de la voix clonee",
                  bloquant=True)
    except ErreurVoix as erreur:
        point("profils de voix disponibles", False, str(erreur)[:200],
              bloquant=True)

    moteur = config.get("engine", "chatterbox")
    point("moteur multilingue", moteur in MOTEURS_MULTILINGUES,
          f"{moteur} — le corpus est en francais, un moteur anglophone "
          "prononcerait mal les noms propres" if moteur not in
          MOTEURS_MULTILINGUES else moteur)

    for libelle, ok, detail in constats:
        print(f"   [{'OK' if ok else '!!'}] {libelle} — {detail}")

    if bloquants:
        print("\nDIAGNOSTIC : INSTANCE INUTILISABLE EN L'ETAT")
        for libelle in bloquants:
            print(f"  bloquant : {libelle}")
        print("\nRepli disponible sans rien installer : --moteur manuel, qui "
              "ecrit les textes a coller dans l'interface graphique.")
        return 3
    print("\nDIAGNOSTIC : INSTANCE CONFORME — synthese automatique possible.")
    return 0


# --- Auto-test ----------------------------------------------------------------
def self_test() -> int:
    essais, echecs = 0, []

    def verifier(libelle, condition):
        nonlocal essais
        essais += 1
        if not condition:
            echecs.append(libelle)

    # lecture du schema OpenAPI : les trois formes rencontrees
    verifier("pattern lu", _langues_acceptees(
        {"components": {"schemas": {"GenerationRequest": {"properties": {
            "language": {"pattern": "^(en|zh)$"}}}}}})[2] == "^(en|zh)$")
    verifier("enum lu", _langues_acceptees(
        {"components": {"schemas": {"GenerationRequest": {"properties": {
            "language": {"enum": ["en", "fr"]}}}}}})[2] == ["en", "fr"])
    verifier("anyOf lu", _langues_acceptees(
        {"components": {"schemas": {"GenerationRequest": {"properties": {
            "language": {"anyOf": [{"type": "null"},
                                   {"enum": ["fr"]}]}}}}}})[2] == ["fr"])
    verifier("schema muet", _langues_acceptees({"components": {}})[0] is None)

    # le moteur manuel doit ecrire un .txt et ne rien appeler
    dossier = Path("/tmp/_voix_selftest")
    shutil.rmtree(dossier, ignore_errors=True)
    resultat = MoteurManuel().synthetiser("Bonjour.", dossier / "intro.mp3",
                                          "victimes", "question")
    verifier("moteur manuel ecrit le texte",
             (dossier / "intro.txt").read_text(encoding="utf-8").strip()
             == "Bonjour.")
    verifier("moteur manuel n'invente pas d'audio", resultat["audio"] is None)
    shutil.rmtree(dossier, ignore_errors=True)

    # garde-fous de MoteurVoicebox, sans reseau
    moteur = MoteurVoicebox({"profils": {"victimes": "abc"},
                             "engine": "chatterbox", "language": "fr"})
    verifier("profil resolu", moteur.profil_de("victimes") == "abc")
    for cas, appel in (
            ("chaine sans profil", lambda: moteur.profil_de("permis")),
            ("texte vide", lambda: moteur.synthetiser("  ", Path("/tmp/x.mp3"),
                                                      "victimes")),
            ("texte trop long", lambda: moteur.synthetiser(
                "a" * (TEXTE_MAX + 1), Path("/tmp/x.mp3"), "victimes"))):
        essais += 1
        try:
            appel()
            echecs.append(f"cas non detecte : {cas}")
        except ErreurVoix:
            pass

    essais += 1
    try:
        MoteurVoicebox({"profils": {"victimes": "a"}, "engine": "inexistant"}).verifier()
        echecs.append("moteur TTS inconnu accepte")
    except ErreurVoix:
        pass

    essais += 1
    try:
        MoteurVoicebox({"engine": "chatterbox"}).verifier()
        echecs.append("absence de profil non detectee")
    except ErreurVoix:
        pass

    verifier("moteur manuel disponible sans configuration",
             charger("manuel").nom == "manuel")

    for echec in echecs:
        print(f"  !! {echec}")
    print(f"auto-test : {essais - len(echecs)}/{essais} verifications passees")
    return 1 if echecs else 0


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analyseur.add_argument("--config", default=CONFIG_DEFAUT)
    analyseur.add_argument("--diagnostic", action="store_true",
                           help="confronte l'instance Voicebox aux besoins")
    analyseur.add_argument("--self-test", action="store_true")
    options = analyseur.parse_args()

    if options.self_test:
        return self_test()
    if options.diagnostic:
        return diagnostiquer(options.config)
    analyseur.error("choisir --diagnostic ou --self-test")


if __name__ == "__main__":
    sys.exit(main())
