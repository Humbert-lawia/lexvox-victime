#!/usr/bin/env python3
"""Verifie que le poste du cabinet a tout ce qu'il faut pour fabriquer un episode.

Ecrit pour etre lance par quelqu'un qui n'est pas informaticien : chaque point
manquant est explique en francais, avec la commande exacte qui le repare. Rien
n'est installe ni modifie — cet outil regarde, il n'agit pas.

    python3 tools/poste_verifier.py
    python3 tools/poste_verifier.py --self-test
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

RACINE_DEFAUT = "~/LEXVOX-PODCASTS"
CONFIG_DEFAUT = "podcasts/voicebox.json"
REGISTRE = Path("podcasts/musique/LICENCES.md")
VOICEBOX_DEFAUT = "http://localhost:8000"


def controler(libelle, ok, detail, remede="", bloquant=True):
    return {"libelle": libelle, "ok": ok, "detail": detail, "remede": remede,
            "bloquant": bloquant}


# --- les controles ------------------------------------------------------------
def controler_python():
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    ok = sys.version_info >= (3, 8)
    return controler(
        "Python 3", ok, f"version {version}",
        "Sur Mac, installer les outils Apple : ouvrir Terminal et taper\n"
        "        xcode-select --install")


def controler_ffmpeg():
    manquants = [nom for nom in ("ffmpeg", "ffprobe") if not shutil.which(nom)]
    if not manquants:
        try:
            sortie = subprocess.run(["ffmpeg", "-version"], capture_output=True,
                                    text=True, timeout=20).stdout.splitlines()
            detail = sortie[0][:60] if sortie else "present"
        except (OSError, subprocess.SubprocessError):
            detail = "present"
        return controler("ffmpeg et ffprobe", True, detail)
    return controler(
        "ffmpeg et ffprobe", False, f"manque : {', '.join(manquants)}",
        "C'est le logiciel qui assemble l'audio. Deux facons :\n"
        "        brew install ffmpeg          (si Homebrew est installe)\n"
        "        python3 -m pip install ffmpeg-binaries   (sinon)")


def controler_voicebox(base: str):
    url = f"{base.rstrip('/')}/openapi.json"
    try:
        requete = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(requete, timeout=10) as reponse:
            schema = json.loads(reponse.read().decode("utf-8", "replace"))
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as erreur:
        motif = getattr(erreur, "reason", erreur)
        return [controler(
            "Voicebox repond", False, f"{base} injoignable ({motif})",
            "Lancer l'application Voicebox et verifier que son serveur est\n"
            "        demarre. C'est elle qui porte la voix clonee.")]

    points = [controler("Voicebox repond", True, base)]
    chemins = set(schema.get("paths", {}))
    for route in ("/generate", "/profiles"):
        points.append(controler(f"route {route}", route in chemins,
                                "presente" if route in chemins else "absente",
                                "Version de Voicebox trop ancienne ou serveur "
                                "partiel."))
    # la question du francais, tranchee par le schema de CETTE instance
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from voix_moteur import lire_contraintes, langue_acceptee
        limites = lire_contraintes(schema)
        accepte = langue_acceptee("fr", limites)
        points.append(controler(
            "le francais est accepte", accepte, limites.get("langue_detail", "?"),
            "L'instance n'accepte pas « fr ». Choisir dans Voicebox un moteur\n"
            "        multilingue (Chatterbox Multilingual, LuxTTS) — le corpus\n"
            "        du cabinet est en francais."))
    except ImportError:
        pass
    return points


def controler_config(chemin: str):
    fichier = Path(chemin)
    if not fichier.is_file():
        return [controler(
            "configuration Voicebox", False, f"{fichier} absent",
            f"Copier le modele puis y coller les identifiants de voix :\n"
            f"        cp podcasts/voicebox.exemple.json {fichier}\n"
            f"        python3 tools/voix_moteur.py --diagnostic")]
    try:
        config = json.loads(fichier.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erreur:
        return [controler("configuration Voicebox", False,
                          f"{fichier} : JSON invalide — {erreur}",
                          "Une virgule ou un guillemet de trop.")]
    profils = {c: p for c, p in (config.get("profils") or {}).items() if p}
    return [
        controler("configuration Voicebox", True, str(fichier)),
        controler(
            "profil de voix pour « victimes »", bool(profils.get("victimes")),
            profils.get("victimes") or "non renseigne",
            "Lancer « python3 tools/voix_moteur.py --diagnostic » : il liste\n"
            "        les voix de l'instance. Coller l'identifiant de la voix\n"
            "        clonee de Me Humbert dans le champ profils.victimes."),
    ]


def controler_musique(racine: Path):
    candidats = [racine / "musique" / "musique-lexvox.mp3",
                 racine / "victimes" / "musique" / "musique-victimes.mp3"]
    trouve = next((c for c in candidats if c.is_file()), None)
    points = [controler(
        "generique musical depose", bool(trouve),
        str(trouve) if trouve else f"attendu : {candidats[0]}",
        f"Deposer la piste Pixabay « Intro YouTube » sous ce nom exact :\n"
        f"        {candidats[0]}")]
    if trouve:
        registre = REGISTRE.read_text(encoding="utf-8") if REGISTRE.is_file() else ""
        inscrit = trouve.stem in registre
        points.append(controler(
            "licence consignee au registre", inscrit,
            f"{trouve.stem} dans {REGISTRE}" if inscrit
            else f"{trouve.stem} absent de {REGISTRE}",
            "Le montage refuse de tourner sans preuve de licence archivee."))
    return points


def controler_arborescence(racine: Path):
    attendus = {
        "victimes/brut": "le debat NotebookLM de chaque episode",
        "victimes/segments": "les 3 segments d'intro (crees automatiquement)",
        "victimes/outro": "l'outro, une seule prise pour la chaine",
        "musique": "le generique musical",
    }
    points = []
    for relatif, role in attendus.items():
        dossier = racine / relatif
        points.append(controler(
            f"dossier {relatif}", dossier.is_dir(), role,
            f"mkdir -p {dossier}", bloquant=False))
    return points


# --- affichage ----------------------------------------------------------------
def rapporter(points) -> int:
    print("=== VERIFICATION DU POSTE ===\n")
    manquants = [p for p in points if not p["ok"]]
    for point in points:
        marque = "OK" if point["ok"] else "!!"
        print(f"   [{marque}] {point['libelle']} — {point['detail']}")

    bloquants = [p for p in manquants if p["bloquant"]]
    if not manquants:
        print("\nTOUT EST EN PLACE. Un episode peut se fabriquer :\n")
        print("   python3 tools/podcast_episode.py --chaine victimes \\")
        print("       --slug <slug> --question \"…?\" --debut-musique 11.7")
        return 0

    print(f"\n--- {len(manquants)} point(s) a regler ---\n")
    for point in manquants:
        urgence = "A REGLER" if point["bloquant"] else "facultatif"
        print(f"  [{urgence}] {point['libelle']}")
        if point["remede"]:
            print(f"        {point['remede']}")
        print()
    return 3 if bloquants else 0


def verifier(options) -> int:
    racine = Path(options.racine).expanduser()
    points = [controler_python(), controler_ffmpeg()]
    points += controler_voicebox(options.voicebox)
    points += controler_config(options.config)
    points += controler_musique(racine)
    points += controler_arborescence(racine)
    return rapporter(points)


# --- auto-test ----------------------------------------------------------------
def self_test() -> int:
    essais, echecs = 0, []

    def verif(libelle, obtenu, attendu=True):
        nonlocal essais
        essais += 1
        if obtenu != attendu:
            echecs.append(f"{libelle} : {obtenu!r} != {attendu!r}")

    verif("python courant accepte", controler_python()["ok"])

    bac = Path("/tmp/_poste_selftest")
    shutil.rmtree(bac, ignore_errors=True)
    bac.mkdir(parents=True)

    # configuration absente, puis vide, puis renseignee
    verif("config absente detectee",
          controler_config(str(bac / "rien.json"))[0]["ok"], False)
    (bac / "vide.json").write_text('{"profils": {"victimes": ""}}',
                                   encoding="utf-8")
    points = controler_config(str(bac / "vide.json"))
    verif("config presente reconnue", points[0]["ok"])
    verif("profil vide detecte", points[1]["ok"], False)
    (bac / "pleine.json").write_text('{"profils": {"victimes": "prof-1"}}',
                                     encoding="utf-8")
    verif("profil renseigne reconnu",
          controler_config(str(bac / "pleine.json"))[1]["ok"])
    (bac / "casse.json").write_text("{ceci n'est pas du json", encoding="utf-8")
    verif("json casse detecte",
          controler_config(str(bac / "casse.json"))[0]["ok"], False)

    # musique absente puis presente
    verif("musique absente detectee",
          controler_musique(bac)[0]["ok"], False)
    (bac / "musique").mkdir(parents=True, exist_ok=True)
    (bac / "musique" / "musique-lexvox.mp3").write_bytes(b"\0" * 16)
    points = controler_musique(bac)
    verif("musique trouvee", points[0]["ok"])
    verif("licence verifiee dans la foulee", len(points), 2)

    # Voicebox injoignable : un port ou rien n'ecoute
    points = controler_voicebox("http://127.0.0.1:9")
    verif("voicebox injoignable detecte", points[0]["ok"], False)
    verif("un seul point quand le serveur ne repond pas", len(points), 1)

    # arborescence : facultative, jamais bloquante
    verif("dossiers manquants non bloquants",
          all(not p["bloquant"] for p in controler_arborescence(bac)))

    shutil.rmtree(bac, ignore_errors=True)
    for echec in echecs:
        print(f"  !! {echec}")
    print(f"auto-test : {essais - len(echecs)}/{essais} verifications passees")
    return 1 if echecs else 0


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analyseur.add_argument("--racine", default=RACINE_DEFAUT)
    analyseur.add_argument("--config", default=CONFIG_DEFAUT)
    analyseur.add_argument("--voicebox", default=VOICEBOX_DEFAUT)
    analyseur.add_argument("--self-test", action="store_true")
    options = analyseur.parse_args()
    return self_test() if options.self_test else verifier(options)


if __name__ == "__main__":
    sys.exit(main())
