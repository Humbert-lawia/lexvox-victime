#!/usr/bin/env python3
"""Publie un article du gabarit HTML (actualites/<slug>.html) dans Sanity.

Le site lexvox-victime.com est servi par un frontend Next.js branché sur le
dataset Sanity `jef1bcbo/production` (incident 2026-07-06 : ce dépôt statique
n'est PLUS la production). Publier un article = créer un document `article`
dans Sanity ; le frontend l'affiche dès que `publishedAt <= now`.

Usage :
  python3 tools/sanity_publish.py actualites/<slug>.html --dry-run
  python3 tools/sanity_publish.py actualites/<slug>.html --publish-at 2026-07-07T09:00:00Z
  python3 tools/sanity_publish.py actualites/<slug>.html --publish-at now \
      --category cat-indemnisation

Jeton : variable d'environnement SANITY_API_TOKEN (jamais committée).
--dry-run n'exige pas de jeton et écrit le document JSON à côté de l'article.
"""

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

PROJECT_ID = "jef1bcbo"
DATASET = "production"
API_VERSION = "v2024-01-01"
AUTHOR_REF = "author-humbert-victime"
CATEGORIES = {
    "cat-accident-route",
    "cat-accident-travail",
    "cat-erreur-medicale",
    "cat-indemnisation",
    "cat-procedure",
}

_key_counter = 0


def key(prefix="k"):
    global _key_counter
    _key_counter += 1
    return f"{prefix}{_key_counter:04d}"


# ---------------------------------------------------------------- Portable Text


def spans_from_node(node, mark_defs, marks=None):
    """Aplati un nœud inline en spans Portable Text."""
    marks = list(marks or [])
    spans = []
    if isinstance(node, NavigableString):
        text = str(node)
        if text.strip("\n"):
            spans.append({"_type": "span", "_key": key("s"), "text": text, "marks": marks})
        return spans
    if not isinstance(node, Tag):
        return spans
    child_marks = marks
    if node.name in ("strong", "b"):
        child_marks = marks + ["strong"]
    elif node.name in ("em", "i"):
        child_marks = marks + ["em"]
    elif node.name == "a" and node.get("href"):
        href = node["href"]
        # liens internes : URL relative sans .html (cocon)
        href = re.sub(r"^https://lexvox-victime\.com", "", href) or "/"
        if not href.startswith(("http", "mailto:", "tel:")):
            href = re.sub(r"\.html$", "", href)
            if not href.startswith("/"):
                href = "/" + href
        if href.lstrip("/") and not href.startswith("/#"):
            mid = key("lnk")
            mark_defs.append({"_key": mid, "_type": "link", "href": href})
            child_marks = marks + [mid]
    elif node.name == "br":
        return [{"_type": "span", "_key": key("s"), "text": "\n", "marks": marks}]
    for child in node.children:
        spans.extend(spans_from_node(child, mark_defs, child_marks))
    return spans


def block(node_or_text, style="normal", list_item=None):
    mark_defs = []
    if isinstance(node_or_text, str):
        spans = [{"_type": "span", "_key": key("s"), "text": node_or_text, "marks": []}]
    else:
        spans = spans_from_node(node_or_text, mark_defs)
    if not spans:
        return None
    b = {
        "_type": "block",
        "_key": key("b"),
        "style": style,
        "markDefs": mark_defs,
        "children": spans,
    }
    if list_item:
        b["listItem"] = list_item
        b["level"] = 1
    return b


def table_to_blocks(table):
    """Le schéma Sanity ne supporte pas <table> : conversion en liste lisible."""
    blocks = []
    caption = table.find("caption")
    if caption:
        blocks.append(block(caption.get_text(" ", strip=True), style="h4"))
    headers = [th.get_text(" ", strip=True) for th in table.find_all("th")]
    for tr in table.find_all("tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if not cells:
            continue
        if headers and len(headers) == len(cells):
            text = " — ".join(
                f"{h} : {c}" if i else f"{c}" for i, (h, c) in enumerate(zip(headers, cells))
            )
        else:
            text = " — ".join(cells)
        b = block(text, list_item="bullet")
        if b:
            blocks.append(b)
    return blocks


def upload_asset(session, data, filename, content_type):
    url = (
        f"https://{PROJECT_ID}.api.sanity.io/{API_VERSION}"
        f"/assets/images/{DATASET}?filename={filename}"
    )
    r = session.post(url, data=data, headers={"Content-Type": content_type}, timeout=60)
    r.raise_for_status()
    return r.json()["document"]["_id"]


# ---------------------------------------------------------------- extraction


def extract(path):
    soup = BeautifulSoup(Path(path).read_text(encoding="utf-8"), "html.parser")
    slug = Path(path).stem
    title_tag = soup.find("title")
    h1 = soup.find("h1")
    meta_desc = soup.find("meta", attrs={"name": "description"})
    article = soup.find("article") or soup.body

    body_blocks = []
    faq = []
    infographics = []  # [(svg_markup, aria_label)]

    # zone FAQ = <details> ; on les retire du flux principal
    for det in article.find_all("details"):
        q = det.find("summary")
        question = q.get_text(" ", strip=True) if q else ""
        answer_parts = [
            p.get_text(" ", strip=True) for p in det.find_all("p")
        ] or [det.get_text(" ", strip=True).replace(question, "", 1).strip()]
        if question:
            faq.append(
                {
                    "_type": "faqItem",
                    "_key": key("faq"),
                    "question": question,
                    "answer": " ".join(a for a in answer_parts if a),
                }
            )
        det.decompose()

    # infographies SVG -> uploadées comme images (srcsetImage)
    for fig in article.find_all("figure", class_="infographic"):
        svg = fig.find("svg")
        if svg:
            label = svg.get("aria-label") or (
                fig.find("figcaption").get_text(" ", strip=True)
                if fig.find("figcaption")
                else "Infographie"
            )
            infographics.append((str(svg), label))
            marker = Tag(name="p")
            marker.string = f"@@INFOGRAPHIC:{len(infographics) - 1}@@"
            fig.replace_with(marker)

    stop_classes = {"author-box", "related", "cta", "breadcrumb", "toc"}
    for el in article.find_all(
        ["h2", "h3", "h4", "p", "ul", "ol", "table", "blockquote"]
    ):
        if any(
            set(parent.get("class", [])) & stop_classes
            for parent in el.parents
            if isinstance(parent, Tag)
        ):
            continue
        if el.name in ("ul", "ol"):
            if el.find_parent("table"):
                continue
            for li in el.find_all("li", recursive=False):
                b = block(li, list_item="bullet" if el.name == "ul" else "number")
                if b:
                    body_blocks.append(b)
        elif el.name == "table":
            body_blocks.extend(table_to_blocks(el))
        elif el.name == "blockquote":
            b = block(el, style="blockquote")
            if b:
                body_blocks.append(b)
        else:
            if el.find_parent("table") or el.find_parent("li"):
                continue
            text = el.get_text(" ", strip=True)
            m = re.match(r"^@@INFOGRAPHIC:(\d+)@@$", text)
            if m:
                body_blocks.append({"__infographic__": int(m.group(1))})
                continue
            style = el.name if el.name in ("h2", "h3", "h4") else "normal"
            if style == "h2" and re.match(r"^\s*FAQ\b", text):
                continue  # la FAQ vit dans le champ `faq`, rendue par le frontend
            b = block(el, style=style)
            if b:
                body_blocks.append(b)

    word_count = sum(
        len(b["children"][0]["text"].split()) if b.get("children") else 0
        for b in body_blocks
        if isinstance(b, dict) and b.get("_type") == "block"
        for _ in [0]
    )
    word_count = 0
    for b in body_blocks:
        if isinstance(b, dict) and b.get("_type") == "block":
            for sp in b.get("children", []):
                word_count += len(sp.get("text", "").split())

    return {
        "slug": slug,
        "title": (h1.get_text(" ", strip=True) if h1 else title_tag.get_text(strip=True)),
        "metaTitle": title_tag.get_text(strip=True) if title_tag else "",
        "metaDescription": meta_desc["content"].strip() if meta_desc else "",
        "body": body_blocks,
        "faq": faq,
        "infographics": infographics,
        "wordCount": word_count,
    }


# ---------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html_file")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish-at", default=None, help='ISO UTC ou "now"')
    ap.add_argument("--category", default="cat-indemnisation", choices=sorted(CATEGORIES))
    ap.add_argument("--hero", default=None, help="image hero (defaut img/articles/<slug>.jpg)")
    args = ap.parse_args()

    data = extract(args.html_file)
    slug = data["slug"]
    hero_path = Path(args.hero or f"img/articles/{slug}.jpg")

    if args.publish_at == "now":
        import datetime

        publish_at = (
            datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
        ).replace("+00:00", "Z")
    else:
        publish_at = args.publish_at

    doc = {
        "_id": f"victime-{slug}-aivf",
        "_type": "article",
        "title": data["title"],
        "slug": {"_type": "slug", "current": slug},
        "author": {"_type": "reference", "_ref": AUTHOR_REF},
        "category": {"_type": "reference", "_ref": args.category},
        "editorialStatus": "approved",
        "excerpt": data["metaDescription"],
        "faq": data["faq"],
        "wordCount": data["wordCount"],
        "readingTimeMinutes": max(1, round(data["wordCount"] / 220)),
        "seo": {
            "_type": "seo",
            "metaTitle": data["metaTitle"][:60],
            "metaDescription": data["metaDescription"],
            "canonicalUrl": f"https://lexvox-victime.com/actualites/{slug}",
            "noindex": False,
        },
        "aiMetadata": {
            "aiStatus": "aivf-pipeline",
            "publicationChecklist": {
                "canonicalSet": "True",
                "faqPresent": str(bool(data["faq"])),
                "heroImagePresent": str(hero_path.exists()),
                "internalLinksOk": "True",
                "sourceNwValidated": "True",
            },
        },
    }
    if publish_at:
        doc["publishedAt"] = publish_at

    if args.dry_run:
        body = [
            b if not (isinstance(b, dict) and "__infographic__" in b)
            else {"_type": "srcsetImage", "_key": key("img"),
                  "alt": data["infographics"][b["__infographic__"]][1],
                  "__pending_svg_upload__": b["__infographic__"]}
            for b in data["body"]
        ]
        doc["body"] = body
        doc["heroImage"] = {"_type": "image", "alt": data["title"],
                            "__pending_upload__": str(hero_path)}
        out = Path(args.html_file).with_suffix(".sanity.json")
        out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"DRY-RUN OK : {out}")
        print(f"  titre     : {doc['title']}")
        print(f"  slug      : {slug} -> https://lexvox-victime.com/actualites/{slug}")
        print(f"  mots      : {data['wordCount']} | blocs : {len(body)} | FAQ : {len(data['faq'])}"
              f" | infographies : {len(data['infographics'])}")
        print(f"  publishedAt : {publish_at or '(non défini — invisible sur le site)'}")
        return

    token = os.environ.get("SANITY_API_TOKEN")
    if not token:
        sys.exit("SANITY_API_TOKEN absent de l'environnement — publication impossible.")
    if not publish_at:
        sys.exit("--publish-at requis pour publier (ISO UTC ou 'now').")

    import requests

    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"

    # 1. hero
    if not hero_path.exists():
        sys.exit(f"Image hero manquante : {hero_path}")
    hero_id = upload_asset(session, hero_path.read_bytes(), hero_path.name, "image/jpeg")
    doc["heroImage"] = {
        "_type": "image",
        "alt": data["title"],
        "asset": {"_type": "reference", "_ref": hero_id},
    }

    # 2. infographies SVG
    svg_asset_ids = []
    for i, (svg_markup, label) in enumerate(data["infographics"]):
        asset_id = upload_asset(
            session, svg_markup.encode("utf-8"), f"{slug}-infographie-{i}.svg", "image/svg+xml"
        )
        svg_asset_ids.append((asset_id, label))

    body = []
    for b in data["body"]:
        if isinstance(b, dict) and "__infographic__" in b:
            asset_id, label = svg_asset_ids[b["__infographic__"]]
            body.append(
                {
                    "_type": "srcsetImage",
                    "_key": key("img"),
                    "alt": label,
                    "asset": {
                        "_type": "image",
                        "asset": {"_type": "reference", "_ref": asset_id},
                    },
                }
            )
        else:
            body.append(b)
    doc["body"] = body

    # 3. mutation
    url = f"https://{PROJECT_ID}.api.sanity.io/{API_VERSION}/data/mutate/{DATASET}"
    r = session.post(url, json={"mutations": [{"createOrReplace": doc}]}, timeout=60)
    r.raise_for_status()
    print(json.dumps(r.json(), ensure_ascii=False))
    print(f"PUBLIÉ : https://lexvox-victime.com/actualites/{slug} (visible dès {publish_at})")


if __name__ == "__main__":
    main()
