# Script d'introduction — chaîne PERMIS

Texte lu par **Me Patrice Humbert**, avec sa voix clonée dans ElevenLabs.

Générer le texte d'un épisode :

```bash
python3 tools/voix_script.py --chaine permis --slug <slug> \
  --sujet "la contestation d'un éthylomètre" --sortie intro-permis-01-<slug>.txt
```

Durée cible à la lecture : **30 à 40 secondes**.

**Structure imposée — c'est la marque de fabrique de la série :**
1. une **question d'accroche**, dont la réponse est précisément l'article du
   jour (variable `{question}`, produite par `PROMPT-INTRO-ELEVENLABS.md`) ;
2. le **jingle verbal**, identique dans tous les épisodes de la chaîne — ne
   jamais le reformuler, c'est lui qui rend la série reconnaissable ;
3. l'annonce du sujet, la présentation de Nathalie et Nicolas avec la
   mention « voix de synthèse », et la relance « La réponse, tout de suite ».

Exemple de question d'accroche pour cette chaîne :
> Les gendarmes viennent de retenir votre permis sur le bord de la route. Que se passe-t-il dans les soixante-douze heures qui suivent ?

⚠️ La mention « voix de synthèse » est **obligatoire** et vérifiée par
l'outil. Ne la retirez pas. Noter aussi qu'aucune spécialisation CNB n'est
revendiquée dans cette matière : l'introduction parle d'expérience, pas de
titre.

<<<SCRIPT
{question}

Bienvenue dans « Permis en danger », le podcast du cabinet LEXVOX
AVOCATS. Je suis Maître Patrice Humbert, avocat au Barreau
d'Aix-en-Provence. Je défends les conducteurs depuis plus de vingt ans.

Aujourd'hui : {sujet}.

Cette émission est animée par Nathalie et Nicolas. Nathalie, la juriste, vous
explique le droit ; Nicolas, le journaliste, pose les questions que vous vous
posez. Ce sont deux voix de synthèse, créées par le cabinet pour rendre ces
sujets techniques accessibles ; l'analyse, elle, vient de mon article
« {titre} », que vous retrouvez sur notre site.

La réponse, tout de suite. Bonne écoute.
SCRIPT>>>
