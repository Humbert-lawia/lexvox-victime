#!/usr/bin/env python3
"""Pont NeuronWriter du pipeline WordPress — applique la methode /nw-optimisation
(audit local zero-API puis score API, budget 2 appels) a un article atelier WP.

Le fichier atelier wp-atelier/<site>/<slug>.html ne contient ni <title>, ni
<meta>, ni <h1> (WordPress les genere depuis les champs title/meta du post -
voir qa_article_wp.py qui interdit justement le <h1> dans le corps). Evaluer /
auditer ce fragment brut sous-noterait artificiellement l'article (categories
title / desc / h1 de NeuronWriter a 0, termes title/h1 non comptes). Ce module
reconstitue la page complete que WordPress affichera (title/meta/h1 injectes
depuis le front-matter WP-META) AVANT toute mesure, exactement comme le fait le
scoreur en production.

Deux sous-commandes, calquees sur tools/nw_lab.py (skill /nw-optimisation) :

  audit  : rapport de couverture LOCAL (zero appel API) du fragment reconstitue
           contre le cache de termes nw-lab/terms-<query>.json. Corriger tous
           les deficits AVANT d'appeler `score` -> objectif 1-2 cycles API.
  score  : evalue la page reconstituee via l'API et JOURNALISE le run dans
           nw-lab/runs-<query>.jsonl (jamais de score invente : tout vient de
           l'API). Seuil bloquant MIN_SCORE (85) herite de neuronwriter.py.

Usage :
  python3 tools/nw_lab.py terms <query_id>                         # cache des termes (1x)
  python3 tools/nw_eval_wp.py audit <query_id> wp-atelier/<site>/<slug>.html
  python3 tools/nw_eval_wp.py score <query_id> wp-atelier/<site>/<slug>.html --note "S1-loop1"
"""
import argparse
import html as html_mod
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import neuronwriter as nw  # noqa: E402  (client API : evaluate, _extract_score, MIN_SCORE)
import nw_lab  # noqa: E402  (primitives partagees : _walk_terms, _count, _norm, _log)

META_RE = re.compile(r"<!--\s*WP-META\s*(\{.*?\})\s*-->", re.S)
NW_MARKER_RE = re.compile(r"<!--\s*NEURONWRITER.*?-->", re.S | re.I)


def _strip(x: str) -> str:
    return html_mod.unescape(re.sub(r"<[^>]+>", " ", x))


def _load(path: str):
    """Retourne (meta, body_html) depuis un fichier atelier WP, marqueurs NW retires."""
    raw = open(path, encoding="utf-8", errors="ignore").read()
    m = META_RE.search(raw)
    if not m:
        sys.exit(f"front-matter WP-META absent dans {path}")
    meta = json.loads(m.group(1))
    for champ in ("title", "metaTitle", "metaDescription"):
        if not meta.get(champ):
            sys.exit(f"champ WP-META '{champ}' manquant dans {path}")
    body = NW_MARKER_RE.sub("", raw[m.end():])
    return meta, body


def wrap(path: str) -> str:
    """Reconstitue la page complete (title/meta/h1) pour l'evaluation API."""
    meta, body = _load(path)
    return (
        f"<html><head><title>{meta['metaTitle']}</title>"
        f'<meta name="description" content="{meta["metaDescription"]}"></head>'
        f"<body><h1>{meta['title']}</h1>{body}</body></html>"
    )


def _zones_wp(path: str) -> dict:
    """Zones SEO d'un article atelier WP, avec le title/meta/h1 du front-matter
    (et non des balises absentes du fragment). Meme decoupage que nw_lab._zones."""
    meta, body = _load(path)
    return {
        "title": _strip(meta["metaTitle"]),
        "desc": _strip(meta["metaDescription"]),
        "h1": _strip(meta["title"]),
        "h2": _strip(" ".join(re.findall(r"<h2[^>]*>(.*?)</h2>", body, re.S | re.I))),
        "body": _strip(body),
    }


def cmd_audit(args) -> int:
    terms_json = os.path.join(nw_lab.LAB_DIR, f"terms-{args.query_id}.json")
    if not os.path.exists(terms_json):
        sys.exit(f"Cache de termes absent : {terms_json}\n"
                 f"Le generer d'abord : python3 tools/nw_lab.py terms {args.query_id}")
    terms = nw_lab._walk_terms(json.load(open(terms_json, encoding="utf-8")))
    if not terms:
        sys.exit("Aucun terme reconnu dans le cache — inspecter le JSON a la main.")
    zones = _zones_wp(args.html)
    znorm = {k: nw_lab._norm(v) for k, v in zones.items()}
    deficits, excess, ok = [], [], 0
    for t in terms:
        n = (nw_lab._count(t["term"], znorm["body"]) + nw_lab._count(t["term"], znorm["title"])
             + nw_lab._count(t["term"], znorm["h1"]) + nw_lab._count(t["term"], znorm["h2"]))
        lo, hi = t["min"] or 0, t["max"]
        if n < lo:
            deficits.append((t, n))
        elif hi and n > hi:
            excess.append((t, n))
        else:
            ok += 1
    total = len(terms)
    words = len(re.findall(r"[\w'’àâéèêëîïôöùûüç-]+", zones["body"]))
    print(f"Audit local (page WP reconstituee) — {args.html}")
    print(f"  mots utiles : {words}")
    print(f"  termes dans les fourchettes : {ok}/{total} ({100 * ok // max(total, 1)} %)")
    if deficits:
        print(f"\n  DEFICITS ({len(deficits)}) — a placer (min requis, trouve) :")
        for t, n in sorted(deficits, key=lambda x: (x[0]["group"], -(x[0]["min"] or 0))):
            print(f"    [{t['group']}] {t['term']!r} : min {t['min']}, trouve {n}")
    if excess:
        print(f"\n  EXCES ({len(excess)}) — sans effet sur le score (loi n2), corriger "
              f"seulement si illisible :")
        for t, n in excess:
            print(f"    [{t['group']}] {t['term']!r} : max {t['max']}, trouve {n}")
    return 0 if not deficits else 1


def cmd_score(args) -> int:
    full_html = wrap(args.html)
    resp = nw.evaluate(args.query_id, full_html)
    score = nw._extract_score(resp)
    if score is None:
        print("Score introuvable — reponse brute :")
        print(json.dumps(resp, ensure_ascii=False, indent=2))
        return 1
    words = len(re.findall(r"[\w'’àâéèêëîïôöùûüç-]+", _zones_wp(args.html)["body"]))
    nw_lab._log(args.query_id, {"file": args.html, "score": score, "words": words,
                                "note": args.note or "wp", "wp_reconstructed": True})
    ok = score >= nw.MIN_SCORE
    print(f"score={score} file={args.html} (page WP reconstituee) "
          f"seuil={nw.MIN_SCORE} -> {'OK' if ok else 'INSUFFISANT'} note={args.note or '-'}")
    print(f"(journal : nw-lab/runs-{args.query_id}.jsonl)")
    return 0 if ok else 1


def main(argv) -> int:
    # Retro-compat : l'ancienne forme `nw_eval_wp.py <query_id> <file>` (sans
    # sous-commande) equivaut desormais a `score` — les prompts/routines qui
    # l'utilisent encore continuent de fonctionner.
    if argv and argv[0] not in ("audit", "score", "-h", "--help"):
        argv = ["score"] + argv
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("audit", help="couverture locale zero-API (page reconstituee)")
    s.add_argument("query_id"); s.add_argument("html"); s.set_defaults(fn=cmd_audit)
    s = sub.add_parser("score", help="evalue via l'API et journalise")
    s.add_argument("query_id"); s.add_argument("html")
    s.add_argument("--note", default=""); s.set_defaults(fn=cmd_score)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
