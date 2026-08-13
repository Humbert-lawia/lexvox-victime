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

| Bloc | Contenu | Segment | Refait à chaque épisode ? |
|---|---|---|---|
| 1 | **Question du jour** — c'est le sujet et l'article, posés en question | `01-question` | ✏️ oui |
| 2 | **Présentation** — l'émission, le cabinet, l'avocat, la confidence | `02-presentation` | 🔒 **non — enregistré une fois** |
| 3 | **Annonce du débat** — Nathalie et Nicolas, et le lancement | `03-final` | 🔒 **non — enregistré une fois** |

Exemple de question d'accroche pour cette chaîne :

> Les gendarmes viennent de retenir votre permis sur le bord de la route. Que
> se passe-t-il dans les soixante-douze heures qui suivent ?

⚠️ Le paragraphe 4 dit que Nathalie et Nicolas **ne sont pas avocats** et
qu'ils sont **créés par le cabinet** — vérifié par l'outil. Noter aussi
qu'aucune spécialisation CNB n'est revendiquée dans cette matière :
l'introduction parle d'expérience, pas de titre.

<<<SCRIPT
{question}

« Permis en danger », le podcast du cabinet LEXVOX AVOCATS. {avocat}, qui
défend les conducteurs devant le tribunal correctionnel et le tribunal de
police.

Nathalie et Nicolas en débattent, d'après mon article. Ils ne sont pas
avocats, ce sont les deux voix de l'émission. C'est parti.
SCRIPT>>>
