# Script d'introduction — chaîne PERMIS

Texte lu par **Me Patrice Humbert**, avec sa voix clonée dans **Voicebox**
(synthèse locale, sur le poste du cabinet).

Émission : **Permis en danger**. ⚠️ La chaîne victimes a été rebaptisée
**LEXVICTIMES** ; dites-le si vous voulez une famille de titres cohérente.

Générer le texte d'un épisode :

```bash
python3 tools/voix_script.py --chaine permis --slug <slug> \
  --question "…?" --sujet "la contestation d'un éthylomètre" \
  --segments ~/LEXVOX-PODCASTS/permis/segments --moteur voicebox
```

Durée cible à la lecture : **30 à 40 secondes**.

## Structure imposée — c'est la marque de fabrique de la série

| Paragraphe | Bloc | Segment | Refait à chaque épisode ? |
|---|---|---|---|
| 1 | **Question d'accroche**, dont la réponse est l'article du jour | `01-question` | ✏️ oui |
| 2 | **Jingle verbal** — nom de l'émission, cabinet, identité de l'avocat | `02-jingle` | 🔒 **non — enregistré une fois** |
| 3 | Sujet du jour et article dont il est tiré | `03-sujet` | ✏️ oui |
| 4-5 | Présentation de Nathalie et Nicolas, puis la relance | `04-final` | 🔒 **non — enregistré une fois** |

Exemple de question d'accroche pour cette chaîne :

> Les gendarmes viennent de retenir votre permis sur le bord de la route. Que
> se passe-t-il dans les soixante-douze heures qui suivent ?

⚠️ Le paragraphe 4 dit que Nathalie et Nicolas **ne sont pas avocats** et
qu'ils sont **créés par le cabinet** — vérifié par l'outil. Noter aussi
qu'aucune spécialisation CNB n'est revendiquée dans cette matière :
l'introduction parle d'expérience, pas de titre.

<<<SCRIPT
{question}

Bienvenue dans « Permis en danger », le podcast du cabinet LEXVOX
AVOCATS. Je suis Maître Patrice Humbert, avocat au Barreau
d'Aix-en-Provence. Je défends les conducteurs depuis plus de vingt ans.

Aujourd'hui : {sujet}. Tout part de mon article « {titre} », que vous
retrouvez sur le site du cabinet.

Cette émission est animée par Nathalie et Nicolas. Nathalie, la juriste, vous
explique le droit ; Nicolas, le journaliste, pose les questions que vous vous
posez. Ils ne sont pas avocats : ce sont les deux voix de l'émission, créées
par le cabinet pour rendre ces sujets techniques accessibles.

La réponse, tout de suite. Bonne écoute.
SCRIPT>>>
