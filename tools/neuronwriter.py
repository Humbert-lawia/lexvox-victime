#!/usr/bin/env python3
"""Client NeuronWriter pour le PIPELINE LEXVOX-AIVF (scoring d'optimisation SEO).

Optimisation NeuronWriter = contrainte NON NEGOCIABLE : score >= 85 par article.
Ce client interroge l'API NeuronWriter pour obtenir le content score d'un article,
afin que la routine de production puisse refuser de publier en dessous de 85.

API : base https://app.neuronwriter.com/neuron-api/0.5/writer , header X-API-KEY.
La cle vient de la variable d'environnement NEURONWRITER_API_KEY (SECRET : jamais
committee — GitHub Actions secret ou variable Cloudflare, cf. regle 5 de CLAUDE.md).

Endpoints utilises :
  POST /list-projects    {}                                            -> [ { project, name, ... } ]
  POST /new-query        { project, keyword, engine, language }        -> { query }
  GET  /get-query        { query }                                     -> { status, terms... }
  POST /evaluate-content { query, html }                               -> { content_score, ... }

Usage :
  export NEURONWRITER_API_KEY=xxxx
  python3 tools/neuronwriter.py list-projects                         # decouvrir le project_id
  python3 tools/neuronwriter.py new-query <project_id> "bareme pretium doloris"
  python3 tools/neuronwriter.py evaluate <query_id> actualites/<slug>.html
      -> imprime le score et sort 0 si >= 85, 1 sinon (gate de publication).

NB : le nom de champ exact de /evaluate-content (html vs content) et du score
(content_score vs score) peut varier selon la version de l'API ; le parsing est
tolerant et, s'il ne trouve pas le score, imprime la reponse brute pour ajuster.
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = "https://app.neuronwriter.com/neuron-api/0.5/writer"
MIN_SCORE = 85
SCORE_KEYS = ("content_score", "score", "seo_score", "contentScore")


def _api_key() -> str:
    key = os.environ.get("NEURONWRITER_API_KEY", "").strip()
    if not key:
        sys.exit("NEURONWRITER_API_KEY absente (secret d'environnement requis).")
    return key


def _post(path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"{BASE}/{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-API-KEY": _api_key()},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def list_projects() -> dict:
    return _post("list-projects", {})


def new_query(project: str, keyword: str, engine: str = "google.fr", language: str = "French") -> dict:
    return _post("new-query", {"project": project, "keyword": keyword, "engine": engine, "language": language})


def get_query(query_id: str) -> dict:
    return _post("get-query", {"query": query_id})


def evaluate(query_id: str, html: str) -> dict:
    return _post("evaluate-content", {"query": query_id, "html": html})


def _extract_score(resp: dict):
    for k in SCORE_KEYS:
        if isinstance(resp.get(k), (int, float)):
            return resp[k]
    # parfois imbrique sous "content" ou "metrics"
    for parent in ("content", "metrics", "result"):
        sub = resp.get(parent)
        if isinstance(sub, dict):
            for k in SCORE_KEYS:
                if isinstance(sub.get(k), (int, float)):
                    return sub[k]
    return None


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    cmd = argv[0]
    try:
        if cmd == "list-projects":
            print(json.dumps(list_projects(), ensure_ascii=False, indent=2))
            return 0
        if cmd == "new-query" and len(argv) >= 3:
            print(json.dumps(new_query(argv[1], " ".join(argv[2:])), ensure_ascii=False, indent=2))
            return 0
        if cmd == "get-query" and len(argv) == 2:
            print(json.dumps(get_query(argv[1]), ensure_ascii=False, indent=2))
            return 0
        if cmd == "evaluate" and len(argv) == 3:
            html = open(argv[2], encoding="utf-8", errors="ignore").read()
            resp = evaluate(argv[1], html)
            score = _extract_score(resp)
            if score is None:
                print("Score introuvable dans la reponse — reponse brute :")
                print(json.dumps(resp, ensure_ascii=False, indent=2))
                return 1
            ok = score >= MIN_SCORE
            print(f"NeuronWriter content score : {score} (seuil {MIN_SCORE}) -> {'OK' if ok else 'INSUFFISANT'}")
            return 0 if ok else 1
    except urllib.error.HTTPError as e:
        sys.exit(f"Erreur API NeuronWriter {e.code} : {e.read().decode('utf-8', 'ignore')[:300]}")
    except urllib.error.URLError as e:
        sys.exit(f"Reseau NeuronWriter injoignable : {e}")
    print("Commande invalide. Voir l'entete du fichier pour l'usage.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
