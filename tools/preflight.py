#!/usr/bin/env python3
"""Validation pré-push du site lexvox-victime.com.

Vérifie les classes d'erreurs qui ont déjà cassé la prod par le passé :
marqueurs de conflit git committés, sitemap.xml invalide ou avec doublons,
JSON-LD corrompu, images locales manquantes, meta SEO hors gabarit.

Usage : python3 scripts/preflight.py
Code retour 0 = OK (les avertissements n'empêchent pas le push),
1 = erreurs bloquantes à corriger avant de pousser.
"""
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = "https://lexvox-victime.com"

errors = []
warnings = []


def tracked_files():
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return [ROOT / line for line in out.splitlines() if line]


def check_conflict_markers():
    """Des marqueurs de conflit ont déjà été committés sur main (sitemap.xml,
    avril-mai 2026) : le sitemap est resté invalide en prod pendant des semaines."""
    marker = re.compile(r"^(<{7} |={7}$|>{7} )", re.M)
    for f in tracked_files():
        if f.suffix in {".png", ".jpg", ".jpeg", ".webp", ".ico", ".pdf", ".docx", ".woff", ".woff2"}:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except (OSError, IsADirectoryError):
            continue
        if marker.search(text):
            errors.append(f"{f.relative_to(ROOT)} : marqueurs de conflit git non résolus")


def check_sitemap():
    path = ROOT / "sitemap.xml"
    if not path.exists():
        errors.append("sitemap.xml manquant")
        return
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        errors.append(f"sitemap.xml : XML invalide ({e})")
        return
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    locs = [el.text.strip() for el in tree.iter(f"{ns}loc") if el.text]
    seen = set()
    for loc in locs:
        if loc in seen:
            errors.append(f"sitemap.xml : URL en doublon — {loc}")
        seen.add(loc)
        if not loc.startswith(DOMAIN):
            errors.append(f"sitemap.xml : domaine non canonique — {loc} (attendu {DOMAIN})")
            continue
        if loc.endswith(".html"):
            errors.append(f"sitemap.xml : URL avec extension .html — {loc}")
        rel = loc[len(DOMAIN):].strip("/")
        candidate = ROOT / (rel + ".html") if rel else ROOT / "index.html"
        alt = ROOT / rel / "index.html" if rel else candidate
        if not candidate.exists() and not alt.exists():
            errors.append(f"sitemap.xml : aucun fichier pour {loc}")
    print(f"  sitemap.xml : {len(locs)} URLs")


def html_pages():
    pages = sorted(ROOT.glob("*.html")) + sorted(ROOT.glob("actualites/*.html")) + sorted(
        ROOT.glob("cabinet/*.html")
    )
    return [p for p in pages if p.name != "404.html"]


def check_pages():
    jsonld_re = re.compile(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S | re.I
    )
    img_re = re.compile(r'<img[^>]+src="([^"]+)"', re.I)
    desc_re = re.compile(r'<meta\s+name="description"\s+content="([^"]*)"', re.I)
    title_re = re.compile(r"<title>(.*?)</title>", re.S | re.I)
    h1_re = re.compile(r"<h1[\s>]", re.I)
    canonical_re = re.compile(r'<link\s+rel="canonical"\s+href="([^"]+)"', re.I)
    noindex_re = re.compile(r'<meta\s+name="robots"\s+content="[^"]*noindex', re.I)

    for page in html_pages():
        rel = page.relative_to(ROOT)
        html = page.read_text(encoding="utf-8", errors="ignore")

        # JSON-LD : du HTML a déjà été injecté dans un bloc FAQPage (avril 2026)
        for i, block in enumerate(jsonld_re.findall(html), 1):
            try:
                json.loads(block)
            except json.JSONDecodeError as e:
                errors.append(f"{rel} : bloc JSON-LD n°{i} invalide ({e})")

        # Images locales : 3 images hero 4XX relevées à l'audit SE Ranking
        for src in img_re.findall(html):
            if src.startswith(("http://", "https://", "data:")):
                continue
            target = ROOT / src.lstrip("/") if src.startswith("/") else page.parent / src
            if not target.exists():
                errors.append(f"{rel} : image locale introuvable — {src}")

        if noindex_re.search(html):
            continue  # pages légales : pas de contraintes SEO

        m = desc_re.search(html)
        if not m or not m.group(1).strip():
            warnings.append(f"{rel} : meta description absente ou vide")
        elif len(m.group(1)) > 165:
            warnings.append(f"{rel} : meta description trop longue ({len(m.group(1))} > 165)")

        m = title_re.search(html)
        if m and len(re.sub(r"\s+", " ", m.group(1)).strip()) > 65:
            warnings.append(f"{rel} : <title> trop long ({len(m.group(1).strip())} > 65)")

        n_h1 = len(h1_re.findall(html))
        if n_h1 != 1:
            warnings.append(f"{rel} : {n_h1} balises <h1> (attendu : 1)")

        m = canonical_re.search(html)
        if not m:
            warnings.append(f"{rel} : balise canonical absente")
        elif m.group(1).endswith(".html") or not m.group(1).startswith(DOMAIN):
            warnings.append(f"{rel} : canonical non conforme — {m.group(1)}")


def check_secrets():
    """Un token d'API a déjà été committé en dur dans le dashboard (juin 2026)."""
    pat = re.compile(r"(sk-[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{30,}|ghp_[A-Za-z0-9]{30,})")
    for f in tracked_files():
        if f.suffix not in {".html", ".js", ".json", ".txt", ".md", ".yml", ".yaml"}:
            continue
        try:
            for m in pat.finditer(f.read_text(encoding="utf-8", errors="ignore")):
                errors.append(f"{f.relative_to(ROOT)} : secret potentiel en clair — {m.group(0)[:12]}…")
        except OSError:
            continue


def main():
    print("Préflight lexvox-victime.com")
    check_conflict_markers()
    check_sitemap()
    check_pages()
    check_secrets()

    for w in warnings:
        print(f"  AVERTISSEMENT  {w}")
    for e in errors:
        print(f"  ERREUR         {e}")
    print(f"\n{len(errors)} erreur(s) bloquante(s), {len(warnings)} avertissement(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
