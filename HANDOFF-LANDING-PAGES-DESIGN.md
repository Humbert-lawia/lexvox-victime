# Passation — Correction du design des landing pages lexvox-victime.com

**Date de la session** : 2026-09-10/11
**Dépôt de travail** : `Humbert-lawia/lexvox-victime` (branche `claude/brave-fermi-3wr28w`, PR [#27](https://github.com/Humbert-lawia/lexvox-victime/pull/27), **draft**)
**Statut** : session arrêtée à la demande de Me Humbert — le travail effectué est insuffisant, voir « Ce qui a foiré » ci-dessous.

---

## 1. La demande initiale

Me Humbert a signalé que 5 pages ne respectaient pas le bon design, par comparaison à 4 pages de référence, toutes sur `lexvox-victime.com` :

**Pages à corriger :**
- https://lexvox-victime.com/expertise-medicale
- https://lexvox-victime.com/indemnisation-victime
- https://lexvox-victime.com/indemnisation-prejudice-corporel
- https://lexvox-victime.com/procedure-indemnisation
- https://lexvox-victime.com/nomenclature-dintilhac

**Pages de référence (bon design) :**
- https://lexvox-victime.com/accident-de-la-route
- https://lexvox-victime.com/accident-du-travail
- https://lexvox-victime.com/erreur-medicale
- https://lexvox-victime.com/responsabilite-medicale

## 2. Ce que j'ai fait (et pourquoi c'est probablement inutile)

J'ai travaillé **uniquement à l'intérieur du dépôt statique `lexvox-victime`** (fichiers `.html` à la racine + `css/style.css`), en comparant les 5 pages signalées aux 4 pages de référence **telles qu'elles existent dans ce dépôt**. J'ai trouvé et corrigé de vrais défauts internes à ce dépôt :

- `indemnisation-victime.html` utilisait un jeu de classes CSS (`.section--light`, `.cards-grid`, `.avantages-grid`, `.steps-list`…) **absent à 100 % de `css/style.css`** — page quasiment non stylée. Reconstruite sur le gabarit standard du dépôt (hero `overline`/`ink`, `.steps-grid`, `.data-table`, `.faq-section`, etc.), contenu juridique conservé intégralement.
- `expertise-medicale.html` : hero sans sur-titre ni trait décoratif, fil d'Ariane à 3 niveaux au lieu de 2, accents français manquants dans une grande partie du texte, section bio utilisant un composant (`.author-card`) réservé à `cabinet.html`/`index.html`.
- `indemnisation-prejudice-corporel.html` et `nomenclature-dintilhac.html` : fil d'Ariane bricolé en style inline avec des variables CSS inexistantes, tableaux mal enveloppés.
- `procedure-indemnisation.html` et `nomenclature-dintilhac.html` : tout le corps de page (et pour `nomenclature-dintilhac.html`, les blocs JSON-LD eux-mêmes) encodé en entités HTML (`&eacute;`, `&agrave;`…) au lieu de caractères UTF-8 natifs.

Tout ça a été fait avec des agents Opus en parallèle, validé par `python3 tools/preflight.py` (0 erreur), et poussé sur la branche `claude/brave-fermi-3wr28w` → PR [#27](https://github.com/Humbert-lawia/lexvox-victime/pull/27) (draft, CI verte, aucun conflit).

**Le problème** : quand Me Humbert m'a envoyé des captures d'écran du site réellement en ligne (`https://lexvox-victime.com/erreur-medicale`), le design affiché **n'a strictement rien à voir** avec ce que ce dépôt peut produire. Voir section 4. Autrement dit : j'ai bien nettoyé des incohérences internes au dépôt `lexvox-victime`, mais ce dépôt **n'est de toute façon pas le code source du site en production** — donc corriger son HTML/CSS ne change rien à ce qui est réellement affiché aux visiteurs.

## 3. La cause racine : ce dépôt n'est plus le site en production

Le `CLAUDE.md` de ce dépôt (déjà présent avant cette session, donc écrit par quelqu'un/une session antérieure après un incident du **2026-07-06**) est formel :

> **Ce dépôt statique n'est PLUS le site en production.** Le site https://lexvox-victime.com est un frontend **Next.js branché sur Sanity** (projet `jef1bcbo`, dataset `production`), servi par le projet Cloudflare Pages `lexvox-victime`. Le 2026-07-06, un push sur `main` a déclenché `.github/workflows/deploy.yml` qui a écrasé ce site avec le vieux template statique ; il a été restauré par rollback Cloudflare.

Conséquences :
- `.github/workflows/deploy.yml` est neutralisé (`workflow_dispatch` uniquement) — pousser sur `main` ne déploie plus rien.
- Ce dépôt ne sert plus que d'**atelier de rédaction d'articles de blog** (`actualites/*.html`), publiés ensuite dans Sanity via `tools/sanity_publish.py`.
- Rien n'indique dans ce `CLAUDE.md` où vivent les **pages piliers** (`accident-de-la-route`, `expertise-medicale`, etc.) dans la nouvelle architecture Next.js/Sanity — probablement dans un autre dépôt de code (le frontend Next.js lui-même), pas dans Sanity (Sanity ne gère que le contenu éditorial `article`).

Important : je n'ai **aucune mémoire d'une session à l'autre**. Je ne sais pas qui a construit le site actuellement en ligne (autre session Claude Code, développeur, agence). Cette information n'est nulle part dans ce dépôt.

## 4. Ce à quoi ressemble le VRAI design en production (d'après les captures envoyées par Me Humbert)

Captures reçues de `https://lexvox-victime.com/erreur-medicale` (via le navigateur de Me Humbert, pas récupérables par moi — aucun accès réseau sortant dans cet environnement, `curl`/`web_read.py` renvoient tous les deux une erreur 403 du proxy). Description précise pour la prochaine session :

- **Typographie** : titres en police à empattements élégante (serif, style éditorial haut de gamme — genre Tiempos/Freight/Georgia raffinée), corps de texte et libellés en sans-serif.
- **Libellés de section** (« sur-titre ») en petites capitales espacées, bleu, ex. « VOTRE AVOCAT », « MÉTHODE LEXVOX », « SITUATIONS ACCOMPAGNÉES », « CHOISIR VOTRE SITUATION ».
- **Palette** : alternance de sections bleu marine très foncé (quasi noir, texte crème/blanc dessus) et de sections crème/blanc cassé (texte bleu marine/gris). Bleu vif utilisé pour les accents (liens « VOIR LA PAGE → », numéros).
- **Photographie** : portraits professionnels réels (Me Humbert en robe d'avocat, bras croisés, fond bureau boisé) et photos de situations (consultation médicale, réunion d'expertise, famille au chevet d'un patient, bloc opératoire, nouveau-né) — composition en grille avec légendes en bas à gauche des images.
- **Bloc « Méthode »** : liste numérotée avec numéros en chiffres italiques bleus (01, 02, 03…), titre + description sous chaque numéro, séparateurs fins horizontaux, disposition en deux colonnes (titre de section à gauche, liste à droite).
- **Bloc « Situations accompagnées »** : fond bleu marine plein cadre, grille 3×2 de cartes (numéro italique bleu clair, titre, description courte), séparateurs verticaux/horizontaux fins.
- **Bloc « Choisir votre situation »** : fond crème, grille 2×2 de cartes photo + texte (image à gauche, libellé « DÉCOUVRIR » en petites capitales bleues, titre serif, description, lien « VOIR LA PAGE → »).
- **Aucune trace** des composants du dépôt `lexvox-victime` : pas de `.dots-pattern`, pas de police manuscrite Caveat/`.handwritten`, pas de couleur or/`.badge-or`, pas de `.quick-answer` à bordure bleue, pas d'icônes SVG décoratives, pas de `.author-card`.

**Conclusion technique** : ce n'est pas un problème de classes CSS mal posées à corriger à la marge — c'est un système de design (police, palette, grille, composants) entièrement différent qui n'existe nulle part dans `css/style.css` de ce dépôt. Impossible à produire en éditant ce dépôt.

Je n'ai pas pu sauvegarder les fichiers image exacts envoyés par Me Humbert (reçus comme pièces jointes de conversation, pas comme fichiers accessibles sur disque dans cet environnement) — la description ci-dessus est la meilleure restitution possible. **Recommandation pour la prochaine session : redemander les captures d'écran, ou mieux, un accès direct au dépôt du frontend réel pour les récupérer en `git clone`.**

## 5. Dépôts GitHub découverts sur le compte `Humbert-lawia` (pertinents)

Obtenus via l'outil `list_repos` en session, à re-vérifier (une recherche plus large `list_repos` sans filtre donnerait la liste complète) :

| Dépôt | Visibilité | Dernier push | Probable rôle |
|---|---|---|---|
| `Humbert-lawia/lexvox-victime` | public | 2026-09-11 | Atelier statique legacy (CE dépôt) — articles de blog uniquement, PLUS le front en prod |
| `Humbert-lawia/lexvox-sanity-migration` | privé | **2026-09-11 (aujourd'hui)** | **Candidat le plus probable pour le vrai frontend Next.js/Sanity** — non vérifié, jamais ouvert cette session |
| `Humbert-lawia/lexvox-divorce` | privé | 2026-09-11 | Même architecture/même piège que lexvox-victime d'après le CLAUDE.md de lexvox-victime (« même architecture que lexvox-divorce.com ») — atelier statique legacy également, cloné cette session dans `/home/user/lexvox-divorce`, contient les mêmes pages piliers en gabarit ancien |
| `Humbert-lawia/lexvox-permis` | privé | 2026-09-11 | Rôle inconnu, non exploré |
| `Humbert-lawia/lexvox-kadence-lp` | privé | 2026-05-08 | Rôle inconnu (nom suggère un thème WordPress Kadence / landing page), non exploré |
| `Humbert-lawia/questionnaire-lexvox` | privé | 2026-04-29 | Rôle inconnu, non exploré |

**Action recommandée en priorité pour la prochaine session** : `add_repo` sur `Humbert-lawia/lexvox-sanity-migration`, cloner, chercher son `README`/`CLAUDE.md`, vérifier s'il contient bien les composants Next.js correspondant aux captures (recherche de mots-clés : "erreur-medicale", "MÉTHODE LEXVOX", couleurs bleu marine, police serif). Si ce n'est pas le bon dépôt, redemander à Me Humbert où vit le code du frontend (il est possible que ce ne soit pas sur GitHub du tout, ou sur un compte/organisation différent).

## 6. État exact du dépôt `lexvox-victime` à l'arrêt de cette session

```
Branche : claude/brave-fermi-3wr28w
Dernier commit : 358b639 "Aligne 5 landing pages piliers sur le design de reference du site"
Arbre de travail : propre (rien en attente)
PR : #27 (draft, ouverte, CI verte "Préflight" au vert, mergeable_state clean, 0 commentaire de revue)
```

Fichiers modifiés par cette session (diff complet consultable via `git show 358b639` ou sur la PR) :
- `expertise-medicale.html`
- `indemnisation-prejudice-corporel.html`
- `indemnisation-victime.html`
- `nomenclature-dintilhac.html`
- `procedure-indemnisation.html`

**Ces modifications restent probablement utiles en soi** (elles corrigent de vraies incohérences internes au dépôt — CSS inexistant, entités HTML, accents manquants) même si elles ne résolvent pas le vrai problème de design signalé. À la prochaine session : décider de garder cette PR telle quelle (nettoyage interne de l'atelier), de la fermer, ou de la retravailler une fois le bon dépôt identifié.

## 7. Ce qu'il faut faire différemment à la prochaine session

1. **Ne pas repartir de ce dépôt `lexvox-victime` pour corriger le design visuel** — il ne peut structurellement pas produire ce qui est en ligne. Il reste valable uniquement pour : rédiger des articles de blog (`actualites/*.html` → Sanity), et pour des demandes explicites de modification de CE gabarit legacy.
2. **Identifier le vrai dépôt du frontend** (candidat : `lexvox-sanity-migration`) avant toute correction de design visuel.
3. **Ne jamais repasser `.github/workflows/deploy.yml` sur `on: push`**, ni lancer de déploiement Cloudflare depuis ce dépôt (`lexvox-victime` et `lexvox-divorce`) — ça écraserait le site Sanity en production (incident du 2026-07-06, cf. section 3).
4. Si le dépôt du frontend est confirmé, relire son propre `CLAUDE.md`/README pour connaître ses conventions (framework, système de design tokens, build, déploiement) avant de toucher au code.
5. Redemander à Me Humbert des captures d'écran fraîches (ou un accès navigateur/réseau si l'environnement de la prochaine session le permet) pour valider visuellement chaque page corrigée avant de proposer une PR.

## 8. Contraintes d'environnement rencontrées (pour info)

- Cet environnement d'exécution sandboxé **n'a aucun accès réseau sortant vers l'Internet public** (proxy renvoie 403/refus de connexion sur `lexvox-victime.com`, y compris via les outils du dépôt `tools/web_read.py`/`tools/exa_search.py` qui passent par des services tiers). Impossible de charger la moindre page du site en production directement.
- Capture d'écran uniquement possible sur le **serveur local** (`npm start`, port 8091, sert les fichiers statiques de CE dépôt) via Chromium préinstallé (`/opt/pw-browsers/chromium`) + Playwright (`NODE_PATH=$(npm root -g) node script.js`, package `playwright` disponible en global uniquement, pas en dépendance locale du projet).
- Aucun moyen technique de récupérer/sauvegarder les images collées par l'utilisateur dans la conversation — seule une description textuelle a pu être produite (section 4).

---
*Document généré à la demande de Me Humbert pour reprise en session locale, avec toutes les informations et difficultés rencontrées durant cette session.*
