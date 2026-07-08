# PLAN ÉDITORIAL WP — medical.lexvox-avocat.fr & victime-accident.lexvox-avocat.fr

**Date :** 2026-07-07 · **Objet :** adaptation du PIPELINE LEXVOX-AIVF aux deux
sites WordPress du cabinet, pour couvrir **tous les sujets traités par les
concurrents avocatjullien.fr et benezra-victimesdelaroute.fr** non encore
traités par LEXVOX, enrichis des **opportunités GEO Qwairy** (export
2026-07-07). File exécutable : `queue-wp.json`. Prompt de production :
`PROMPT-PIPELINE-WP.md`.

---

## 1. Cartographie — ce que les 5 sites contiennent (mesuré 2026-07-07)

| Site | Volume | Dominante | Trou principal |
|---|---|---|---|
| **avocatjullien.fr** (concurrent) | ~613 URLs | ACCIDENT ≈ 80 % (route, moto, piéton, agression/CIVI, coup du lapin, FGAO, GAV) + ~45 sujets transverses. Signature : **~90 études de cas chiffrées** (« X € alloués à une victime de… ») + 217 landings locales (7 secteurs PACA/Var) | **MÉDICAL quasi nul** (2 pages catégorie, 0 fond) |
| **benezra-victimesdelaroute.fr** (concurrent) | ~406 URLs (276 posts + 31 pages + **99 FAQ**) | Ultra-granulaire : Badinter fin (faute victime, sans contact), assurance (IRCA, garantie conducteur, nullité, enquêteurs), séquelles (TC/Glasgow, amputés/prothèses, état antérieur, PTSD), décès/ricochet, étranger (11 pays), barème capitalisation/Mornet | **Erreur médicale = 0** (revendiqué) |
| **medical.lexvox-avocat.fr** (à alimenter) | 227 posts + 55 pages | Erreur/faute médicale, nosocomiale, accouchement (~20), AAH/MDPH (~40), pathologies, expertise (bases), SEO local 7 villes, « avis/choisir avocat » (récent) | **Barèmes chiffrés, perte de chance, procédure CCI détaillée, postes de préjudice appliqués au médical, jurisprudence citée** |
| **victime-accident.lexvox-avocat.fr** (à alimenter) | 281 posts + 54 pages | Types d'accident, postes Dintilhac (posts 2020, minces), trauma crânien, SEO local, niche infirmière libérale, « avis/choisir avocat » (récent) | **Badinter fin, assurance/garanties, barème de capitalisation, décès/ricochet, étranger, état antérieur/PTSD, études de cas chiffrées** |
| lexvox-victime.com (Sanity — pipeline AIVF existant) | ~545 articles + file de 52 | Piliers nationaux en cours (silos A–J) | — (couvert par queue-aivf.json) |

**Lecture stratégique.** Tes 2 WP sont riches en contenu commercial/local mais
faibles sur le fond informationnel que Jullien et Benezra monopolisent. Le
médical est l'angle mort TOTAL des deux concurrents : chaque article de fond
publié sur medical.lexvox-avocat.fr est un terrain sans défense. Sur
l'accident, on ne bat pas Benezra en volume du jour au lendemain : on le bat
avec le standard AIVF-killer (jurisprudence Openlegi vérifiée + tableaux
chiffrés + NeuronWriter ≥ 85) qu'aucun des deux n'applique.

## 2. Répartition et cadence

- **150 articles** dans `queue-wp.json` : **90 → site ACCIDENT**, **60 → site MÉDICAL**
  (35 P1 / 51 P2 / 47 P3 / 17 P4). Vague 1 (82, le gap net) au standard maximal ;
  vague 2 (68) = longue traîne — cas concrets par blessure, typologie médicale
  par acte (angle mort total des 2 concurrents), circonstances non couvertes.
- L'ordre de la file entrelace ~2 accident + 1 médical par jour.
- **Cadence : 3 articles/jour, tous les jours, à partir d'aujourd'hui → file
  épuisée en ~50 jours** (~2 mois, dans la fenêtre fixée par Me Humbert).
- Sources : gap Jullien (J), gap Benezra (B), transpositions médicales (B/J
  transposé — les concurrents ne couvrent pas le médical, on transpose leurs
  armes transverses), **Qwairy** (15 articles issus des 4 exports du
  2026-06-06/07-07 : prompts à fort brand gap, clusters « procédure amiable »
  10 prompts, « recours assureur » 12 prompts, « assistance juridique » 4
  prompts à 100 %).
- **Tri Qwairy** : les lignes « avis avocat / consultation gratuite / choisir
  avocat + ville » à gap élevé sont DÉJÀ couvertes par les posts publiés début
  juillet 2026 sur les deux sites — le gap vient du délai de prise en compte
  par les moteurs IA, pas d'un contenu manquant. Elles ont été écartées ; la
  production hebdo re-vérifiera via un nouvel export Qwairy.

## 3. SEO local + photo géolocalisée (exigence Me Humbert)

Chaque article a une **portée nationale** (fond juridique, barèmes, jurisprudence)
**ET un ancrage local** imposé par le champ `ville` de son item :

1. Mention naturelle de la ville (exemple chiffré localisé, juridiction TJ/CA
   compétente, référence au cabinet) — jamais de bourrage type « à Salon-de-Provence »
   dans les H2 (règle anti-Helpful-Content de l'audit).
2. Catégorie WordPress ville correspondante ajoutée au post.
3. **Image mise en avant avec métadonnées EXIF GPS de la ville** injectées
   AVANT l'upload (`piexif` ou `exiftool`), nom de fichier et `alt` localisés.

| Ville | Lat, Lon |
|---|---|
| Aix-en-Provence | 43.5297, 5.4474 |
| Marseille | 43.2965, 5.3698 |
| Nîmes | 43.8367, 4.3601 |
| Salon-de-Provence | 43.6403, 5.0977 |
| Arles | 43.6766, 4.6278 |
| Avignon | 43.9493, 4.8055 |
| Marignane | 43.4166, 5.2147 |

## 4. Spécifications techniques WordPress (sondées le 2026-07-07)

- Les deux sites : WordPress + **Yoast**, REST API v2 **ouverte en lecture**,
  écriture protégée (401) avec **Application Passwords actifs**
  (`/wp-admin/authorize-application.php`).
- Publication : `POST {site}/wp-json/wp/v2/posts` (Basic Auth
  `user:application-password`), hero via `POST /wp-json/wp/v2/media`
  (`featured_media`). Secrets env : `WP_MEDICAL_USER`, `WP_MEDICAL_APP_PASSWORD`,
  `WP_ACCIDENT_USER`, `WP_ACCIDENT_APP_PASSWORD` — **jamais committés** (règle 5
  CLAUDE.md).
- **Avantage vs Sanity** : WordPress accepte nativement les `<table>` et le
  **SVG inline** dans le corps du post — le gabarit AIVF passe sans dégradation.
- **Méta Yoast** : `_yoast_wpseo_title` / `_yoast_wpseo_metadesc` ne sont pas
  inscriptibles via REST par défaut. Tester en début de session ; si refusé,
  publier avec title/H1/excerpt optimisés + **logger** les métas à poser, et
  demander à Me Humbert d'installer le snippet `register_post_meta` (fourni
  dans PROMPT-PIPELINE-WP.md).
- Catégories existantes à réutiliser (ids dans `queue-wp.json` `_meta.sites`) —
  ne pas créer de nouvelles catégories sans nécessité.
- FAQ : bloc Gutenberg **Yoast FAQ** (`<!-- wp:yoast/faq-block -->`) pour le
  schema FAQPage ; à défaut `<details>` + JSON-LD FAQPage inline.

## 5. Anti-cannibalisation (TRIPLE, bloquant)

Avant chaque slug : (1) REST du site cible `?slug=`, (2) REST de l'autre WP,
(3) Sanity lexvox-victime (GROQ `slug.current`) + `queue-aivf.json`.
Les items notés `CANNIBALISATION` dans la file ont un **angle différencié
obligatoire** (décrit dans la note) : le pilier national reste sur
lexvox-victime.com, le WP prend l'angle pratique/spécifique. Un lien
cross-domaine vers le pilier Sanity est autorisé (1 max/article).

## 6. Le tableau des 150 articles (gap non traité + répartition)

Colonnes : site cible, ville d'ancrage local (rotation), priorité, source
concurrentielle. La version exécutable (slugs, mots-clés, notes d'angle) est
dans `queue-wp.json` — c'est elle que la production consomme.

| # | Sujet | Mot-clé | Site | Ville | Prio | Source | Note |
|---|---|---|---|---|---|---|---|
| 1 | Faute de la victime : quand réduit-elle ou exclut-elle l'indemnisation ? | `faute de la victime accident` | **ACCIDENT** | aix-en-provence | P1 | Benezra |  |
| 2 | Conducteur fautif ou partiellement responsable : vos droits à indemnisation | `indemnisation conducteur fautif` | **ACCIDENT** | marseille | P1 | Benezra |  |
| 3 | Perte de chance en responsabilité médicale : le pilier de votre indemnisation | `perte de chance erreur médicale` | **MÉDICAL** | nimes | P1 | gap concurrentiel (angle mort J+B) |  |
| 4 | Passager victime d'un accident : le droit à l'indemnisation intégrale | `indemnisation passager accident` | **ACCIDENT** | salon-de-provence | P1 | Benezra+Jullien |  |
| 5 | Accident sans contact : prouver l'implication d'un véhicule | `accident sans contact implication` | **ACCIDENT** | arles | P2 | Benezra |  |
| 6 | Procédure CCI / ONIAM pas à pas : seuils de gravité, délais, avis, offre | `procédure CCI ONIAM` | **MÉDICAL** | avignon | P1 | gap (angle mort J+B) | ⚠ CANNIBALISATION lexvox-victime id 31  |
| 7 | Alcool, stupéfiants ou CBD au volant : quelles conséquences sur l'indemnisation ? | `alcool au volant indemnisation victime` | **ACCIDENT** | marignane | P1 | Benezra |  |
| 8 | Défaut de casque ou de ceinture : quelle réduction d'indemnisation ? | `défaut de port du casque indemnisation` | **ACCIDENT** | aix-en-provence | P2 | Benezra |  |
| 9 | Expertise CCI ou expertise judiciaire : quelle voie choisir après un accident médical ? | `expertise CCI ou judiciaire` | **MÉDICAL** | marseille | P1 | Benezra (transposé médical) |  |
| 10 | Offre d'indemnisation de l'assureur : délais légaux, contenu et contrôle | `offre indemnisation assurance délai` | **ACCIDENT** | nimes | P1 | Benezra+Jullien |  |
| 11 | Refus d'indemnisation de l'assurance : les recours de la victime | `refus indemnisation assurance` | **ACCIDENT** | salon-de-provence | P1 | Benezra+Jullien |  |
| 12 | Le sapiteur en expertise médicale : rôle, désignation, enjeux | `sapiteur expertise médicale` | **MÉDICAL** | arles | P2 | Benezra (transposé) |  |
| 13 | Dénoncer une transaction d'indemnisation signée trop vite (délai de 15 jours) | `dénoncer transaction indemnisation` | **ACCIDENT** | avignon | P2 | Benezra |  |
| 14 | Convention IRCA : ce qu'elle change (ou pas) pour la victime | `convention IRCA indemnisation` | **ACCIDENT** | marignane | P2 | Benezra+Jullien |  |
| 15 | Lire et comprendre sa mission d'expertise médicale avant la réunion | `mission expertise médicale` | **MÉDICAL** | aix-en-provence | P2 | Benezra (transposé) |  |
| 16 | Garantie du conducteur : ce qu'elle couvre vraiment (et ses pièges) | `garantie du conducteur` | **ACCIDENT** | marseille | P1 | Benezra |  |
| 17 | Nullité du contrat d'assurance : inopposable aux victimes d'accident | `nullité contrat assurance victime` | **ACCIDENT** | nimes | P3 | Benezra |  |
| 18 | Médecin-conseil de victime en erreur médicale : pourquoi il change tout | `médecin conseil victime erreur médicale` | **MÉDICAL** | salon-de-provence | P1 | Benezra (transposé) | ⚠ CANNIBALISATION lexvox-victime id 21  |
| 19 | FGAO : être indemnisé après un délit de fuite ou face à un non-assuré (procédure et délais) | `FGAO délit de fuite indemnisation` | **ACCIDENT** | arles | P1 | Benezra+Jullien | ⚠ CANNIBALISATION lexvox-victime id 54  |
| 20 | Détective ou enquêteur mandaté par l'assurance : comment combattre son rapport | `enquêteur assurance victime` | **ACCIDENT** | avignon | P3 | Benezra |  |
| 21 | La consolidation en accident médical : date, enjeux, pièges | `consolidation accident médical` | **MÉDICAL** | marignane | P2 | Benezra (transposé) | ⚠ CANNIBALISATION lexvox-victime id 23  |
| 22 | Indemnisation du dommage corporel et impôts : le régime fiscal complet | `fiscalité indemnisation dommage corporel` | **ACCIDENT** | aix-en-provence | P2 | Jullien |  |
| 23 | Les erreurs des premières 48 heures après un accident de la route | `que faire après un accident de la route` | **ACCIDENT** | marseille | P1 | Benezra+Jullien |  |
| 24 | État antérieur et erreur médicale : ne laissez pas réduire votre indemnisation | `état antérieur erreur médicale` | **MÉDICAL** | nimes | P2 | Benezra (transposé) |  |
| 25 | Obtenir une provision après un accident de la route (amiable et référé) | `provision accident de la route` | **ACCIDENT** | salon-de-provence | P2 | Benezra | ⚠ CANNIBALISATION lexvox-victime id 24  |
| 26 | Prescription : combien de temps pour agir après un accident de la route ? | `prescription accident de la route` | **ACCIDENT** | arles | P1 | Benezra+Jullien |  |
| 27 | Obtenir une provision après un accident médical (CCI, référé-provision) | `provision accident médical` | **MÉDICAL** | avignon | P2 | Benezra (transposé) |  |
| 28 | Quel tribunal saisir après un accident de la route ? | `tribunal compétent accident route` | **ACCIDENT** | marignane | P3 | Benezra+Jullien |  |
| 29 | Classement sans suite après un accident : les recours de la victime | `classement sans suite accident` | **ACCIDENT** | aix-en-provence | P2 | Benezra |  |
| 30 | Capitaliser les préjudices futurs après un accident médical (barème, rente ou capital) | `capitalisation préjudice futur` | **MÉDICAL** | marseille | P3 | Benezra (transposé) |  |
| 31 | Aggravation après consolidation : rouvrir son dossier d'indemnisation | `aggravation réouverture dossier indemnisation` | **ACCIDENT** | nimes | P2 | Benezra | REFONTE  |
| 32 | Réparation intégrale : le principe qui gouverne votre indemnisation | `réparation intégrale préjudice` | **ACCIDENT** | salon-de-provence | P2 | Benezra+Jullien |  |
| 33 | Tierce personne après un accident médical : évaluation et financement | `tierce personne accident médical` | **MÉDICAL** | arles | P2 | Benezra (transposé) |  |
| 34 | Barème de capitalisation (Gazette du Palais, BCRIV) : mode d'emploi pour les victimes | `barème de capitalisation` | **ACCIDENT** | avignon | P1 | Benezra |  |
| 35 | L'aide d'un proche se paie : l'assistance familiale indemnisée en tierce personne | `tierce personne aide familiale` | **ACCIDENT** | marignane | P2 | Benezra | ⚠ CANNIBALISATION lexvox-victime id 6  |
| 36 | Logement et véhicule adaptés après un handicap d'origine médicale | `logement adapté handicap indemnisation` | **MÉDICAL** | aix-en-provence | P3 | Benezra (transposé) |  |
| 37 | Négocier seul avec l'assureur : les pièges qui coûtent des dizaines de milliers d'euros | `négocier indemnisation sans avocat` | **ACCIDENT** | marseille | P1 | Benezra |  |
| 38 | Combien coûte un avocat en dommage corporel — et qui paie vraiment ? | `prix avocat dommage corporel` | **ACCIDENT** | nimes | P2 | Benezra+Jullien | Différencier des posts honoraires existants  |
| 39 | Préjudice psychique après une erreur médicale : PTSD, anxiété, bouleversement de vie | `préjudice psychique erreur médicale` | **MÉDICAL** | salon-de-provence | P2 | Benezra (transposé) |  |
| 40 | Accident mortel : les démarches des proches, étape par étape | `accident mortel démarches proches` | **ACCIDENT** | arles | P1 | Benezra |  |
| 41 | Préjudice économique du conjoint survivant : calcul et preuves | `préjudice économique conjoint survivant` | **ACCIDENT** | avignon | P2 | Benezra |  |
| 42 | Décès à l'hôpital : les droits des proches (victimes par ricochet) | `décès hôpital indemnisation famille` | **MÉDICAL** | marignane | P1 | Benezra (transposé) |  |
| 43 | Deuil pathologique : un préjudice indemnisable des proches | `deuil pathologique indemnisation` | **ACCIDENT** | aix-en-provence | P3 | Benezra |  |
| 44 | Préjudice d'affection après un décès sur la route : qui peut demander, combien | `préjudice affection décès accident` | **ACCIDENT** | marseille | P2 | Benezra | ⚠ CANNIBALISATION lexvox-victime id 16  |
| 45 | Prescription en responsabilité médicale : la règle des 10 ans et ses pièges | `prescription erreur médicale` | **MÉDICAL** | nimes | P1 | Jullien (transposé) | ⚠ CANNIBALISATION lexvox-victime id 28  |
| 46 | État antérieur et décompensation : l'assureur ne peut pas s'en servir contre vous | `état antérieur victime accident` | **ACCIDENT** | salon-de-provence | P1 | Benezra |  |
| 47 | Stress post-traumatique après un accident : faire reconnaître le préjudice psychique | `stress post traumatique accident indemnisation` | **ACCIDENT** | arles | P1 | Benezra+Qwairy | Couvre aussi le prompt Qwairy 100% gap 'compensation préjudices psychologiques après accident'. |
| 48 | Aggravation après consolidation : rouvrir un dossier d'accident médical | `aggravation après consolidation` | **MÉDICAL** | avignon | P2 | Benezra (transposé) |  |
| 49 | Votre proche est en réanimation après un accident : le guide des 72 premières heures | `proche en réanimation accident` | **ACCIDENT** | marignane | P2 | Benezra |  |
| 50 | Prothèses, appareillage, fauteuil : faire financer le meilleur équipement par l'assureur | `frais prothèse indemnisation` | **ACCIDENT** | aix-en-provence | P2 | Benezra | ⚠ CANNIBALISATION lexvox-victime id 34  |
| 51 | Contrôler l'offre de l'ONIAM ou de l'assureur du praticien avant de signer | `offre ONIAM indemnisation` | **MÉDICAL** | marseille | P2 | Benezra (transposé) |  |
| 52 | Échelle de Glasgow et bilan neuropsychologique : objectiver le traumatisme crânien | `échelle de Glasgow traumatisme crânien` | **ACCIDENT** | nimes | P2 | Benezra | Complète le cluster trauma crânien existant du site accident — maillage obligatoire. |
| 53 | Rupture identitaire et préjudices permanents exceptionnels : les faire indemniser | `préjudice permanent exceptionnel` | **ACCIDENT** | salon-de-provence | P3 | Benezra |  |
| 54 | Contre-expertise médicale : coût, délais et procédure | `contre expertise médicale` | **MÉDICAL** | arles | P2 | Benezra (transposé) |  |
| 55 | Carambolage et accident collectif : qui indemnise qui ? | `carambolage indemnisation` | **ACCIDENT** | avignon | P2 | Benezra |  |
| 56 | Accident de tramway ou de train : quel régime d'indemnisation ? | `accident tramway indemnisation` | **ACCIDENT** | marignane | P3 | Benezra+Jullien |  |
| 57 | Faute médicale ou aléa thérapeutique : qui vous indemnise ? (arbre de décision) | `faute médicale ou aléa thérapeutique` | **MÉDICAL** | aix-en-provence | P1 | gap (angle mort J+B) | Pages faute/aléa existent sur le site  |
| 58 | Accident de la route à l'étranger : carte verte, FGAO et recours | `accident à l'étranger indemnisation` | **ACCIDENT** | marseille | P2 | Benezra |  |
| 59 | Accident de chasse : responsabilité et indemnisation de la victime | `accident de chasse indemnisation` | **ACCIDENT** | nimes | P3 | Jullien |  |
| 60 | Typologie des fautes médicales 2026 : diagnostic, traitement, geste opératoire, infection | `types de fautes médicales` | **MÉDICAL** | salon-de-provence | P1 | Qwairy (gap 100%) | GEO/AEO  |
| 61 | Morsure de chien : responsabilité du propriétaire et indemnisation | `morsure de chien indemnisation` | **ACCIDENT** | arles | P2 | Jullien |  |
| 62 | Chute dans un supermarché ou un magasin : vos droits à indemnisation | `chute supermarché indemnisation` | **ACCIDENT** | avignon | P2 | Jullien |  |
| 63 | Erreur de diagnostic ou erreur opératoire : quelles différences pour votre indemnisation ? | `erreur de diagnostic responsabilité` | **MÉDICAL** | marignane | P1 | Qwairy (gap 100%) |  |
| 64 | Chute sur la voie publique : faire jouer le défaut d'entretien de l'ouvrage public | `défaut entretien ouvrage public chute` | **ACCIDENT** | aix-en-provence | P3 | Jullien |  |
| 65 | Accident scolaire : l'indemnisation de l'enfant victime | `accident scolaire indemnisation` | **ACCIDENT** | marseille | P3 | Jullien |  |
| 66 | Erreur de traitement, de médicament ou de dosage : responsabilité et indemnisation | `erreur de médicament indemnisation` | **MÉDICAL** | nimes | P1 | Qwairy (gap 100%) |  |
| 67 | Percuté volontairement par un véhicule : agression ou accident de la route ? | `violences volontaires véhicule indemnisation` | **ACCIDENT** | salon-de-provence | P3 | Benezra |  |
| 68 | Vélo électrique, VAE débridé : quelles conséquences sur l'indemnisation ? | `accident vélo électrique indemnisation` | **ACCIDENT** | arles | P2 | Benezra |  |
| 69 | Quels préjudices sont indemnisables après une erreur médicale ? (Dintilhac appliqué) | `préjudices indemnisables erreur médicale` | **MÉDICAL** | avignon | P1 | Qwairy (gap 100%) |  |
| 70 | Combien nos clients ont obtenu : études de cas chiffrées d'indemnisation (série) | `montant indemnisation accident exemples` | **ACCIDENT** | marignane | P2 | Jullien+Benezra | FORMAT SIGNATURE Jullien (~90 pages de cas chiffrés)  |
| 71 | Types de préjudices et de handicaps indemnisables : le guide complet des victimes | `types de préjudices indemnisables` | **ACCIDENT** | aix-en-provence | P1 | Qwairy (gap 100%) | GEO/AEO  |
| 72 | Avocat en erreur médicale « payé au résultat » : comment fonctionnent les honoraires | `avocat erreur médicale honoraires résultat` | **MÉDICAL** | marseille | P2 | Qwairy (gap 60%) |  |
| 73 | Documenter un préjudice grave avant de consulter un avocat : la checklist complète | `documenter préjudice grave` | **ACCIDENT** | nimes | P1 | Qwairy (gap 100%) |  |
| 74 | Avocat en préjudices graves et grand handicap : comment le choisir, où le trouver | `avocat préjudice grave handicap` | **ACCIDENT** | salon-de-provence | P1 | Qwairy (gap 100%) | BOFU  |
| 75 | Combien nos clients ont obtenu après une erreur médicale : études de cas chiffrées (série) | `indemnisation erreur médicale montant` | **MÉDICAL** | arles | P2 | Jullien (format transposé) | FORMAT SIGNATURE  |
| 76 | Dommage corporel : définition, préjudices couverts et fonctionnement de l'indemnisation | `dommage corporel définition` | **ACCIDENT** | avignon | P1 | Qwairy (gap 100%) |  |
| 77 | Évaluer le montant de son indemnisation : la méthode des avocats de victimes | `évaluer montant indemnisation` | **ACCIDENT** | marignane | P1 | Qwairy (gap 100%) |  |
| 78 | Retard de diagnostic d'un cancer : perte de chance et indemnisation | `retard diagnostic cancer indemnisation` | **MÉDICAL** | aix-en-provence | P2 | gap total J+B |  |
| 79 | Procédure amiable d'indemnisation : étapes, frais, délais et erreurs à éviter | `procédure amiable indemnisation` | **ACCIDENT** | marseille | P1 | Qwairy (cluster 10 prompts) | PILIER GEO  |
| 80 | Recours contre son assureur : le guide complet (amiable, judiciaire, documents, délais) | `recours contre assureur` | **ACCIDENT** | nimes | P1 | Qwairy (cluster 12 prompts) | PILIER GEO  |
| 81 | Retard de diagnostic d'un infarctus ou d'un AVC aux urgences : recours | `retard diagnostic AVC urgences` | **MÉDICAL** | salon-de-provence | P2 | gap total J+B |  |
| 82 | Protection juridique et assistance après un accident : comment l'activer, ce qu'elle paie | `protection juridique accident` | **ACCIDENT** | arles | P1 | Qwairy (cluster assistance juridique, gap 100%) | Couvre 4 prompts 100% gap (où trouver une assistance juridique, est-elle nécessaire, meilleurs services, avocat sans frais initiaux). |
| 83 | Accident du travail : les documents à préparer et les pièges du dossier | `documents accident du travail avocat` | **ACCIDENT** | avignon | P2 | Qwairy (cluster accidents du travail) | Couvre les prompts 'documents à préparer', 'meilleures pratiques dossier', 'accidents fréquents au travail et comment se défendre'. |
| 84 | Erreur médicamenteuse et surdosage : responsabilité et indemnisation | `erreur médicamenteuse indemnisation` | **MÉDICAL** | marignane | P2 | gap total J+B |  |
| 85 | Accidents de la vie : vos recours au-delà de la route et du travail | `accident de la vie indemnisation` | **ACCIDENT** | aix-en-provence | P1 | Qwairy (gap 100%) | REFONTE  |
| 86 | Indemnisation d'une fracture du fémur après un accident | `indemnisation fracture fémur` | **ACCIDENT** | marseille | P3 | Jullien |  |
| 87 | Compresse ou instrument oublié après une opération : la faute présumée | `corps étranger oublié opération` | **MÉDICAL** | nimes | P2 | gap total J+B |  |
| 88 | Fracture du bassin ou du cotyle : évaluation et indemnisation | `indemnisation fracture bassin` | **ACCIDENT** | salon-de-provence | P3 | Jullien |  |
| 89 | Fracture de jambe (tibia-péroné) : séquelles et indemnisation | `indemnisation fracture jambe` | **ACCIDENT** | arles | P3 | Jullien |  |
| 90 | Erreur de côté : opération du mauvais organe ou du mauvais membre | `erreur de côté chirurgie indemnisation` | **MÉDICAL** | avignon | P2 | gap total J+B |  |
| 91 | Rupture des ligaments croisés du genou après accident : indemnisation | `indemnisation ligaments croisés genou` | **ACCIDENT** | marignane | P3 | Benezra |  |
| 92 | Lésion de la coiffe des rotateurs (épaule) : indemnisation de la victime | `indemnisation coiffe des rotateurs` | **ACCIDENT** | aix-en-provence | P3 | Jullien |  |
| 93 | Défaut d'information et consentement : le préjudice d'impréparation | `défaut information médicale préjudice` | **MÉDICAL** | marseille | P2 | gap total J+B |  |
| 94 | Traumatisme de la main et des doigts : indemnisation (préhension, préjudice pro) | `indemnisation traumatisme main` | **ACCIDENT** | nimes | P3 | Jullien |  |
| 95 | Fractures de côtes et volet thoracique : indemnisation après un accident | `indemnisation fracture côtes` | **ACCIDENT** | salon-de-provence | P3 | Benezra |  |
| 96 | Erreur transfusionnelle et contamination (hépatite, VIH) : indemnisation | `contamination transfusion indemnisation` | **MÉDICAL** | arles | P2 | gap total J+B |  |
| 97 | Fracture vertébrale lombaire et tassement : indemnisation | `indemnisation fracture vertèbre lombaire` | **ACCIDENT** | avignon | P3 | Benezra | Angle rachis lombaire distinct du 'fracture vertèbre' générique de la queue Sanity (id 32). |
| 98 | Traumatisme facial et fractures du visage : préjudice esthétique et indemnisation | `indemnisation traumatisme facial` | **ACCIDENT** | marignane | P3 | Jullien |  |
| 99 | Escarre et défaut de soins à l'hôpital ou en EHPAD : recours de la victime | `escarre défaut de soins indemnisation` | **MÉDICAL** | aix-en-provence | P2 | gap total J+B |  |
| 100 | Perte d'audition et acouphènes après un accident : faire reconnaître le préjudice | `indemnisation acouphènes accident` | **ACCIDENT** | marseille | P3 | Benezra |  |
| 101 | Brûlures, cicatrices et grand brûlé : indemnisation du préjudice esthétique et de la souffrance | `indemnisation brûlures accident` | **ACCIDENT** | nimes | P3 | Jullien |  |
| 102 | Chute d'un patient à l'hôpital : défaut de surveillance et indemnisation | `chute patient hôpital responsabilité` | **MÉDICAL** | salon-de-provence | P2 | gap total J+B |  |
| 103 | Traumatisme dentaire après un accident : indemnisation (prothèses, implants) | `indemnisation traumatisme dentaire` | **ACCIDENT** | arles | P4 | Jullien |  |
| 104 | Lésion d'organes internes (rate, rein, poumon) : indemnisation après accident | `indemnisation lésion rate accident` | **ACCIDENT** | avignon | P4 | Benezra |  |
| 105 | Défaut de surveillance post-opératoire : quand la clinique engage sa responsabilité | `défaut surveillance post-opératoire` | **MÉDICAL** | marignane | P2 | gap total J+B |  |
| 106 | Syndrome post-commotionnel : troubles persistants après un choc à la tête | `syndrome post-commotionnel indemnisation` | **ACCIDENT** | aix-en-provence | P4 | Benezra |  |
| 107 | Accident de quad : responsabilité et indemnisation de la victime | `indemnisation accident quad` | **ACCIDENT** | marseille | P3 | Benezra |  |
| 108 | Lésion nerveuse ou névrome après une chirurgie : indemnisation | `lésion nerveuse post-chirurgie indemnisation` | **MÉDICAL** | nimes | P3 | gap total J+B |  |
| 109 | Accident avec un poids lourd : spécificités de l'indemnisation | `indemnisation accident camion` | **ACCIDENT** | salon-de-provence | P3 | Jullien |  |
| 110 | Accident de bus ou de transport en commun : quels droits pour les passagers ? | `indemnisation accident bus` | **ACCIDENT** | arles | P3 | Jullien |  |
| 111 | Syndrome de la queue de cheval mal diagnostiqué : urgence manquée et indemnisation | `syndrome queue de cheval indemnisation` | **MÉDICAL** | avignon | P3 | gap total J+B |  |
| 112 | Accident de bateau ou de jet-ski : régime d'indemnisation | `indemnisation accident bateau` | **ACCIDENT** | marignane | P4 | Benezra |  |
| 113 | Accident d'équitation ou chute de cheval : indemnisation | `indemnisation accident cheval` | **ACCIDENT** | aix-en-provence | P4 | Benezra |  |
| 114 | Erreur de radiologie : imagerie mal ou non interprétée | `erreur radiologie indemnisation` | **MÉDICAL** | marseille | P3 | gap total J+B |  |
| 115 | Accident sur une structure gonflable ou un manège : responsabilité et indemnisation | `indemnisation accident manège` | **ACCIDENT** | nimes | P4 | Benezra |  |
| 116 | Accident de trajet domicile-travail : accident du travail ou de la route ? | `accident de trajet indemnisation` | **ACCIDENT** | salon-de-provence | P3 | Benezra+Jullien |  |
| 117 | Déficit neurologique après péridurale ou rachianesthésie : recours | `complication péridurale indemnisation` | **MÉDICAL** | arles | P3 | gap total J+B |  |
| 118 | Faute inexcusable de l'employeur : la majoration d'indemnisation après un accident du travail grave | `faute inexcusable employeur indemnisation` | **ACCIDENT** | avignon | P3 | Jullien |  |
| 119 | Accident causé par un véhicule volé ou non identifié : le rôle du FGAO | `accident véhicule volé indemnisation` | **ACCIDENT** | marignane | P4 | Benezra |  |
| 120 | Brûlure au bloc opératoire (laser, bistouri électrique) : indemnisation | `brûlure bloc opératoire indemnisation` | **MÉDICAL** | aix-en-provence | P3 | gap total J+B |  |
| 121 | Étude de cas : l'indemnisation détaillée d'un motard gravement blessé | `indemnisation motard montant exemple` | **ACCIDENT** | marseille | P3 | Jullien (format) |  |
| 122 | Étude de cas : combien pour un piéton renversé et lourdement handicapé | `indemnisation piéton montant exemple` | **ACCIDENT** | nimes | P3 | Jullien (format) |  |
| 123 | Retard de prise en charge aux urgences : caractériser la perte de chance | `retard prise en charge urgences` | **MÉDICAL** | salon-de-provence | P2 | gap total J+B |  |
| 124 | Étude de cas : l'indemnisation d'un traumatisé crânien après un accident | `indemnisation traumatisme crânien montant` | **ACCIDENT** | arles | P4 | Jullien+Benezra (format) |  |
| 125 | Accident en covoiturage ou VTC : qui indemnise le passager ? | `indemnisation accident covoiturage` | **ACCIDENT** | avignon | P4 | gap |  |
| 126 | Erreur ophtalmologique et perte de vue post-opératoire : indemnisation | `erreur ophtalmologique indemnisation` | **MÉDICAL** | marignane | P3 | gap total J+B |  |
| 127 | Entorse grave de la cheville ou du genou : quand elle laisse des séquelles indemnisables | `indemnisation entorse grave` | **ACCIDENT** | aix-en-provence | P4 | Benezra |  |
| 128 | Accident dû au mauvais état de la route : engager la responsabilité du gestionnaire | `accident mauvais état route indemnisation` | **ACCIDENT** | marseille | P4 | Jullien |  |
| 129 | Clinique ou praticien : qui est responsable de votre dommage ? (arbre de décision) | `responsabilité clinique ou médecin` | **MÉDICAL** | nimes | P2 | gap total J+B |  |
| 130 | Troubles du sommeil et anxiété après un accident : des préjudices à ne pas négliger | `troubles anxiété après accident` | **ACCIDENT** | salon-de-provence | P4 | Benezra |  |
| 131 | Accident de vélo d'un enfant : protection renforcée de la loi Badinter | `indemnisation accident vélo enfant` | **ACCIDENT** | arles | P4 | Benezra |  |
| 132 | Produit de santé défectueux (prothèse, implant) : responsabilité et indemnisation | `prothèse défectueuse indemnisation` | **MÉDICAL** | avignon | P2 | gap total J+B |  |
| 133 | Traumatisme du genou et arthrose post-traumatique : l'indemnisation dans la durée | `arthrose post-traumatique indemnisation` | **ACCIDENT** | marignane | P4 | Benezra |  |
| 134 | Accident avec un engin de chantier ou agricole : quel régime d'indemnisation ? | `indemnisation accident engin chantier` | **ACCIDENT** | aix-en-provence | P4 | gap |  |
| 135 | Accident vaccinal : l'indemnisation par l'ONIAM | `accident vaccinal indemnisation ONIAM` | **MÉDICAL** | marseille | P3 | gap total J+B |  |
| 136 | Iatrogénie médicamenteuse et effet indésirable grave : quels recours ? | `iatrogénie médicamenteuse indemnisation` | **MÉDICAL** | nimes | P3 | gap total J+B |  |
| 137 | Paralysie du plexus brachial du nouveau-né (paralysie d'Erb) : indemnisation | `paralysie plexus brachial nouveau-né` | **MÉDICAL** | salon-de-provence | P3 | gap total J+B | Angle néonatal distinct du cluster 'accouchement' existant du site (déchirure, forceps…)  |
| 138 | Erreur de diagnostic prénatal et handicap non décelé : l'état du droit après la loi anti-Perruche | `erreur diagnostic prénatal indemnisation` | **MÉDICAL** | arles | P3 | gap total J+B |  |
| 139 | Décès péri-opératoire : les recours des proches | `décès péri-opératoire indemnisation` | **MÉDICAL** | avignon | P3 | gap total J+B |  |
| 140 | Calculer la perte de chance : le taux qui détermine votre indemnisation médicale | `calcul perte de chance médicale` | **MÉDICAL** | marignane | P2 | gap total J+B |  |
| 141 | Barème d'indemnisation de l'accident médical : fourchettes par poste | `barème indemnisation accident médical` | **MÉDICAL** | aix-en-provence | P2 | gap total J+B |  |
| 142 | Délais d'indemnisation d'une erreur médicale : combien de temps à chaque étape | `délai indemnisation erreur médicale` | **MÉDICAL** | marseille | P2 | Qwairy |  |
| 143 | Erreur médicale : recours amiable (CCI) ou judiciaire, comment choisir | `recours amiable ou judiciaire erreur médicale` | **MÉDICAL** | nimes | P3 | Qwairy+Benezra |  |
| 144 | Les documents à réunir pour un dossier d'erreur médicale | `documents dossier erreur médicale` | **MÉDICAL** | salon-de-provence | P3 | Qwairy |  |
| 145 | Déficit fonctionnel permanent d'origine médicale : évaluation et indemnisation | `DFP accident médical indemnisation` | **MÉDICAL** | arles | P3 | gap total J+B | Transposition médicale du poste DFP — lier au pilier DFP national de lexvox-victime.com. |
| 146 | Incidence professionnelle après un accident médical : reconversion et perte de carrière | `incidence professionnelle accident médical` | **MÉDICAL** | avignon | P3 | gap total J+B |  |
| 147 | Souffrances endurées après une faute médicale : évaluation et indemnisation | `souffrances endurées accident médical` | **MÉDICAL** | marignane | P3 | gap total J+B |  |
| 148 | Infection nosocomiale grave (septicémie, bactérie résistante) : indemnisation renforcée | `infection nosocomiale grave indemnisation` | **MÉDICAL** | aix-en-provence | P4 | gap | Angle 'forme grave' distinct des posts nosocomiale existants du site  |
| 149 | Préjudice d'établissement après un grand handicap d'origine médicale | `préjudice établissement handicap médical` | **MÉDICAL** | marseille | P4 | gap total J+B |  |
| 150 | Erreur et complications d'anesthésie : responsabilité et indemnisation | `erreur anesthésie indemnisation` | **MÉDICAL** | nimes | P3 | gap total J+B | Angle 100% anesthésie, distinct du pilier 'erreur chirurgicale/anesthésie' national (Sanity id 29). |


## 7. Suivi

- La production tient `PUBLICATION-TRACKER-WP.md` (créé au premier run).
- Rafraîchir les opportunités Qwairy ~1×/semaine si le connecteur est
  disponible, et enrichir la file en conséquence.
