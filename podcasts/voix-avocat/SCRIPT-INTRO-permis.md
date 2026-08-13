# Script d'introduction — chaîne PERMIS

Le droit routier est traité par **l'associé** de Me Humbert, qui s'occupe
exclusivement des victimes. C'est donc l'associé qui présente cette chaîne :
son nom se passe en paramètre, il n'est pas écrit en dur dans le gabarit.

```bash
--avocat "Maître Prénom Nom"
```

Texte lu avec la voix clonée de cet avocat dans **Voicebox** (synthèse
locale, sur le poste du cabinet).

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
| 1 | **Question du jour** — c'est le sujet et l'article, posés en question | `01-question` | ✏️ oui |
| 2 | **Présentation** — l'émission, le cabinet, l'avocat, la confidence | `02-presentation` | 🔒 **non — enregistré une fois** |
| 3 | Sujet et article dont il est tiré | `03-sujet` | ✏️ oui |
| 4 | Nathalie et Nicolas, puis la relance | `04-final` | 🔒 **non — enregistré une fois** |

Exemple de question d'accroche pour cette chaîne :

> Les gendarmes viennent de retenir votre permis sur le bord de la route. Que
> se passe-t-il dans les soixante-douze heures qui suivent ?

⚠️ Le paragraphe 4 dit que Nathalie et Nicolas **ne sont pas avocats** et
qu'ils sont **créés par le cabinet** — vérifié par l'outil. Noter aussi
qu'aucune spécialisation CNB n'est revendiquée dans cette matière :
l'introduction parle d'expérience, pas de titre.

<<<SCRIPT
{question}

Bienvenue dans « Permis en danger », le podcast du cabinet LEXVOX AVOCATS
consacré à la défense du permis de conduire. Je suis {avocat}, du Barreau
d'Aix-en-Provence. Je défends les conducteurs devant le tribunal
correctionnel et le tribunal de police.

Aujourd'hui, {sujet}, d'après mon article « {titre} ».

Pour en débattre, Nathalie et Nicolas. Ils ne sont pas avocats : ce sont les
deux voix de l'émission, créées par le cabinet. La réponse, tout de suite.
SCRIPT>>>
