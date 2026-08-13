# PLAN PODCASTS LEXVOX — 2026-08

Automatisation de **trois chaînes de podcasts** générés avec NotebookLM à
partir des meilleurs articles (mesurés dans Google Search Console) des sites
du cabinet. Ce document contient l'analyse critique du prompt initial (§2),
l'architecture cible (§3), le plan d'action phasé (§4) et les décisions à
valider par Me Humbert (§5).

Fichiers liés :
- `PROMPT-PODCAST-NOTEBOOKLM.md` — le prompt maître réécrit (v2), à utiliser
  dans une session Claude **sur le poste de Me Humbert** (voir §3.1).
- `podcasts/queue-podcast-TEMPLATE.csv` — gabarit du fichier d'état (généré
  une seule fois par chaîne depuis Search Console).
- `podcasts/fiche-cabinet-victimes.md` / `-famille.md` / `-permis.md` — la
  « fiche cabinet » injectée comme **seconde source** dans chaque notebook
  (présentation + conclusion/CTA, textes verrouillés déontologiquement).

---

## 1. Les trois chaînes

| Chaîne | Public | Sites sources (propriétés GSC) | Nom suggéré (à valider) |
|---|---|---|---|
| **Victimes** | victimes de dommage corporel / erreur médicale | `medical.lexvox-avocat.fr` + `victime-accident.lexvox-avocat.fr` + `lexvox-victime.com` (ou `medical` seul pour démarrer, comme le prompt initial) | « Victimes : vos droits » |
| **Famille** | personnes en instance de divorce, garde, pension | ⚠️ à confirmer (`lexvox-divorce.com` ?) | « Divorce & famille : parlons-en » |
| **Permis** | conducteurs (suspension, annulation, alcool/stupéfiants) | ⚠️ à confirmer (pages/landing permis du cabinet) | « Permis en danger » |

Chaque chaîne = 24 épisodes (les 24 meilleurs articles GSC), un notebook
NotebookLM par article, un épisode < 5 min par notebook. Total : 72 épisodes.

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
   La règle « sources exclusives » devient alors cohérente et tenable.
2. **Prompt mono-article à trous, sans état.** `[INSÉRER L'URL]` = une session
   manuelle par article, aucune trace de ce qui est fait/raté. Impossible de
   tenir 24 épisodes × 3 chaînes. **Correction v2 :** boucle pilotée par un
   **CSV d'état** (généré une fois depuis GSC, cf. §3.3) : l'agent prend la
   première ligne `todo`, la traite, met à jour la ligne, passe à la suivante.
3. **Le champ « Personnaliser » de NotebookLM est limité** (~500 caractères
   constatés ; à re-vérifier en calibration). Le texte de personnalisation du
   prompt initial fait ~2 300 caractères : il serait **tronqué silencieusement**.
   **Correction v2 :** personnalisation courte (< 450 caractères) + tout le
   contenu long (biographie, CTA mot à mot) déplacé dans la fiche cabinet
   (source n° 2), que les hôtes peuvent citer intégralement.
4. **Quotas ignorés.** NotebookLM limite les générations audio (ordre de
   grandeur : ~3/jour en gratuit, ~20/jour avec l'abonnement payant — chiffres
   à confirmer en calibration, Google les fait évoluer). Lancer 24 générations
   d'affilée échouera. **Correction v2 :** production par **lots de 3 à 5
   épisodes/session**, arrêt propre à la première erreur de quota, reprise le
   lendemain grâce au CSV.
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

### 2.4 Risques déontologiques (RIN, loi n° 71-1130) — à arbitrer AVANT production

Un podcast diffusé en masse est de la **publicité personnelle** (RIN art.
10.2 : sincère et véridique, sans mention comparative). Trois points :

12. **« 1er avocat certifié en Intelligence Artificielle en France »** : c'est
    un superlatif comparatif. Le site l'utilise déjà (choix assumé du
    cabinet), mais le répéter oralement dans 72 épisodes sur les plateformes
    d'écoute augmente l'exposition au risque. Les fiches cabinet proposent la
    variante factuelle « avocat certifié en intelligence artificielle,
    créateur d'outils d'évaluation des préjudices » ; **si Me Humbert souhaite
    conserver le superlatif, décision expresse à noter en §5**.
13. **Honoraires.** « un pourcentage sur les sommes obtenues » seul décrit un
    pacte de quota litis prohibé (art. 10, loi 71-1130). La formule déjà
    validée sur le site est reprise mot à mot dans les fiches : *convention
    d'honoraires transparente avec une part fixe et un complément au
    résultat*. Aucune autre formulation ne doit sortir dans l'audio.
14. **Promesse de résultat.** « obtenir une réparation intégrale » promet un
    résultat. Les fiches disent : *« faire valoir vos droits à la réparation
    intégrale »*. De même, **ne mentionner que les titres réellement
    détenus** : la mention « Spécialiste CNB dommage corporel » figure sur le
    site ; l'ajout « et Responsabilité Médicale » comme spécialisation CNB est
    à confirmer sur le certificat (la spécialisation officielle voisine est
    « droit de la santé »). Et surtout : **ne pas recycler la fiche victimes
    dans les chaînes famille et permis** — chaque chaîne a sa fiche, limitée
    aux titres vérifiés pour ce domaine.

### 2.5 Choix d'outillage : ce que « filmer mon écran » permet (et ne permet pas)

- Le **partage d'écran** (Claude Desktop / Cowork) permet à Claude de **voir**
  votre écran, pas d'agir. Il sert à la **Phase 2 de calibration** : vous
  faites UN épisode à la main pendant que Claude relève les libellés exacts
  des boutons, la limite réelle du champ Personnaliser, le format du fichier
  téléchargé et les temps réels — puis fige le prompt v2.
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
  faire lire par une **TTS multi-locuteurs** (API Gemini ou ElevenLabs).
  100 % scriptable, 24 épisodes en un lot sans surveillance, coût faible ;
  contrepartie : dialogue un peu moins « naturel » que NotebookLM.

---

## 3. Architecture cible

### 3.1 Répartition des rôles

| Où | Quoi |
|---|---|
| **Poste de Me Humbert** (Claude + navigateur connecté) | Export GSC (Phase 1), pilotage NotebookLM (Phases 2–3), post-traitement audio local (ffmpeg), dossier de travail `~/LEXVOX-PODCASTS/<chaine>/` |
| **Ce dépôt** (atelier) | Plan, prompt maître, fiches cabinet, CSV d'état commité après chaque lot, `podcasts/PODCAST-TRACKER.md`, journal des incidents |
| **Plateformes** | Hébergeur RSS + intégration sur les pages articles (Phase 4) |

### 3.2 Flux (par chaîne)

```
GSC (une fois) ──► CSV top 24 ──► [boucle par épisode]
   notebook neuf ► source 1 : URL article (repli : texte collé)
                 ► source 2 : fiche cabinet (texte collé)
                 ► Personnaliser (texte court) + durée « courte » + langue FR
                 ► Générer ► attendre ► Télécharger
   post-traitement local : renommer, MP3, loudnorm, tags
   QA (durée, langue, CTA) ► CSV mis à jour ► épisode suivant
[fin de lot] ► commit CSV + tracker ► [Phase 4] hébergement, intégration, mesure
```

### 3.3 Le CSV d'état (généré UNE fois par chaîne, puis seule source de vérité)

Colonnes (gabarit dans `podcasts/queue-podcast-TEMPLATE.csv`) :
`rank,site,url,slug,title,clicks_12m,impressions_12m,position_avg,status,audio_file,generated_at,published_at,notes`

- Sélection GSC : **Performances › Résultats de recherche › 12 derniers mois ›
  dimension Pages**, export, puis filtre éditorial : articles uniquement
  (exclure accueil, pages piliers/landing, contact, catégories), fusion des
  propriétés si plusieurs sites, dédoublonnage, tri par clics → **top 24**.
- `status` : `todo → doing → done` (+ `error`, `skipped`). `published_at`
  n'est rempli qu'en Phase 4. Un épisode `error` est repris au lot suivant
  après lecture de la note.

### 3.4 Cadence réaliste

Lots de 3–5 épisodes/session (quota + surveillance légère) → une chaîne de
24 épisodes = **5 à 8 sessions**, soit ~2 semaines par chaîne en rythme
tranquille, ou les 3 chaînes en ~6 semaines. L'abonnement NotebookLM payant
(quota ~20/jour) est fortement conseillé pour tenir ce rythme.

---

## 4. Plan d'action phasé

| Phase | Contenu | Qui | Livrable |
|---|---|---|---|
| **0. Cadrage** (1 session) | Choix des sites famille/permis ; vérif accès GSC des propriétés ; abonnement NotebookLM ; **validation des 3 fiches cabinet** (déonto §2.4) ; choix distribution (§4-Phase 4) ; noms des chaînes | Me Humbert + Claude | Décisions du §5 arbitrées, fiches validées commitées |
| **1. Sélection** (1 fois/chaîne, ~30 min) | Partage d'écran : GSC › Performances › 12 mois › Pages › export ; fusion/filtre/tri ; top 24 | Claude (guide) + vous (clics) ou Claude in Chrome | `podcasts/<chaine>/queue-podcast.csv` commité |
| **2. Calibration** (1 épisode pilote) | Vous faites 1 épisode à la main en partage d'écran ; Claude relève libellés exacts, limite du champ, durée réelle, format téléchargé ; ajustement du prompt v2 ; **écoute et validation du pilote par vous** (ton, CTA, exactitude) | Me Humbert + Claude | Prompt v2 figé ; épisode pilote validé |
| **3. Production** (5–8 sessions/chaîne) | Claude in Chrome déroule `PROMPT-PODCAST-NOTEBOOKLM.md` par lots de 3–5 ; post-traitement ffmpeg ; QA ; CSV mis à jour et commité en fin de lot | Claude (vous en survol) | 24 fichiers MP3 normalisés + CSV `done` |
| **4. Publication & mesure** | Hébergeur RSS (Spotify for Creators gratuit, ou Ausha, français) → Spotify/Apple/Deezer/YouTube ; intégration `<audio>` + transcription + JSON-LD `AudioObject` sur les pages articles **WordPress** ; pour `lexvox-victime.com` (Sanity) l'intégration = évolution du frontend Next.js, **sur demande expresse uniquement** (règle CLAUDE.md) — en attendant, plateformes seulement ; liens UTM ; revue mensuelle des écoutes dans `podcasts/PODCAST-TRACKER.md` | Claude + webmaster | Épisodes en ligne + tracker |
| **5. Déclinaison** | Rejouer Phases 1→4 pour Famille puis Permis avec leurs variables (fiches, CTA, sites) | idem | 3 chaînes actives |

---

## 5. Décisions à valider par Me Humbert (bloquantes avant Phase 1)

1. **Sites sources** de la chaîne Victimes (les 3 propriétés, ou `medical`
   seul pour démarrer ?) ; propriétés GSC exactes pour **Famille** et **Permis**.
2. **Formulation IA** dans l'audio : variante factuelle (recommandée, déjà
   dans les fiches) ou superlatif « 1er avocat certifié IA de France »
   (décision expresse à tracer ici).
3. **Certificats de spécialisation exacts** à citer (dommage corporel : oui ;
   « responsabilité médicale »/« droit de la santé » : à confirmer sur le
   certificat CNB) — et titres citables pour famille/permis.
4. **Abonnement NotebookLM** payant : oui/non.
5. **Canal de distribution** : hébergeur RSS retenu + ordre des plateformes.
6. **Plan B TTS** : accord de principe pour basculer si la calibration révèle
   une automatisation NotebookLM trop fragile.

---

*Créé le 2026-08-13 (branche `claude/podcast-automation-plan-5m6b59`). Les
fichiers audio ne sont jamais commités dans ce dépôt (`.gitignore`).*
