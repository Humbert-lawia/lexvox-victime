# PIPELINE LEXVOX-AIVF — architecture de production anti-concurrent

> Manuel opérationnel pour produire, en série et de façon automatisée, des
> articles de fond qui **surclassent le concurrent AIVF**
> (association-aivf-faq.fr) sur la profondeur juridique, les données et la
> pédagogie visuelle. Découle de `AUDIT-COMPARATIF-AIVF-2026-07.md` et intègre
> les correctifs de l'audit critique du pipeline (v2).
>
> **Ce fichier + le prompt en fin de document suffisent à démarrer une nouvelle
> session de production entièrement automatisée.**

---

## 1. Objectif stratégique

Score head-to-head de l'audit : **AIVF 6 / Lexvox 2 / nuls 3**. Cause : AIVF
couvre des silos entiers absents chez Lexvox (calcul/barèmes, postes un par un,
grand handicap…), met des tableaux partout, et Lexvox dilue son autorité dans
81 % de déclinaisons locales dupliquées.

**Contrainte n°1, non négociable (Me Humbert)** : chaque article doit être
**optimisé NeuronWriter avec un score ≥ 85** avant publication, et faire **au
minimum 1900 mots** (le volume peut monter pour gagner des points, jamais
descendre sous 1900). C'est le critère prioritaire ; les trois armes ci-dessous
s'y ajoutent, elles ne le remplacent pas.

**Riposte** : ~52 articles de fond en 10 silos, chacun plus fort que son
équivalent AIVF grâce à **trois armes qu'AIVF n'a pas** :

| Arme | AIVF | LEXVOX-AIVF (standard v2) |
|------|------|---------------------------|
| Analyse jurisprudentielle | ❌ aucune | ✅ ≥ 1 arrêt **réel vérifié via Openlegi** + backlink source + « lecture de praticien » |
| Tableaux de données | ~1 barème brut | ✅ ≥ 2 tableaux (barèmes, comparatifs, checklists chiffrées) |
| Schéma visuel | ❌ / stock | ✅ ≥ 1 infographie SVG inline sur-mesure |
| Couverture d'intent | ~1100 mots | ✅ ≥ 5 H2 + FAQ 6 questions, ≥ 1500/2500 mots utiles |
| E-E-A-T auteur | « association » | ✅ Me Humbert, avocat qui plaide, « premier avocat certifié IA » |

---

## 2. Correctifs intégrés (audit critique du pipeline)

| # | Correctif appliqué | Où |
|---|--------------------|-----|
| 0 | **Optimisation NeuronWriter ≥ 85 (priorité absolue)** + plancher **1900 mots**. Score obtenu via l'API (`tools/neuronwriter.py`, clé en secret) ou un connecteur, collé en marqueur `<!-- NEURONWRITER SCORE: N -->` ; le QA bloque si < 85 ou absent. | skill §5bis + QA |
| B | **Vérification juridique câblée — Openlegi UNIQUEMENT** (pas Lexbase). Chaque arrêt est confirmé par un appel Openlegi ; son URL sert de **backlink** ; un marqueur `<!-- OPENLEGI VERIFIED: … -->` est collé par décision. | skill §1/§4 + QA |
| C | **QA câblé en CI bloquante** (`qa_queue.py` dans `validate.yml`) + comptage de mots **hors chrome** (nav/footer exclus). | `validate.yml`, `qa_article_aivf.py` |
| D | **Dédoublonnage de la file** : paires cannibales fusionnées (pretium↔souffrances → id 12 ; calcul-DFP↔DFP → id 11), en hub + ancres. 54 → 52 articles actifs. | `queue-aivf.json` |
| E | **Plancher d'intent** (≥ 5 H2 + 6 FAQ) au lieu du seul quota de mots + **pages hub de silo** (cocon). | skill §2/§5, `_meta.silos` |
| F | **Prérequis GSC/GA4** documenté (valider le volume réel des mots-clés avant un silo). | §5 ci-dessous, prompt |
| — | **Point A ANNULÉ à la demande de Me Humbert** : publication **directe sur `main` (prod)**, vérification **a posteriori**. Le garde-fou avant mise en ligne est donc la vérification Openlegi + le QA. | skill §6 |
| G | **Non traité** (déontologie / stratégie images / rendu SVG) — exclu volontairement. | — |

---

## 3. Pipeline actuel vs pipeline LEXVOX-AIVF

| Étape | `/nouvel-article` (existant) | `/article-aivf` (nouveau) |
|-------|------------------------------|---------------------------|
| Sujet | ad hoc / villes | **file ordonnancée `queue-aivf.json`** |
| Sourcing droit | « citer les textes réels » | **obligatoire + vérifié Openlegi** avant rédaction, backlink source |
| Structure | hero + 4–5 H2 + FAQ | + **bloc juris vérifié** + **2 tableaux** + **infographie SVG** + ≥ 5 H2 + 6 FAQ |
| Visuel | 1 hero jpg | hero jpg **+ 1 schéma SVG inline** |
| Cocon | maillage libre | **hub de silo** obligatoire (voir `_meta.silos`) |
| Validation | `preflight.py` | `preflight.py` **+ `qa_article_aivf.py` + `qa_queue.py` (CI)** |
| Publication | push `main` | push `main` **direct (prod)**, revue a posteriori |
| Cadence | manuelle | **1 article/jour ouvré** via routine planifiée |

Le pipeline existant reste pour les déclinaisons locales (bots). Le nouveau vit
**en complément**, dédié aux piliers/silos de fond.

---

## 4. Le gabarit augmenté (détail dans `/article-aivf`)

Ordre imposé : Hero+H1 → `quick-answer` → `toc` → **≥ 5 `<h2>`** → **≥ 2
`.data-table`** → **≥ 1 `.infographic` (SVG)** → **≥ 1 `.juris-block` vérifié
Openlegi + backlink** → **FAQ ≥ 6 `<details>`** → auteur + CTA + 3 liés.

SEO bloquant (inchangé) : title ≤ 60, meta 120–155, 1 H1, canonical/og:url `.com`
sans `.html`, 4 JSON-LD valides, NAP = `mentions-legales.html`.

Composants livrés dans `css/style.css` : `.infographic` / `.ig-*` (SVG),
`.juris-block` (encadré doré + backlink), tableaux `.data-table` existants.

Le bloc juris porte **toujours** un backlink `<a href="<URL Légifrance renvoyée
par Openlegi>">` et un marqueur `<!-- OPENLEGI VERIFIED: … -->`. Sans ça, le QA
bloque. **Jamais de n° de pourvoi inventé** : il vient de la réponse Openlegi.

---

## 5. Roadmap, cocon et prérequis

Source : `AUDIT-COMPARATIF-AIVF-2026-07.md` §7 ; file exécutable `queue-aivf.json`.

| Silo | Thème | Hub (cocon) | Nb actifs | Prio |
|------|-------|-------------|-----------|------|
| **A** | Calcul / barèmes / montants | `/actualites/bareme-indemnisation-prejudice-corporel-2026` (à créer, id 2) | 7 | **P1** |
| **B** | Postes de préjudice | `/nomenclature-dintilhac` (existant) | 9 | P1/P2 |
| **C** | Cas concrets de séquelles | `/indemnisation-prejudice-corporel` (existant) | 6 | P2 |
| **D** | Grand handicap | `/indemnisation-prejudice-corporel` (existant) | 4 | P2 |
| **E** | Expertise médicale | `/expertise-medicale` (existant) | 5 | P2 |
| **F** | Accident médical | `/responsabilite-medicale` (existant) | 6 | P2 |
| **G** | Accident de la vie / GAV | `/actualites/garantie-accidents-de-la-vie-gav` (à créer, id 42) | 4 | P2/P3 |
| **H** | Agression / CIVI / FGTI | `/victime-agression` (existant) | 4 | P2 |
| **I** | Usagers vulnérables | `/accident-de-la-route` (existant) | 3 | P2 |
| **J** | Thought-leadership (IA, Badinter) | `/cabinet` (existant) | 3 | P1/P2 |

**Ordre de production** (encodé dans la file) :
`id 1 (IA) → Silo A → B → E → F → C → D → G → H → I → J en continu.`

**Cocon** : chaque feuille lie vers le hub de son silo EN PREMIER + 2–3 feuilles
sœurs ; le hub (id 2, id 42, ou page pilier existante) liste toutes ses feuilles.

**Prérequis à câbler côté Me Humbert** :
- **NeuronWriter (bloquant, priorité 1)** : fournir la **clé API NeuronWriter**
  comme **secret** `NEURONWRITER_API_KEY` (GitHub Actions secret ou variable
  Cloudflare — **jamais committée**, règle 5 de CLAUDE.md) + l'ID de projet
  NeuronWriter. Alternative : autoriser un **connecteur NeuronWriter** dans la
  session. Sans l'un des deux, la prod ne peut pas atteindre le gate ≥ 85 →
  publication impossible.
  **⚠️ Réseau** : l'appel API vise `app.neuronwriter.com`. La session de
  production doit tourner dans un **environnement dont la politique réseau
  autorise cet hôte en egress** (cf. Network policy à la création de
  l'environnement — https://code.claude.com/docs/en/claude-code-on-the-web).
  L'environnement d'audit actuel le **bloque** (proxy egress → 403), donc le
  scoring API n'y est pas testable ; utiliser un environnement à réseau ouvert
  ou un **connecteur MCP NeuronWriter** (qui ne passe pas par ce proxy).
- **GSC/GA4 (correctif F)** : les `keyword` de la file sont des hypothèses
  (GSC/GA4 non configurés — actions I-03/I-04 du SUIVI). **Avant de lancer un
  silo, valider le volume réel** des mots-clés. Sans données, produire mais
  logguer l'hypothèse.

---

## 6. Diffusion journalière

- **Rythme** : 1 article de fond/jour ouvré (lun–ven), en complément des
  déclinaisons locales des bots. ~52 articles en ~11 semaines.
- **Mécanisme** : la nouvelle session met en place une **routine planifiée**
  (trigger quotidien) qui, à chaque déclenchement :
  1. lit `queue-aivf.json`, prend le 1er `todo` (ignore les `merged`) ;
  2. déroule `/article-aivf` (sourcing **vérifié Openlegi** → rédaction → SVG →
     cocon → 4 fichiers) ;
  3. `preflight.py` + `qa_article_aivf.py` + `qa_queue.py` verts ;
  4. `git pull --rebase` puis **push direct `main` (prod)** ;
  5. passe l'item en `done` (+ date) et s'arrête jusqu'au lendemain.
- **Cohabitation bots** : `git pull --rebase origin main` avant push ; conflits
  `sitemap.xml`/`actualites.html`/`llms.txt` = **union + déduplication**, jamais
  de suppression (règle CLAUDE.md). Jamais de marqueur de conflit committé.
- **Limite d'automatisation à connaître** : l'environnement de session est
  éphémère ; si le container est recyclé, relancer une session avec le prompt §8.

---

## 7. Fichiers du pipeline

| Fichier | Rôle |
|---------|------|
| `PIPELINE-LEXVOX-AIVF.md` | ce manuel (architecture + roadmap + prompt) |
| `queue-aivf.json` | file ordonnancée (52 actifs, 2 fusionnés) + carte des hubs |
| `.claude/skills/article-aivf/SKILL.md` | skill `/article-aivf` (procédure augmentée) |
| `tools/neuronwriter.py` | client API NeuronWriter (new-query / get-query / evaluate) — gate score ≥ 85 |
| `tools/qa_article_aivf.py` | validateur d'un article (**NeuronWriter ≥ 85**, juris+backlink+Openlegi, 2 tableaux, SVG, intent, ≥ 1900 mots) |
| `tools/qa_queue.py` | runner CI : valide les articles `done` de la file |
| `.github/workflows/validate.yml` | CI : `preflight.py` + `qa_queue.py` (bloquants) |
| `css/style.css` (ajout) | `.infographic` / `.ig-*` / `.juris-block` |

---

## 8. PROMPT à copier dans une nouvelle conversation

> Copie-colle le bloc ci-dessous tel quel dans une **nouvelle session Claude Code**
> ouverte sur ce dépôt. Il lance la production automatisée en publication directe.

```
Tu prends en charge la production éditoriale de lexvox-victime.com selon le
PIPELINE LEXVOX-AIVF. Lis d'abord, dans cet ordre :
  1. PIPELINE-LEXVOX-AIVF.md            (architecture, gabarit, roadmap, diffusion)
  2. AUDIT-COMPARATIF-AIVF-2026-07.md   (forces/faiblesses vs AIVF)
  3. queue-aivf.json                    (file ordonnancée + hubs de silo)
  4. .claude/skills/article-aivf/SKILL.md   (la procédure détaillée)
  5. CLAUDE.md                          (règles critiques du dépôt)

MISSION : produire les articles de queue-aivf.json dans l'ordre du tableau (ignore
les status "merged"). L'item id 1 est l'article IA/Village de la Justice déjà
rédigé au format .docx (article-village-justice-ia-dommage-corporel.docx, version
longue) : publie-le en le convertissant au gabarit, ne le réécris pas.

PRIORITÉ ABSOLUE, NON NÉGOCIABLE : chaque article doit être optimisé NeuronWriter
avec un score >= 85 AVANT publication, et faire >= 1900 mots utiles (le volume peut
monter pour gagner des points, jamais descendre sous 1900). Accès NeuronWriter :
en PRIORITÉ le CONNECTEUR MCP NeuronWriter (charge ses outils avec ToolSearch,
requête "neuronwriter" ; il ne passe pas par le proxy egress). À défaut, l'API
tools/neuronwriter.py (clé secret NEURONWRITER_API_KEY, nécessite un environnement
autorisant l'egress vers app.neuronwriter.com). Procédure : crée/ouvre une query
sur le mot-clé, couvre les termes NLP recommandés, évalue le score, itère jusqu'à
>= 85, puis colle le marqueur <!-- NEURONWRITER SCORE: N query=<id> le AAAA-MM-JJ -->.
Sans NeuronWriter disponible, NE PUBLIE PAS (signale le blocage). Le QA refuse tout
article < 85 ou sans marqueur.

Chaque article DOIT surpasser l'équivalent AIVF via les 3 armes du standard :
  • ≥ 1 bloc d'analyse jurisprudentielle dont l'arrêt est VÉRIFIÉ via le MCP
    OPENLEGI UNIQUEMENT (pas Lexbase) — charge-le avec ToolSearch (serveur
    "Openlegi"). Le n° de pourvoi vient de la réponse Openlegi ; JAMAIS inventé.
    Intègre un BACKLINK <a href> vers l'URL source renvoyée par Openlegi et colle
    un marqueur <!-- OPENLEGI VERIFIED: réf — URL --> par décision. Si Openlegi
    est indisponible, ne fabrique aucun bloc juris : passe à des textes de loi
    vérifiables et signale-le.
  • ≥ 2 tableaux data-table (barème/fourchettes, comparatif, checklist chiffrée) ;
  • ≥ 1 infographie schéma SVG inline (<figure class="infographic"> + <svg>).
Couverture d'intent : ≥ 5 H2 + FAQ 6 questions ; ≥ 1900 mots utiles (feuille) /
2500 (pilier), plancher absolu 1900, sans délayage. Cocon : lie vers le hub du silo (_meta.silos) puis
2–3 feuilles sœurs. Invoque /article-aivf et déroule ses 6 étapes.

VALIDATION avant chaque push (bloquant) :
  python3 tools/neuronwriter.py evaluate <query_id> actualites/<slug>.html   (>= 85)
  python3 tools/preflight.py
  python3 tools/qa_article_aivf.py actualites/<slug>.html [--pilier]
  python3 tools/qa_queue.py
  git diff --check ; git pull --rebase origin main   (union+dedup si conflit sitemap)

PUBLICATION : DIRECTE et automatique sur main (= prod immédiate Cloudflare Pages).
PAS de PR, PAS de sas : Me Humbert vérifie a posteriori une fois en ligne. Ne
pousse jamais un article qui échoue preflight ou qa. Un commit = un article
complet + ses 4 fichiers maillés (sitemap.xml, actualites.html, llms.txt, cocon)
+ queue-aivf.json à jour (status "done" + date).

CADENCE : mets en place une diffusion d'1 article/jour ouvré via une routine
quotidienne (trigger) qui prend le prochain item todo, le produit, le valide, le
pousse sur main, puis s'arrête jusqu'au lendemain.

PRÉREQUIS (à faire par Me Humbert AVANT de coller ce prompt) : (1) autoriser le
CONNECTEUR NeuronWriter dans les réglages de connecteurs claude.ai ; (2) le
serveur MCP Openlegi doit être connecté (vérif jurisprudence). Vérifie les deux
en début de session via ToolSearch ("neuronwriter" et "openlegi") ; si l'un
manque, arrête-toi et demande son autorisation, n'invente ni score ni arrêt. Les
volumes de mots-clés ne sont pas validés (GSC/GA4 non configurés) — produis mais
logue l'hypothèse de volume par silo.

COMMENCE MAINTENANT : traite l'item id 1 de bout en bout et publie-le, puis
enchaîne id 2 (le hub du silo A), et continue la file.
```
