# Checklist de recette globale — kits LEXVOX Victime

Relecture humaine unique avant mise en ligne (Me Humbert). État au 11 juillet 2026.
La vérification juridique est machine (OpenLegi), tracée et jointe au manifest.

| # | Point de recette | État | Preuve |
|---|---|:---:|---|
| 1 | Référentiel vérifié du lot 0 présent, complet, daté | OK | `referentiel/referentiel-verifie.json` (24 références, test connectivité OK) + `note-de-cadrage.md` |
| 2 | 23 documents de contenu livrés, complets, aux longueurs cibles | OK | 13 Accident + 10 Erreur médicale (`kits/`), ~66 500 mots |
| 3 | 2 landing pages conformes au template, autonomes | OK | `landing/kit-accident.html` (42 Ko), `landing/kit-erreur-medicale.html` (40 Ko), 3 blocs JSON-LD valides chacune, 1 seul H1, meta 120-155 |
| 4 | 100 % des références tracées dans le journal OpenLegi | OK | `qc/rapport-qc-final.md` : 0 référence orpheline ; manifest : 137 citations tracées |
| 5 | Disclaimers RIN 11.1 et avertissement « pas une consultation » présents | OK | Table §3 du rapport QC : avertissement présent dans les 23 documents ; RIN 11.1 sous chaque bloc chiffré ; urgence 15 dans tous les documents médicaux |
| 6 | Aucun avis fictif, aucun chiffre invérifiable, aucune promesse de résultat | OK | Avis Google en placeholders `[AVIS_GOOGLE_x]` ; seules données chiffrées = preuves BLOC 3 ; QC §2 : 0 promesse détectée |
| 7 | Placeholders Stripe et Sanity recensés dans le manifest | OK | `manifest.json` > `placeholders_a_remplacer` |
| 8 | 3 points réservés à Me Humbert identifiés | OK | Prix définitifs, CGV définitives, structure de vente / qualification du palier premium (manifest > `points_reserves_arbitrage_final`) |
| 9 | Tunnel complet (emails, page merci, nurturing, CGV) | OK | `tunnel/` : 4 emails de livraison, page merci, séquence 6 emails (variantes accident/médical), trame CGV |
| 10 | PDF maquettés par palier + fichiers à remplir A4 | OK | `pdf/` : 6 PDF paliers + 5 fichiers à remplir (couverture, sommaire cliquable, pieds de page, pagination) |
| 11 | Aucun tiret cadratin, chiffres en chiffres | OK | QC §2 : 0 tiret cadratin dans le corps des textes |
| 12 | Aucun marqueur de conflit, aucun secret en dur | OK | `git diff --check` propre ; aucun token committé |

## Actions humaines restantes avant mise en ligne

1. Renseigner les placeholders (liens Stripe, photo Me Humbert, avis Google réels, endpoint formulaire).
2. Arbitrer les prix définitifs et valider les CGV définitives (une trame seule est produite).
3. Valider, avec l'Ordre, la qualification commerciale du palier premium (audit / pré-analyse sous convention d'honoraires).
4. Décider du routage/URL des landing pages et de leur intégration au frontend Sanity
   (ce dépôt atelier n'est plus servi en production, cf. CLAUDE.md : aucun déploiement lancé).
5. Confirmer le rendu Lighthouse mobile > 90 sur l'environnement de préproduction réel.

## Rappel architecture (CLAUDE.md)

Ces livrables sont des fichiers **atelier**. Aucun déploiement Cloudflare n'a été déclenché,
`deploy.yml` reste neutralisé, et rien n'a été poussé vers Sanity. La mise en ligne
effective (landing pages, tunnel, PDF) relève d'une décision expresse de Me Humbert.
