# PLAN PODCASTS LEXVOX — 2026-08

Automatisation de **trois chaînes de podcasts** générés avec NotebookLM à
partir des meilleurs articles (mesurés dans Google Search Console) des sites
du cabinet. Ce document contient l'analyse critique du prompt initial (§2),
l'architecture cible (§3), le plan d'action phasé (§4) et les décisions à
valider par Me Humbert (§5).

Fichiers liés :
- `PROMPT-PODCAST-NOTEBOOKLM.md` — le prompt maître réécrit (v3), à utiliser
  dans une session Claude **sur le poste de Me Humbert** (voir §3.1).
- `PROMPT-MONTAGE-DIFFUSION.md` — l'étape aval : intro (voix de l'avocat) dans la
  voix de l'avocat + corps NotebookLM → MP3 diffusable, avec
  `tools/voix_script.py` et `tools/podcast_montage.py`.
- `PROMPT-INTRO-VOIX.md` — produit la question d'accroche et le sujet
  à partir de l'article, et porte les réglages de voix Voicebox.
- `podcasts/voix-avocat/SCRIPT-INTRO-<chaine>.md` et `SCRIPT-OUTRO-<chaine>.md`
  — les gabarits lus par la voix clonée de l'avocat.
- `podcasts/queue-podcast.csv` — **le** fichier d'état, unique pour les trois
  chaînes (colonne `chaine`), rempli une seule fois depuis Search Console.
- `podcasts/fiche-cabinet-victimes.md` / `-famille.md` / `-permis.md` — la
  « fiche cabinet » injectée comme **seconde source** dans chaque notebook
  (présentation + conclusion/CTA, textes verrouillés déontologiquement). Le
  Markdown est la source ; `tools/fiche_to_pdf.py` en produit le **PDF**
  (téléversé dans NotebookLM) et le **DOCX** (relecture dans Google Docs).
- `podcasts/CALIBRATION-NOTEBOOKLM.md` — carnet d'interface rempli par
  l'agent au pilote de chaque chaîne.

---

## 1. Les trois chaînes

| Chaîne | Public | Sites sources (propriétés GSC) | Signataire des articles | Nom suggéré |
|---|---|---|---|---|
| **Victimes** | victimes de dommage corporel / erreur médicale | `medical.lexvox-avocat.fr` + `victime-accident.lexvox-avocat.fr` + `lexvox-victime.com` (⚠️ périmètre à confirmer) | Me Patrice Humbert | **LEXVICTIME** — le podcast du droit des victimes |
| **Famille** | personnes en instance de divorce, garde, pension | `lexvox-divorce.com` ✅ | **Me Cédrine Raybaud** | « Divorce & famille : parlons-en » |
| **Permis** | conducteurs (suspension, annulation, alcool/stupéfiants) | `lexvox-permis.com` ✅ | Me Patrice Humbert | « Permis en danger » |

Les trois sites se renvoient mutuellement en pied de page (« Nos sites :
Droit routier / Droit de la famille / Dommage corporel »), ce qui confirme le
périmètre de chaque chaîne.

Chaque chaîne = 24 épisodes (les 24 meilleurs articles GSC), un notebook
NotebookLM par article, un épisode < 5 min par notebook. Total : 72 épisodes,
soit **4 journées de production** au quota de 20 générations/jour (§3.4).

Chaque épisode est composé de trois blocs assemblés : une **introduction de
30–40 s dite par l'avocat lui-même** (voix clonée Voicebox), qui s'ouvre
toujours sur une **question dont la réponse est l'article** puis sur le
**jingle verbal** de la série ; le débat NotebookLM ; puis une **outro de
25–35 s** dans la même voix réelle, qui porte l'appel à l'action — le débat ne le récite donc plus, et l'outro étant
identique pour toute une chaîne, trois enregistrements couvrent les
72 épisodes. Les deux animateurs du débat sont les mêmes dans les trois
chaînes : **Nathalie**, la juriste pédagogue, et **Nicolas**, le journaliste
curieux — deux voix créées par le cabinet, que l'introduction présente
nommément et
annonce comme telles (cf. `PROMPT-MONTAGE-DIFFUSION.md` §1 et §A3).

---

## 2. Analyse critique du prompt initial

### 2.1 Ce qui est bon — à conserver
- Le **format débat à deux voix**, la cible < 5 min (taux de complétion), le
  ton vulgarisateur : bons choix éditoriaux, conservés tels quels.
- La **bascule « mode texte »** si l'ingestion de l'URL échoue : bon réflexe,
  conservé et précisé (extraction propre du texte de l'article).
- La structure en séquence d'actions numérotées : conservée, mais complétée
  (états, quotas, post-traitement, QA).

### 2.2 Défauts bloquants (le prompt ne peut pas produire 24 épisodes en l'état)

1. **Contradiction interne fatale.** La règle n° 1 impose « SOURCE EXCLUSIVE :
   basez la totalité du débat STRICTEMENT sur la source » … puis exige que les
   hôtes parlent de la spécialisation CNB, du cursus médecine, de la
   certification IA et des honoraires — **informations absentes de l'article**.
   NotebookLM va soit ignorer ces consignes (source unique oblige), soit les
   halluciner. **Correction v2 :** chaque notebook reçoit **deux sources** —
   l'article (le fond) + la « fiche cabinet » (présentation et conclusion).
   La règle « sources exclusives » devient alors cohérente et tenable. La
   fiche est un **PDF téléversé**, identique pour tous les épisodes d'une
   chaîne : un fichier à joindre au lieu d'un copier-coller par épisode,
   soit 72 manipulations et autant d'occasions d'erreur en moins.
2. **Prompt mono-article à trous, sans état.** `[INSÉRER L'URL]` = une session
   manuelle par article, aucune trace de ce qui est fait/raté. Impossible de
   tenir 24 épisodes × 3 chaînes. **Correction v2 :** boucle pilotée par un
   **CSV d'état unique** pour les trois chaînes (généré une fois depuis GSC,
   cf. §3.3) : l'agent filtre sur la colonne `chaine`, prend la première
   ligne `todo`, la traite, met à jour la ligne, passe à la suivante.
3. **Le champ « Personnaliser » de NotebookLM est limité** (~500 caractères
   constatés ; à re-vérifier en calibration). Le texte de personnalisation du
   prompt initial fait ~2 300 caractères : il serait **tronqué silencieusement**.
   **Correction v2 :** personnalisation courte (443 à 448 caractères selon la
   chaîne, comptés exactement) + tout le contenu long (biographie, CTA mot à
   mot) déplacé dans la fiche cabinet (source n° 2), que les hôtes peuvent
   citer intégralement.
4. **Quotas ignorés.** NotebookLM limite les générations audio. Le cabinet
   dispose de l'**abonnement payant : 20 générations/jour** (confirmé
   2026-08-13). Lancer 24 générations d'affilée échouerait quand même.
   **Correction v2 :** compteur quotidien tenu dans le journal, arrêt propre
   des lancements à 20, reprise le lendemain grâce au CSV.
5. **Aucune phase de sélection.** Le prompt suppose l'URL connue ; votre
   demande (top 24 GSC → CSV) n'y figure pas. **Correction v2 :** Phase 1
   dédiée (§4), exécutée une seule fois par chaîne.

### 2.3 Défauts majeurs (fiabilité et qualité)

6. **Durée par consigne texte = non fiable.** « STRICTEMENT MOINS DE 5
   MINUTES » en prose est ignoré une fois sur deux. NotebookLM expose un
   **sélecteur de durée** (« Plus court / Par défaut / Plus long ») : la v2
   l'utilise (option courte) + garde la consigne + contrôle la durée réelle
   en QA (ffprobe), avec tolérance jusqu'à 5 min 30.
7. **Langue de sortie non configurée.** Rien ne garantit un épisode en
   français ; la v2 impose la vérification du réglage « langue de sortie »
   avant la première génération de chaque session.
8. **Téléchargement/renommage fragiles.** Renommer dans le navigateur est
   le point de friction classique ; le format téléchargé varie (.wav/.m4a).
   La v2 télécharge sans renommer, puis un **post-traitement local** fait le
   travail proprement : renommage `podcast-<slug>`, conversion MP3,
   normalisation de sonie (loudnorm ‑16 LUFS, standard podcast), tags ID3.
9. **Aucune QA.** Rien ne vérifie que l'épisode est en français, dure < 5 min,
   contient le CTA final, et n'invente pas de droit. La v2 ajoute une
   checklist QA par épisode + écoute humaine des 2 premiers épisodes de
   chaque chaîne, puis par échantillonnage (1 sur 5).
10. **Rien après le fichier audio.** Pas d'hébergement, pas de flux RSS, pas
    d'intégration sur les pages articles, pas de transcription (pourtant un
    atout SEO), pas de mesure. La v2 ajoute une Phase 4 « Publication &
    mesure » (§4) — c'est elle qui transforme 72 fichiers en audience.
11. **Boucle d'attente optimiste.** « 2 à 4 minutes » : en pratique 3 à 10 min
    et plus selon la charge. « Attends 15 s et relance » : trop naïf. La v2
    définit timeout 15 min, 1 seul retry après 60 s, puis `status=error`
    journalisé — jamais de clics au hasard dans l'interface.

### 2.4 Risques déontologiques (RIN, loi n° 71-1130) — ✅ ARBITRÉS le 2026-08-13

Un podcast diffusé en masse est de la **publicité personnelle** (RIN art.
10.2 : sincère et véridique, sans mention comparative). Me Humbert a validé
les quatre corrections ci-dessous, désormais figées dans
`podcasts/fiche-cabinet-victimes.md` (et son PDF) :

12. **« 1er avocat certifié en IA en France »** : superlatif comparatif,
    **retiré de l'audio** au profit de la variante factuelle « avocat
    certifié en intelligence artificielle, créateur d'outils d'analyse des
    préjudices ». Le superlatif reste sur le site — il n'est simplement pas
    répété à l'oral dans 72 épisodes.
13. **Honoraires.** « un pourcentage sur les sommes obtenues » seul décrit un
    pacte de quota litis prohibé (art. 10, loi 71-1130). Formule retenue :
    *convention d'honoraires signée avant intervention, comprenant une part
    fixe et un complément calculé sur le résultat*. Aucune autre formulation
    ne doit sortir dans l'audio, et **aucun montant** (les 700 € HT et le
    10–15 % du site ne sont pas cités : ils varient et vieillissent mal).
14. **Promesse de résultat.** « obtenir une réparation intégrale » promet un
    résultat → remplacé par *« faire valoir vos droits à la réparation
    intégrale »*. Les indemnisations déjà obtenues ne sont pas mentionnées.
15. **Titres réellement détenus** (vérifiés dans `index.html`, bloc auteur) :
    certificat de spécialisation CNB **en droit du dommage corporel**
    uniquement — la responsabilité médicale n'est PAS présentée comme une
    spécialisation CNB ; Master en droit de la santé ; DU sciences
    criminelles ; formation en faculté de médecine sur les traumatismes
    cranio-cérébraux. **Ne pas recycler la fiche victimes dans les chaînes
    famille et permis** — chaque chaîne a sa fiche, limitée aux titres
    vérifiés pour son domaine.

**Garde-fou outillé :** `tools/fiche_to_pdf.py` refuse de générer le PDF
d'une fiche contenant encore une mention « À VALIDER » ou « ⚠ ». Un texte
non arbitré ne peut donc pas partir dans l'audio par inadvertance.

### 2.4 bis — Ce que la rédaction des fiches famille et permis a révélé (2026-08-13)

La règle « une fiche par chaîne, jamais de recyclage » n'était pas une
précaution de principe : la lecture des pages publiques de
`lexvox-divorce.com` et `lexvox-permis.com` a fait apparaître **quatre
divergences** qui auraient produit des informations fausses dans 48 épisodes
si la fiche victimes avait été transposée.

| Élément | Chaîne victimes | Chaînes famille et permis |
|---|---|---|
| Signataire des articles | Me Patrice Humbert | **Me Cédrine Raybaud** en famille ; Me Humbert en permis |
| Première consultation | **gratuite** | **payante**, 30 min à tarif fixe (80 € TTC affichés) |
| Couverture territoriale | « partout en France en visioconférence » | 4 bureaux en Provence + consultations à distance ; le JAF et le tribunal correctionnel sont territorialement compétents — **pas de couverture nationale** |
| Honoraires | part fixe + complément au résultat | **permis** : idem ; **famille** : seulement une convention signée à l'avance, aucun honoraire de résultat annoncé |
| Spécialisation CNB citable | droit du dommage corporel | **famille** : droit de la famille, des personnes et de leur patrimoine (Me Raybaud) ; **permis** : aucune — expérience de 20+ ans seulement |

Chaque affirmation des trois fiches est désormais tracée jusqu'à sa source
dans les notes internes du fichier `.md` correspondant (section « Sources de
chaque affirmation »), hors document diffusé.

### 2.5 Choix d'outillage : rôle des outils sur le poste

- **Pas d'apprentissage par démonstration à l'écran** (décision Me Humbert,
  2026-08-13) : une génération dure ~10 min, trop long à montrer en direct.
  En compensation, le prompt v3 décrit chaque action au niveau
  « computer use » (référentiel d'interface écran par écran, critère de
  réussite et repli après chaque clic), et la première session de chaque
  chaîne est un **MODE PILOTE** : l'agent déroule UN épisode seul, consigne
  l'interface réellement rencontrée dans
  `podcasts/CALIBRATION-NOTEBOOKLM.md`, et l'épisode est écouté et validé
  par Me Humbert avant la production en série. Me Humbert enregistre son
  écran de son côté, en parallèle : cet enregistrement sert de référence
  visuelle et de dépannage, il ne conditionne pas le déroulé de l'agent.
- Pour **agir** (cliquer, coller, télécharger), il faut le pilotage de
  navigateur **sur votre poste** (extension Claude pour Chrome, ou le
  pilotage d'ordinateur de Cowork). Gros avantage : votre session Google y
  est déjà connectée — pas de login/2FA à automatiser (ce que les conditions
  Google interdisent de contourner ; à cadence humaine sur votre propre
  compte, on reste dans l'usage toléré, sans jamais forcer un CAPTCHA).
- La session Claude Code distante (ce dépôt) ne peut PAS piloter NotebookLM :
  elle n'a pas votre session Google. Son rôle : préparer et archiver (plan,
  prompt, CSV, fiches, tracker).
- **Plan B à garder en réserve** (si la calibration révèle une UI trop
  instable ou des quotas trop serrés) : générer le **script** du débat avec
  Claude (contrôle mot à mot du CTA et de la déonto, durée exacte) puis le
  faire lire par une **TTS multi-locuteurs** (API Gemini ou Voicebox).
  100 % scriptable, 24 épisodes en un lot sans surveillance, coût faible ;
  contrepartie : dialogue un peu moins « naturel » que NotebookLM.

---

## 3. Architecture cible

### 3.1 Répartition des rôles

| Où | Quoi |
|---|---|
| **Poste de Me Humbert** (Claude + navigateur connecté) | Export GSC (Phase 1), pilotage NotebookLM (Phases 2–3), post-traitement audio local (ffmpeg), dossier de travail `~/LEXVOX-PODCASTS/` |
| **Ce dépôt** (atelier) | Plan, prompt maître, fiches cabinet (Markdown → PDF/DOCX), CSV d'état commité après chaque session, `podcasts/PODCAST-TRACKER.md`, journal des incidents |
| **Plateformes** | Hébergeur RSS + intégration sur les pages articles (Phase 4) |

### 3.2 Flux — pipeline glissant

Une génération dure **~10 min** et continue en arrière-plan quand on quitte
le notebook. La boucle maintient donc **5 générations en vol** : on lance
tant qu'il reste de la place et du quota, on récolte dès qu'un épisode est
mûr. Aucune attente passive devant une barre de progression.

```
GSC (une fois) ──► CSV unique (colonne chaine) ──► session du jour (20 max)

    ┌── moins de 5 en vol ET quota du jour restant ? ──► LANCEMENT
    │      notebook neuf
    │        ► source 1 : URL article (repli : texte collé)
    │        ► source 2 : fiche-cabinet-<chaine>.pdf (téléversé, identique
    │                     pour tous les épisodes de la chaîne)
    │        ► Personnaliser : Débat + durée courte + texte < 500 car., FR
    │        ► Générer ► CSV status=generating + launched_at
    │
    └── sinon ──────────────────────────────────────► RÉCOLTE
           le plus ancien dont launched_at + 8 min est dépassé
             ► lecteur présent ? ► Télécharger ► ffmpeg (MP3, loudnorm,
               tags) ► QA durée ► CSV status=done

[fin de session] ► commit CSV + journal ► [Phase 4] hébergement, mesure
```

### 3.3 Le CSV d'état (UN seul fichier, seule source de vérité)

`podcasts/queue-podcast.csv`, colonnes :
`chaine,rank,site,url,slug,title,clicks_12m,impressions_12m,position_avg,status,launched_at,corps_file,intro_file,audio_file,generated_at,published_at,notes`

(`corps_file` = audio NotebookLM récolté, `intro_file` = intro (voix de l'avocat),
`audio_file` = MP3 final assemblé.)

- **Un seul CSV pour les trois chaînes** (arbitrage 2026-08-13) : la colonne
  `chaine` sépare les files, l'agent filtre dessus en début de session. Un
  seul fichier à committer, à sauvegarder et à consulter pour voir
  l'avancement global des 72 épisodes.
- Sélection GSC : **Performances › Résultats de recherche › 12 derniers mois ›
  dimension Pages**, export, puis filtre éditorial : articles uniquement
  (exclure accueil, pages piliers/landing, contact, catégories), fusion des
  propriétés si plusieurs sites, dédoublonnage, tri par clics → **top 24**
  par chaîne, ajoutés au CSV avec leur valeur de `chaine`.
- `status` : `todo → doing → generating → done` (corps NotebookLM récolté)
  `→ monte` (MP3 final assemblé et validé) `→ published` (Phase 4), plus
  `error` et `skipped`.
  `generating` + `launched_at` permettent le pipeline glissant et la
  reprise : une ligne restée `generating` d'une session interrompue est
  récoltée en priorité à la session suivante. `published_at` n'est rempli
  qu'en Phase 4. Un épisode `error` est repris à la session suivante après
  lecture de la note.

### 3.4 Cadence réelle

Abonnement NotebookLM **payant : 20 générations/jour** (confirmé
2026-08-13), toutes chaînes confondues. Avec le pipeline glissant, ces 20
épisodes tiennent en **~3 h 30 de session** (lancement ~3 min, génération
~10 min recouverte, récolte + post-traitement ~4 min).

| | Épisodes | Journées de production |
|---|---|---|
| Une chaîne | 24 | 2 (20 + 4) |
| Les trois chaînes | 72 | **4 journées** |

En pratique, prévoir 5 à 6 journées avec le pilote de chaque chaîne et la
marge d'erreurs. Le facteur limitant n'est plus le quota mais la QA humaine
et la Phase 4 (mise en ligne).

---

## 4. Plan d'action phasé

| Phase | Contenu | Qui | Livrable |
|---|---|---|---|
| **0. Cadrage** | ✅ **fait le 2026-08-13** pour : déontologie (§2.4), fiche victimes, PDF comme source, CSV unique, quota 20/j. **Reste** : sites GSC famille/permis, fiches famille/permis à compléter, canal de distribution | Me Humbert + Claude | Fiche victimes figée (`.md` + `.pdf` + `.docx`) |
| **1. Sélection** (1 fois/chaîne, ~30 min) | Sur votre poste (Claude in Chrome) : GSC › Performances › 12 mois › Pages › export ; fusion/filtre/tri ; top 24 ajoutés au CSV avec leur `chaine` | Claude in Chrome (vous en survol) | `podcasts/queue-podcast.csv` rempli et commité |
| **2. Pilote autonome** (1 épisode) | L'agent computer use déroule seul UN épisode complet (MODE PILOTE du prompt v3), consigne l'interface réelle dans `podcasts/CALIBRATION-NOTEBOOKLM.md` ; puis **écoute et validation du pilote par vous** (ton, CTA, exactitude) — remplace la démonstration à l'écran, abandonnée (génération ~10 min) | Claude in Chrome, puis Me Humbert (écoute) | Carnet de calibration rempli ; épisode pilote validé |
| **3. Production** (~2 journées/chaîne) | Claude in Chrome déroule `PROMPT-PODCAST-NOTEBOOKLM.md` en pipeline glissant, 20 générations/jour ; post-traitement ffmpeg ; QA ; CSV mis à jour et commité en fin de session | Claude (vous en survol) | 24 fichiers MP3 normalisés + CSV `done` |
| **3 bis. Intro + montage** (en parallèle de la production) | Phase A : `tools/voix_script.py` rend le texte, Voicebox le fait lire par la voix clonée de l'avocat, fichier nommé au slug. Phase B : `tools/podcast_montage.py` normalise, assemble intro → débat, encode en MP3 et passe les 14 contrôles | Me Humbert (voix) + Claude | `mp3/podcast-<chaine>-<NN>-<slug>.mp3` validés |
| **4. Publication & mesure** | Hébergeur RSS (Spotify for Creators gratuit, ou Ausha, français) → Spotify/Apple/Deezer/YouTube ; intégration `<audio>` + transcription + JSON-LD `AudioObject` sur les pages articles **WordPress** ; pour `lexvox-victime.com` (Sanity) l'intégration = évolution du frontend Next.js, **sur demande expresse uniquement** (règle CLAUDE.md) — en attendant, plateformes seulement ; liens UTM ; revue mensuelle des écoutes dans `podcasts/PODCAST-TRACKER.md` | Claude + webmaster | Épisodes en ligne + tracker |
| **5. Déclinaison** | Rejouer Phases 1→4 pour Famille puis Permis avec leurs variables (fiches, CTA, sites) | idem | 3 chaînes actives |

---

## 5. Décisions

### ✅ Arbitrées le 2026-08-13

| Sujet | Décision |
|---|---|
| Fiche cabinet | Document dédié, **téléversé en PDF** comme seconde source de chaque notebook (`.docx` fourni pour relecture dans Google Docs / Word) |
| Personnalisation | **< 500 caractères** — textes figés à 443/448/444 selon la chaîne |
| File de production | **Un seul CSV** pour les trois chaînes (`podcasts/queue-podcast.csv`, colonne `chaine`) |
| Quota NotebookLM | Abonnement **payant : 20 générations/jour** |
| Déontologie | Corrections §2.4 adoptées : variante factuelle pour l'IA, honoraires part fixe + résultat, aucune promesse de résultat, spécialisation CNB dommage corporel seule |
| Calibration | Pas de démonstration filmée ; **pilote autonome** + carnet de calibration. Me Humbert enregistre son écran de son côté, en parallèle |

| Fiches famille et permis | **Rédigées le 2026-08-13** à partir des pages publiques de `lexvox-divorce.com` et `lexvox-permis.com`, chaque affirmation tracée jusqu'à sa source ; PDF et DOCX générés |
| Sites sources famille / permis | `lexvox-divorce.com` et `lexvox-permis.com` (établis par les liens inter-sites du cabinet) |

### ⏳ Restant à trancher (bloquantes avant Phase 1)

1. **Périmètre Search Console de la chaîne Victimes** : les 3 propriétés
   (`medical`, `victime-accident`, `lexvox-victime.com`), ou
   `medical.lexvox-avocat.fr` seul pour démarrer ?
2. **Relecture des fiches famille et permis** — en particulier par
   Me Raybaud pour la fiche famille, dont elle est la signataire.
3. **Montants à l'oral** : les deux fiches disent aujourd'hui « un tarif
   fixe, annoncé lors de la prise de rendez-vous » plutôt que « 80 € TTC »
   (et « une part fixe » plutôt que « 700 € HT »). Formulation durable, qui
   évite qu'une révision tarifaire rende 48 épisodes faux. Basculer sur les
   montants explicites si vous préférez le concret.
4. **Canal de distribution** : hébergeur RSS retenu + ordre des plateformes
   (variable `PLATEFORME_DIFFUSION`, aujourd'hui `[À DÉFINIR]` — aucun envoi
   n'est tenté tant qu'elle n'est pas renseignée).
5. **Outro dans votre voix ?** Le CTA final est aujourd'hui prononcé par
   NotebookLM, donc soumis à sa bonne volonté. Le dire vous-même en outro
   Voicebox le rend certain au mot près et plus crédible ; l'outil accepte
   déjà `--outro`. Oui/non.
6. **Débit du MP3** : 192 kb/s comme vous l'avez spécifié (défaut retenu), ou
   128 kb/s — standard podcast en mono, sans différence audible sur de la
   voix, fichier un tiers plus léger.
7. **Plan B TTS** : accord de principe pour basculer si le pilote révèle une
   automatisation NotebookLM trop fragile.

---

*Créé le 2026-08-13 (branche `claude/podcast-automation-plan-5m6b59`). Les
fichiers audio ne sont jamais commités dans ce dépôt (`.gitignore`).*
