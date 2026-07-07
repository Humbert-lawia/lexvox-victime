# PROTOCOLE NW-LAB — méthodologie NeuronWriter ≥ 90 en un minimum de cycles

Objectif fixé par Me Humbert (session 2026-07-07) : trouver la méthodologie qui
produit **systématiquement ≥ 90** (cible ~95) avec **le moins d'appels
`evaluate` possible**, en comparant plusieurs séquences de production et
plusieurs rédacteurs (Claude vs ChatGPT/OpenAI).

Outils : `tools/neuronwriter.py` (client de production) + `tools/nw_lab.py`
(cache de termes, audit local sans API, journal des runs, batch, rédacteur GPT).
Règle absolue inchangée : **aucun score inventé** — tout score vient de l'API et
est journalisé dans `nw-lab/runs-<query>.jsonl`.

## 0. Prérequis d'environnement (bloquants — c'est ce qui a empêché la session 2026-07-07)

Dans les réglages de l'environnement Claude Code (claude.ai/code → environnement
du dépôt) :

1. **Politique réseau** : autoriser l'egress vers `app.neuronwriter.com`
   (+ `api.openai.com` pour les bras S4/S5). La politique actuelle renvoie un
   403 au CONNECT du proxy → aucun scoring possible, quel que soit le code.
2. **Secrets** : `NEURONWRITER_API_KEY` (+ `OPENAI_API_KEY` pour S4/S5).
   Les clés ne sont JAMAIS committées (règle 5 de CLAUDE.md) et ne sont pas
   récupérables depuis les sessions passées (conteneurs isolés et éphémères) :
   elles doivent être définies dans l'environnement, comme pour les sessions
   qui ont produit les scores historiques.

Test de départ de toute session labo :
`python3 tools/neuronwriter.py list-projects` doit répondre.

## 1. Ce que disent les données historiques (17 articles scorés, dépôt au 2026-07-07)

| Famille de mot-clé | Exemples | Scores | Lecture |
|---|---|---|---|
| « indemnisation/montant/barème X » | montant indemnisation accident route (100), DFT (93), DFP (90), barèmes A (86-87), postes B (84-87) | **84-100** | SERP homogène (sites juridiques d'indemnisation) → termes atteignables |
| Procédure / définition (silo E et feuilles B « indigentes ») | déroulé expertise (62), consolidation (65), établissement (66), contester rapport (77), provision (77-78), esthétique (79) | **62-79, plafond** | SERP hétérogène (CPAM, assureurs, médecins, service-public) → clusters de termes hors intent victime |
| Loops aveugles | id 21 : 15 loops pour 84 ; id 25 : 6 loops pour 62 | — | le rendement marginal d'un loop « deviner-réévaluer » est quasi nul après 2-3 cycles |

Hypothèses à tester : **H1** le score atteignable dépend d'abord de la famille de
SERP, pas du rédacteur ; **H2** construire l'article à partir du budget de termes
(`get-query` AVANT rédaction) atteint le plafond en 1-2 cycles au lieu de 6-15 ;
**H3** sur les familles « procédure », élargir l'angle éditorial (couvrir aussi le
versant CPAM/assureur du sujet) relève le plafond de 10-15 points.

### 1bis. Analyse structurelle des 12 articles mesurables (2026-07-07, hors API)

Caractéristiques extraites des HTML (mots utiles, H2, tableaux, FAQ, mot-clé
exact dans title/H1/H2/corps, densité de chiffres et de « € ») :

| score | mots | h2 | tab | faq | kw dans title/H1 | tokens chiffrés | € |
|---|---|---|---|---|---|---|---|
| 100 (montant accident route) | 2492 | 8 | 2 | 7 | non | 117 | 21 |
| 93 (DFT) | 2885 | 9 | 2 | 7 | non | 121 | 15 |
| 90 (DFP) | 3262 | 10 | 2 | 6 | non | 101 | 30 |
| 87 (PGP) | 2705 | 10 | 3 | 6 | non | 52 | 7 |
| 86 (barème AIPP) | 2599 | 9 | 2 | 7 | oui | 87 | 19 |
| 84 (médecin conseil) | 2739 | 11 | 3 | 7 | non | 58 | 10 |
| 79 (esthétique) | 1918 | 10 | 2 | 6 | non | 142 | 27 |
| 77 (contester rapport) | 3018 | 10 | 3 | 7 | non | 44 | 0 |
| 77 (provision) | 2833 | 10 | 3 | 7 | non | 48 | 0 |
| 66 (établissement) | 2699 | 9 | 2 | 6 | oui | 48 | 10 |
| 65 (consolidation) | 3027 | 13 | 2 | 7 | oui | 38 | 0 |
| 62 (déroulé expertise, v1) | 2486 | 11 | 2 | 8 | non | 64 | 0 |

Constats : (a) la **structure ne discrimine pas** — tout le corpus respecte le
même gabarit (8-13 H2, 2-3 tableaux, 6-8 FAQ, 1900-3300 mots) de 62 à 100 ;
(b) le mot-clé exact dans title/H1 **ne prédit rien** (présent à 66 et 65,
absent à 100) ; (c) le corrélat visible le plus net est la **densité de
contenu chiffré/monétaire** : les ≥ 90 ont 101-121 tokens chiffrés et 15-30
« € », les 4 pires en « procédure » ont ≤ 64 tokens et 0-10 « € » (l'exception
esthétique 79, riche en chiffres mais plafonnée, confirme que la famille de
SERP reste le premier facteur). D'où **H4** : sur mots-clés procéduraux,
ajouter des sections chiffrées (coûts, délais en chiffres, fourchettes €,
barème d'honoraires d'expertise) relève le score — variante à tester sur K2.

## 2. Plan d'expériences — séquences comparées

Chaque séquence est exécutée sur les **3 mêmes mots-clés étalons** (un par famille) :

- K1 (facile, étalon haut) : prochain item silo C « indemnisation fracture » (id 32) ;
- K2 (dur, plafond connu) : « deroule expertise medicale », query existante
  `a7e923cccd64fc29` (réécriture 2026-07-07 non scorée en attente = premier point de mesure) ;
- K3 (moyen, silo F) : « indemnisation infection nosocomiale » (id 26).

Budget par bras : **3 appels `evaluate` maximum** (c'est la contrainte du jeu).

| Bras | Séquence | Détail |
|---|---|---|
| S0 | Contrôle historique | rédaction libre → evaluate → corrections intuitives → evaluate (méthode des sessions passées) |
| S1 | **Term-budget first** | `nw_lab terms` AVANT rédaction → brief contractuel (termes title/H1/H2/desc + fourchettes corps) → rédaction 1 passe → `nw_lab audit` local → patch → 1er evaluate |
| S2 | Audit-driven | rédaction libre (sans voir les termes) → `audit` → patch ciblé sur les seuls déficits → evaluate |
| S3 | Squelette SERP-mimétique | structure H2/FAQ calquée sur les termes à plus fort `usage_pc` h2/title → corps ensuite (teste le poids de la structure vs le lexique) |
| S4 | Rédacteur ChatGPT | même brief que S1 exécuté par `nw_lab gpt-draft` (OpenAI), assemblage dans le gabarit atelier → audit → evaluate |
| S5 | Hybride | ossature + blocs juridiques (Openlegi) par Claude, passe d'enrichissement lexical par ChatGPT sur les déficits d'audit (et variante inversée) |
| S6 | Escalier de longueur | meilleure variante S1 dupliquée à ~1900 / ~2500 / ~3200 mots → `batch` (élasticité score/longueur, 3 appels) |

Pour K2 (famille dure), ajouter le test de H3 : une variante S1 « intent élargi »
qui couvre aussi expertise CPAM / assurance de personnes dans des H2 dédiés.

## 3. Métriques et journal

Chaque `evaluate` est journalisé par `nw_lab.py` (`nw-lab/runs-<query>.jsonl`) :
fichier, score, mots, note de bras (`S1-K2-loop1`), horodatage. À la fin :

- tableau bras × mot-clé : meilleur score, nb d'appels, points gagnés par appel ;
- verdict H1/H2/H3 ;
- **méthodologie gagnante** rédigée dans ce fichier (§4) puis reportée dans le
  skill `/article-aivf` (§5bis) pour la production courante.

Critère de succès global : la séquence retenue donne ≥ 90 sur K1 et K3 et le
maximum démontré atteignable sur K2, en ≤ 2 appels `evaluate` par article.

## 4. Résultats (à remplir pendant les runs — jamais à la main sans API)

_Aucun run exécuté à ce jour : session 2026-07-07 bloquée par la politique
réseau (403 egress) et l'absence de `NEURONWRITER_API_KEY`. Premier run à
lancer : `python3 tools/nw_lab.py evaluate a7e923cccd64fc29
actualites/deroule-expertise-medicale.html --note "S1-K2-baseline-rewrite"`._
