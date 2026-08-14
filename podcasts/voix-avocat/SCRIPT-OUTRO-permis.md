# Script d'outro — chaîne PERMIS

Le droit routier est traité par **l'associé** de Me Humbert, qui s'occupe
exclusivement des victimes. C'est donc lui qui dit cet outro, avec sa voix
clonée dans **Voicebox** (synthèse locale). Son nom se passe en paramètre :
`--avocat "Maître Prénom Nom"`.

**Cet outro ne dépend pas de l'épisode** : une seule prise Voicebox
suffit pour les 24 épisodes de la chaîne. À enregistrer sous
`~/LEXVOX-PODCASTS/permis/outro/outro-permis.mp3`.

```bash
python3 tools/voix_script.py --bloc outro --chaine permis \
  --sortie ~/LEXVOX-PODCASTS/permis/outro/outro-permis.txt
```

Durée cible à la lecture : **25 à 35 secondes**.

⚠️ Texte verrouillé déontologiquement. Particularités de cette matière :
première consultation **payante**, **aucune spécialisation CNB** revendiquée
en droit routier (expérience seulement), et **aucune promesse** de conserver
le permis — on parle d'analyse de la procédure et d'options de défense. Voir
`podcasts/fiche-cabinet-permis.md`.

<<<SCRIPT
{avocat} à nouveau. Dans ce domaine, je vous le redis : les
délais sont très courts, et chaque jour qui passe ferme des options de
défense.

J'analyse votre procès-verbal et la régularité de la procédure lors d'une
première consultation de trente minutes, à un tarif fixe annoncé lors de la
prise de rendez-vous. Les honoraires sont ensuite fixés par une convention
signée à l'avance, avec une part fixe et un complément au résultat. Le
cabinet vous reçoit à Aix-en-Provence, Salon-de-Provence, Arles et Marignane,
et répond sous vingt-quatre heures.

Prenez contact sur le site du cabinet, ou appelez le zéro quatre, quatre-
vingt-dix, cinquante-quatre, cinquante-huit, dix. À bientôt.
SCRIPT>>>
