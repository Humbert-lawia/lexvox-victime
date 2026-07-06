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
     <!-- NEURONWRITER SCORE: N ... --> present et N >= 85.
  6. Plancher de mots (chrome exclu) : >= 1900 mots utiles pour TOUT article
     (limite non negociable), >= 2500 pour un pilier. Le volume peut monter
     au-dessus de 1900 si cela ameliore le score, jamais descendre en dessous.

Usage :
  python3 tools/qa_article_aivf.py actualites/mon-article.html
  python3 tools/qa_article_aivf.py actualites/mon-hub.html --pilier
  python3 tools/qa_article_aivf.py a.html b.html          # lot

Code retour 0 = conforme, 1 = au moins un article non conforme.
"""
import re
import sys
from pathlib import Path

TAG_RE = re.compile(r"<[^>]+>")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
# blocs de "chrome" (menu, en-tete, pied) a exclure du comptage de mots utiles
CHROME_RE = re.compile(r"<(nav|header|footer)[^>]*>.*?</\1>", re.S | re.I)
BAR_RE = re.compile(r'<div[^>]*class="[^"]*reassurance-bar[^"]*"[^>]*>.*?</div>', re.S | re.I)
JURIS_RE = re.compile(r'<div[^>]*class="[^"]*juris-block[^"]*"[^>]*>(.*?)</div>', re.S | re.I)
HREF_RE = re.compile(r'<a[^>]+href="https?://', re.I)


def content_word_count(html: str) -> int:
    """Mots de contenu visible, hors script/style/commentaires ET hors chrome
    (nav/header/footer/barre de reassurance) — evite les faux positifs."""
    text = COMMENT_RE.sub(" ", html)
    text = SCRIPT_STYLE_RE.sub(" ", text)
    text = CHROME_RE.sub(" ", text)
    text = BAR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return len(text.split())


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

    # 5. Optimisation NeuronWriter — score >= 85 (non negociable)
    m = re.search(r"<!--\s*NEURONWRITER\s+SCORE:\s*([0-9]+(?:\.[0-9]+)?)", html, re.I)
    if not m:
        problems.append(
            "aucun marqueur de score NeuronWriter (<!-- NEURONWRITER SCORE: N ... -->) : "
            "l'optimisation NeuronWriter >= 85 est obligatoire avant publication"
        )
    elif float(m.group(1)) < 85:
        problems.append(f"score NeuronWriter {m.group(1)} < 85 (seuil non negociable)")

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

    print(f"\n{total_ko} article(s) non conforme(s) sur {len(files)}.")
    return 1 if total_ko else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
