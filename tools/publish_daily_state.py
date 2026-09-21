#!/usr/bin/env python3
"""Etat de la routine de publication quotidienne : file + tracker.

Ce module est l'outil d'etat appele par tools/publish-daily.sh. Il ne publie
rien lui-meme : il lit les files de production, designe les candidats du jour
et enregistre a posteriori ce qui a ete publie.

Trois sites, deux pipelines :
  victime            -> queue-aivf.json, actualites/<slug>.html,
                        PUBLICATION-TRACKER.md          (publication Sanity)
  medical, accident  -> queue-wp.json,  wp-atelier/<site>/<slug>.html,
                        PUBLICATION-TRACKER-WP.md       (publication WordPress)

Commandes :
  candidates <site> [--limit N]
      Liste, en JSON, les items 'todo' dans l'ordre de la file, avec le chemin
      de l'article atelier, son existence et son score NeuronWriter declare.

  mark-done <site> --id N --url URL [--score S] [--post-id P] [--media-id M]
            [--date YYYY-MM-DD] [--published-at ISO]
      Passe l'item en 'done' dans la file et deplace sa ligne du tableau
      « En preparation » vers le tableau « Articles publies » du tracker.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date as date_cls
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

SITES = {
    "victime": {
        "queue": REPO / "queue-aivf.json",
        "atelier": REPO / "actualites",
        "tracker": REPO / "PUBLICATION-TRACKER.md",
        "qa": "tools/qa_article_aivf.py",
    },
    "medical": {
        "queue": REPO / "queue-wp.json",
        "atelier": REPO / "wp-atelier" / "medical",
        "tracker": REPO / "PUBLICATION-TRACKER-WP.md",
        "qa": "tools/qa_article_wp.py",
    },
    "accident": {
        "queue": REPO / "queue-wp.json",
        "atelier": REPO / "wp-atelier" / "accident",
        "tracker": REPO / "PUBLICATION-TRACKER-WP.md",
        "qa": "tools/qa_article_wp.py",
    },
}

NW_RE = re.compile(r"<!--\s*NEURONWRITER SCORE:\s*(\d+)([^>]*)-->")


def die(msg: str) -> None:
    sys.exit(f"ERREUR publish_daily_state : {msg}")


def load_queue(site: str) -> tuple[Path, dict]:
    path = SITES[site]["queue"]
    if not path.exists():
        die(f"{path} introuvable")
    return path, json.loads(path.read_text(encoding="utf-8"))


def json_layout(path: Path) -> tuple[int, str]:
    """Indentation et fin de fichier du JSON existant.

    La file est committee par trois acteurs : reecrire le fichier avec une
    autre mise en forme produirait un diff integral a chaque publication, et
    un conflit a chaque rebase. On rend donc le fichier tel qu'on l'a trouve.
    """
    raw = path.read_text(encoding="utf-8")
    second = raw.split("\n", 2)[1] if "\n" in raw else ""
    indent = len(second) - len(second.lstrip(" ")) or 2
    return indent, "\n" if raw.endswith("\n") else ""


def article_path(site: str, slug: str) -> Path:
    return SITES[site]["atelier"] / f"{slug}.html"


def nw_score(path: Path) -> tuple[int | None, str]:
    """Score NeuronWriter declare dans l'article, et le reste du marqueur."""
    if not path.exists():
        return None, ""
    m = NW_RE.search(path.read_text(encoding="utf-8"))
    if not m:
        return None, ""
    return int(m.group(1)), m.group(2).strip(" -")


def queue_items(site: str, queue: dict) -> list[dict]:
    items = queue["articles"]
    if site == "victime":
        return items
    return [a for a in items if a.get("site") == site]


def cmd_candidates(args: argparse.Namespace) -> int:
    site = args.site
    _, queue = load_queue(site)
    out = []
    for item in queue_items(site, queue):
        if item.get("status") != "todo":
            continue
        path = article_path(site, item["slug"])
        score, note = nw_score(path)
        out.append(
            {
                "id": item["id"],
                "slug": item["slug"],
                "title": item.get("title", ""),
                "silo": item.get("silo", ""),
                "type": item.get("type", "feuille"),
                "ville": item.get("ville", ""),
                "path": str(path.relative_to(REPO)),
                "exists": path.exists(),
                "nw_score": score,
                "nw_note": note,
            }
        )
        if args.limit and len(out) >= args.limit:
            break
    print(json.dumps(out, ensure_ascii=False))
    return 0


def update_queue(site: str, item_id: int, fields: dict) -> dict:
    path, queue = load_queue(site)
    target = None
    for item in queue_items(site, queue):
        if item["id"] == item_id:
            target = item
            break
    if target is None:
        die(f"id {item_id} absent de {path.name} pour le site {site}")
    target.update(fields)
    indent, tail = json_layout(path)
    path.write_text(
        json.dumps(queue, ensure_ascii=False, indent=indent) + tail, encoding="utf-8"
    )
    return target


def tracker_victime(item: dict, url: str, score: str, published_at: str) -> None:
    """Retire la ligne de « En preparation », l'ajoute aux « Articles publies »."""
    path = SITES["victime"]["tracker"]
    lines = path.read_text(encoding="utf-8").split("\n")
    row_re = re.compile(rf"^\|\s*{item['id']}\s*\|")

    published_end = None  # derniere ligne du premier tableau
    in_published = False
    kept = []
    for line in lines:
        if line.startswith("## Articles publiés"):
            in_published = True
        elif line.startswith("## En préparation"):
            in_published = False
        if in_published and line.startswith("|"):
            published_end = len(kept)
        if not in_published and row_re.match(line):
            continue  # ligne « à venir » de cet article : supprimee
        kept.append(line)

    if published_end is None:
        die("tableau « Articles publiés » introuvable dans PUBLICATION-TRACKER.md")

    row = (
        f"| {item['id']} | {item.get('silo', '')} | {item.get('type', '')} | "
        f"{item.get('title', '')} | {url} | {score} | {published_at} |"
    )
    kept.insert(published_end + 1, row)
    path.write_text("\n".join(kept), encoding="utf-8")


def tracker_wp(site: str, item: dict, url: str, score: str, day: str) -> None:
    path = SITES[site]["tracker"]
    lines = path.read_text(encoding="utf-8").split("\n")
    last_row = None
    for i, line in enumerate(lines):
        if line.startswith("| ") and "lexvox-avocat.fr" in line:
            last_row = i
    if last_row is None:
        die("tableau « Articles publiés » introuvable dans PUBLICATION-TRACKER-WP.md")
    row = f"| {day} | {site} | {item['slug']} | {score} | {url} |"
    lines.insert(last_row + 1, row)
    path.write_text("\n".join(lines), encoding="utf-8")


def cmd_mark_done(args: argparse.Namespace) -> int:
    site = args.site
    day = args.date or date_cls.today().isoformat()
    score_val, note = nw_score(article_path(site,_slug_of(site, args.id)))
    score = args.score or (str(score_val) if score_val is not None else "n/c")
    if note and "derogation" in note.lower():
        score += "*"

    fields = {"status": "done", "date": day, "url": args.url}
    if score_val is not None:
        fields["neuronwriter_score"] = score_val
    if args.post_id:
        fields["wp_post_id"] = int(args.post_id)
    if args.media_id:
        fields["wp_media_id"] = int(args.media_id)
    item = update_queue(site, args.id, fields)

    if site == "victime":
        tracker_victime(item, args.url, score, args.published_at or day)
    else:
        tracker_wp(site, item, args.url, score, day)

    print(f"file + tracker mis a jour : id {args.id} ({item['slug']}) -> done")
    return 0


def _slug_of(site: str, item_id: int) -> str:
    _, queue = load_queue(site)
    for item in queue_items(site, queue):
        if item["id"] == item_id:
            return item["slug"]
    die(f"id {item_id} absent de la file du site {site}")
    return ""  # inatteignable


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("candidates", help="items 'todo' dans l'ordre de la file")
    c.add_argument("site", choices=sorted(SITES))
    c.add_argument("--limit", type=int, default=0)
    c.set_defaults(func=cmd_candidates)

    d = sub.add_parser("mark-done", help="enregistre une publication")
    d.add_argument("site", choices=sorted(SITES))
    d.add_argument("--id", type=int, required=True)
    d.add_argument("--url", required=True)
    d.add_argument("--score", default=None)
    d.add_argument("--post-id", default=None)
    d.add_argument("--media-id", default=None)
    d.add_argument("--date", default=None)
    d.add_argument("--published-at", default=None)
    d.set_defaults(func=cmd_mark_done)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
