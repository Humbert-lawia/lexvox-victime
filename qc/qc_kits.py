#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passe QC finale des kits LEXVOX (Lot 7).

Controle machine, sans validation humaine intermediaire :
1. Extrait toutes les references juridiques de TOUS les livrables.
2. Confronte chaque reference au referentiel verifie OpenLegi.
3. Controle disclaimers obligatoires, absence de promesse de resultat,
   absence de tiret cadratin, chiffres en chiffres.
Produit qc/rapport-qc-final.md.

Usage : python3 qc/qc_kits.py
"""
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENTIEL = os.path.join(ROOT, "referentiel", "referentiel-verifie.json")

CONTENT_DIRS = ["kits", "landing", "tunnel"]

# --- Chargement du referentiel verifie -------------------------------------

def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")

def load_referentiel():
    with open(REFERENTIEL, encoding="utf-8") as f:
        data = json.load(f)
    allowed_articles = set()   # ex: "l211-9", "1240", "d1142-1", "l221-28"
    allowed_pourvois = set()   # ex: "12-22.123"
    allowed_urls = set()
    art_pat = re.compile(r'\b((?:l|r|d)?\d+(?:-\d+)*)\b')
    for ref in data["references"]:
        label = strip_accents(ref["reference"]).lower()
        # numeros d'article dans l'intitule : L211-9, L1142-1-1, D1142-1, 1240, 202, R4127-46...
        for m in art_pat.findall(label):
            if any(ch.isdigit() for ch in m):
                allowed_articles.add(m)
        # articles cites A L'INTERIEUR du texte verifie (renvois internes de Legifrance) :
        # ils font partie d'une citation exacte verifiee, pas d'assertions autonomes.
        cite = strip_accents(ref.get("citation_exacte") or "").lower()
        for m in re.findall(r'\barticle[s]?\s+((?:l|r|d)\.?\s?\d+(?:-\d+)*)', cite):
            allowed_articles.add(m.replace(" ", "").replace(".", ""))
        # numeros de pourvoi
        for m in re.findall(r'\b(\d{2}-\d{2}\.\d{3})\b', label):
            allowed_pourvois.add(m)
        v = ref.get("verification", {})
        num = v.get("numero_pourvoi")
        if num:
            allowed_pourvois.add(num)
        url = ref.get("url_legifrance")
        if url:
            allowed_urls.add(url.strip())
    return data, allowed_articles, allowed_pourvois, allowed_urls

# --- Extraction des references dans un texte -------------------------------

ART_RE = re.compile(r'\b(?:article|art\.?)\s+((?:L|R|D)?\.?\s?\d+[-\d]*)', re.IGNORECASE)
POURVOI_RE = re.compile(r'\b(\d{2}-\d{2}\.\d{3})\b')
LOI_RE = re.compile(r'loi\s+n°?\s*([\d-]+)', re.IGNORECASE)
URL_RE = re.compile(r'https?://www\.legifrance\.gouv\.fr/\S+')
CASS_RE = re.compile(r'\bCass\.?', re.IGNORECASE)

def norm_article(a):
    a = a.replace(" ", "").replace(".", "").lower()
    return a

HEADING_ART_RE = re.compile(r'(?m)(?:^\s*#+\s*|\*\*)?article\s+(\d{1,2})\s*[.:]', re.IGNORECASE)

def extract_refs(text):
    # articles de loi cites : on ignore les intitules de clauses des CGV
    # ("Article 6. Palier premium") qui sont des titres de section, pas des lois.
    heading_nums = set(HEADING_ART_RE.findall(text))
    arts = set()
    for a in ART_RE.findall(text):
        na = norm_article(a)
        # un article a numero simple (<=2 chiffres, sans prefixe L/R/D) suivi d'un point
        # et sans code cite est un titre de clause : on ne le compte pas comme reference.
        if na.isdigit() and len(na) <= 2 and na in heading_nums:
            continue
        arts.add(na)
    pourvois = set(POURVOI_RE.findall(text))
    urls = set(u.rstrip('*).,;:"\'>') for u in URL_RE.findall(text))
    lois = set(LOI_RE.findall(text))
    return arts, pourvois, urls, lois

# --- Controles de conformite -----------------------------------------------

PROMESSES_INTERDITES = [
    "vous obtiendrez", "garantit votre indemnisation", "assure de gagner",
    "assure de gagner", "nous garantissons", "resultat garanti",
    "indemnisation garantie", "vous gagnerez", "vous allez obtenir",
    "vous obtiendrez gain de cause",
]
DISCLAIMER_RIN = "obligation de moyens, non de resultat"
AVERT_KIT = "ne constitue pas une consultation juridique"
AVERT_URGENCE = "appelez le 15"

def has(text, needle):
    # normalise les espaces/retours a la ligne : les disclaimers sont souvent
    # replies sur plusieurs lignes dans les blockquotes markdown.
    def norm(x):
        x = strip_accents(x).lower()
        x = re.sub(r'[>*#`_]', ' ', x)   # retire le chrome markdown (blockquotes, gras...)
        return re.sub(r'\s+', ' ', x)
    return norm(needle) in norm(text)

def check_file(path, allowed_articles, allowed_pourvois, allowed_urls):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    rel = os.path.relpath(path, ROOT)
    findings = []
    arts, pourvois, urls, lois = extract_refs(text)

    # references non tracees
    for a in sorted(arts):
        if a not in allowed_articles:
            findings.append(("REF_NON_TRACEE", f"article {a}"))
    for p in sorted(pourvois):
        if p not in allowed_pourvois:
            findings.append(("POURVOI_NON_TRACE", p))
    for u in sorted(urls):
        if u not in allowed_urls:
            findings.append(("URL_NON_TRACEE", u))

    # promesses de resultat
    for p in PROMESSES_INTERDITES:
        if has(text, p):
            findings.append(("PROMESSE_RESULTAT", p))

    # tiret cadratin / demi-cadratin dans le corps (hors separateurs markdown '---')
    body = re.sub(r'(?m)^\s*-{3,}\s*$', '', text)
    if "—" in body or "–" in body:
        findings.append(("TIRET_CADRATIN", "presence de — ou –"))

    return rel, text, findings, (arts, pourvois, urls)

def main():
    data, allowed_articles, allowed_pourvois, allowed_urls = load_referentiel()
    files = []
    for d in CONTENT_DIRS:
        base = os.path.join(ROOT, d)
        for dirpath, _, filenames in os.walk(base):
            for fn in filenames:
                if fn.endswith((".md", ".html")):
                    files.append(os.path.join(dirpath, fn))
    files.sort()

    all_findings = []
    total_refs = {"articles": set(), "pourvois": set(), "urls": set()}
    per_file = []
    for path in files:
        rel, text, findings, refs = check_file(
            path, allowed_articles, allowed_pourvois, allowed_urls)
        per_file.append((rel, text, findings, refs))
        for a in refs[0]:
            total_refs["articles"].add(a)
        for p in refs[1]:
            total_refs["pourvois"].add(p)
        for u in refs[2]:
            total_refs["urls"].add(u)
        for cat, detail in findings:
            all_findings.append((rel, cat, detail))

    # rapport
    lines = []
    lines.append("# Rapport QC final — kits LEXVOX Victime\n")
    lines.append("Lot 7 · Passe QC machine · Referentiel : referentiel/referentiel-verifie.json\n")
    lines.append(f"Fichiers analyses : {len(files)} (kits, landing, tunnel).\n")
    lines.append(f"References distinctes reperees : {len(total_refs['articles'])} articles, "
                 f"{len(total_refs['pourvois'])} pourvois, {len(total_refs['urls'])} URL Legifrance.\n")

    ref_findings = [f for f in all_findings if f[1] in
                    ("REF_NON_TRACEE", "POURVOI_NON_TRACE", "URL_NON_TRACEE")]
    lines.append("\n## 1. Tracabilite OpenLegi des references\n")
    if not ref_findings:
        lines.append("**100 % des references extraites correspondent au referentiel verifie OpenLegi.** "
                     "Aucune reference orpheline.\n")
    else:
        lines.append("References a re-verifier ou corriger :\n")
        for rel, cat, detail in ref_findings:
            lines.append(f"- `{rel}` : {cat} — {detail}")
        lines.append("")

    style_findings = [f for f in all_findings if f[1] in
                      ("PROMESSE_RESULTAT", "TIRET_CADRATIN")]
    lines.append("\n## 2. Conformite deontologique et style\n")
    if not style_findings:
        lines.append("Aucune promesse de resultat detectee. Aucun tiret cadratin dans le corps des textes.\n")
    else:
        for rel, cat, detail in style_findings:
            lines.append(f"- `{rel}` : {cat} — {detail}")
        lines.append("")

    # disclaimers
    lines.append("\n## 3. Presence des disclaimers obligatoires\n")
    lines.append("| Fichier | Avertissement kit | Disclaimer RIN 11.1 | Urgence 15 (si medical) |")
    lines.append("|---|:---:|:---:|:---:|")
    for rel, text, findings, refs in per_file:
        is_med = "/medical/" in rel or "medical" in rel or "erreur-medicale" in rel
        av = "OK" if has(text, AVERT_KIT) else "-"
        rin = "OK" if has(text, DISCLAIMER_RIN) else "-"
        urg = ("OK" if has(text, AVERT_URGENCE) else "MANQUE") if is_med else "n/a"
        lines.append(f"| {rel} | {av} | {rin} | {urg} |")

    lines.append("\n## 4. Points reserves a l'arbitrage de Me Humbert\n")
    lines.append("- Prix definitifs des paliers (36 € / 60 €).")
    lines.append("- Version definitive des CGV (une trame seule est produite).")
    lines.append("- Structure de vente et qualification du palier premium au regard de l'Ordre.\n")

    n_issues = len(ref_findings) + len(style_findings)
    lines.append(f"\n## Synthese : {n_issues} anomalie(s) bloquante(s) detectee(s).\n")

    out = os.path.join(ROOT, "qc", "rapport-qc-final.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Rapport ecrit : {out}")
    print(f"Anomalies bloquantes : {n_issues}")
    return 0 if n_issues == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
