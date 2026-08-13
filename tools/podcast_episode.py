#!/usr/bin/env python3
"""Fabrique un episode de bout en bout : voix, montage, controles, en une commande.

Enchaine les deux outils du chantier, qui restent utilisables seuls :

    voix_script.py --segments --moteur voicebox   -> les 3 segments d'intro
                                                     (+ l'outro si elle manque)
    podcast_montage.py                            -> le MP3 diffusable

Ce que cette commande N'automatise PAS, et ne peut pas automatiser :

  - la QUESTION du jour. Elle se lit dans l'article et demande un jugement :
    quelle question l'auditeur se pose vraiment, et l'article y repond-il ?
    Elle se produit avec PROMPT-INTRO-VOIX.md et se passe ici en clair.
  - le DEBAT NotebookLM. Il se pilote a l'ecran, sur le poste du cabinet
    (PROMPT-PODCAST-NOTEBOOKLM.md). Le fichier doit deja etre depose dans
    <racine>/<chaine>/brut/<slug>.mp3 — la commande le verifie AVANT de
    lancer la synthese, pour ne pas faire tourner le GPU en pure perte.

Usage :
    python3 tools/podcast_episode.py --chaine victimes --slug mon-article \\
        --question "Vous etes convoque a une expertise medicale. …?" \\
        --debut-musique 11.7

    python3 tools/podcast_episode.py --self-test
"""

import argparse
import subprocess
import sys
from pathlib import Path

RACINE_DEFAUT = "~/LEXVOX-PODCASTS"
OUTILS = Path(__file__).resolve().parent


def executer(commande, etape: str) -> int:
    """Lance une etape en laissant sa sortie s'afficher telle quelle."""
    print(f"\n=== {etape} ===", flush=True)
    print("  " + " ".join(str(m) for m in commande), flush=True)
    return subprocess.run(commande).returncode


def chemins(racine: str, chaine: str, slug: str) -> dict:
    base = Path(racine).expanduser() / chaine
    return {
        "base": base,
        "segments": base / "segments",
        "corps": base / "brut" / f"{slug}.mp3",
        "outro": base / "outro" / f"outro-{chaine}.mp3",
        "mp3": base / "mp3",
    }


def verifier_prealables(lieux: dict, slug: str) -> list:
    """Ce qui doit exister AVANT de faire tourner quoi que ce soit de couteux."""
    manques = []
    if not lieux["corps"].is_file():
        manques.append(
            f"le debat NotebookLM est absent : {lieux['corps']}\n"
            f"      Le produire avec PROMPT-PODCAST-NOTEBOOKLM.md, puis le "
            f"deposer sous ce nom exact ({slug}.mp3).")
    return manques


def fabriquer(options) -> int:
    lieux = chemins(options.racine, options.chaine, options.slug)

    manques = verifier_prealables(lieux, options.slug)
    if manques and not options.sans_montage:
        print("ARRET AVANT TOUTE SYNTHESE — il manque une source :\n")
        for manque in manques:
            print(f"  - {manque}")
        print("\nRien n'a ete genere : inutile de faire tourner le moteur de "
              "voix pour un montage qui echouera de toute facon.")
        return 2

    # --- 1. l'outro : une seule prise pour les 24 episodes de la chaine
    if not lieux["outro"].is_file():
        code = executer(
            [sys.executable, str(OUTILS / "voix_script.py"),
             "--bloc", "outro", "--chaine", options.chaine,
             "--sortie", str(lieux["outro"]),
             "--moteur", options.moteur, "--config", options.config],
            f"outro de la chaine {options.chaine} (absente — premiere prise)")
        if code != 0:
            print(f"\nECHEC a l'etape outro (code {code}).")
            return code
    else:
        print(f"\n=== outro : deja enregistree, REUTILISEE "
              f"({lieux['outro'].name}) ===")

    # --- 2. les trois segments d'intro ; seule la question est resynthetisee
    commande = [sys.executable, str(OUTILS / "voix_script.py"),
                "--chaine", options.chaine, "--slug", options.slug,
                "--question", options.question,
                "--segments", str(lieux["segments"]),
                "--moteur", options.moteur, "--config", options.config,
                "--csv", options.csv]
    if options.avocat:
        commande += ["--avocat", options.avocat]
    if options.refaire_invariants:
        commande.append("--refaire-invariants")
    code = executer(commande, "intro — 3 segments (invariants reutilises)")
    if code != 0:
        print(f"\nECHEC a l'etape intro (code {code}). Rien n'a ete monte.")
        return code

    if options.sans_montage:
        print("\nSegments produits. Montage non demande (--sans-montage).")
        return 0

    # --- 3. le montage
    commande = [sys.executable, str(OUTILS / "podcast_montage.py"),
                "--chaine", options.chaine, "--slug", options.slug,
                "--racine", options.racine,
                "--segments", str(lieux["segments"]),
                "--csv", options.csv]
    if options.debut_musique is not None:
        commande += ["--debut-musique", str(options.debut_musique)]
    if options.sans_musique:
        commande.append("--sans-musique")
    if options.json:
        commande += ["--json", options.json]
    code = executer(commande, "montage")
    if code != 0:
        print(f"\nECHEC au montage (code {code}). Les segments de voix, eux, "
              "sont conserves : relancer ne les resynthetisera pas.")
        return code

    print(f"\nEPISODE FABRIQUE — {lieux['mp3']}")
    return 0


def self_test() -> int:
    essais, echecs = 0, []

    def verifier(libelle, obtenu, attendu=True):
        nonlocal essais
        essais += 1
        if obtenu != attendu:
            echecs.append(f"{libelle} : {obtenu!r} != {attendu!r}")

    lieux = chemins("/tmp/_ep", "victimes", "mon-article")
    verifier("corps attendu au bon endroit", lieux["corps"],
             Path("/tmp/_ep/victimes/brut/mon-article.mp3"))
    verifier("outro nommee par chaine", lieux["outro"].name,
             "outro-victimes.mp3")
    verifier("segments partages par la chaine", lieux["segments"],
             Path("/tmp/_ep/victimes/segments"))
    verifier("le tilde est developpe",
             str(chemins("~/X", "famille", "s")["base"]).startswith("/"))

    # le debat manquant doit etre vu AVANT toute synthese : c'est ce qui evite
    # de faire tourner le GPU pour un montage voue a l'echec.
    verifier("debat manquant detecte",
             len(verifier_prealables(lieux, "mon-article")), 1)
    dossier = Path("/tmp/_ep/victimes/brut")
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / "mon-article.mp3").write_bytes(b"\0")
    verifier("debat present : plus rien a signaler",
             verifier_prealables(lieux, "mon-article"), [])
    (dossier / "mon-article.mp3").unlink()

    for echec in echecs:
        print(f"  !! {echec}")
    print(f"auto-test : {essais - len(echecs)}/{essais} verifications passees")
    return 1 if echecs else 0


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    analyseur.add_argument("--chaine", choices=("victimes", "famille", "permis"))
    analyseur.add_argument("--slug")
    analyseur.add_argument("--question",
                           help="l'accroche du jour (cf. PROMPT-INTRO-VOIX.md)")
    analyseur.add_argument("--avocat", help="signataire, pour la chaine permis")
    analyseur.add_argument("--racine", default=RACINE_DEFAUT)
    analyseur.add_argument("--csv", default="podcasts/queue-podcast.csv")
    analyseur.add_argument("--config", default="podcasts/voicebox.json")
    analyseur.add_argument("--moteur", choices=("aucun", "manuel", "voicebox"),
                           default="voicebox")
    analyseur.add_argument("--debut-musique", type=float,
                           help="point d'entree du generique, en secondes")
    analyseur.add_argument("--sans-musique", action="store_true")
    analyseur.add_argument("--sans-montage", action="store_true",
                           help="s'arrete apres la voix")
    analyseur.add_argument("--refaire-invariants", action="store_true",
                           help="resynthetise les blocs 2 et 3 — la signature "
                                "de la serie derive, ne le faire qu'a bon "
                                "escient")
    analyseur.add_argument("--json", help="rapport de montage en JSON")
    analyseur.add_argument("--self-test", action="store_true")
    options = analyseur.parse_args()

    if options.self_test:
        return self_test()
    for obligatoire in ("chaine", "slug", "question"):
        if not getattr(options, obligatoire):
            analyseur.error(f"--{obligatoire} est requis")
    return fabriquer(options)


if __name__ == "__main__":
    sys.exit(main())
