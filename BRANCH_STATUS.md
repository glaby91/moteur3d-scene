# État des branches — scène CSE WARP

Audit effectué le 24 novembre 2026. Les branches sont conservées ; ce repère précise seulement laquelle suivre.

## Repère immédiat

**Branche de travail et de publication :** [`main`](https://github.com/glaby91/moteur3d-scene/tree/main)  
**Révision actuelle indiquée dans le README :** V17.623.  
**PR ouverte :** aucune au moment de l’audit.

La branche `codex/v17-623-glass-mosaic` pointe actuellement sur le même commit que `main`. Elle est conservée, mais `main) est la branche à utiliser pour les prochaines modifications de scène et publications.

## Branches observées

| Branche | Rôle |
|---|---|
| `main` | Branche par défaut, source de travail et de publication de la scène |
| `codex/v17-623-glass-mosaic` | Même tête que `main` lors de l’audit ; branche conservée |
| `package/pripyat-central-scene-20261124` | Package historique/alternative de la scène centrale de Pripiat |
| `package/pripyat-v16-compat-20261124` | Package de compatibilité V16/V17 de cette scène |

Ne pas reprendre les branches `package/*` pour modifier la scène civique de référence du moteur.

## Règle de travail

Modifier les données et scripts de scène sur `main), puis vérifier la génération et la publication. Le moteur récupère la release de scène selon son workflow ; les dépôts moteur et scène restent séparés.

Aucune branche n’a été supprimée, fermée, renommée ou déplacée pendant cet audit.
