# État du chantier PODCASTS — à lire en premier dans une nouvelle session

> Fiche de reprise. Elle dit **où en est le chantier**, **ce qui est prouvé**,
> **ce qui ne l'est pas** et **ce qui attend une décision de Me Humbert**.
> Dernière mise à jour : **2026-08-14**, branche `claude/podcast-automation-plan-5m6b59`.
>
> **Le pilote est monté pour de bon, sur le poste du cabinet, avec la vraie voix
> clonée et le vrai débat : 14/14 au vert** (cf. §5ter). Ce qui restait à prouver
> au §6 l'est, sauf le service ffmpeg distant.

---

## 1. Ce qu'on fabrique

Trois séries de podcasts, une par chaîne éditoriale du cabinet, sur le
modèle : **voix clonée de l'avocat** en introduction et en conclusion, **débat
NotebookLM** entre deux animateurs au milieu.

| Chaîne | Émission | Signataire imposé | État |
|---|---|---|---|
| `victimes` | **LEXVICTIME** — droit des victimes d'accident et d'erreur médicale | **Patrice Humbert** (dit « Imbert ») | ✅ **seule chaîne configurée** |
| `famille` | (à nommer) | **Cédrine Raybaud** | gabarits en place, texte **non validé** |
| `permis` | Permis en danger | variable → `--avocat` obligatoire | gabarits en place, texte **non validé** |

**Consigne de Me Humbert (2026-08-13)** : « on va configurer que Victimes dans
un 1er temps et si cela fonctionne on fera les configurations des autres
podcasts. » Ne pas retoucher famille/permis sans demande explicite.

---

## 2. L'intro en trois blocs — validée le 2026-08-13

C'est la décision structurante de la session. Après trois versions
successives (86 s → 78 s → 57 s), Me Humbert a demandé « une version ultra
optimisée de 30 secondes, en 3 blocs », puis a validé le résultat.

| # | Bloc | Segment | Durée | Refait par épisode ? |
|---|---|---|---|---|
| 1 | **Question du jour** — c'est le sujet ET l'article, posés en question | `01-question` | ~8 s | ✏️ **oui, le seul** |
| 2 | **Présentation** — émission, cabinet, avocat, confidence | `02-presentation` | ~14 s | 🔒 non — une seule prise |
| 3 | **Annonce du débat** — Nathalie et Nicolas, lancement | `03-final` | ~9 s | 🔒 non — une seule prise |

Texte exact (chaîne victimes), dans `podcasts/voix-avocat/SCRIPT-INTRO-victimes.md`
entre `<<<SCRIPT` et `SCRIPT>>>` :

```
{question}

LEXVICTIME, le podcast du cabinet LEXVOX AVOCATS. Maître Patrice Humbert,
spécialisé en dommage corporel. Une confidence : ce n'est pas le dossier le
plus grave qui est le mieux indemnisé, c'est le mieux défendu.

Nathalie et Nicolas en débattent, d'après mon article. Ils ne sont pas
avocats, ce sont les deux voix de l'émission. C'est parti.
```

**Total 463 caractères ≈ 31 s, dont 23 s enregistrées une seule fois** pour
les 24 épisodes de la chaîne.

### Ce qui a été retiré, et pourquoi (ne pas le réintroduire sans demande)

- **« Aujourd'hui, {sujet}, d'après mon article "{titre}" »** — supprimé :
  faisait doublon, la question du jour *est* le sujet et l'article. L'article
  survit en incise du bloc 3 (« d'après mon article »).
- **« Bienvenue dans… »**, **« avocat au Barreau d'Aix-en-Provence »**,
  **« Depuis plus de vingt ans, je consacre mon activité à… »** — coupés pour
  tenir 30 s. Me Humbert a validé cet arbitrage.
- **« et en responsabilité médicale »** après « spécialisé » — jamais
  réintroduire : le certificat CNB vérifié dans `index.html` porte sur le
  **dommage corporel seul**, et « spécialiste » est un titre protégé
  (art. 21-1 loi n° 71-1130 ; décret n° 91-1197).
- **« tous les moyens de gagner »** (brouillon initial) — promesse de
  résultat. Remplacé par la chute retenue, qui énonce une règle générale au
  présent de vérité générale, sans « vous ». **Ne jamais la reformuler en
  « votre dossier sera mieux indemnisé ».**
- **« premier avocat certifié en IA de France »** — écarté (mention
  comparative, RIN art. 10.2). Décision non tranchée, à sa main.

---

## 3. Décisions de Me Humbert à respecter telles quelles

1. **Prononciation** : le moteur doit dire **« Patrice Imbert »** (h muet).
   La table `PRONONCIATION` de `voix_script.py` corrige le texte **lu**
   uniquement ; gabarits et métadonnées gardent « Humbert ».
2. **Nathalie et Nicolas** : ne jamais dire que ce sont des voix de synthèse
   ou une IA. La formule retenue est **« Ils ne sont pas avocats, ce sont les
   deux voix de l'émission. »** Le point à préserver n'est pas la phrase mais
   le fait qu'on ne puisse pas les prendre pour des collaborateurs du cabinet
   (garde `MARQUEURS_HONNETETE`, qui accepte une famille de formulations).
3. **Signataires imposés** : victimes = Patrice Humbert, famille = Cédrine
   Raybaud. Contrôlé par `verifier_signataire()`.
4. **Le permis, c'est son associé**, pas lui — il travaille exclusivement pour
   les victimes. Instruction expresse : **« suis mes instructions et ne
   conteste pas »**. Ne pas rouvrir ce sujet.
5. **Voicebox remplace ElevenLabs** : gratuit, local, sa voix y est déjà
   clonée. Aucun texte ne sort de sa machine.
6. **Les blocs invariants ne se resynthétisent jamais** — sa remarque : « le
   regénérer à chaque épisode le fait varier légèrement et la signature
   s'émousse. »

---

## 4. Outillage — ce que chaque fichier fait

| Fichier | Rôle |
|---|---|
| `tools/voix_script.py` | produit les textes dits par l'avocat, découpe l'intro en 3 segments, applique la phonétique, refuse un script altéré. `--self-test` : **45/45** |
| `tools/voix_moteur.py` | moteur de synthèse : `aucun` / `manuel` (écrit les .txt à coller) / `voicebox` (HTTP, local **ou distant authentifié**). Attend la fin des générations **asynchrones**. `--self-test` : **41/41**, `--diagnostic` interroge l'instance |
| `tools/podcast_episode.py` | **une seule commande** : outro + segments + montage. Accepte le débat dans **toutes** les extensions que le montage sait lire, M4A compris. `--self-test` : **8/8** |
| `tools/poste_verifier.py` | vérifie que le poste a tout (ffmpeg, Voicebox, config, musique) et explique chaque manque en français. Sonde l'adresse **de la configuration**, pas le port par défaut. `--self-test` : **15/15** |
| `tools/voicebox_tunnel.py` | publie Voicebox derrière Cloudflare Tunnel + Access, portail posé **avant** le DNS. `--self-test` : **9/9** |
| `GUIDE-POSTE-MAC.md` | **la voie recommandée** : installer Claude sur le Mac du cabinet, 4 étapes, aucun tunnel |
| `CONNEXION-VOICEBOX.md` | l'alternative : piloter Voicebox depuis une session distante — tunnel **authentifié**, secrets en variables d'environnement |
| `tools/podcast_montage.py` | montage ffmpeg complet : appariement, loudness 2 passes, générique musical, concaténation, limiteur, MP3, 14 contrôles qualité. `--self-test` : **36/36** |
| `tools/ffmpeg_moteur.py` | binaire local ou service HTTP distant, même contrat. `--self-test` : **10/10** (sans option) |
| `PROMPT-INTRO-VOIX.md` | le prompt à copier une fois par épisode — produit **la question du jour**, rien d'autre |
| `PROMPT-PODCAST-NOTEBOOKLM.md` | pilotage du débat NotebookLM (agent computer-use, **sur son poste**) |
| `PROMPT-MONTAGE-DIFFUSION.md` | montage et diffusion |
| `podcasts/queue-podcast.csv` | file des épisodes (chaine, rank, slug, titre, url…) |
| `podcasts/musique/LICENCES.md` | registre des licences — le montage **refuse de tourner** si la piste n'y figure pas |
| `podcasts/voicebox.exemple.json` | gabarit de configuration ; le vrai `voicebox.json` est **gitignoré** |

### Constantes de montage (ne pas changer sans raison mesurée)

```
LOUDNESS_CIBLE = -16.0 LUFS     VRAI_PIC_MAX = -1.5 dBTP
ECHANTILLONNAGE = 44100 Hz      DEBIT_DEFAUT = 192 kb/s CBR
PAUSE_DEFAUT = 400 ms           PAUSE_SEGMENTS = 150 ms
MUSIQUE_DUREE = 6.0 s           MUSIQUE_NIVEAU = -20.0 LUFS (4 LU sous la voix)
MUSIQUE_FONDU_ENTREE = 0.3 s    MUSIQUE_FONDU_SORTIE = 1.5 s
MUSIQUE_PAUSE = 250 ms          TOLERANCE_LOUDNESS = 0.5 LU / DUREE = 0.5 s
MUSIQUE_DEBUT = 0.0 s           point d'entrée (--debut-musique)
LIMITEUR_MARGE = 1.5 dB         marge vrai pic / pic échantillon
```

**Le limiteur et le contrôle ne mesurent pas la même chose.** `alimiter` borne
le pic **échantillon** ; le contrôle mesure le **vrai pic**, suréchantillonné,
qui compte les crêtes reconstituées entre les échantillons — et l'encodage MP3
en ajoute. D'où la marge, et la boucle de finalisation qui vérifie après coup.

**Ordre imposé pour le générique : découper → mettre au niveau → fondre.**
Il a été établi à la mesure, pas par principe (cf. §5).

---

## 5. Le test du 2026-08-13 — ce qui est PROUVÉ

Article pilote choisi par Me Humbert :
`https://medical.lexvox-avocat.fr/10-conseils-pour-reussir-son-expertise/`
(slug `10-conseils-pour-reussir-son-expertise`, déjà inscrit dans la file).

Question du jour produite :

> Vous êtes convoqué à une expertise médicale. Que faut-il préparer, et quelle
> erreur peut vous coûter votre indemnisation ? *(122 car ≈ 8,1 s)*

**La chaîne de montage a tourné pour de bon**, avec des sources audio
synthétiques (bruit rose modulé) aux durées réelles des trois blocs — ffmpeg
et ffprobe obtenus depuis PyPI (`pip install ffmpeg-binaries`), l'image de
base n'en a pas. Résultat : **14/14 contrôles qualité au vert**, MP3 269,19 s,
192 kb/s, **−16,3 LUFS**, vrai pic **−1,73 dBTP**.

Découpage mesuré sur le fichier produit (`silencedetect`), conforme au plan :

| de | à | bloc | niveau |
|---|---|---|---|
| 0,00 | 5,95 s | générique musical (fondu éteint **avant** la voix) | −20,5 LUFS |
| 6,25 | 14,36 s | bloc 1 — question | −16,2 LUFS |
| 14,51 | 28,61 s | bloc 2 — présentation | −16,3 LUFS |
| 28,76 | 37,36 s | bloc 3 — annonce du débat | — |
| 37,76 | 219,76 s | corps NotebookLM | −16,2 LUFS |
| 220,16 | 269,19 s | outro | — |

**Intro voix = 31,1 s**, exactement la cible. Réutilisation des invariants
vérifiée : au second passage, les blocs 2 et 3 sont marqués « déjà enregistré,
RÉUTILISÉ » et ne repassent pas par le moteur.

### La musique réelle (2026-08-13, même journée)

Me Humbert a fourni ***Intro YouTube* de Kulakovka** (Pixabay, ID 295915),
certificat de licence nominatif archivé dans
`podcasts/musique/licences/pixabay-intro-youtube-295915.txt`. Le montage a été
rejoué avec cette piste : **14/14 au vert**, générique à **−20,5 LUFS** contre
**−16,2 LUFS** pour la voix, soit les 4 LU d'écart visés.

### Quatre vrais défauts trouvés par ces tests, et corrigés

1. **`podcast_montage.py` — contrôle « encodeur libmp3lame » impossible à
   passer.** Il lisait l'étiquette ID3 `encoder`, où le multiplexeur mp3 de
   ffmpeg écrit **toujours** sa propre version (`Lavf60.3.100`) — il écrase
   même un `-metadata encoder=…` fourni à la main. Tout premier montage réel
   aurait échoué en fin de chaîne, après avoir tout calculé. Le contrôle
   cherche désormais la marque **`LAME`** que l'encodeur écrit *dans le flux*
   (entête LAME de la première trame) : c'est la seule preuve authentique.
2. **`voix_script.py` — dépendance morte à la file CSV.** L'intro à trois
   blocs ne cite plus `{titre}` ni `{sujet}`, mais l'outil exigeait toujours
   une ligne dans `queue-podcast.csv` et **échouait (code 2)** pour un slug
   absent. La lecture n'a lieu que si le gabarit s'en sert ; sinon un
   avertissement signale le slug inconnu sans bloquer.
3. **Générique coupé à l'aveugle sur les 6 premières secondes.** Mesurée
   seconde par seconde, la piste réelle s'ouvre sur des frappes isolées
   séparées de quasi-silence, et la musique pleine ne démarre qu'à **12,00 s**.
   Le réglage par défaut aurait placé **≈ 3 s de trou** juste avant la première
   syllabe de l'avocat. Ajout de **`--debut-musique`** : le point d'entrée est
   réglé à **11,70 s**, le fondu d'entrée se consomme dans le silence qui
   précède et l'attaque arrive à plein niveau. *(Défaut invisible au premier
   test : la musique de synthèse y était uniforme.)*
4. **Le générique n'atteignait pas son niveau.** L'outil normalisait la piste
   **entière** (115 s) puis en coupait 6 s : le niveau intégré d'une piste de
   deux minutes n'est pas celui de l'extrait qu'on en tire. Mesure : **−23,1
   LUFS** livrés pour −20 demandés, soit un générique **7 LU** sous la voix au
   lieu de 4 — timide là où il doit poser la marque. L'ordre est désormais
   **découper → mettre au niveau → fondre**, ce qui ramène la mesure à
   **−19,6 LUFS** hors montage et **−20,5 LUFS** dans le fichier final.
   *(Même angle mort que le défaut 3 : une source de test uniforme masque le
   problème, une vraie musique le révèle.)*

### Le premier débat NotebookLM réel (2026-08-13)

Fichier reçu : *Réussir l'expertise médicale pour être indemnisé*, **AAC en
conteneur M4A**, stéréo 44,1 kHz, 875,5 s, −17,5 LUFS. Aucun silence dans tout
le fichier, décroissance naturelle sur la dernière demi-seconde — il ne se
coupe pas au milieu d'un mot.

**Il dure 14 min 35, alors que la consigne demandait « moins de 5 min ».**
L'épisode monté fait donc **16 min 02** au lieu des 6 à 7 minutes visées.

→ **Arbitrage de Me Humbert (2026-08-13) : durée acceptée, à titre
exceptionnel, pour cet épisode.** La consigne « Moins de 5 min » reste en
vigueur pour la suite.

Le texte du champ n'est donc pas le levier de la durée : il a été ignoré. Au
prochain épisode, vérifier si le dialogue « Personnaliser » offre un choix de
DURÉE (*Plus court* / *Shorter*) en français — le référentiel le donne comme
parfois absent. C'est l'écart n° 1 du carnet de calibration.

**Un cinquième défaut, révélé par ce contenu réel :** le montage a échoué sur
le contrôle de vrai pic, à **−0,35 dBTP** pour un plafond de −1,5. Le limiteur
bornait le pic *échantillon* à −1,5 dB quand le contrôle mesure le *vrai* pic,
suréchantillonné — deux grandeurs différentes, et l'encodage MP3 creuse encore
l'écart. Avec du bruit rose l'écart était négligeable ; avec de la parole
réelle il valait 1,15 dB. **Tout épisode réel aurait échoué en fin de chaîne.**

Correction : marge de 1,5 dB sur le limiteur, plus une boucle qui mesure et
corrige, en arbitrant explicitement — le plafond prime sur le niveau, car un
dépassement fait retirer l'épisode quand un demi-décibel ne s'entend pas.

Deux méthodes ont été comparées à la mesure sur l'assemblage réel :

| | niveau | dynamique (LRA) | vrai pic |
|---|---|---|---|
| gain + limiteur à −3,0 dB *(retenue)* | −16,2 LUFS | 5,1 LU | −1,8 dBTP |
| `loudnorm` à vrai pic, TP −2,0 | −16,5 LUFS | 4,9 LU | −2,1 dBTP |

Contre l'intuition — un limiteur à vrai pic étant l'outil théoriquement juste —
la première tient mieux le niveau **et** la dynamique. Résultat final :
**14/14 au vert**, 962,72 s, −16,25 LUFS, −1,8 dBTP.

---

## 5bis. Le dialogue Voicebox mis à l'épreuve (2026-08-13)

Le client HTTP n'avait **jamais** été exécuté. Il l'a été contre un faux
Voicebox implémentant le contrat documenté — `/openapi.json`, `/profiles`,
`POST /generate`, `GET /audio/{id}` — y compris en mode **strict**, c'est-à-dire
appliquant réellement la négociation de contenu et les contraintes de son
propre schéma. **Quatre défauts, tous invisibles à la lecture du code :**

1. **`Accept: application/json` envoyé pour télécharger l'audio.** Tout serveur
   qui applique la négociation de contenu répond **406** — et le refus tombe
   *après* la génération, donc après le temps de calcul GPU. L'en-tête suit
   désormais ce qu'on demande vraiment.
2. **`max_chunk_chars` envoyé en dur.** Le diagnostic lisait le schéma de
   l'instance ; la synthèse, elle, l'ignorait. Une instance qui plafonne cette
   valeur rendait un **422** incompréhensible. Le client lit maintenant les
   limites déclarées (langue, longueur de texte, plafond de découpage) et s'y
   plie, en avertissant si un segment devient trop long pour tenir d'une traite.
3. **La langue n'était vérifiée qu'au diagnostic.** Le refus arrivait donc en
   pleine production. Il tombe désormais **avant** l'appel, avec le renvoi au
   piège documenté.
4. **`voix_script.py --sortie` écrivait le texte dans le fichier audio** — que
   la synthèse écrasait aussitôt — et ne créait pas son dossier parent. Le
   texte va à côté, en `.txt`, et le dossier est créé.

S'y ajoute un contrôle qui manquait : **ce que rend `/audio` doit ressembler à
de l'audio**. Un code 200 ne prouve rien ; derrière un portail
d'authentification — précisément le montage recommandé — une requête mal
authentifiée rend volontiers une page de connexion en HTML, avec un code 200,
qui finissait écrite dans un `.mp3`.

**Chaîne complète exécutée en une commande** (`podcast_episode.py`) contre ce
serveur strict : outro, trois segments d'intro, montage — **14/14 au vert**,
code 0. Au second passage, outro et blocs invariants réutilisés sans repasser
par le moteur.

⚠️ Ce qui est prouvé, c'est que **le client parle correctement à une instance
conforme**. La vraie instance du cabinet reste à confronter :
`python3 tools/voix_moteur.py --diagnostic`.

---

## 5ter. Le pilote monté sur le poste du cabinet (2026-08-14)

Première exécution de bout en bout **hors machine de développement** : vraie
instance Voicebox, vraie voix clonée, vrai débat NotebookLM.

**Résultat : 14/14 au vert.** MP3 de **947,46 s** (15 min 47), 192 kb/s, mono,
44,1 kHz, **−16,31 LUFS**, vrai pic **−1,81 dBTP**. Découpage relevé sur le
fichier livré : générique 0 → 5,96 s, voix à partir de **6,27 s** — le fondu
s'éteint avant la première syllabe, sans trou.

### Ce que le poste réclamait, et qui a été réglé

- **ffmpeg absent, pas de Homebrew** : installé par `pip install ffmpeg-binaries`,
  liens dans `~/.local/bin` (déjà dans le PATH) — les outils le cherchent par
  `shutil.which`.
- **Voicebox écoute sur le port 17493**, pas 8000.
- **Profil de la chaîne victimes** : `43cf0487-787a-4ba1-9c6e-83967714935a`
  (« Patrice Humbert », `default_engine: chatterbox`).

### La question du français est tranchée : il est ACCEPTÉ

Le `/openapi.json` de l'instance du cabinet déclare
`^(en|zh|ja|ko|de|fr|ru|pt|es|it)$`. Le piège de la doc publique
(« en|zh seulement ») ne concerne pas cette instance. Le diagnostic conclut
**INSTANCE CONFORME**. Les 72 épisodes peuvent se produire.

### La panne qui n'était pas dans le code : « orphaned by worker »

Aucune synthèse ne partait. L'instance acceptait `/generate`, rendait un
identifiant, et **ne calculait rien** — état `generating` éternel à 0,6 % de
processeur. Cause : **le serveur avait survécu à son interface** et tournait
orphelin depuis le 25 juillet, son processus parent mort. Voicebox le dit
lui-même quand on annule : *« Generation orphaned by worker »*.

Remède : `POST /shutdown`, puis rouvrir l'application. Après quoi : **30 s de
chargement du modèle, puis environ 30 s de calcul pour 4 s de voix**.

**À reconnaître avant de chercher ailleurs** : un état `generating` qui dure
sans consommer de processeur n'est pas une synthèse lente, c'est un serveur
orphelin. Vérifier son âge (`ps`) plutôt que le code.

### Trois défauts d'outillage, invisibles jusqu'à cette instance

1. **`voix_moteur.py` — `/generate` est ASYNCHRONE.** Il rend un identifiant
   avec `status: generating` ; l'audio n'existe qu'après. Le client
   téléchargeait aussitôt et récoltait un **500** — après le temps de calcul,
   donc au pire moment. Il attend désormais, et annonce la cause en cas
   d'échec. *Piège dans le piège :* `/generate/{id}/status` est un **flux** qui
   ne se ferme qu'à la fin et **gèle** tout appel synchrone ; c'est
   `/history/{id}` qu'il faut sonder — il répond en 0,01 s.
2. **`podcast_episode.py` exigeait un `.mp3`.** NotebookLM rend un **M4A**, que
   `podcast_montage.py` sait pourtant lire depuis toujours. La vérification
   préalable arrêtait donc tout devant un fichier présent et valide. Les deux
   outils partagent maintenant la même liste d'extensions.
3. **`poste_verifier.py` sondait `localhost:8000` en dur.** Il annonçait
   « Voicebox injoignable » d'une instance qui tournait, et faisait déclarer le
   poste en panne alors qu'il était bon. Il lit l'adresse de la configuration ;
   un `--voicebox` explicite prime toujours.

### Prononciation : vérifiée par la machine, pas par l'oreille

`POST /transcribe` (multipart ; champ `model` = `base|small|medium|large|turbo`
— **pas** `whisper-large`) a réécouté le bloc 2. Il rend :

> « L'ex-victime, le podcast du cabinet Lexvox Avocat. **Maître Patrice Imbert**,
> spécialisé en dommages corporels. Une confidence, ce n'est pas le dossier le
> plus grave qui est le mieux indemnisé, c'est le mieux défendu. »

**« Imbert » est confirmé, le h est muet.** Méthode à rejouer sur tout nouveau
bloc invariant : elle prouve la prononciation sans dépendre d'une écoute.

Elle révèle aussi que **« LEXVICTIME » s'entend « l'ex-victime »** → décision
n° 9 du §8.

*(Le service de transcription a ensuite rendu six 500 d'affilée, whisper-large
et chatterbox étant chargés ensemble. Les autres blocs n'ont pas été
retranscrits : circuit-breaker.)*

### Un sixième défaut de montage, mesuré : le générique tient 1 LU, pas 4

Mesures indépendantes prises **sur le fichier livré**, en décodant les extraits :

| bloc | niveau |
|---|---|
| générique (0 → 5,95 s) | **−17,06 LUFS** |
| intro voix (6,3 → 37 s) | **−16,00 LUFS** |
| corps NotebookLM (60 → 120 s) | −16,50 LUFS |
| outro (897 → 947 s) | −15,58 LUFS |

Le générique n'est qu'à **1,06 LU** sous la voix, là où `MUSIQUE_NIVEAU` en vise
**4**. Ce n'est **pas** la mise à niveau qui dérive : rejouée à part, elle rend
**−19,99 LUFS**, et **−20,11** après les fondus — exactement la cible.

La cause est la **boucle de finalisation**. Elle applique un gain global, puis
`alimiter` borne à −3 dB. La voix, dont les crêtes touchent le limiteur, ne
monte pas de tout le gain ; la musique, à crêtes basses, l'encaisse en entier.
L'écart se referme de 4 LU à 1.

**Pourquoi le 13/08 ne pouvait pas le voir** : ses blocs de voix étaient du bruit
rose, qui ne déclenche pas le limiteur comme de la parole. Même angle mort que
les défauts 3 et 4 — *une source de test régulière masque ce qu'une vraie source
révèle*.

**Portée réelle** : le générique **précède** la voix, il ne passe pas dessous.
Rien n'est masqué, l'intelligibilité est intacte. C'est un confort d'écoute, pas
un défaut de diffusion — d'où l'arbitrage laissé à Me Humbert (§8, décision 10)
plutôt qu'une constante changée d'autorité.

---

## 6. Ce qui n'est PAS prouvé — à valider sur le poste du cabinet

| À valider | Comment | Pourquoi ça n'a pas pu l'être ici |
|---|---|---|
| ~~**Dialogue HTTP**~~ | ✅ **exercé** contre un faux Voicebox conforme au schéma, puis ✅ **contre la vraie instance** le 2026-08-14 — un 5e défaut trouvé là (génération asynchrone), cf. §5bis et §5ter | — |
| ~~**Le français est accepté**~~ | ✅ **tranché le 2026-08-14** : l'instance du cabinet déclare `^(en\|zh\|ja\|ko\|de\|fr\|ru\|pt\|es\|it)$`. Le piège de la doc publique ne la concerne pas | — |
| ~~**Qualité de la voix clonée**~~ | ✅ « **Imbert** » confirmé par transcription automatique (§5ter), et l'épisode est écoutable. Reste à l'oreille de Me Humbert : « Dintilhac », « Marignane » | — |
| ~~**Musique réelle**~~ | ✅ **fait** — *Intro YouTube* (Kulakovka, Pixabay), licence archivée, montage rejoué 14/14. Déposer la piste en `~/LEXVOX-PODCASTS/musique/musique-lexvox.mp3` et monter avec `--debut-musique 11.7` | — |
| **`MoteurAPI` (service ffmpeg distant)** | — | jamais exécuté ; seul le moteur **local** est prouvé |

---

## 7. Marche à suivre pour l'épisode pilote

**La commande qui a réellement produit le pilote**, une fois le débat déposé et
`poste_verifier.py` tout vert — elle enchaîne outro, segments et montage :

```bash
python3 tools/podcast_episode.py --chaine victimes \
    --slug 10-conseils-pour-reussir-son-expertise \
    --question "Vous êtes convoqué à une expertise médicale. Que faut-il préparer, et quelle erreur peut vous coûter votre indemnisation ?" \
    --debut-musique 11.7
```

Le détail étape par étape, si l'une d'elles doit être rejouée seule :

```bash
# 0. sur le poste du cabinet, Voicebox lancé
python3 tools/poste_verifier.py          # doit afficher TOUT EST EN PLACE
python3 tools/voix_moteur.py --diagnostic

# 1. produire la question du jour  (prompt : PROMPT-INTRO-VOIX.md)
#    puis fabriquer les 3 segments — seul le bloc 1 est réellement synthétisé
python3 tools/voix_script.py --chaine victimes \
  --slug 10-conseils-pour-reussir-son-expertise \
  --question "Vous êtes convoqué à une expertise médicale. Que faut-il préparer, et quelle erreur peut vous coûter votre indemnisation ?" \
  --segments ~/LEXVOX-PODCASTS/victimes/segments --moteur voicebox

# 2. l'outro : une seule prise pour toute la chaîne
python3 tools/voix_script.py --bloc outro --chaine victimes

# 3. le débat NotebookLM  (PROMPT-PODCAST-NOTEBOOKLM.md, sur son poste)
#    -> déposer le rendu dans ~/LEXVOX-PODCASTS/victimes/brut/<slug>.<ext>
#       Le M4A rendu par NotebookLM se dépose TEL QUEL : le reconvertir en MP3
#       n'ajouterait qu'une génération de perte.

# 4. montage  —  --debut-musique 11.7 est le point d'entrée mesuré du
#    générique en service (cf. podcasts/musique/LICENCES.md)
python3 tools/podcast_montage.py --chaine victimes \
  --slug 10-conseils-pour-reussir-son-expertise \
  --racine ~/LEXVOX-PODCASTS \
  --segments ~/LEXVOX-PODCASTS/victimes/segments \
  --debut-musique 11.7
```

Arborescence attendue sous `--racine` :

```
~/LEXVOX-PODCASTS/
├── musique/            musique-lexvox.mp3   (générique commun aux 3 chaînes)
└── victimes/
    ├── segments/   01-question-victimes-<slug>.mp3, 02-presentation-victimes.mp3, 03-final-victimes.mp3
    ├── brut/       <slug>.m4a          (débat NotebookLM, tel qu'il sort)
    ├── outro/      outro-victimes.mp3  (une seule prise pour la chaîne)
    ├── musique/    musique-victimes.mp3   (facultatif — prime sur le commun)
    └── mp3/        podcast-victimes-01-<slug>.mp3   (produit)
```

---

## 8. Décisions qui attendent Me Humbert

1. **LEXVICTIME ou LEXVICTIMES ?** Il a écrit les deux ; la marque du site est
   **LEXVICTIME®**, les gabarits disent LEXVICTIME. À confirmer.
2. **Nom de l'associé** qui signe la chaîne permis (paramètre `--avocat`).
3. **Titre de l'émission famille**.
4. **Plateforme de diffusion / hébergeur RSS** — `PLATEFORME_DIFFUSION` vaut
   toujours `[À DÉFINIR]` ; le montage produit le fichier et s'arrête là.
5. **Débit 192 ou 128 kb/s** (192 par défaut aujourd'hui).
6. **Service ffmpeg distant** (`--moteur api`) : utile seulement s'il ne veut
   pas installer ffmpeg localement.
7. **Mention « premier avocat certifié en IA de France »** : écartée, à sa
   main.
8. **Durée des épisodes.** Le pilote fait 16 min 02 — accepté à titre
   exceptionnel. Si NotebookLM continue d'ignorer la consigne « moins de
   5 min », faut-il l'accepter comme format de la série, ou chercher le levier
   dans le dialogue « Personnaliser » (choix de DURÉE) ? Un débat de quinze
   minutes n'est pas le même produit qu'un épisode de six.
9. **« LEXVICTIME » s'entend « l'ex-victime ».** La transcription automatique du
   bloc 2 rend « L'ex-victime, le podcast du cabinet Lexvox Avocat » : la
   machine a entendu ce qu'un auditeur peut entendre. Garder tel quel, ou faire
   détacher « LEX — VICTIME » par la table `PRONONCIATION` ? *(Se règle dans le
   texte lu, sans toucher aux gabarits ni à la marque.)* **Recoupe la décision
   n° 1**, qui portait sur l'orthographe : celle-ci porte sur le son.
10. **Le générique tient 1 LU sous la voix au lieu de 4** (§5ter), parce que le
    limiteur rabote la voix et pas la musique. Rien n'est masqué — le générique
    précède la voix. Laisser ainsi, ou compenser ? La correction propre est
    d'abaisser `MUSIQUE_NIVEAU` de la valeur mesurée, **après** avoir vérifié
    qu'elle se reproduit sur un second épisode : un réglage calé sur un seul
    montage se paie au suivant.

### Décisions déjà prises, pour mémoire

| Décision | Date | Effet |
|---|---|---|
| Le débat **oriente** vers l'avocat, l'outro **convertit** | 2026-08-13 | fiche cabinet + personnalisation réécrites |
| Durée du pilote acceptée à 16 min | 2026-08-13 | exception ; consigne « moins de 5 min » maintenue |
| Générique : *Intro YouTube* (Kulakovka, Pixabay), entrée à 11,70 s | 2026-08-13 | licence archivée, `--debut-musique 11.7` |
| Voicebox remplace ElevenLabs, en local | 2026-08-13 | aucun texte ne sort de la machine |
| Nathalie et Nicolas jamais présentés comme des voix de synthèse | 2026-08-13 | « ils ne sont pas avocats, ce sont les deux voix de l'émission » |
| Épisode pilote **fabriqué et livré** sur le poste du cabinet | 2026-08-14 | 947,46 s, 14/14 au vert ; §6 vidé de ses inconnues sauf le ffmpeg distant |

---

## 9. Règles du dépôt qui s'appliquent à ce chantier

- **Aucun fichier audio n'est committé.**
- **Aucun secret en dur** : `SANITY_API_TOKEN`, `WP_*`, jeton Voicebox →
  variables d'environnement uniquement. `podcasts/voicebox.json` est gitigné.
- **Développer et pousser sur `claude/podcast-automation-plan-5m6b59`**
  (PR #23), jamais sur `main` directement.
- **`git pull --rebase origin main` avant chaque push** ; `git diff --check`
  avant chaque commit.
- **Ne jamais toucher `.github/workflows/deploy.yml`** (neutralisé en
  `workflow_dispatch` — un `on: push` écraserait le site Sanity en production).
- Recherche web : `tools/web_read.py` et `tools/exa_search.py`, **contenu
  public uniquement**.
