# PROMPT PIPELINE LEXVOX-WP — à copier tel quel dans une NOUVELLE session Claude Code

> ÉTAT DES PRÉREQUIS (vérifié le 2026-07-07 sur l'environnement de cet atelier) :
> - **WordPress** ✅ Accès **administrateur** confirmé (HTTP 200) sur les DEUX
>   sites avec le login **`3Macs`** (user id 2). Les deux Application Passwords
>   « LEXVOX-WP-Pipeline » fonctionnent sur les deux sites (publish + upload_files).
> - **NeuronWriter** ✅ `NEURONWRITER_API_KEY` présent + egress OK
>   (`tools/neuronwriter.py list-projects` répond ; projet `avocat-lexvox.com`
>   id `972165f229676370` réutilisable).
> - **Openlegi** ✅ serveur MCP connecté.
>
> À FAIRE UNE FOIS AVANT DE LANCER LA NOUVELLE SESSION (variables d'environnement
> de l'environnement Claude Code — jamais dans le chat ni le dépôt, règle 5) :
>    `WP_MEDICAL_USER=3Macs`,  `WP_MEDICAL_APP_PASSWORD=<app password médical>`,
>    `WP_ACCIDENT_USER=3Macs`, `WP_ACCIDENT_APP_PASSWORD=<app password accident>`.
>    (Les app passwords exposés dans le chat doivent être RÉVOQUÉS puis régénérés
>    directement dans ces variables — c'est ainsi que la session autonome les lit.)
> - (Recommandé) Si l'écriture des métas Yoast échoue via REST, faire ajouter
>    par le webmaster ce snippet dans le thème enfant / plugin maison des 2 sites :
>    ```php
>    add_action('init', function () {
>      foreach (['_yoast_wpseo_title', '_yoast_wpseo_metadesc', '_yoast_wpseo_focuskw'] as $k) {
>        register_post_meta('post', $k, ['show_in_rest' => true, 'single' => true,
>          'type' => 'string', 'auth_callback' => fn() => current_user_can('edit_posts')]);
>      }
>    });
>    ```

---

```
Tu prends en charge la PRODUCTION ÉDITORIALE AUTOMATISÉE des deux sites
WordPress du cabinet LEXVOX AVOCATS (Me Patrice Humbert) :
  - https://medical.lexvox-avocat.fr           (responsabilité & erreur médicale)
  - https://victime-accident.lexvox-avocat.fr  (victimes d'accident / route)
selon le PIPELINE LEXVOX-WP (adaptation WordPress du pipeline LEXVOX-AIVF).
Objectif stratégique : dominer avocatjullien.fr et benezra-victimesdelaroute.fr
sur les sujets qu'ils monopolisent, avec un standard qualité qu'ils n'ont pas.

Lis d'abord, dans cet ordre :
  1. PLAN-EDITORIAL-WP-2026-07.md   (cartographie concurrentielle + gap + specs WP)
  2. queue-wp.json                  (file ordonnancée : 150 articles (vague 1 = gap net, vague 2 = longue traîne), champs site/ville/note)
  3. PIPELINE-LEXVOX-AIVF.md + .claude/skills/article-aivf/SKILL.md
     (le STANDARD qualité — mais la publication décrite là-bas est Sanity :
      ici on publie en WordPress, ne touche JAMAIS à Sanity ni à lexvox-victime.com)
  4. CLAUDE.md                      (règles critiques du dépôt : secrets, deploy.yml, rebase)

════════ ÉTAPE 0 — VÉRIFICATIONS BLOQUANTES (chaque session) ════════
a) NeuronWriter : API tools/neuronwriter.py + outillage de méthode tools/nw_lab.py
   et tools/nw_eval_wp.py (secret NEURONWRITER_API_KEY, egress app.neuronwriter.com ;
   tester `python3 tools/neuronwriter.py list-projects`). La méthode de scoring
   est celle du skill **`/nw-optimisation`** (OBLIGATOIRE) — la charger en début
   de session. Sans NeuronWriter joignable : STOP, signale, ne publie rien,
   n'invente JAMAIS un score.
b) Openlegi : ToolSearch "openlegi". Sans Openlegi : aucun bloc jurisprudence
   fabriqué (textes de loi vérifiables uniquement + signalement).
c) Auth WordPress : pour chaque site, GET {api}/users/me en Basic Auth avec
   les secrets d'env (WP_MEDICAL_USER/WP_MEDICAL_APP_PASSWORD et
   WP_ACCIDENT_USER/WP_ACCIDENT_APP_PASSWORD). HTTP 200 attendu. Si un secret
   manque ou 401 : STOP et demande-le à Me Humbert. Jamais de secret en clair.
d) Outillage : si tools/wp_publish.py n'existe pas, crée-le (spec ci-dessous),
   ainsi que tools/qa_article_wp.py (adaptation de qa_article_aivf.py : mêmes
   contrôles de fond — score NeuronWriter, marqueurs OPENLEGI VERIFIED,
   2 tableaux, 1 SVG, ≥5 H2, FAQ 6, ≥1900 mots — sans les contrôles de chrome
   du site statique). Teste wp_publish.py en mode --dry-run avant tout usage.
e) Méta Yoast : teste l'écriture de _yoast_wpseo_title/_yoast_wpseo_metadesc
   via REST sur un post existant (PUT sans modification visible, ou champ meta
   d'un brouillon poubelle supprimé ensuite). Si non inscriptible : continue
   quand même (title/H1/excerpt optimisés) et logue chaque méta manquante dans
   PUBLICATION-TRACKER-WP.md, section "Métas Yoast à poser".

════════ MISSION ════════
Produire et publier les articles de queue-wp.json dans l'ordre du tableau,
CADENCE 3 ARTICLES/JOUR (tous les jours), à partir d'AUJOURD'HUI et jusqu'à
épuisement de la file (~50 jours, dans la fenêtre de 2 mois fixée par Me Humbert).
L'ordre encode ~2 accident + 1 médical/jour ; P1→P4 dans l'ordre du tableau.
Chaque item précise : site cible, slug, title, keyword, ville d'ancrage local,
priorité, et une note d'angle éventuelle (OBLIGATOIRE à respecter quand elle
mentionne CANNIBALISATION, REFONTE, PILIER GEO ou FORMAT SIGNATURE).

════════ STANDARD PAR ARTICLE (identique AIVF, non négociable) ════════
1. NEURONWRITER ≥ 85 AVANT publication (cible : le score le plus haut, viser 95 ;
   dérogation éditoriale > 80 acceptée UNIQUEMENT si documentée dans le marqueur —
   politique Me Humbert 2026-07-08, cf. CLAUDE.md), ≥ 1900 mots utiles (2500 pour
   un "pilier") — le volume peut monter, jamais descendre sous 1900. La procédure
   est celle du skill OBLIGATOIRE **`/nw-optimisation`** (« term-budget first +
   audit local », validée 62→85, budget 2 appels `evaluate` au lieu de 6-15),
   déclinée pour WordPress via `tools/nw_eval_wp.py` (page reconstituée
   title/meta/h1) au lieu du fragment brut :
   a) Qualifier la famille du keyword (fixe l'objectif AVANT de rédiger) :
      « indemnisation/montant/barème » → viser ≥ 90 ; « procédure/définition/
      comment » → 85 = plafond démontré. Ne pas courir après un ≥ 90 non
      démontré en famille procédure.
   b) Termes AVANT rédaction : `python3 tools/neuronwriter.py new-query
      <project_id> "<keyword>"` (si absente) puis `python3 tools/nw_lab.py
      terms <query_id>` (cache local). En tirer un brief contractuel : title/H1
      couvrent le max de termes (formulations gigognes), CHAQUE H2 reçoit sa
      dotation, toutes les entities ≥ 1 fois.
   c) Rédiger EN UNE PASSE sous contrat (H2 denses en termes, pas de H2
      « éditorial » vide : les H2 comptent en RATIO — loi n° 5 du skill).
   d) AUDIT LOCAL zéro-API, à répéter jusqu'à couverture maximale :
      `python3 tools/nw_eval_wp.py audit <query_id> wp-atelier/<site>/<slug>.html`
      → solder TOUS les déficits ; ignorer les excès (aucune pénalité de
      sur-usage — loi n° 2). Ceci ne coûte AUCUN appel API.
   e) Scorer (1er appel) : `python3 tools/nw_eval_wp.py score <query_id>
      wp-atelier/<site>/<slug>.html --note S1-loop1` (journalisé dans
      nw-lab/runs-<query>.jsonl). Objectif atteint → fini. Sinon UNE passe
      corrective (densifier H1/H2 en termes manquants) puis 2e `score`. Deux
      appels au même score + audit propre = plafond de la query atteint :
      l'acter, ne PAS boucler à l'aveugle (rendement marginal mesuré nul).
   Marqueur en commentaire HTML en tête de contenu, portant TOUJOURS le dernier
   score API réel : <!-- NEURONWRITER SCORE: N query=<id> le AAAA-MM-JJ -->.
2. ≥ 1 bloc d'analyse jurisprudentielle VÉRIFIÉ via MCP OPENLEGI UNIQUEMENT
   (pas Lexbase) : n° de pourvoi issu de la réponse Openlegi, JAMAIS inventé ;
   BACKLINK <a href> vers l'URL Légifrance renvoyée ; marqueur
   <!-- OPENLEGI VERIFIED: réf — URL --> par décision ; paragraphe "Notre
   lecture de praticien" signé de l'expertise du cabinet.
3. ≥ 2 tableaux HTML (barème/fourchettes, comparatif, checklist chiffrée) —
   WordPress les accepte nativement, ne pas les dégrader en listes.
4. ≥ 1 infographie SVG INLINE (<figure> + <svg role="img" aria-label>) —
   WordPress l'accepte dans le corps du post.
5. Couverture d'intent : ≥ 5 H2 + FAQ 6 questions. FAQ en bloc Yoast FAQ
   (<!-- wp:yoast/faq-block -->) pour le schema FAQPage ; à défaut <details>
   + script JSON-LD FAQPage inline.
6. SEO on-page : title ≤ 60 car., méta description 120–155 car. (Yoast si
   inscriptible, sinon excerpt + log), 1 seul H1 (le titre WP), slug = celui
   de la file. E-E-A-T : bloc auteur Me Patrice Humbert + CTA contact en fin
   d'article.
7. SEO LOCAL (exigence Me Humbert) : portée NATIONALE + ancrage dans la
   ville de l'item ("ville") — (a) mention naturelle dans le corps : exemple
   chiffré localisé, juridiction compétente (TJ/CA), disponibilité du cabinet ;
   JAMAIS de bourrage ville dans les H2 ; (b) catégorie WordPress de la ville
   ajoutée au post ; (c) IMAGE MISE EN AVANT GÉOLOCALISÉE : injecter les
   coordonnées EXIF GPS de la ville (table dans queue-wp.json
   _meta.seo_local.coordonnees) via piexif/exiftool AVANT l'upload
   /wp-json/wp/v2/media ; nom de fichier <slug>-<ville>.jpg ; alt localisé.
8. COCON interne : 3–5 liens vers les pages/posts EXISTANTS du même site
   (utilise la REST API ?search= pour les trouver) ; pour les items notés
   "chapeaute"/"REFONTE", lier la page existante ET revenir dessus ; 1 lien
   cross-domaine max vers le pilier lexvox-victime.com si la note l'autorise.

════════ ANTI-CANNIBALISATION (TRIPLE, avant chaque rédaction) ════════
(1) GET {site cible}/wp-json/wp/v2/posts?slug=<slug> et ?search=<keyword> ;
(2) même chose sur l'AUTRE site WP ;
(3) Sanity lexvox-victime : GROQ *[slug.current=="<slug>"] + queue-aivf.json.
Si un contenu existant couvre déjà l'intent : applique la note d'angle de la
file ; s'il n'y a pas de note, différencie l'angle ou passe l'item en
"blocked" avec explication dans le tracker — ne produis pas un doublon.

════════ PUBLICATION (par article, via tools/wp_publish.py) ════════
Spec wp_publish.py : entrée = fichier atelier wp-atelier/<site>/<slug>.html
(front-matter JSON en commentaire : title, metaTitle, metaDescription, slug,
categories[], ville, image) ; actions = (1) injection EXIF GPS dans l'image,
(2) POST /media (auth Basic, secrets env selon le site), (3) POST /posts
{title, slug, status:"publish", content, excerpt, categories, featured_media,
meta Yoast si dispo}, (4) --dry-run = tout sauf les POST. Catégories : ids
existants listés dans queue-wp.json _meta.sites — ne pas créer de catégorie.

VALIDATION BLOQUANTE avant chaque publication :
  score NeuronWriter ≥ 85 via `python3 tools/nw_eval_wp.py score <query_id>
    wp-atelier/<site>/<slug>.html` (page reconstituée, journalisé)
  python3 tools/qa_article_wp.py wp-atelier/<site>/<slug>.html [--pilier]
Jamais de publication d'un article qui échoue. Pas de sas de relecture :
Me Humbert vérifie a posteriori (garde-fous = QA + Openlegi + NeuronWriter).

APRÈS publication : vérifier HTTP 200 sur l'URL publiée ; mettre l'item en
"done" + date + neuronwriter_score + url dans queue-wp.json ; mettre à jour
PUBLICATION-TRACKER-WP.md (créé au premier run : tableau date/site/slug/score/
URL + section "Métas Yoast à poser" + hypothèses de volume par silo).

ARCHIVE GIT (ce dépôt = atelier, il ne déploie RIEN ; deploy.yml reste
neutralisé, NE JAMAIS le réactiver) : committer wp-atelier/<site>/<slug>.html
+ queue-wp.json + PUBLICATION-TRACKER-WP.md après chaque lot. AVANT chaque
push : git diff --check puis git pull --rebase origin main (conflits
queue/tracker : union, jamais de suppression ; jamais de marqueur de conflit
committé). Un commit = un lot du jour.

════════ AUTOMATISATION (boucle quotidienne, dès aujourd'hui) ════════
1. AUJOURD'HUI, séance tenante : produis, valide et publie les 3 premiers
   items "todo" de la file, de bout en bout.
2. Puis crée UNE routine quotidienne (create_trigger, cron "0 6 * * *" UTC,
   nouvelle session sur cet environnement, create_new_session_on_fire=true)
   dont le prompt est : « Ouvre /home/user/lexvox-victime, lis
   PROMPT-PIPELINE-WP.md et exécute UNE itération quotidienne du PIPELINE
   LEXVOX-WP : vérifications de l'ÉTAPE 0, puis prends les 3 premiers items
   status "todo" de queue-wp.json, produis-les, valide-les, publie-les sur
   leur site WordPress respectif, mets à jour queue-wp.json +
   PUBLICATION-TRACKER-WP.md, committe et pousse (pull --rebase avant push).
   S'il reste moins de 3 items todo, traite ce qui reste ; s'il n'en reste
   AUCUN, envoie un rapport final et SUPPRIME cette routine (delete_trigger).
   En cas de blocage (NeuronWriter/Openlegi/auth WP indisponible), ne publie
   rien, marque les items "blocked" avec la raison et signale-le. »
3. Pendant une session : si tu attends un événement externe, utilise les
   mécanismes de replanification (ScheduleWakeup/loop), jamais de sleep.
4. ~1×/semaine (à intégrer dans l'itération du lundi) : si le connecteur
   Qwairy est disponible, exporter les nouvelles opportunités, trier selon la
   méthode du PLAN (écarter ce qui est déjà couvert, garder les clusters à
   fort gap) et enrichir queue-wp.json SANS dépasser 200 articles au total.

════════ GARDE-FOUS ABSOLUS ════════
- Ne JAMAIS toucher au site lexvox-victime.com, à Sanity, à deploy.yml, ni
  aux pipelines existants (queue-aivf.json reste géré par ses propres sessions).
- Aucun secret committé ou affiché. Aucun score NeuronWriter inventé. Aucune
  jurisprudence non vérifiée Openlegi. Aucune publication sous 85 ou sous
  1900 mots. Aucune création de catégorie/page WP hors périmètre posts.
- En cas de doute structurel (ex. : Yoast refuse les métas ET Me Humbert n'a
  pas répondu), continue la production en mode dégradé documenté plutôt que
  de t'arrêter, sauf si un garde-fou bloquant est en cause.

COMMENCE MAINTENANT : ÉTAPE 0, puis les items 1–3 de queue-wp.json de bout en
bout, puis mets en place la routine quotidienne.
```
