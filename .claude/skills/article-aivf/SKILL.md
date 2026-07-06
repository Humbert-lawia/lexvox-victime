---
name: article-aivf
description: Produire un article de fond haut de gamme selon le PIPELINE LEXVOX-AIVF (gabarit augmente pour surpasser le concurrent AIVF) — optimisation NeuronWriter score >=85 (priorite non negociable, min 1900 mots), analyse jurisprudentielle VERIFIEE via Openlegi avec backlink, 2+ tableaux, infographie SVG inline, couverture d'intent, cocon, maillage des 4 fichiers, puis publication directe sur main (prod). Utiliser pour tout article de queue-aivf.json ou quand l'utilisateur demande un article "qualite AIVF-killer".
---

# Produire un article — PIPELINE LEXVOX-AIVF

Ce skill remplace `/nouvel-article` pour les articles du plan anti-AIVF.
Il reprend la mecanique de maillage et ajoute les signatures de differenciation
imposees par l'audit (`AUDIT-COMPARATIF-AIVF-2026-07.md`) et le manuel
`PIPELINE-LEXVOX-AIVF.md`.

Regle d'or de publication : **publication directe et automatique sur `main`
(= production immediate via Cloudflare Pages), sans sas de relecture prealable.**
La verification humaine se fait A POSTERIORI (Me Humbert relit une fois en ligne).
Le seul garde-fou avant mise en ligne est donc la **verification Openlegi** de
chaque jurisprudence (§1/§4) : aucun arret non confirme par Openlegi ne doit etre
publie. Le QA (`preflight` + `qa_article_aivf`) doit passer avant chaque push.

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

## 5. Mailler les 4 fichiers + cocon (systematique)

1. `sitemap.xml` : `<url>` + `lastmod` du jour, sans doublon.
2. `actualites.html` : carte dans la bonne categorie + compteur ; pilier => "A la une".
3. `llms.txt` : ligne dans les articles recents.
4. **Cocon** : lier vers le **HUB du silo** (voir `_meta.silos[<silo>].hub_url` dans
   `queue-aivf.json`) EN PREMIER, + 2–3 liens vers les feuilles freres du meme silo,
   + backlink depuis le hub si le hub est un article qu'on cree/maintient. Un pilier
   nouvellement cree (id 2 silo A, id 42 silo G) EST le hub : il doit lister toutes
   ses feuilles. Mettre `queue-aivf.json` a jour (`status: "done"`, `date`).

## 5bis. Optimiser avec NeuronWriter — score >= 85 (LA priorite, non negociable)

C'est le critere le plus important : **aucun article publie sous 85**. Boucle
d'optimisation avant validation :

1. Creer/reutiliser une query NeuronWriter pour le mot-cle de l'article
   (`_meta` / `keyword` de la file). Deux voies (priorite au connecteur) :
   - **Connecteur MCP NeuronWriter** (voie recommandee, marche meme en reseau
     restreint) : charger ses outils via ToolSearch (requete "neuronwriter"),
     creer la query, recuperer les termes, evaluer le score.
   - **API** (si l'environnement autorise l'egress vers app.neuronwriter.com) :
     `tools/neuronwriter.py` avec la cle en secret d'env `NEURONWRITER_API_KEY`
     (jamais committee). `python3 tools/neuronwriter.py new-query <project_id> "<keyword>"`
     -> `query_id` ; `get-query` pour les termes ; `evaluate` pour le score.
2. Rediger/enrichir en couvrant les **termes NLP recommandes** (titres, corps,
   FAQ, tableaux) sans bourrage — rester >= 1900 mots.
3. Evaluer : `python3 tools/neuronwriter.py evaluate <query_id> actualites/<slug>.html`.
   Si < 85 : ajouter/replacer les termes manquants et re-evaluer. Iterer jusqu'a >= 85.
   Le volume peut augmenter pour cela ; il ne descend jamais sous 1900 mots.
4. **Coller le score obtenu en marqueur** dans le `<head>` ou en haut du `<article>` :
   `<!-- NEURONWRITER SCORE: 87 query=<query_id> le AAAA-MM-JJ -->`.
   (Le QA lit ce marqueur et bloque si < 85 ou absent.)

Si NeuronWriter est indisponible (ni API ni connecteur), NE PAS publier : signaler
le blocage. Le score >= 85 est une condition de mise en ligne, pas une option.

## 6. Valider, puis publier directement sur main (auto)

```bash
python3 tools/neuronwriter.py evaluate <query_id> actualites/<slug>.html   # >= 85 (BLOQUANT)
python3 tools/preflight.py                                   # SEO de base — 0 erreur (BLOQUANT)
python3 tools/qa_article_aivf.py actualites/<slug>.html [--pilier]   # standard AIVF-killer (BLOQUANT)
python3 tools/qa_queue.py                                    # coherence de la file (BLOQUANT)
git diff --check
git checkout main
git add -A && git commit -m "Article <silo>-<id> : <sujet>"
git pull --rebase origin main                                # union+dedup si conflit sitemap
git push origin main                                         # => deploie en PROD (Cloudflare Pages)
```

Publication **directe sur `main`** = mise en production immediate ; la relecture de
Me Humbert est faite a posteriori. **Ne jamais pousser un article qui echoue le
score NeuronWriter >= 85, `preflight.py` ou `qa_article_aivf.py`** (ces garde-fous,
dont l'optimisation NeuronWriter et la verification Openlegi des jurisprudences,
remplacent le sas humain). Ne JAMAIS committer de
marqueur de conflit. Un commit = un article complet + ses 4 fichiers maillés
(sitemap, actualites, llms.txt, cocon) + `queue-aivf.json` a jour (`done` + date).
