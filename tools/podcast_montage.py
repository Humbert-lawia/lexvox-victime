#!/usr/bin/env python3
"""Assemble le generique, la voix de l'avocat et le debat en un MP3 diffusable.

Ordre de montage IMPERATIF :
    GENERIQUE MUSICAL -> INTRO (voix de l'avocat, Voicebox)
    -> CORPS (NotebookLM) -> OUTRO (voix de l'avocat, Voicebox).

L'OUTRO porte l'appel a l'action, dit par l'avocat lui-meme. Le debat ne le
recite plus : sans outro, l'episode n'en contient aucun — d'ou le refus de
monter si elle manque, sauf --sans-outro explicite.

L'INTRO peut arriver en un seul fichier ou en TROIS SEGMENTS
(cf. voix_script.py --segments). Le mode segments est preferable : la
presentation et la relance finale sont alors enregistrees une seule fois par
chaine et reutilisees telles quelles, au lieu de deriver a chaque resynthese.
Seule la question du jour est refaite — 8 des 30 secondes d'intro.

Le GENERIQUE est une musique libre de droit, taillee et fondue en tete
d'episode. Elle est mixee PLUS BAS que la voix, et le montage refuse de
tourner si sa licence n'est pas consignee dans podcasts/musique/LICENCES.md :
une musique dont on ne retrouve pas la licence peut faire retirer les
72 episodes des plateformes.

Chaine de traitement :
  1. appariement DETERMINISTE des sources par (chaine, slug) via le CSV ;
  2. normalisation loudness EN DEUX PASSES de chaque source separement,
     la musique visant une cible plus basse que la voix ;
  3. concatenation avec des respirations calibrees, sans chevauchement ;
  4. limiteur de securite puis encodage MP3 libmp3lame ;
  5. mesure du resultat, correction unique si l'ecart depasse 0,5 LU ;
  6. controles qualite ; aucune publication si l'un echoue.

Jamais d'upload : la plateforme de diffusion est une variable de
configuration non encore definie (cf. PROMPT-MONTAGE-DIFFUSION.md §11).

Usage :
    python3 tools/podcast_montage.py --chaine victimes --slug mon-article
    python3 tools/podcast_montage.py --chaine victimes --slug x \\
        --segments ~/LEXVOX-PODCASTS/victimes/segments
    python3 tools/podcast_montage.py --chaine permis --slug x --dry-run
    python3 tools/podcast_montage.py --self-test
"""

import argparse
import csv
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ffmpeg_moteur import ErreurMoteur, charger  # noqa: E402

# --- Configuration editoriale -------------------------------------------------
CHAINES = {
    "victimes": {"podcast": "LEXVICTIME — le podcast du droit des victimes",
                 "auteur": "Patrice Humbert"},
    "famille": {"podcast": "Divorce & famille : parlons-en",
                "auteur": "Cédrine Raybaud"},
    "permis": {"podcast": "Permis en danger",
               "auteur": "Patrice Humbert"},
}
EDITEUR = "SELARL LEXVOX AVOCATS"

# --- Cible technique (PROMPT-MONTAGE-DIFFUSION.md §4) -------------------------
LOUDNESS_CIBLE = -16.0      # LUFS
VRAI_PIC_MAX = -1.5         # dBTP
ECHANTILLONNAGE = 44100     # Hz
DEBIT_DEFAUT = 192          # kb/s CBR
PAUSE_DEFAUT = 400          # ms de respiration entre les blocs
PAUSE_SEGMENTS = 150        # ms entre segments d'une meme intro : ce sont
                            # des phrases qui s'enchainent, pas des blocs
TOLERANCE_LOUDNESS = 0.5    # LU
TOLERANCE_DUREE = 0.5       # s

# --- Generique musical --------------------------------------------------------
MUSIQUE_DUREE = 6.0         # s conserves en tete d'episode
MUSIQUE_NIVEAU = -20.0      # LUFS : 4 LU sous la voix, sinon elle l'ecrase
MUSIQUE_FONDU_ENTREE = 0.3  # s
MUSIQUE_FONDU_SORTIE = 1.5  # s — la musique doit mourir avant la question
MUSIQUE_PAUSE = 250         # ms entre la fin du generique et la voix
REGISTRE_LICENCES = Path("podcasts/musique/LICENCES.md")

# Le nom du fichier de segment est fixe par voix_script.py --segments.
SEGMENTS_INTRO = (("01-question", False), ("02-presentation", True),
                  ("03-final", True))


# --- Utilitaires --------------------------------------------------------------
MOTEUR = None   # renseigne par traiter() : MoteurLocal ou MoteurAPI


def executer(commande, attendre_json=False):
    """Lance ffmpeg/ffprobe via le moteur courant (local ou API)."""
    code, sortie, erreur = MOTEUR.executer(commande)
    if attendre_json and code != 0:
        raise RuntimeError(f"echec de {commande[0]} : {erreur.strip()[:400]}")
    return code, sortie, erreur


def sonder(fichier: Path) -> dict:
    """ffprobe -> dict des caracteristiques du premier flux audio."""
    _, sortie, _ = executer(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(fichier)], attendre_json=True)
    donnees = json.loads(sortie)
    flux = next((f for f in donnees.get("streams", [])
                 if f.get("codec_type") == "audio"), None)
    if flux is None:
        raise RuntimeError(f"aucun flux audio dans {fichier}")
    format_ = donnees.get("format", {})
    return {
        "codec": flux.get("codec_name"),
        "canaux": int(flux.get("channels", 0)),
        "echantillonnage": int(flux.get("sample_rate", 0)),
        "duree": float(format_.get("duration") or flux.get("duration") or 0),
        "debit": int(format_.get("bit_rate", 0)) // 1000,
        "octets": int(format_.get("size", 0)),
        "encodeur": (format_.get("tags", {}) or {}).get("encoder", ""),
        "etiquettes": format_.get("tags", {}) or {},
    }


def mesurer_loudness(fichier: Path) -> tuple:
    """Mesure EBU R128 via la premiere passe de loudnorm. -> (I, TP)."""
    _, _, journal = executer(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(fichier),
         "-af", f"loudnorm=I={LOUDNESS_CIBLE}:TP={VRAI_PIC_MAX}:LRA=11:"
                "print_format=json", "-f", "null", "-"])
    mesures = extraire_json_loudnorm(journal)
    return float(mesures["input_i"]), float(mesures["input_tp"])


def extraire_json_loudnorm(journal: str) -> dict:
    """Isole le bloc JSON que loudnorm ecrit en fin de flux d'erreur."""
    debut = journal.rfind("{")
    fin = journal.rfind("}")
    if debut == -1 or fin == -1 or fin < debut:
        raise RuntimeError("mesure loudnorm illisible (ffmpeg trop ancien ?)")
    return json.loads(journal[debut:fin + 1])


def normaliser(source: Path, destination: Path, canaux: int,
               cible: float = LOUDNESS_CIBLE):
    """Loudness en deux passes vers un WAV intermediaire.

    `cible` descend pour le generique musical : mixe au meme niveau que la
    voix, il la couvrirait.
    """
    _, _, journal = executer(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(source),
         "-af", f"loudnorm=I={cible}:TP={VRAI_PIC_MAX}:LRA=11:"
                "print_format=json", "-f", "null", "-"])
    m = extraire_json_loudnorm(journal)
    filtre = (f"loudnorm=I={cible}:TP={VRAI_PIC_MAX}:LRA=11:"
              f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:"
              f"measured_thresh={m['input_thresh']}:"
              f"offset={m['target_offset']}:linear=true:print_format=summary")
    code, _, erreur = executer(
        ["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", str(source),
         "-af", filtre, "-ar", str(ECHANTILLONNAGE), "-ac", str(canaux),
         "-c:a", "pcm_s16le", str(destination)])
    if code != 0:
        raise RuntimeError(f"normalisation de {source.name} : "
                           f"{erreur.strip()[:300]}")


def tailler_musique(source: Path, destination: Path, canaux: int,
                    duree: float):
    """Coupe le generique a la duree voulue et le fait entrer puis mourir.

    Le fondu de sortie doit s'achever AVANT la premiere syllabe : une musique
    qui traine sous la question d'accroche la rend moins intelligible, et
    c'est justement la phrase qui doit accrocher l'auditeur.
    """
    depart_sortie = max(0.0, duree - MUSIQUE_FONDU_SORTIE)
    filtre = (f"atrim=0:{duree:.3f},asetpts=N/SR/TB,"
              f"afade=t=in:st=0:d={MUSIQUE_FONDU_ENTREE:.3f},"
              f"afade=t=out:st={depart_sortie:.3f}:"
              f"d={MUSIQUE_FONDU_SORTIE:.3f}")
    code, _, erreur = executer(
        ["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", str(source),
         "-af", filtre, "-ar", str(ECHANTILLONNAGE), "-ac", str(canaux),
         "-c:a", "pcm_s16le", str(destination)])
    if code != 0:
        raise RuntimeError(f"taille du generique : {erreur.strip()[:300]}")


def assembler(segments, pauses_ms, destination: Path, canaux: int):
    """Concatene les WAV normalises en inserant les respirations demandees.

    `pauses_ms` compte un element de moins que `segments` : les blocs
    (generique, intro, corps, outro) respirent plus longtemps entre eux que
    les phrases d'une meme intro.
    """
    if len(pauses_ms) != max(0, len(segments) - 1):
        raise RuntimeError(
            f"{len(segments)} segments mais {len(pauses_ms)} pauses — "
            "incoherence de montage, traitement interrompu")
    entrees = []
    for segment in segments:
        entrees += ["-i", str(segment)]
    disposition = "mono" if canaux == 1 else "stereo"
    silence = (f"anullsrc=channel_layout={disposition}:"
               f"sample_rate={ECHANTILLONNAGE}")

    morceaux, filtres = [], []
    for indice in range(len(segments)):
        morceaux.append(f"[{indice}:a]")
        if indice < len(segments) - 1 and pauses_ms[indice] > 0:
            etiquette = f"[p{indice}]"
            filtres.append(
                f"{silence}:d={pauses_ms[indice] / 1000:.3f}{etiquette}")
            morceaux.append(etiquette)
    filtres.append(f"{''.join(morceaux)}concat=n={len(morceaux)}:v=0:a=1[out]")

    code, _, erreur = executer(
        ["ffmpeg", "-hide_banner", "-nostats", "-y", *entrees,
         "-filter_complex", ";".join(filtres), "-map", "[out]",
         "-ar", str(ECHANTILLONNAGE), "-ac", str(canaux),
         "-c:a", "pcm_s16le", str(destination)])
    if code != 0:
        raise RuntimeError(f"assemblage : {erreur.strip()[:300]}")


def encoder(source: Path, destination: Path, debit: int, canaux: int,
            metadonnees: dict, correction_db: float = 0.0):
    """Limiteur de securite puis encodage MP3 CBR avec etiquettes ID3v2.3."""
    filtres = []
    if abs(correction_db) > 0.01:
        filtres.append(f"volume={correction_db:.2f}dB")
    filtres.append(f"alimiter=limit={VRAI_PIC_MAX}dB:level=disabled")

    commande = ["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", str(source),
                "-af", ",".join(filtres),
                "-c:a", "libmp3lame", "-b:a", f"{debit}k",
                "-ar", str(ECHANTILLONNAGE), "-ac", str(canaux),
                "-id3v2_version", "3", "-write_id3v1", "1"]
    for cle, valeur in metadonnees.items():
        if valeur:
            commande += ["-metadata", f"{cle}={valeur}"]
    commande.append(str(destination))
    code, _, erreur = executer(commande)
    if code != 0:
        raise RuntimeError(f"encodage : {erreur.strip()[:300]}")


# --- Appariement des sources --------------------------------------------------
def normaliser_slug(valeur: str) -> str:
    sans_accent = unicodedata.normalize("NFKD", valeur)
    sans_accent = "".join(c for c in sans_accent if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", sans_accent.lower()).strip("-")


def nom_final(chaine: str, rang, slug: str) -> str:
    """podcast-<chaine>-<NN>-<slug>.mp3 (la chaine evite les collisions)."""
    try:
        numero = f"{int(rang):02d}"
    except (TypeError, ValueError):
        numero = "00"
    return f"podcast-{normaliser_slug(chaine)}-{numero}-{normaliser_slug(slug)}.mp3"


def lire_ligne_csv(csv_path: Path, chaine: str, slug: str) -> dict:
    with csv_path.open(encoding="utf-8", newline="") as flux:
        for ligne in csv.DictReader(flux):
            if (ligne.get("chaine", "").strip() == chaine
                    and ligne.get("slug", "").strip() == slug):
                return ligne
    raise RuntimeError(
        f"aucune ligne chaine={chaine} slug={slug} dans {csv_path} — "
        "appariement impossible, traitement interrompu")


def trouver_outro(racine: Path, chaine: str, slug: str) -> Path:
    """Cherche l'outro : d'abord propre a l'episode, sinon celle de la chaine.

    L'outro porte l'appel a l'action et ne depend pas de l'article : une
    seule prise de voix sert les 24 episodes d'une chaine. Une version
    specifique reste possible (episodes sensibles, par exemple violences
    conjugales) et prime alors sur la version commune.
    """
    dossier = racine / "outro"
    for motif in (f"outro-*{slug}.*", f"outro-{chaine}.*"):
        candidats = [c for c in sorted(dossier.glob(motif))
                     if c.suffix.lower() in (".mp3", ".m4a", ".wav", ".aac",
                                             ".flac", ".ogg", ".opus")]
        if len({c.stem for c in candidats}) > 1:
            raise RuntimeError(
                f"plusieurs outros concurrentes dans {dossier} : "
                f"{', '.join(c.name for c in candidats)} — correspondance "
                "incertaine, traitement interrompu")
        if candidats:
            return candidats[0]
    raise RuntimeError(
        f"outro introuvable dans {dossier} (attendu outro-{chaine}.mp3, ou "
        f"une version propre a l'episode). L'appel a l'action n'est plus "
        "recite par le debat : sans outro, l'episode n'en contient aucun. "
        "Enregistrer l'outro, ou passer --sans-outro en connaissance de cause.")


def trouver_source(dossier: Path, motifs) -> Path:
    """Cherche un fichier par NOM (jamais par date) : appariement certain."""
    candidats = []
    for motif in motifs:
        candidats += sorted(dossier.glob(motif))
    audio = [c for c in candidats
             if c.suffix.lower() in (".mp3", ".m4a", ".wav", ".aac", ".flac",
                                     ".ogg", ".opus")]
    if not audio:
        raise RuntimeError(
            f"source introuvable dans {dossier} (motifs : {', '.join(motifs)})")
    if len({c.stem for c in audio}) > 1:
        raise RuntimeError(
            f"plusieurs sources concurrentes dans {dossier} : "
            f"{', '.join(c.name for c in audio)} — correspondance incertaine, "
            "traitement interrompu")
    return audio[0]


def trouver_segments_intro(dossier: Path, chaine: str, slug: str) -> list:
    """Les quatre segments d'intro, dans l'ordre impose par la serie.

    Les invariants (jingle, relance) ne portent pas le slug : c'est ce qui
    permet de les enregistrer une fois et de les rejouer a l'identique.
    """
    trouves = []
    for nom, invariant in SEGMENTS_INTRO:
        base = f"{nom}-{chaine}" if invariant else f"{nom}-{chaine}-{slug}"
        fichier = trouver_source(dossier, [f"{base}.*"])
        trouves.append((nom, fichier, invariant))
    return trouves


def trouver_musique(racine: Path, chaine: str) -> Path:
    """Generique de la chaine, sinon generique commun au cabinet."""
    for dossier, motif in ((racine / "musique", f"musique-{chaine}.*"),
                           (racine.parent / "musique", f"musique-{chaine}.*"),
                           (racine.parent / "musique", "musique-lexvox.*")):
        if dossier.is_dir():
            try:
                return trouver_source(dossier, [motif])
            except RuntimeError:
                continue
    raise RuntimeError(
        f"generique musical introuvable (cherche musique-{chaine}.mp3 dans "
        f"{racine / 'musique'} puis {racine.parent / 'musique'}, a defaut "
        "musique-lexvox.mp3). Deposer une musique LIBRE DE DROIT et consigner "
        f"sa licence dans {REGISTRE_LICENCES}, ou passer --sans-musique.")


def verifier_licence(musique: Path, registre: Path = REGISTRE_LICENCES):
    """Refuse une musique dont la licence n'est pas consignee.

    Ce n'est pas une formalite : une plateforme qui recoit une reclamation
    retire l'episode, parfois toute la serie. La preuve doit exister AVANT la
    diffusion, pas le jour de la reclamation.
    """
    if not registre.is_file():
        raise RuntimeError(
            f"registre des licences absent : {registre}. Aucune musique ne "
            "doit etre diffusee sans preuve de licence archivee.")
    texte = registre.read_text(encoding="utf-8")
    if musique.stem not in texte:
        raise RuntimeError(
            f"« {musique.name} » n'est pas consigne dans {registre}. Ajouter "
            "la fiche de la piste (source, licence, date de telechargement, "
            "usage commercial autorise) avant de monter quoi que ce soit.")


# --- Controles qualite --------------------------------------------------------
def controler(final: Path, sondage: dict, loudness, duree_attendue: float,
              debit: int, canaux: int, ordre_verifie: bool) -> list:
    integre, vrai_pic = loudness
    controles = [
        ("fichier final present", final.is_file(), str(final)),
        ("fichier lisible par ffprobe", sondage["duree"] > 0,
         f"{sondage['duree']:.2f} s"),
        ("codec MP3", sondage["codec"] == "mp3", sondage["codec"]),
        ("encodeur libmp3lame", "lame" in sondage["encodeur"].lower(),
         sondage["encodeur"] or "(non etiquete)"),
        (f"debit proche de {debit} kb/s", abs(sondage["debit"] - debit) <= 12,
         f"{sondage['debit']} kb/s"),
        (f"echantillonnage {ECHANTILLONNAGE} Hz",
         sondage["echantillonnage"] == ECHANTILLONNAGE,
         f"{sondage['echantillonnage']} Hz"),
        (f"canaux = {canaux}", sondage["canaux"] == canaux,
         str(sondage["canaux"])),
        ("ordre intro -> corps respecte", ordre_verifie,
         "montage construit dans cet ordre"),
        ("aucune source tronquee",
         sondage["duree"] >= duree_attendue - TOLERANCE_DUREE,
         f"{sondage['duree']:.2f} s pour {duree_attendue:.2f} s attendues"),
        ("duree coherente avec la somme des sources",
         abs(sondage["duree"] - duree_attendue) <= TOLERANCE_DUREE,
         f"ecart {sondage['duree'] - duree_attendue:+.2f} s"),
        (f"loudness proche de {LOUDNESS_CIBLE} LUFS",
         abs(integre - LOUDNESS_CIBLE) <= TOLERANCE_LOUDNESS,
         f"{integre:.2f} LUFS"),
        (f"vrai pic <= {VRAI_PIC_MAX} dBTP", vrai_pic <= VRAI_PIC_MAX + 0.1,
         f"{vrai_pic:.2f} dBTP"),
        ("etiquettes ID3 presentes",
         bool(sondage["etiquettes"].get("title")),
         ", ".join(sorted(sondage["etiquettes"])) or "(aucune)"),
    ]
    return [{"controle": libelle, "ok": bool(ok), "detail": detail}
            for libelle, ok, detail in controles]


# --- Traitement d'un episode --------------------------------------------------
def traiter(options) -> int:
    global MOTEUR
    MOTEUR = charger(options.moteur, options.config)
    MOTEUR.verifier()
    if not MOTEUR.journal_disponible:
        raise ErreurMoteur(
            "ce service ffmpeg ne rend pas le journal d'execution. Sans lui, "
            "loudnorm ne peut pas fonctionner en deux passes (les mesures de "
            "la 1re passe s'y trouvent) et les controles 11 (loudness) et 12 "
            "(vrai pic) sont invérifiables. Choisir un service qui rend le "
            "flux d'erreur de ffmpeg, ou monter en local.")

    csv_path = Path(options.csv)
    ligne = lire_ligne_csv(csv_path, options.chaine, options.slug)
    reglages = CHAINES.get(options.chaine)
    if reglages is None:
        raise RuntimeError(f"chaine inconnue : {options.chaine}")

    racine = Path(options.racine).expanduser() / options.chaine
    dossier_intro = racine / "intro"
    dossier_corps = racine / "brut"
    dossier_final = racine / "mp3"
    dossier_final.mkdir(parents=True, exist_ok=True)
    travail = racine / ".travail"
    travail.mkdir(parents=True, exist_ok=True)

    # --- generique musical (facultatif, mais licence obligatoire s'il existe)
    musique = None
    if not options.sans_musique:
        musique = (Path(options.musique).expanduser() if options.musique
                   else trouver_musique(racine, options.chaine))
        verifier_licence(musique, Path(options.licences))

    # --- introduction : un seul fichier, ou quatre segments reutilisables
    segments_intro = []
    if options.segments:
        segments_intro = trouver_segments_intro(
            Path(options.segments).expanduser(), options.chaine, options.slug)
        intro = None
    else:
        intro = (Path(options.intro).expanduser() if options.intro
                 else trouver_source(dossier_intro, [f"intro-*{options.slug}.*"]))

    corps = (Path(options.corps).expanduser() if options.corps
             else trouver_source(dossier_corps, [f"{options.slug}.*"]))
    if options.outro:
        outro = Path(options.outro).expanduser()
    elif options.sans_outro:
        outro = None
    else:
        outro = trouver_outro(racine, options.chaine, options.slug)

    # Chaque bloc porte sa cible de loudness et la respiration qui le suit.
    blocs = []
    if musique:
        blocs.append({"etiquette": "generique musical", "fichier": musique,
                      "cible": MUSIQUE_NIVEAU, "pause": MUSIQUE_PAUSE,
                      "taille": options.duree_musique})
    if segments_intro:
        for rang, (nom, fichier, invariant) in enumerate(segments_intro):
            dernier = rang == len(segments_intro) - 1
            blocs.append({
                "etiquette": f"intro {nom}"
                             f"{' (réutilisé)' if invariant else ''}",
                "fichier": fichier, "cible": LOUDNESS_CIBLE,
                "pause": PAUSE_DEFAUT if dernier else options.pause_segments,
                "taille": None})
    else:
        blocs.append({"etiquette": "intro (voix de l'avocat)",
                      "fichier": intro, "cible": LOUDNESS_CIBLE,
                      "pause": PAUSE_DEFAUT, "taille": None})
    blocs.append({"etiquette": "corps NotebookLM", "fichier": corps,
                  "cible": LOUDNESS_CIBLE, "pause": options.pause,
                  "taille": None})
    if outro:
        blocs.append({"etiquette": "outro (voix de l'avocat)",
                      "fichier": outro, "cible": LOUDNESS_CIBLE,
                      "pause": 0, "taille": None})
    blocs[-1]["pause"] = 0

    sources = [(bloc["etiquette"], bloc["fichier"]) for bloc in blocs]
    for etiquette, fichier in sources:
        if not fichier.is_file():
            raise RuntimeError(f"{etiquette} absente : {fichier}")

    final = dossier_final / nom_final(options.chaine, ligne.get("rank"),
                                      options.slug)

    if options.dry_run:
        print("Plan de montage (aucune commande executee) :")
        for etiquette, fichier in sources:
            print(f"  {etiquette:20} {fichier}")
        print(f"  {'fichier final':20} {final}")
        print(f"  ordre : {' -> '.join(e for e, _ in sources)}")
        return 0

    sondages = {}
    for bloc in blocs:
        sondage = sonder(bloc["fichier"])
        if sondage["duree"] <= 0:
            raise RuntimeError(f"{bloc['etiquette']} illisible ou vide : "
                               f"{bloc['fichier']}")
        # le generique n'entre qu'a hauteur de la duree conservee
        bloc["duree"] = (min(sondage["duree"], bloc["taille"])
                         if bloc["taille"] else sondage["duree"])
        sondages[bloc["etiquette"]] = sondage

    canaux = 1 if options.canaux == "mono" else 2
    if options.canaux == "auto":
        canaux = 1  # contenu essentiellement vocal

    normalises = []
    for indice, bloc in enumerate(blocs):
        cible = travail / f"{indice}-{normaliser_slug(bloc['etiquette'])}.wav"
        normaliser(bloc["fichier"], cible, canaux, bloc["cible"])
        if bloc["taille"]:
            taillee = travail / f"{indice}-generique-taille.wav"
            tailler_musique(cible, taillee, canaux, bloc["duree"])
            cible = taillee
        normalises.append(cible)

    assemble = travail / "assemble.wav"
    pauses_ms = [bloc["pause"] for bloc in blocs[:-1]]
    assembler(normalises, pauses_ms, assemble, canaux)

    duree_attendue = (sum(bloc["duree"] for bloc in blocs)
                      + sum(pauses_ms) / 1000)

    metadonnees = {
        "title": ligne.get("title") or options.slug,
        "album": reglages["podcast"],
        "artist": reglages["auteur"],
        "album_artist": reglages["auteur"],
        "publisher": EDITEUR,
        "track": ligne.get("rank") or "",
        "date": (ligne.get("published_at") or "")[:10],
        "comment": ligne.get("notes") or "",
        "genre": "Podcast",
    }
    encoder(assemble, final, options.debit, canaux, metadonnees)

    integre, vrai_pic = mesurer_loudness(final)
    correction = 0.0
    if abs(integre - LOUDNESS_CIBLE) > TOLERANCE_LOUDNESS:
        correction = LOUDNESS_CIBLE - integre
        encoder(assemble, final, options.debit, canaux, metadonnees,
                correction_db=correction)
        integre, vrai_pic = mesurer_loudness(final)

    sondage_final = sonder(final)
    controles = controler(final, sondage_final, (integre, vrai_pic),
                          duree_attendue, options.debit, canaux, True)
    controles.append({
        "controle": "licence du generique consignee",
        "ok": True,
        "detail": (f"{musique.name} — {options.licences}" if musique
                   else "aucun generique (--sans-musique)")})
    if not options.garder_travail:
        shutil.rmtree(travail, ignore_errors=True)

    echecs = [c for c in controles if not c["ok"]]
    rapport = {
        "chaine": options.chaine,
        "slug": options.slug,
        "ordre_de_montage": " -> ".join(e for e, _ in sources),
        "fichier_generique": musique.name if musique else "aucun",
        "fichier_intro": (", ".join(f.name for _, f, _ in segments_intro)
                          if segments_intro else intro.name),
        "segments_reutilises": [f.name for nom, f, inv in segments_intro if inv],
        "fichier_corps": corps.name,
        "fichier_outro": outro.name if outro else "aucune (--sans-outro)",
        "fichier_final": final.name,
        "chemin_final": str(final),
        "duree_s": round(sondage_final["duree"], 2),
        "poids_octets": sondage_final["octets"],
        "codec": sondage_final["codec"],
        "debit_kbps": sondage_final["debit"],
        "echantillonnage_hz": sondage_final["echantillonnage"],
        "canaux": sondage_final["canaux"],
        "loudness_lufs": round(integre, 2),
        "vrai_pic_dbtp": round(vrai_pic, 2),
        "correction_appliquee_db": round(correction, 2),
        "controles": controles,
        "plateforme_diffusion": options.plateforme,
        "statut_transmission": "aucune — plateforme non configuree",
        "statut": ("ECHEC — TRAITEMENT INTERROMPU" if echecs else
                   "SUCCES — FICHIER GENERE, PUBLICATION EN ATTENTE"),
    }
    if echecs:
        rapport["causes"] = [f"{c['controle']} : {c['detail']}" for c in echecs]

    afficher_rapport(rapport)
    if options.json:
        Path(options.json).write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
    return 4 if echecs else 0


def afficher_rapport(rapport: dict):
    print(f"\n=== COMPTE RENDU — {rapport['chaine']} / {rapport['slug']} ===")
    print(f"ordre de montage      : {rapport['ordre_de_montage']}")
    print(f"generique musical     : {rapport['fichier_generique']}")
    print(f"intro (voix avocat)   : {rapport['fichier_intro']}")
    if rapport.get("segments_reutilises"):
        print(f"  dont reutilises     : "
              f"{', '.join(rapport['segments_reutilises'])}")
    print(f"corps NotebookLM      : {rapport['fichier_corps']}")
    print(f"outro (voix avocat)   : {rapport['fichier_outro']}")
    print(f"fichier final         : {rapport['fichier_final']}")
    print(f"chemin                : {rapport['chemin_final']}")
    print(f"duree / poids         : {rapport['duree_s']} s / "
          f"{rapport['poids_octets'] // 1024} Ko")
    print(f"codec / debit         : {rapport['codec']} / "
          f"{rapport['debit_kbps']} kb/s")
    print(f"echantillonnage       : {rapport['echantillonnage_hz']} Hz, "
          f"{rapport['canaux']} canal/canaux")
    print(f"loudness / vrai pic   : {rapport['loudness_lufs']} LUFS / "
          f"{rapport['vrai_pic_dbtp']} dBTP")
    print("controles qualite     :")
    for controle in rapport["controles"]:
        print(f"   [{'OK' if controle['ok'] else '!!'}] {controle['controle']}"
              f" — {controle['detail']}")
    print(f"plateforme            : {rapport['plateforme_diffusion']}")
    print(f"transmission          : {rapport['statut_transmission']}")
    print(f"\n{rapport['statut']}")
    for cause in rapport.get("causes", []):
        print(f"  cause : {cause}")
    if not rapport.get("causes"):
        print("Fichier final valide — publication en attente de configuration "
              "de la plateforme de diffusion.")


# --- Auto-test des parties independantes de ffmpeg ----------------------------
def self_test() -> int:
    essais, echecs = 0, []

    def verifier(libelle, obtenu, attendu):
        nonlocal essais
        essais += 1
        if obtenu != attendu:
            echecs.append(f"{libelle} : obtenu {obtenu!r}, attendu {attendu!r}")

    verifier("slug accents", normaliser_slug("Indemnisation Éclair"),
             "indemnisation-eclair")
    verifier("slug ponctuation", normaliser_slug("permis : alcool/volant !"),
             "permis-alcool-volant")
    verifier("nom final", nom_final("victimes", "7", "mon-article"),
             "podcast-victimes-07-mon-article.mp3")
    verifier("nom final rang absent", nom_final("permis", None, "abc"),
             "podcast-permis-00-abc.mp3")

    # appariement : rang et slug relus depuis un CSV temporaire
    temporaire = Path("/tmp/_montage_selftest.csv")
    temporaire.write_text(
        "chaine,rank,slug,title\nvictimes,3,article-a,Titre A\n"
        "permis,1,article-b,Titre B\n", encoding="utf-8")
    verifier("lecture CSV", lire_ligne_csv(temporaire, "permis",
                                           "article-b")["title"], "Titre B")
    try:
        lire_ligne_csv(temporaire, "famille", "inexistant")
        echecs.append("lecture CSV : absence non detectee")
    except RuntimeError:
        pass
    essais += 1
    temporaire.unlink(missing_ok=True)

    # controles qualite : un fichier conforme passe, un fichier degrade echoue
    conforme = {"codec": "mp3", "canaux": 1, "echantillonnage": 44100,
                "duree": 300.0, "debit": 192, "octets": 7_200_000,
                "encodeur": "Lame 3.100", "etiquettes": {"title": "T"}}
    resultat = controler(Path("/tmp/x.mp3"), conforme, (-16.05, -1.7),
                         300.0, 192, 1, True)
    verifier("controles conformes", [c for c in resultat if not c["ok"]][1:],
             [])  # seul « fichier present » echoue sur un chemin fictif
    degrade = dict(conforme, codec="aac", echantillonnage=48000, duree=250.0)
    noms = {c["controle"] for c in controler(Path("/tmp/x.mp3"), degrade,
                                             (-12.0, -0.2), 300.0, 192, 1,
                                             True) if not c["ok"]}
    for attendu in ("codec MP3", "echantillonnage 44100 Hz",
                    "aucune source tronquee", "vrai pic <= -1.5 dBTP"):
        essais += 1
        if attendu not in noms:
            echecs.append(f"controle non declenche : {attendu}")

    # licence du generique : le refus doit venir AVANT tout appel a ffmpeg
    bac = Path("/tmp/_montage_musique")
    shutil.rmtree(bac, ignore_errors=True)
    bac.mkdir(parents=True, exist_ok=True)
    registre = bac / "LICENCES.md"
    essais += 1
    try:
        verifier_licence(bac / "musique-victimes.mp3", registre)
        echecs.append("registre de licences absent non detecte")
    except RuntimeError:
        pass
    registre.write_text("# Licences\n\n- musique-victimes : Pixabay\n",
                        encoding="utf-8")
    essais += 1
    try:
        verifier_licence(bac / "musique-victimes.mp3", registre)
    except RuntimeError as erreur:
        echecs.append(f"licence consignee refusee : {erreur}")
    essais += 1
    try:
        verifier_licence(bac / "musique-permis.mp3", registre)
        echecs.append("musique non consignee acceptee")
    except RuntimeError:
        pass

    # appariement des segments d'intro : invariants sans slug, variables avec
    segments = bac / "segments"
    segments.mkdir(parents=True, exist_ok=True)
    for nom in ("01-question-victimes-mon-article", "02-presentation-victimes",
                "03-final-victimes"):
        (segments / f"{nom}.mp3").write_bytes(b"\0")
    trouves = trouver_segments_intro(segments, "victimes", "mon-article")
    verifier("trois segments apparies", len(trouves), 3)
    verifier("question reconnue variable", trouves[0][2], False)
    verifier("presentation reconnue invariante", trouves[1][2], True)
    verifier("relance appariee sans slug", trouves[2][1].name,
             "03-final-victimes.mp3")
    (segments / "02-presentation-victimes.mp3").unlink()
    essais += 1
    try:
        trouver_segments_intro(segments, "victimes", "mon-article")
        echecs.append("segment manquant non detecte")
    except RuntimeError:
        pass
    shutil.rmtree(bac, ignore_errors=True)

    # incoherence pauses/segments : refus avant toute commande ffmpeg
    essais += 1
    try:
        assembler([Path("a.wav"), Path("b.wav")], [100, 200],
                  Path("/tmp/x.wav"), 1)
        echecs.append("nombre de pauses incoherent accepte")
    except RuntimeError:
        pass

    for echec in echecs:
        print(f"  !! {echec}")
    print(f"auto-test : {essais - len(echecs)}/{essais} verifications passees")
    return 1 if echecs else 0


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--chaine", choices=sorted(CHAINES))
    analyseur.add_argument("--slug")
    analyseur.add_argument("--csv", default="podcasts/queue-podcast.csv")
    analyseur.add_argument("--racine", default="~/LEXVOX-PODCASTS")
    analyseur.add_argument("--intro", help="force le fichier d'introduction")
    analyseur.add_argument("--corps", help="force le fichier NotebookLM")
    analyseur.add_argument("--outro",
                           help="force l'outro (sinon cherchee dans outro/)")
    analyseur.add_argument("--sans-outro", action="store_true",
                           help="monte l'episode SANS appel a l'action final")
    analyseur.add_argument("--segments",
                           help="dossier des 4 segments d'intro produits par "
                                "voix_script.py --segments (mode recommande : "
                                "jingle et relance enregistres une seule fois)")
    analyseur.add_argument("--musique", help="force le generique musical")
    analyseur.add_argument("--sans-musique", action="store_true",
                           help="monte l'episode sans generique musical")
    analyseur.add_argument("--duree-musique", type=float,
                           default=MUSIQUE_DUREE,
                           help="secondes de generique conservees en tete")
    analyseur.add_argument("--licences", default=str(REGISTRE_LICENCES),
                           help="registre des licences de musique")
    analyseur.add_argument("--pause-segments", type=int,
                           default=PAUSE_SEGMENTS,
                           help="respiration entre segments d'intro, en ms")
    analyseur.add_argument("--debit", type=int, default=DEBIT_DEFAUT)
    analyseur.add_argument("--canaux", choices=("auto", "mono", "stereo"),
                           default="auto")
    analyseur.add_argument("--pause", type=int, default=PAUSE_DEFAUT,
                           help="respiration entre segments, en ms")
    analyseur.add_argument("--moteur", choices=("local", "api"),
                           default="local",
                           help="binaire local ou service ffmpeg distant")
    analyseur.add_argument("--config", default="podcasts/ffmpeg-api.json",
                           help="configuration du service (--moteur api)")
    analyseur.add_argument("--plateforme", default="[À DÉFINIR]")
    analyseur.add_argument("--json", help="ecrit le compte rendu en JSON")
    analyseur.add_argument("--dry-run", action="store_true")
    analyseur.add_argument("--garder-travail", action="store_true")
    analyseur.add_argument("--self-test", action="store_true")
    options = analyseur.parse_args()

    if options.self_test:
        return self_test()
    if not options.chaine or not options.slug:
        analyseur.error("--chaine et --slug sont requis")
    try:
        return traiter(options)
    except ErreurMoteur as erreur:
        print(f"\nECHEC — TRAITEMENT INTERROMPU (moteur) : {erreur}",
              file=sys.stderr)
        return 3
    except RuntimeError as erreur:
        print(f"\nECHEC — TRAITEMENT INTERROMPU : {erreur}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
