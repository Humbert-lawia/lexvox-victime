---
name: article-aivf
description: Produire un article de fond haut de gamme selon le PIPELINE LEXVOX-AIVF v2 (gabarit augmente pour surpasser le concurrent AIVF) — optimisation NeuronWriter score >=85 (priorite non negociable, min 1900 mots), analyse jurisprudentielle VERIFIEE via Openlegi avec backlink, 2+ tableaux, infographie SVG inline, couverture d'intent, cocon, puis PUBLICATION DANS SANITY (tools/sanity_publish.py) — le site en prod est un frontend Next.js+Sanity, plus ce depot statique. Utiliser pour tout article de queue-aivf.json ou quand l'utilisateur demande un article "qualite AIVF-killer".
---

# Produire un article — PIPELINE LEXVOX-AIVF v2 (Sanity)

Ce skill remplace `/nouvel-article` pour les articles du plan anti-AIVF.
Il reprend la mecanique de production et ajoute les signatures de differenciation
imposees par l'audit (`AUDIT-COMPARATIF-AIVF-2026-07.md`) et le manuel
`PIPELINE-LEXVOX-AIVF.md`.

**ARCHITECTURE (incident 2026-07-06, lire la section dediee de CLAUDE.md) :**
la production est le frontend **Next.js + Sanity** (projet `jef1bcbo`, dataset
`production`). Ce depot est l'ATELIER : on y redige l'article au gabarit HTML,
on y passe tous les QA, on l'archive sur `main` (aucun deploiement n'est
declenche : `deploy.yml` est neutralise — NE JAMAIS le reactiver), puis on
publie le document dans Sanity via `tools/sanity_publish.py`. Le frontend
affiche l'article des que `publishedAt <= now` (publication progressive,
cadence existante ~2/jour a 09:00Z et 15:00Z).

Regle d'or : **aucun sas de relecture prealable** — la relecture de Me Humbert
se fait a posteriori. Les garde-fous bloquants avant publication Sanity :
verification **Openlegi** de chaque jurisprudence (§1/§4), **NeuronWriter >= 85**
(§5bis), `preflight` + `qa_article_aivf` verts (§6).

## 0. Choisir le sujet dans la file

- Ouvrir `queue-aivf.json`. Prendre le **premier `status: "todo"`** dans l'ordre
  du tableau (l'ordre EST la strategie). **Ignorer les `status: "merged"`**
  (fusionnes pour eviter la cannibalisation ; leur contenu est une section
  ancree de l'article `merged_into`).
- Passer l'item a `"in_progress"`, produire, puis `"done"` + `"date"` (AAAA-MM-JJ).
- `type: "pilier"` => cible 2500+ mots utiles et role de HUB ; `feuille` => 1500+.
- Item id 1 : publier le `.docx` de Me Humbert
  (`article-village-justice-ia-dommage-corporel.docx`, version longue) en le
  convertissant au gabarit (extraire le texte via `unzip -p <fichier>.docx word/document.xml`
  puis nettoyer), ne pas le reecrire.

## 1. Sourcer et VERIFIER le droit AVANT de rediger (non negociable)

C'est ce qui nous rend meilleurs qu'AIVF (eux : zero jurisprudence). **Serveur
MCP Openlegi UNIQUEMENT** (pas Lexbase). Le charger via ToolSearch, ex.
`ToolSearch "select:mcp__Openlegi__rechercher_jurisprudence_judiciaire,mcp__Openlegi__get_decision_judiciaire"`
(le prefixe exact du serveur peut varier selon la session : rechercher "Openlegi").

Pour chaque article :

1. **Chercher 1 a 2 decisions reelles** pertinentes via `rechercher_jurisprudence_judiciaire`
   (Cass. civ. 2e de preference en dommage corporel, ou CE, ou CA), puis
   `get_decision_judiciaire` pour recuperer le texte, la reference exacte
   (juridiction, date, n° de pourvoi) ET **l'URL/identifiant de la source**.
2. **Ne jamais citer un arret qui n'a pas ete confirme par Openlegi.** Le n° de
   pourvoi vient de la reponse Openlegi, pas de la memoire du modele.
3. **Construire le backlink** : `<a href="<URL Legifrance renvoyee par Openlegi>"
   rel="nofollow noopener" target="_blank">…</a>` dans le bloc juris.
4. **Coller un marqueur de verification** en commentaire HTML au-dessus du bloc :
   `<!-- OPENLEGI VERIFIED: Cass. civ. 2e, 12 mai 2022, n° 20-XX.XXX — <URL> -->`.
   (Le QA compte 1 marqueur par bloc juris ; sinon il bloque.)
5. Completer avec les **articles de loi** applicables (numeros exacts : Code
   civil, loi Badinter, Code de la sante publique, Code des assurances — via
   `rechercher_code`) et les **baremes** (referentiel Mornet dans le repo,
   echelle pretium 1–7, AIPP), toujours "a titre indicatif, souverainete du juge".

Si Openlegi est indisponible : ne pas inventer de jurisprudence. Se rabattre sur
des textes verifiables (Legifrance, service-public.fr — jamais `.gouv.fr`), le
signaler dans le commit, et ne pas fabriquer de bloc juris factice.

## 2. Rediger dans le gabarit augmente

Partir d'un article recent conforme comme squelette (hero, nav, footer, JSON-LD).
Structure **obligatoire**, dans l'ordre :

1. Hero (image jpg) + `<h1>` unique (<= 100 car.).
2. `quick-answer` : reponse directe 2–3 phrases (featured snippet).
3. `toc` (sommaire ancre).
4. **>= 5 sections `<h2>`** (couverture d'intent, pas de remplissage) avec `<h3>` par sous-poste.
5. **>= 2 tableaux `<table class="data-table">`** (barème/fourchettes, comparatif, checklist chiffree…).
6. **>= 1 infographie `<figure class="infographic">` avec `<svg>` inline** (cf. §3).
7. **>= 1 bloc `<div class="juris-block">`** verifie Openlegi + backlink (cf. §4).
8. **FAQ >= 6 questions** (`<details>`) — memes questions que le JSON-LD FAQPage.
9. Bloc auteur (Me Patrice Humbert) + CTA + 3 cartes "articles lies".

Contraintes bloquantes (comme `/nouvel-article`) : `<title>` <= 60 car. ; meta
120–155 car. non vide ; 1 seul `<h1>` ; `canonical` = `og:url` =
`https://lexvox-victime.com/actualites/<slug>` (.com, **sans** `.html`) ; 4 JSON-LD
valides (`LegalService`, `Article` avec `image`, `FAQPage`, `BreadcrumbList`),
JSON pur ; coordonnees = `mentions-legales.html`. **Plancher de mots NON
NEGOCIABLE : jamais moins de 1900 mots utiles** (2500 pour un pilier), chrome
nav/footer exclu. Le volume peut MONTER au-dessus de 1900 si cela aide le score
NeuronWriter, mais jamais descendre sous 1900.

Priorite a la **couverture d'intent** sur le remplissage : chaque `<h2>` repond a
une sous-question reelle (People Also Ask / FAQ). Ne pas delayer betement, mais
couvrir les termes NLP attendus (cf. §5bis NeuronWriter).

## 3. L'infographie SVG inline (au moins une)

SVG inline (net Retina, indexable, accessible, zero asset binaire). CSS
`.infographic` / `.ig-*` deja livre dans `css/style.css`. Archetypes : flux/
procedure (etapes + fleches), echelle/barème (graduation 1–7), timeline/delais,
repartition des postes. Squelette :

```html
<figure class="infographic">
  <figcaption>Les 4 etapes de la procedure CCI/CRCI</figcaption>
  <svg viewBox="0 0 800 200" role="img" aria-label="Schema des 4 etapes de la procedure CCI/CRCI">
    <defs><marker id="igArrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" class="ig-fill"/></marker></defs>
    <!-- .ig-box / .ig-box-accent, texte .ig-t + .ig-label, fleches .ig-arrow -->
  </svg>
  <p class="ig-source">Source : art. L.1142-1 et s. Code de la sante publique.</p>
</figure>
```

`role="img"` + `aria-label` obligatoires ; classes `.ig-*` (jamais de couleur en
dur) ; SVG sobre, lisible mobile.

## 4. Le bloc d'analyse jurisprudentielle (signature LEXVOX)

Un `.juris-block` minimum, avec **backlink** et **marqueur de verification** :

```html
<!-- OPENLEGI VERIFIED: Cass. civ. 2e, 12 mai 2022, n° 20-XX.XXX — https://www.legifrance.gouv.fr/juri/id/... -->
<div class="juris-block">
  <span class="juris-tag">Analyse jurisprudentielle</span>
  <h3>Ce que dit la Cour de cassation sur ...</h3>
  <p>Dans un arret
     <a href="https://www.legifrance.gouv.fr/juri/id/..." rel="nofollow noopener" target="_blank">
     <span class="juris-ref">Cass. civ. 2e, 12 mai 2022, n° 20-XX.XXX</span></a>,
     la Cour a juge que ... . Concretement pour la victime, cela signifie ... .</p>
  <p><strong>Notre lecture de praticien :</strong> ... (angle avocat qui plaide, E-E-A-T).</p>
  <cite>Cass. civ. 2e, 12 mai 2022, n° 20-XX.XXX (verifie via Openlegi).</cite>
</div>
```

Le paragraphe "Notre lecture de praticien" incarne l'expertise de Me Humbert :
toujours le renseigner. Reference + n° de pourvoi = ceux renvoyes par Openlegi.

## 5. Cocon + suivi (systematique)

1. **Cocon dans le corps de l'article** : lier vers le **HUB du silo** (voir
   `_meta.silos[<silo>].hub_url` dans `queue-aivf.json`) EN PREMIER, + 2–3 liens
   vers les feuilles freres du meme silo, + backlink depuis le hub si le hub est
   un article qu'on cree/maintient. Un pilier nouvellement cree EST le hub : il
   doit lister toutes ses feuilles. Liens internes en URL relative sans `.html`
   (`/actualites/<slug>`, `/nomenclature-dintilhac`…) — `sanity_publish.py` les
   convertit tels quels.
2. **Anti-cannibalisation Sanity** : avant de creer un slug, verifier qu'aucun
   des ~545 articles existants ne le prend deja :
   `curl -s "https://jef1bcbo.apicdn.sanity.io/v2024-01-01/data/query/production?query=*%5Bslug.current%3D%3D%22<slug>%22%5D%7B_id%7D"`
   (les slugs Sanity historiques peuvent porter un prefixe `actualites-` : tester les deux).
3. `queue-aivf.json` a jour (`status: "done"`, `date`, `neuronwriter_score`).
4. `PUBLICATION-TRACKER.md` a jour (tableau publies / en attente, avec URLs).
5. Legacy (facultatif) : `sitemap.xml`, `actualites.html`, `llms.txt` du depot ne
   sont plus servis en production — ne les maintenir que si demande.

## 5bis. Optimiser avec NeuronWriter — score >= 85 (LA priorite, non negociable)

C'est le critere le plus important : **aucun article publie sous 85**.

**L'optimisation s'execute OBLIGATOIREMENT selon le skill `/nw-optimisation`**
(`.claude/skills/nw-optimisation/SKILL.md`, methode "term-budget first + audit
local" VALIDEE le 2026-07-07 : 62 -> 85 sur la query la plus dure du corpus,
au lieu de 6-15 loops aveugles). En resume — le detail, les lois empiriques du
scoreur et les objectifs par famille de mot-cle sont dans le skill :

1. Recuperer les termes AVANT de rediger : `python3 tools/nw_lab.py terms
   <query_id>` (query creee via `tools/neuronwriter.py new-query <project_id>
   "<keyword>"` si absente ; cle en secret d'env `NEURONWRITER_API_KEY`, jamais
   committee, egress `app.neuronwriter.com` requis — pas de connecteur).
   En tirer le brief contractuel : termes title/H1/H2/desc + budget corps.
2. Rediger EN UNE PASSE sous contrat (le §2 de ce skill reste le gabarit),
   puis auditer LOCALEMENT (`python3 tools/nw_lab.py audit ...`, 0 appel API)
   et solder tous les deficits de couverture.
3. Scorer : `python3 tools/nw_lab.py evaluate <query_id> actualites/<slug>.html
   --note "..."` — **budget 2 appels**, pas de boucle aveugle. Sous l'objectif :
   une passe corrective (densifier H1/H2), 2e evaluate, puis acter le plafond.
   Le volume peut augmenter pour cela ; il ne descend jamais sous 1900 mots.
4. **Coller le score obtenu en marqueur** dans le `<head>` ou en haut du `<article>` :
   `<!-- NEURONWRITER SCORE: 87 query=<query_id> le AAAA-MM-JJ -->` — toujours
   le dernier score API reel, jamais un score invente.
   (Le QA lit ce marqueur et bloque si < 85 ou absent.)

Si NeuronWriter est indisponible (ni API ni connecteur), NE PAS publier : signaler
le blocage. Le score >= 85 est une condition de mise en ligne, pas une option.

## 6. Valider, archiver, puis publier dans SANITY

```bash
python3 tools/neuronwriter.py evaluate <query_id> actualites/<slug>.html   # >= 85 (BLOQUANT)
python3 tools/preflight.py                                   # SEO de base — 0 erreur (BLOQUANT)
python3 tools/qa_article_aivf.py actualites/<slug>.html [--pilier]   # standard AIVF-killer (BLOQUANT)
python3 tools/qa_queue.py                                    # coherence de la file (BLOQUANT)

# 1) Archive Git (ne deploie RIEN : deploy.yml neutralise — ne pas le reactiver)
git diff --check
git checkout main
git add actualites/<slug>.html img/articles/<slug>.jpg queue-aivf.json PUBLICATION-TRACKER.md
git commit -m "Article <silo>-<id> : <sujet>"
git pull --rebase origin main && git push origin main

# 2) Publication SANITY (= mise en ligne reelle)
python3 tools/sanity_publish.py actualites/<slug>.html --dry-run          # controle du JSON
python3 tools/sanity_publish.py actualites/<slug>.html \
    --publish-at <ISO-UTC|now> --category <cat-...>   # jeton env SANITY_API_TOKEN requis

# 3) Verifier en ligne (des que publishedAt est passe)
curl -s -o /dev/null -w "%{http_code}" https://lexvox-victime.com/actualites/<slug>
```

Choisir `--publish-at` : "now" si Me Humbert veut l'article visible immediatement ;
sinon le prochain creneau libre de la cadence (09:00Z / 15:00Z) APRES les articles
deja programmes dans Sanity (requete GROQ `*[_type=="article"] | order(publishedAt desc)[0].publishedAt`).
`--category` : choisir parmi cat-accident-route, cat-accident-travail,
cat-erreur-medicale, cat-indemnisation, cat-procedure (silo A/B => cat-indemnisation ;
E/F => cat-erreur-medicale ou cat-procedure ; C/D => cat-indemnisation ;
G/H/I/J => selon sujet).

**Ne jamais publier dans Sanity un article qui echoue NeuronWriter >= 85,
`preflight.py` ou `qa_article_aivf.py`** (garde-fous remplacant le sas humain).
Si `SANITY_API_TOKEN` est absent : s'arreter et le demander a Me Humbert
(a ajouter dans les variables d'environnement de l'environnement Claude Code,
jamais en clair dans le depot ni le chat). Limitations schema Sanity : les
`<table class="data-table">` sont converties en listes, l'infographie SVG est
uploadee en asset image — verifier le rendu apres publication.
