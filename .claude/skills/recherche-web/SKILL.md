---
name: recherche-web
description: Rechercher sur le web en français et lire une page publique en Markdown brut (JavaScript exécuté) via tools/exa_search.py et tools/web_read.py. Utiliser pour analyser un article concurrent, relever son balisage Hn, compter ses mots, collecter des termes avant un contrat NeuronWriter, ou faire une veille — de préférence aux outils WebSearch/WebFetch natifs, dont l'index est restreint aux États-Unis et qui ne renvoient qu'un résumé de page.
---

# Recherche et lecture web

Deux scripts, aucune clé API. À préférer aux outils natifs, dont les limites sont
mesurées : `WebSearch` interroge un index restreint aux États-Unis (faible sur le
français) et `WebFetch` renvoie un résumé produit par un modèle intermédiaire, pas
le texte de la page — inexploitable pour un audit SEO — et échoue sur les pages
rendues en JavaScript.

## Chercher

```bash
python3 tools/exa_search.py "requête en langage naturel" -n 5
```

Décrire la page recherchée plutôt qu'empiler des mots-clés : « guide complet de
l'indemnisation d'un accident de moto en 2026 » bat « indemnisation moto ».
Chaque résultat donne titre, URL, date et un extrait du contenu réel.

L'endpoint public n'accepte que `query` et `numResults` : pas de filtre par
domaine ni par date. Pour restreindre à un site, mettre le domaine dans la
requête. `--json` donne la réponse brute.

## Lire une page

```bash
python3 tools/web_read.py https://exemple.fr/article --max-chars 0
```

Rend la page en Markdown brut, JavaScript exécuté. `--max-chars 0` = pas de
troncature (défaut 12000) ; c'est ce qu'il faut pour compter des mots ou relever
un plan de titres fidèlement. Lecteur `r.jina.ai` par défaut, bascule automatique
sur `mcp.exa.ai` en cas d'échec ; `--reader jina|exa` pour forcer.

## Secret professionnel — la règle qui prime

Ces services sont des **tiers** : ils reçoivent chaque URL et chaque requête.

- **Contenu public uniquement** : sites concurrents, jurisprudence publiée, pages
  du cabinet.
- **Jamais** d'URL d'extranet, de webmail, de RPVA/e-Barreau, de console Sanity
  ni de dossier client. Jamais de nom de client ni de donnée de santé
  identifiante dans une requête.

`web_read.py` refuse en amont (code retour 2) les hôtes locaux, IP privées,
identifiants dans l'URL, paramètres de type jeton ou clé, extranets et webmails.
Ce garde-fou couvre l'évident, pas le subtil : vérifier reste nécessaire.

## Ce que ces outils ne font pas

Pas d'accès aux contenus sous paywall (Dalloz, Lexis, Gazette du Palais), aux
pages derrière identification, ni aux sites à anti-bot agressif. Pour ces cas,
Chromium et Playwright sont préinstallés dans l'environnement.

Pour la recherche **juridique**, préférer les serveurs MCP dédiés (Openlegi,
Lexbase) : ces deux scripts visent le web ouvert, pas les bases de jurisprudence.

En cas d'échec d'une commande, coller l'erreur brute et passer à la suivante — ne
jamais inventer une URL ni un contenu de page.
