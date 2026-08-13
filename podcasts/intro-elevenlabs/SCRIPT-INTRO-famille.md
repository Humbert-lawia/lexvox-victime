# Script d'introduction — chaîne FAMILLE

Texte lu par **Me Cédrine Raybaud**, avec sa voix clonée dans ElevenLabs —
c'est elle qui signe les articles de `lexvox-divorce.com`, l'introduction
doit donc être dite par elle. (Si Me Raybaud préfère ne pas prêter sa voix,
la variante en fin de fiche permet à Me Humbert de présenter l'émission au
nom du cabinet.)

Générer le texte d'un épisode :

```bash
python3 tools/intro_script.py --chaine famille --slug <slug> \
  --sujet "la prestation compensatoire" --sortie intro-famille-01-<slug>.txt
```

Durée cible à la lecture : **25 à 35 secondes**.

⚠️ La mention « voix de synthèse » est **obligatoire** et vérifiée par
l'outil. Ne la retirez pas.

<<<SCRIPT
Bonjour, je suis Maître Cédrine Raybaud, avocate au Barreau d'Aix-en-Provence,
spécialiste en droit de la famille. Bienvenue dans « Divorce & famille :
parlons-en », le podcast du cabinet LEXVOX AVOCATS.

Aujourd'hui, nous prenons le temps d'expliquer un sujet qui revient sans
cesse dans mon cabinet : {sujet}.

Pour en parler, je laisse la parole à Élise et Thomas. Élise vous explique le
droit, Thomas pose les questions que vous vous posez. Ce sont deux voix de
synthèse, créées par le cabinet pour rendre ces sujets techniques
accessibles ; l'analyse, elle, vient de mon article « {titre} », que vous
retrouvez sur notre site.

Je vous souhaite une bonne écoute.
SCRIPT>>>

---

## Variante si l'introduction est dite par Me Humbert

Remplacer la première phrase par : « Bonjour, je suis Maître Patrice Humbert,
du cabinet LEXVOX AVOCATS. Bienvenue dans "Divorce & famille : parlons-en". »
et, plus loin, « mon article » par « l'article de ma consœur Maître Cédrine
Raybaud, spécialiste en droit de la famille ».
