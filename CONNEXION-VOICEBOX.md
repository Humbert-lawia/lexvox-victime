# Piloter Voicebox depuis une session distante

Voicebox tourne sur le poste du cabinet et n'écoute que `localhost`. Une
session Claude qui s'exécute dans le nuage ne peut donc pas l'atteindre : il
n'existe aucune route entre les deux. Pour qu'elle le puisse, il faut publier
l'instance derrière une adresse joignable — et, c'est tout l'objet de ce
document, **derrière une authentification**.

## Le risque, en une phrase

Voicebox n'a **aucune authentification native**. Une instance publiée sans
portail, c'est la voix clonée d'un avocat mise à disposition de quiconque
connaît l'URL, sans trace ni limite : n'importe qui peut lui faire dire
n'importe quoi, y compris se faire passer pour Me Humbert auprès d'un client.
Un tunnel « rapide » (`cloudflared tunnel --url …`, ngrok gratuit) donne
exactement cela. **Ne pas s'en servir**, même quelques minutes, même « pour
essayer ».

L'outillage refuse d'ailleurs de coopérer : `voix_moteur.py` rejette toute
adresse distante en `http` — le texte lu et la voix circuleraient en clair.

## Le montage recommandé — Cloudflare Tunnel + Access

Le cabinet est déjà chez Cloudflare pour le site : c'est le chemin le plus
court, et il est gratuit à cette échelle.

### 1. Sur le poste, publier l'instance

```bash
cloudflared tunnel login
cloudflared tunnel create voicebox-lexvox
cloudflared tunnel route dns voicebox-lexvox voicebox.lexvox-victime.com
cloudflared tunnel run --url http://localhost:8000 voicebox-lexvox
```

À ce stade l'instance est **publique**. Ne pas s'arrêter ici.

### 2. Fermer la porte — une application Access

Dans le tableau de bord Cloudflare, *Zero Trust → Access → Applications*,
créer une application self-hosted sur `voicebox.lexvox-victime.com`, puis
une politique **Service Auth** qui n'accepte qu'un **jeton de service**.
Cloudflare rend alors un identifiant et un secret.

Tout ce qui n'a pas ces deux en-têtes est refusé **avant** d'atteindre le
poste : le GPU ne tourne pas, et la voix clonée reste inatteignable.

### 3. Sur la machine qui pilote, les deux secrets dans l'environnement

```bash
export VOICEBOX_CF_ID="…​.access"
export VOICEBOX_CF_SECRET="…"
```

Jamais dans un fichier, jamais dans un dépôt. `podcasts/voicebox.json` est
ignoré par git, mais un fichier ignoré se copie, se joint à un courriel et se
retrouve dans une sauvegarde — la règle du dépôt reste la règle.

### 4. La configuration

```json
{
  "base_url": "https://voicebox.lexvox-victime.com",
  "auth_headers": {
    "CF-Access-Client-Id": "env:VOICEBOX_CF_ID",
    "CF-Access-Client-Secret": "env:VOICEBOX_CF_SECRET"
  },
  "engine": "chatterbox",
  "language": "fr",
  "profils": { "victimes": "…identifiant rendu par --diagnostic…" }
}
```

`auth_headers` ne porte que des **renvois** `env:NOM`. Y écrire le secret lui-même
est refusé par l'outil, avec un message qui explique pourquoi.

### 5. Vérifier avant de produire

```bash
python3 tools/voix_moteur.py --diagnostic
```

Le diagnostic lit le `/openapi.json` de **votre** instance et tranche la
question du français, que la documentation publique de Voicebox laisse
ambiguë. S'il refuse, rien n'est produit : c'est voulu.

## Quand tout est en place — une seule commande par épisode

```bash
python3 tools/podcast_episode.py \
    --chaine victimes --slug 10-conseils-pour-reussir-son-expertise \
    --question "Vous êtes convoqué à une expertise médicale. Que faut-il préparer, et quelle erreur peut vous coûter votre indemnisation ?" \
    --debut-musique 11.7
```

Elle enchaîne l'outro (première prise seulement), les trois segments d'intro
(seule la question est réellement synthétisée), puis le montage complet avec
ses quatorze contrôles. Elle s'arrête **avant** toute synthèse si le débat
NotebookLM n'est pas déposé : inutile de faire tourner le GPU pour un montage
voué à l'échec.

## Deux choses qu'elle n'automatise pas, et pourquoi

**La question du jour.** Elle demande de lire l'article et de juger : quelle
question l'auditeur se pose réellement, et l'article y répond-il ? Une
accroche dont l'article ne donne pas la réponse casse la promesse dès le
premier épisode. Elle se produit avec `PROMPT-INTRO-VOIX.md`.

**Le débat NotebookLM.** Il se pilote à l'écran, sur le poste
(`PROMPT-PODCAST-NOTEBOOKLM.md`). Le rendu se dépose dans
`<racine>/<chaîne>/brut/<slug>.mp3`.

## L'alternative, si publier l'instance ne convient pas

Rien n'oblige à exposer Voicebox. La chaîne entière est faite pour tourner
**sur le poste** : c'est même l'argument qui a fait préférer Voicebox à
ElevenLabs — aucun texte ne sort de la machine. Dans ce cas, lancer
`podcast_episode.py` localement ; une session distante prépare la question et
relit, mais ne synthétise pas. Cette voie ne demande ni tunnel, ni jeton, ni
surface exposée.
