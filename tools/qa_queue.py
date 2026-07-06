#!/usr/bin/env python3
"""Applique qa_article_aivf sur tous les articles publies du PIPELINE LEXVOX-AIVF.

Lit queue-aivf.json et valide chaque item status:"done" contre le standard
augmente (via qa_article_aivf.check). Les articles herites (hors file) ne sont
PAS soumis au standard : la CI reste verte sur l'existant, mais tout nouvel
article du pipeline est bloquant s'il n'est pas conforme.

Usage : python3 tools/qa_queue.py
Code retour 0 = tous conformes (ou aucun 'done'), 1 = au moins un non conforme.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qa_article_aivf import check  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "queue-aivf.json"


def main() -> int:
    if not QUEUE.exists():
        print("queue-aivf.json introuvable — rien a valider.")
        return 0
    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    done = [a for a in data.get("articles", []) if a.get("status") == "done"]

    print(f"QA file LEXVOX-AIVF — {len(done)} article(s) publie(s) a valider")
    if not done:
        print("Aucun article 'done' : OK.")
        return 0

    total_ko = 0
    for a in done:
        path = ROOT / "actualites" / f"{a['slug']}.html"
        if not path.exists():
            print(f"  ERREUR        id {a['id']} : {path.relative_to(ROOT)} introuvable (statut done mais fichier absent)")
            total_ko += 1
            continue
        problems = check(path, pilier=a.get("type") == "pilier")
        if problems:
            total_ko += 1
            print(f"  NON CONFORME  id {a['id']} — {path.relative_to(ROOT)}")
            for p in problems:
                print(f"      - {p}")
        else:
            print(f"  OK            id {a['id']} — {path.relative_to(ROOT)}")

    print(f"\n{total_ko} article(s) non conforme(s) sur {len(done)}.")
    return 1 if total_ko else 0


if __name__ == "__main__":
    sys.exit(main())
