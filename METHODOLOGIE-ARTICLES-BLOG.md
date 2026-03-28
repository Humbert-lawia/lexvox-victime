# Methodologie de redaction d'un article de blog — lexvox-victime.fr

> Document de reference pour la creation de chaque article publie sur le site.
> Toutes les regles sont imperatives et non negociables.

---

## 1. Pipeline de publication (4 etapes obligatoires)

| Etape | Outil | Objectif |
|-------|-------|----------|
| 1. Generation | Multi-Agent SEO Blog Generator (Gemini 2.5 Flash) | Brouillon optimise avec prompts juridiques |
| 2. Enrichissement juridique | MCP Lexbase | Verifier et enrichir les references jurisprudentielles |
| 3. Optimisation SEO | YourTextGuru | DSEO < 7% obligatoire, SEO maximum |
| 4. Publication | Conversion HTML + deploiement Netlify | Integration au site avec template standard |

**Aucun article ne doit etre publie sans avoir passe les 4 etapes.**

---

## 2. Regles de contenu

### 2.1 Volume et langue
- **2 000 a 2 500 mots** par article
- Redige en **francais** avec accents corrects (UTF-8)
- Vocabulaire centre sur les **victimes** (empathique, simple, pas de jargon non explique)
- Tutoiement interdit — toujours le vouvoiement

### 2.2 SEO / GEO / LLMO / AEO
- Chaque section commence par une **reponse directe en 40-60 mots** extractible par les moteurs IA
- **Une statistique verifiable** tous les 150-200 mots (source nommee)
- **Termes juridiques definis inline** a leur premiere utilisation : "Le DFP (deficit fonctionnel permanent — le taux d'incapacite definitive evalue par l'expert medical)"
- **Citations legales precises** : "Article L1142-1 du Code de la sante publique", "Loi n° 85-677 du 5 juillet 1985 (dite Loi Badinter)"
- Structure hierarchique : **H1 > H2 > H3 > H4**, jamais de saut de niveau

### 2.3 DSEO (YourTextGuru)
- **DSEO < 7%** obligatoire avant publication
- **SEO maximum** (objectif SOSEO > 60%)
- Pour atteindre DSEO < 7% : chaque mot-cle ne doit apparaitre que **3 a 5 fois maximum** dans tout l'article
- Utiliser systematiquement des **synonymes et periphrases** pour varier le vocabulaire :
  - "erreur medicale" → "faute de soins", "manquement therapeutique", "incident clinique"
  - "victime" → "patient lese", "personne concernee"
  - "indemnisation" → "reparation", "compensation", "dedommagement"
  - "avocat" → "conseil juridique", "defenseur", "professionnel du droit"
  - "medecin" → "praticien", "soignant", "professionnel de sante"
  - "expertise" → "evaluation", "examen", "analyse"
  - "prejudice" → "dommage", "tort", "atteinte"

### 2.4 Deontologie (obligation de moyens)
- **JAMAIS** promettre de resultat
- **JAMAIS** ecrire "pas d'honoraires sans resultat", "aucun frais a avancer", "si nous n'obtenons rien vous ne payez rien"
- **Honoraires** : part fixe a partir de 700 EUR HT + pourcentage de 10 a 15% HT au resultat
- **Slogan** : "Expertise medicale, juridique et IA"
- Valoriser les **competences et moyens deployes**, pas les resultats

---

## 3. Mots-cles geographiques — OBLIGATOIRE

Chaque article **DOIT** mentionner les 4 villes des bureaux au moins une fois :
- **Aix-en-Provence**
- **Salon-de-Provence**
- **Arles**
- **Marignane**

Integrations naturelles :
- "Nos bureaux d'Aix-en-Provence, Salon-de-Provence, Arles et Marignane sont a votre disposition."
- "Me Humbert intervient depuis ses bureaux d'Aix-en-Provence, Salon-de-Provence, Arles et Marignane."
- Dans la FAQ : "Intervenez-vous dans ma ville ?" → mentionner les 4 villes + "toute la France"

Pour les articles SEO local (Marseille, Nimes) : cibler la ville dans le titre + 10 mentions minimum.

---

## 4. Liens — OBLIGATOIRE

### 4.1 Maillage interne (minimum 5 liens par article)
- Liens vers les pages principales du site :
  - `/accident-de-la-route.html`
  - `/responsabilite-medicale.html`
  - `/indemnisation-prejudice-corporel.html`
  - `/expertise-medicale.html`
  - `/nomenclature-dintilhac.html`
  - `/procedure-indemnisation.html`
  - `/contact.html`
  - `/cabinet.html`
  - `/actualites.html`
- Liens vers d'autres articles du blog (minimum 3 via la section "Articles lies")
- Tous les liens utilisent l'extension `.html`

### 4.2 Liens externes institutionnels (minimum 2 par article)
- Chaque article doit contenir **minimum 2 liens externes** vers des sites gouvernementaux ou institutionnels
- Ouvrent dans un nouvel onglet : `target="_blank" rel="noopener"`
- Integres naturellement dans le texte (pas en liste separee)
- Sites cibles :
  - Legifrance.gouv.fr (textes de loi)
  - Service-public.fr (droits des victimes)
  - ONIAM.fr (indemnisation accidents medicaux)
  - Ameli.fr (CPAM, accidents du travail)
  - Justice.gouv.fr (procedures judiciaires)
  - ONISR / securite-routiere.gouv.fr (securite routiere)
  - HAS / has-sante.fr (haute autorite de sante)

---

## 5. Structure HTML de chaque article

### 5.1 Ordre des elements dans le hero

```
1. Breadcrumb (Accueil > Actualites > Titre article)
2. Overline (ex: "AVOCAT ERREUR MEDICALE AIX-EN-PROVENCE")
3. Ink separator (trait bleu decoratif)
4. H1 (titre principal avec mot-cle en .accent)
5. Image article (Imagen 4.0, max-height 250px, lazy loading)
6. Date + Auteur ("28 mars 2026 — Par Me Patrice Humbert")
7. Temps de lecture ("Temps de lecture : X min" — calcul : mots / 250)
8. Boutons partage social (LinkedIn, X, Facebook, Email)
9. Quick-answer (40-60 mots, reponse directe)
10. Boutons CTA ("Consultation gratuite" + lien section)
11. Plan de lecture / Table des matieres (TOC)
```

**Le plan de lecture est TOUJOURS apres l'image, jamais avant.**
**Le plan ne doit JAMAIS etre fixe (position: static obligatoire).**

### 5.2 Plan de lecture (TOC)

- Structure imbriquee avec H2 (items principaux) et H3 (sous-items indentes)
- Liens ancres vers chaque section (`#id-section`)
- Collapsible via JS (clic sur "Plan de lecture")
- CSS classes : `.toc`, `.toc-list`, `.toc-sublist`
- `position: static !important` (ne doit jamais rester fixe au scroll)

Exemple :
```html
<nav class="toc" aria-label="Plan de lecture">
  <div class="toc-title">Plan de lecture</div>
  <ol class="toc-list">
    <li><a href="#section1">Titre H2</a>
      <ul class="toc-sublist">
        <li><a href="#sous-section1">Sous-titre H3</a></li>
        <li><a href="#sous-section2">Sous-titre H3</a></li>
      </ul>
    </li>
    <li><a href="#section2">Titre H2</a></li>
  </ol>
</nav>
```

### 5.3 Sections de contenu

- Alterner les fonds : `var(--creme)` → `section-bleu-pale` → `#fff` → `section-bleu-pale`
- **PAS de fond noir** (section-dark) dans le corps de l'article
- Fond noir reserve UNIQUEMENT a la derniere section CTA en bas
- Chaque section a un `id` pour les ancres du plan de lecture
- Utiliser les composants CSS : `.quick-answer`, `.data-table`, `.callout`, `.callout-or`

### 5.4 Bloc auteur (AVANT la FAQ)

```html
<div class="article-author">
  <img src="../img/photo-humbert.jpg" alt="Me Patrice Humbert" width="80" height="80">
  <div class="article-author-info">
    <h4>Me Patrice Humbert</h4>
    <p>Avocat au Barreau d'Aix-en-Provence — Plus de 20 ans d'experience</p>
    <div class="badge-or">1er avocat certifie IA de France</div>
    <p><a href="/cabinet.html">En savoir plus sur le cabinet</a></p>
  </div>
</div>
```

### 5.5 FAQ (6-8 questions minimum)

- Schema JSON-LD FAQPage obligatoire
- Structure HTML : `<details>` / `<summary>`
- Premiere phrase de chaque reponse en **gras** (reponse directe)
- CSS class : `.faq-section`

### 5.6 Articles lies (APRES la FAQ, AVANT le CTA)

```html
<div class="related-articles">
  <h3>Articles qui pourraient vous interesser</h3>
  <div class="related-grid">
    <a href="/actualites/SLUG.html" class="related-card">
      <h4>Titre</h4>
      <p>Description courte</p>
    </a>
    <!-- 3 articles lies, jamais l'article lui-meme -->
  </div>
</div>
```

### 5.7 CTA final (derniere section, fond noir)

```html
<section class="section-dark" style="text-align: center;">
  <div class="container">
    <h2>Premiere consultation <span style="color: var(--or);">gratuite</span></h2>
    <p>Nous evaluons votre dossier gratuitement en 30 minutes.</p>
    <a href="tel:+33490545810" class="btn btn-phone">04 90 54 58 10</a>
    <a href="/contact.html" class="btn btn-light">Demander un rappel</a>
  </div>
</section>
```

---

## 6. Schemas JSON-LD (triple stack obligatoire)

Chaque article doit avoir 3 blocs JSON-LD dans le `<head>` :

### 6.1 Article
```json
{
  "@type": "Article",
  "headline": "Titre de l'article",
  "datePublished": "2026-XX-XX",
  "dateModified": "2026-XX-XX",
  "author": {
    "@type": "Person",
    "name": "Patrice Humbert",
    "honorificPrefix": "Me"
  },
  "publisher": {
    "@type": "Organization",
    "name": "SELARL LEXVOX AVOCATS"
  }
}
```

### 6.2 FAQPage
```json
{
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Question ?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Reponse directe."
      }
    }
  ]
}
```

### 6.3 BreadcrumbList (3 niveaux)
```json
{
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"position": 1, "name": "Accueil", "item": "https://lexvox-victime.fr/"},
    {"position": 2, "name": "Actualites", "item": "https://lexvox-victime.fr/actualites"},
    {"position": 3, "name": "Titre article"}
  ]
}
```

---

## 7. Meta tags (head)

| Tag | Format |
|-----|--------|
| Title | `{Titre article} \| LEXVOX AVOCATS` (max 60 car.) |
| Meta description | 140-160 car., mot-cle + benefice victime + CTA |
| Canonical | `https://lexvox-victime.fr/actualites/{slug}` |
| OG type | `article` |
| OG image | `https://lexvox-victime.fr/img/articles/{slug}.png` |
| Twitter card | `summary_large_image` |

---

## 8. Image article

- Generee par **Imagen 4.0** via l'API Google
- Format : 16:9, sans texte
- Style : professionnel, institutionnel, tons creme et bleu
- Pas de visages humains (`personGeneration: 'dont_allow'`)
- Sauvegardee dans `/img/articles/{slug}.png`
- HTML : `max-height: 250px`, `object-fit: cover`, `loading="lazy"`, `border-radius: 12px`

---

## 9. Informations du cabinet (a integrer dans chaque article)

| Champ | Valeur |
|-------|--------|
| Cabinet | SELARL LEXVOX AVOCATS |
| Avocat | Me Patrice Humbert |
| Barreau | Aix-en-Provence |
| Distinction | 1er avocat certifie en intelligence artificielle de France |
| Experience | Plus de 20 ans en dommage corporel |
| Diplomes | Master Droit de la sante, DU Sciences criminelles, Formation traumatisme cranio-cerebral |
| Specialisation | CNB dommage corporel |
| Bureaux | Aix-en-Provence, Salon-de-Provence, Arles, Marignane |
| Telephone | 04 90 54 58 10 |
| Email | contact@avocat-lexvox.com |
| Honoraires | Part fixe a partir de 700 EUR HT + 10-15% HT au resultat |
| Consultation | Gratuite, 30 minutes |
| Reseaux | LinkedIn, YouTube, Instagram, TikTok |

---

## 10. Apres publication — checklist

- [ ] Article dans le sitemap.xml
- [ ] Redirect dans _redirects (Netlify)
- [ ] Lien ajoute sur la page actualites.html
- [ ] Cache bust CSS incremente (`?v=X`)
- [ ] Maillage interne verifie (liens entrants depuis autres pages)
- [ ] Navigation testee (page accessible depuis le menu)
- [ ] Schemas JSON-LD valides (Google Rich Results Test)
- [ ] Responsive verifie (mobile + desktop)
- [ ] Pas de "18 ans" (toujours "plus de 20 ans")
- [ ] Pas de "6 bureaux" (toujours "4 bureaux")
- [ ] Pas de Marseille/Nimes en tant que bureaux
- [ ] Pas de promesse de resultat
- [ ] 4 villes mentionnees dans le texte
- [ ] 2 liens externes institutionnels minimum
- [ ] DSEO < 7% sur YourTextGuru
- [ ] Git commit + push (auto-deploy Netlify)

---

*Document cree le 28 mars 2026 — SELARL LEXVOX AVOCATS / LAWIA*
*Derniere mise a jour : 28 mars 2026*
