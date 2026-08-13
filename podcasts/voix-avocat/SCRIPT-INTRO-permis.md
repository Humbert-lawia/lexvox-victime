# Script d'introduction — chaîne PERMIS

> 🛑 **NE PAS ENREGISTRER EN L'ÉTAT — signataire à confirmer.**
>
> Me Humbert a indiqué le 2026-08-13 qu'il s'occupe **exclusivement des
> victimes** et que le droit routier est traité par un associé. Or
> `lexvox-permis.com` dit l'inverse : il y est présenté avec « plus de 20 ans
> d'expérience **exclusive en droit pénal routier** », et la page ajoute
> « Me Humbert examine systématiquement la régularité de la procédure ». La
> seule autre avocate nommée sur ce site est **Me Cédrine Raybaud**
> (spécialiste en droit de la famille, Master en droit pénal,
> co-fondatrice) — mais rien ne lui attribue le contentieux routier.
>
> Le gabarit ci-dessous fait donc dire à Me Humbert une phrase qui est
> peut-être fausse, et qui le serait 24 fois. Deux réponses à donner avant
> d'aller plus loin : **qui présente la chaîne permis**, et **quel site
> corriger** — celui qui revendique l'exclusivité victimes, ou celui qui
> revendique l'exclusivité routière. Je répercute ensuite ici.

Texte lu par **Me Patrice Humbert** (sous réserve ci-dessus), avec sa voix
clonée dans **Voicebox** (synthèse locale, sur le poste du cabinet).

Émission : **Permis en danger**. ⚠️ La chaîne victimes a été rebaptisée
**LEXVICTIMES** ; dites-le si vous voulez une famille de titres cohérente.

Générer le texte d'un épisode :

```bash
python3 tools/voix_script.py --chaine permis --slug <slug> \
  --question "…?" --sujet "la contestation d'un éthylomètre" \
  --segments ~/LEXVOX-PODCASTS/permis/segments --moteur voicebox
```

Durée cible à la lecture : **30 à 40 secondes**.

## Structure imposée — c'est la marque de fabrique de la série

| Paragraphe | Bloc | Segment | Refait à chaque épisode ? |
|---|---|---|---|
| 1 | **Question d'accroche**, dont la réponse est l'article du jour | `01-question` | ✏️ oui |
| 2 | **Jingle verbal** — nom de l'émission, cabinet, identité de l'avocat | `02-jingle` | 🔒 **non — enregistré une fois** |
| 3 | Sujet du jour et article dont il est tiré | `03-sujet` | ✏️ oui |
| 4-5 | Présentation de Nathalie et Nicolas, puis la relance | `04-final` | 🔒 **non — enregistré une fois** |

Exemple de question d'accroche pour cette chaîne :

> Les gendarmes viennent de retenir votre permis sur le bord de la route. Que
> se passe-t-il dans les soixante-douze heures qui suivent ?

⚠️ Le paragraphe 4 dit que Nathalie et Nicolas **ne sont pas avocats** et
qu'ils sont **créés par le cabinet** — vérifié par l'outil. Noter aussi
qu'aucune spécialisation CNB n'est revendiquée dans cette matière :
l'introduction parle d'expérience, pas de titre.

<<<SCRIPT
{question}

Bienvenue dans « Permis en danger », le podcast du cabinet LEXVOX
AVOCATS. Je suis Maître Patrice Humbert, avocat au Barreau
d'Aix-en-Provence. Je défends les conducteurs depuis plus de vingt ans.

Aujourd'hui : {sujet}. Tout part de mon article « {titre} », que vous
retrouvez sur le site du cabinet.

Cette émission est animée par Nathalie et Nicolas. Nathalie, la juriste, vous
explique le droit ; Nicolas, le journaliste, pose les questions que vous vous
posez. Ils ne sont pas avocats : ce sont les deux voix de l'émission, créées
par le cabinet pour rendre ces sujets techniques accessibles.

La réponse, tout de suite. Bonne écoute.
SCRIPT>>>
