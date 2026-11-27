# Scène de référence CSE WARP V17

Ce dépôt contient les données de la scène civique de référence de V17 : géométrie, instances, matériaux, textures et caméras. Il ne contient aucun exécutable ni code du moteur.

> **Branche active de la scène :** `main`. La branche `codex/v17-623-glass-mosaic` pointe sur le même commit au moment de l’audit. Les branches de package restent archivées et ne sont pas le point de départ de la scène civique ; voir [BRANCH_STATUS.md](BRANCH_STATUS.md).

## Révision publiée

La scène principale est **V17.631** (géométrie V17.629 conservée), avec politique optique intégrée, BVH précalculé et index Z Reflect schema 2. Les cinq plans optiques comprennent l’eau et quatre plans vitrés ; les vitres de l’ascenseur sont exclues des caméras planaires. Les 29 vues de référence ont été contrôlées. La release existante `scene-reflect-V17.631` est promue sans changer son archive ni ses empreintes SHA256.

Le fichier racine `SCENE_VERSION.json` identifie l’archive source épinglée V17.605. Le manifeste `scene-release.json` identifie la base V17.629 ; `reflect-release.json` définit la révision principale avec caches optiques ; le workflow génère le manifeste de sortie de la révision publiée et le place dans l’archive. Pour le moteur et les utilisateurs, le manifeste inclus dans l’asset de release est la référence de la scène livrée.

## Télécharger et intégrer

La release contient `V17-scene.zip` et son manifeste `SCENE_VERSION.json`. Les liens permanents vers les derniers fichiers sont :

- [Archive de la scène publiée](https://github.com/glaby91/moteur3d-scene/releases/latest/download/V17-scene.zip)
- [Manifeste de la scène publiée](https://github.com/glaby91/moteur3d-scene/releases/latest/download/SCENE_VERSION.json)

Le dépôt moteur [CSE WARP](https://github.com/glaby91/moteur3d) valide la scène de référence séparément. Le moteur télécharge la scène publiée au démarrage si nécessaire ; son package Windows ne contient pas l’archive de scène. Le build officiel [V17.003 #587](https://github.com/glaby91/moteur3d/actions/runs/45080722276) a livré la scène V17.613.

## Scène historique de Pripiat — place centrale

Un package autonome de données est également disponible pour la **scène centrale de Pripiat** : la place, le Palais de la Culture Energetik et l’hôtel Polissya. L’archive contient le binaire de scène natif, les sources éditables et la documentation ; elle ne contient pas le moteur ni son exécutable.

[Télécharger le package de la scène centrale de Pripiat — Energetik, place et Polissya](https://github.com/glaby91/moteur3d-scene/releases/download/pripyat-scene-central-20261124.1/Pripyat-place-centrale-Energetik-Polissya.zip) · [Notes de la version](https://github.com/glaby91/moteur3d-scene/releases/tag/pripyat-scene-central-20261124.1)

## Faire évoluer la scène

Les fichiers de correction versionnés dans `tools/` produisent la scène publiée depuis l’archive de base. Le workflow principal `publish-reflect-scene.yml` publie les révisions optiques depuis `main`. Pour une modification de scène, incrémenter la révision, adapter la politique et épingler le compilateur. Le workflow historique est manuel et ne désigne plus une ancienne scène comme latest.

### V17.632 — nettoyage ciblé (27 novembre 2026)
Suppression des deux cloisons de mosaïque de verre, des cinq douches et de la dalle résiduelle de l'ancienne trémie du hall. Voir [rapport et périmètre](docs/V17.632-nettoyage.md). La publication reste conditionnée au workflow natif ; V17.631 conservée comme version de retour.
