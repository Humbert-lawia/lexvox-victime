# PIPELINE LEXVOX-AIVF — architecture de production anti-concurrent

> Manuel opérationnel pour produire, en série et de façon automatisée, des
> articles de fond qui **surclassent le concurrent AIVF**
> (association-aivf-faq.fr) sur la profondeur juridique, les données et la
> pédagogie visuelle. Découle directement de `AUDIT-COMPARATIF-AIVF-2026-07.md`.
>
> **Ce fichier + le prompt en fin de document suffisent à démarrer une nouvelle
> session entièrement dédiée à la production.**

---

## 1. Objectif stratégique

L'audit a établi un score head-to-head **AIVF 6 / Lexvox 2 / nuls 3**. La cause
n'est pas la qualité rédactionnelle (Lexvox écrit plus long et mieux) mais :

1. AIVF **couvre des silos entiers que Lexvox n'a pas** (calcul/barèmes, postes
   de préjudice un par un, grand handicap, expertise détaillée…).
2. AIVF met des **tableaux partout** ; Lexvox n'en a que sur 5 articles / 59.
3. Lexvox **dilue** son autorité dans 81 % de déclinaisons locales quasi
   dupliquées au lieu de bâtir des piliers thématiques.

**La riposte** : produire ~54 articles de fond organisés en 10 silos, chacun
plus fort que son équivalent AIVF grâce à **trois armes qu'AIVF n'a pas** :

| Arme | AIVF | LEXVOX-AIVF (nouveau standard) |
|------|------|--------------------------------|
| Analyse jurisprudentielle | ❌ aucune | ✅ ≥ 1 arrêt réel analysé + « lecture de praticien » |
| Tableaux de données | ~1 barème brut | ✅ ≥ 2 tableaux (barèmes, comparatifs, checklists chiffrées) |
| Schéma visuel | ❌ / stock | ✅ ≥ 1 infographie SVG inline sur-mesure |
| Volume utile | ~1100 mots | ✅ 1800 (feuille) / 3000+ (pilier) mots |
| E-E-A-T auteur | générique « association » | ✅ Me Humbert, avocat qui plaide, « premier avocat certifié IA » |

---

## 2. Pipeline actuel vs pipeline LEXVOX-AIVF

| Étape | Pipeline actuel (`/nouvel-article`) | Pipeline LEXVOX-AIVF (`/article-aivf`) |
|-------|-------------------------------------|----------------------------------------|
| Sujet | ad hoc / villes | **file ordonnancée `queue-aivf.json`** (silo = stratégie) |
| Sourcing droit | « citer les textes réels » | **obligatoire AVANT rédaction** : 1–2 arrêts réels via MCP Openlegi/Lexbase + articles de loi |
| Structure | hero + 4–5 H2 + FAQ | + **bloc jurisprudentiel** + **2 tableaux** + **infographie SVG** imposés |
| Visuel | 1 hero jpg | hero jpg **+ 1 schéma SVG inline** dans le corps |
| Volume | libre | plancher 1800 / 3000 mots |
| Validation | `preflight.py` | `preflight.py` **+ `qa_article_aivf.py`** |
| Cadence | manuelle | **1 article/jour ouvré** via routine planifiée |

Le pipeline actuel n'est **pas supprimé** : il reste pour les déclinaisons
locales (bots LAWIA/SEO). Le nouveau pipeline vit **en complément**, dédié aux
piliers/silos de fond.

---

## 3. Le gabarit augmenté (résumé — détail dans le skill `/article-aivf`)

Ordre imposé du corps d'article :

1. Hero (image jpg) + `<h1>` unique.
2. `quick-answer` (featured snippet).
3. `toc` (sommaire ancré).
4. 5–7 `<h2>`.
5. **≥ 2 `<table class="data-table">`**.
6. **≥ 1 `<figure class="infographic">` avec `<svg>` inline**.
7. **≥ 1 `<div class="juris-block">`** (arrêt réel + « notre lecture de praticien »).
8. FAQ 6 questions (`<details>` = JSON-LD FAQPage).
9. Bloc auteur Me Humbert + CTA + 3 cartes articles liés.

SEO bloquant (inchangé) : title ≤ 60, meta 120–155, 1 seul H1, canonical/og:url
sur `.com` sans `.html`, 4 JSON-LD valides, coordonnées = `mentions-legales.html`.

### Les 3 composants ajoutés (CSS déjà livré dans `css/style.css`)

- **`.infographic`** : figure + SVG inline. 4 archétypes — flux/procédure,
  échelle/barème, timeline/délais, répartition des postes. Classes `.ig-box`,
  `.ig-arrow`, `.ig-t`, `.ig-label`… (pas de couleur en dur, compatible dark).
- **`.juris-block`** : encadré doré « Analyse jurisprudentielle » = arrêt réel
  analysé + paragraphe « Notre lecture de praticien » (signature E-E-A-T).
- Tableaux : réutilisent `.data-table` / `.table-wrapper` existants.

---

## 4. Roadmap — 54 articles, 10 silos

Source : `AUDIT-COMPARATIF-AIVF-2026-07.md` §7 ; file exécutable :
`queue-aivf.json` (ordre = ordre de production).

| Silo | Thème | Nb | Priorité | Statut couverture actuelle |
|------|-------|----|----------|----------------------------|
| **A** | Calcul / barèmes / montants | 8 | **P1** | ❌ 0 article — plus gros trou (AIVF ~15) |
| **B** | Postes de préjudice un par un | 11 | P1/P2 | ❌ dispersé dans la nomenclature seule |
| **C** | Cas concrets de séquelles | 6 | P2 | ❌ absent |
| **D** | Grand handicap | 4 | P2 | ❌ absent |
| **E** | Expertise médicale détaillée | 5 | P2 | 🟡 1 article générique |
| **F** | Accident médical spécifique | 6 | P2 | 🟡 partiel |
| **G** | Accident de la vie / GAV / sport | 4 | P2/P3 | ❌ absent |
| **H** | Agression / CIVI / FGTI | 4 | P2 | 🟡 1 article agression |
| **I** | Usagers vulnérables (piéton, vélo, trottinette) | 3 | P2 | ❌ absent |
| **J** | Thought-leadership / différenciation (IA, Badinter) | 3 | P1/P2 | 🟡 2 `.docx` non publiés |

**Ordre de production** (encodé dans la file) :
`Quick win IA (id 1) → Silo A → Silo B → Silo E → Silo F → Silo C → Silo D → Silo G → Silo H → Silo I → J en continu.`

Justification : on frappe d'abord là où AIVF est seul et où l'intent
transactionnel est le plus fort (calcul/montants), après avoir posé le quick
win E-E-A-T (article IA déjà rédigé).

---

## 5. Diffusion journalière

- **Rythme** : 1 article de fond LEXVOX-AIVF par **jour ouvré** (lun–ven), en
  **complément** des déclinaisons locales produites par les bots existants
  (LAWIA Pipeline / LEXVOX SEO Bot). ~5 articles de fond/semaine ⇒ les 54
  articles en ~11 semaines.
- **Mécanisme** : la nouvelle session met en place une **routine planifiée**
  (trigger quotidien) qui, à chaque déclenchement :
  1. lit `queue-aivf.json`, prend le 1er `todo` ;
  2. déroule le skill `/article-aivf` (sourcing droit → rédaction → 4 fichiers → QA) ;
  3. `preflight.py` + `qa_article_aivf.py` verts, puis `git pull --rebase` + push ;
  4. passe l'item en `done` (+ date) et s'arrête jusqu'au lendemain.
- **Cohabitation bots** : toujours `git pull --rebase origin main` avant push ;
  conflits `sitemap.xml`/`actualites.html`/`llms.txt` = **union + déduplication**,
  jamais de suppression (règle CLAUDE.md).
- **Garde-fou qualité** : ne jamais publier un article qui échoue `qa_article_aivf.py`
  (bloc juris manquant, < 2 tableaux, pas d'infographie, sous le plancher de mots).

---

## 6. Outils livrés dans ce commit

| Fichier | Rôle |
|---------|------|
| `PIPELINE-LEXVOX-AIVF.md` | ce manuel (architecture + roadmap + prompt) |
| `queue-aivf.json` | file ordonnancée des 54 articles (backbone de l'automatisation) |
| `.claude/skills/article-aivf/SKILL.md` | skill invocable `/article-aivf` (procédure augmentée) |
| `tools/qa_article_aivf.py` | validateur du standard (juris + 2 tableaux + infographie + volume) |
| `css/style.css` (ajout) | composants `.infographic` / `.ig-*` / `.juris-block` |

---

## 7. PROMPT à copier dans une nouvelle conversation

> Copie-colle le bloc ci-dessous tel quel dans une **nouvelle session Claude Code**
> ouverte sur ce dépôt. Il lance la production automatisée.

```
Tu prends en charge la production éditoriale du site lexvox-victime.com selon le
PIPELINE LEXVOX-AIVF. Lis d'abord, dans cet ordre, ces fichiers du dépôt :
  1. PIPELINE-LEXVOX-AIVF.md   (architecture, gabarit augmenté, roadmap, diffusion)
  2. AUDIT-COMPARATIF-AIVF-2026-07.md   (le pourquoi : forces/faiblesses vs AIVF)
  3. queue-aivf.json           (la file ordonnancée des 54 articles à produire)
  4. .claude/skills/article-aivf/SKILL.md   (la procédure détaillée)
  5. CLAUDE.md                 (règles critiques du dépôt : domaine .com, pas de
     marqueurs de conflit, git pull --rebase avant push, NAP, aucun secret)

MISSION : produire les 54 articles de fond de queue-aivf.json, dans l'ordre du
tableau (le 1er item todo est l'article IA/Village de la Justice déjà rédigé au
format .docx — publie-le en le convertissant au gabarit, ne le réécris pas).

Chaque article DOIT surpasser l'équivalent AIVF via les 3 armes du standard :
  • ≥ 1 bloc d'analyse jurisprudentielle (arrêt RÉEL vérifié via les MCP
    juridiques Openlegi/Lexbase — charge-les avec ToolSearch ; jamais de numéro
    de pourvoi inventé) avec un paragraphe « Notre lecture de praticien » ;
  • ≥ 2 tableaux data-table (barème/fourchettes, comparatif, checklist chiffrée) ;
  • ≥ 1 infographie schéma SVG inline (<figure class="infographic"> + <svg>).
Volume : 1800 mots minimum (feuille), 3000+ (pilier). Invoque le skill
/article-aivf pour chaque article et déroule ses 6 étapes (sujet → sourcing droit
→ rédaction → infographie → maillage des 4 fichiers → validation).

VALIDATION avant chaque push (bloquant) :
  python3 tools/preflight.py
  python3 tools/qa_article_aivf.py actualites/<slug>.html [--pilier]
  git diff --check ; git pull --rebase origin main   (union+dedup si conflit sitemap)
Ne pousse jamais un article qui échoue le QA. Un commit = un article complet +
ses 4 fichiers maillés (sitemap.xml, actualites.html, llms.txt, maillage interne)
+ queue-aivf.json mis à jour (status "done" + date).

CADENCE : mets en place une diffusion d'1 article de fond par jour ouvré, en
complément des déclinaisons locales des bots existants — planifie une routine
quotidienne qui prend le prochain item todo de la file, le produit, le valide, le
pousse, puis s'arrête jusqu'au lendemain. Vérifie que main déploie bien en prod
(Cloudflare Pages) après chaque push.

COMMENCE MAINTENANT : traite l'item id 1 de queue-aivf.json de bout en bout, puis
propose-moi le calendrier de diffusion des 53 suivants avant d'enchaîner.
```
