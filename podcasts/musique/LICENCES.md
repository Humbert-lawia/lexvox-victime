# Registre des licences — génériques musicaux

`podcast_montage.py` **refuse de monter** un épisode dont le générique n'est
pas consigné ici. Ce n'est pas une formalité : une plateforme qui reçoit une
réclamation retire l'épisode, parfois la série entière. La preuve doit
exister **avant** la diffusion, pas le jour de la réclamation.

Une entrée est valide quand le **nom de fichier sans extension** apparaît
ci-dessous (c'est ce que l'outil cherche) et que les quatre informations
suivantes sont renseignées.

## Où chercher une musique réellement utilisable

| Source | Licence | Attribution | Usage commercial | Remarque |
|---|---|---|---|---|
| **Pixabay Music** | Pixabay Content License | non exigée | oui | le plus simple ; conserver la page et la date de téléchargement |
| **Free Music Archive** | variable **piste par piste** | selon la piste | selon la piste | ne jamais généraliser : lire la licence de CHAQUE morceau |
| **Uppbeat** | offre gratuite avec crédit obligatoire | oui en gratuit | oui | l'abonnement supprime l'obligation de crédit |
| **Epidemic Sound / Artlist** | abonnement | non | oui | payant, mais la licence est nominative et archivable — le choix le plus sûr pour un cabinet |
| Bibliothèque audio YouTube | pensée pour YouTube | variable | **ambigu hors YouTube** | à éviter pour un podcast diffusé ailleurs |

Deux réflexes :

- **Télécharger la page de licence en PDF** au moment du téléchargement, et
  la ranger à côté du fichier audio. Une page web change ; un PDF daté non.
- Se méfier de « libre de droit » employé seul : l'expression n'a pas de
  valeur juridique en France. Ce qui compte est le texte de la licence.

## Pistes en service

<!-- Une ligne par piste. Le nom de fichier SANS extension doit apparaître
     tel quel : c'est la chaîne que podcast_montage.py recherche. -->

| Fichier | Titre / auteur | Source (URL) | Licence | Téléchargé le | Commercial |
|---|---|---|---|---|---|
| `musique-lexvox` | *Intro YouTube* — Kulakovka | https://pixabay.com/music/beats-intro-youtube-295915/ | Pixabay Content License — certificat nominatif archivé : `licences/pixabay-intro-youtube-295915.txt` | 2026-08-13 | oui, sans attribution |

⚠️ **Le contrôle du montage ne compare que le nom de fichier.** Si
`musique-lexvox.mp3` est un jour remplacé par une autre piste sans que cette
ligne change, la vérification passera pour une musique dont la licence n'est
pas celle-ci. Remplacer la piste = réécrire la ligne dans le même geste.

### Générique en service — *Intro YouTube* (Kulakovka)

Piste source : 115,2 s, 256 kb/s, 44,1 kHz, stéréo, −12,5 LUFS intégrés.

**Point d'entrée : 11,70 s** (`--debut-musique 11.7`). Ce réglage n'est pas un
détail de goût. Mesurée seconde par seconde, la piste s'ouvre sur des frappes
isolées séparées de quasi-silence — hits à 0 s, 3 s, 6 s, 9,5 s, puis un
silence net de 10,75 s à 11,99 s — avant que la musique pleine ne démarre à
**12,00 s**. Couper les six premières secondes, comme le fait le réglage par
défaut, placerait environ trois secondes de trou juste avant la première
syllabe de l'avocat.

Entrer à 11,70 s laisse le fondu d'entrée (0,3 s) se consommer entièrement
dans le silence qui précède : l'attaque de 12,00 s arrive à plein niveau, et
l'extrait 11,70 → 17,70 s reste dense jusqu'au fondu de sortie.

```bash
python3 tools/podcast_montage.py --chaine victimes --slug <slug> \
    --segments ~/LEXVOX-PODCASTS/victimes/segments \
    --debut-musique 11.7
```

## Où déposer le fichier

- `~/LEXVOX-PODCASTS/musique/musique-lexvox.mp3` — générique commun aux trois
  chaînes ;
- `~/LEXVOX-PODCASTS/<chaine>/musique/musique-<chaine>.mp3` — générique
  propre à une chaîne, qui prime sur le commun.

Le montage en conserve **6 secondes** par défaut (`--duree-musique`), avec
une entrée en fondu de 0,3 s et une extinction de 1,5 s qui s'achève **avant**
la première syllabe : une musique qui traîne sous la question d'accroche rend
moins intelligible la phrase qui doit justement accrocher l'auditeur. Elle
est mixée à −20 LUFS, soit 4 LU sous la voix.
