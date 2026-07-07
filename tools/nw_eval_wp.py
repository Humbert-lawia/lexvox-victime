#!/usr/bin/env python3
"""Evalue un article atelier WP avec NeuronWriter en reconstituant la page
complete (title/meta/h1) que WordPress affichera reellement.

Le fichier atelier wp-atelier/<site>/<slug>.html ne contient ni <title>, ni
<meta>, ni <h1> (WordPress les genere depuis les champs title/meta du post -
voir qa_article_wp.py qui interdit justement le <h1> dans le corps). Evaluer
ce fragment brut avec tools/neuronwriter.py sous-note artificiellement le
score (categories title/desc_title/h1 de NeuronWriter toujours a 0). Ce
script enveloppe le corps avec les champs du front-matter WP-META avant
evaluation, pour un score representatif de la page publiee.

Usage :
  python3 tools/nw_eval_wp.py <query_id> wp-atelier/<site>/<slug>.html
"""
import json
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import neuronwriter as nw  # noqa: E402

META_RE = re.compile(r"<!--\s*WP-META\s*(\{.*?\})\s*-->", re.S)
NW_MARKER_RE = re.compile(r"<!--\s*NEURONWRITER.*?-->", re.S | re.I)


def wrap(path: str) -> str:
    html = open(path, encoding="utf-8", errors="ignore").read()
    m = META_RE.search(html)
    if not m:
        sys.exit("front-matter WP-META absent")
    meta = json.loads(m.group(1))
    body = NW_MARKER_RE.sub("", html[m.end():])
    return (
        f"<html><head><title>{meta['metaTitle']}</title>"
        f'<meta name="description" content="{meta["metaDescription"]}"></head>'
        f"<body><h1>{meta['title']}</h1>{body}</body></html>"
    )


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 1
    query_id, path = argv
    full_html = wrap(path)
    resp = nw.evaluate(query_id, full_html)
    score = nw._extract_score(resp)
    if score is None:
        print("Score introuvable — reponse brute :")
        print(json.dumps(resp, ensure_ascii=False, indent=2))
        return 1
    ok = score >= nw.MIN_SCORE
    print(f"NeuronWriter content score (page complete reconstituee) : {score} "
          f"(seuil {nw.MIN_SCORE}) -> {'OK' if ok else 'INSUFFISANT'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
