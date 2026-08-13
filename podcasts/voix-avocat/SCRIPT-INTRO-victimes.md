# Script d'introduction — chaîne VICTIMES

Texte lu par **Me Patrice Humbert**, avec sa voix clonée dans **Voicebox**
(synthèse locale, sur le poste du cabinet — aucun texte ne sort de la machine).

Émission : **LEXVICTIME — le podcast du cabinet LEXVOX AVOCATS consacré au
droit des victimes d'accident et d'erreur médicale**.

> ⚠️ **Un point à trancher** : vous avez écrit « LEXVICTIMES » puis
> « LEXVICTIME ». La marque déposée qui figure sur le site est
> **LEXVICTIME®** — c'est celle retenue ici. Un mot de vous et je bascule
> tout sur le pluriel : c'est un seul endroit à changer.

Générer le texte d'un épisode :

```bash
python3 tools/voix_script.py --chaine victimes --slug <slug> \
  --question "…?" --sujet "la contre-visite médicale" \
  --segments ~/LEXVOX-PODCASTS/victimes/segments --moteur voicebox
```

Durée cible : **55 à 65 secondes** pour l'intro complète (voir le décompte
plus bas — le jingle long y pèse pour la moitié).

## Structure imposée — c'est la marque de fabrique de la série

| Paragraphe | Bloc | Segment | Refait à chaque épisode ? |
|---|---|---|---|
| 1 | **Question d'accroche**, dont la réponse est l'article du jour | `01-question` | ✏️ oui |
| 2 | **Jingle verbal** — émission, cabinet, identité, promesse éditoriale | `02-jingle` | 🔒 **non — enregistré une fois** |
| 3 | Sujet du jour et article dont il est tiré | `03-sujet` | ✏️ oui |
| 4-5 | Présentation de Nathalie et Nicolas, puis la relance | `04-final` | 🔒 **non — enregistré une fois** |

Les deux blocs verrouillés sont **rigoureusement identiques** d'un épisode à
l'autre. Les resynthétiser à chaque fois les fait dériver et la signature
s'émousse : `--segments` les enregistre une seule fois par chaîne, puis les
réutilise. Ne pas fusionner ni ajouter de paragraphe — le découpage repose
sur cette structure et l'outil refuse toute autre.

## Trois corrections apportées à votre brouillon

Votre version disait, et il valait mieux ne pas l'enregistrer ainsi :

| Votre formulation | Pourquoi elle pose problème | Retenu |
|---|---|---|
| « spécialisé en dommage corporel **et en responsabilité médicale** » | « spécialiste » est un **titre protégé** (art. 21-1 loi n° 71-1130 ; décret n° 91-1197). Vérifié dans `index.html` : le certificat CNB porte sur le **dommage corporel** seul — le revendiquer aussi en responsabilité médicale serait inexact, répété 24 fois | le **certificat de spécialisation du Conseil national des barreaux en droit du dommage corporel**, énoncé en toutes lettres ; la responsabilité médicale reste décrite comme **pratique**, dans la phrase suivante |
| « une victime bien informée a **tous les moyens de gagner** » | promesse de résultat implicite, la formulation la plus surveillée en publicité d'avocat | voir la chute ci-dessous : même audace, aucun engagement sur l'issue |

### La chute du jingle — cinq versions

C'est la dernière phrase que l'auditeur retient, et elle est dite 24 fois.
Aucune ne promet de résultat : toutes déplacent la promesse de **l'issue du
dossier** vers **le déséquilibre d'information**, qui est réel et vérifiable.

| | Version | Ton |
|---|---|---|
| **1** | *« Et je vais vous faire une confidence : ce n'est pas le dossier le plus grave qui est le mieux indemnisé, c'est le mieux défendu. »* — **RETENUE, choix de Me Humbert du 2026-08-13** | la plus forte : elle dit en une phrase pourquoi l'assistance change l'issue |
| 2 | *« Et je vais vous faire une confidence : en face, personne ne vous dira jamais ce que vous êtes en droit de demander. Alors ce sera moi. »* | audacieux, personnel ; justifie l'existence de l'émission |
| 3 | *« L'assureur, lui, a ses experts, ses médecins et ses avocats. Vous, vous avez des droits — encore faut-il savoir lesquels. »* | pose le rapport de force, très factuel |
| 4 | *« Retenez ceci : face à un assureur, ce que vous ignorez ne se retourne jamais contre lui. »* | le plus court, le plus tranchant |
| 5 | *« L'indemnisation, ça ne se demande pas poliment. Ça se prépare. »* | sec, mémorable, se retient dès le premier épisode |

La formule retenue énonce une **règle générale sur la conduite d'un dossier**,
au présent de vérité générale, sans « vous » ni promesse adressée à
l'auditeur : c'est ce qui la distingue d'un engagement de résultat. Elle ne
doit donc jamais être reformulée en « votre dossier sera mieux indemnisé ».

### Ce que le jingle met en avant, et d'où ça vient

| Affirmation | Source |
|---|---|
| « plus de vingt ans » | `index.html` — « spécialisé depuis plus de 20 ans » |
| « la seule défense des victimes » | `index.html` — « défense exclusive des victimes de dommages corporels et de responsabilité médicale » |
| « certificat de spécialisation … en droit du dommage corporel » | `index.html` — « Spécialiste en dommage corporel — Certificat CNB » |
| « des centaines de dossiers » | `index.html` — « des centaines de dossiers traités » |

Le titre est énoncé **en toutes lettres** plutôt que par le sigle : à l'oral,
« CNB » est lu comme trois lettres et perd tout son poids, alors que
« le certificat de spécialisation du Conseil national des barreaux » sonne
pour ce qu'il est — une qualification officielle, que la plupart des
confrères n'ont pas.

> ⚠️ **Point tranché par Me Humbert le 2026-08-13** : la spécialisation CNB
> et la défense *exclusive* des victimes sont bien à revendiquer ; le permis
> est traité par un associé. Reste une contradiction **dans vos sites**, pas
> dans ce gabarit : `lexvox-permis.com` présente Me Humbert avec « plus de
> 20 ans d'expérience exclusive en droit pénal routier » et écrit
> « Me Humbert examine systématiquement la régularité de la procédure ». Les
> deux « exclusive » ne peuvent pas être vraies ensemble. À arbitrer avant
> d'enregistrer la chaîne permis — voir l'avertissement en tête de
> `SCRIPT-INTRO-permis.md`.

> ℹ️ **Non retenu, à votre main.** Votre site vous présente aussi comme
> « premier avocat certifié en intelligence artificielle de France ». C'est
> distinctif, mais hors sujet dans une émission sur le droit des victimes, et
> la formule « premier … de France » se rapproche de la mention comparative
> que proscrit le RIN art. 10.2. Dites-le si vous la voulez quand même.

## Variantes pour présenter Nathalie et Nicolas

Le point à préserver n'est pas une phrase, c'est le fait qu'on ne puisse pas
les prendre pour deux collaborateurs du cabinet. L'outil accepte n'importe
laquelle de ces formulations :

1. **Retenue ci-dessous** — « Ils ne sont pas avocats : ce sont les deux voix
   de l'émission, créées par le cabinet. »
2. Plus imagée — « Ils ne portent pas la robe, ils portent vos questions :
   ce sont les deux voix de l'émission, créées par le cabinet. »
3. Plus directe — « Ni l'un ni l'autre n'est avocat. Ce sont les deux voix
   que le cabinet a créées pour rendre ces sujets écoutables. »
4. Plus chaleureuse — « Aucun des deux n'est avocat, et c'est tout l'intérêt :
   ils posent les questions qu'un client n'ose pas toujours poser. Ce sont
   les deux voix de l'émission, créées par le cabinet. »
5. La plus sobre — « Nathalie et Nicolas ne plaident pas, ils expliquent :
   ce sont les deux voix de l'émission, créées par le cabinet. »

ℹ️ Le nom « Humbert » a un h muet : envoyé tel quel au moteur vocal, il est
souvent articulé. `voix_script.py` écrit donc **« Imbert »** dans le texte
lu — et seulement là ; ce gabarit et les métadonnées gardent l'orthographe
exacte.

<<<SCRIPT
{question}

Bienvenue dans LEXVICTIME, le podcast du cabinet LEXVOX AVOCATS consacré au
droit des victimes d'accident et d'erreur médicale. Je suis Maître Patrice
Humbert, avocat au Barreau d'Aix-en-Provence, titulaire du certificat de
spécialisation du Conseil national des barreaux en droit du dommage corporel.
Depuis plus de vingt ans, je consacre mon activité à la seule défense des
victimes — dommage corporel et responsabilité médicale — face aux compagnies
d'assurance. Et je vais vous faire une confidence : ce n'est pas le dossier le
plus grave qui est le mieux indemnisé, c'est le mieux défendu.

Aujourd'hui : {sujet}. Tout part de mon article « {titre} », que vous
retrouvez sur le site du cabinet.

Pour en débattre, vos deux podcasteurs préférés : Nathalie et Nicolas.
Nathalie, la juriste, vous explique le droit ; Nicolas, le journaliste, pose
les questions que vous vous posez. Ils ne sont pas avocats : ce sont les deux
voix de l'émission, créées par le cabinet.

La réponse, tout de suite. Bonne écoute.
SCRIPT>>>

---

## Version resserrée, si l'intro vous paraît longue

Le jingle ci-dessus fait environ **37 secondes**, ce qui porte l'intro
complète à près de 90 secondes — sur un épisode de cinq minutes, presque un
tiers du temps avant d'entrer dans le sujet. Cette variante garde les deux
arguments qui portent (le certificat et les vingt ans) et tombe à environ
**22 secondes** :

> Bienvenue dans LEXVICTIME, le podcast du cabinet LEXVOX AVOCATS consacré
> au droit des victimes d'accident et d'erreur médicale. Je suis Maître
> Patrice Humbert, avocat au Barreau d'Aix-en-Provence, titulaire du
> certificat de spécialisation du Conseil national des barreaux en droit du
> dommage corporel. Depuis plus de vingt ans, je ne défends que des victimes
> face aux compagnies d'assurance — et une victime bien informée ne signe
> pas n'importe quoi.

Rappel de proportion : le jingle est dit **à chaque épisode**. Quinze
secondes de trop, ce sont dix-huit minutes d'antenne sur les 72 épisodes.
