#!/usr/bin/env python3
"""Soumet toutes les URLs du sitemap à IndexNow (Bing, Yandex, Seznam, Naver).

Lancé automatiquement par .github/workflows/deploy.yml après chaque
déploiement Cloudflare Pages. Google n'utilise pas IndexNow : côté Google,
la découverte passe par la ligne `Sitemap:` de robots.txt et par la
Search Console (le sitemap y est re-téléchargé périodiquement).

La clé IndexNow n'est PAS un secret : le protocole exige qu'elle soit
publiée à la racine du site (fichier <clé>.txt) pour prouver qu'on
contrôle le domaine.
"""
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET

HOST = "lexvox-victime.com"
KEY = "a7c31f0862d94b2fa4c9e5d17b83f6e0"
ENDPOINT = "https://api.indexnow.org/indexnow"
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def main() -> int:
    urls = [loc.text.strip() for loc in ET.parse("sitemap.xml").getroot().findall(".//sm:loc", NS)]
    if not urls:
        print("sitemap.xml : aucune URL — abandon")
        return 1
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": f"https://{HOST}/{KEY}.txt",
        "urlList": urls,
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"IndexNow : HTTP {resp.status} — {len(urls)} URLs soumises")
            return 0
    except urllib.error.HTTPError as e:
        print(f"IndexNow : HTTP {e.code} — {e.read().decode(errors='replace')[:200]}")
        return 0 if e.code in (200, 202) else 1


if __name__ == "__main__":
    sys.exit(main())
