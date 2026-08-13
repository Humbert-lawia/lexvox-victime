#!/usr/bin/env python3
"""Genere les textes dits par la voix clonee de l'avocat (Voicebox, en local).

Deux blocs encadrent le debat NotebookLM :

  INTRO  (par episode) — structure imposee, marque de fabrique de la serie :
         (1) une QUESTION d'accroche dont la reponse est l'article du jour,
         (2) le JINGLE verbal, identique dans tous les episodes de la chaine,
         (3) le sujet et l'article dont il est tire,
         (4) la presentation de Nathalie et Nicolas, puis la relance.
         La question se produit avec PROMPT-INTRO-VOIX.md.

  OUTRO  (fixe par chaine) — porte l'APPEL A L'ACTION, dit par l'avocat
         lui-meme. Il ne depend pas de l'episode : une seule prise sert les
         24 episodes d'une chaine. Depuis qu'il existe, le debat NotebookLM
         ne doit plus reciter de conclusion commerciale.

SEGMENTS — deux des quatre blocs de l'intro sont RIGOUREUSEMENT identiques
d'un episode a l'autre. Les resynthetiser a chaque fois les fait deriver
legerement et la signature de la serie s'emousse. `--segments` decoupe donc
l'intro en morceaux : les invariants se generent UNE fois par chaine et se
reutilisent, seuls « question » et « sujet » sont refaits chaque semaine.
Effet de bord utile : aucun segment n'atteint le seuil de decoupage de
Voicebox, donc aucun raccord audible a l'interieur d'une phrase.

Usage :
    python3 tools/voix_script.py --chaine victimes --slug mon-article \\
        --question "Pouvez-vous refuser la contre-visite ?"
    python3 tools/voix_script.py --chaine victimes --slug x --question "…?" \\
        --segments ~/LEXVOX-PODCASTS/victimes/segments --moteur voicebox
    python3 tools/voix_script.py --bloc outro --chaine victimes
    python3 tools/voix_script.py --self-test
"""

import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from voix_moteur import ErreurVoix, charger  # noqa: E402

GABARITS = Path("podcasts/voix-avocat")

# Decoupage de l'intro en segments. Les indices renvoient aux paragraphes du
# gabarit, dans l'ordre. « invariant » = identique dans toute la chaine, donc
# genere une seule fois et reutilise par le montage.
SEGMENTS_INTRO = (
    ("01-question", (0,), False),
    ("02-jingle", (1,), True),
    ("03-sujet", (2,), False),
    ("04-final", (3, 4), True),
)

# L'auditeur ne doit jamais pouvoir croire que Nathalie et Nicolas sont des
# avocats du cabinet. Le mot « synthese » n'est pas obligatoire — l'honnetete
# l'est. Une de ces formulations au moins doit figurer dans l'intro.
MARQUEURS_HONNETETE = (
    "ne sont pas avocats",
    "ne sont pas des avocats",
    "créées par le cabinet",
    "créés par le cabinet",
    "voix de synthèse",
)

EXIGENCES = {
    "intro": {"mentions": ("le podcast du cabinet lexvox avocats",),
              "noms": ("Nathalie", "Nicolas"),
              "honnetete": True},
    "outro": {"mentions": (), "noms": (), "honnetete": False},
}

# Publicite personnelle de l'avocat : RIN art. 10.2 (sincere et veridique,
# sans mention comparative) et art. 10 de la loi n° 71-1130 (interdiction du
# pacte de quota litis). Ces formulations ne doivent jamais sortir a l'oral.
FORMULES_INTERDITES = (
    "résultat garanti", "garantie de résultat", "nous garantissons",
    "je garantis", "vous obtiendrez", "sans aucun risque",
    "meilleur avocat", "le plus performant",
)

# Orthographe PHONETIQUE appliquee au seul texte envoye au moteur vocal.
# « Humbert » a un h muet : lu tel quel, le moteur articule le h et le nom
# sonne faux des la premiere seconde de chaque episode. Les gabarits, eux,
# gardent l'orthographe exacte : ils sont relus par des humains et servent
# aussi aux metadonnees.
PRONONCIATION = (
    ("Humbert", "Imbert"),
    ("LEXVOX AVOCATS", "Lexvox Avocats"),
    ("LEXVOX", "Lexvox"),
    ("LEXVICTIMES", "Lex-Victimes"),
    ("LEXVICTIME", "Lex-Victime"),
)


def appliquer_prononciation(texte: str) -> str:
    """Applique la table, meme quand l'expression est coupee par un retour
    a la ligne : les gabarits sont mis en forme pour l'oeil, et « LEXVOX
    AVOCATS » se retrouve souvent a cheval sur deux lignes."""
    for ecrit, dit in PRONONCIATION:
        motif = r"\s+".join(re.escape(mot) for mot in ecrit.split())
        texte = re.sub(motif, dit, texte)
    return texte


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


def composer(gabarit: str, titre: str, sujet: str, bloc: str = "intro",
             question: str = "", avocat: str = "") -> str:
    texte = (gabarit.replace("{titre}", titre).replace("{sujet}", sujet)
             .replace("{question}", question))
    # {avocat} n'existe que la ou le signataire n'est pas fixe par la chaine.
    # Laisse en place si non fourni : le controle ci-dessous le signalera.
    if avocat:
        texte = texte.replace("{avocat}", avocat)
    restants = re.findall(r"\{(\w+)\}", texte)
    if restants:
        raise RuntimeError(f"variables non remplacees : {', '.join(restants)}")
    # les retours a la ligne du gabarit ne doivent pas masquer une mention
    aplati = re.sub(r"\s+", " ", texte.lower())
    exigences = EXIGENCES[bloc]
    manquantes = [m for m in exigences["mentions"] if m not in aplati]
    if manquantes:
        raise RuntimeError(
            f"jingle verbal altere : « {', '.join(manquantes)} » a disparu — "
            "c'est la phrase qui rend la serie reconnaissable, elle ne se "
            "reformule pas d'un episode a l'autre")
    absents = [a for a in exigences["noms"] if a.lower() not in aplati]
    if absents:
        raise RuntimeError(
            f"animateur non presente dans l'introduction : {', '.join(absents)}"
            " — l'avocat doit nommer les deux personnes qui animent l'emission")
    if exigences["honnetete"] and not any(m in aplati
                                          for m in MARQUEURS_HONNETETE):
        raise RuntimeError(
            "l'introduction ne dit plus que Nathalie et Nicolas ne sont pas "
            "des avocats du cabinet. Sans cela, l'auditeur peut croire qu'il "
            "ecoute deux collaborateurs : garder l'une des formulations "
            f"suivantes — {', '.join(MARQUEURS_HONNETETE)}")
    if bloc == "intro":
        accroche = texte.strip().split("\n\n")[0].strip()
        if not accroche.rstrip().endswith("?"):
            raise RuntimeError(
                "l'introduction ne commence pas par une question — c'est la "
                "structure imposée de la série : une accroche interrogative "
                f"dont la réponse est l'article. Reçu : « {accroche[:70]}… »")
    interdites = [f for f in FORMULES_INTERDITES if f in aplati]
    if interdites:
        raise RuntimeError(
            f"formulation interdite dans le script : {', '.join(interdites)}"
            " — publicite personnelle de l'avocat, RIN art. 10.2 et art. 10 "
            "de la loi n° 71-1130")
    return texte


def decouper(texte: str):
    """Intro -> [(nom, texte, invariant)] selon SEGMENTS_INTRO."""
    paragraphes = [p.strip() for p in re.split(r"\n\s*\n", texte.strip())
                   if p.strip()]
    attendus = 1 + max(i for _, indices, _ in SEGMENTS_INTRO for i in indices)
    if len(paragraphes) != attendus:
        raise RuntimeError(
            f"l'intro compte {len(paragraphes)} paragraphes, {attendus} "
            "attendus. Le decoupage en segments repose sur cette structure : "
            "question / jingle / sujet / animateurs / relance. Ne pas fusionner "
            "ni ajouter de paragraphe au gabarit.")
    return [(nom, "\n\n".join(paragraphes[i] for i in indices), invariant)
            for nom, indices, invariant in SEGMENTS_INTRO]


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
        if not options.question:
            raise RuntimeError(
                "--question est requise : chaque episode s'ouvre sur une "
                "question dont la reponse est l'article. La produire avec "
                "PROMPT-INTRO-VOIX.md")
    else:
        # l'outro est fixe par chaine : aucune variable d'episode
        titre, sujet = titre or "", sujet or ""
    if "{avocat}" in gabarit and not options.avocat:
        raise RuntimeError(
            f"la chaine « {options.chaine} » n'a pas de signataire fixe : "
            "passer --avocat \"Maître Prénom Nom\". C'est l'avocat qui traite "
            "cette matiere qui presente l'emission, et c'est sa voix clonee "
            "qui doit la dire.")
    texte = composer(gabarit, titre, sujet, bloc, options.question or "",
                     options.avocat or "")
    dit = texte if options.sans_phonetique else appliquer_prononciation(texte)

    print(dit)
    rappel = ("" if bloc == "intro" else
              " — fixe pour toute la chaine, une seule prise suffit")
    print(f"\n--- {len(dit)} caracteres — a faire dire par la voix clonee "
          f"du cabinet dans Voicebox{rappel} ---", file=sys.stderr)
    if not options.sans_phonetique and dit != texte:
        print("--- orthographe phonetique appliquee (Humbert -> Imbert, etc.) "
              ": elle ne concerne QUE le texte lu ---", file=sys.stderr)
    if options.sortie:
        Path(options.sortie).write_text(dit + "\n", encoding="utf-8")
        print(f"--- ecrit dans {options.sortie} ---", file=sys.stderr)

    if options.segments and bloc == "intro":
        return produire_segments(options, texte)
    if options.moteur != "aucun":
        moteur = charger(options.moteur, options.config)
        moteur.verifier()
        cible = Path(options.sortie or f"{bloc}-{options.chaine}.mp3")
        resultat = moteur.synthetiser(dit, cible.with_suffix(".mp3"),
                                      options.chaine, bloc)
        print(f"--- {resultat.get('consigne') or resultat['audio']} ---",
              file=sys.stderr)
    return 0


def produire_segments(options, texte: str) -> int:
    """Ecrit (et synthetise) les quatre segments de l'intro."""
    dossier = Path(options.segments).expanduser()
    dossier.mkdir(parents=True, exist_ok=True)
    moteur = None
    if options.moteur != "aucun":
        moteur = charger(options.moteur, options.config)
        moteur.verifier()

    print(f"\n--- segments dans {dossier} ---", file=sys.stderr)
    for nom, morceau, invariant in decouper(texte):
        base = (f"{nom}-{options.chaine}" if invariant
                else f"{nom}-{options.chaine}-{options.slug}")
        cible = dossier / f"{base}.mp3"
        dit = (morceau if options.sans_phonetique
               else appliquer_prononciation(morceau))
        (dossier / f"{base}.txt").write_text(dit + "\n", encoding="utf-8")

        etat = "invariant" if invariant else "variable "
        if invariant and cible.is_file() and not options.refaire_invariants:
            print(f"   [{etat}] {cible.name} — deja enregistre, REUTILISE "
                  "(ne pas le refaire : la signature deriverait)",
                  file=sys.stderr)
            continue
        if moteur is None:
            print(f"   [{etat}] {base}.txt — a faire dire", file=sys.stderr)
            continue
        resultat = moteur.synthetiser(dit, cible, options.chaine, nom)
        print(f"   [{etat}] {resultat.get('consigne') or resultat['audio']}",
              file=sys.stderr)
    return 0


def self_test() -> int:
    essais, echecs = 0, []

    def verifier(libelle, condition):
        nonlocal essais
        essais += 1
        if not condition:
            echecs.append(libelle)

    honnete = ("Nathalie et Nicolas ne sont pas avocats, ce sont les voix de "
               "l'émission.")
    gabarit = ("{question}\n\nBienvenue dans le podcast du cabinet LEXVOX "
               f"AVOCATS.\n\nAujourd'hui : {{sujet}}, d'après « {{titre}} ».\n\n{honnete}"
               "\n\nLa réponse, tout de suite.")
    rendu = composer(gabarit, "Mon Titre", "l'indemnisation", "intro",
                     "Pouvez-vous refuser l'expertise ?")
    verifier("substitution titre", "Mon Titre" in rendu)
    verifier("substitution sujet", "l'indemnisation" in rendu)
    verifier("substitution question", rendu.startswith("Pouvez-vous"))
    verifier("aucune accolade restante", "{" not in rendu)

    socle = ("\n\nBienvenue dans le podcast du cabinet LEXVOX AVOCATS."
             f"\n\nAujourd'hui : {{sujet}}, d'après « {{titre}} ».\n\n{honnete}"
             "\n\nLa réponse, tout de suite.")
    for mauvais, motif in (
            ("{question}" + socle + "\n\n{inconnu}", "variable non remplacee"),
            ("{question}\n\nBienvenue dans le podcast du cabinet LEXVOX "
             "AVOCATS.\n\nAujourd'hui : {sujet}, d'après « {titre} »."
             "\n\nNathalie et Nicolas animent l'émission.\n\nBonne écoute.",
             "aucun marqueur d'honnetete"),
            ("{question}\n\nBienvenue dans le podcast du cabinet LEXVOX "
             "AVOCATS.\n\nAujourd'hui : {sujet}, d'après « {titre} »."
             "\n\nNicolas n'est pas avocat.\n\nBonne écoute.",
             "second animateur absent"),
            ("Bonjour à tous." + socle, "ne commence pas par une question"),
            ("{question}\n\nUne émission juridique.\n\nAujourd'hui : {sujet}, "
             f"d'après « {{titre}} ».\n\n{honnete}\n\nBonne écoute.",
             "jingle absent")):
        essais += 1
        try:
            composer(mauvais, "T", "s", "intro", "Une question ?")
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

    # prononciation : appliquee au texte dit, jamais au gabarit
    verifier("h muet corrige",
             appliquer_prononciation("Maître Patrice Humbert")
             == "Maître Patrice Imbert")
    verifier("sigle adouci",
             "Lexvox Avocats" in appliquer_prononciation("LEXVOX AVOCATS"))
    verifier("sigle coupe par un retour a la ligne",
             appliquer_prononciation("cabinet LEXVOX\nAVOCATS.")
             == "cabinet Lexvox Avocats.")
    verifier("aucun sigle majuscule residuel",
             not any(mot in appliquer_prononciation(
                 extraire_gabarit(GABARITS / f"SCRIPT-INTRO-{c}.md"))
                 for c in ("victimes", "famille", "permis")
                 for mot in ("LEXVOX", "AVOCATS", "LEXVICTIME")))

    # decoupage en segments
    segments = decouper(composer(gabarit, "T", "s", "intro", "Question ?"))
    verifier("quatre segments", len(segments) == 4)
    verifier("question variable", segments[0] == ("01-question", "Question ?",
                                                  False))
    verifier("jingle invariant", segments[1][2] is True)
    verifier("final invariant et fusionne",
             segments[3][2] is True and "\n\n" in segments[3][1])
    essais += 1
    try:
        decouper("un seul paragraphe")
        echecs.append("structure alteree non detectee")
    except RuntimeError:
        pass

    # les six gabarits livres doivent passer tous les controles de leur bloc
    for bloc in ("intro", "outro"):
        for chaine in ("victimes", "famille", "permis"):
            chemin = GABARITS / f"SCRIPT-{bloc.upper()}-{chaine}.md"
            essais += 1
            try:
                texte = composer(extraire_gabarit(chemin), "Titre d'essai",
                                 "un sujet d'essai", bloc,
                                 "Une question d'essai ?", "Maître Essai")
                if bloc == "intro":
                    for prenom in ("Nathalie", "Nicolas"):
                        if prenom not in texte:
                            echecs.append(f"{chaine} : prenom {prenom} absent")
                            break
                    else:
                        decouper(texte)
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
    analyseur.add_argument("--question",
                           help="accroche interrogative dont la reponse est "
                                "l'article (cf. PROMPT-INTRO-VOIX.md)")
    analyseur.add_argument("--avocat",
                           help="signataire de l'episode, pour les chaines "
                                "dont le gabarit porte {avocat} (permis)")
    analyseur.add_argument("--csv", default="podcasts/queue-podcast.csv")
    analyseur.add_argument("--sortie", help="ecrit le script dans un fichier")
    analyseur.add_argument("--segments",
                           help="decoupe l'intro et ecrit chaque segment dans "
                                "ce dossier (invariants reutilises)")
    analyseur.add_argument("--refaire-invariants", action="store_true",
                           help="resynthetise le jingle deja enregistre "
                                "(deconseille : la signature derive)")
    analyseur.add_argument("--moteur", choices=("aucun", "manuel", "voicebox"),
                           default="aucun",
                           help="voicebox = synthese locale automatique")
    analyseur.add_argument("--config", default="podcasts/voicebox.json")
    analyseur.add_argument("--sans-phonetique", action="store_true",
                           help="n'applique pas les corrections de prononciation")
    analyseur.add_argument("--self-test", action="store_true")
    options = analyseur.parse_args()

    if options.self_test:
        return self_test()
    if not options.chaine:
        analyseur.error("--chaine est requis")
    if options.bloc == "intro" and not (options.slug or options.titre):
        analyseur.error("pour une intro, --slug ou --titre est requis "
                        "(l'outro, lui, ne depend pas de l'episode)")
    if options.segments and not options.slug:
        analyseur.error("--segments a besoin de --slug pour nommer les "
                        "segments variables")
    try:
        return generer(options)
    except (RuntimeError, FileNotFoundError, ErreurVoix) as erreur:
        print(f"ECHEC : {erreur}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
