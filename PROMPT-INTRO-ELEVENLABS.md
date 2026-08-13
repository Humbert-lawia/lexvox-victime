# PROMPT INTRO ELEVENLABS — analyser l'article, produire l'accroche, enregistrer la voix

> À copier dans une session Claude, une fois par épisode. Il produit les deux
> variables que le gabarit d'intro attend — la **question d'accroche** et le
> **sujet** — puis fabrique le texte final à faire lire par la voix clonée.
>
> Le reste de l'intro (jingle, présentation de Nathalie et Nicolas, mention
> « voix de synthèse », relance finale) est **invariant** : il vit dans
> `podcasts/voix-elevenlabs/SCRIPT-INTRO-<chaine>.md` et ne se réécrit pas.

---

## 1. La structure, et pourquoi elle ne bouge jamais

Chaque intro suit exactement cet ordre. C'est la marque de fabrique de la
série : l'auditeur qui revient doit reconnaître l'émission en trois secondes.

| # | Bloc | Variable ? |
|---|---|---|
| 1 | **Question d'accroche** — sa réponse est précisément l'article du jour | ✏️ à produire |
| 2 | **Jingle verbal** — nom de l'émission, cabinet, identité de l'avocat | 🔒 invariant |
| 3 | **Annonce du sujet** — « Aujourd'hui : … » | ✏️ à produire |
| 4 | **Présentation de Nathalie et Nicolas** + mention « voix de synthèse » | 🔒 invariant |
| 5 | **Relance** — « La réponse, tout de suite. Bonne écoute. » | 🔒 invariant |

La relance du bloc 5 renvoie à la question du bloc 1 : c'est ce qui fait
tenir l'ensemble. Une accroche dont l'article ne donne pas la réponse casse
la promesse dès le premier épisode.

`tools/voix_script.py` **refuse** un script qui ne commencerait pas par une
question, ou d'où le jingle, les deux prénoms ou la mention de transparence
auraient disparu. Il refuse aussi toute promesse de résultat.

---

## 2. Le prompt

```
Tu prépares l'introduction d'un épisode de podcast du cabinet LEXVOX AVOCATS.
Ta seule mission est de produire DEUX courts textes à partir d'un article :
la QUESTION d'accroche et le SUJET. Tu ne réécris rien d'autre.

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
Une à deux phrases, 140 à 220 caractères, qui se terminent par « ? ».
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

ÉTAPE 3 — ÉCRIRE LE SUJET
Un groupe nominal de 40 à 90 caractères qui complète « Aujourd'hui : … ».
Pas de phrase, pas de verbe conjugué, pas de majuscule initiale.
    « la contre-visite médicale demandée par votre assureur »
    « le calcul de la prestation compensatoire »
    « la rétention du permis après un contrôle d'alcoolémie »

ÉTAPE 4 — FABRIQUER LE TEXTE FINAL
    python3 tools/voix_script.py --chaine <chaîne> --slug <slug> \
        --question "<question>" --sujet "<sujet>" \
        --sortie ~/LEXVOX-PODCASTS/<chaîne>/intro/intro-<chaîne>-<NN>-<slug>.txt
L'outil injecte les blocs invariants et vérifie la structure. S'il refuse,
corrige la question ou le sujet — ne modifie JAMAIS le gabarit pour faire
passer un contrôle.

ÉTAPE 5 — RENDRE COMPTE
Affiche-moi : la question, le sujet, le texte final, son nombre de
caractères, et la durée de lecture estimée (environ 15 caractères par
seconde en diction posée). Si le texte dépasse 40 secondes estimées,
raccourcis la question — jamais les blocs invariants.
```

---

## 3. Réglages ElevenLabs

Le texte produit se colle tel quel dans ElevenLabs, sur la **voix clonée** de
l'avocat concerné — Me Humbert pour victimes et permis, Me Raybaud pour
famille, puisque c'est elle qui signe les articles de `lexvox-divorce.com`.

| Réglage | Valeur conseillée | Pourquoi |
|---|---|---|
| Modèle | le plus récent en multilingue français | la qualité du français a beaucoup progressé d'une version à l'autre |
| Stability | **plutôt élevée** | une intro est une signature : elle doit sonner pareil dans les 24 épisodes. Une valeur basse rend la diction expressive mais variable d'une prise à l'autre |
| Similarity | **élevée** | c'est votre voix qui porte la crédibilité ; on veut la reconnaître |
| Style / exagération | **bas** | l'emphase artificielle sonne « publicité », exactement ce qu'un avocat doit éviter |
| Speaker boost | activé | tenue plus stable sur les phrases longues |
| Vitesse | normale | ralentir donne un ton solennel qui vieillit mal |

Trois conseils de fabrication, qui comptent plus que les réglages :

1. **Générez le jingle une seule fois, et réutilisez-le.** Le bloc 2 est
   identique dans les 24 épisodes : le regénérer à chaque fois le fait varier
   légèrement, et la signature perd sa force. Vous pouvez le découper une
   fois pour toutes et ne faire varier que les blocs 1 et 3 — dites-le-moi
   si vous voulez que le montage l'assemble ainsi.
2. **Écoutez la prononciation des noms propres** au premier épisode :
   « Dintilhac », « Marignane », « Salon-de-Provence », « éthylomètre ». Si
   un mot passe mal, écrivez-le phonétiquement dans le texte source.
3. **Les nombres s'écrivent en toutes lettres.** L'outil le vérifie déjà pour
   le numéro de téléphone de l'outro ; faites-en autant dans la question.

---

## 4. Si vous voulez un vrai jingle musical

Le « jingle » ci-dessus est verbal. Si vous souhaitez en plus quelques
secondes de musique en tête d'épisode, deux points avant de s'y engager :

- **La licence.** Une musique déposée exige une licence commerciale couvrant
  la diffusion en podcast, y compris sur les plateformes. Une musique libre
  de droits mal vérifiée peut faire retirer les 72 épisodes. Choisissez une
  source dont la licence est écrite et archivée.
- **L'assemblage.** Le montage sait déjà enchaîner des segments : ajouter un
  fichier `jingle-<chaine>.mp3` en tête est une ligne de configuration. Dites
  le mot et je l'ajoute — en le plaçant AVANT l'intro, ce qui laisse votre
  règle « l'intro ElevenLabs précède toujours le débat » intacte.
