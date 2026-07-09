# lexvox-victime.com — mémoire projet

Dépôt **atelier éditorial** du cabinet LEXVOX AVOCATS (Me Patrice Humbert,
dommage corporel et responsabilité médicale, PACA).

## ⚠️ ARCHITECTURE RÉELLE (incident 2026-07-06 — à lire avant TOUT travail)

**Ce dépôt statique n'est PLUS le site en production.** Le site
https://lexvox-victime.com est un frontend **Next.js branché sur Sanity**
(projet `jef1bcbo`, dataset `production`), servi par le projet Cloudflare
Pages `lexvox-victime` (même architecture que lexvox-divorce.com). Le
2026-07-06, un push sur `main` a déclenché `.github/workflows/deploy.yml`
qui a écrasé ce site avec le vieux template statique ; il a été restauré
par rollback Cloudflare (déploiement `de014c96`).

Conséquences IMMUABLES, sauf demande expresse de Me Humbert :
1. **`deploy.yml` est neutralisé** (`workflow_dispatch` uniquement).
   **Ne JAMAIS le repasser sur `on: push`** et ne jamais lancer de
   déploiement Cloudflare de ce dépôt : cela écraserait le site Sanity.
2. **Publier un article = créer un document `article` dans Sanity**
   (`python3 tools/sanity_publish.py`, jeton env `SANITY_API_TOKEN`),
   PAS déployer du HTML. Le frontend affiche l'article dès que
   `publishedAt <= now` (publication progressive native : ~2/jour à
   09:00Z et 15:00Z, file déjà programmée jusqu'à mi-août 2026).
3. Ce dépôt reste l'**atelier** : rédaction des articles au gabarit HTML
   (`actualites/<slug>.html`), QA (`preflight`, `qa_article_aivf`,
   NeuronWriter, Openlegi), archivage Git, puis conversion/publication
   Sanity. `sitemap.xml`, `actualites.html`, `llms.txt` du dépôt ne sont
   **plus servis** : leur maillage est géré par le frontend Sanity.
4. Ne jamais modifier le template/design du site : toute évolution passe
   par le projet Next.js/Sanity, sur demande expresse uniquement.

## Sanity — repères techniques

- Projet `jef1bcbo`, dataset `production` (lecture publique, écriture par
  jeton `SANITY_API_TOKEN` — jamais committé, cf. règle secrets).
- Types : `article` (body Portable Text : block normal/h2/h3/h4 + listes +
  `srcsetImage` ; PAS de table ni de SVG inline — tableaux convertis en
  listes, infographies uploadées en asset image), `faq` (champ dédié),
  `heroImage`, `seo{metaTitle,metaDescription,canonicalUrl}`, `author`
  (ref `author-humbert-victime`), `category` (refs `cat-accident-route`,
  `cat-accident-travail`, `cat-erreur-medicale`, `cat-indemnisation`,
  `cat-procedure`), `publishedAt`, `editorialStatus`.
- Slug SANS préfixe `actualites-` → URL `lexvox-victime.com/actualites/<slug>`.
- ~545 articles existants : vérifier l'absence de doublon/cannibalisation
  avant de créer un slug (requête GROQ sur `slug.current`).

## Commandes

- Prévisualiser l'atelier localement : `npm start` (port 8091).
- Valider un article : `python3 tools/preflight.py` +
  `python3 tools/qa_article_aivf.py actualites/<slug>.html [--pilier]`.
- Convertir/publier vers Sanity : `python3 tools/sanity_publish.py
  actualites/<slug>.html --dry-run` puis `--publish-at <ISO|now>`.
- Optimiser un score NeuronWriter : **toujours** via le skill `/nw-optimisation`
  (`tools/nw_lab.py terms/audit/evaluate`) — voir la règle NeuronWriter ci-dessous.

## NeuronWriter — méthode unique (validée 2026-07-07, 62 → 85)

**Tout flux qui score un contenu avec NeuronWriter** (articles atelier
`/article-aivf`, pipeline WordPress `PROMPT-PIPELINE-WP.md`, refontes,
routines LEXVOX SEO Bot / LAWIA Pipeline, productions futures) applique le
skill **`/nw-optimisation`** (`.claude/skills/nw-optimisation/SKILL.md`) :
termes AVANT rédaction (`nw_lab.py terms`), rédaction en une passe sous
contrat de termes, audit LOCAL (`nw_lab.py audit`, 0 appel API), puis
**2 appels `evaluate` maximum** — jamais de boucle aveugle
« rédiger-scorer-deviner » (rendement historique : 6-15 loops pour 62-84).
Lois mesurées du scoreur : pure couverture de termes, aucune pénalité de
sur-usage, chrome ignoré, longueur neutre, H2 comptés en ratio (un H2 pauvre
en termes fait baisser le score). Objectifs par famille de mot-clé :
« indemnisation/montant/barème » ≥ 90 ; « procédure/définition » 85 (plafond
démontré). Aucun score inventé : le marqueur `<!-- NEURONWRITER SCORE: … -->`
porte toujours le dernier score API réel, journalisé dans
`nw-lab/runs-<query>.jsonl`.

**Seuil de publication (politique Me Humbert, 2026-07-08).** Cible = le score le
plus haut possible (viser 95). On pousse via la méthode ci-dessus : audit local
exhaustif (gratuit) + jusqu'à **6 cycles `evaluate` maximum** vers le plus haut
score. Seuil de publication **≥ 85** ; en dessous, **dérogation éditoriale
acceptée si score > 80** (jamais ≤ 80), à condition d'être **documentée dans le
marqueur** (`… — derogation … : plafond de famille, score réel`). C'est la seule
exception au seuil, et elle est tracée : `qa_article_aivf.py` / `qa_article_wp.py`
la vérifient (mot « derogation » + score > 80). Rappel des lois mesurées :
au-delà du plateau de la famille, le gain marginal des cycles est nul — les
6 cycles sont un plafond de sécurité, pas une obligation de brûler 6 appels API.

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
- Publier un article = (1) valider le HTML atelier (QA + NeuronWriter ≥ 85 +
  Openlegi), (2) le pousser sur `main` (archive — ne déclenche plus aucun
  déploiement), (3) le publier dans Sanity via `tools/sanity_publish.py`,
  (4) mettre à jour `queue-aivf.json` et `PUBLICATION-TRACKER.md`.
  (`sitemap.xml`/`actualites.html`/`llms.txt` du dépôt : maillage legacy,
  plus servi en production — entretien facultatif.)

Utiliser le skill projet `/article-aivf` pour dérouler la checklist complète
(`/nouvel-article` est le legacy pré-Sanity), et `/preflight` avant de pousser.

## Pipeline WordPress (sites satellites)

Depuis 2026-07-07, un second pipeline éditorial vise les deux WordPress du
cabinet : `medical.lexvox-avocat.fr` et `victime-accident.lexvox-avocat.fr`
(publication via REST API WP + Application Passwords, secrets env
`WP_MEDICAL_*`/`WP_ACCIDENT_*` — jamais committés). Fichiers :
`PLAN-EDITORIAL-WP-2026-07.md` (gap concurrentiel avocatjullien.fr /
benezra-victimesdelaroute.fr + opportunités Qwairy), `queue-wp.json` (file de
82 articles, champ `site`), `PROMPT-PIPELINE-WP.md` (prompt de production
autonome, cadence 3/jour). Même standard que LEXVOX-AIVF (NeuronWriter ≥ 85,
jurisprudence Openlegi vérifiée, 2 tableaux, SVG inline) + SEO local 7 villes
PACA avec image mise en avant géolocalisée (EXIF GPS). Ce pipeline ne touche
NI Sanity NI lexvox-victime.com — anti-cannibalisation triple obligatoire
(2 WP + Sanity) avant chaque slug.

## Suivi

`SUIVI-ACTIONS-CORRECTIVES.md` trace les actions issues des audits SEO — le
mettre à jour quand une action listée est traitée.

## Images à remplacer

Image `img/articles/accident-de-moto-indemnisation-nimes.jpg` = placeholder
réutilisé (visuel moto générique) — à remplacer par un visuel spécifique au
sujet dès que possible.

Image `img/articles/indemnisation-erreur-chirurgicale.jpg` (id 29) = copie de
`faute-chirurgicale-indemnisation-aix-en-provence.jpg` (pas de visuel dédié
au moment de la rédaction) — à remplacer par un visuel spécifique dès que
possible.

Image `img/articles/obtenir-dossier-medical.jpg` (id 30) = copie de
`erreur-medicale-que-faire.jpg` (pas de visuel dédié au moment de la
rédaction) — à remplacer par un visuel spécifique dès que possible.

Image `img/articles/procedure-cci-crci.jpg` (id 31, pilier) = copie de
`bareme-cci-crci-accident-medical.jpg` (thématiquement proche mais issue
d'un autre article) — à remplacer par un visuel dédié dès que possible.

Image `img/articles/indemnisation-fracture-cheville-poignet-vertebre.jpg`
(id 32) = copie de `indemnisation-prejudice-corporel-grave.jpg` (aucun
visuel dédié disponible) — à remplacer dès que possible.

Image `img/articles/indemnisation-perte-oeil.jpg` (id 33) = copie de
`indemnisation-prejudice-corporel-grave.jpg` (aucun visuel dédié
disponible) — à remplacer dès que possible.

Image `img/articles/indemnisation-amputation.jpg` (id 34) = copie de
`indemnisation-prejudice-corporel-grave.jpg` (aucun visuel dédié
disponible) — à remplacer dès que possible.

Image `img/articles/indemnisation-algodystrophie-sdrc.jpg` (id 35) = copie de
`indemnisation-prejudice-corporel-grave.jpg` (aucun visuel dédié
disponible) — à remplacer dès que possible.

Image `img/articles/indemnisation-coup-du-lapin.jpg` (id 36) = copie de
`indemnisation-prejudice-corporel-grave.jpg` (aucun visuel dédié
disponible) — à remplacer dès que possible.

Image `img/articles/indemnisation-plexus-brachial.jpg` (id 37) = copie de
`indemnisation-prejudice-corporel-grave.jpg` (aucun visuel dédié
disponible) — à remplacer dès que possible.

Image `img/articles/indemnisation-tetraplegie.jpg` (id 39) = copie de
`indemnisation-prejudice-corporel-grave.jpg` (aucun visuel dédié
disponible) — à remplacer dès que possible.

Image `img/articles/indemnisation-hemiplegie.jpg` (id 40) = copie de
`indemnisation-tetraplegie.jpg` (aucun visuel dédié disponible) — à
remplacer dès que possible. Article par ailleurs bloqué (NW 77, sous le
seuil de 80) — voir marqueur NEURONWRITER SCORE dans le fichier.

Image `img/articles/indemnisation-coma-etat-vegetatif.jpg` (id 41) =
copie de `indemnisation-tetraplegie.jpg` (aucun visuel dédié disponible)
— à remplacer dès que possible.

Image `img/articles/garantie-accidents-de-la-vie-gav.jpg` (id 42, pilier)
= copie de `indemnisation-prejudice-corporel-grave.jpg` (aucun visuel
dédié disponible) — à remplacer par un visuel dédié dès que possible.

Image `img/articles/indemnisation-accident-domestique.jpg` (id 43) =
copie de `indemnisation-prejudice-corporel-grave.jpg` (aucun visuel
dédié disponible) — à remplacer dès que possible.

Image `img/articles/indemnisation-accident-ski.jpg` (id 44) = copie de
`indemnisation-prejudice-corporel-grave.jpg` (aucun visuel dédié
disponible) — à remplacer dès que possible.

Image `img/articles/fgti-fonds-garantie-victimes.jpg` (id 47) = copie de
`indemnisation-prejudice-corporel-grave.jpg` (aucun visuel dédié
disponible) — à remplacer par un visuel dédié dès que possible.

Image `img/articles/porter-plainte-agression.jpg` (id 48) = copie de
`indemnisation-prejudice-corporel-grave.jpg` (aucun visuel dédié
disponible) — à remplacer par un visuel dédié dès que possible.

Image `img/articles/indemnisation-coups-et-blessures.jpg` (id 49) =
copie de `indemnisation-prejudice-corporel-grave.jpg` (aucun visuel
dédié disponible) — à remplacer par un visuel dédié dès que possible.

Image `img/articles/indemnisation-chute-rue-escalier.jpg` (id 45) =
copie de `indemnisation-prejudice-corporel-grave.jpg` (aucun visuel
dédié disponible) — à remplacer dès que possible.

Image `img/articles/indemnisation-civi.jpg` (id 46, pilier) = copie de
`indemnisation-prejudice-corporel-grave.jpg` (aucun visuel dédié
disponible) — à remplacer par un visuel dédié dès que possible.
