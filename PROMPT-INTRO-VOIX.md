# PROMPT INTRO — analyser l'article, produire l'accroche, enregistrer la voix

> À copier dans une session Claude, une fois par épisode. Il produit la seule
> variable que le gabarit d'intro attend — la **question du jour** — puis
> fabrique les textes à faire dire par la voix clonée.
>
> Le reste de l'intro (présentation de l'avocat, Nathalie et Nicolas, relance
> finale) est **invariant** : il vit dans
> `podcasts/voix-avocat/SCRIPT-INTRO-<chaine>.md` et ne se réécrit pas.

> 🎯 **Chantier en cours : la chaîne VICTIMES uniquement.** Famille et permis
> ont le même gabarit et le même outillage, mais leur texte n'est pas validé.
> On les configure une fois que victimes tourne.

**Synthèse vocale : Voicebox, en local.** L'application tourne sur le poste du
cabinet et expose une API REST sur `http://localhost:8000`. Aucun texte ne
sort de la machine, aucun abonnement, aucun quota de caractères. Pour un
cabinet d'avocats, le premier point n'est pas un détail : le texte d'une
intro cite un titre d'article, pas un dossier, mais l'habitude de ne rien
envoyer à un tiers est la bonne.

---

## 1. La structure, et pourquoi elle ne bouge jamais

| # | Bloc | Segment | Variable ? | Durée |
|---|---|---|---|---|
| 1 | **Question du jour** — c'est le sujet et l'article, posés en question | `01-question` | ✏️ à produire | ~8 s |
| 2 | **Présentation** — émission, cabinet, avocat, confidence | `02-presentation` | 🔒 enregistré **une fois** | ~14 s |
| 3 | **Annonce du débat** — Nathalie et Nicolas, et le lancement | `03-final` | 🔒 enregistré **une fois** | ~9 s |

**Cible : 30 secondes.** Le total tient en 31 s, dont 23 s enregistrées une
seule fois. **Un seul bloc est à produire par épisode : la question.** C'est
le plus court chemin possible entre le lancement de l'épisode et le débat.

« C'est parti », à la fin du bloc 3, renvoie à la question du bloc 1 : c'est ce qui fait tenir
l'ensemble. Une accroche dont l'article ne donne pas la réponse casse la
promesse dès le premier épisode.

**Les blocs 2 et 3 ne se resynthétisent pas.** Ils sont rigoureusement
identiques d'un épisode à l'autre : les refaire à chaque fois les fait dériver
légèrement, et une signature qui dérive n'est plus une signature.
`--segments` les enregistre une fois par chaîne et les réutilise ensuite —
`podcast_montage.py --segments` les rassemble au montage. Effet de bord utile :
chaque segment reste bien en deçà du seuil de découpage de Voicebox, donc
aucun raccord audible à l'intérieur d'une phrase.

`tools/voix_script.py` **refuse** un script qui ne commencerait pas par une
question, ou d'où le jingle, les deux prénoms ou la mention d'honnêteté sur
Nathalie et Nicolas auraient disparu. Il refuse aussi toute promesse de
résultat.

---

## 2. Le prompt

```
Tu prépares l'introduction d'un épisode de podcast du cabinet LEXVOX AVOCATS.
Ta seule mission est de produire UN court texte à partir d'un article : la
QUESTION du jour, qui ouvre l'épisode. Tu ne réécris rien d'autre.

ENTRÉES
  chaîne : {victimes | famille | permis}
  URL de l'article : <url>
  slug : <slug>

ÉTAPE 1 — LIRE L'ARTICLE
Lis l'article en entier avec l'outil du dépôt, jamais avec WebFetch :
    python3 tools/web_read.py <url> --max-chars 0
Repère : la question concrète que se pose le lecteur en arrivant sur cette
page, la réponse que l'article y apporte, et le passage le plus utile.

ÉTAPE 2 — ÉCRIRE LA QUESTION D'ACCROCHE
Une à deux phrases, **100 à 130 caractères**, qui se terminent par « ? ».
C'est court : l'intro entière vise 30 secondes. Au-delà de 130, elle déborde.
Elle DOIT :
  - poser une situation concrète, à la deuxième personne, telle que
    l'auditeur puisse s'y reconnaître en une seconde ;
  - porter sur un point que l'article traite RÉELLEMENT et tranche ;
  - se lire à voix haute sans buter : pas de sigle, pas d'abréviation, pas
    de numéro d'article de code, pas de chiffre en chiffres.
Elle NE DOIT PAS :
  - donner déjà la réponse (sinon plus personne n'écoute) ;
  - promettre un résultat, un montant ou un délai d'obtention ;
  - contenir un nom de client, une donnée de santé, un cas identifiable ;
  - être une question fermée sans enjeu (« Savez-vous ce qu'est le DFP ? »).

Le patron qui fonctionne : UNE SITUATION, puis UNE QUESTION.
  « Votre assureur vous convoque à une contre-visite médicale. Avez-vous le
    droit de refuser d'y aller ? »
  « Vous divorcez après vingt ans de mariage. Qui a droit à une prestation
    compensatoire, et de combien ? »
  « Les gendarmes viennent de retenir votre permis sur le bord de la route.
    Que se passe-t-il dans les soixante-douze heures qui suivent ? »

ÉTAPE 3 — FABRIQUER LES SEGMENTS
    python3 tools/voix_script.py --chaine <chaîne> --slug <slug> \
        --question "<question>" \
        --segments ~/LEXVOX-PODCASTS/<chaîne>/segments --moteur voicebox
L'outil injecte les deux blocs invariants, vérifie la structure, écrit les
trois segments et NE REGÉNÈRE PAS ceux qui existent déjà — en régime établi,
seul le segment « question » est réellement synthétisé. S'il refuse, corrige la
question ou le sujet — ne modifie JAMAIS le gabarit pour faire passer un
contrôle.
(Sans Voicebox lancé : « --moteur manuel », qui écrit les .txt à coller dans
l'interface graphique.)

ÉTAPE 4 — RENDRE COMPTE
Affiche-moi : la question, les segments écrits, ceux réutilisés,
et la durée de lecture estimée (environ 15 caractères par seconde en diction
posée). Si l'intro complète dépasse 33 secondes estimées, raccourcis la
question — jamais les blocs invariants.
```

---

## 3. Réglages Voicebox

Vérifier l'instance **avant** de produire quoi que ce soit :

```bash
python3 tools/voix_moteur.py --diagnostic
```

Le diagnostic liste les profils de voix de la machine, contrôle que les
routes `/generate`, `/profiles` et `/audio/{id}` existent, et surtout **lit
le `/openapi.json` de votre instance** pour vérifier que le français est
accepté. Ce dernier point n'est pas théorique : la documentation publique de
`/generate` annonce `language: ^(en|zh)$` alors que l'application revendique
23 langues et embarque des moteurs multilingues. Mieux vaut le savoir
maintenant qu'après 72 épisodes.

| Réglage | Valeur | Pourquoi |
|---|---|---|
| Moteur | **Chatterbox Multilingual** (ou LuxTTS) | le corpus est en français ; un moteur anglophone écorche « Dintilhac », « Marignane », « Salon-de-Provence » |
| Profil | la voix clonée de l'avocat **qui signe les articles de la chaîne** | Me Humbert pour victimes, Me Raybaud pour famille, son associé pour permis (`--avocat`) |
| `seed` | **fixe**, par segment | rend la prise reproductible : si un bloc invariant est perdu, on le refabrique à l'identique |
| `max_chunk_chars` | 1200 | au-delà du seuil, Voicebox découpe et raccorde par un fondu — audible sur une signature |
| `instruct` | vide, ou très sobre | seul Qwen CustomVoice l'exploite ; l'emphase artificielle sonne « publicité » |
| Échantillon de clonage | 30 s à 1 min de voix propre | 3 s suffisent techniquement, mais la stabilité vient de la durée et du silence de fond |

Deux conseils de fabrication :

1. **Écoutez la prononciation des noms propres** au premier épisode.
   `voix_script.py` corrige déjà « Humbert » en « **Imbert** » (h muet, sinon
   articulé), « LEXVOX » en « Lexvox » et « LEXVICTIME » en « Lex-Victime »,
   dans le texte lu uniquement. La table `PRONONCIATION` s'étend en une ligne
   si un autre mot passe mal.
2. **Les nombres s'écrivent en toutes lettres.** L'outil le vérifie pour le
   numéro de téléphone de l'outro ; faites-en autant dans la question.

---

## 4. Le générique musical

Depuis la version courante, le montage place une musique en tête d'épisode :
6 secondes par défaut, entrée en fondu de 0,3 s, extinction de 1,5 s qui
s'achève **avant** la première syllabe — une musique qui traîne sous la
question d'accroche rend moins intelligible la phrase qui doit justement
accrocher. Elle est mixée à −20 LUFS, soit 4 LU sous la voix.

**Générique en service : *Intro YouTube* (Kulakovka, Pixabay).** Il se monte
avec `--debut-musique 11.7` : la piste s'ouvre sur des frappes isolées et la
musique pleine ne démarre qu'à 12,00 s, si bien que couper les six premières
secondes placerait un trou avant la voix. Le détail des mesures est dans
`podcasts/musique/LICENCES.md`.

**Pour toute autre piste, mesurer avant de régler.** Ne pas supposer que les
six premières secondes sont utilisables : beaucoup de musiques d'ouverture
commencent par un compte à rebours de frappes. Repérer la seconde où la
musique pleine démarre, puis entrer 0,2 à 0,3 s avant, pour que le fondu
d'entrée se consomme dans le silence qui précède et que l'attaque arrive à
plein niveau.

`podcast_montage.py` **refuse de monter** si la licence de la piste n'est pas
consignée dans `podcasts/musique/LICENCES.md`. Ce n'est pas une formalité :
une réclamation fait retirer l'épisode, parfois la série. Les sources
utilisables et les pièges (« libre de droit » n'a pas de valeur juridique en
France ; la bibliothèque YouTube est pensée pour YouTube) sont documentés
dans ce registre.
