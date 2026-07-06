---
name: article-aivf
description: Produire un article de fond haut de gamme selon le PIPELINE LEXVOX-AIVF (gabarit augmente pour surpasser le concurrent AIVF) — analyse jurisprudentielle, 2+ tableaux, infographie SVG inline, puis maillage, sitemap, actualites.html, llms.txt et preflight. Utiliser pour tout article issu de la file queue-aivf.json ou quand l'utilisateur demande un article "qualite AIVF-killer".
---

# Produire un article — PIPELINE LEXVOX-AIVF

Ce skill **remplace `/nouvel-article` pour les articles du plan de bataille anti-AIVF**.
Il reprend toute la mecanique de maillage (`/nouvel-article`) et ajoute les
**3 signatures de differenciation** imposees par l'audit
(`AUDIT-COMPARATIF-AIVF-2026-07.md`) et le manuel `PIPELINE-LEXVOX-AIVF.md`.

Ne jamais s'arreter apres la seule creation du HTML : un article non maille est orphelin.

## 0. Choisir le sujet dans la file

- Ouvrir `queue-aivf.json`. Prendre le **premier article `status: "todo"`** dans l'ordre
  du tableau (l'ordre EST la strategie : quick win -> Silo A -> B -> E -> F -> C -> D -> G -> H -> I -> J).
- Passer son `status` a `"in_progress"`, produire, puis `"done"` + `"date"` (AAAA-MM-JJ) une fois pousse.
- `type: "pilier"` => cible 3000+ mots ; `type: "feuille"` => 1800+ mots.
- Cas special id 1 : publier le `.docx` existant de Me Humbert (article IA/Village de la Justice),
  ne pas le re-rediger de zero — le convertir au gabarit.

## 1. Sourcer le droit AVANT de rediger (non negociable)

C'est ce qui nous rend meilleurs qu'AIVF (eux : zero jurisprudence citee).
Rassembler, via les MCP juridiques disponibles (Openlegi / Lexbase — charger par ToolSearch) :

- **1 a 2 decisions reelles** pertinentes (Cass. civ. 2e de preference en dommage corporel,
  ou CE, ou CA) : juridiction, date, n° de pourvoi/role, principe pose. Verifier qu'elles existent.
- Les **articles de loi** applicables (Code civil, Code de la route/loi Badinter, Code de la sante
  publique, Code des assurances) — citer le numero exact.
- Les **baremes/chiffres** : referentiel Mornet (PDF dans le repo), echelle pretium doloris 1–7,
  barticle AIPP, fourchettes indicatives. Toujours dire "a titre indicatif, souverainete du juge".

Si un MCP juridique est indisponible, ne pas inventer de reference : se rabattre sur des textes
verifiables (Legifrance, service-public.fr — jamais `.gouv.fr`) et le signaler dans le commit.

## 2. Rediger dans le gabarit augmente

Partir d'un article recent conforme comme squelette (hero, nav, footer, JSON-LD).
Structure **obligatoire** (dans l'ordre) :

1. Hero avec image jpg + `<h1>` unique (<= 100 car.).
2. `quick-answer` : reponse directe en 2–3 phrases (featured snippet).
3. `toc` (sommaire ancre).
4. 5–7 sections `<h2>` (avec `<h3>` pour les sous-postes).
5. **>= 2 tableaux `<table class="data-table">`** (barème/fourchettes, comparatif, checklist chiffree…).
6. **>= 1 infographie schema `<figure class="infographic">` avec `<svg>` inline** (cf. §3).
7. **>= 1 bloc `<div class="juris-block">`** — l'analyse jurisprudentielle (cf. §4).
8. FAQ 6 questions (`<details>`) — memes questions que le JSON-LD FAQPage.
9. Bloc auteur (Me Patrice Humbert) + CTA + 3 cartes "articles lies".

Contraintes bloquantes (identiques `/nouvel-article`) :
- `<title>` <= 60 car. ; meta description 120–155 car., non vide.
- `canonical` = `og:url` = `https://lexvox-victime.com/actualites/<slug>` (domaine `.com`, **sans** `.html`).
- 4 blocs JSON-LD valides (`LegalService`, `Article` avec `image`, `FAQPage`, `BreadcrumbList`) —
  JSON pur, aucune balise HTML dedans.
- Coordonnees cabinet reprises de `mentions-legales.html`, rien d'invente.
- Volume : feuille >= 1800 mots, pilier >= 3000 mots.

## 3. L'infographie SVG inline (au moins une)

Format retenu : **SVG inline** (net en Retina, indexable, accessible, zero asset binaire, zero build).
Le CSS `.infographic` / `.ig-*` est deja dans `css/style.css`. Choisir l'archetype qui sert le sujet :

- **Flux / procedure** (etapes numerotees + fleches) — ex. procedure CCI/CRCI, saisine CIVI.
- **Echelle / barème** (graduation 1–7, paliers) — ex. pretium doloris, AIPP.
- **Timeline / delais** (axe horizontal date -> consolidation -> prescription).
- **Repartition** (barres/parts des postes de prejudice dans une indemnisation type).

Squelette minimal (adapter viewBox et contenu) :

```html
<figure class="infographic">
  <figcaption>Les 4 etapes de la procedure CCI/CRCI</figcaption>
  <svg viewBox="0 0 800 200" role="img" aria-label="Schema des 4 etapes de la procedure CCI/CRCI">
    <defs>
      <marker id="igArrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
        <path d="M0,0 L8,3 L0,6 Z" class="ig-fill"/>
      </marker>
    </defs>
    <!-- boites .ig-box / .ig-box-accent, texte .ig-t + .ig-label, fleches .ig-arrow -->
  </svg>
  <p class="ig-source">Source : art. L.1142-1 et s. Code de la sante publique.</p>
</figure>
```

Regles : `role="img"` + `aria-label` descriptif obligatoires ; utiliser les classes `.ig-*`
(pas de couleur en dur) pour rester coherent light/dark ; garder le SVG sobre et lisible mobile.

## 4. Le bloc d'analyse jurisprudentielle (la signature LEXVOX)

Un encadre `.juris-block` par article minimum. C'est le paragraphe qui nous differencie : AIVF
n'en a aucun. Il doit **analyser** une decision reelle, pas la citer platement.

```html
<div class="juris-block">
  <span class="juris-tag">Analyse jurisprudentielle</span>
  <h3>Ce que dit la Cour de cassation sur ...</h3>
  <p>Dans un arret <span class="juris-ref">Cass. civ. 2e, 12 mai 2022, n° 20-XX.XXX</span>,
     la Cour a juge que ... . Concretement pour la victime, cela signifie ... .</p>
  <p><strong>Notre lecture de praticien :</strong> ... (angle avocat qui plaide, valeur ajoutee E-E-A-T).</p>
  <cite>Cass. civ. 2e, 12 mai 2022, n° 20-XX.XXX ; art. XXXX Code civil.</cite>
</div>
```

Le paragraphe "Notre lecture de praticien" est ce qui incarne l'expertise de Me Humbert :
toujours le renseigner. Ne jamais inventer un numero de pourvoi — le verifier au §1.

## 5. Mailler les 4 fichiers (systematique)

1. `sitemap.xml` : `<url>` + `lastmod` du jour, sans doublon.
2. `actualites.html` : carte dans la bonne categorie + compteur de categorie ; pilier => envisager "A la une".
3. `llms.txt` : ligne dans les articles recents.
4. Maillage interne : 3–5 liens vers les piliers du silo (le HUB du silo d'abord) + liens croises
   vers les articles freres. Mettre a jour `queue-aivf.json` (`status: "done"`, `date`).

## 6. Valider et pousser

```bash
python3 tools/preflight.py                       # SEO de base — 0 erreur bloquante
python3 tools/qa_article_aivf.py actualites/<slug>.html [--pilier]   # standard AIVF-killer
git diff --check
git pull --rebase origin main                    # main bouge (bots) — union+dedup sitemap si conflit
```

Ne JAMAIS committer de marqueur de conflit. Un commit = un article complet + ses 4 fichiers maillés
+ `queue-aivf.json` a jour. Message de commit clair (sujet + silo).
