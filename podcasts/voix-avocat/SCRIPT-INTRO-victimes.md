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
| « spécialisé en dommage corporel **et en responsabilité médicale** » | « spécialiste » est un **titre protégé** (art. 21-1 loi n° 71-1130 ; décret n° 91-1197). Le certificat CNB du cabinet porte sur le **dommage corporel** seul — le revendiquer en responsabilité médicale serait inexact, répété 24 fois | « spécialiste en droit du dommage corporel », la responsabilité médicale devenant une **pratique** décrite, pas un titre |
| « je m'occupe **exclusivement** des victimes » | contredit la chaîne permis, où vous défendez des conducteurs. La publicité de l'avocat doit être **sincère et véridique** (RIN art. 10.2) | « je défends des victimes face aux compagnies d'assurance » |
| « une victime bien informée a **tous les moyens de gagner** » | promesse de résultat implicite, la formulation la plus surveillée en publicité d'avocat | « une victime bien informée ne signe pas n'importe quoi » — même énergie, aucun engagement sur l'issue |

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
Humbert, avocat au Barreau d'Aix-en-Provence, spécialiste en droit du dommage
corporel, et je consacre l'essentiel de mon activité à la réparation du
dommage corporel et à la responsabilité médicale. Depuis plus de vingt ans,
je défends des victimes face aux compagnies d'assurance. Et je vais vous
faire une confidence : une victime bien informée ne signe pas n'importe quoi.

Aujourd'hui : {sujet}. Tout part de mon article « {titre} », que vous
retrouvez sur le site du cabinet.

Pour en débattre, vos deux podcasteurs préférés : Nathalie et Nicolas.
Nathalie, la juriste, vous explique le droit ; Nicolas, le journaliste, pose
les questions que vous vous posez. Ils ne sont pas avocats : ce sont les deux
voix de l'émission, créées par le cabinet.

La réponse, tout de suite. Bonne écoute.
SCRIPT>>>

---

## Version courte du jingle, si l'intro vous paraît longue

Le jingle ci-dessus fait environ **30 secondes** à lui seul, ce qui porte
l'intro complète à près d'une minute — sur un épisode de cinq minutes, c'est
un cinquième du temps avant que le sujet ne commence. Variante à environ
18 secondes, si vous préférez entrer plus vite dans le vif :

> Bienvenue dans LEXVICTIME, le podcast du cabinet LEXVOX AVOCATS consacré
> au droit des victimes d'accident et d'erreur médicale. Je suis Maître
> Patrice Humbert, spécialiste en droit du dommage corporel. Depuis plus de
> vingt ans, je défends des victimes face aux assureurs — et une victime
> bien informée ne signe pas n'importe quoi.
