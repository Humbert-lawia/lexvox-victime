# Script d'introduction — chaîne FAMILLE

Texte lu par **Me Cédrine Raybaud**, avec sa voix clonée dans ElevenLabs —
c'est elle qui signe les articles de `lexvox-divorce.com`, l'introduction
doit donc être dite par elle. (Si Me Raybaud préfère ne pas prêter sa voix,
la variante en fin de fiche permet à Me Humbert de présenter l'émission au
nom du cabinet.)

Générer le texte d'un épisode :

```bash
python3 tools/voix_script.py --chaine famille --slug <slug> \
  --sujet "la prestation compensatoire" --sortie intro-famille-01-<slug>.txt
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
> Vous divorcez après vingt ans de mariage. Qui a droit à une prestation compensatoire, et de combien ?

⚠️ La mention « voix de synthèse » est **obligatoire** et vérifiée par
l'outil. Ne la retirez pas.

<<<SCRIPT
{question}

Bienvenue dans « Divorce & famille : parlons-en », le podcast du
cabinet LEXVOX AVOCATS. Je suis Maître Cédrine Raybaud, avocate au
Barreau d'Aix-en-Provence, spécialiste en droit de la famille.

Aujourd'hui : {sujet}.

Cette émission est animée par Nathalie et Nicolas. Nathalie, la juriste, vous
explique le droit ; Nicolas, le journaliste, pose les questions que vous vous
posez. Ce sont deux voix de synthèse, créées par le cabinet pour rendre ces
sujets techniques accessibles ; l'analyse, elle, vient de mon article
« {titre} », que vous retrouvez sur notre site.

La réponse, tout de suite. Bonne écoute.
SCRIPT>>>

---

## Variante si l'introduction est dite par Me Humbert

Remplacer la première phrase par : « Bonjour, je suis Maître Patrice Humbert,
du cabinet LEXVOX AVOCATS. Bienvenue dans "Divorce & famille : parlons-en". »
et, plus loin, « mon article » par « l'article de ma consœur Maître Cédrine
Raybaud, spécialiste en droit de la famille ».
