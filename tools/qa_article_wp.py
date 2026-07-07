#!/usr/bin/env python3
"""Controle qualite d'un article WordPress produit selon le PIPELINE LEXVOX-WP.

Adaptation de tools/qa_article_aivf.py au format atelier WordPress
(wp-atelier/<site>/<slug>.html) : memes controles DE FOND, sans les controles
de "chrome" du site statique (pas de <head>, nav, footer, JSON-LD de page —
WordPress/Yoast les gerent). L'article atelier = front-matter JSON en
commentaire <!-- WP-META {...} --> + corps HTML du post.

Controles bloquants :
  1. Front-matter WP-META valide : site (medical|accident), title <= 60 car.,
     metaDescription 120-155 car., slug (= nom de fichier), ville, categories,
     image existante.
  2. Analyse jurisprudentielle VERIFIEE : >= 1 <div class="juris-block">,
     chaque bloc avec backlink <a href="https://..."> (Legifrance), et autant
     de marqueurs <!-- OPENLEGI ... --> que de blocs.
  3. Donnees : >= 2 tableaux <table class="data-table">.
  4. Infographie : >= 1 <figure class="infographic"> contenant un <svg>
     avec role="img" et aria-label.
  5. Couverture d'intent : >= 5 <h2> ET FAQ >= 6 questions (bloc Yoast FAQ
     .schema-faq-section, ou a defaut <details>).
  6. NeuronWriter (NON NEGOCIABLE) : <!-- NEURONWRITER SCORE: N --> avec N >= 85.
  7. Plancher de mots : >= 1900 mots utiles (>= 2500 avec --pilier).
  8. Hygiene : AUCUN <h1> dans le corps (le titre WP est le H1), aucun
     marqueur de conflit git, aucun secret evident.

Usage :
  python3 tools/qa_article_wp.py wp-atelier/<site>/<slug>.html [--pilier]

Code retour 0 = conforme, 1 = au moins un article non conforme.
"""
import json
import re
import sys
from pathlib import Path

TAG_RE = re.compile(r"<[^>]+>")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
JURIS_RE = re.compile(r'<div[^>]*class="[^"]*juris-block[^"]*"[^>]*>(.*?)</div>', re.S | re.I)
HREF_RE = re.compile(r'<a[^>]+href="https?://', re.I)
META_RE = re.compile(r"<!--\s*WP-META\s*(\{.*?\})\s*-->", re.S)
SECRET_RE = re.compile(r"(sk-[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_\-]{30,}|xox[bp]-|BEGIN [A-Z ]*PRIVATE KEY)")

SITES = ("medical", "accident")


def content_word_count(html: str) -> int:
    text = COMMENT_RE.sub(" ", html)
    text = SCRIPT_STYLE_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return len(text.split())


def check(path: Path, pilier: bool) -> list[str]:
    problems = []
    html = path.read_text(encoding="utf-8", errors="ignore")

    # 0. Hygiene
    if re.search(r"^(<<<<<<<|=======$|>>>>>>>)", html, re.M):
        problems.append("marqueur de conflit git present")
    if SECRET_RE.search(html):
        problems.append("secret potentiel detecte dans le fichier")

    # 1. Front-matter WP-META
    m = META_RE.search(html)
    meta = None
    if not m:
        problems.append("front-matter <!-- WP-META {json} --> absent")
    else:
        try:
            meta = json.loads(m.group(1))
        except json.JSONDecodeError as e:
            problems.append(f"front-matter WP-META : JSON invalide ({e})")
    if meta:
        site = meta.get("site")
        if site not in SITES:
            problems.append(f"WP-META.site invalide : {site!r} (attendu medical|accident)")
        title = (meta.get("title") or "").strip()
        if not title:
            problems.append("WP-META.title vide")
        elif len(title) > 60:
            problems.append(f"WP-META.title {len(title)} car. (max 60)")
        desc = (meta.get("metaDescription") or "").strip()
        if not 120 <= len(desc) <= 155:
            problems.append(f"WP-META.metaDescription {len(desc)} car. (attendu 120-155)")
        slug = (meta.get("slug") or "").strip()
        if not slug:
            problems.append("WP-META.slug vide")
        elif slug != path.stem:
            problems.append(f"WP-META.slug {slug!r} != nom de fichier {path.stem!r}")
        if not meta.get("ville"):
            problems.append("WP-META.ville vide (ancrage local obligatoire)")
        if not meta.get("categories"):
            problems.append("WP-META.categories vide")
        img = meta.get("image")
        if not img:
            problems.append("WP-META.image vide (image mise en avant obligatoire)")
        elif not (path.parent / img).exists() and not Path(img).exists():
            problems.append(f"WP-META.image introuvable : {img}")
        alt = (meta.get("imageAlt") or "").strip()
        if not alt:
            problems.append("WP-META.imageAlt vide (alt localise obligatoire)")

    # 2. Bloc(s) jurisprudentiel(s) verifie(s)
    juris_blocks = JURIS_RE.findall(html)
    if len(juris_blocks) < 1:
        problems.append('aucun bloc d\'analyse jurisprudentielle (<div class="juris-block">)')
    else:
        sans_backlink = sum(1 for b in juris_blocks if not HREF_RE.search(b))
        if sans_backlink:
            problems.append(
                f"{sans_backlink} bloc(s) juris sans backlink hypertexte vers la source "
                '(<a href="https://..."> Legifrance attendu)'
            )
        markers = len(re.findall(r"<!--\s*OPENLEGI", html, re.I))
        if markers < len(juris_blocks):
            problems.append(
                f"{markers} marqueur(s) Openlegi pour {len(juris_blocks)} bloc(s) juris : "
                "chaque decision doit etre verifiee via Openlegi"
            )

    # 3. Tableaux
    tables = len(re.findall(r'<table[^>]*class="[^"]*data-table', html))
    if tables < 2:
        problems.append(f"{tables} tableau(x) data-table (minimum 2 requis)")

    # 4. Infographie SVG inline
    figs = re.findall(r'<figure[^>]*class="[^"]*infographic[^"]*"[^>]*>(.*?)</figure>', html, re.S | re.I)
    svg_ok = False
    for f in figs:
        msvg = re.search(r"<svg[^>]*>", f, re.I)
        if msvg:
            svg_ok = True
            tag = msvg.group(0)
            if 'role="img"' not in tag:
                problems.append('infographie : <svg> sans role="img"')
            if "aria-label" not in tag:
                problems.append("infographie : <svg> sans aria-label")
    if not svg_ok:
        problems.append('aucune infographie SVG inline (<figure class="infographic"> avec <svg>)')

    # 5. Couverture d'intent
    n_h2 = len(re.findall(r"<h2[\s>]", html, re.I))
    if n_h2 < 5:
        problems.append(f"{n_h2} sections <h2> (minimum 5 pour couvrir l'intent)")
    n_faq = len(re.findall(r'class="schema-faq-section"', html, re.I)) or len(
        re.findall(r"<details[\s>]", html, re.I)
    )
    if n_faq < 6:
        problems.append(
            f"{n_faq} questions FAQ (minimum 6 — bloc Yoast FAQ .schema-faq-section ou <details>)"
        )

    # 6. NeuronWriter >= 85
    m = re.search(r"<!--\s*NEURONWRITER\s+SCORE:\s*([0-9]+(?:\.[0-9]+)?)", html, re.I)
    if not m:
        problems.append(
            "aucun marqueur <!-- NEURONWRITER SCORE: N --> : l'optimisation >= 85 est obligatoire"
        )
    elif float(m.group(1)) < 85:
        problems.append(f"score NeuronWriter {m.group(1)} < 85 (seuil non negociable)")

    # 7. Plancher de mots
    n = content_word_count(html)
    floor = 2500 if pilier else 1900
    if n < floor:
        kind = "pilier" if pilier else "feuille"
        problems.append(f"{n} mots utiles (minimum {floor} pour un {kind}, plancher absolu 1900)")

    # 8. Pas de H1 dans le corps (le titre WordPress est le H1)
    n_h1 = len(re.findall(r"<h1[\s>]", html, re.I))
    if n_h1:
        problems.append(f"{n_h1} <h1> dans le corps du post (interdit : le titre WP est le H1)")

    return problems


def main(argv: list[str]) -> int:
    pilier = "--pilier" in argv
    files = [a for a in argv if not a.startswith("--")]
    if not files:
        print("Usage : python3 tools/qa_article_wp.py wp-atelier/<site>/<slug>.html [--pilier]")
        return 1

    total_ko = 0
    print("QA article — standard PIPELINE LEXVOX-WP")
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
