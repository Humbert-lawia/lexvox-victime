# Script d'introduction — chaîne VICTIMES

Texte lu par **Me Patrice Humbert**, avec sa voix clonée dans ElevenLabs.
Seules les variables `{titre}` et `{sujet}` changent d'un épisode à l'autre.

Générer le texte d'un épisode :

```bash
python3 tools/intro_script.py --chaine victimes --slug <slug> \
  --sujet "la contre-visite médicale" --sortie intro-victimes-01-<slug>.txt
```

Durée cible à la lecture : **25 à 35 secondes**. Ne pas allonger : l'épisode
complet doit rester sous cinq minutes, intro comprise.

⚠️ La mention « voix de synthèse » est **obligatoire** et vérifiée par
l'outil : sans elle, l'auditeur peut croire que les deux animateurs sont des
avocats du cabinet. Ne la retirez pas.

<<<SCRIPT
Bonjour, je suis Maître Patrice Humbert, avocat au Barreau d'Aix-en-Provence,
spécialiste en droit du dommage corporel. Bienvenue dans « Victimes : vos
droits », le podcast du cabinet LEXVOX AVOCATS.

Aujourd'hui, nous décryptons pour vous un sujet essentiel : {sujet}.

Cette émission est animée par Nathalie et Nicolas. Nathalie, la juriste, vous
explique le droit ; Nicolas, le journaliste, pose les questions que vous vous
posez. Ce sont deux voix de synthèse, créées par le cabinet pour rendre ces
sujets techniques accessibles ; l'analyse, elle, vient de mon article
« {titre} », que vous retrouvez sur notre site.

Je vous souhaite une bonne écoute.
SCRIPT>>>
