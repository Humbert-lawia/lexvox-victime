# Script d'introduction — chaîne VICTIMES

Texte lu par **Me Patrice Humbert**, avec sa voix clonée dans **Voicebox**
(synthèse locale, sur le poste du cabinet — aucun texte ne sort de la machine).

Émission : **LEXVICTIME — le podcast du cabinet LEXVOX AVOCATS consacré au
droit des victimes d'accident et d'erreur médicale**.

Générer le texte d'un épisode :

```bash
python3 tools/voix_script.py --chaine victimes --slug <slug> \
  --question "…?" --sujet "la contre-visite médicale" \
  --segments ~/LEXVOX-PODCASTS/victimes/segments --moteur voicebox
```

Durée cible : **65 à 75 secondes** pour l'intro complète. Les trois blocs
verrouillés y pèsent environ 45 s, dits à l'identique dans les 24 épisodes.

## Structure imposée — c'est la marque de fabrique de la série

| Bloc | Contenu | Segment | Refait à chaque épisode ? |
|---|---|---|---|
| 1 | **Question du jour** — c'est le sujet et l'article, posés en question | `01-question` | ✏️ oui |
| 2 | **Présentation** — l'émission, le cabinet, l'avocat, la confidence | `02-presentation` | 🔒 **non — enregistré une fois** |
| 3 | **Annonce du débat** — Nathalie et Nicolas, et le lancement | `03-final` | 🔒 **non — enregistré une fois** |

Les trois blocs verrouillés sont **rigoureusement identiques** d'un épisode à
l'autre. Les resynthétiser à chaque fois les fait dériver et la signature
s'émousse : `--segments` les enregistre une seule fois par chaîne, puis les
réutilise. Ne pas fusionner ni ajouter de paragraphe — le découpage repose
sur cette structure et l'outil refuse toute autre.

## Trois corrections apportées à votre brouillon

Votre version disait, et il valait mieux ne pas l'enregistrer ainsi :

| Votre formulation | Pourquoi elle pose problème | Retenu |
|---|---|---|
| « spécialisé en dommage corporel **et en responsabilité médicale** » | « spécialiste » est un **titre protégé** (art. 21-1 loi n° 71-1130 ; décret n° 91-1197). Vérifié dans `index.html` : le certificat CNB porte sur le **dommage corporel** seul — le revendiquer aussi en responsabilité médicale serait inexact, répété 24 fois | « spécialisé en droit du dommage corporel » seul. La responsabilité médicale n'est plus citée comme titre |
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
| « spécialisé en droit du dommage corporel » | `index.html` — « Spécialiste en dommage corporel — Certificat CNB » |

ℹ️ **Une réserve à garder en tête.** Le texte dit « spécialisé en droit du
dommage corporel », sans nommer le certificat. C'est votre choix de
formulation et il est exact. Si vous vouliez un jour appuyer davantage, la
version longue existe : « titulaire du certificat de spécialisation du
Conseil national des barreaux en droit du dommage corporel » — plus lourde
d'environ 5 secondes, mais elle nomme une qualification officielle que la
plupart des confrères n'ont pas. Le sigle « CNB » seul est à éviter à l'oral :
trois lettres ne pèsent rien.

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

LEXVICTIME, le podcast du cabinet LEXVOX AVOCATS. Maître Patrice Humbert,
spécialisé en dommage corporel. Une confidence : ce n'est pas le dossier le
plus grave qui est le mieux indemnisé, c'est le mieux défendu.

Nathalie et Nicolas en débattent, d'après mon article. Ils ne sont pas
avocats, ce sont les deux voix de l'émission. C'est parti.
SCRIPT>>>
