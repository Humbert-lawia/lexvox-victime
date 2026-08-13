# Script d'outro — chaîne FAMILLE

Texte lu par **Me Cédrine Raybaud**, avec sa voix clonée dans ElevenLabs
(variante Me Humbert plus bas si elle préfère ne pas prêter sa voix).

**Cet outro ne dépend pas de l'épisode** : une seule génération ElevenLabs
suffit pour les 24 épisodes de la chaîne. À enregistrer sous
`~/LEXVOX-PODCASTS/famille/outro/outro-famille.mp3`.

```bash
python3 tools/voix_script.py --bloc outro --chaine famille \
  --sortie ~/LEXVOX-PODCASTS/famille/outro/outro-famille.txt
```

Durée cible à la lecture : **25 à 35 secondes**.

⚠️ Texte verrouillé déontologiquement. Rappel des particularités de cette
matière : la première consultation est **payante** (30 min à tarif fixe), il
n'y a **pas de couverture nationale** annoncée, et **aucun honoraire de
résultat** n'est mentionné — ne pas importer les formules du dommage
corporel. Voir `podcasts/fiche-cabinet-famille.md`.

<<<SCRIPT
Maître Cédrine Raybaud à nouveau. Un divorce ou une séparation se prépare :
ne prenez pas seule, ou seul, les décisions qui engageront vos années à
venir.

Je vous reçois dans les bureaux du cabinet LEXVOX à Aix-en-Provence,
Salon-de-Provence, Arles et Marignane, ou à distance. La première
consultation dure trente minutes, à un tarif fixe annoncé lors de la prise de
rendez-vous ; les honoraires sont ensuite fixés par une convention signée à
l'avance.

Prenez rendez-vous sur le site du cabinet, ou appelez le zéro quatre, quatre-
vingt-dix, cinquante-quatre, cinquante-huit, dix. À bientôt.
SCRIPT>>>

---

## Variante si l'outro est dit par Me Humbert

Remplacer la première phrase par : « Maître Patrice Humbert, du cabinet
LEXVOX AVOCATS. » et « Je vous reçois » par « Ma consœur Maître Cédrine
Raybaud, spécialiste en droit de la famille, vous reçoit ».

## Si l'épisode traite de violences conjugales

Prévoir une seconde version de l'outro, à monter sur ces épisodes-là
uniquement, ouvrant par : « Si vous êtes en danger, appelez le 3919, ou le 17
en cas d'urgence immédiate. » Enregistrer sous
`outro-famille-violences.mp3` et la passer au montage via `--outro`.
