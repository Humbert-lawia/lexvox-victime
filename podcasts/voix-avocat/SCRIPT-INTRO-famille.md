# Script d'introduction — chaîne FAMILLE

Texte lu par **Me Cédrine Raybaud**, avec sa voix clonée dans **Voicebox** —
c'est elle qui signe les articles de `lexvox-divorce.com`, l'introduction
doit donc être dite par elle. (Si Me Raybaud préfère ne pas prêter sa voix,
la variante en fin de fiche permet à Me Humbert de présenter l'émission au
nom du cabinet.)

Émission : **Divorce & famille : parlons-en**. ⚠️ La chaîne victimes a été
rebaptisée **LEXVICTIMES** ; si vous voulez une famille de titres cohérente
(LEXFAMILLE, LEXPERMIS…), dites-le et je répercute partout.

Générer le texte d'un épisode :

```bash
python3 tools/voix_script.py --chaine famille --slug <slug> \
  --question "…?" --sujet "la prestation compensatoire" \
  --segments ~/LEXVOX-PODCASTS/famille/segments --moteur voicebox
```

Durée cible à la lecture : **30 à 40 secondes**.

## Structure imposée — c'est la marque de fabrique de la série

| Paragraphe | Bloc | Segment | Refait à chaque épisode ? |
|---|---|---|---|
| 1 | **Question d'accroche**, dont la réponse est l'article du jour | `01-question` | ✏️ oui |
| 2 | **Jingle verbal** — nom de l'émission, cabinet, identité de l'avocate | `02-jingle` | 🔒 **non — enregistré une fois** |
| 3 | Sujet du jour et article dont il est tiré | `03-sujet` | ✏️ oui |
| 4-5 | Présentation de Nathalie et Nicolas, puis la relance | `04-final` | 🔒 **non — enregistré une fois** |

Exemple de question d'accroche pour cette chaîne :

> Vous divorcez après vingt ans de mariage. Qui a droit à une prestation
> compensatoire, et de combien ?

⚠️ Le paragraphe 4 dit que Nathalie et Nicolas **ne sont pas avocats** et
qu'ils sont **créés par le cabinet**. C'est vérifié par l'outil : sans cela,
l'auditeur peut croire qu'il écoute deux collaborateurs du cabinet.

<<<SCRIPT
{question}

Bienvenue dans « Divorce & famille : parlons-en », le podcast du
cabinet LEXVOX AVOCATS. Je suis Maître Cédrine Raybaud, avocate au
Barreau d'Aix-en-Provence, spécialiste en droit de la famille.

Aujourd'hui : {sujet}. Tout part de mon article « {titre} », que vous
retrouvez sur le site du cabinet.

Cette émission est animée par Nathalie et Nicolas. Nathalie, la juriste, vous
explique le droit ; Nicolas, le journaliste, pose les questions que vous vous
posez. Ils ne sont pas avocats : ce sont les deux voix de l'émission, créées
par le cabinet pour rendre ces sujets techniques accessibles.

La réponse, tout de suite. Bonne écoute.
SCRIPT>>>

---

## Variante si l'introduction est dite par Me Humbert

Remplacer la première phrase par : « Bonjour, je suis Maître Patrice Humbert,
du cabinet LEXVOX AVOCATS. Bienvenue dans "Divorce & famille : parlons-en". »
et, plus loin, « mon article » par « l'article de ma consœur Maître Cédrine
Raybaud, spécialiste en droit de la famille ».
