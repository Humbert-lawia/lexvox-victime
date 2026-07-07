#!/usr/bin/env python3
"""Banc d'essai NeuronWriter — recherche de la méthodologie score >= 90 en un minimum de cycles.

Complète tools/neuronwriter.py (qui reste le client de production). Ce labo ajoute
ce qui manquait aux sessions précédentes (jusqu'à 15 loops aveugles pour 84) :

  1. `terms`    : télécharger et CACHER les termes NLP recommandés d'une query
                  (content_basic / content_extended / entities + fourchettes
                  sugg_usage et cibles title/h1/h2/desc) -> nw-lab/terms-<query>.json.
  2. `audit`    : rapport de couverture LOCAL (zéro appel API) d'un HTML contre le
                  cache de termes : déficits/excès par terme et par zone. Permet de
                  corriger AVANT d'appeler evaluate -> objectif 1-2 cycles API au lieu de 6-15.
  3. `evaluate` : scorer via l'API et JOURNALISER chaque run (score, note de séquence,
                  nb de mots) dans nw-lab/runs-<query>.jsonl — historique loop par loop
                  exigé par le protocole (jamais de score inventé : tout vient de l'API).
  4. `batch`    : scorer plusieurs variantes d'un coup et les classer.
  5. `gpt-draft`: rédacteur alternatif OpenAI/ChatGPT pour les bras S4/S5 du protocole
                  (clé env OPENAI_API_KEY, jamais committée — cf. règle secrets CLAUDE.md).

Usage :
  export NEURONWRITER_API_KEY=...          # secret d'environnement, jamais committé
  python3 tools/nw_lab.py terms <query_id>
  python3 tools/nw_lab.py audit nw-lab/terms-<query_id>.json actualites/<slug>.html
  python3 tools/nw_lab.py evaluate <query_id> actualites/<slug>.html --note "S1-loop1"
  python3 tools/nw_lab.py batch <query_id> fichier1.html fichier2.html ...
  python3 tools/nw_lab.py gpt-draft --brief brief.md [--model gpt-5.1] [--out variante.html]

Prérequis réseau : egress autorisé vers app.neuronwriter.com (et api.openai.com
pour gpt-draft). Voir PROTOCOLE-NW-LAB.md pour le plan d'expériences S0-S6.
"""
import argparse
import datetime
import html as html_mod
import json
import os
import re
import sys
import unicodedata
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import neuronwriter as nw  # noqa: E402  (client API existant : _post, evaluate, get_query)

LAB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "nw-lab")


# ---------------------------------------------------------------- utilitaires
def _norm(s: str) -> str:
    """minuscules + accents retirés, pour un comptage tolérant."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


def _count(term: str, text_norm: str) -> int:
    """Occurrences du terme (frontières de mots, insensible casse/accents)."""
    pat = r"(?<![\w'])" + re.escape(_norm(term)).replace(r"\ ", r"[\s '-]+") + r"(?![\w])"
    return len(re.findall(pat, text_norm))


def _zones(path: str) -> dict:
    """Extrait les zones SEO d'un article HTML de l'atelier."""
    h = open(path, encoding="utf-8", errors="ignore").read()
    get = lambda p: (re.search(p, h, re.S | re.I) or [None, ""])[1]
    body = re.search(r'class="article-content".*?</div>\s*</div>\s*</section>', h, re.S)
    body_html = body.group(0) if body else h
    strip = lambda x: html_mod.unescape(re.sub(r"<[^>]+>", " ", x))
    return {
        "title": strip(get(r"<title>(.*?)</title>")),
        "desc": strip(get(r'name="description" content="(.*?)"')),
        "h1": strip(get(r"<h1[^>]*>(.*?)</h1>")),
        "h2": strip(" ".join(re.findall(r"<h2[^>]*>(.*?)</h2>", h, re.S))),
        "body": strip(body_html),
    }


def _walk_terms(obj, parent="terms", out=None):
    """Extraction tolérante : le format exact de get-query varie selon la version
    de l'API — on récupère toute liste de dicts portant un terme + fourchettes."""
    if out is None:
        out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            _walk_terms(v, k, out)
    elif isinstance(obj, list):
        for it in obj:
            if isinstance(it, dict):
                term = it.get("t") or it.get("term") or it.get("name") or it.get("keyword")
                if isinstance(term, str) and term.strip():
                    rng = it.get("sugg_usage") or it.get("usage") or []
                    lo = rng[0] if isinstance(rng, (list, tuple)) and len(rng) > 0 else it.get("min", 1)
                    hi = rng[1] if isinstance(rng, (list, tuple)) and len(rng) > 1 else it.get("max")
                    out.append({"group": parent, "term": term.strip(),
                                "min": lo or 0, "max": hi,
                                "usage_pc": it.get("usage_pc") or it.get("usage_percent")})
                else:
                    _walk_terms(it, parent, out)
    return out


def _words(path: str) -> int:
    txt = _zones(path)["body"]
    return len(re.findall(r"[\w'’àâéèêëîïôöùûüç-]+", txt))


def _log(query_id: str, entry: dict):
    os.makedirs(LAB_DIR, exist_ok=True)
    entry["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    with open(os.path.join(LAB_DIR, f"runs-{query_id}.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- commandes
def cmd_terms(args):
    resp = nw.get_query(args.query_id)
    os.makedirs(LAB_DIR, exist_ok=True)
    path = os.path.join(LAB_DIR, f"terms-{args.query_id}.json")
    json.dump(resp, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    terms = _walk_terms(resp)
    groups = {}
    for t in terms:
        groups.setdefault(t["group"], []).append(t)
    print(f"Cache écrit : {path}")
    for g, ts in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f"  {g:<20} {len(ts)} termes")
    return 0


def cmd_audit(args):
    data = json.load(open(args.terms_json, encoding="utf-8"))
    terms = _walk_terms(data)
    if not terms:
        sys.exit("Aucun terme reconnu dans le cache — inspecter le JSON à la main.")
    zones = _zones(args.html)
    znorm = {k: _norm(v) for k, v in zones.items()}
    deficits, excess, ok = [], [], 0
    for t in terms:
        n = _count(t["term"], znorm["body"]) + _count(t["term"], znorm["title"]) \
            + _count(t["term"], znorm["h1"]) + _count(t["term"], znorm["h2"])
        lo, hi = t["min"] or 0, t["max"]
        if n < lo:
            deficits.append((t, n))
        elif hi and n > hi:
            excess.append((t, n))
        else:
            ok += 1
    total = len(terms)
    print(f"Audit local — {args.html}")
    print(f"  mots utiles : {_words(args.html)}")
    print(f"  termes dans les fourchettes : {ok}/{total} ({100 * ok // max(total, 1)} %)")
    if deficits:
        print(f"\n  DÉFICITS ({len(deficits)}) — à placer (min requis, trouvé) :")
        for t, n in sorted(deficits, key=lambda x: (x[0]["group"], -(x[0]["min"] or 0))):
            print(f"    [{t['group']}] {t['term']!r} : min {t['min']}, trouvé {n}")
    if excess:
        print(f"\n  EXCÈS ({len(excess)}) — à alléger (max conseillé, trouvé) :")
        for t, n in excess:
            print(f"    [{t['group']}] {t['term']!r} : max {t['max']}, trouvé {n}")
    return 0 if not deficits else 1


def cmd_evaluate(args):
    html = open(args.html, encoding="utf-8", errors="ignore").read()
    resp = nw.evaluate(args.query_id, html)
    score = nw._extract_score(resp)
    if score is None:
        print(json.dumps(resp, ensure_ascii=False, indent=2))
        sys.exit("Score introuvable dans la réponse API (voir brut ci-dessus).")
    _log(args.query_id, {"file": args.html, "score": score, "words": _words(args.html),
                         "note": args.note or ""})
    print(f"score={score} file={args.html} note={args.note or '-'}")
    print(f"(journal : nw-lab/runs-{args.query_id}.jsonl)")
    return 0


def cmd_batch(args):
    results = []
    for path in args.htmls:
        html = open(path, encoding="utf-8", errors="ignore").read()
        score = nw._extract_score(nw.evaluate(args.query_id, html))
        _log(args.query_id, {"file": path, "score": score, "words": _words(path),
                             "note": args.note or "batch"})
        results.append((score if score is not None else -1, path))
        print(f"  {score} — {path}")
    best = max(results)
    print(f"\nMeilleure variante : {best[1]} (score {best[0]})")
    return 0


def cmd_gpt_draft(args):
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        sys.exit("OPENAI_API_KEY absente (secret d'environnement requis, jamais committé).")
    brief = open(args.brief, encoding="utf-8").read()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps({
            "model": args.model,
            "messages": [
                {"role": "system", "content": "Tu es un rédacteur SEO juridique francophone. "
                 "Tu produis du HTML de corps d'article (h2/h3/p/table/details) sans <html> ni <head>, "
                 "en respectant strictement le budget de termes fourni dans le brief."},
                {"role": "user", "content": brief},
            ],
        }).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.loads(r.read().decode("utf-8"))
    text = resp["choices"][0]["message"]["content"]
    if args.out:
        open(args.out, "w", encoding="utf-8").write(text)
        print(f"Écrit : {args.out} ({len(text)} caractères, modèle {args.model})")
    else:
        print(text)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("terms"); s.add_argument("query_id"); s.set_defaults(fn=cmd_terms)
    s = sub.add_parser("audit"); s.add_argument("terms_json"); s.add_argument("html"); s.set_defaults(fn=cmd_audit)
    s = sub.add_parser("evaluate"); s.add_argument("query_id"); s.add_argument("html")
    s.add_argument("--note", default=""); s.set_defaults(fn=cmd_evaluate)
    s = sub.add_parser("batch"); s.add_argument("query_id"); s.add_argument("htmls", nargs="+")
    s.add_argument("--note", default=""); s.set_defaults(fn=cmd_batch)
    s = sub.add_parser("gpt-draft"); s.add_argument("--brief", required=True)
    s.add_argument("--model", default=os.environ.get("OPENAI_MODEL", "gpt-5.1"))
    s.add_argument("--out", default=""); s.set_defaults(fn=cmd_gpt_draft)
    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
