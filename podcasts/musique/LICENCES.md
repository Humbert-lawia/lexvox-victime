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
| _(aucune piste enregistrée)_ | | | | | |

### Exemple d'entrée correctement remplie

| Fichier | Titre / auteur | Source (URL) | Licence | Téléchargé le | Commercial |
|---|---|---|---|---|---|
| `musique-lexvox` | *Corporate Uplift* — A. Exemple | https://pixabay.com/music/… | Pixabay Content License (PDF archivé : `licences/pixabay-corporate-uplift.pdf`) | 2026-08-13 | oui, sans attribution |

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
