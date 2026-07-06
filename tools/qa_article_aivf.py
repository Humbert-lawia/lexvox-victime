#!/usr/bin/env python3
"""Controle qualite d'un article produit selon le PIPELINE LEXVOX-AIVF.

Complete tools/preflight.py (qui valide le SEO de base : title/meta/H1/JSON-LD/
sitemap/images) en verifiant les 3 marqueurs de differenciation face a AIVF
imposes par le nouveau gabarit :

  1. >= 1 bloc d'analyse jurisprudentielle  (<div class="juris-block">)
  2. >= 2 tableaux de donnees               (<table class="data-table">)
  3. >= 1 infographie schema inline SVG     (<figure class="infographic"> ... <svg>)
  4. volume minimal de texte                (1800 mots feuille / 3000 mots pilier)

Usage :
  python3 tools/qa_article_aivf.py actualites/mon-article.html
  python3 tools/qa_article_aivf.py actualites/mon-hub.html --pilier
  python3 tools/qa_article_aivf.py actualites/a.html actualites/b.html   # lot

Code retour 0 = conforme, 1 = au moins un article non conforme.
"""
import re
import sys
from pathlib import Path

TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)


def word_count(html: str) -> int:
    """Compte approximatif des mots de contenu visible (hors script/style/balises)."""
    text = SCRIPT_STYLE_RE.sub(" ", html)
    text = TAG_RE.sub(" ", text)
    return len(text.split())


def check(path: Path, pilier: bool) -> list[str]:
    problems = []
    html = path.read_text(encoding="utf-8", errors="ignore")

    juris = len(re.findall(r'class="[^"]*juris-block', html))
    if juris < 1:
        problems.append("aucun bloc d'analyse jurisprudentielle (<div class=\"juris-block\">)")

    tables = len(re.findall(r'<table[^>]*class="[^"]*data-table', html))
    if tables < 2:
        problems.append(f"{tables} tableau(x) data-table (minimum 2 requis)")

    figs = re.findall(r'<figure[^>]*class="[^"]*infographic[^"]*"[^>]*>(.*?)</figure>', html, re.S | re.I)
    svg_ok = any("<svg" in f.lower() for f in figs)
    if not svg_ok:
        problems.append("aucune infographie SVG inline (<figure class=\"infographic\"> avec <svg>)")

    n = word_count(html)
    floor = 3000 if pilier else 1800
    if n < floor:
        kind = "pilier" if pilier else "feuille"
        problems.append(f"{n} mots (minimum {floor} pour un {kind})")

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
            print(f"  ERREUR  {f} : fichier introuvable")
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
