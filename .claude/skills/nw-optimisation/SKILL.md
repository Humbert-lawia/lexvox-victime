---
name: nw-optimisation
description: Methode d'optimisation NeuronWriter VALIDEE (run reel 2026-07-07, 62 -> 85 sur query procedurale) — "term-budget first + audit local", objectif plafond de la famille en 1-2 appels evaluate (>=90 famille indemnisation, >=85 famille procedure). OBLIGATOIRE pour TOUT flux qui score un contenu avec NeuronWriter : article-aivf (§5bis), pipeline WordPress (nw_eval_wp.py), refontes, routines automatiques. Requiert NEURONWRITER_API_KEY + egress app.neuronwriter.com.
---

# Optimisation NeuronWriter — méthode « term-budget first + audit local » (v2, VALIDÉE)

Méthode issue du NW-LAB (`PROTOCOLE-NW-LAB.md`) et **validée par un run réel
complet le 2026-07-07** sur la query K2 `a7e923cccd64fc29` (« deroule expertise
medicale », famille procédure, la plus dure du corpus) : **62/100 en 6 loops
aveugles → 85/100 dès le 1er evaluate d'un jet « sous contrat de termes »
(81), plafond 85 atteint en 11 appels puis confirmé par ~10 sondes à variable
unique** (historique intégral : `nw-lab/runs-a7e923cccd64fc29.jsonl`).
Elle remplace définitivement la boucle « rédiger → evaluate → deviner →
re-evaluate » (rendement historique : 15 loops pour 84, 6 loops pour 62).

## Règles absolues (héritées de CLAUDE.md et du pipeline)

1. **Aucun score inventé, jamais** : tout score vient de l'API et chaque appel
   est journalisé (`tools/nw_lab.py evaluate` le fait automatiquement). Le
   marqueur `<!-- NEURONWRITER SCORE: N query=<id> le AAAA-MM-JJ -->` porte
   TOUJOURS le dernier score API réel, même décevant.
2. Plancher de mots **1900** (2500 pilier) : contrainte ÉDITORIALE du gabarit —
   pas une contrainte NW (cf. loi n° 4 ci-dessous). Le volume monte si utile,
   ne descend jamais.
3. Si NeuronWriter est injoignable (clé absente ou egress bloqué — tester
   `python3 tools/neuronwriter.py list-projects`) : **stop**, signaler le
   blocage, ne pas publier. Ne pas contourner la politique réseau.

## Lois empiriques du scoreur (mesurées le 2026-07-07, sondes API à variable unique)

Ces propriétés ont été établies par des appels `evaluate` réels en ne changeant
qu'une variable à la fois. Elles dictent où investir l'effort :

1. **Le score est (quasi) une pure fonction de COUVERTURE** des termes
   recommandés dans title / meta desc / H1 / H2 / corps. C'est le seul levier
   qui a produit des points (+4 en densifiant H1 et H2).
2. **Aucune pénalité de sur-usage** : bourrage d'un terme ×6 → score inchangé.
   Ne JAMAIS dépenser un loop à « dé-bourrer » ; les excès signalés par
   l'audit local sont sans effet sur le score (les corriger seulement si le
   texte devient illisible).
3. **Le chrome nav/footer est ignoré** par le scoreur : inutile d'y placer des
   termes, inutile de l'élaguer.
4. **La longueur est neutre** : 2 465 mots utiles vs médiane concurrente 1 214
   → aucun coût, aucun gain. Ne pas gonfler ni couper pour NW.
5. **Les H2 comptent en RATIO, pas en somme** : ajouter un H2 pauvre en termes
   `h2` FAIT BAISSER le score (dilution mesurée). Peu de H2, très denses en
   termes recommandés ; chaque H2 doit consommer son quota du brief.
6. **Les formulations gigognes démultiplient la couverture** : « demander une
   expertise judiciaire » couvre à la fois « expertise judiciaire », « demander
   une expertise » et « expertise ». Les privilégier partout (H1, H2, corps).
7. **L'enrichissement chiffré/€ (hypothèse H4) est NEUTRE sur le score** —
   mesuré 85 → 85 sur query procédurale. Garder les fourchettes €, délais et
   barèmes pour le lecteur et l'E-E-A-T, pas pour NW. (La corrélation
   historique « chiffres → ≥90 » était confondue avec la famille de mot-clé.)
8. **Plafonds par famille de SERP, révisés** : les plafonds historiques 62-79
   de la famille « procédure/définition » reflétaient un DÉFAUT DE COUVERTURE
   (v1 62/100 : 5/17 termes h1, 5/31 h2, 11/53 extended), pas une limite dure.
   Plafond démontré famille procédure : **85**. Famille « indemnisation/
   montant/barème » : 84-100, viser ≥ 90. Un ≥ 90 sur famille procédure reste
   non démontré : ne pas le promettre, ne pas le poursuivre en loops aveugles.

## La séquence (S1 v2), dans l'ordre — budget : 2 appels `evaluate`

### 0. Qualifier le mot-clé (fixe l'objectif AVANT de rédiger)

Identifier la famille : « indemnisation / montant / barème X » → objectif ≥ 90 ;
« procédure / définition / comment se passe » → objectif 85 = plafond démontré.
Quand le sujet le permet, formuler le mot-clé côté « indemnisation/montant ».
La dérogation éventuelle < 85 se décide en connaissance de famille, pas après
10 loops.

### 1. Termes AVANT rédaction

```bash
python3 tools/neuronwriter.py new-query 49f477e9d390de9c "<keyword>"   # si query absente
python3 tools/nw_lab.py terms <query_id>       # cache nw-lab/terms-<query_id>.json
```

En tirer un **brief contractuel** : title et H1 couvrent le maximum de termes
`title`/`h1` (formulations gigognes) ; CHAQUE H2 reçoit sa dotation de termes
`h2` ; budget d'occurrences corps par terme `content_basic`/`content_extended`
(viser le min de `sugg_usage`, le max est sans enjeu — loi n° 2) ; toutes les
`entities` présentes au moins une fois.

### 2. Rédiger EN UNE PASSE sous contrat

Gabarit atelier habituel (hero, quick-answer, toc, ≥ 5 H2, ≥ 2 data-table,
≥ 1 SVG, juris Openlegi vérifiée, FAQ ≥ 6 synchronisée JSON-LD). Chaque H2
répond à une sous-question réelle ET consomme son quota de termes — ne PAS
créer de H2 « éditorial » vide de termes (loi n° 5). Couvrir aussi les clusters
hors intent victime présents dans les termes (CPAM, assureur, employeur…) dans
des H2/FAQ dédiés : c'est de la couverture, donc des points.

### 3. Audit LOCAL (zéro appel API) et patch unique

```bash
python3 tools/nw_lab.py audit nw-lab/terms-<query_id>.json actualites/<slug>.html
```

Corriger **tous les déficits** en une seule passe (chaque terme manquant
s'installe dans une phrase qui apporte une information ; ignorer les excès —
loi n° 2). Re-lancer l'audit jusqu'à couverture maximale compatible avec
l'éditorial ; cela ne coûte aucun appel API.

### 4. Scorer (1er appel), corriger une fois, scorer (2e appel)

```bash
python3 tools/nw_lab.py evaluate <query_id> actualites/<slug>.html --note "S1-loop1"
```

- **Objectif atteint** (≥ 90 indemnisation / ≥ 85 procédure) : terminé. Coller
  le marqueur `<!-- NEURONWRITER SCORE: N query=<id> le AAAA-MM-JJ -->`.
- **Sous l'objectif** : une seule passe corrective — densifier H1/H2 en termes
  manquants (levier n° 1 mesuré) + solder les déficits d'audit résiduels —
  puis 2e evaluate.
- **2 appels au même score + audit propre** : le plafond de la query est
  atteint. L'acter, le documenter dans le commit, décision de dérogation au
  flux appelant. NE PAS boucler à l'aveugle : au-delà de 2 appels identiques,
  le rendement marginal mesuré est nul (plateau 85 confirmé par 10 sondes).

### 5. Journal et traçabilité

`nw-lab/runs-<query>.jsonl` contient l'historique loop par loop (réel). Le
marqueur HTML porte TOUJOURS le dernier score API. Reporter le score dans
`queue-aivf.json` / tracker selon le flux appelant.

## Rattachement aux flux existants (OBLIGATOIRE — aucune boucle aveugle nulle part)

- `/article-aivf` §5bis : la boucle d'optimisation s'exécute selon CE skill
  (le seuil bloquant ≥ 85 et le marqueur QA restent inchangés).
- Pipeline WordPress (`PROMPT-PIPELINE-WP.md`, PR #9/#10) : même séquence, en
  scorant via `tools/nw_eval_wp.py` (page reconstituée) au lieu du fragment.
- Toute refonte/réécriture : commencer par `terms` + `audit` sur l'existant
  avant de toucher au texte (diagnostic de couverture = diagnostic du plafond).
- Routines automatiques (LEXVOX SEO Bot, LAWIA Pipeline, routine WP à venir) :
  leurs prompts doivent référencer ce skill ; toute session qui lit CLAUDE.md
  y est renvoyée.
