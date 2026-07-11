#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lot 6 : mise en page PDF des kits LEXVOX.

Convertit les documents Markdown en PDF maquettes (couverture par kit, charte
sobre serif + 1 couleur d'accent, sommaire cliquable, pieds de page, pagination)
via Chromium headless. Genere 1 PDF par palier + les fichiers a remplir en A4.

Usage : python3 pdf/build_pdf.py
"""
import os
import re
import subprocess
import sys

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "pdf")
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

ACCENT = "#8a1c2b"  # bordeaux sobre, cohérent avec un cabinet d'avocats

# Paliers : (id, titre du kit, sous-titre, [fichiers md dans l'ordre])
PALIERS = [
    ("kit-accident-palier-1", "Kit Victime d'accident", "Palier 1 : preparez votre dossier", [
        "kits/accident/palier-1/1-1-journal-de-bord.md",
        "kits/accident/palier-1/1-2-checklist-30-documents.md",
        "kits/accident/palier-1/1-3-plan-30-premiers-jours.md",
        "kits/accident/palier-1/1-4-protocole-face-assureur.md",
        "kits/accident/palier-1/1-5-six-courriers-types.md",
        "kits/accident/palier-1/1-6-nomenclature-dintilhac-traduite.md",
        "kits/accident/palier-1/1-7-lexique-et-textes.md",
    ]),
    ("kit-accident-palier-2", "Kit Expertise accident", "Palier 2 : preparez votre expertise", [
        "kits/accident/palier-2/2-1-guide-preparation-expertise-medicale.md",
        "kits/accident/palier-2/2-2-grille-auto-recensement-20-postes.md",
        "kits/accident/palier-2/2-3-tableau-tierce-personne.md",
        "kits/accident/palier-2/2-4-calculateur-pertes-de-gains.md",
    ]),
    ("kit-accident-palier-premium", "Kit + Audit d'avocat accident", "Palier premium : faites verifier votre offre", [
        "kits/accident/palier-2/2-1-guide-preparation-expertise-medicale.md",
        "kits/accident/palier-2/2-2-grille-auto-recensement-20-postes.md",
        "kits/accident/palier-2/2-3-tableau-tierce-personne.md",
        "kits/accident/palier-2/2-4-calculateur-pertes-de-gains.md",
        "kits/accident/palier-3/3-1-protocole-audit-offre.md",
        "kits/accident/palier-3/3-2-lettre-accompagnement-audit.md",
    ]),
    ("kit-medical-palier-1", "Kit Victime d'erreur medicale", "Palier 1 : constituez votre dossier", [
        "kits/medical/palier-1/m1-1-obtenir-dossier-medical.md",
        "kits/medical/palier-1/m1-2-chronologie-des-soins.md",
        "kits/medical/palier-1/m1-3-journal-symptomes-sequelles.md",
        "kits/medical/palier-1/m1-4-carte-des-3-voies.md",
        "kits/medical/palier-1/m1-5-10-signaux-erreur-medicale.md",
        "kits/medical/palier-1/m1-6-lexique-et-textes.md",
    ]),
    ("kit-medical-palier-2", "Kit Expertise CCI", "Palier 2 : preparez votre expertise CCI", [
        "kits/medical/palier-2/m2-1-test-eligibilite-cci.md",
        "kits/medical/palier-2/m2-2-guide-expertise-cci.md",
        "kits/medical/palier-2/m2-3-prejudices-specifiques-medical.md",
    ]),
    ("kit-medical-palier-premium", "Kit + Audit d'avocat medical", "Palier premium : faites pre-analyser votre dossier", [
        "kits/medical/palier-2/m2-1-test-eligibilite-cci.md",
        "kits/medical/palier-2/m2-2-guide-expertise-cci.md",
        "kits/medical/palier-2/m2-3-prejudices-specifiques-medical.md",
        "kits/medical/palier-3/m3-1-protocole-pre-analyse-dossier-medical.md",
    ]),
]

# Fichiers a remplir, en A4 imprimable, un PDF chacun
FILLABLES = [
    ("a-remplir-journal-de-bord-accident", "Journal de bord de la victime",
     "kits/accident/palier-1/1-1-journal-de-bord.md"),
    ("a-remplir-tableau-tierce-personne", "Tableau tierce personne",
     "kits/accident/palier-2/2-3-tableau-tierce-personne.md"),
    ("a-remplir-grille-20-postes", "Grille d'auto-recensement des 20 postes",
     "kits/accident/palier-2/2-2-grille-auto-recensement-20-postes.md"),
    ("a-remplir-chronologie-des-soins", "Chronologie des soins",
     "kits/medical/palier-1/m1-2-chronologie-des-soins.md"),
    ("a-remplir-journal-symptomes", "Journal des symptomes et sequelles",
     "kits/medical/palier-1/m1-3-journal-symptomes-sequelles.md"),
]

CSS = """
@page {
  size: A4;
  margin: 20mm 18mm 20mm 18mm;
  @bottom-left { content: "(c) SELARL LEXVOX AVOCATS"; font-size: 7.5pt; color:#888; }
  @bottom-center { content: "Ce document ne constitue pas une consultation juridique"; font-size:7.5pt; color:#888; }
  @bottom-right { content: counter(page) " / " counter(pages); font-size:7.5pt; color:#888; }
}
@page :first { margin:0; @bottom-left{content:""} @bottom-center{content:""} @bottom-right{content:""} }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: Georgia, 'Times New Roman', serif; font-size: 10.8pt; line-height: 1.5; color:#1c1c1c; margin:0; }
h1,h2,h3,h4 { font-family: Georgia, serif; color: %(accent)s; line-height:1.25; }
h1 { font-size: 20pt; border-bottom: 2px solid %(accent)s; padding-bottom:6px; margin-top: 0; page-break-before: always; }
h2 { font-size: 15pt; margin-top: 1.4em; }
h3 { font-size: 12.5pt; }
h4 { font-size: 11pt; color:#333; }
p, li { orphans: 2; widows: 2; }
a { color: %(accent)s; text-decoration: none; }
table { border-collapse: collapse; width: 100%%; margin: 12px 0; font-size: 9.5pt; page-break-inside: avoid; }
th, td { border: 1px solid #c9c9c9; padding: 5px 7px; text-align: left; vertical-align: top; }
th { background: #f3ecec; color:%(accent)s; }
blockquote { border-left: 3px solid %(accent)s; margin: 12px 0; padding: 6px 14px; background:#faf6f6; }
code { background:#f2f2f2; padding:1px 4px; border-radius:3px; font-size:9.5pt; }
hr { border:0; border-top:1px solid #ddd; margin:16px 0; }
details { margin:8px 0; }
summary { font-weight:bold; color:%(accent)s; }
/* Couverture */
.cover { page-break-after: always; height: 257mm; display:flex; flex-direction:column;
  justify-content:center; padding: 0 24mm; }
.cover .band { border-top:4px solid %(accent)s; border-bottom:4px solid %(accent)s; padding:24px 0; }
.cover h1 { border:0; page-break-before: avoid; font-size: 30pt; margin:0 0 8px; }
.cover .sub { font-size: 14pt; color:#444; font-style:italic; }
.cover .cab { margin-top: 40px; font-size: 12pt; color:%(accent)s; font-weight:bold; }
.cover .meta { font-size: 10pt; color:#666; margin-top:4px; }
.cover .disc { position:absolute; bottom: 18mm; left:24mm; right:24mm; font-size:8pt; color:#888; }
/* Sommaire */
.toc { page-break-after: always; }
.toc h1 { page-break-before: avoid; }
.toc ol { font-size: 11pt; line-height:1.9; }
.doc { }
"""


def slugify(s):
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s.lower()).strip('-')
    return s


def md_to_html(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        text = f.read()
    html = markdown.markdown(
        text, extensions=["tables", "fenced_code", "sane_lists", "attr_list", "md_in_html"])
    return html


def first_h1_title(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        for line in f:
            if line.startswith("# "):
                return line[2:].strip()
    return os.path.basename(path)


def build_html(kit_title, subtitle, files, with_cover_toc=True):
    parts = []
    parts.append(f"<style>{CSS % {'accent': ACCENT}}</style>")
    if with_cover_toc:
        parts.append(f"""
<div class="cover"><div class="band">
  <div class="meta">SELARL LEXVOX AVOCATS</div>
  <h1>{kit_title}</h1>
  <div class="sub">{subtitle}</div>
  <div class="cab">Concu et redige par Me Patrice Humbert</div>
  <div class="meta">Avocat specialiste CNB en dommage corporel : Barreau d'Aix-en-Provence</div>
</div>
  <div class="disc">Ce kit est un outil d'information et de preparation. Il ne constitue pas une
  consultation juridique personnalisee et ne remplace pas l'analyse de votre situation par un avocat.
  En cas d'urgence medicale, appelez le 15.</div>
</div>""")
        # sommaire
        toc = ['<div class="toc"><h1>Sommaire</h1><ol>']
        for path in files:
            t = first_h1_title(path)
            anchor = slugify(t)
            toc.append(f'<li><a href="#{anchor}">{t}</a></li>')
        toc.append("</ol></div>")
        parts.append("\n".join(toc))
    for path in files:
        t = first_h1_title(path)
        anchor = slugify(t)
        body = md_to_html(path)
        # ancrer le premier h1 du doc
        body = re.sub(r'<h1>', f'<h1 id="{anchor}">', body, count=1)
        parts.append(f'<section class="doc">{body}</section>')
    return "<!doctype html><html lang=fr><head><meta charset=utf-8></head><body>" + \
        "\n".join(parts) + "</body></html>"


def render_pdf(html, out_name):
    html_path = os.path.join(OUT, "_tmp_" + out_name + ".html")
    pdf_path = os.path.join(OUT, out_name + ".pdf")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    cmd = [
        CHROME, "--headless", "--no-sandbox", "--disable-gpu",
        "--no-pdf-header-footer",
        "--print-to-pdf=" + pdf_path,
        "file://" + html_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if not os.path.exists(pdf_path):
        print("ERREUR rendu", out_name, r.stderr[-500:])
        return None
    os.remove(html_path)
    return pdf_path


def main():
    os.makedirs(OUT, exist_ok=True)
    made = []
    for pid, title, sub, files in PALIERS:
        files = [f for f in files if os.path.exists(os.path.join(ROOT, f))]
        if not files:
            continue
        html = build_html(title, sub, files, with_cover_toc=True)
        p = render_pdf(html, pid)
        if p:
            made.append(p)
            print("OK", os.path.relpath(p, ROOT), f"({os.path.getsize(p)//1024} Ko)")
    for fid, title, path in FILLABLES:
        if not os.path.exists(os.path.join(ROOT, path)):
            continue
        html = build_html(title, "Version A4 a imprimer et remplir", [path], with_cover_toc=False)
        p = render_pdf(html, fid)
        if p:
            made.append(p)
            print("OK", os.path.relpath(p, ROOT), f"({os.path.getsize(p)//1024} Ko)")
    print(f"\n{len(made)} PDF generes dans pdf/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
