# Script d'introduction — chaîne VICTIMES

Texte lu par **Me Patrice Humbert**, avec sa voix clonée dans ElevenLabs.
Seules les variables `{titre}` et `{sujet}` changent d'un épisode à l'autre.

Générer le texte d'un épisode :

```bash
python3 tools/voix_script.py --chaine victimes --slug <slug> \
  --sujet "la contre-visite médicale" --sortie intro-victimes-01-<slug>.txt
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
> Votre assureur vous convoque à une contre-visite médicale. Avez-vous le droit de refuser d'y aller ? Ne pas allonger : l'épisode
complet doit rester sous cinq minutes, intro comprise.

⚠️ La mention « voix de synthèse » est **obligatoire** et vérifiée par
l'outil : sans elle, l'auditeur peut croire que les deux animateurs sont des
avocats du cabinet. Ne la retirez pas.

<<<SCRIPT
{question}

Bienvenue dans « Victimes : vos droits », le podcast du cabinet
LEXVOX AVOCATS. Je suis Maître Patrice Humbert, avocat au Barreau
d'Aix-en-Provence, spécialiste en droit du dommage corporel.

Aujourd'hui : {sujet}.

Cette émission est animée par Nathalie et Nicolas. Nathalie, la juriste, vous
explique le droit ; Nicolas, le journaliste, pose les questions que vous vous
posez. Ce sont deux voix de synthèse, créées par le cabinet pour rendre ces
sujets techniques accessibles ; l'analyse, elle, vient de mon article
« {titre} », que vous retrouvez sur notre site.

La réponse, tout de suite. Bonne écoute.
SCRIPT>>>
