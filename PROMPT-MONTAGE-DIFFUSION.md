# PROMPT MONTAGE & DIFFUSION v3 — intro + débat + outro → MP3 diffusable

> Réécriture du prompt « Production, contrôle et diffusion automatisée d'un
> épisode de podcast » (analyse critique en §0). Il s'exécute **sur le poste
> de Me Humbert**, après la récolte NotebookLM (`PROMPT-PODCAST-NOTEBOOKLM.md`).
>
> Changement principal : le traitement audio n'est plus décrit en prose pour
> qu'un agent recompose des commandes ffmpeg à chaque épisode — il est
> **exécuté par `tools/podcast_montage.py`**, qui applique la chaîne complète
> et rend les quatorze contrôles sous forme d'assertions. Un agent qui écrit
> ses propres lignes de commande 72 fois finit par en écrire une de travers ;
> un script testé produit le même résultat à chaque fois.

---

## 0. Analyse critique du prompt initial

### Ce qui est juste et conservé

L'ordre imposé intro → corps, la liste des contrôles qualité, le traitement
de la plateforme comme variable non encore définie, l'interdiction de publier
sur une plateforme choisie d'initiative, le refus d'assembler des fichiers
dont la correspondance est incertaine, et le compte rendu structuré avec ses
trois statuts : tout cela est repris tel quel.

### Les six corrections

1. **Une étape manquait en amont.** Le prompt commence à « deux fichiers
   existent ». Or l'intro ElevenLabs n'existe pas : il faut l'écrire, la faire
   lire par la voix clonée, puis la nommer correctement. C'est la **phase A**
   ci-dessous, avec `tools/voix_script.py` qui rend le texte de chaque
   épisode depuis un gabarit.
2. **Appariement par date = piège.** « Sélectionner les fichiers les plus
   récemment générés » casse dès qu'une génération est relancée ou qu'un
   téléchargement traîne. L'appariement se fait par **slug**, lu dans le CSV :
   `intro-<chaine>-<NN>-<slug>.mp3` et `brut/<slug>.*`. Deux candidats de
   noms différents → arrêt, jamais de choix implicite.
3. **Normaliser après concaténation ne corrige pas un déséquilibre interne.**
   Une passe loudnorm sur le fichier assemblé décale l'ensemble sans rien
   régler entre l'intro et le corps. Chaque source est donc normalisée
   **séparément en deux passes** à −16 LUFS, puis assemblée, puis mesurée ;
   une correction unique s'applique si l'écart final dépasse 0,5 LU.
4. **192 kb/s CBR en mono est au-delà du transparent** pour de la voix : le
   standard podcast est 128 kb/s mono, sans différence audible, pour un
   fichier 33 % plus léger — ce qui sert votre exigence « rester léger et
   universel ». Le script garde **192 par défaut, comme demandé**, et expose
   `--debit 128` : c'est votre arbitrage, pas le mien.
5. **« Aucun silence artificiel » pris au pied de la lettre colle les deux
   fichiers.** Une respiration de 400 ms entre l'intro et le débat n'est pas
   du remplissage, c'est ce qui rend la transition naturelle. Réglable par
   `--pause`, `0` pour coller franchement.
6. **ID3 v2.3 ne s'obtient pas par défaut** : ffmpeg écrit de l'ID3v2.4. Le
   script force `-id3v2_version 3` et ajoute un ID3v1 pour les vieux
   lecteurs. Sans ces options, la consigne §7 du prompt initial est
   silencieusement ignorée.

### L'outro — ✅ adopté le 2026-08-13

Le CTA était prononcé par NotebookLM, donc soumis à sa bonne volonté. Il est
désormais dit **dans la vraie voix de l'avocat**, en outro ElevenLabs :
certain au mot près, et plus crédible. L'ordre devient **intro → corps →
outro** ; l'intro reste première, la règle initiale est respectée.

Trois conséquences, dont la première est la plus importante :

1. **Le débat ne récite plus aucune conclusion commerciale.** Sinon le CTA
   serait dit deux fois, une fois mal par le modèle et une fois bien par
   vous. La fiche cabinet ne contient donc plus le texte du CTA, ni le
   numéro de téléphone, ni l'adresse du site : elle dit désormais aux hôtes
   de conclure sur le fond et de s'arrêter là. La personnalisation le répète.
2. **Trente secondes rendues au contenu.** Le débat n'a plus à consacrer ses
   dernières secondes au message commercial : à budget égal (moins de cinq
   minutes), l'auditeur reçoit plus de droit et moins de publicité.
3. **Une seule prise de voix par chaîne.** L'outro ne dépend pas de
   l'article : trois enregistrements ElevenLabs couvrent les 72 épisodes,
   contre 72 pour les intros. Le montage cherche d'abord une outro propre à
   l'épisode, puis se rabat sur celle de la chaîne.

**L'outro est désormais obligatoire.** Le CTA n'existant plus nulle part
ailleurs, un épisode monté sans elle n'aurait aucun appel à l'action : le
montage s'arrête si elle est introuvable, à moins de passer `--sans-outro`
en connaissance de cause.

---

## 1. Les deux animateurs — figés pour les trois chaînes

| Rôle | Prénom | Fonction dans le débat |
|---|---|---|
| Voix féminine | **Nathalie** | la juriste pédagogue : explique le droit |
| Voix masculine | **Nicolas** | le journaliste curieux : pose les questions de l'auditeur |

### Pourquoi ces deux prénoms (données INSEE, recherche du 2026-08-13)

Le critère n'est pas le prénom le plus donné aujourd'hui, mais celui qui
sonne comme un **contemporain de l'auditeur**. Le public visé — victimes
d'accident, personnes qui divorcent, conducteurs — a majoritairement entre 30
et 65 ans, donc est né entre 1961 et 1996.

- **Nathalie** : prénom féminin n° 1 en France **sept années consécutives**
  (1965-1971), 382 978 porteuses, **6ᵉ** de tout le classement féminin depuis
  1900. Aucun autre prénom féminin encore perçu comme « adulte moderne »
  n'atteint cette diffusion.
- **Nicolas** : prénom masculin n° 1 en **1980, 1981, 1982 et 1995**,
  405 952 porteurs, **18ᵉ** de tout le classement masculin depuis 1900 — le
  seul prénom masculin récent du top 20 tous temps confondus. Ce double pic,
  à quinze ans d'écart, lui donne une reconnaissance qui traverse les
  générations.

Écartés, et pourquoi — la vérification a été faite sur votre propre corpus :

| Prénom | Statut | Motif d'exclusion |
|---|---|---|
| **Marie** | n° 1 absolu (2 231 347) | collision phonétique avec « mariage » et « se marier », omniprésents sur la chaîne famille ; et avec Les Saintes-Maries-de-la-Mer dans vos zones d'intervention |
| **Jean** | n° 1 absolu (1 911 457) | collision avec **Jean-Pierre Dintilhac**, cité dans presque chaque épisode de la chaîne victimes ; et sonne comme un homme de 80 ans (pic 1900-1957) |
| Louise, Jade / Gabriel, Raphaël | n° 1 des naissances 2024 | ce sont des prénoms d'enfants : un auditeur de 45 ans n'y entend pas un pair |
| Julien | n° 1 de 1983 à 1988 | le concurrent `avocatjullien.fr` |
| Céline | n° 1 de 1978 à 1981 | trop proche de **Cédrine** Raybaud |
| Julie | n° 1 en 1987 | **Juliette**, l'assistante virtuelle de `lexvox-divorce.com` |
| Kévin | n° 1 de 1989 à 1994 | stéréotype social défavorable bien documenté en France — inadapté à un podcast juridique |
| Antoine | — | la rue du bureau de Marignane, lue dans les adresses |

Une enquête Flashs/IRSS de février 2025 (2 000 personnes) conforte ce choix :
le premier critère des Français au moment de choisir un prénom est **« une
prononciation simple et claire » (33 %)**, et **27 % reconnaissent avoir déjà
jugé un inconnu sur son prénom**. Nathalie et Nicolas ne se prêtent à aucune
hésitation de prononciation, ni à aucune ambiguïté de genre — ce qui compte
doublement pour une synthèse vocale.

Le choix d'attribuer l'expertise juridique à la voix féminine et les
questions à la voix masculine est délibéré : il évite le cliché de l'expert
masculin qui explique à l'interlocutrice.

### Deux déclarations distinctes, à ne pas confondre

Les prénoms se déclarent à deux endroits qui ne jouent pas le même rôle. Les
confondre, c'est risquer une intro qui annonce Nathalie et Nicolas sur un
débat où NotebookLM aura choisi d'autres voix.

**1. Côté ElevenLabs — l'avocat les présente comme les animateurs.**
L'introduction, dite dans la voix réelle de l'avocat, dit textuellement :
*« Cette émission est animée par Nathalie et Nicolas. Nathalie, la juriste,
vous explique le droit ; Nicolas, le journaliste, pose les questions que vous
vous posez. Ce sont deux voix de synthèse… »*
`tools/voix_script.py` **refuse de rendre un script** où l'un des deux
prénoms manquerait, ou d'où la mention « voix de synthèse » aurait disparu.

**2. Côté NotebookLM — la configuration impose le genre de chaque voix.**
Nommer les animateurs ne suffit pas : sans indication de genre, rien ne
garantit que Nathalie reçoive la voix féminine. Le texte de personnalisation
l'impose explicitement :
*« Podcast animé par deux personnes : Nathalie, une FEMME, juriste pédagogue
(voix féminine), et Nicolas, un HOMME, journaliste curieux (voix
masculine). »*
La fiche cabinet PDF, seconde source du notebook, le répète dans sa section
« Les deux voix de l'émission » — une consigne présente dans la
personnalisation **et** dans une source a plus de chances d'être suivie.

⚠️ **À vérifier au pilote :** NotebookLM ne respecte pas toujours les
prénoms imposés. Si l'épisode pilote ne les emploie pas, ne pas diffuser une
intro qui annonce « Nathalie et Nicolas » alors que le débat ne les nomme jamais —
soit on renforce la consigne, soit on retire les prénoms de l'intro.

---

## 2. Phase A — Fabriquer les voix ElevenLabs

### A0 — L'outro : une fois par chaîne, avant tout le reste

```bash
python3 tools/voix_script.py --bloc outro --chaine victimes \
    --sortie ~/LEXVOX-PODCASTS/victimes/outro/outro-victimes.txt
```

Coller dans ElevenLabs (voix clonée), générer, écouter, enregistrer sous
`~/LEXVOX-PODCASTS/<chaine>/outro/outro-<chaine>.mp3`. **C'est tout** : ce
fichier sert les 24 épisodes de la chaîne. Trois enregistrements couvrent
donc l'ensemble du projet.

Une outro propre à un épisode reste possible et prime sur celle de la chaîne
— utile par exemple pour les épisodes de la chaîne famille traitant de
violences conjugales, qui ouvrent sur le 3919.

### A1 — L'intro : une par épisode

L'intro suit une structure imposée — c'est la marque de fabrique de la
série : **une question d'accroche** dont la réponse est l'article, puis le
**jingle verbal** identique à chaque épisode, puis le sujet, la présentation
des animateurs et la relance « La réponse, tout de suite ».

La question et le sujet se produisent en lisant l'article :
voir **`PROMPT-INTRO-ELEVENLABS.md`**, qui porte aussi les réglages de voix.

```bash
python3 tools/voix_script.py --chaine victimes --slug <slug> \
    --question "Votre assureur vous convoque à une contre-visite médicale. \
Avez-vous le droit de refuser d'y aller ?" \
    --sujet "la contre-visite médicale demandée par votre assureur" \
    --sortie ~/LEXVOX-PODCASTS/victimes/intro/intro-victimes-01-<slug>.txt
```

`voix_script.py` refuse un script qui ne commencerait pas par une question,
ou d'où le jingle, les prénoms ou la mention « voix de synthèse » auraient
disparu.

2. Coller ce texte dans ElevenLabs, **voix clonée du cabinet** (Me Humbert
   pour victimes et permis, Me Raybaud pour famille — c'est elle qui signe
   les articles de `lexvox-divorce.com`).
3. Générer, écouter, télécharger.
4. Enregistrer sous `~/LEXVOX-PODCASTS/<chaine>/intro/intro-<chaine>-<NN>-<slug>.mp3`
   — le nom doit contenir le slug, c'est lui qui garantit l'appariement.

**Durée cible : 25 à 35 secondes.** L'épisode complet, intro comprise, doit
rester sous cinq minutes : c'est pourquoi la consigne NotebookLM vise
strictement moins de cinq minutes pour le seul débat, et pourquoi le contrôle
de durée du montage tolère jusqu'à 5 min 30 pour le corps seul.

### A3 — Mention de transparence, non négociable

Chaque intro dit que les deux animateurs sont des **voix de synthèse**.
`tools/voix_script.py` refuse de rendre un script d'où la mention aurait
disparu. Raison : deux voix artificielles qui discutent de droit, dont l'une
présentée comme « juriste », peuvent laisser croire à l'auditeur qu'il écoute
des avocats du cabinet. Votre voix réelle qui présente nommément deux voix
synthétiques lève l'ambiguïté d'emblée — c'est cohérent avec la section
« Transparence éditoriale et intelligence artificielle » de vos mentions
légales, et c'est ce qui rend l'ensemble du dispositif défendable.

---

## 3. Phase B — Montage, contrôle, compte rendu

```bash
# ffmpeg installé sur le poste
python3 tools/podcast_montage.py --chaine victimes --slug <slug>

# ffmpeg derrière une API
python3 tools/podcast_montage.py --chaine victimes --slug <slug> \
    --moteur api --config podcasts/ffmpeg-api.json

# options : --debit 128 | --canaux stereo | --pause 0 | --outro <fichier>
#           --json rapport.json | --dry-run | --garder-travail
```

### Le moteur d'exécution est interchangeable

Toute la chaîne de traitement passe par une seule interface,
`Moteur.executer(arguments)` (`tools/ffmpeg_moteur.py`). Deux implémentations :
`MoteurLocal` appelle les binaires du poste, `MoteurAPI` délègue à un service
HTTP. **La logique de montage et les quatorze contrôles sont identiques dans
les deux cas** — seul le lieu d'exécution change.

**Contrat minimal exigé du service** (à vérifier avant de le retenir) :

| Exigence | Pourquoi elle est indispensable |
|---|---|
| 1. accepter une **ligne de commande ffmpeg arbitraire**, filtres compris (`loudnorm`, `alimiter`, `concat`, `anullsrc`, `filter_complex`) | un service limité à « convertir A en B » ne sait ni normaliser ni assembler |
| 2. accepter des fichiers en entrée et rendre le fichier produit | — |
| 3. **rendre le journal d'exécution** (flux d'erreur de ffmpeg) | `loudnorm` en deux passes lit dans ce journal les mesures de la 1re passe pour les injecter à la 2de |
| 4. rendre la **sortie standard** pour les commandes `ffprobe` | c'est là qu'arrive le JSON des caractéristiques, sans quoi 8 des 14 contrôles tombent |

⚠️ **Si le service ne rend pas le journal (point 3)**, la normalisation
retombe à une seule passe — précision de l'ordre de 1 LU au lieu de 0,1 — et
les contrôles 11 (loudness) et 12 (vrai pic) deviennent **invérifiables**.
L'outil le détecte via `journal_disponible` et **s'arrête** plutôt que de
produire un fichier dont la conformité serait invérifiée.

Configuration : copier `podcasts/ffmpeg-api.exemple.json` en
`podcasts/ffmpeg-api.json` (ignoré par git) et l'adapter. **La clé d'API n'y
figure jamais** : le fichier ne porte que le *nom* de la variable
d'environnement qui la contient (règle 5 du `CLAUDE.md`).

### Diagnostiquer un service AVANT de l'adopter

```bash
python3 tools/ffmpeg_moteur.py --diagnostic --moteur api \
    --config podcasts/ffmpeg-api.json
```

La commande fabrique un petit fichier audio de test (sans ffmpeg, en Python
pur), puis confronte le service aux quatre exigences et rend un verdict
ligne par ligne : sondage `ffprobe`, présence des mesures `loudnorm` dans le
journal, acceptation d'un filtre arbitraire, récupération du fichier produit.
Elle sort en erreur si le contrat n'est pas satisfait.

Il vaut mieux découvrir ainsi qu'un service ne rend pas les journaux, que
s'en apercevoir après 72 montages dont la conformité sonore n'aura jamais pu
être vérifiée.

Convention de lecture des arguments par `MoteurAPI` : les valeurs suivant
`-i` sont des entrées à téléverser, le dernier argument est le fichier à
récupérer — sauf `-` (passes de mesure, aucun fichier produit) et sauf pour
`ffprobe`, dont le dernier argument est au contraire une entrée.

Le script enchaîne, dans cet ordre :

| Étape | Ce qui est fait |
|---|---|
| Appariement | ligne CSV `(chaine, slug)` → titre, rang ; sources trouvées **par nom**, jamais par date ; deux candidats concurrents → arrêt |
| Sondage | `ffprobe` sur chaque source ; durée nulle ou fichier illisible → arrêt |
| Normalisation | `loudnorm` **deux passes** par source, −16 LUFS / −1,5 dBTP, vers WAV 44,1 kHz |
| Assemblage | `concat` avec respiration de 400 ms ; aucun chevauchement, aucune troncature |
| Encodage | limiteur `alimiter` à −1,5 dBTP, puis `libmp3lame` CBR, ID3v2.3 + ID3v1 |
| Correction | mesure du final ; si l'écart à −16 LUFS dépasse 0,5 LU, une seule reprise avec décalage de gain |
| Contrôles | les 14 vérifications, rendues avec leur valeur mesurée |
| Compte rendu | tableau lisible + JSON optionnel, et l'un des trois statuts |

Le fichier final s'appelle **`podcast-<chaine>-<NN>-<slug>.mp3`**. Votre
format demandé était `podcast-[numero]-[slug].mp3` ; la chaîne y est ajoutée
parce que les trois séries partagent la numérotation 01–24 et que les noms
entreraient en collision dans un même dossier ou un même flux.

### Codes de sortie

| Code | Signification |
|---|---|
| 0 | tous les contrôles passés — fichier prêt |
| 2 | traitement interrompu (source absente, illisible, appariement incertain) |
| 3 | panne de moteur : ffmpeg absent du poste, API injoignable ou mal configurée, clé absente de l'environnement, service ne rendant pas le journal |
| 4 | fichier produit mais **un contrôle a échoué** — ne pas publier |

---

## 4. Phase C — Diffusion

`PLATEFORME_DIFFUSION = [À DÉFINIR]`

Tant que cette variable n'est pas renseignée, le script **ne tente aucun
envoi** et conclut :

> Fichier final validé — publication en attente de configuration de la
> plateforme de diffusion.

Quand la plateforme sera choisie, l'envoi transmettra le MP3 et ses
métadonnées (titre, description, numéro d'épisode, date prévue, auteur,
éditeur), puis vérifiera l'acceptation, récupérera l'identifiant, l'URL
publique et le statut de publication. La mission n'est terminée qu'à cette
confirmation — jamais au seul motif que le MP3 existe. Aucune plateforme
n'est choisie d'initiative, aucune publication à une date non définie.

---

## 5. Où le montage s'insère dans le pipeline

```
Search Console ──► CSV unique
        │
        ├── Phase A0 voix_script.py --bloc outro ──► ElevenLabs
        │              └► outro/outro-<chaine>.mp3   (1 fois par chaine)
        │
        ├── Phase A1 voix_script.py ──► ElevenLabs (voix du cabinet)
        │              └► intro/intro-<chaine>-<NN>-<slug>.mp3  (par episode)
        │
        ├── NotebookLM (pipeline glissant, 20/jour) ──► brut/<slug>.<ext>
        │
        ├── Phase B  podcast_montage.py ──► mp3/podcast-<chaine>-<NN>-<slug>.mp3
        │              intro -> corps -> outro, + 14 contrôles + compte rendu
        │
        └── Phase C  plateforme [À DÉFINIR] ──► publication
```

Statuts du CSV : `todo → doing → generating → done` (corps NotebookLM
récolté) `→ monte` (MP3 final validé) `→ published` (Phase C).

---

## 6. État de validation de l'outillage

| Élément | État |
|---|---|
| `tools/voix_script.py` | ✅ testé (8/8 vérifications, `--self-test`) |
| `tools/podcast_montage.py` — logique hors ffmpeg | ✅ testée (11/11, `--self-test`) : nommage, appariement CSV, détection de sources concurrentes, déclenchement des contrôles |
| `tools/ffmpeg_moteur.py` — convention entrées/sorties | ✅ testée (10/10) : passes de mesure sans sortie, encodage, assemblage à trois entrées, cas `ffprobe`, refus d'une clé absente de l'environnement |
| `tools/podcast_montage.py` — chaîne ffmpeg réelle | ⚠️ **non exécutée** : ffmpeg est absent de l'environnement d'atelier et n'y est pas installable. À valider au premier épisode pilote, avec `--garder-travail` pour inspecter les fichiers intermédiaires |
| `MoteurAPI` — dialogue HTTP réel | ⚠️ **non exécuté** : le service n'est pas encore désigné. Le transport (téléversement multipart, soumission, sondage d'état, récupération) est écrit contre le contrat ci-dessus et sera à confronter au service retenu |

Le pilote de la chaîne victimes est donc aussi le test grandeur nature du
montage : prévoir d'écouter le raccord intro → débat, et de vérifier le
compte rendu ligne à ligne avant d'enchaîner en série.
