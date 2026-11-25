# Scène de référence CSE WARP V17

Ce dépôt contient les données de la scène civique de référence de V17 : géométrie, instances, matériaux, textures et caméras. Il ne contient aucun exécutable ni code du moteur.

> **Branche active de la scène :** `main`. La branche `codex/v17-623-glass-mosaic` pointe sur le même commit au moment de l’audit. Les branches de package restent archivées et ne sont pas le point de départ de la scène civique ; voir [BRANCH_STATUS.md](BRANCH_STATUS.md).

## Révision publiée

La scène préparée est **V17.628**, à partir de V17.627. Elle corrige aussi la référence du jeu PBR sur le vitrage cabine, renommé en même temps que son matériau. Le packaging vérifie maintenant chaque association matériau → jeu de textures sur l’ensemble de la scène et bloque la publication en cas de référence manquante. Elle conserve les corrections V17.627 du camion : enseigne réduite et plaquée sur les vrais triangles, filet rouge interrompu aux ouvertures, vitrages et lentilles identifiés séparément, normales pondérées pour lisser la carrosserie sans gommer les arêtes. Les dimensions et le placement du camion restent inchangés ; la scène de piscine n’est pas modifiée. La scène part de l’archive **V17.605** et applique les correctifs versionnés dans `tools/`. Les révisions antérieures conservent notamment la mosaïque vitrée aqua/turquoise et les luminaires repositionnés.

Le fichier racine `SCENE_VERSION.json` identifie l’archive source épinglée V17.605. Le manifeste de publication `scene-release.json` identifie la révision produite ; le workflow génère le manifeste de sortie de la révision publiée et le place dans l’archive. Pour le moteur et les utilisateurs, le manifeste inclus dans l’asset de release est la référence de la scène livrée.

## Télécharger et intégrer

La release contient `V17-scene.zip` et son manifeste `SCENE_VERSION.json`. Les liens permanents vers les derniers fichiers sont :

- [Archive de la scène publiée](https://github.com/glaby91/moteur3d-scene/releases/latest/download/V17-scene.zip)
- [Manifeste de la scène publiée](https://github.com/glaby91/moteur3d-scene/releases/latest/download/SCENE_VERSION.json)

Le dépôt moteur [CSE WARP](https://github.com/glaby91/moteur3d) récupère la dernière release au moment de la compilation, valide son manifeste et son chargement, puis l’intègre au package Windows autonome. Le build officiel [V17.003 #587](https://github.com/glaby91/moteur3d/actions/runs/45080722276) a livré la scène V17.613.

## Scène historique de Pripiat — place centrale

Un package autonome de données est également disponible pour la **scène centrale de Pripiat** : la place, le Palais de la Culture Energetik et l’hôtel Polissya. L’archive contient le binaire de scène natif, les sources éditables et la documentation ; elle ne contient pas le moteur ni son exécutable.

[Télécharger le package de la scène centrale de Pripiat — Energetik, place et Polissya](https://github.com/glaby91/moteur3d-scene/releases/download/pripyat-scene-central-20261124.1/Pripyat-place-centrale-Energetik-Polissya.zip) · [Notes de la version](https://github.com/glaby91/moteur3d-scene/releases/tag/pripyat-scene-central-20261124.1)

## Faire évoluer la scène

Les fichiers de correction versionnés dans `tools/` produisent la scène publiée depuis l’archive de base. Chaque commit concerné poussé sur `main` lance le workflow de publication, qui valide l’archive et met à disposition une nouvelle release sans compiler le moteur.
