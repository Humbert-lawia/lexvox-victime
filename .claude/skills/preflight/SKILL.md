---
name: preflight
description: Valider le site avant push — marqueurs de conflit, sitemap.xml, JSON-LD, images manquantes, meta SEO, secrets. Utiliser avant tout commit/push et quand l'utilisateur demande de vérifier ou auditer le site.
---

# Préflight du site

```bash
python3 tools/preflight.py
```

## Interpréter la sortie

- **ERREUR** (code retour 1) : bloquant, corriger avant tout push. Classes
  d'erreurs qui ont déjà cassé la production : marqueurs de conflit git,
  sitemap.xml invalide ou avec doublons, JSON-LD corrompu, image locale
  introuvable, secret en clair.
- **AVERTISSEMENT** : non bloquant (title/meta description trop longs, H1
  multiples, canonical manquant). Corriger ceux introduits par le diff
  courant ; ne pas entamer de correction en masse de l'existant sans demande
  explicite.

## Corrections types

- Conflit sitemap : garder l'union des URLs des deux côtés, dédupliquer,
  supprimer les lignes `<<<<<<<`/`=======`/`>>>>>>>`, puis revalider.
- JSON-LD invalide : c'est presque toujours du HTML injecté dans le JSON
  (guillemets non échappés, balises `<a>` dans une réponse FAQPage). Réécrire
  la valeur en texte brut.
- Image introuvable : copier un visuel thématique existant de
  `img/articles/` sous le nom attendu, le signaler dans le commit.

Après correction : relancer le script jusqu'à `0 erreur(s) bloquante(s)`.
