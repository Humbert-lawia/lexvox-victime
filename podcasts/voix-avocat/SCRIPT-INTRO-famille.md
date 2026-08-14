# Script d'introduction — chaîne FAMILLE

Texte lu par **Me Cédrine Raybaud**, avec sa voix clonée dans **Voicebox** — c'est elle
qui signe les articles de `lexvox-divorce.com`, et elle **seule** présente
cette chaîne.

Émission : **Divorce & famille : parlons-en**. ⚠️ La chaîne victimes a été
rebaptisée **LEXVICTIME** ; si vous voulez une famille de titres cohérente
(LEXFAMILLE, LEXPERMIS…), dites-le et je répercute partout.

Générer le texte d'un épisode :

```bash
python3 tools/voix_script.py --chaine famille --slug <slug> \
  --question "…?" --sujet "la prestation compensatoire" \
  --segments ~/LEXVOX-PODCASTS/famille/segments --moteur voicebox
```

Durée cible à la lecture : **30 à 40 secondes**.

## Structure imposée — c'est la marque de fabrique de la série

| Bloc | Contenu | Segment | Refait à chaque épisode ? |
|---|---|---|---|
| 1 | **Question du jour** — c'est le sujet et l'article, posés en question | `01-question` | ✏️ oui |
| 2 | **Présentation** — l'émission, le cabinet, l'avocat, la confidence | `02-presentation` | 🔒 **non — enregistré une fois** |
| 3 | **Annonce du débat** — Nathalie et Nicolas, et le lancement | `03-final` | 🔒 **non — enregistré une fois** |

Exemple de question d'accroche pour cette chaîne :

> Vous divorcez après vingt ans de mariage. Qui a droit à une prestation
> compensatoire, et de combien ?

⚠️ Le paragraphe 4 dit que Nathalie et Nicolas **ne sont pas avocats** et
qu'ils sont **créés par le cabinet**. C'est vérifié par l'outil : sans cela,
l'auditeur peut croire qu'il écoute deux collaborateurs du cabinet.

<<<SCRIPT
{question}

« Divorce & famille : parlons-en », le podcast du cabinet LEXVOX AVOCATS.
Maître Cédrine Raybaud, spécialiste en droit de la famille, des personnes et
de leur patrimoine.

Nathalie et Nicolas en débattent, d'après mon article. Ils ne sont pas
avocats, ce sont les deux voix de l'émission. C'est parti.
SCRIPT>>>
