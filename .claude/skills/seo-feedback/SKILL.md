---
name: seo-feedback
description: SQUELETTE (2026-08-27, en attente de l'action I-03). Boucle de retour Search Console sur le corpus DEJA publie (~545 articles Sanity + 2 WordPress) — diagnostic de chute de trafic, erosion lente (content decay), cannibalisation reelle, quick wins de seconde page, titles a faible CTR, et porte d'entree "reoptimiser avant de creer" des files editoriales. Utiliser quand l'utilisateur demande pourquoi le trafic baisse, ce qu'il faut corriger en priorite, quelles pages remonter, s'il faut ecrire un article ou en reoptimiser un, ou pour le point hebdomadaire/mensuel SEO. Outil : tools/gsc_report.py.
---

# Boucle de retour Search Console

Le pipeline LEXVOX est complet **en production** (termes NeuronWriter avant
redaction, jurisprudence Openlegi verifiee, QA bloquants, anti-cannibalisation)
et aveugle **apres publication** : rien ne mesure ce que deviennent les ~545
articles en ligne. Ce skill est cette boucle de retour.

Il ne remplace aucun skill existant : `/article-aivf` produit, `/nw-optimisation`
score, `/qwairy-audit-geo` mesure la visibilite dans les IA, `/preflight` valide
le HTML. Celui-ci regarde ce que le corpus publie a REELLEMENT fait, et en tire
au plus trois decisions.

## Prerequis : l'action I-03 (bloquante)

Tout ce qui suit repose sur des donnees Search Console reelles. **La propriete
GSC de lexvox-victime.com n'est pas configuree** (action **I-03** du
`SUIVI-ACTIONS-CORRECTIVES.md`, toujours ouverte, avec **I-04** pour GA4).

Tant qu'elle l'est :

- `tools/gsc_report.py --api` **refuse de repondre** (code retour 2) plutot que
  de rendre un rapport vide qui passerait pour un site en bonne sante ;
- le mode `--csv` fonctionne des aujourd'hui sur un export manuel de
  l'interface GSC d'un site qui en a une (les deux WordPress, si la propriete
  existe) ;
- **ne jamais combler le trou par une estimation.** Un chiffre invente dans un
  rapport SEO a exactement la meme allure qu'un chiffre mesure. Si la donnee
  manque, le dire.

Premiere chose a faire si Me Humbert demande ce rapport et que I-03 est
toujours ouverte : le signaler, et proposer de la traiter (creer la propriete,
soumettre `https://lexvox-victime.com/sitemap.xml`, lier GA4).

## Les seuils (ils font tout le travail)

Un diagnostic sans seuil rend vingt recommandations, c'est-a-dire aucune
decision. Les seuils vivent dans `tools/gsc_report.py` — les ajuster la, jamais
au cas par cas dans un rapport.

| Analyse | Seuil | Pourquoi celui-la |
|---|---|---|
| Chute de trafic | tri par **clics perdus en valeur absolue** | Une page qui perd 80 % de 12 clics n'est pas le sujet. Le volume absolu designe les 2-3 pages qui expliquent l'essentiel de la chute. |
| Cause de la chute | impressions / CTR / position, separement | Transforme "Google nous en veut" en une cause unique avec une action unique derriere. |
| Cannibalisation | **>= 2 URLs a plus de 50 impressions** sur une requete | Sous 50, deux URLs sur une meme requete relevent du hasard. |
| Page cible d'un conflit | **meilleure position ET meilleur CTR** | Si les deux se contredisent, l'outil ne tranche pas a notre place : il le dit, et on arbitre sur le sujet reellement traite. |
| Content decay | **2 periodes consecutives de baisse** | Une baisse isolee est du bruit. Deux d'affilee sont le seul signal fiable d'une erosion reelle. |
| Quick wins | **positions 11-20, > 200 impressions** | Le meilleur rapport effort/resultat du corpus : la page est deja comprise par Google. |
| Titles | **CTR sous la moitie de l'attendu** pour la position | En dessous de cet ecart, c'est de la variation normale. |
| Rapport | **3 actions maximum** | Au-dela, on n'hierarchise plus, on inventorie. |

## Commandes

```bash
# Le point hebdomadaire (10 min) — ce qui a bouge, puis 3 actions
python3 tools/gsc_report.py synthese --csv exports/2026-08/ --csv exports/2026-07/

# Le point mensuel (30 min)
python3 tools/gsc_report.py chute  --csv exports/2026-08/ --csv exports/2026-07/
python3 tools/gsc_report.py decay  --csv exports/2026-08/ --csv exports/2026-07/ --csv exports/2026-06/
python3 tools/gsc_report.py quickwins --csv exports/2026-08/

# Ponctuel
python3 tools/gsc_report.py titres          --csv exports/2026-08/
python3 tools/gsc_report.py cannibalisation --csv exports/2026-08/
python3 tools/gsc_report.py reoptimiser --keyword "<mot-cle>" --csv exports/2026-08/
```

Les exports sont a placer hors du depot ou dans un dossier ignore : ce sont des
donnees de performance, pas du contenu editorial. Repeter `--csv` de la periode
la plus **recente** a la plus **ancienne**.

`cannibalisation` et `reoptimiser` ont besoin du croisement **requete x page**,
qu'un export standard de l'interface GSC ne contient pas (onglets Requetes et
Pages separes). L'outil le signale et s'arrete en code 2 : il faut l'API ou un
export Looker Studio portant les deux colonnes.

## Ce qu'on fait des resultats

1. **Reoptimiser avant de creer.** C'est la sortie la plus utile du skill, et
   la porte d'entree des deux files editoriales (`queue-aivf.json`,
   `queue-wp.json`, cf. `/article-aivf` §0bis). Si `reoptimiser` montre qu'une
   page capte deja l'intent : passer l'item en `status: "reoptimiser"` avec
   `"reoptimise_url"`, et **enrichir la page existante** — recuperer toutes ses
   requetes reelles, les comparer a ce qu'elle traite, ajouter les sections
   manquantes. Publier un second article sur cet intent fabriquerait la
   cannibalisation qu'on passerait ensuite du temps a reparer.
2. **Ne jamais proposer "reecrire l'article".** Dire quelles **sections**
   ajouter ou refaire, en s'appuyant sur ce que couvrent les pages qui nous
   depassent aujourd'hui (les relever avec `/recherche-web`, jamais avec les
   outils natifs).
3. **Ne jamais supprimer une page qui recoit des clics.** Sur un conflit :
   desoptimiser la perdante (title, H1), fusionner avec une 301, ou poser un
   lien interne vers la cible avec l'ancre exacte.
4. **Controler la saisonnalite avant d'agir sur un decay.** Si la meme page
   baissait deja a la meme periode l'an dernier, la sortir de la liste — sinon
   on reecrit des pages qui remonteraient seules. Le dommage corporel a des
   cycles reels (vacances, rentree judiciaire).
5. **Tracer.** Les actions retenues vont dans `SUIVI-ACTIONS-CORRECTIVES.md`
   (c'est son role) ; une reoptimisation effectuee se note dans
   `PUBLICATION-TRACKER.md` ou `PUBLICATION-TRACKER-WP.md`.
6. **Une page reoptimisee repasse par les garde-fous** : `/nw-optimisation`
   (score >= 85), `qa_article_aivf.py`, puis republication Sanity via
   `tools/sanity_publish.py` (jamais de deploiement de ce depot — cf. l'incident
   du 2026-07-06 dans `CLAUDE.md`).

## Cadence

- **Chaque lundi, 10 min** : `synthese` sur 7 jours. Ce qui a bouge, la seule
  action qui en sort.
- **Chaque mois, 30 min** : `chute`, `decay`, `quickwins`.
- **Chaque trimestre** : `cannibalisation` sur l'ensemble du corpus (c'est la
  seule analyse qui exige de regarder les 545 articles ensemble), et revue de
  la file a la lumiere de `reoptimiser`.
- **A chaque item de file** : `reoptimiser --keyword` avant de rediger.

## Limites assumees

- **Netlinking** : hors perimetre. Analyser les backlinks des concurrents
  demande une source de donnees (type Ahrefs) que le cabinet n'a pas.
- **Technique / Core Web Vitals** : le site en production est le frontend
  Next.js + Sanity, qu'on ne modifie **que sur demande expresse de Me Humbert**.
  Un constat d'indexation (sitemap vs index) est utile ; le correctif passe par
  le projet Next.js, pas par ce depot.
- **Interventions sur les forums (Reddit, Quora)** : ne jamais automatiser.
  Pour un avocat, une intervention publique touche aux regles de publicite et
  de sollicitation du RIN et au secret professionnel. Toute demarche de ce type
  passe par Me Humbert, et se verifie au besoin avec `/deontologie`.
- **Visibilite dans les IA** : couverte par `/qwairy-audit-geo`. Ce skill ne la
  redouble pas ; sa contribution GEO est la regle de **citabilite des reponses
  FAQ** appliquee a la redaction (`/article-aivf` §2).
