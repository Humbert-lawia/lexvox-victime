#!/usr/bin/env python3
"""Genere le texte de l'introduction a faire lire par la voix ElevenLabs.

L'introduction est dite par Me Humbert (ou Me Raybaud pour la chaine
famille) avec sa propre voix clonee. Elle remplit trois fonctions :
  1. presenter l'emission et l'episode du jour ;
  2. presenter nommement les deux voix qui animent le debat ;
  3. ANNONCER QUE CES DEUX VOIX SONT DES VOIX DE SYNTHESE — mention de
     transparence non negociable (cf. PROMPT-MONTAGE-DIFFUSION.md §A3).

Le gabarit vit dans podcasts/intro-elevenlabs/SCRIPT-INTRO-<chaine>.md ;
seules les variables {titre} et {sujet} changent d'un episode a l'autre.

Usage :
    python3 tools/intro_script.py --chaine victimes --slug mon-article
    python3 tools/intro_script.py --chaine permis --slug x --sujet "l'alcool"
    python3 tools/intro_script.py --self-test
"""

import argparse
import csv
import re
import sys
from pathlib import Path

GABARITS = Path("podcasts/intro-elevenlabs")
MENTIONS_OBLIGATOIRES = ("voix de synthèse",)
# L'introduction doit presenter nommement les deux animateurs : c'est la
# seule chose qui relie la voix reelle de l'avocat au debat qui suit.
ANIMATEURS = ("Nathalie", "Nicolas")


def lire_ligne_csv(csv_path: Path, chaine: str, slug: str) -> dict:
    with csv_path.open(encoding="utf-8", newline="") as flux:
        for ligne in csv.DictReader(flux):
            if (ligne.get("chaine", "").strip() == chaine
                    and ligne.get("slug", "").strip() == slug):
                return ligne
    raise RuntimeError(f"aucune ligne chaine={chaine} slug={slug} "
                       f"dans {csv_path}")


def extraire_gabarit(chemin: Path) -> str:
    """Recupere le texte entre les balises <<<SCRIPT et SCRIPT>>>."""
    contenu = chemin.read_text(encoding="utf-8")
    trouve = re.search(r"<<<SCRIPT\s*(.+?)\s*SCRIPT>>>", contenu, re.S)
    if not trouve:
        raise RuntimeError(f"balises <<<SCRIPT ... SCRIPT>>> absentes de "
                           f"{chemin}")
    return trouve.group(1).strip()


def composer(gabarit: str, titre: str, sujet: str) -> str:
    texte = gabarit.replace("{titre}", titre).replace("{sujet}", sujet)
    restants = re.findall(r"\{(\w+)\}", texte)
    if restants:
        raise RuntimeError(f"variables non remplacees : {', '.join(restants)}")
    # les retours a la ligne du gabarit ne doivent pas masquer la mention
    aplati = re.sub(r"\s+", " ", texte.lower())
    manquantes = [m for m in MENTIONS_OBLIGATOIRES if m not in aplati]
    if manquantes:
        raise RuntimeError(
            "mention de transparence absente du gabarit : "
            f"{', '.join(manquantes)} — l'auditeur doit savoir que les deux "
            "voix qui animent le debat sont synthetiques")
    absents = [a for a in ANIMATEURS if a.lower() not in aplati]
    if absents:
        raise RuntimeError(
            f"animateur non presente dans l'introduction : {', '.join(absents)}"
            " — l'avocat doit nommer les deux personnes qui animent l'emission")
    return texte


def generer(options) -> int:
    gabarit = extraire_gabarit(GABARITS / f"SCRIPT-INTRO-{options.chaine}.md")
    titre = options.titre
    if titre is None:
        ligne = lire_ligne_csv(Path(options.csv), options.chaine, options.slug)
        titre = ligne.get("title") or options.slug
    texte = composer(gabarit, titre, options.sujet or titre.lower())

    print(texte)
    print(f"\n--- {len(texte)} caracteres — a coller dans ElevenLabs "
          f"(voix clonee du cabinet) ---", file=sys.stderr)
    if options.sortie:
        Path(options.sortie).write_text(texte + "\n", encoding="utf-8")
        print(f"--- ecrit dans {options.sortie} ---", file=sys.stderr)
    return 0


def self_test() -> int:
    essais, echecs = 0, []

    def verifier(libelle, condition):
        nonlocal essais
        essais += 1
        if not condition:
            echecs.append(libelle)

    gabarit = ("Bonjour, ici {titre}. Nathalie et Nicolas, deux voix de synthèse, "
               "vous parlent de {sujet}.")
    rendu = composer(gabarit, "Mon Titre", "l'indemnisation")
    verifier("substitution titre", "Mon Titre" in rendu)
    verifier("substitution sujet", "l'indemnisation" in rendu)
    verifier("aucune accolade restante", "{" not in rendu)

    for mauvais, motif in (
            ("Bonjour {titre}, avec {inconnu}.", "variable non remplacee"),
            ("Bonjour {titre}, Nathalie et Nicolas animent.",
             "mention de transparence absente"),
            ("Bonjour {titre}, deux voix de synthèse parlent de {sujet}.",
             "animateurs non nommes"),
            ("Bonjour {titre}, Nathalie, voix de synthèse, parle de {sujet}.",
             "second animateur absent")):
        essais += 1
        try:
            composer(mauvais, "T", "s")
            echecs.append(f"cas non detecte : {motif}")
        except RuntimeError:
            pass

    # les trois gabarits livres doivent passer tous les controles
    for chaine in ("victimes", "famille", "permis"):
        chemin = GABARITS / f"SCRIPT-INTRO-{chaine}.md"
        essais += 1
        try:
            texte = composer(extraire_gabarit(chemin), "Titre d'essai",
                             "un sujet d'essai")
            for prenom in ("Nathalie", "Nicolas"):
                if prenom not in texte:
                    echecs.append(f"{chaine} : prenom {prenom} absent")
                    break
        except (RuntimeError, FileNotFoundError) as erreur:
            echecs.append(f"{chaine} : {erreur}")

    for echec in echecs:
        print(f"  !! {echec}")
    print(f"auto-test : {essais - len(echecs)}/{essais} verifications passees")
    return 1 if echecs else 0


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--chaine", choices=("victimes", "famille",
                                               "permis"))
    analyseur.add_argument("--slug")
    analyseur.add_argument("--titre", help="court-circuite la lecture du CSV")
    analyseur.add_argument("--sujet", help="formulation orale du sujet")
    analyseur.add_argument("--csv", default="podcasts/queue-podcast.csv")
    analyseur.add_argument("--sortie", help="ecrit le script dans un fichier")
    analyseur.add_argument("--self-test", action="store_true")
    options = analyseur.parse_args()

    if options.self_test:
        return self_test()
    if not options.chaine or not (options.slug or options.titre):
        analyseur.error("--chaine et (--slug ou --titre) sont requis")
    try:
        return generer(options)
    except (RuntimeError, FileNotFoundError) as erreur:
        print(f"ECHEC : {erreur}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
