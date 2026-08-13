# PROMPT MONTAGE & DIFFUSION v2 — intro ElevenLabs + corps NotebookLM → MP3 diffusable

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
   ci-dessous, avec `tools/intro_script.py` qui rend le texte de chaque
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

### Une proposition qui vous appartient : l'outro

Le CTA — le moment qui transforme un auditeur en client — est aujourd'hui
prononcé par NotebookLM, donc soumis à sa bonne volonté. Le dire **dans votre
vraie voix**, en outro ElevenLabs, le rend certain au mot près et plus
crédible. Le script accepte déjà `--outro`, l'ordre devenant
intro → corps → outro (l'intro reste première, votre règle est respectée).
Décision à prendre : oui/non.

---

## 1. Les deux animateurs — figés pour les trois chaînes

| Rôle | Prénom | Fonction dans le débat |
|---|---|---|
| Voix féminine | **Élise** | la juriste pédagogue : explique le droit |
| Voix masculine | **Thomas** | le journaliste curieux : pose les questions de l'auditeur |

Choisis pour être clairement genrés à l'oreille, faciles à prononcer par une
synthèse vocale, et sans collision avec l'existant du cabinet : pas de
Patrice ni de Cédrine (les avocats), pas de Juliette (l'assistante virtuelle
de `lexvox-divorce.com`), pas d'Antoine (la rue du bureau de Marignane, lue
dans les adresses).

Le choix d'attribuer l'expertise juridique à la voix féminine et les
questions à la voix masculine est délibéré : il évite le cliché de l'expert
masculin qui explique à l'interlocutrice.

Les prénoms sont déclarés à **trois endroits**, qui doivent rester cohérents :
1. le texte de personnalisation NotebookLM (`PROMPT-PODCAST-NOTEBOOKLM.md`,
   section TEXTES PAR CHAÎNE) — c'est lui qui pilote réellement les voix ;
2. la fiche cabinet PDF, section « Les deux voix de l'émission » ;
3. l'intro ElevenLabs, qui les présente nommément à l'auditeur.

⚠️ **À vérifier au pilote :** NotebookLM ne respecte pas toujours les
prénoms imposés. Si l'épisode pilote ne les emploie pas, ne pas diffuser une
intro qui annonce « Élise et Thomas » alors que le débat ne les nomme jamais —
soit on renforce la consigne, soit on retire les prénoms de l'intro.

---

## 2. Phase A — Fabriquer l'intro ElevenLabs

Pour chaque épisode, **avant** le montage :

```bash
# 1. rendre le texte (contrôle automatique de la mention de transparence)
python3 tools/intro_script.py --chaine victimes --slug <slug> \
    --sujet "la contre-visite médicale" \
    --sortie ~/LEXVOX-PODCASTS/victimes/intro/intro-victimes-01-<slug>.txt
```

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
`tools/intro_script.py` refuse de rendre un script d'où la mention aurait
disparu. Raison : deux voix artificielles qui discutent de droit, dont l'une
présentée comme « juriste », peuvent laisser croire à l'auditeur qu'il écoute
des avocats du cabinet. Votre voix réelle qui présente nommément deux voix
synthétiques lève l'ambiguïté d'emblée — c'est cohérent avec la section
« Transparence éditoriale et intelligence artificielle » de vos mentions
légales, et c'est ce qui rend l'ensemble du dispositif défendable.

---

## 3. Phase B — Montage, contrôle, compte rendu

```bash
python3 tools/podcast_montage.py --chaine victimes --slug <slug>
# options : --debit 128 | --canaux stereo | --pause 0 | --outro <fichier>
#           --json rapport.json | --dry-run
```

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
| 3 | ffmpeg ou ffprobe absent du poste |
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
        ├── Phase A  intro_script.py ──► ElevenLabs (voix du cabinet)
        │                                   └► intro/intro-<chaine>-<NN>-<slug>.mp3
        │
        ├── NotebookLM (pipeline glissant, 20/jour) ──► brut/<slug>.<ext>
        │
        ├── Phase B  podcast_montage.py ──► mp3/podcast-<chaine>-<NN>-<slug>.mp3
        │                                    + 14 contrôles + compte rendu
        │
        └── Phase C  plateforme [À DÉFINIR] ──► publication
```

Statuts du CSV : `todo → doing → generating → done` (corps NotebookLM
récolté) `→ monte` (MP3 final validé) `→ published` (Phase C).

---

## 6. État de validation de l'outillage

| Élément | État |
|---|---|
| `tools/intro_script.py` | ✅ testé (8/8 vérifications, `--self-test`) |
| `tools/podcast_montage.py` — logique hors ffmpeg | ✅ testée (11/11, `--self-test`) : nommage, appariement CSV, détection de sources concurrentes, déclenchement des contrôles |
| `tools/podcast_montage.py` — chaîne ffmpeg réelle | ⚠️ **non exécutée** : ffmpeg est absent de l'environnement d'atelier et n'y est pas installable. À valider sur votre poste lors du premier épisode pilote, avec `--garder-travail` pour inspecter les fichiers intermédiaires |

Le pilote de la chaîne victimes est donc aussi le test grandeur nature du
montage : prévoir d'écouter le raccord intro → débat, et de vérifier le
compte rendu ligne à ligne avant d'enchaîner en série.
