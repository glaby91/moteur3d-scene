# Scène de référence CSE WARP V17

Ce dépôt contient les données de la scène civique de référence de V17 : géométrie, instances, matériaux, textures et caméras. Il ne contient aucun exécutable ni code du moteur.

## Révision publiée

La dernière scène publiée est **V17.613** : [release V17.613](https://github.com/glaby91/moteur3d-scene/releases/tag/scene-V17.613-19). Elle est générée depuis l’archive de base **V17.605** et les correctifs de scène versionnés dans `tools/`.

Le fichier racine `SCENE_VERSION.json` identifie l’archive source épinglée V17.605. Le manifeste de publication `scene-release.json` identifie la révision produite ; le workflow génère alors le manifeste de sortie V17.613 et le place dans l’archive publiée. Pour le moteur et les utilisateurs, le manifeste inclus dans l’asset de release est la référence de la scène livrée.

## Télécharger et intégrer

La release contient `V17-scene.zip` et son manifeste `SCENE_VERSION.json`. Les liens permanents vers les derniers fichiers sont :

- [Archive de la scène publiée](https://github.com/glaby91/moteur3d-scene/releases/latest/download/V17-scene.zip)
- [Manifeste de la scène publiée](https://github.com/glaby91/moteur3d-scene/releases/latest/download/SCENE_VERSION.json)

Le dépôt moteur [CSE WARP](https://github.com/glaby91/moteur3d) récupère la dernière release au moment de la compilation, valide son manifeste et son chargement, puis l’intègre au package Windows autonome. Le build officiel [V17.003 #587](https://github.com/glaby91/moteur3d/actions/runs/45080722276) a livré la scène V17.613.

## Faire évoluer la scène

Les fichiers de correction versionnés dans `tools/` produisent la scène publiée depuis l’archive de base. Chaque commit concerné poussé sur `main` lance le workflow de publication, qui valide l’archive et met à disposition une nouvelle release sans compiler le moteur.