#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lot 6 : mise en page PDF des kits LEXVOX, charte magazine LEXVOX.

Design inspire du guide LawIA (couverture magazine, en-tete/pied courants,
pastilles de chapitre, encadres a ombre portee, tableaux de marque), transpose
a l'identite LEXVOX (bleu #4a7ba8, creme #faf9f5, dark #141413, serif Gelasio
facon Georgia, sans Carlito facon Calibri). Rendu via Chromium headless.

Usage : python3 pdf/build_pdf.py [--guides-only]
"""
import os
import re
import subprocess
import sys

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "pdf")
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
FONTS = os.path.join(ROOT, "pdf", "fonts")  # polices embarquees dans le depot

# Palette LEXVOX (extraite de css/style.css)
C = {
    "bleu": "#6a9bcc", "bleuf": "#4a7ba8", "bleuc": "#a8c4e0", "bleup": "#d3e5f8",
    "dark": "#141413", "creme": "#faf9f5", "gris": "#8f8d84", "grisc": "#e8e6dc",
    "or": "#c4748a", "orc": "#d4bc7c", "negatif": "#c4745b", "encre": "#1f1f1e",
}

# (id fichier, titre du kit, sous-titre, edition, [documents md])
PALIERS = [
    ("kit-accident-palier-1", "Kit Victime d'accident", "Préparez votre dossier d'indemnisation",
     "Palier 1 : le kit gratuit", [
        "kits/accident/palier-1/1-1-journal-de-bord.md",
        "kits/accident/palier-1/1-2-checklist-30-documents.md",
        "kits/accident/palier-1/1-3-plan-30-premiers-jours.md",
        "kits/accident/palier-1/1-4-protocole-face-assureur.md",
        "kits/accident/palier-1/1-5-six-courriers-types.md",
        "kits/accident/palier-1/1-6-nomenclature-dintilhac-traduite.md",
        "kits/accident/palier-1/1-7-lexique-et-textes.md",
    ]),
    ("kit-accident-palier-2", "Kit Expertise accident", "Préparez votre expertise médicale",
     "Palier 2 : le kit expertise", [
        "kits/accident/palier-2/2-1-guide-preparation-expertise-medicale.md",
        "kits/accident/palier-2/2-2-grille-auto-recensement-20-postes.md",
        "kits/accident/palier-2/2-3-tableau-tierce-personne.md",
        "kits/accident/palier-2/2-4-calculateur-pertes-de-gains.md",
    ]),
    ("kit-accident-palier-premium", "Kit + Audit d'avocat accident", "Faites vérifier votre offre par un avocat",
     "Palier premium", [
        "kits/accident/palier-2/2-1-guide-preparation-expertise-medicale.md",
        "kits/accident/palier-2/2-2-grille-auto-recensement-20-postes.md",
        "kits/accident/palier-2/2-3-tableau-tierce-personne.md",
        "kits/accident/palier-2/2-4-calculateur-pertes-de-gains.md",
        "kits/accident/palier-3/3-1-protocole-audit-offre.md",
        "kits/accident/palier-3/3-2-lettre-accompagnement-audit.md",
    ]),
    ("kit-medical-palier-1", "Kit Victime d'erreur médicale", "Constituez votre dossier médical",
     "Palier 1 : le kit gratuit", [
        "kits/medical/palier-1/m1-1-obtenir-dossier-medical.md",
        "kits/medical/palier-1/m1-2-chronologie-des-soins.md",
        "kits/medical/palier-1/m1-3-journal-symptomes-sequelles.md",
        "kits/medical/palier-1/m1-4-carte-des-3-voies.md",
        "kits/medical/palier-1/m1-5-10-signaux-erreur-medicale.md",
        "kits/medical/palier-1/m1-6-lexique-et-textes.md",
    ]),
    ("kit-medical-palier-2", "Kit Expertise CCI", "Préparez votre expertise CCI",
     "Palier 2 : le kit expertise", [
        "kits/medical/palier-2/m2-1-test-eligibilite-cci.md",
        "kits/medical/palier-2/m2-2-guide-expertise-cci.md",
        "kits/medical/palier-2/m2-3-prejudices-specifiques-medical.md",
    ]),
    ("kit-medical-palier-premium", "Kit + Audit d'avocat médical", "Faites pré-analyser votre dossier",
     "Palier premium", [
        "kits/medical/palier-2/m2-1-test-eligibilite-cci.md",
        "kits/medical/palier-2/m2-2-guide-expertise-cci.md",
        "kits/medical/palier-2/m2-3-prejudices-specifiques-medical.md",
        "kits/medical/palier-3/m3-1-protocole-pre-analyse-dossier-medical.md",
    ]),
]

FILLABLES = [
    ("a-remplir-journal-de-bord-accident", "Journal de bord de la victime", "kits/accident/palier-1/1-1-journal-de-bord.md"),
    ("a-remplir-tableau-tierce-personne", "Tableau tierce personne", "kits/accident/palier-2/2-3-tableau-tierce-personne.md"),
    ("a-remplir-grille-20-postes", "Grille d'auto-recensement des 20 postes", "kits/accident/palier-2/2-2-grille-auto-recensement-20-postes.md"),
    ("a-remplir-chronologie-des-soins", "Chronologie des soins", "kits/medical/palier-1/m1-2-chronologie-des-soins.md"),
    ("a-remplir-journal-symptomes", "Journal des symptômes et séquelles", "kits/medical/palier-1/m1-3-journal-symptomes-sequelles.md"),
]

def font_face():
    def u(name): return "file://" + os.path.join(FONTS, name)
    return f"""
@font-face {{ font-family:'Gelasio'; font-weight:400; font-style:normal; src:url('{u("gelasio-400.woff2")}') format('woff2'); }}
@font-face {{ font-family:'Gelasio'; font-weight:700; font-style:normal; src:url('{u("gelasio-700.woff2")}') format('woff2'); }}
@font-face {{ font-family:'Gelasio'; font-weight:400; font-style:italic; src:url('{u("gelasio-400i.woff2")}') format('woff2'); }}
@font-face {{ font-family:'Gelasio'; font-weight:700; font-style:italic; src:url('{u("gelasio-700i.woff2")}') format('woff2'); }}
@font-face {{ font-family:'Carlito'; font-weight:400; font-style:normal; src:url('{u("carlito-400.woff2")}') format('woff2'); }}
@font-face {{ font-family:'Carlito'; font-weight:700; font-style:normal; src:url('{u("carlito-700.woff2")}') format('woff2'); }}
@font-face {{ font-family:'Carlito'; font-weight:400; font-style:italic; src:url('{u("carlito-400i.woff2")}') format('woff2'); }}
@font-face {{ font-family:'Carlito'; font-weight:700; font-style:italic; src:url('{u("carlito-700i.woff2")}') format('woff2'); }}
"""

def css(kit_upper):
    return font_face() + f"""
@page {{
  size: A4; margin: 22mm 17mm 20mm 17mm;
  @top-left {{ content: "LEXVOX \\2014 VICTIME"; font-family:'Gelasio',serif; font-weight:700; font-size:8.5pt; color:{C['dark']}; }}
  @top-right {{ content: "{kit_upper}"; font-family:'Carlito',sans-serif; font-size:7.5pt; letter-spacing:2px; color:{C['gris']}; }}
  @bottom-left {{ content: "\\00A9 SELARL LEXVOX AVOCATS"; font-family:'Carlito',sans-serif; font-size:7pt; letter-spacing:1px; color:{C['gris']}; }}
  @bottom-center {{ content: "Ce document ne constitue pas une consultation juridique"; font-family:'Carlito',sans-serif; font-size:7pt; color:{C['gris']}; }}
  @bottom-right {{ content: counter(page) " / " counter(pages); font-family:'Carlito',sans-serif; font-weight:700; font-size:8pt; color:{C['bleuf']}; }}
}}
@page :first {{ margin:0;
  @top-left {{ content:""; }} @top-right {{ content:""; }}
  @bottom-left {{ content:""; }} @bottom-center {{ content:""; }} @bottom-right {{ content:""; }}
}}
* {{ box-sizing:border-box; }}
html {{ -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
body {{ font-family:'Carlito','DejaVu Sans',sans-serif; font-size:10.5pt; line-height:1.62; color:{C['encre']}; margin:0; }}
h1,h2,h3,h4 {{ font-family:'Gelasio','DejaVu Serif',serif; font-weight:700; color:{C['dark']}; line-height:1.18; }}

/* Ouverture de document (chapitre) */
.docopen {{ page-break-before:always; margin-bottom:1.4em; }}
.docopen:first-of-type {{ page-break-before:avoid; }}
.chapline {{ display:flex; align-items:center; gap:12px; margin-bottom:14px; }}
.pill {{ display:inline-block; font-family:'Carlito',sans-serif; font-weight:700; font-size:7.5pt;
  letter-spacing:1.5px; text-transform:uppercase; color:{C['dark']}; background:#fff;
  border:1.5px solid {C['dark']}; border-radius:5px; padding:4px 10px; box-shadow:2.5px 2.5px 0 0 {C['bleuf']}; }}
.eyebrow {{ font-family:'Carlito',sans-serif; font-weight:700; font-size:8pt; letter-spacing:3px;
  text-transform:uppercase; color:{C['bleuf']}; }}
h1 {{ font-size:25pt; margin:0 0 6px; }}
h1 .accent {{ color:{C['bleuf']}; }}
.lead {{ font-family:'Gelasio',serif; font-style:italic; font-size:12.5pt; color:{C['gris']};
  margin:2px 0 10px; }}
.rule {{ border:0; border-top:1px solid {C['grisc']}; margin:14px 0; }}

h2 {{ font-size:15pt; margin:1.5em 0 .5em; padding-bottom:5px; border-bottom:2px solid {C['bleuf']}; }}
h3 {{ font-size:12pt; margin:1.3em 0 .35em; color:{C['bleuf']}; }}
h4 {{ font-size:10.7pt; margin:1em 0 .3em; color:{C['dark']}; }}
p {{ margin:0 0 .7em; }}
strong {{ color:{C['dark']}; }}
a {{ color:{C['bleuf']}; text-decoration:none; word-break:break-word; }}
ul,ol {{ margin:.3em 0 .9em 1.2em; padding:0; }}
li {{ margin:.22em 0; padding-left:.2em; }}
ul li::marker {{ color:{C['bleuf']}; }}
ol li::marker {{ color:{C['bleuf']}; font-weight:700; font-family:'Gelasio',serif; }}
hr {{ border:0; border-top:1px solid {C['grisc']}; margin:1.1em 0; }}
code {{ font-family:'DejaVu Sans Mono',monospace; font-size:8.8pt; background:{C['grisc']};
  padding:1px 4px; border-radius:3px; color:{C['dark']}; }}

/* Encadres (blockquotes markdown) facon carte a ombre portee */
blockquote {{ position:relative; margin:1.1em 0; padding:14px 18px 14px 20px; background:#fff;
  border:1.8px solid {C['dark']}; border-radius:10px; box-shadow:5px 5px 0 0 rgba(74,123,168,0.22);
  page-break-inside:avoid; }}
blockquote::before {{ content:""; position:absolute; left:0; top:10px; bottom:10px; width:4px;
  background:{C['bleuf']}; border-radius:4px; }}
blockquote > p:first-child strong:first-child {{ font-family:'Gelasio',serif; color:{C['dark']}; }}
blockquote p {{ margin:0 0 .5em; font-size:9.8pt; }}
blockquote p:last-child {{ margin-bottom:0; }}

/* Tableaux LEXVOX */
table {{ border-collapse:collapse; width:100%; margin:1em 0; font-size:9pt;
  border:2px solid {C['dark']}; page-break-inside:avoid; }}
thead {{ background:{C['bleuf']}; }}
th {{ color:#fff; font-family:'Gelasio',serif; font-weight:700; font-size:8.2pt; text-transform:uppercase;
  letter-spacing:.4px; padding:7px 9px; text-align:left; border-right:1px solid rgba(255,255,255,.2); }}
td {{ padding:6px 9px; border-bottom:1px solid {C['grisc']}; vertical-align:top; }}
tbody tr:nth-child(even) {{ background:{C['bleup']}; }}
tbody tr:nth-child(odd) {{ background:#fff; }}

details {{ border:1.8px solid {C['dark']}; border-radius:10px; margin:.7em 0; padding:8px 14px; background:#fff; }}
summary {{ font-family:'Gelasio',serif; font-weight:700; color:{C['dark']}; }}

/* Couverture magazine */
.cover {{ page-break-after:always; position:relative; height:297mm; width:100%;
  background:{C['dark']}; color:{C['creme']}; overflow:hidden; }}
.cover .dots {{ position:absolute; inset:0;
  background-image:radial-gradient(circle, rgba(168,196,224,0.10) 1.1px, transparent 1.1px);
  background-size:26px 26px; opacity:.7; }}
.cover .frame {{ position:absolute; inset:14mm; border:1px solid rgba(250,249,245,0.18); }}
.cover .inner {{ position:absolute; inset:0; padding:34mm 26mm; display:flex; flex-direction:column; }}
.cover .top {{ font-family:'Carlito',sans-serif; font-size:9pt; letter-spacing:5px; text-transform:uppercase;
  color:{C['bleuc']}; }}
.cover .kicker {{ margin-top:auto; font-family:'Carlito',sans-serif; font-size:10pt; letter-spacing:5px;
  text-transform:uppercase; color:{C['or']}; margin-bottom:8px; }}
.cover h1.title {{ font-family:'Gelasio',serif; font-weight:700; font-size:44pt; line-height:1.06;
  color:{C['creme']}; margin:0; border:0; }}
.cover .sub {{ font-family:'Gelasio',serif; font-style:italic; font-size:15pt; color:{C['bleuc']};
  margin-top:14px; max-width:80%; }}
.cover .barre {{ width:70px; height:4px; background:{C['bleuf']}; margin:22px 0 0; }}
.cover .sig {{ margin-top:26px; }}
.cover .sig .by {{ font-family:'Carlito',sans-serif; font-size:8pt; letter-spacing:2px; text-transform:uppercase;
  color:{C['gris']}; }}
.cover .sig .name {{ font-family:'Gelasio',serif; font-weight:700; font-size:16pt; color:{C['creme']}; margin-top:2px; }}
.cover .sig .role {{ font-family:'Carlito',sans-serif; font-size:8.5pt; color:{C['bleuc']}; margin-top:2px; }}
.cover .foot {{ margin-top:28px; padding-top:14px; border-top:1px solid rgba(250,249,245,0.18);
  display:flex; justify-content:space-between; font-family:'Carlito',sans-serif; font-size:8pt;
  letter-spacing:1.5px; text-transform:uppercase; color:{C['gris']}; }}
.cover .brand {{ font-family:'Gelasio',serif; font-weight:700; font-size:15pt; color:{C['creme']}; letter-spacing:1px; }}
.cover .brand .v {{ color:{C['bleu']}; }}

/* Bloc auteur de fin */
.author {{ page-break-inside:avoid; margin-top:2.4em; padding-top:14px; border-top:2px solid {C['dark']}; }}
.author .name {{ font-family:'Gelasio',serif; font-weight:700; font-size:13pt; color:{C['dark']}; }}
.author .cred {{ font-family:'Carlito',sans-serif; font-size:8pt; letter-spacing:1.2px; text-transform:uppercase;
  color:{C['gris']}; line-height:1.7; margin-top:4px; }}
.author .disc {{ font-size:8.5pt; color:{C['gris']}; font-style:italic; margin-top:12px; }}
"""

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

def md_html(path):
    txt = open(os.path.join(ROOT, path), encoding="utf-8").read()
    return markdown.markdown(txt, extensions=["tables", "fenced_code", "sane_lists", "attr_list", "md_in_html"])

def first_title(path):
    if path.endswith(".html"):
        s = open(os.path.join(ROOT, path), encoding="utf-8").read()
        m = re.search(r'<title>(.*?)</title>', s, re.S)
        return m.group(1).strip() if m else os.path.basename(path)
    for line in open(os.path.join(ROOT, path), encoding="utf-8"):
        if line.startswith("# "):
            return line[2:].strip()
    return os.path.basename(path)

AUTHOR = """
<div class="author">
  <div class="name">Maître Patrice Humbert</div>
  <div class="cred">
    Avocat au Barreau d'Aix-en-Provence &middot; Toque 187 &middot; Spécialiste CNB en dommage corporel<br>
    Master en droit de la santé &middot; Formation médicale en traumatisme crânio-cérébral<br>
    SELARL LEXVOX AVOCATS &middot; 4 bureaux en PACA &middot; 04 90 54 58 10 &middot; lexvox-victime.com
  </div>
  <div class="disc">Ce kit est un outil d'information et de preparation. Il ne constitue pas une consultation
  juridique personnalisée et ne remplace pas l'analyse de votre situation par un avocat.
  En cas d'urgence médicale, appelez le 15.</div>
</div>
"""

def cover(kit_title, subtitle, edition):
    return f"""
<div class="cover"><div class="dots"></div><div class="frame"></div>
  <div class="inner">
    <div class="top">SELARL LEXVOX AVOCATS &middot; Guide victime</div>
    <div class="kicker">{edition}</div>
    <h1 class="title">{kit_title}</h1>
    <div class="sub">{subtitle}.</div>
    <div class="barre"></div>
    <div class="sig">
      <div class="by">Conçu et rédigé par</div>
      <div class="name">Maître Patrice Humbert</div>
      <div class="role">Avocat spécialiste CNB en dommage corporel &middot; Barreau d'Aix-en-Provence</div>
    </div>
    <div class="foot">
      <span class="brand">LE<span class="v">X</span>VOX</span>
      <span>Édition 2026 &middot; lexvox-victime.com</span>
    </div>
  </div>
</div>
"""

def build_html(fid, kit_title, subtitle, edition, files, cover_on=True):
    kit_upper = re.sub(r"[^A-Za-z0-9 ']", '', kit_title).upper()
    parts = [f"<style>{css(kit_upper)}</style>"]
    if cover_on:
        parts.append(cover(kit_title, subtitle, edition))
        # sommaire
        toc = [f'<div class="docopen"><div class="chapline"><span class="pill">Sommaire</span>'
               f'<span class="eyebrow">{edition}</span></div><h1>Dans ce guide</h1>'
               f'<div class="lead">{kit_title} : {len(files)} documents.</div><hr class="rule"><ol>']
        for p in files:
            t = first_title(p)
            toc.append(f'<li style="font-family:Gelasio,serif;font-size:11pt;margin:.35em 0"><a href="#{slug(t)}">{t}</a></li>')
        toc.append("</ol></div>")
        parts.append("\n".join(toc))
    for i, p in enumerate(files, 1):
        t = first_title(p)
        body = md_html(p)
        # transformer le premier <h1> du document en ouverture de chapitre
        opener = (f'<div class="docopen"><div class="chapline">'
                  f'<span class="pill">Document {i:02d}</span>'
                  f'<span class="eyebrow">{edition}</span></div>')
        body = re.sub(r'<h1>(.*?)</h1>',
                      opener + rf'<h1 id="{slug(t)}">\1</h1></div>', body, count=1, flags=re.S)
        parts.append(f'<section>{body}</section>')
    parts.append(AUTHOR)
    return "<!doctype html><html lang=fr><head><meta charset=utf-8></head><body>" + "\n".join(parts) + "</body></html>"

def render(html, name):
    hp = os.path.join(OUT, "_tmp_" + name + ".html")
    pp = os.path.join(OUT, name + ".pdf")
    open(hp, "w", encoding="utf-8").write(html)
    cmd = [CHROME, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
           "--print-to-pdf=" + pp, "file://" + hp]
    subprocess.run(cmd, capture_output=True, text=True, timeout=200)
    if os.path.exists(pp):
        os.remove(hp)
        return pp
    return None

def main():
    guides_only = "--guides-only" in sys.argv
    os.makedirs(OUT, exist_ok=True)
    made = []
    for fid, title, sub, edition, files in PALIERS:
        files = [f for f in files if os.path.exists(os.path.join(ROOT, f))]
        if not files:
            continue
        p = render(build_html(fid, title, sub, edition, files, cover_on=True), fid)
        if p:
            made.append(p); print("OK", os.path.relpath(p, ROOT), f"({os.path.getsize(p)//1024} Ko)")
    if not guides_only:
        for fid, title, path in FILLABLES:
            if not os.path.exists(os.path.join(ROOT, path)):
                continue
            p = render(build_html(fid, title, "Version A4 à imprimer et à remplir", "Fichier à remplir",
                                  [path], cover_on=True), fid)
            if p:
                made.append(p); print("OK", os.path.relpath(p, ROOT), f"({os.path.getsize(p)//1024} Ko)")
    print(f"\n{len(made)} PDF generes dans pdf/")
    return 0

if __name__ == "__main__":
    sys.exit(main())
