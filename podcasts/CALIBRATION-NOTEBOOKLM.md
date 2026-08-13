# Carnet de calibration NotebookLM

Rempli par l'agent computer use pendant le **MODE PILOTE** de chaque chaîne
(remplace l'apprentissage par démonstration à l'écran, abandonné le
2026-08-13 : une génération dure ~10 min, trop long à montrer en direct).
Référentiel d'interface attendu : `PROMPT-PODCAST-NOTEBOOKLM.md`.

## Constats (à remplir au premier pilote, mettre à jour si l'UI change)

| Point | Attendu (référentiel) | Constaté (date + valeur) |
|---|---|---|
| Libellé bouton création (Écran A) | [+ Créer] / [Create new] | |
| Libellés types de source (Écran B) | [Site web], [Texte copié] | |
| Choix de FORMAT présent (D1) ? | Débat disponible ? | |
| Choix de DURÉE présent (D2) ? | Plus court disponible en FR ? | **à vérifier en priorité** — voir écart n° 1 |
| Limite du champ D3 | ~500 caractères | |
| Texte de personnalisation entier accepté ? | oui (fin visible) | |
| Extension du fichier téléchargé | .wav ou .m4a | **2026-08-13 : `.m4a`** — AAC 257 kb/s, stéréo, 44,1 kHz |
| Durée réelle de génération | ~10 min | |
| Durée de l'épisode pilote | 2:00–5:30 visé | **2026-08-13 : 14 min 35** (875,5 s) |
| Quota constaté (msg éventuel) | ~3/j gratuit, ~20/j payant | |

## Écarts constatés avec le référentiel

**1. La consigne de durée écrite dans le champ n'est pas suivie.** La
personnalisation demandait « Moins de 5 min » ; l'épisode rendu fait **14 min
35**, soit près de trois fois la cible. Le texte n'est donc pas le bon levier.

→ **À vérifier au prochain épisode** : le dialogue « Personnaliser » comporte-t-il
un choix de DURÉE (D2 : *Plus court* / *Shorter*) en français ? Le référentiel
le donne comme parfois absent. S'il existe, c'est lui qu'il faut utiliser ; le
laisser sur « Par défaut » explique le résultat. Sinon, la durée n'est pas
pilotable et il faut en tirer les conséquences éditoriales.

*Conséquence sur l'épisode pilote : durée acceptée à titre exceptionnel par Me
Humbert (2026-08-13). La consigne « Moins de 5 min » reste en vigueur pour la
suite.*

**2. Qualité technique du rendu : conforme.** −17,5 LUFS, vrai pic −1,9 dBFS,
LRA 5,5 LU, aucun silence dans tout le fichier, décroissance naturelle sur la
dernière demi-seconde. Le format AAC/M4A traverse la chaîne de montage sans
réserve.

## Historique des pilotes

| Date | Chaîne | Slug pilote | Verdict QA humaine |
|---|---|---|---|
| 2026-08-13 | victimes | `10-conseils-pour-reussir-son-expertise` | débat reçu ; écoute de la conclusion en cours (orientation vers l'avocat à confirmer) |
