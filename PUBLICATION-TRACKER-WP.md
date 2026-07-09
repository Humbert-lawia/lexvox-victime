# PUBLICATION-TRACKER-WP.md — suivi PIPELINE LEXVOX-WP

Suivi des publications de `queue-wp.json` sur les sites WordPress
`medical.lexvox-avocat.fr` et `victime-accident.lexvox-avocat.fr`.
Ce dépôt est l'atelier (rédaction + QA + archive Git) ; la publication réelle
se fait via `tools/wp_publish.py` (POST REST WordPress), pas par déploiement
Git. Ne jamais toucher à Sanity ni à `lexvox-victime.com` depuis ce pipeline.

## Articles publiés

| Date | Site | Slug | NW score | URL |
|---|---|---|---|---|
| 2026-07-07 | accident | faute-victime-accident-reduction-indemnisation | 85 | https://victime-accident.lexvox-avocat.fr/2026/07/07/faute-victime-accident-reduction-indemnisation/ |
| 2026-07-07 | accident | conducteur-fautif-victime-droits-indemnisation | 86 | https://victime-accident.lexvox-avocat.fr/2026/07/07/conducteur-fautif-victime-droits-indemnisation/ |
| 2026-07-07 | medical | perte-de-chance-erreur-medicale-indemnisation | 88 (pilier) | https://medical.lexvox-avocat.fr/2026/07/07/perte-de-chance-erreur-medicale-indemnisation/ |
| 2026-07-09 | accident | recours-contre-assureur-guide-complet | 86 (pilier) | https://victime-accident.lexvox-avocat.fr/2026/07/09/recours-contre-assureur-guide-complet/ |
| 2026-07-09 | accident | accidents-de-la-vie-recours-indemnisation | 92 | https://victime-accident.lexvox-avocat.fr/2026/07/09/accidents-de-la-vie-recours-indemnisation/ |
| 2026-07-09 | accident | procedure-amiable-indemnisation-guide-erreurs | 86 (pilier) | https://victime-accident.lexvox-avocat.fr/2026/07/09/procedure-amiable-indemnisation-guide-erreurs/ |

Les scores NeuronWriter ci-dessus sont mesurés sur la **page reconstituée**
(title + meta description + h1 injectés autour du corps atelier, cf.
`tools/nw_eval_wp.py`) : le fichier atelier `wp-atelier/<site>/<slug>.html`
ne contient lui-même ni `<title>`, ni `<meta>`, ni `<h1>` (WordPress les
génère depuis les champs `title`/`meta` du post), donc une évaluation directe
du fragment brut avec `tools/neuronwriter.py evaluate` sous-note
artificiellement l'article — toujours utiliser `nw_eval_wp.py` pour les
articles WP.

## Métas Yoast à poser manuellement

Sur les deux sites, `_yoast_wpseo_title` et `_yoast_wpseo_metadesc` ne sont
**pas persistées via l'API REST** (confirmé par test à l'ÉTAPE 0 : POST/PUT
accepté en HTTP 200/201 mais champ `meta` non relu ensuite). Tant que le
snippet `register_post_meta` (voir `PROMPT-PIPELINE-WP.md`, section
prérequis) n'est pas ajouté par le webmaster sur les deux sites, poser
manuellement dans Yoast (à faire par Me Humbert ou le webmaster) :

| Post | Yoast SEO title | Yoast meta description |
|---|---|---|
| accident #7811 — faute-victime-accident-reduction-indemnisation | Faute de la victime : quand réduit-elle l'indemnisation ? | Faute de la victime d'un accident : quand réduit-elle l'indemnisation du dommage corporel ? Loi Badinter, jurisprudence et recours pratiques. |
| accident #7813 — conducteur-fautif-victime-droits-indemnisation | Conducteur fautif : quels droits à indemnisation ? | Conducteur fautif après un accident : quelle indemnisation reste possible ? Loi Badinter, garantie conducteur, jurisprudence. |
| medical #5210 — perte-de-chance-erreur-medicale-indemnisation | Perte de chance en responsabilité médicale : indemnisation | Perte de chance en erreur médicale : évaluation, barème et indemnisation de la chance perdue par la victime. Jurisprudence et rôle de l'ONIAM. |
| accident #7815 — recours-contre-assureur-guide-complet | Recours contre l'assureur : litige, médiation, indemnisation | Recours contre son assureur après un accident : réclamation, médiateur de l'assurance, action en justice, délais et documents. Guide d'un avocat à Nîmes. |
| accident #7817 — accidents-de-la-vie-recours-indemnisation | Accident de la vie courante : indemnisation et recours | Accident de la vie courante : qui indemnise la victime ? Garantie accidents de la vie (GAV), tiers responsable, expertise et recours. Avocat à Aix. |
| accident #7819 — procedure-amiable-indemnisation-guide-erreurs | Procédure amiable d'indemnisation : étapes et erreurs | Procédure amiable d'indemnisation après un accident : étapes, expertise, offre de l'assureur, délais, erreurs et voie judiciaire. Avocat à Marseille. |

En attendant, le `title` WordPress (H1 affiché) et l'`excerpt` du post portent
déjà ce contenu optimisé — seul le rendu du snippet Google (title/desc dans
les SERP) reste à corriger une fois Yoast inscriptible.

## Écarts documentés (mode dégradé)

- **Item 2 (conducteur-fautif-victime-droits-indemnisation, ville Marseille)** :
  aucune catégorie WordPress « Marseille » n'existe sur le site accident
  (`_meta.sites.accident.categories_existantes` ne liste que Aix/Arles/Ales ;
  vérifié aussi en direct via `/wp-json/wp/v2/categories?search=marseille` →
  vide). Conformément au garde-fou absolu « aucune création de catégorie »,
  l'article a été publié avec la seule catégorie `accident de la route`
  (id 286), sans catégorie ville. L'ancrage local reste assuré par le corps
  du texte (exemples chiffrés, TJ/CA compétents, cabinet) et par l'image
  hero géolocalisée EXIF GPS Marseille. Si Me Humbert souhaite une catégorie
  Marseille sur ce site, elle doit être créée manuellement dans WordPress
  (hors périmètre de ce pipeline automatisé).

## Hypothèses de volume par silo

- **Silo WA (accident, victime-accident.lexvox-avocat.fr)** : ~100 items
  prévus dans `queue-wp.json` (silo majoritaire, ~2 articles/jour).
- **Silo WM (medical, medical.lexvox-avocat.fr)** : ~50 items prévus
  (~1 article/jour), avec des piliers (2500+ mots) sur les sujets de gap
  concurrentiel les plus disputés (perte de chance, ONIAM, CCI...).
- Cadence cible : 3 articles/jour (2 accident + 1 médical), jusqu'à
  épuisement des 150 items (~50 jours).

## Notes de session

- **2026-07-07** : ÉTAPE 0 validée (auth WP ×2 HTTP 200, NeuronWriter API OK
  — projet `avocat-lexvox.com` id `972165f229676370` réutilisé, Openlegi MCP
  OK, test Yoast REST négatif — voir section dédiée ci-dessus).
  `tools/wp_publish.py` et `tools/qa_article_wp.py` créés et testés en
  `--dry-run`. `tools/nw_eval_wp.py` ajouté en complément pour évaluer les
  articles WP avec un score NeuronWriter représentatif (page reconstituée
  title/meta/h1 — voir explication ci-dessus). 3 premiers items produits,
  validés et publiés de bout en bout. Routine quotidienne à installer.
