---
name: nw-optimisation
description: Boucle d'optimisation NeuronWriter "term-budget first + audit local" pour atteindre le score maximal en 1-2 appels evaluate (objectif >=90, plancher 85). A utiliser par TOUT flux qui score un contenu avec NeuronWriter (article-aivf, pipeline WP, refontes) a la place des loops aveugles rediger-scorer-deviner. Requiert NEURONWRITER_API_KEY + egress app.neuronwriter.com (environnement "Neurowriter auto AIVF cloud").
---

# Optimisation NeuronWriter — méthode « term-budget first + audit local »

Méthode issue de l'expérimentation NW-LAB (2026-07-07, `PROTOCOLE-NW-LAB.md`,
demande de Me Humbert : ≥ 90 systématique, viser ~95, minimum de cycles).
Elle remplace la boucle historique « rédiger → evaluate → deviner → re-evaluate »
(rendement mesuré : 15 loops pour 84, 6 loops pour 62).

> **STATUT DE VALIDATION : EN COURS.** Les runs réels sont journalisés dans
> `nw-lab/runs-<query>.jsonl` et le verdict dans `PROTOCOLE-NW-LAB.md` §4.
> Tant que le verdict n'est pas « validé », les flux appelants gardent leur
> seuil bloquant ≥ 85 inchangé ; ce skill décrit la méthode à appliquer et
> sera mis à jour (scores mesurés, recette ajustée) à l'issue des runs.

## Règles absolues (héritées de CLAUDE.md et du pipeline)

1. **Aucun score inventé, jamais** : tout score vient de l'API et chaque appel
   est journalisé (`tools/nw_lab.py evaluate` le fait automatiquement).
2. Plancher de mots **1900** (2500 pilier) : le volume monte si utile, ne
   descend jamais.
3. Si NeuronWriter est injoignable (clé absente ou egress bloqué — tester
   `python3 tools/neuronwriter.py list-projects`) : **stop**, signaler le
   blocage, ne pas publier. Ne pas contourner la politique réseau.

## La séquence (S1), dans l'ordre — budget : 2 appels `evaluate`, 3 en cas de H4

### 0. Choisir/qualifier le mot-clé (levier n° 1 sur le score atteignable)

Les données historiques (17 articles) montrent que la **famille de SERP** borne
le score : « indemnisation / montant / barème X » → 84-100 ; « procédure /
définition / comment se passe » → plafonds 62-79 malgré un gabarit identique.
Avant de rédiger : formuler le mot-clé côté « indemnisation/montant » quand
c'est possible, et annoncer un plafond réaliste sinon (le seuil de dérogation
< 85 se décide en connaissance de famille, pas après 10 loops).

### 1. Termes AVANT rédaction

```bash
python3 tools/neuronwriter.py new-query 49f477e9d390de9c "<keyword>"   # si query absente
python3 tools/nw_lab.py terms <query_id>       # cache nw-lab/terms-<query_id>.json
```

Lire le cache : termes `content_basic` / `content_extended` / `entities` avec
fourchettes `sugg_usage`, et cibles title/h1/h2/desc (`usage_pc`). En tirer un
**brief contractuel** : quels termes vont dans le `<title>`, le H1, chaque H2,
la méta, et le budget d'occurrences corps par terme.

### 2. Rédiger EN UNE PASSE sous contrat

Gabarit atelier habituel (hero, quick-answer, toc, ≥ 5 H2, ≥ 2 data-table,
≥ 1 SVG, juris Openlegi vérifiée, FAQ ≥ 6 synchronisée JSON-LD). Chaque H2
répond à une sous-question réelle ET consomme son quota de termes. Intégrer
d'office du **contenu chiffré/monétaire** (fourchettes €, délais chiffrés,
barèmes) : c'est le corrélat le plus net des articles ≥ 90 (101-121 tokens
chiffrés, 15-30 « € ») — hypothèse H4, particulièrement sur les mots-clés
procéduraux.

### 3. Audit LOCAL (zéro appel API) et patch unique

```bash
python3 tools/nw_lab.py audit nw-lab/terms-<query_id>.json actualites/<slug>.html
```

Corriger **tous** les déficits listés (et les excès) en une seule passe
éditoriale — sans bourrage : chaque terme manquant s'installe dans une phrase
qui apporte une information. Re-lancer l'audit jusqu'à couverture maximale
compatible avec l'éditorial ; cela ne coûte aucun appel API.

### 4. Scorer (1er appel), décider, corriger une fois (2e appel)

```bash
python3 tools/nw_lab.py evaluate <query_id> actualites/<slug>.html --note "S1-loop1"
```

- **≥ 90** : terminé. Coller `<!-- NEURONWRITER SCORE: N query=<id> le AAAA-MM-JJ -->`.
- **85-89** : une passe H4 (enrichissement chiffré) + déficits résiduels, 2e evaluate.
- **< 85 après 2 appels** : ne PAS boucler à l'aveugle. Diagnostiquer la famille
  de SERP dans le cache de termes (clusters hors intent : CPAM, assureur,
  employeur…) ; soit couvrir ces clusters dans des H2 dédiés (3e appel max),
  soit acter le plafond structurel et le documenter dans le commit — la
  décision de dérogation appartient au flux appelant.

### 5. Journal et traçabilité

`nw-lab/runs-<query>.jsonl` contient l'historique loop par loop (réel). Le
marqueur HTML porte TOUJOURS le dernier score API, même décevant. Reporter le
score dans `queue-aivf.json` / tracker selon le flux appelant.

## Rattachement aux flux existants

- `/article-aivf` §5bis : la boucle d'optimisation s'exécute selon CE skill
  (le seuil bloquant ≥ 85 et le marqueur QA restent inchangés).
- Pipeline WordPress (`PROMPT-PIPELINE-WP.md`, branche dédiée) : même séquence,
  en scorant via `tools/nw_eval_wp.py` (page reconstituée) au lieu du fragment.
- Toute refonte/réécriture : commencer par `terms` + `audit` sur l'existant
  avant de toucher au texte.
