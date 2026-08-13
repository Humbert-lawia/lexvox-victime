#!/usr/bin/env python3
"""Genere les textes dits par la voix clonee de l'avocat dans ElevenLabs.

Deux blocs encadrent le debat NotebookLM :

  INTRO  (par episode) — presente l'emission et le sujet du jour, nomme les
         deux animateurs, et ANNONCE QUE CE SONT DES VOIX DE SYNTHESE :
         mention de transparence non negociable, sans quoi l'auditeur peut
         croire qu'il ecoute des avocats du cabinet.

  OUTRO  (fixe par chaine) — porte l'APPEL A L'ACTION, dit par l'avocat
         lui-meme. Il ne depend pas de l'episode : une seule generation
         ElevenLabs sert les 24 episodes d'une chaine. Depuis qu'il existe,
         le debat NotebookLM ne doit plus reciter de conclusion commerciale,
         sous peine de la dire deux fois.

Gabarits : podcasts/voix-elevenlabs/SCRIPT-{INTRO,OUTRO}-<chaine>.md.
Seul l'intro porte les variables {titre} et {sujet}.

Usage :
    python3 tools/voix_script.py --chaine victimes --slug mon-article
    python3 tools/voix_script.py --bloc outro --chaine victimes
    python3 tools/voix_script.py --self-test
"""

import argparse
import csv
import re
import sys
from pathlib import Path

GABARITS = Path("podcasts/voix-elevenlabs")

# L'introduction doit presenter nommement les deux animateurs et dire qu'ils
# sont synthetiques : c'est ce qui relie la voix reelle de l'avocat au debat
# qui suit, et ce qui evite de laisser croire a des avocats du cabinet.
EXIGENCES = {
    "intro": {"mentions": ("voix de synthèse",),
              "noms": ("Nathalie", "Nicolas")},
    "outro": {"mentions": (), "noms": ()},
}

# Publicite personnelle de l'avocat : RIN art. 10.2 (sincere et veridique,
# sans mention comparative) et art. 10 de la loi n° 71-1130 (interdiction du
# pacte de quota litis). Ces formulations ne doivent jamais sortir a l'oral.
FORMULES_INTERDITES = (
    "résultat garanti", "garantie de résultat", "nous garantissons",
    "je garantis", "vous obtiendrez", "sans aucun risque",
    "meilleur avocat", "le plus performant",
)


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


def composer(gabarit: str, titre: str, sujet: str, bloc: str = "intro") -> str:
    texte = gabarit.replace("{titre}", titre).replace("{sujet}", sujet)
    restants = re.findall(r"\{(\w+)\}", texte)
    if restants:
        raise RuntimeError(f"variables non remplacees : {', '.join(restants)}")
    # les retours a la ligne du gabarit ne doivent pas masquer la mention
    aplati = re.sub(r"\s+", " ", texte.lower())
    exigences = EXIGENCES[bloc]
    manquantes = [m for m in exigences["mentions"] if m not in aplati]
    if manquantes:
        raise RuntimeError(
            "mention de transparence absente du gabarit : "
            f"{', '.join(manquantes)} — l'auditeur doit savoir que les deux "
            "voix qui animent le debat sont synthetiques")
    absents = [a for a in exigences["noms"] if a.lower() not in aplati]
    if absents:
        raise RuntimeError(
            f"animateur non presente dans l'introduction : {', '.join(absents)}"
            " — l'avocat doit nommer les deux personnes qui animent l'emission")
    interdites = [f for f in FORMULES_INTERDITES if f in aplati]
    if interdites:
        raise RuntimeError(
            f"formulation interdite dans le script : {', '.join(interdites)}"
            " — publicite personnelle de l'avocat, RIN art. 10.2 et art. 10 "
            "de la loi n° 71-1130")
    return texte


def generer(options) -> int:
    bloc = options.bloc
    gabarit = extraire_gabarit(
        GABARITS / f"SCRIPT-{bloc.upper()}-{options.chaine}.md")

    titre, sujet = options.titre, options.sujet
    if bloc == "intro":
        if titre is None:
            ligne = lire_ligne_csv(Path(options.csv), options.chaine,
                                   options.slug)
            titre = ligne.get("title") or options.slug
        sujet = sujet or titre.lower()
    else:
        # l'outro est fixe par chaine : aucune variable d'episode
        titre, sujet = titre or "", sujet or ""
    texte = composer(gabarit, titre, sujet, bloc)

    print(texte)
    rappel = ("" if bloc == "intro" else
              " — fixe pour toute la chaine, une seule generation suffit")
    print(f"\n--- {len(texte)} caracteres — a coller dans ElevenLabs "
          f"(voix clonee du cabinet){rappel} ---", file=sys.stderr)
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

    # une garantie de resultat doit etre refusee dans les deux blocs
    for interdit in ("Résultat garanti pour votre dossier.",
                     "Nous garantissons une indemnisation."):
        essais += 1
        try:
            composer(interdit, "T", "s", "outro")
            echecs.append(f"formulation interdite acceptee : {interdit}")
        except RuntimeError:
            pass

    # les six gabarits livres doivent passer tous les controles de leur bloc
    for bloc in ("intro", "outro"):
        for chaine in ("victimes", "famille", "permis"):
            chemin = GABARITS / f"SCRIPT-{bloc.upper()}-{chaine}.md"
            essais += 1
            try:
                texte = composer(extraire_gabarit(chemin), "Titre d'essai",
                                 "un sujet d'essai", bloc)
                if bloc == "intro":
                    for prenom in ("Nathalie", "Nicolas"):
                        if prenom not in texte:
                            echecs.append(f"{chaine} : prenom {prenom} absent")
                            break
                elif "04 90 54 58 10" in texte:
                    echecs.append(
                        f"{chaine} : numero en chiffres dans l'outro — "
                        "l'ecrire en toutes lettres pour la synthese vocale")
            except (RuntimeError, FileNotFoundError) as erreur:
                echecs.append(f"{bloc}/{chaine} : {erreur}")

    for echec in echecs:
        print(f"  !! {echec}")
    print(f"auto-test : {essais - len(echecs)}/{essais} verifications passees")
    return 1 if echecs else 0


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--bloc", choices=("intro", "outro"),
                           default="intro",
                           help="intro (par episode) ou outro (fixe par chaine)")
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
    if not options.chaine:
        analyseur.error("--chaine est requis")
    if options.bloc == "intro" and not (options.slug or options.titre):
        analyseur.error("pour une intro, --slug ou --titre est requis "
                        "(l'outro, lui, ne depend pas de l'episode)")
    try:
        return generer(options)
    except (RuntimeError, FileNotFoundError) as erreur:
        print(f"ECHEC : {erreur}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
