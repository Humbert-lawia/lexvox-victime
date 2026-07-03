# lexvox-victime.com — mémoire projet

Site vitrine statique du cabinet LEXVOX AVOCATS (Me Patrice Humbert, dommage
corporel et responsabilité médicale, PACA). HTML/CSS/JS pur, sans framework ni
build. Déployé sur **Cloudflare Pages** : **tout push sur `main` part
immédiatement en production** (`.github/workflows/deploy.yml`).

## Commandes

- Prévisualiser localement : `npm start` (sert le site sur le port 8091) —
  **toujours tester ici avant de pousser** un changement de `_headers`,
  `_redirects` ou CSP ; ne pas déboguer en production à coups de commits.
- Valider avant tout push : `python3 tools/preflight.py` (bloquant si
  marqueurs de conflit, sitemap invalide/doublons, JSON-LD corrompu, image
  locale manquante, secret en clair).

## Règles critiques (chacune vient d'un incident réel)

1. **Jamais de marqueurs de conflit committés.** Le sitemap.xml est resté
   invalide en production ~2 mois (avril–juin 2026) à cause de `<<<<<<<`
   committés sur main. Avant tout commit : `git diff --check` + préflight.
2. **`git pull --rebase origin main` avant chaque push.** Trois acteurs
   committent sur main (sessions interactives, LEXVOX SEO Bot, LAWIA
   Pipeline) : les conflits sont fréquents, surtout sur `sitemap.xml`,
   `actualites.html` et `llms.txt`. En cas de conflit sur le sitemap :
   union des URLs des deux côtés + déduplication, jamais de suppression.
3. **Domaine canonique : `https://lexvox-victime.com`** (jamais `.fr`).
   URLs internes et canonicals **sans extension `.html`**.
4. **Identité légale (NAP)** : la source de vérité est `mentions-legales.html`
   (nom complet, siège social à Arles, SIREN seul, TVA FR54…). Ne jamais
   inventer ou recopier une ancienne variante depuis un autre fichier.
5. **Aucun secret en dur** (token API, clé OpenAI/Gemini…) : un token a déjà
   dû être purgé du dashboard. Les clés vivent dans Cloudflare
   (variables d'environnement des Functions) ou les secrets GitHub Actions.
6. **Pas de fichiers `.bak`** ni de brouillons committés (`*.bak` est ignoré).

## Gabarit SEO d'un article (`actualites/*.html`)

Contraintes vérifiées par le préflight — les dérives passées ont demandé des
corrections en masse (103 titles régénérés, 20 meta descriptions, H1 dédupliqués) :

- `<title>` ≤ 60 caractères ; méta description **non vide**, 120–155 caractères.
- **Un seul `<h1>`**, ≤ 100 caractères.
- `canonical` = `og:url` = URL sans `.html` sur le domaine canonique.
- 4 blocs JSON-LD valides : `LegalService`, `Article` (avec champ `image`),
  `FAQPage`, `BreadcrumbList`. Jamais de HTML brut dans le JSON.
- Image hero existante dans `img/articles/<slug>.jpg` + `og:image`/`twitter:image`.
- Publier un article = mettre à jour **4 fichiers** : l'article,
  `sitemap.xml` (lastmod du jour), `actualites.html` (carte + compteur de
  catégorie), `llms.txt` (section articles récents).

Utiliser le skill projet `/nouvel-article` pour dérouler la checklist complète,
et `/preflight` avant de pousser.

## Suivi

`SUIVI-ACTIONS-CORRECTIVES.md` trace les actions issues des audits SEO — le
mettre à jour quand une action listée est traitée.

## Images à remplacer

Image `img/articles/accident-de-moto-indemnisation-nimes.jpg` = placeholder
réutilisé (visuel moto générique) — à remplacer par un visuel spécifique au
sujet dès que possible.
