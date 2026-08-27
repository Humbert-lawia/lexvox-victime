#!/usr/bin/env python3
"""Controle qualite d'un article produit selon le PIPELINE LEXVOX-AIVF.

Complete tools/preflight.py (SEO de base) en verifiant les marqueurs de
differenciation face a AIVF imposes par le gabarit augmente :

  1. Analyse jurisprudentielle VERIFIEE : >= 1 bloc <div class="juris-block">,
     et CHAQUE bloc doit contenir un backlink hypertexte (<a href> vers la
     source, typiquement Legifrance) ; l'article doit porter autant de
     marqueurs de verification Openlegi (<!-- OPENLEGI ... -->) que de blocs.
  2. Donnees : >= 2 tableaux <table class="data-table">.
  3. Infographie : >= 1 <figure class="infographic"> contenant un <svg>.
  4. Couverture d'intent : >= 5 sections <h2> ET >= 6 questions FAQ (<details>).
  5. Optimisation NeuronWriter (NON NEGOCIABLE) : marqueur
     <!-- NEURONWRITER SCORE: N ... --> present et N >= 85. Exception :
     derogation editoriale documentee DANS le marqueur (mention "derogation"
     + contexte, ex. "derogation >80 apres 15 loops, plafond SERP") acceptee
     si N > 80 — trace ecrite obligatoire, jamais de derogation implicite.
  6. Plancher de mots (chrome exclu) : >= 1900 mots utiles pour TOUT article
     (limite non negociable), >= 2500 pour un pilier. Le volume peut monter
     au-dessus de 1900 si cela ameliore le score, jamais descendre en dessous.

En plus des controles bloquants, l'outil rend des AVERTISSEMENTS non bloquants
sur la citabilite des reponses FAQ (chaque reponse doit ouvrir sur une phrase
autosuffisante, comprehensible sans avoir lu la question — c'est ce format que
les moteurs de reponse IA reprennent). Mesure du 2026-08-27 : 46 % des reponses
du corpus deja publie ouvrent sur "Oui.", "Non." ou une anaphore ; le controle
reste donc consultatif tant que ce stock n'est pas repris, pour ne pas rendre
la CI rouge sur l'existant. Il ne change pas le code retour.

Usage :
  python3 tools/qa_article_aivf.py actualites/mon-article.html
  python3 tools/qa_article_aivf.py actualites/mon-hub.html --pilier
  python3 tools/qa_article_aivf.py a.html b.html          # lot

Code retour 0 = conforme, 1 = au moins un article non conforme.
"""
import re
import sys
from html import unescape as html_unescape
from pathlib import Path

TAG_RE = re.compile(r"<[^>]+>")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
# blocs de "chrome" (menu, en-tete, pied) a exclure du comptage de mots utiles
CHROME_RE = re.compile(r"<(nav|header|footer)[^>]*>.*?</\1>", re.S | re.I)
BAR_RE = re.compile(r'<div[^>]*class="[^"]*reassurance-bar[^"]*"[^>]*>.*?</div>', re.S | re.I)
JURIS_RE = re.compile(r'<div[^>]*class="[^"]*juris-block[^"]*"[^>]*>(.*?)</div>', re.S | re.I)
HREF_RE = re.compile(r'<a[^>]+href="https?://', re.I)

# --- Citabilite des reponses FAQ (avertissements, non bloquant) -------------
DETAILS_RE = re.compile(r"<details[^>]*>(.*?)</details>", re.S | re.I)
SUMMARY_RE = re.compile(r"<summary[^>]*>(.*?)</summary>", re.S | re.I)
# Longueur plancher d'une phrase d'ouverture qui porte sujet + affirmation.
FAQ_MIN_OPENING = 60
# Ouvertures qui ne se comprennent qu'en ayant lu la question juste au-dessus.
FAQ_ANAPHORA_RE = re.compile(
    r"^(?:oui|non|si)\s*[.!]"                       # "Oui." / "Non." isoles
    r"|^(?:il|elle|ils|elles|on|cela|ceci|ca)\b"
    r"|^c(?:'|’)est\b|^ce\s+(?:sont|n(?:'|’)est)\b"
    r"|^(?:cette|cet|ces|ce)\s+\w+"
    r"|^(?:celui|celle|ceux|celles)\b"
    r"|^(?:leur|leurs|son|sa|ses)\b",
    re.I,
)


def content_word_count(html: str) -> int:
    """Mots de contenu visible, hors script/style/commentaires ET hors chrome
    (nav/header/footer/barre de reassurance) — evite les faux positifs."""
    text = COMMENT_RE.sub(" ", html)
    text = SCRIPT_STYLE_RE.sub(" ", text)
    text = CHROME_RE.sub(" ", text)
    text = BAR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return len(text.split())


def _plain(fragment: str) -> str:
    """Texte visible d'un fragment HTML, entites resolues, espaces normalises."""
    return re.sub(r"\s+", " ", html_unescape(TAG_RE.sub(" ", fragment))).strip()


def faq_citability(path: Path) -> list[str]:
    """Avertissements NON BLOQUANTS sur la citabilite des reponses FAQ.

    Regle du gabarit : chaque reponse ouvre sur une phrase autosuffisante,
    citable hors contexte (sujet + affirmation), parce que c'est ce fragment
    que ChatGPT, Perplexity ou Gemini reprennent quand ils citent la page.
    Une reponse qui commence par "Oui.", "Non." ou "C'est le poste qui..."
    perd tout sens des qu'elle est extraite de la page.

    Deux signaux, volontairement grossiers pour rester lisibles :
      - ouverture anaphorique (pronom ou demonstratif renvoyant a la question) ;
      - phrase d'ouverture trop courte pour porter sujet ET affirmation.
    """
    warnings = []
    doc = path.read_text(encoding="utf-8", errors="ignore")
    for i, block in enumerate(DETAILS_RE.findall(doc), start=1):
        question = _plain(SUMMARY_RE.search(block).group(1)) if SUMMARY_RE.search(block) else f"question {i}"
        answer = _plain(SUMMARY_RE.sub(" ", block))
        if not answer:
            continue
        m = re.search(r"^(.*?[.!?])(?:\s|$)", answer)
        opening = (m.group(1) if m else answer).strip()
        reasons = []
        if FAQ_ANAPHORA_RE.match(opening):
            reasons.append("ouverture anaphorique (ne se comprend qu'avec la question)")
        if len(opening) < FAQ_MIN_OPENING:
            reasons.append(f"phrase d'ouverture de {len(opening)} car. (< {FAQ_MIN_OPENING})")
        if reasons:
            warnings.append(
                f"FAQ « {question[:60]} » : {' + '.join(reasons)} — "
                f"ouverture actuelle : \"{opening[:80]}\""
            )
    return warnings


def check(path: Path, pilier: bool) -> list[str]:
    problems = []
    html = path.read_text(encoding="utf-8", errors="ignore")

    # 1. Bloc(s) jurisprudentiel(s) verifie(s)
    juris_blocks = JURIS_RE.findall(html)
    if len(juris_blocks) < 1:
        problems.append("aucun bloc d'analyse jurisprudentielle (<div class=\"juris-block\">)")
    else:
        sans_backlink = sum(1 for b in juris_blocks if not HREF_RE.search(b))
        if sans_backlink:
            problems.append(
                f"{sans_backlink} bloc(s) juris sans backlink hypertexte vers la source "
                "(<a href=\"https://...\"> Legifrance attendu)"
            )
        markers = len(re.findall(r"<!--\s*OPENLEGI", html, re.I))
        if markers < len(juris_blocks):
            problems.append(
                f"{markers} marqueur(s) de verification Openlegi (<!-- OPENLEGI ... -->) "
                f"pour {len(juris_blocks)} bloc(s) juris : chaque decision doit etre verifiee via Openlegi"
            )

    # 2. Tableaux
    tables = len(re.findall(r'<table[^>]*class="[^"]*data-table', html))
    if tables < 2:
        problems.append(f"{tables} tableau(x) data-table (minimum 2 requis)")

    # 3. Infographie SVG inline
    figs = re.findall(r'<figure[^>]*class="[^"]*infographic[^"]*"[^>]*>(.*?)</figure>', html, re.S | re.I)
    if not any("<svg" in f.lower() for f in figs):
        problems.append("aucune infographie SVG inline (<figure class=\"infographic\"> avec <svg>)")

    # 4. Couverture d'intent (remplace le simple plancher de mots)
    n_h2 = len(re.findall(r"<h2[\s>]", html, re.I))
    if n_h2 < 5:
        problems.append(f"{n_h2} sections <h2> (minimum 5 pour couvrir l'intent)")
    n_faq = len(re.findall(r"<details[\s>]", html, re.I))
    if n_faq < 6:
        problems.append(f"{n_faq} questions FAQ <details> (minimum 6)")

    # 5. Optimisation NeuronWriter — score >= 85 (non negociable), sauf
    # derogation editoriale explicite ecrite dans le marqueur (score > 80).
    m = re.search(r"<!--\s*NEURONWRITER\s+SCORE:\s*([0-9]+(?:\.[0-9]+)?)(.*?)-->", html, re.I | re.S)
    if not m:
        problems.append(
            "aucun marqueur de score NeuronWriter (<!-- NEURONWRITER SCORE: N ... -->) : "
            "l'optimisation NeuronWriter >= 85 est obligatoire avant publication"
        )
    else:
        score = float(m.group(1))
        derog = re.search(r"d[ée]rogation", m.group(2), re.I)
        if score < 85 and not derog:
            problems.append(f"score NeuronWriter {m.group(1)} < 85 (seuil non negociable, "
                            "derogation possible >80 uniquement si documentee dans le marqueur)")
        elif score <= 80 and derog:
            problems.append(f"score NeuronWriter {m.group(1)} <= 80 : la derogation documentee "
                            "ne s'applique qu'au-dessus de 80")

    # 6. Plancher de mots (chrome exclu) — jamais moins de 1900 mots
    n = content_word_count(html)
    floor = 2500 if pilier else 1900
    if n < floor:
        kind = "pilier" if pilier else "feuille"
        problems.append(f"{n} mots utiles (minimum {floor} pour un {kind}, plancher absolu 1900, chrome exclu)")

    return problems


def main(argv: list[str]) -> int:
    pilier = "--pilier" in argv
    files = [a for a in argv if not a.startswith("--")]
    if not files:
        print("Usage : python3 tools/qa_article_aivf.py <fichier.html> [--pilier]")
        return 1

    total_ko = 0
    total_warn = 0
    print("QA article — standard PIPELINE LEXVOX-AIVF")
    for f in files:
        path = Path(f)
        if not path.exists():
            print(f"  ERREUR        {f} : fichier introuvable")
            total_ko += 1
            continue
        problems = check(path, pilier)
        if problems:
            total_ko += 1
            print(f"  NON CONFORME  {f}")
            for p in problems:
                print(f"      - {p}")
        else:
            print(f"  OK            {f}")
        for w in faq_citability(path):
            total_warn += 1
            print(f"      ~ (avertissement) {w}")

    print(f"\n{total_ko} article(s) non conforme(s) sur {len(files)}.")
    if total_warn:
        print(f"{total_warn} avertissement(s) de citabilite FAQ — non bloquant, "
              "a corriger a la redaction (phrase d'ouverture autosuffisante).")
    return 1 if total_ko else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
