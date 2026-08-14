# Installer Claude sur votre Mac — pas à pas

Ce guide ne suppose aucune connaissance technique. Il y a **quatre étapes**, et
seule la quatrième vous demande de coller un texte. Une fois terminé, la
session Claude qui tourne sur votre Mac fait le reste elle-même : elle voit
Voicebox, elle voit vos fichiers, et elle peut ouvrir des applications et se
servir de votre écran.

C'est là toute la différence : la session qui vous parle en ce moment tourne
dans le nuage, sur une machine qui n'a aucun lien avec la vôtre. Celle que vous
allez installer tourne **chez vous**.

---

## Étape 1 — Télécharger l'application

Ouvrir **https://claude.ai/download** dans Safari ou Chrome, et télécharger
l'application pour Mac.

Ouvrir le fichier téléchargé, glisser **Claude** dans le dossier
**Applications**, comme pour n'importe quelle application.

> L'application contient déjà tout ce qu'il faut. Rien d'autre à installer :
> ni Node.js, ni ligne de commande.

## Étape 2 — Se connecter

Lancer **Claude** depuis le dossier Applications, et se connecter avec le
compte du cabinet — le même qu'ici.

En haut de la fenêtre, trois onglets : **Chat**, **Cowork**, **Code**.
Cliquer sur **Code**.

## Étape 3 — Deux réglages, une fois pour toutes

Au-dessus de la zone où l'on écrit, régler :

- **Environnement : Local.** C'est le réglage déterminant — il dit à Claude de
  travailler sur votre Mac et non dans le nuage. Sans lui, il ne verra pas
  Voicebox.
- **Dossier du projet :** choisir un dossier, par exemple **Documents**. Si le
  dépôt `lexvox-victime` n'y est pas encore, ce n'est pas grave : Claude ira le
  chercher lui-même à l'étape suivante.

## Étape 4 — Coller ce message

Copier le texte ci-dessous **en entier**, le coller dans la zone de saisie,
et envoyer. C'est la seule chose à faire.

```
Tu travailles sur le poste du cabinet LEXVOX AVOCATS (Mac), en local.

Contexte : je ne suis pas informaticien. Explique-moi ce que tu fais en
français simple, et fais les choses toi-même plutôt que de me donner des
commandes à taper. Demande-moi seulement ce que toi seul ne peux pas savoir.

Voici ce que je veux obtenir : le premier épisode du podcast LEXVICTIME.

Marche à suivre :

1. Si le dossier du dépôt lexvox-victime n'est pas déjà là, récupère-le depuis
   GitHub (Humbert-lawia/lexvox-victime), puis place-toi dedans.

2. Lis ETAT-CHANTIER-PODCASTS.md en entier. Ce fichier porte mes décisions,
   ce qui est déjà prouvé par les tests et ce qui ne l'est pas. Ne remets pas
   en cause ce qui y est arrêté.

3. Lance : python3 tools/poste_verifier.py
   Il liste ce qui manque sur cette machine. Répare chaque point toi-même :
   ffmpeg, la configuration Voicebox, les dossiers de travail.

4. Voicebox étant lancé, exécute : python3 tools/voix_moteur.py --diagnostic
   Il lit le schéma de mon instance et tranche la question du français.
   Reporte-moi le résultat, et renseigne dans podcasts/voicebox.json
   l'identifiant de ma voix clonée pour la chaîne victimes.

5. Le générique musical : la piste Pixabay « Intro YouTube » de Kulakovka est
   dans mes téléchargements. Copie-la en
   ~/LEXVOX-PODCASTS/musique/musique-lexvox.mp3
   Sa licence est déjà consignée dans podcasts/musique/LICENCES.md.

6. Le débat NotebookLM de l'épisode pilote doit être déposé en
   ~/LEXVOX-PODCASTS/victimes/brut/10-conseils-pour-reussir-son-expertise.mp3
   Si je ne l'ai pas encore produit, dis-le-moi et arrête-toi là.

7. Quand tout est en place, fabrique l'épisode :

   python3 tools/podcast_episode.py --chaine victimes \
       --slug 10-conseils-pour-reussir-son-expertise \
       --question "Vous êtes convoqué à une expertise médicale. Que faut-il préparer, et quelle erreur peut vous coûter votre indemnisation ?" \
       --debut-musique 11.7

8. Fais-moi écouter le résultat et dis-moi ce que valent les quatorze
   contrôles qualité.

Deux points sur lesquels je ne transige pas : la voix doit prononcer
« Imbert » (le h est muet), et Nathalie et Nicolas ne sont jamais présentés
comme des voix de synthèse ou des intelligences artificielles — seulement
comme « les deux voix de l'émission », qui ne sont pas avocats.
```

---

## Ce qui va se passer ensuite

Claude va travailler sur votre Mac, vous montrer ce qu'il fait, et vous poser
des questions quand il en aura besoin. Vous pouvez lui parler normalement :
« je ne comprends pas », « refais-moi ça », « c'est trop fort », « la musique
est trop longue » — il ajustera.

Si quelque chose bloque, dites-le-lui simplement. Il a de quoi diagnostiquer :
`poste_verifier.py` pour la machine, `voix_moteur.py --diagnostic` pour
Voicebox, et les quatorze contrôles du montage pour le fichier produit.

## Si vous préférez malgré tout le tunnel

Publier Voicebox pour qu'une session distante l'atteigne reste possible, et
`tools/voicebox_tunnel.py` le fait en une commande. Mais cela demande un compte
Cloudflare Zero Trust, un jeton d'API et un terminal laissé ouvert — bien plus
que ces quatre étapes. Voir `CONNEXION-VOICEBOX.md`.
