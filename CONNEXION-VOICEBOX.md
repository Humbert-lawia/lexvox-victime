# Piloter Voicebox depuis une session distante

Voicebox tourne sur le poste du cabinet et n'écoute que `localhost`. Une
session Claude qui s'exécute dans le nuage ne peut donc pas l'atteindre : il
n'existe aucune route entre les deux. Pour qu'elle le puisse, il faut publier
l'instance derrière une adresse joignable — et, c'est tout l'objet de ce
document, **derrière une authentification**.

---

## ⚠️ À lire avant tout : il y a plus simple, et c'est plus sûr

Le tunnel n'existe que pour une raison : permettre à une session Claude
**distante** d'atteindre le poste. Si Claude tourne **sur le poste lui-même**
— l'application Claude Code pour Mac ou Windows — il parle à Voicebox par
`localhost`, et **tout ce document devient inutile** : pas de tunnel, pas de
compte Cloudflare, pas de jeton, pas de terminal à laisser ouvert, et surtout
aucune surface exposée.

| | Claude sur le poste | Tunnel Cloudflare |
|---|---|---|
| À installer | l'application Claude Code | cloudflared, un jeton d'API, une application Access |
| Voix clonée exposée | **jamais** | derrière un portail, s'il est bien posé |
| À maintenir | rien | un tunnel qui doit rester lancé |
| Ce que ça demande de vous | ouvrir l'application | un tableau de bord Cloudflare |

**Pour quelqu'un qui n'est pas informaticien, c'est la voie à prendre.** C'est
aussi celle qui respecte le mieux l'argument qui a fait choisir Voicebox
plutôt qu'ElevenLabs : aucun texte, aucune voix ne quitte la machine.

Le reste de ce document décrit le tunnel, pour le cas où l'instance doive
vraiment être pilotée de l'extérieur.

---

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

## Le montage — Cloudflare Tunnel + Access, en une commande

Le cabinet est déjà chez Cloudflare pour le site : c'est le chemin le plus
court, et il est gratuit à cette échelle.

### L'ordre compte, et ce n'est pas l'ordre des tutoriels

La plupart des guides font créer le tunnel, puis poser le portail. **Entre les
deux, l'instance répond à tout le monde** — le temps d'aller cliquer dans un
tableau de bord. Pour une voix clonée d'avocat, cette fenêtre est inacceptable.

`tools/voicebox_tunnel.py` inverse l'ordre : le portail existe **avant** que le
nom d'hôte ne résolve.

```
1. jeton de service       l'identité qui aura le droit d'entrer
2. application Access     le portail            ← avant que le nom existe
3. politique              n'accepte que ce jeton
4. tunnel + route DNS     le nom se met à résoudre, déjà protégé
5. vérification           sans jeton → refusé ; avec jeton → 200
```

### Ce qu'il faut avoir sous la main

- `cloudflared` installé sur le poste (macOS : `brew install cloudflared` ;
  Windows : `winget install --id Cloudflare.cloudflared`), puis
  `cloudflared tunnel login` une fois, qui ouvre le navigateur ;
- un **jeton d'API Cloudflare** avec trois droits : *Access: Apps and
  Policies:Edit*, *Access: Service Tokens:Edit*, *DNS:Edit* ;
- l'**identifiant de compte** Cloudflare (visible dans le tableau de bord).

### La commande

```bash
export CLOUDFLARE_API_TOKEN="…"
export CLOUDFLARE_ACCOUNT_ID="…"

python3 tools/voicebox_tunnel.py --installer \
    --hote voicebox.lexvox-victime.com
```

Elle est **rejouable** : un tunnel, une application ou un jeton déjà créés
sont réutilisés, pas dupliqués. À la fin, elle affiche le couple identifiant /
secret du jeton de service — **Cloudflare ne réaffichera jamais ce secret**.

Puis, sur le poste, à laisser tourner :

```bash
cloudflared tunnel run voicebox-lexvox
```

Et enfin, le seul contrôle qui compte :

```bash
python3 tools/voicebox_tunnel.py --verifier --hote voicebox.lexvox-victime.com
```

Il vérifie que **sans jeton, l'instance refuse**. S'il annonce l'inverse, il
dit de couper le tunnel immédiatement.

### Les deux secrets, dans l'environnement

```bash
export VOICEBOX_CF_ID="…​.access"
export VOICEBOX_CF_SECRET="…"
```

Jamais dans un fichier, jamais dans un dépôt. `podcasts/voicebox.json` est
ignoré par git, mais un fichier ignoré se copie, se joint à un courriel et se
retrouve dans une sauvegarde — la règle du dépôt reste la règle.

### La configuration

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

## L'alternative, redite en clair

Rien n'oblige à exposer Voicebox. La chaîne entière est faite pour tourner
**sur le poste** — c'est l'argument qui a fait préférer Voicebox à ElevenLabs.
Installer Claude Code sur le Mac ou le PC du cabinet, ouvrir le dépôt, et
lancer :

```bash
python3 tools/podcast_episode.py --chaine victimes --slug <slug> \
    --question "…?" --debut-musique 11.7
```

Ni tunnel, ni jeton, ni compte à configurer, ni surface exposée. Une session
distante peut toujours préparer la question, relire, corriger le code — elle
ne synthétise simplement pas elle-même.
