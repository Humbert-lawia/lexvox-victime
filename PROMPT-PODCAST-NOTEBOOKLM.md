# PROMPT PODCAST NOTEBOOKLM v2 — à copier dans une session Claude SUR LE POSTE de Me Humbert

> Remplace le prompt initial « MISSION : AUTOMATISATION NATIVE… » (analyse
> critique : `PLAN-PODCASTS-2026-08.md` §2). Une session Claude Code distante
> ne peut PAS exécuter ce prompt (pas de session Google) : il se lance dans
> **Claude sur le poste** (extension Claude pour Chrome, ou pilotage
> d'ordinateur Cowork), navigateur connecté au compte Google du cabinet.
>
> À PRÉPARER UNE FOIS AVANT LA PREMIÈRE SESSION :
> - Dossier de travail local : `~/LEXVOX-PODCASTS/<chaine>/` (chaine =
>   `victimes` | `famille` | `permis`) contenant :
>   - `queue-podcast.csv` (top 24 issu de Search Console — Phase 1 du plan) ;
>   - `fiche-cabinet.md` (copie de `podcasts/fiche-cabinet-<chaine>.md` du
>     dépôt, VERSION VALIDÉE par Me Humbert) ;
>   - sous-dossiers `brut/` (téléchargements) et `mp3/` (fichiers finaux).
> - `ffmpeg` installé sur le poste (post-traitement).
> - NotebookLM : langue de sortie réglée sur **français** (paramètres), et
>   abonnement payant si disponible (quota de générations audio).
> - Calibration faite (Phase 2 du plan) : les libellés d'interface entre
>   [crochets] ci-dessous ont été vérifiés à l'écran une fois.

---

```
Tu pilotes le navigateur de ce poste pour produire EN SÉRIE des épisodes de
podcast NotebookLM pour le cabinet LEXVOX AVOCATS (Me Patrice Humbert).

CHAÎNE DE CETTE SESSION : {victimes | famille | permis}
DOSSIER DE TRAVAIL : ~/LEXVOX-PODCASTS/<chaine>/
TAILLE DU LOT : 3 épisodes par défaut (5 maximum si le quota le permet).

RÈGLES ABSOLUES
- Textes verrouillés : tu n'improvises JAMAIS de mention sur les titres,
  spécialisations, honoraires ou résultats du cabinet. Seuls les textes de
  fiche-cabinet.md et le texte de personnalisation ci-dessous font foi.
- Tu ne contournes jamais une demande de connexion, de vérification ou un
  CAPTCHA : si la session Google est déconnectée, tu t'arrêtes et tu me
  préviens.
- Si un élément d'interface attendu est introuvable : capture d'écran,
  arrêt de l'épisode en cours, note dans le CSV — jamais de clics au hasard.
- Le CSV est l'unique source de vérité de l'avancement. Tu le mets à jour
  après CHAQUE épisode, pas en fin de lot.

════════ ÉTAPE 0 — PRÉ-VOL (une fois par session) ════════
a) Ouvre https://notebooklm.google.com/ ; vérifie que la session Google est
   active (sinon STOP).
b) Vérifie dans les paramètres que la langue de sortie audio est le français.
c) Lis queue-podcast.csv ; annonce-moi : nb d'épisodes done / todo / error,
   et les 3-5 slugs que tu vas traiter dans ce lot.
d) Vérifie que fiche-cabinet.md est présente et lis-la entièrement.

════════ BOUCLE PAR ÉPISODE (répéter jusqu'à fin de lot ou quota) ════════

ÉTAPE 1 — SÉLECTION
1. Prends la première ligne du CSV avec status=todo (ou error si sa note
   indique une cause corrigée). Passe status=doing.

ÉTAPE 2 — NOTEBOOK
1. Clique [+ Créer] / [Nouveau notebook].
2. Renomme le notebook : « PODCAST <chaine> — <slug> ».

ÉTAPE 3 — SOURCES (deux sources, toujours)
1. Source 1 (l'article) : [Ajouter une source] → [Site web / Lien], colle
   l'URL de la ligne CSV, valide. Attends la fin de l'ingestion.
   ▸ REPLI si l'ingestion échoue : ouvre l'URL dans un autre onglet, copie
     le texte intégral de l'article (sans menus ni pied de page), et
     ajoute-le via [Texte collé / Copier-coller du texte].
2. Source 2 (la fiche cabinet) : [Ajouter une source] → [Texte collé],
   colle l'intégralité de fiche-cabinet.md, valide.

ÉTAPE 4 — CONFIGURATION AUDIO
1. Sur [Résumé audio / Aperçu audio], clique [Personnaliser].
2. Si un sélecteur de durée existe, choisis l'option la plus COURTE.
3. Colle EXACTEMENT le texte de personnalisation de la chaîne (bloc
   « TEXTES PAR CHAÎNE » ci-dessous — il tient dans la limite du champ ;
   s'il est tronqué à l'écran, STOP et préviens-moi).
4. Lance [Générer].

ÉTAPE 5 — ATTENTE
- Attente passive jusqu'à 15 minutes, sans rafraîchir avant 5 minutes.
- Fin détectée : apparition du lecteur audio avec sa durée.
- Erreur de génération : attends 60 s, relance UNE fois. Second échec →
  status=error + note (message exact), épisode suivant.
- Message de quota atteint → status reste todo, note « quota », FIN DU LOT
  proprement (étape 8).

ÉTAPE 6 — TÉLÉCHARGEMENT
1. Menu ⋮ du lecteur → [Télécharger]. Ne renomme RIEN dans le navigateur.
2. Déplace le fichier téléchargé vers brut/.

ÉTAPE 7 — POST-TRAITEMENT + QA (terminal local)
1. Convertis et normalise :
   ffmpeg -i brut/<fichier> -af loudnorm=I=-16:TP=-1.5:LRA=11 -ar 44100
     -b:a 160k -metadata title="<title>" -metadata artist="LEXVOX Avocats"
     -metadata album="<nom de la chaîne>" mp3/podcast-<slug>.mp3
2. QA automatique : ffprobe → durée entre 2:00 et 5:30 ; sinon status=error
   + note « durée <x> », ne pas garder le MP3.
3. QA humaine : les 2 PREMIERS épisodes de la chaîne + 1 épisode sur 5
   ensuite sont à faire écouter à Me Humbert avant toute publication
   (français correct, CTA final présent et conforme, pas de droit inventé).
   Note « à écouter » dans le CSV pour ces épisodes.

ÉTAPE 8 — ÉTAT
1. CSV : status=done, audio_file=mp3/podcast-<slug>.mp3,
   generated_at=<date ISO>.
2. Ajoute une ligne au journal local journal.md : date, slug, durée,
   incidents éventuels, générations restantes estimées.
3. Épisode suivant, ou fin de lot : récapitule-moi le lot (fait/raté/quota)
   et rappelle-moi de committer le CSV + le journal dans le dépôt atelier.
```

---

## TEXTES PAR CHAÎNE

### Personnalisation — chaîne VICTIMES (à coller tel quel, ~430 caractères)

> Débat vif et accessible entre deux voix : un journaliste curieux et un
> juriste pédagogue. Appuyez-vous uniquement sur les deux sources : l'article
> (le fond juridique) et la fiche cabinet (le contexte et la conclusion).
> Vulgarisez chaque terme technique. Faites ressortir les enjeux de l'article
> et les pièges de sous-évaluation par les assureurs. Durée : moins de 5
> minutes. Terminez les 30 dernières secondes par la conclusion exacte donnée
> dans la fiche cabinet.

### Personnalisation — chaîne FAMILLE

> Identique, en remplaçant la phrase des pièges par : « Faites ressortir les
> enjeux concrets pour une personne qui traverse un divorce ou une séparation,
> et les erreurs classiques à éviter. »

### Personnalisation — chaîne PERMIS

> Identique, en remplaçant la phrase des pièges par : « Faites ressortir les
> délais à ne pas manquer et les recours possibles pour un conducteur qui
> risque de perdre son permis. »

### Fiches cabinet (source n° 2 de chaque notebook)

Textes complets, avec le CTA mot à mot, dans le dépôt :
- `podcasts/fiche-cabinet-victimes.md` (prête, à faire valider) ;
- `podcasts/fiche-cabinet-famille.md` (⚠️ à compléter/valider — Phase 0) ;
- `podcasts/fiche-cabinet-permis.md` (⚠️ à compléter/valider — Phase 0).

Toute modification de ces fiches passe par une validation expresse de
Me Humbert AVANT la session de production suivante (publicité personnelle :
RIN art. 10.2 — voir `PLAN-PODCASTS-2026-08.md` §2.4).
