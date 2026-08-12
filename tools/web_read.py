#!/usr/bin/env python3
"""Lecture d'une page web PUBLIQUE en Markdown brut (via r.jina.ai).

Complète l'outil WebFetch de Claude Code, qui renvoie un *résumé* produit par
un petit modèle et échoue sur les pages rendues en JavaScript. Ici la page est
rendue puis restituée telle quelle : c'est ce qu'il faut pour auditer un
article concurrent (balisage Hn réel, volume de texte, termes exacts pour un
contrat NeuronWriter) sans passer par une reformulation intermédiaire.

Deux lecteurs gratuits, sans clé : r.jina.ai par défaut, mcp.exa.ai en secours
automatique (aucun des deux n'offre de garantie de service).

⚠️ Secret professionnel — ces lecteurs sont des services TIERS : chaque URL
demandée leur est communiquée, ainsi que le contenu récupéré. N'appeler ce
script que sur du contenu PUBLIC (sites concurrents, jurisprudence publiée,
pages du cabinet). Jamais une URL d'extranet, de webmail, de RPVA/e-Barreau, de
dossier client ni aucune adresse portant un jeton. Les cas les plus évidents
sont refusés par le garde-fou ci-dessous, qui ne dispense pas de vérifier.

Usage :
    python3 tools/web_read.py URL [--max-chars N] [--timeout S] [--reader R]

    --max-chars   troncature de la sortie (défaut 12000, 0 = illimité)
    --timeout     délai réseau en secondes (défaut 60)
    --reader      auto (défaut), jina ou exa

Code retour 0 = page lue, 1 = échec réseau/HTTP, 2 = URL refusée.
"""
import argparse
import ipaddress
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

JINA = "https://r.jina.ai/"
EXA = "https://mcp.exa.ai/mcp"
UA = "curl/8.5.0"

# Hôtes jamais transmis à un tiers : messagerie, extranets, outils métier.
BLOCKED_HOST_PARTS = (
    "e-barreau",
    "rpva",
    "avocat.fr",
    "extranet",
    "webmail",
    "roundcube",
    "owa.",
    "vpn.",
    "intranet",
    "manage.sanity.io",
    "api.sanity.io",
)
BLOCKED_HOST_PREFIXES = ("mail.", "secure.", "portail.", "admin.", "dashboard.")
# Paramètres d'URL qui trahissent une session ou une clé.
BLOCKED_QUERY = re.compile(
    r"(?:^|[?&])(?:[a-z_]*token|api[_-]?key|password|passwd|secret|sig|signature)=",
    re.I,
)


def refuse(reason):
    print(f"URL refusée : {reason}", file=sys.stderr)
    print(
        "Ce script ne lit que du contenu public (cf. docstring, secret professionnel).",
        file=sys.stderr,
    )
    sys.exit(2)


def check_public(url):
    """Refuse ce qui ne doit manifestement pas transiter par un tiers."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https"):
        refuse(f"schéma « {parts.scheme or '?'} » non supporté (http/https seuls)")
    host = (parts.hostname or "").lower()
    if not host:
        refuse("aucun nom d'hôte")
    if parts.username or parts.password:
        refuse("identifiants présents dans l'URL")
    if BLOCKED_QUERY.search(parts.query or ""):
        refuse("jeton, clé ou mot de passe dans les paramètres")
    if host in ("localhost", "::1") or host.endswith((".local", ".internal", ".lan")):
        refuse(f"hôte local ou interne ({host})")
    try:
        if not ipaddress.ip_address(host).is_global:
            refuse(f"adresse IP non publique ({host})")
    except ValueError:
        pass  # nom de domaine : rien à vérifier ici
    if any(part in host for part in BLOCKED_HOST_PARTS):
        refuse(f"hôte sensible ({host})")
    if host.startswith(BLOCKED_HOST_PREFIXES):
        refuse(f"hôte sensible ({host})")


def read_jina(url, timeout, max_chars):
    req = urllib.request.Request(JINA + url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def read_exa(url, timeout, max_chars):
    """Secours : l'outil web_fetch_exa du même endpoint MCP que exa_search.py."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": UA,
    }

    def rpc(method, params, request_id):
        body = json.dumps(
            {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        ).encode()
        req = urllib.request.Request(EXA, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
        for line in raw.splitlines():
            if line.startswith("data: "):
                raw = line[6:]
                break
        return json.loads(raw)

    rpc(
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "lexvox-victime", "version": "1.0"},
        },
        1,
    )
    arguments = {"urls": [url]}
    if max_chars > 0:
        arguments["maxCharacters"] = max_chars
    result = rpc("tools/call", {"name": "web_fetch_exa", "arguments": arguments}, 2)
    if "error" in result:
        raise RuntimeError(result["error"])
    blocks = result.get("result", {}).get("content", [])
    texts = [block.get("text", "") for block in blocks if block.get("text")]
    if not texts:
        raise RuntimeError("réponse vide")
    return "\n".join(texts)


READERS = {"jina": read_jina, "exa": read_exa}


def read(url, timeout, max_chars, choice):
    """Lit la page ; en mode « auto », bascule sur Exa si Jina échoue."""
    order = list(READERS) if choice == "auto" else [choice]
    last = None
    for name in order:
        try:
            content = READERS[name](url, timeout, max_chars)
        except Exception as exc:
            last = exc
            print(f"Lecteur {name} en échec ({type(exc).__name__}) : {exc}", file=sys.stderr)
            continue
        if name != order[0]:
            print(f"[lu via le lecteur de secours : {name}]", file=sys.stderr)
        return content
    raise last


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("url", help="URL publique à lire")
    parser.add_argument("--max-chars", type=int, default=12000, help="0 = illimité")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--reader", choices=["auto", "jina", "exa"], default="auto")
    args = parser.parse_args()

    url = args.url
    if "://" not in url:
        url = "https://" + url
    check_public(url)

    try:
        content = read(url, args.timeout, args.max_chars, args.reader)
    except urllib.error.HTTPError as exc:
        print(f"ERREUR HTTP {exc.code} sur {url}", file=sys.stderr)
        return 1
    except Exception as exc:  # réseau, TLS, délai dépassé
        print(f"ERREUR lecture ({type(exc).__name__}) : {exc}", file=sys.stderr)
        return 1

    if args.max_chars > 0 and len(content) > args.max_chars:
        print(content[: args.max_chars])
        print(
            f"\n[...] tronqué à {args.max_chars} caractères sur {len(content)} "
            "— relancer avec --max-chars 0 pour tout obtenir.",
            file=sys.stderr,
        )
    else:
        print(content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
