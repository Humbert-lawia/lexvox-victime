#!/usr/bin/env python3
"""Recherche web sémantique via l'endpoint MCP public d'Exa (sans clé API).

Complète l'outil WebSearch de Claude Code, dont l'index est restreint aux
États-Unis et donc faible sur les requêtes francophones (concurrence PACA,
barèmes, veille dommage corporel). Exa indexe le web par similarité
sémantique et renvoie, pour chaque résultat, l'URL, la date et un extrait du
contenu réel — utile pour un repérage concurrentiel avant rédaction.

Décrire la page recherchée plutôt que d'empiler des mots-clés :
    « guide complet de l'indemnisation d'un accident de moto en 2026 »
donne de meilleurs résultats que « indemnisation moto ».

⚠️ Secret professionnel — mcp.exa.ai est un service TIERS : la requête lui est
communiquée. N'y écrire aucun nom de client, aucune référence de dossier,
aucune donnée de santé identifiante.

Usage :
    python3 tools/exa_search.py "requête" [-n 5] [--json]

    -n / --num     nombre de résultats (défaut 5)
    --json         sortie brute de l'API au lieu du texte formaté

L'endpoint public n'expose que « query » et « numResults » (vérifié par
tools/list le 2026-08-12) : pas de filtre par domaine ni par date. Pour
restreindre à un site, ajouter le domaine dans la requête elle-même.

Code retour 0 = résultats obtenus, 1 = échec réseau/API, 2 = requête refusée.
"""
import argparse
import json
import sys
import urllib.error
import urllib.request

ENDPOINT = "https://mcp.exa.ai/mcp"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "User-Agent": "curl/8.5.0",
}
TIMEOUT = 90


def rpc(method, params, request_id):
    """Appel JSON-RPC ; la réponse peut arriver en SSE (« data: {...} »)."""
    body = json.dumps(
        {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
    ).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        raw = resp.read().decode("utf-8", "replace")
    for line in raw.splitlines():
        if line.startswith("data: "):
            raw = line[6:]
            break
    return json.loads(raw)


def search(query, num):
    rpc(
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "lexvox-victime", "version": "1.0"},
        },
        1,
    )
    arguments = {"query": query, "numResults": num}
    return rpc("tools/call", {"name": "web_search_exa", "arguments": arguments}, 2)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("query", help="requête en langage naturel")
    parser.add_argument("-n", "--num", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="sortie brute")
    args = parser.parse_args()

    query = args.query.strip()
    if not query:
        print("Requête vide.", file=sys.stderr)
        return 2
    if args.num < 1:
        print("--num doit être au moins 1.", file=sys.stderr)
        return 2

    try:
        result = search(query, args.num)
    except urllib.error.HTTPError as exc:
        print(f"ERREUR HTTP {exc.code} sur {ENDPOINT}", file=sys.stderr)
        return 1
    except Exception as exc:  # réseau, TLS, délai dépassé, réponse illisible
        print(f"ERREUR recherche ({type(exc).__name__}) : {exc}", file=sys.stderr)
        return 1

    if "error" in result:
        print(f"ERREUR API Exa : {result['error']}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    blocks = result.get("result", {}).get("content", [])
    texts = [block.get("text", "") for block in blocks if block.get("text")]
    if not texts:
        print(f"Aucun résultat pour : {query}", file=sys.stderr)
        return 1
    print("\n".join(texts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
