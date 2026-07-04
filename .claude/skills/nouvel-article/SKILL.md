---
name: nouvel-article
description: Publier un article actualités complet sur lexvox-victime.com — gabarit SEO, JSON-LD, maillage, sitemap, actualites.html, llms.txt, image, préflight. Utiliser dès que l'utilisateur demande de rédiger ou publier un article (pilier ou déclinaison locale).
---

# Publier un article actualités

Dérouler ces étapes dans l'ordre. Ne jamais s'arrêter après la seule création
du fichier HTML : un article non maillé est orphelin et invisible.

## 1. Préparer

- Slug : `actualites/<sujet>-<ville>.html` (minuscules, tirets, sans accents).
  Vérifier qu'il n'existe pas déjà (`ls actualites/ | grep <mot-clé>`).
- Prendre un article récent du même type comme gabarit (ex.
  `actualites/accident-infirmiere-liberale-indemnisation.html` pour un pilier,
  une déclinaison `-marseille` pour un article local).
- Sources juridiques : citer les textes réels (Légifrance, service-public.fr —
  attention : `service-public.fr`, PAS `.gouv.fr`). Utiliser les MCP Openlegi/
  Themia si disponibles pour vérifier articles de loi et jurisprudence.

## 2. Rédiger dans le gabarit

Structure attendue : hero avec image, quick-answer, 4–5 sections H2, tableau
ou liste des préjudices (nomenclature Dintilhac), FAQ 6 questions, CTA,
articles liés (3 cartes).

Contraintes bloquantes :
- `<title>` ≤ 60 caractères ; meta description 120–155 caractères, non vide.
- Un seul `<h1>` ≤ 100 caractères.
- `canonical` et `og:url` : `https://lexvox-victime.com/actualites/<slug>` —
  domaine `.com`, **sans** `.html`.
- 4 blocs JSON-LD : `LegalService`, `Article` (avec `image`, `datePublished`,
  `publisher.logo`), `FAQPage` (mêmes questions que la FAQ visible),
  `BreadcrumbList`. Valider chaque bloc en JSON pur — aucune balise HTML dedans.
- Identité du cabinet : reprendre les coordonnées de `mentions-legales.html`,
  ne rien inventer.

## 3. Image

- `img/articles/<slug>.jpg` doit exister. Réutiliser un visuel thématique
  existant si aucune nouvelle image n'est fournie (précédent accepté), et le
  noter dans le commit pour remplacement ultérieur.
- Référencer la même image dans le hero (`../img/articles/…`), `og:image` et
  `twitter:image` (URL absolue).

## 4. Mailler (les 4 fichiers, systématiquement)

1. **`sitemap.xml`** : ajouter `<url>` avec `lastmod` du jour, sans doublon.
2. **`actualites.html`** : ajouter la carte dans la bonne catégorie et
   incrémenter le compteur de la catégorie ; pour un pilier, envisager la
   section « À la une ».
3. **`llms.txt`** : ajouter l'article dans la section des articles récents.
4. **Maillage interne** : 3–5 liens sortants vers les pages piliers
   (`/accident-de-la-route`, `/nomenclature-dintilhac`, `/expertise-medicale`…)
   et liens croisés depuis/vers les déclinaisons locales sœurs.

## 5. Valider et pousser

```bash
python3 tools/preflight.py   # doit finir sur 0 erreur bloquante
git pull --rebase origin main  # main bouge tous les jours (bots)
```

En cas de conflit sur `sitemap.xml`/`actualites.html`/`llms.txt` : union des
deux côtés + déduplication. Ne JAMAIS committer de marqueurs de conflit.
