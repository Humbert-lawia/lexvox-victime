#!/usr/bin/env python3
"""Convertit une fiche cabinet (Markdown) en .pdf + .docx pour NotebookLM.

Le .pdf est la source n°2 televersee dans chaque notebook ; le .docx permet
a Me Humbert de relire ou retoucher le texte dans Google Docs ou Word.

Aucune dependance : bibliotheque standard uniquement (ni LibreOffice, ni
reportlab, ni python-docx), pour que l'outil tourne aussi bien sur le poste
de Me Humbert que dans une session distante.

Le contenu situe apres le marqueur <!-- FIN DU DOCUMENT PDF --> est ignore
(notes internes, journal de validation). Une fiche contenant encore une
mention « A VALIDER » est refusee : elle partirait telle quelle dans l'audio.

Usage :
    python3 tools/fiche_to_pdf.py podcasts/fiche-cabinet-victimes.md
    python3 tools/fiche_to_pdf.py podcasts/fiche-cabinet-*.md
"""

import re
import sys
import unicodedata
import xml.sax.saxutils as xml_escape
import zipfile
from pathlib import Path

MARQUEUR_FIN = "<!-- FIN DU DOCUMENT PDF -->"

# --- Mise en page (points PostScript, A4) ------------------------------------
PAGE_L, PAGE_H = 595.28, 841.89
MARGE_G, MARGE_D, MARGE_HAUT, MARGE_BAS = 62.0, 62.0, 70.0, 62.0
LARGEUR_TEXTE = PAGE_L - MARGE_G - MARGE_D

STYLES = {  # (police, corps, interligne, espace avant, retrait)
    "h1": ("F2", 19.0, 24.0, 0.0, 0.0),
    "h2": ("F2", 13.5, 18.0, 16.0, 0.0),
    "p": ("F1", 11.5, 16.0, 5.0, 0.0),
    "quote": ("F3", 11.5, 16.5, 8.0, 26.0),
}

# Largeurs Times-Roman (unites/1000). Les glyphes accentues reprennent la
# largeur de leur lettre de base, conformement a l'AFM.
LARGEURS = {
    " ": 250, "!": 333, '"': 408, "#": 500, "$": 500, "%": 833, "&": 778,
    "'": 333, "(": 333, ")": 333, "*": 500, "+": 564, ",": 250, "-": 333,
    ".": 250, "/": 278, ":": 278, ";": 278, "<": 564, "=": 564, ">": 564,
    "?": 444, "@": 921, "[": 333, "\\": 278, "]": 333, "^": 469, "_": 500,
    "`": 333, "{": 480, "|": 200, "}": 480, "~": 541,
    "A": 722, "B": 667, "C": 667, "D": 722, "E": 611, "F": 556, "G": 722,
    "H": 722, "I": 333, "J": 389, "K": 722, "L": 611, "M": 889, "N": 722,
    "O": 722, "P": 556, "Q": 722, "R": 667, "S": 556, "T": 611, "U": 722,
    "V": 722, "W": 944, "X": 722, "Y": 722, "Z": 611,
    "a": 444, "b": 500, "c": 444, "d": 500, "e": 444, "f": 333, "g": 500,
    "h": 500, "i": 278, "j": 278, "k": 500, "l": 278, "m": 778, "n": 500,
    "o": 500, "p": 500, "q": 500, "r": 333, "s": 389, "t": 278, "u": 500,
    "v": 500, "w": 722, "x": 500, "y": 500, "z": 444,
    "’": 333, "‘": 333, "“": 444, "”": 444,
    "—": 1000, "–": 500, "…": 1000, "«": 500,
    "»": 500, "°": 400, "€": 500, " ": 250,
}
for chiffre in "0123456789":
    LARGEURS[chiffre] = 500


def largeur_caractere(car: str) -> int:
    if car in LARGEURS:
        return LARGEURS[car]
    base = unicodedata.normalize("NFD", car)[0]  # e accent aigu -> e
    return LARGEURS.get(base, 500)


def largeur_texte(texte: str, corps: float, gras: bool) -> float:
    total = sum(largeur_caractere(c) for c in texte) / 1000.0 * corps
    return total * (1.045 if gras else 1.0)


# --- Lecture du Markdown -----------------------------------------------------
def lire_blocs(texte: str):
    """Retourne une liste de (style, texte) : h1, h2, p, quote."""
    corps, sep, _ = texte.partition(MARQUEUR_FIN)
    if not sep:
        print("  ! marqueur de fin absent : document converti en entier",
              file=sys.stderr)

    blocs, tampon, citation = [], [], []

    def vider(cible, style):
        if cible:
            blocs.append((style, " ".join(cible)))
            cible.clear()

    for ligne in corps.splitlines():
        ligne = ligne.rstrip()
        if ligne.startswith("<!--") or ligne.strip() == "---":
            continue
        if ligne.startswith("> "):
            vider(tampon, "p")
            citation.append(nettoyer(ligne[2:]))
            continue
        vider(citation, "quote")
        if not ligne.strip():
            vider(tampon, "p")
        elif ligne.startswith("## "):
            vider(tampon, "p")
            blocs.append(("h2", nettoyer(ligne[3:])))
        elif ligne.startswith("# "):
            vider(tampon, "p")
            blocs.append(("h1", nettoyer(ligne[2:])))
        else:
            tampon.append(nettoyer(ligne))
    vider(tampon, "p")
    vider(citation, "quote")
    return blocs


def nettoyer(fragment: str) -> str:
    fragment = re.sub(r"\*\*(.+?)\*\*", r"\1", fragment)
    return re.sub(r"`(.+?)`", r"\1", fragment).strip()


def couper_lignes(texte: str, corps: float, gras: bool, largeur: float):
    lignes, courante = [], ""
    for mot in texte.split():
        essai = f"{courante} {mot}".strip()
        if courante and largeur_texte(essai, corps, gras) > largeur:
            lignes.append(courante)
            courante = mot
        else:
            courante = essai
    if courante:
        lignes.append(courante)
    return lignes or [""]


# --- Generation du PDF -------------------------------------------------------
def echapper_pdf(texte: str) -> bytes:
    octets = texte.encode("cp1252", errors="replace")
    for motif, remplacement in ((b"\\", b"\\\\"), (b"(", b"\\("),
                                (b")", b"\\)")):
        octets = octets.replace(motif, remplacement)
    return octets


def composer_pages(blocs):
    pages, page, y = [], [], PAGE_H - MARGE_HAUT
    for style, texte in blocs:
        police, corps, interligne, avant, retrait = STYLES[style]
        gras = police == "F2"
        y -= avant
        for ligne in couper_lignes(texte, corps, gras,
                                   LARGEUR_TEXTE - retrait):
            if y - interligne < MARGE_BAS:
                pages.append(page)
                page, y = [], PAGE_H - MARGE_HAUT
            y -= interligne
            page.append((MARGE_G + retrait, y, police, corps, ligne))
    if page:
        pages.append(page)
    return pages


def ecrire_pdf(pages, destination: Path):
    objets = []  # corps de chaque objet, indice 0 = objet 1

    def ajouter(corps: bytes) -> int:
        objets.append(corps)
        return len(objets)

    numero_catalogue = ajouter(b"")   # 1, complete plus bas
    numero_pages = ajouter(b"")       # 2, complete plus bas
    polices = {
        "F1": ajouter(b"<< /Type /Font /Subtype /Type1 /BaseFont "
                      b"/Times-Roman /Encoding /WinAnsiEncoding >>"),
        "F2": ajouter(b"<< /Type /Font /Subtype /Type1 /BaseFont "
                      b"/Times-Bold /Encoding /WinAnsiEncoding >>"),
        "F3": ajouter(b"<< /Type /Font /Subtype /Type1 /BaseFont "
                      b"/Times-Italic /Encoding /WinAnsiEncoding >>"),
    }
    ressources = ("<< /Font << " + " ".join(
        f"/{nom} {num} 0 R" for nom, num in polices.items()) + " >> >>")

    numeros_pages = []
    for lignes in pages:
        flux = []
        for x, y, police, corps, texte in lignes:
            flux.append(b"BT /" + police.encode() + b" "
                        + f"{corps:.2f}".encode() + b" Tf "
                        + f"1 0 0 1 {x:.2f} {y:.2f}".encode() + b" Tm ("
                        + echapper_pdf(texte) + b") Tj ET")
        contenu = b"\n".join(flux)
        numero_flux = ajouter(b"<< /Length " + str(len(contenu)).encode()
                              + b" >>\nstream\n" + contenu + b"\nendstream")
        numeros_pages.append(ajouter(
            f"<< /Type /Page /Parent {numero_pages} 0 R /MediaBox "
            f"[0 0 {PAGE_L:.2f} {PAGE_H:.2f}] /Resources {ressources} "
            f"/Contents {numero_flux} 0 R >>".encode()))

    objets[numero_catalogue - 1] = (
        f"<< /Type /Catalog /Pages {numero_pages} 0 R >>".encode())
    objets[numero_pages - 1] = (
        "<< /Type /Pages /Kids ["
        + " ".join(f"{n} 0 R" for n in numeros_pages)
        + f"] /Count {len(numeros_pages)} >>").encode()

    sortie = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    decalages = []
    for indice, corps in enumerate(objets, start=1):
        decalages.append(len(sortie))
        sortie += f"{indice} 0 obj\n".encode() + corps + b"\nendobj\n"
    depart_xref = len(sortie)
    sortie += f"xref\n0 {len(objets) + 1}\n".encode()
    sortie += b"0000000000 65535 f \n"
    for decalage in decalages:
        sortie += f"{decalage:010d} 00000 n \n".encode()
    sortie += (f"trailer\n<< /Size {len(objets) + 1} /Root "
               f"{numero_catalogue} 0 R >>\nstartxref\n{depart_xref}\n"
               "%%EOF\n").encode()
    destination.write_bytes(bytes(sortie))


# --- Generation du DOCX ------------------------------------------------------
DOCX_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

DOCX_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

DOCX_DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def style_docx(identifiant, nom, taille, gras, italique, avant):
    return (
        f'<w:style w:type="paragraph" w:styleId="{identifiant}">'
        f'<w:name w:val="{nom}"/><w:qFormat/><w:pPr>'
        f'<w:spacing w:before="{avant}" w:after="80" w:line="276" '
        f'w:lineRule="auto"/></w:pPr><w:rPr>'
        f'<w:rFonts w:ascii="Georgia" w:hAnsi="Georgia"/>'
        f'{"<w:b/>" if gras else ""}{"<w:i/>" if italique else ""}'
        f'<w:sz w:val="{taille}"/></w:rPr></w:style>')


DOCX_STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<w:styles {W}>'
    + style_docx("Title", "Title", 38, True, False, 0)
    + style_docx("Heading1", "heading 1", 27, True, False, 320)
    + style_docx("Normal", "Normal", 23, False, False, 0)
    + style_docx("Quote", "Quote", 23, False, True, 160)
    + "</w:styles>")

CORRESPONDANCE_DOCX = {"h1": "Title", "h2": "Heading1", "p": "Normal",
                       "quote": "Quote"}


def ecrire_docx(blocs, destination: Path):
    paragraphes = []
    for style, texte in blocs:
        nom = CORRESPONDANCE_DOCX[style]
        retrait = ('<w:ind w:left="454"/>' if style == "quote" else "")
        paragraphes.append(
            f'<w:p><w:pPr><w:pStyle w:val="{nom}"/>{retrait}</w:pPr>'
            f'<w:r><w:t xml:space="preserve">'
            f'{xml_escape.escape(texte)}</w:t></w:r></w:p>')
    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<w:document {W}><w:body>' + "".join(paragraphes)
                + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
                  '<w:pgMar w:top="1418" w:right="1247" w:bottom="1247" '
                  'w:left="1247"/></w:sectPr></w:body></w:document>')

    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", DOCX_TYPES)
        archive.writestr("_rels/.rels", DOCX_RELS)
        archive.writestr("word/_rels/document.xml.rels", DOCX_DOC_RELS)
        archive.writestr("word/styles.xml", DOCX_STYLES)
        archive.writestr("word/document.xml", document)


# --- Pilotage ----------------------------------------------------------------
def convertir(source: Path) -> int:
    if not source.is_file():
        print(f"  ! introuvable : {source}", file=sys.stderr)
        return 1
    contenu = source.read_text(encoding="utf-8")
    diffuse = contenu.partition(MARQUEUR_FIN)[0]
    if "A VALIDER" in diffuse.upper() or "⚠" in diffuse:
        print(f"  ! {source.name} contient encore des mentions a valider — "
              "conversion refusee (la fiche partirait telle quelle dans "
              "l'audio).", file=sys.stderr)
        return 2

    blocs = lire_blocs(contenu)
    if not blocs:
        print(f"  ! {source.name} : aucun contenu a convertir",
              file=sys.stderr)
        return 2

    pdf = source.with_suffix(".pdf")
    docx = source.with_suffix(".docx")
    ecrire_pdf(composer_pages(blocs), pdf)
    ecrire_docx(blocs, docx)
    print(f"  ✓ {pdf} ({pdf.stat().st_size // 1024} Ko)")
    print(f"  ✓ {docx} ({docx.stat().st_size // 1024} Ko)")
    return 0


def main() -> int:
    cibles = [Path(argument) for argument in sys.argv[1:]]
    if not cibles:
        print(__doc__)
        return 1
    return max(convertir(cible) for cible in cibles)


if __name__ == "__main__":
    sys.exit(main())
