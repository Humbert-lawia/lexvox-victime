# Script d'introduction — chaîne PERMIS

Texte lu par **Me Patrice Humbert**, avec sa voix clonée dans ElevenLabs.

Générer le texte d'un épisode :

```bash
python3 tools/intro_script.py --chaine permis --slug <slug> \
  --sujet "la contestation d'un éthylomètre" --sortie intro-permis-01-<slug>.txt
```

Durée cible à la lecture : **25 à 35 secondes**.

⚠️ La mention « voix de synthèse » est **obligatoire** et vérifiée par
l'outil. Ne la retirez pas. Noter aussi qu'aucune spécialisation CNB n'est
revendiquée dans cette matière : l'introduction parle d'expérience, pas de
titre.

<<<SCRIPT
Bonjour, je suis Maître Patrice Humbert, avocat au Barreau d'Aix-en-Provence.
Je défends les conducteurs depuis plus de vingt ans. Bienvenue dans « Permis
en danger », le podcast du cabinet LEXVOX AVOCATS.

Aujourd'hui, un sujet où chaque jour compte : {sujet}.

Pour en parler, je laisse la parole à Nathalie et Nicolas. Nathalie vous explique le
droit, Nicolas pose les questions que vous vous posez. Ce sont deux voix de
synthèse, créées par le cabinet pour rendre ces sujets techniques
accessibles ; l'analyse, elle, vient de mon article « {titre} », que vous
retrouvez sur notre site.

Je vous souhaite une bonne écoute.
SCRIPT>>>
