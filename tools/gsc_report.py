#!/usr/bin/env python3
"""Boucle de retour Search Console — diagnostic du corpus DEJA publie.

SQUELETTE (2026-08-27). Le pipeline LEXVOX est complet en PRODUCTION (termes
NeuronWriter avant redaction, Openlegi, QA, anti-cannibalisation) mais aveugle
APRES publication : rien ne mesure ce que deviennent les ~545 articles en
ligne. Cet outil comble ce trou. Il applique des seuils chiffres plutot que des
impressions generales, parce qu'un diagnostic SEO sans seuil produit une liste
de vingt recommandations, c'est-a-dire aucune decision.

  synthese         rapport court : au plus 3 actions, classees par gain
  chute            pages qui perdent le plus de CLICS EN VALEUR ABSOLUE
  decay            erosion lente : 2 periodes consecutives de baisse
  quickwins        positions 11-20 a fort volume d'impressions
  titres           CTR anormalement bas pour la position occupee
  cannibalisation  requetes captees par >= 2 de nos URLs
  reoptimiser      --keyword "<kw>" : une page capte-t-elle deja cet intent ?

`reoptimiser` est la sous-commande appelee par les deux files editoriales
(queue-aivf.json, queue-wp.json) avant de produire un article : si une page
recoit deja des impressions sur le mot-cle, l'item n'est pas un article neuf
mais une reoptimisation.

SOURCES DE DONNEES
  --api             API Search Console (searchanalytics.query, dimensions
                    requete x page). Les fenetres de comparaison sont calculees
                    seules : aucun export a faire. Requiert la propriete GSC
                    (action I-03) et la cle d'un compte de service dans
                    GSC_SERVICE_ACCOUNT_JSON — jamais committee.
  --csv <dossier>   export Search Console (CSV/TSV), pour travailler sans API.
                    Repeter l'option pour comparer des periodes, de la plus
                    recente a la plus ancienne (chute = 2 periodes, decay = 3).

Tant que la propriete n'existe pas ou que la cle manque, `--api` s'arrete en
code 2 avec la marche a suivre : jamais de rapport vide, qui aurait l'allure
d'un site en bonne sante.

Un export de l'interface GSC ne contient PAS le croisement requete x page :
`cannibalisation` et `reoptimiser` en ont besoin et ne sont donc exploitables
qu'en mode --api (ou via un export Looker Studio portant les deux colonnes).
Les commandes le signalent au lieu de rendre un resultat trompeur.

Usage :
  python3 tools/gsc_report.py synthese --api
  python3 tools/gsc_report.py decay --api --jours 90
  python3 tools/gsc_report.py reoptimiser --keyword "prejudice d'agrement" --api
  python3 tools/gsc_report.py quickwins --csv exports/2026-08/
  python3 tools/gsc_report.py chute --csv exports/2026-08/ --csv exports/2026-07/

Codes retour : 0 = rapport rendu, 1 = erreur d'usage, 2 = source indisponible.
"""
import argparse
import base64
import csv
import json
import os
import sys
import time
import urllib.parse
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import requests

# --- Seuils de la methode -------------------------------------------------
# Chacun elimine du bruit. Les valeurs viennent de la pratique SEO courante ;
# les ajuster ici, jamais au cas par cas dans un rapport.

# Cannibalisation : sous 50 impressions, deux URLs sur une meme requete
# relevent du hasard, pas d'un conflit reel.
SEUIL_CANNIBALISATION_IMPRESSIONS = 50
# Quick wins : page 2 (positions 11-20) avec assez de volume pour que gagner
# quelques places rapporte vraiment.
QUICKWIN_POSITION = (10.0, 20.0)
QUICKWIN_IMPRESSIONS = 200
# Titres : on ne signale qu'un CTR tombe sous la MOITIE de l'attendu pour la
# position — en dessous, c'est de la variation normale.
CTR_RATIO_ALERTE = 0.5
CTR_MIN_IMPRESSIONS = 100
# Decay : une baisse isolee est du bruit ; deux periodes consecutives de baisse
# sont le seul signal fiable d'une erosion reelle.
DECAY_PERIODES_CONSECUTIVES = 2
# Un rapport se termine par des decisions, pas par un inventaire.
MAX_ACTIONS = 3

# --- API Search Console ---------------------------------------------------
GSC_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
GSC_TOKEN_URL = "https://oauth2.googleapis.com/token"
GSC_API = "https://searchconsole.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query"
# Propriete de DOMAINE (prefixe sc-domain:) : elle couvre http/https, www et
# tous les sous-domaines d'un coup, et se verifie par un enregistrement DNS —
# donc sans toucher au frontend Next.js/Sanity servi en production.
GSC_SITE_DEFAUT = "sc-domain:lexvox-victime.com"
# Search Console publie avec ~2-3 jours de retard : inclure ces jours ferait
# passer un delai de publication pour une chute de trafic.
GSC_DECALAGE_JOURS = 3
GSC_MAX_LIGNES = 25000
GSC_JOURS_DEFAUT = 28

# CTR moyen observe par position sur la SERP (ordre de grandeur, toutes
# requetes confondues). Sert uniquement de reference relative pour reperer une
# anomalie : ce n'est pas un objectif a atteindre.
CTR_ATTENDU = {
    1: 0.28, 2: 0.15, 3: 0.11, 4: 0.08, 5: 0.06,
    6: 0.05, 7: 0.04, 8: 0.03, 9: 0.03, 10: 0.02,
}
CTR_ATTENDU_AU_DELA = 0.01

# Noms de colonnes acceptes dans les exports (FR et EN, GSC et Looker Studio).
COLONNES = {
    "query": ("query", "requete", "requête", "requetes", "requêtes les plus fréquentes", "top queries"),
    "page": ("page", "url", "adresse", "pages les plus populaires", "top pages"),
    "clicks": ("clicks", "clics", "clics", "nombre de clics"),
    "impressions": ("impressions", "affichages", "nombre d'impressions"),
    "ctr": ("ctr", "taux de clics", "click through rate"),
    "position": ("position", "position moyenne", "average position"),
    "date": ("date", "jour"),
}


@dataclass
class Ligne:
    """Une ligne de performance normalisee, quelle que soit la source."""
    query: str
    page: str
    clicks: float
    impressions: float
    ctr: float
    position: float
    date: str = ""


def ctr_attendu(position: float) -> float:
    return CTR_ATTENDU.get(int(round(position)), CTR_ATTENDU_AU_DELA)


# --- Chargement des donnees ----------------------------------------------

def _norme(entete: str) -> str:
    return entete.strip().lower().lstrip("﻿")


def _mapper_colonnes(entetes: list[str]) -> dict[str, int]:
    trouve = {}
    for i, brut in enumerate(entetes):
        e = _norme(brut)
        for champ, alias in COLONNES.items():
            if champ not in trouve and e in alias:
                trouve[champ] = i
    return trouve


def _nombre(valeur: str) -> float:
    """Tolere les formats FR ('1 234', '12,5 %', '3,4')."""
    v = (valeur or "").strip().replace(" ", "").replace(" ", "")
    v = v.replace("%", "").replace(",", ".")
    try:
        return float(v) if v else 0.0
    except ValueError:
        return 0.0


def _taux(brut: str, clicks: float, impressions: float) -> float:
    """CTR en fraction (0.04 = 4 %).

    On le RECALCULE des que clics et impressions sont connus : la colonne CTR
    d'un export est ambigue — '0,9' vaut 0,9 % chez Search Console mais serait
    lu comme 90 % si on le prenait pour une fraction — et cette ambiguite
    fausserait silencieusement tout le rapport.
    """
    if impressions:
        return clicks / impressions
    valeur = _nombre(brut)
    if "%" in (brut or ""):
        return valeur / 100
    return valeur / 100 if valeur > 1 else valeur


def charger_csv(dossier: Path) -> list[Ligne]:
    """Charge tous les CSV/TSV d'un dossier d'export Search Console."""
    if not dossier.exists():
        sys.exit(f"ERREUR : dossier d'export introuvable : {dossier}")
    fichiers = sorted(
        f for f in dossier.iterdir()
        if f.suffix.lower() in (".csv", ".tsv") and f.is_file()
    )
    if not fichiers:
        sys.exit(f"ERREUR : aucun .csv/.tsv dans {dossier}")

    lignes: list[Ligne] = []
    for f in fichiers:
        texte = f.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        if not texte:
            continue
        delim = "\t" if f.suffix.lower() == ".tsv" or "\t" in texte[0] else ","
        lecteur = csv.reader(texte, delimiter=delim)
        entetes = next(lecteur, None)
        if not entetes:
            continue
        cols = _mapper_colonnes(entetes)
        if "impressions" not in cols and "clicks" not in cols:
            continue  # onglet sans donnee de performance (Devices, Countries...)

        def champ(row, nom, defaut=""):
            i = cols.get(nom)
            return row[i] if i is not None and i < len(row) else defaut

        for row in lecteur:
            if not any(c.strip() for c in row):
                continue
            impressions = _nombre(champ(row, "impressions"))
            clicks = _nombre(champ(row, "clicks"))
            ctr = _taux(champ(row, "ctr"), clicks, impressions)
            lignes.append(Ligne(
                query=champ(row, "query").strip(),
                page=champ(row, "page").strip(),
                clicks=clicks,
                impressions=impressions,
                ctr=ctr,
                position=_nombre(champ(row, "position")),
                date=champ(row, "date").strip(),
            ))
    return lignes


def _source_indisponible(message: str) -> None:
    """Sort en code 2 : source manquante, distinct d'une erreur d'usage (1)."""
    print(message, file=sys.stderr)
    sys.exit(2)


def _compte_de_service() -> dict:
    """Cle du compte de service, depuis l'environnement UNIQUEMENT.

    `GSC_SERVICE_ACCOUNT_JSON` porte soit le JSON lui-meme, soit le chemin du
    fichier. Jamais dans le depot : c'est une cle privee (regle 5 du CLAUDE.md,
    ecrite apres qu'un jeton a du etre purge du dashboard).
    """
    brut = os.environ.get("GSC_SERVICE_ACCOUNT_JSON", "").strip()
    if not brut:
        _source_indisponible(
            "IDENTIFIANTS ABSENTS : la variable d'environnement\n"
            "  GSC_SERVICE_ACCOUNT_JSON n'est pas definie (JSON du compte de\n"
            "  service, ou chemin vers ce fichier).\n"
            "\n"
            "  Marche a suivre dans .claude/skills/seo-feedback/SKILL.md,\n"
            "  section « Brancher l'API ». Ne jamais committer cette cle."
        )
    if not brut.lstrip().startswith("{"):
        chemin = Path(brut).expanduser()
        if not chemin.exists():
            _source_indisponible(
                f"IDENTIFIANTS ILLISIBLES : {chemin} introuvable.\n"
                "  GSC_SERVICE_ACCOUNT_JSON doit porter le JSON du compte de\n"
                "  service ou le chemin d'un fichier existant."
            )
        brut = chemin.read_text(encoding="utf-8")
    try:
        compte = json.loads(brut)
    except json.JSONDecodeError as e:
        _source_indisponible(f"IDENTIFIANTS ILLISIBLES : JSON invalide ({e}).")
    manquants = [c for c in ("client_email", "private_key") if not compte.get(c)]
    if manquants:
        _source_indisponible(
            f"IDENTIFIANTS INCOMPLETS : champ(s) {', '.join(manquants)} absent(s) "
            "du JSON du compte de service."
        )
    return compte


def _b64url(donnees: bytes) -> str:
    return base64.urlsafe_b64encode(donnees).rstrip(b"=").decode("ascii")


def jeton_acces(compte: dict) -> str:
    """Signe un JWT RS256 et l'echange contre un jeton d'acces OAuth2.

    Implemente a la main plutot qu'avec google-auth : le paquet n'est pas
    installe, et la boucle JWT -> jeton tient en quinze lignes avec
    `cryptography`.
    """
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except Exception as e:
        # Une installation partielle de `cryptography` (backend cffi absent)
        # remonte sinon un panic Rust illisible.
        _source_indisponible(
            f"DEPENDANCE MANQUANTE : `cryptography` inutilisable ({type(e).__name__}).\n"
            "  Installer :  python3 -m pip install cffi cryptography\n"
            "  (necessaire seulement pour --api ; le mode --csv n'en depend pas.)"
        )

    maintenant = int(time.time())
    entete = {"alg": "RS256", "typ": "JWT"}
    revendications = {
        "iss": compte["client_email"],
        "scope": GSC_SCOPE,
        "aud": GSC_TOKEN_URL,
        "iat": maintenant,
        "exp": maintenant + 3600,
    }
    corps = ".".join(
        _b64url(json.dumps(x, separators=(",", ":")).encode("utf-8"))
        for x in (entete, revendications)
    ).encode("ascii")

    cle = serialization.load_pem_private_key(
        compte["private_key"].encode("utf-8"), password=None)
    signature = cle.sign(corps, padding.PKCS1v15(), hashes.SHA256())
    assertion = f"{corps.decode('ascii')}.{_b64url(signature)}"

    reponse = requests.post(
        GSC_TOKEN_URL,
        data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
              "assertion": assertion},
        timeout=30,
    )
    if reponse.status_code != 200:
        _source_indisponible(
            f"AUTHENTIFICATION REFUSEE (HTTP {reponse.status_code}) : "
            f"{reponse.text[:300]}\n"
            "  Verifier que l'API Search Console est activee sur le projet "
            "Google Cloud\n  et que l'heure systeme est juste (un JWT expire "
            "est refuse sans autre explication)."
        )
    return reponse.json()["access_token"]


def _fenetre(fin_decalage: int, jours: int, index: int) -> tuple[str, str]:
    """Fenetre glissante n° `index` (0 = la plus recente), en dates ISO.

    `fin_decalage` recule la fin de quelques jours : Search Console publie ses
    donnees avec environ 2 a 3 jours de retard, et inclure ces jours-la ferait
    passer un simple delai de publication pour une chute de trafic.
    """
    fin = date.today() - timedelta(days=fin_decalage + index * jours)
    debut = fin - timedelta(days=jours - 1)
    return debut.isoformat(), fin.isoformat()


def charger_api(site: str, jours: int, index: int = 0) -> list[Ligne]:
    """Une fenetre de donnees reelles, croisement requete x page compris."""
    compte = _compte_de_service()
    jeton = jeton_acces(compte)
    debut, fin = _fenetre(GSC_DECALAGE_JOURS, jours, index)
    url = GSC_API.format(site=urllib.parse.quote(site, safe=""))

    lignes: list[Ligne] = []
    depart = 0
    while True:
        reponse = requests.post(
            url,
            headers={"Authorization": f"Bearer {jeton}"},
            json={"startDate": debut, "endDate": fin,
                  "dimensions": ["query", "page"], "type": "web",
                  "rowLimit": GSC_MAX_LIGNES, "startRow": depart},
            timeout=120,
        )
        if reponse.status_code == 403:
            _source_indisponible(
                f"ACCES REFUSE a la propriete « {site} » (HTTP 403).\n"
                f"  Le compte de service {compte['client_email']}\n"
                "  doit etre ajoute comme utilisateur de la propriete dans\n"
                "  Search Console (Parametres > Utilisateurs et autorisations).\n"
                "  Verifier aussi la forme du site : propriete de domaine =\n"
                "  `sc-domain:lexvox-victime.com`, prefixe d'URL = l'URL complete."
            )
        if reponse.status_code == 404:
            _source_indisponible(
                f"PROPRIETE INTROUVABLE : « {site} » (HTTP 404).\n"
                "  L'action I-03 (creer la propriete Search Console) est-elle "
                "faite ?\n  Sinon aucune donnee n'existe : ne rien inventer, "
                "utiliser --csv ou attendre."
            )
        if reponse.status_code != 200:
            _source_indisponible(
                f"API Search Console : HTTP {reponse.status_code} — "
                f"{reponse.text[:300]}")

        rangs = reponse.json().get("rows", [])
        for r in rangs:
            cles = r.get("keys", ["", ""])
            lignes.append(Ligne(
                query=cles[0] if len(cles) > 0 else "",
                page=cles[1] if len(cles) > 1 else "",
                clicks=float(r.get("clicks", 0)),
                impressions=float(r.get("impressions", 0)),
                ctr=float(r.get("ctr", 0)),
                position=float(r.get("position", 0)),
                date=f"{debut}..{fin}",
            ))
        if len(rangs) < GSC_MAX_LIGNES:
            break
        depart += GSC_MAX_LIGNES
    return lignes


def charger(args) -> list[Ligne]:
    if args.api:
        return charger_api(args.site, args.jours)
    if not args.csv:
        sys.exit("ERREUR : preciser au moins une source (--csv <dossier> ou --api).")
    return charger_csv(Path(args.csv[0]))


def charger_periodes(args, minimum: int) -> list[list[Ligne]]:
    """Periodes comparables, de la plus RECENTE a la plus ANCIENNE.

    En mode API, les fenetres sont deduites de `--jours` : aucun export a faire,
    c'est tout l'interet d'avoir branche l'API.
    """
    if args.api:
        return [charger_api(args.site, args.jours, i) for i in range(minimum)]
    if len(args.csv or []) < minimum:
        sys.exit(
            f"ERREUR : cette commande compare {minimum} periodes.\n"
            f"  Repeter --csv, de la plus RECENTE a la plus ANCIENNE :\n"
            f"  python3 tools/gsc_report.py {args.commande} "
            + " ".join(f"--csv exports/p{i+1}/" for i in range(minimum))
            + "\n  Ou utiliser --api : les fenetres sont alors calculees seules."
        )
    return [charger_csv(Path(d)) for d in args.csv[:minimum]]


def _exiger_requete_et_page(lignes: list[Ligne], commande: str) -> None:
    """Refuse de conclure quand la source ne porte pas le croisement necessaire."""
    if not any(l.query and l.page for l in lignes):
        _source_indisponible(
            f"SOURCE INSUFFISANTE : `{commande}` a besoin du croisement\n"
            "  requete x page, qu'un export standard de l'interface GSC ne\n"
            "  contient pas (les onglets Requetes et Pages sont separes).\n"
            "\n"
            "  Deux voies : brancher l'API (dimensions ['query','page'], cf.\n"
            "  action I-03), ou fournir un export Looker Studio portant les\n"
            "  deux colonnes. Sans cela, tout resultat serait devine."
        )


# --- Agregation -----------------------------------------------------------

def agreger(lignes: list[Ligne], par: str) -> dict[str, Ligne]:
    """Regroupe par 'page' ou 'query' ; position et CTR ponderes par impressions."""
    cumul: dict[str, list[Ligne]] = {}
    for l in lignes:
        cle = getattr(l, par)
        if cle:
            cumul.setdefault(cle, []).append(l)

    resultat = {}
    for cle, groupe in cumul.items():
        clicks = sum(l.clicks for l in groupe)
        impressions = sum(l.impressions for l in groupe)
        poids = impressions or len(groupe)
        position = sum(l.position * (l.impressions or 1) for l in groupe) / poids
        resultat[cle] = Ligne(
            query=cle if par == "query" else "",
            page=cle if par == "page" else "",
            clicks=clicks,
            impressions=impressions,
            ctr=clicks / impressions if impressions else 0.0,
            position=position,
        )
    return resultat


# --- Analyses -------------------------------------------------------------

def analyse_quickwins(lignes: list[Ligne]) -> list[dict]:
    """Positions 11-20 a fort volume : le meilleur rapport effort/resultat."""
    bas, haut = QUICKWIN_POSITION
    trouve = []
    for cle, l in agreger(lignes, "query" if not any(x.page for x in lignes) else "page").items():
        if bas < l.position <= haut and l.impressions >= QUICKWIN_IMPRESSIONS:
            trouve.append({
                "libelle": cle,
                "position": round(l.position, 1),
                "impressions": int(l.impressions),
                "clics": int(l.clicks),
                "gain_estime": int(l.impressions * (ctr_attendu(8) - l.ctr)),
            })
    return sorted(trouve, key=lambda d: -d["gain_estime"])


def analyse_titres(lignes: list[Ligne]) -> list[dict]:
    """CTR tombe sous la moitie de l'attendu pour la position : title et meta."""
    trouve = []
    for cle, l in agreger(lignes, "page" if any(x.page for x in lignes) else "query").items():
        if l.impressions < CTR_MIN_IMPRESSIONS or l.position <= 0:
            continue
        attendu = ctr_attendu(l.position)
        if l.ctr < attendu * CTR_RATIO_ALERTE:
            trouve.append({
                "libelle": cle,
                "position": round(l.position, 1),
                "impressions": int(l.impressions),
                "ctr_pct": round(l.ctr * 100, 2),
                "ctr_attendu_pct": round(attendu * 100, 2),
                "clics_manques": int(l.impressions * (attendu - l.ctr)),
            })
    return sorted(trouve, key=lambda d: -d["clics_manques"])


def analyse_cannibalisation(lignes: list[Ligne]) -> list[dict]:
    """Requetes ou >= 2 de nos URLs depassent le seuil d'impressions."""
    _exiger_requete_et_page(lignes, "cannibalisation")
    par_requete: dict[str, dict[str, Ligne]] = {}
    for l in lignes:
        if l.query and l.page:
            par_requete.setdefault(l.query, {})
            deja = par_requete[l.query].get(l.page)
            if deja:
                deja.clicks += l.clicks
                deja.impressions += l.impressions
            else:
                par_requete[l.query][l.page] = Ligne(
                    l.query, l.page, l.clicks, l.impressions, l.ctr, l.position)

    conflits = []
    for requete, pages in par_requete.items():
        en_lice = [p for p in pages.values()
                   if p.impressions >= SEUIL_CANNIBALISATION_IMPRESSIONS]
        if len(en_lice) < 2:
            continue
        # Page cible : meilleure position ET meilleur CTR. Si les deux se
        # contredisent, on ne tranche pas a la place de l'editeur : on le dit.
        meilleure_position = min(en_lice, key=lambda p: p.position)
        meilleur_ctr = max(en_lice, key=lambda p: p.ctr)
        accord = meilleure_position.page == meilleur_ctr.page
        conflits.append({
            "requete": requete,
            "urls": [{
                "page": p.page,
                "impressions": int(p.impressions),
                "clics": int(p.clicks),
                "position": round(p.position, 1),
                "ctr": round(p.ctr * 100, 2),
            } for p in sorted(en_lice, key=lambda p: p.position)],
            "cible": meilleure_position.page if accord else None,
            "arbitrage": (
                "position et CTR designent la meme page"
                if accord else
                f"position -> {meilleure_position.page} mais CTR -> {meilleur_ctr.page} : "
                "trancher sur le sujet reellement traite, et le motiver"
            ),
            "impressions_en_jeu": int(sum(p.impressions for p in en_lice)),
        })
    return sorted(conflits, key=lambda d: -d["impressions_en_jeu"])


def analyse_reoptimiser(lignes: list[Ligne], keyword: str) -> list[dict]:
    """Une page capte-t-elle deja l'intent ? Porte d'entree des files."""
    _exiger_requete_et_page(lignes, "reoptimiser")
    mots = [m for m in keyword.lower().split() if len(m) > 2]
    captees: dict[str, Ligne] = {}
    for l in lignes:
        if not (l.query and l.page):
            continue
        q = l.query.lower()
        if all(m in q for m in mots):
            deja = captees.get(l.page)
            if deja:
                deja.clicks += l.clicks
                deja.impressions += l.impressions
                deja.position = min(deja.position, l.position)
            else:
                captees[l.page] = Ligne(l.query, l.page, l.clicks,
                                        l.impressions, l.ctr, l.position)
    return sorted(
        [{
            "page": p.page,
            "impressions": int(p.impressions),
            "clics": int(p.clicks),
            "meilleure_position": round(p.position, 1),
        } for p in captees.values()],
        key=lambda d: -d["impressions"],
    )


def analyse_chute(recente: list[Ligne], precedente: list[Ligne]) -> list[dict]:
    """Pages qui perdent le plus de clics EN VALEUR ABSOLUE, avec la cause.

    Trier par pourcentage est l'erreur classique : une page qui perd 80 % de
    12 clics n'est pas le sujet. Le volume absolu designe les deux ou trois
    pages qui expliquent l'essentiel de la chute.
    """
    par = "page" if any(l.page for l in recente) else "query"
    avant, apres = agreger(precedente, par), agreger(recente, par)

    pertes = []
    for cle, a in avant.items():
        b = apres.get(cle)
        clics_perdus = a.clicks - (b.clicks if b else 0)
        if clics_perdus <= 0:
            continue
        if b is None:
            cause = "sortie de l'index ou de l'export : verifier l'indexation"
        elif b.position > a.position + 1:
            cause = f"perte de position ({a.position:.1f} -> {b.position:.1f})"
        elif b.impressions < a.impressions * 0.8:
            cause = (f"perte d'impressions a position stable "
                     f"({int(a.impressions)} -> {int(b.impressions)}) : "
                     "perte de visibilite sur la requete, pas de classement")
        elif b.ctr < a.ctr * 0.8:
            cause = (f"chute de CTR ({a.ctr*100:.1f} % -> {b.ctr*100:.1f} %) "
                     "a position stable : title et meta description")
        else:
            cause = "aucune cause dominante mesuree — ne pas conclure"
        pertes.append({
            "libelle": cle,
            "clics_perdus": int(round(clics_perdus)),
            "clics_avant": int(a.clicks),
            "clics_apres": int(b.clicks) if b else 0,
            "cause": cause,
        })
    return sorted(pertes, key=lambda d: -d["clics_perdus"])


def analyse_decay(periodes: list[list[Ligne]]) -> list[dict]:
    """Erosion lente : baisse sur DECAY_PERIODES_CONSECUTIVES periodes.

    Un article ne meurt pas d'un coup : il perd quelques points par mois
    pendant des mois, sous le seuil de visibilite d'un rapport global. Deux
    periodes consecutives de baisse distinguent l'erosion de la fluctuation.
    """
    par = "page" if any(l.page for l in periodes[0]) else "query"
    series = [agreger(p, par) for p in periodes]   # [0] = la plus recente

    declins = []
    for cle in series[0]:
        clics = [s.get(cle).clicks if s.get(cle) else 0.0 for s in series]
        # series[0] recente -> comparaisons successives vers le passe
        baisses = sum(1 for i in range(len(clics) - 1) if clics[i] < clics[i + 1])
        if baisses >= DECAY_PERIODES_CONSECUTIVES:
            declins.append({
                "libelle": cle,
                "clics_de_la_plus_recente_a_la_plus_ancienne": [int(c) for c in clics],
                "clics_encore_en_jeu": int(clics[0]),
                "perte_totale": int(clics[-1] - clics[0]),
                "note": "controler la saisonnalite avant d'agir "
                        "(meme baisse a la meme periode l'an dernier ?)",
            })
    return sorted(declins, key=lambda d: -d["clics_encore_en_jeu"])


# --- Rendu ----------------------------------------------------------------

def titre(texte: str) -> None:
    print(f"\n{texte}\n{'=' * len(texte)}")


def rendre(items: list[dict], vide: str, limite: int = 20) -> None:
    if not items:
        print(f"  {vide}")
        return
    for i, item in enumerate(items[:limite], start=1):
        principal = item.get("libelle") or item.get("requete") or item.get("page")
        print(f"\n  {i}. {principal}")
        for k, v in item.items():
            if k in ("libelle", "requete", "page"):
                continue
            if isinstance(v, list) and not any(isinstance(s, dict) for s in v):
                print(f"       {k} : {' | '.join(str(s) for s in v)}")
            elif isinstance(v, list):
                print(f"       {k} :")
                for sous in v:
                    if isinstance(sous, dict):
                        tete = sous.get("page") or sous.get("libelle") or ""
                        detail = ", ".join(f"{sk} {sv}" for sk, sv in sous.items()
                                           if sk not in ("page", "libelle"))
                        print(f"         - {tete} ({detail})")
                    else:
                        print(f"         - {sous}")
            else:
                print(f"       {k} : {v}")
    if len(items) > limite:
        print(f"\n  … {len(items) - limite} autre(s) non affiche(s) "
              f"(les plus gros volumes sont en tete).")


def rendre_synthese(recente: list[Ligne], precedente: list[Ligne] | None) -> None:
    """Rapport court : ce qui a bouge, puis AU PLUS 3 actions.

    La contrainte des 3 actions fait tout le travail : sans elle, un rapport
    rend vingt recommandations, c'est-a-dire un tableau de bord de plus a
    traiter, et rien ne se decide.
    """
    titre("Synthese Search Console")
    clics = sum(l.clicks for l in recente)
    impressions = sum(l.impressions for l in recente)
    print(f"  Clics : {int(clics)}   Impressions : {int(impressions)}   "
          f"CTR : {clics / impressions * 100:.2f} %" if impressions else "  (aucune impression)")
    if precedente:
        avant = sum(l.clicks for l in precedente)
        delta = clics - avant
        print(f"  Evolution : {delta:+.0f} clics vs periode precedente "
              f"({delta / avant * 100:+.1f} %)" if avant else "")

    # (clics en jeu, texte) — le classement se fait sur le gain mesure, seul
    # critere qui permette de dire laquelle des trois passe en premier.
    actions: list[tuple[int, str]] = []
    for qw in analyse_quickwins(recente)[:2]:
        actions.append((qw["gain_estime"],
                        f"Pousser « {qw['libelle']} » (position {qw['position']}, "
                        f"{qw['impressions']} impressions) : "
                        f"~{qw['gain_estime']} clics/mois a gagner"))
    for t in analyse_titres(recente)[:1]:
        actions.append((t["clics_manques"],
                        f"Reecrire le title de « {t['libelle']} » "
                        f"(CTR {t['ctr_pct']} % pour {t['ctr_attendu_pct']} % attendu "
                        f"en position {t['position']}) : "
                        f"~{t['clics_manques']} clics/mois manques"))
    if precedente:
        for c in analyse_chute(recente, precedente)[:1]:
            actions.append((c["clics_perdus"],
                            f"Traiter la chute de « {c['libelle']} » "
                            f"(-{c['clics_perdus']} clics) : {c['cause']}"))

    titre(f"Les {MAX_ACTIONS} actions de la semaine")
    if not actions:
        print("  Rien de mesurable a traiter sur cette periode.")
    for i, (_, a) in enumerate(sorted(actions, reverse=True)[:MAX_ACTIONS], start=1):
        print(f"  {i}. {a}")
    print("\n  (Rapport volontairement limite a 3 actions : au-dela, on ne "
          "hierarchise plus, on inventorie.)")


# --- CLI ------------------------------------------------------------------

def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        prog="gsc_report.py",
        description="Boucle de retour Search Console sur le corpus publie.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("commande", choices=[
        "synthese", "chute", "decay", "quickwins",
        "titres", "cannibalisation", "reoptimiser",
    ])
    p.add_argument("--csv", action="append", metavar="DOSSIER",
                   help="dossier d'export GSC ; repeter de la periode la plus "
                        "RECENTE a la plus ANCIENNE")
    p.add_argument("--api", action="store_true",
                   help="source API Search Console (cle : GSC_SERVICE_ACCOUNT_JSON)")
    p.add_argument("--site", default=os.environ.get("GSC_SITE_URL", GSC_SITE_DEFAUT),
                   metavar="PROPRIETE",
                   help=f"propriete Search Console (defaut : {GSC_SITE_DEFAUT})")
    p.add_argument("--jours", type=int, default=GSC_JOURS_DEFAUT, metavar="N",
                   help=f"longueur d'une periode en mode --api (defaut : {GSC_JOURS_DEFAUT})")
    p.add_argument("--keyword", help="mot-cle a tester (commande reoptimiser)")
    args = p.parse_args(argv)

    if args.commande == "reoptimiser" and not args.keyword:
        p.error("--keyword est requis pour la commande reoptimiser")

    if args.commande == "synthese":
        if args.api:
            # Deux fenetres : la synthese compare toujours a la periode d'avant.
            periodes = [charger_api(args.site, args.jours, i) for i in range(2)]
        else:
            periodes = [charger_csv(Path(d)) for d in (args.csv or [])]
        if not periodes:
            sys.exit("ERREUR : preciser au moins une source (--csv <dossier> ou --api).")
        rendre_synthese(periodes[0], periodes[1] if len(periodes) > 1 else None)
        return 0

    if args.commande == "chute":
        recente, precedente = charger_periodes(args, 2)
        titre("Pages qui perdent le plus de clics (valeur absolue)")
        rendre(analyse_chute(recente, precedente),
               "Aucune perte de clics mesuree entre les deux periodes.")
        return 0

    if args.commande == "decay":
        periodes = charger_periodes(args, 3)
        titre(f"Erosion lente ({DECAY_PERIODES_CONSECUTIVES} periodes consecutives de baisse)")
        rendre(analyse_decay(periodes),
               "Aucune page en erosion continue sur les periodes fournies.")
        return 0

    lignes = charger(args)
    if not lignes:
        sys.exit("ERREUR : aucune ligne de performance lue dans l'export.")

    if args.commande == "quickwins":
        titre(f"Quick wins — positions {QUICKWIN_POSITION[0] + 1:.0f}-{QUICKWIN_POSITION[1]:.0f} "
              f"(seconde page), > {QUICKWIN_IMPRESSIONS} impressions")
        rendre(analyse_quickwins(lignes),
               "Aucune page en seconde page avec un volume suffisant.")
    elif args.commande == "titres":
        titre(f"Titles a reecrire — CTR sous {CTR_RATIO_ALERTE:.0%} de l'attendu")
        rendre(analyse_titres(lignes),
               "Aucun CTR anormalement bas pour la position occupee.")
    elif args.commande == "cannibalisation":
        titre(f"Cannibalisation — >= 2 URLs a plus de "
              f"{SEUIL_CANNIBALISATION_IMPRESSIONS} impressions")
        conflits = analyse_cannibalisation(lignes)
        rendre(conflits, "Aucun conflit au-dessus du seuil de bruit.")
        if conflits:
            print("\n  Ne jamais supprimer une page qui recoit des clics : "
                  "desoptimiser, fusionner avec 301, ou lier vers la cible.")
    elif args.commande == "reoptimiser":
        titre(f"Intent deja capte ? — « {args.keyword} »")
        captees = analyse_reoptimiser(lignes, args.keyword)
        if captees:
            rendre(captees, "")
            print("\n  VERDICT : une page capte deja cet intent. L'item de la file "
                  "n'est PAS un article neuf.\n"
                  "  -> statut \"reoptimiser\" + \"reoptimise_url\", et enrichir la "
                  "page ci-dessus (sections manquantes)\n"
                  "     plutot que d'en publier une seconde qui la cannibaliserait.")
        else:
            print("  Aucune page ne recoit d'impressions sur ce mot-cle.")
            print("\n  VERDICT : intent libre — produire l'article neuf, apres le "
                  "controle de slug (GROQ Sanity / REST WP).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
