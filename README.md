# Scène de référence CSE WARP V17

Ce dépôt contient uniquement les données de la scène civique de référence de V17 : géométrie, instances, matériaux, textures et caméras. Il ne contient aucun exécutable ni code du moteur. Les données sont conservées dans `payload/` en blocs d’archive afin que chaque fichier source reste lisible par les outils GitHub.

La révision initiale est **V17.605**. Elle reprend la scène avec les corrections récentes du jardin et des arbres, les pots déplacés derrière la façade vitrée, les fragments d'étage supprimés et les éléments de mosaïque.

## Publication

Chaque commit poussé sur `main` reconstitue et valide l’archive source, puis publie `V17-scene.zip` dans une nouvelle release GitHub. Le paquet contient `benchmark-civic/` et `SCENE_VERSION.json`. Le dernier paquet est téléchargeable ici :

`https://github.com/glaby91/moteur3d-scene/releases/latest/download/V17-scene.zip`

La compilation LumaTrace V17 récupère cet asset, vérifie son manifeste et sa révision, puis l'intègre dans la distribution du moteur. La compilation échoue avant de compiler si le paquet est absent ou incohérent.

## Faire évoluer la scène

Pour préparer une nouvelle révision, modifier les ressources de la scène, reconstruire `payload/` avec `V17-scene.zip` et mettre à jour `source-archive.json` ainsi que `scene-release.json`. Augmenter `revision` (`V17.606`, `V17.607`, etc.). Le workflow publiera ensuite le paquet de scène sans compiler le moteur.
