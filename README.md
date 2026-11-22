# Scène de référence CSE WARP V17

Ce dépôt contient uniquement les données de la scène civique de référence de V17 : géométrie, instances, matériaux, textures et caméras. Il ne contient aucun exécutable ni code du moteur. Les données sont conservées dans `payload/` en blocs d’archive afin que chaque fichier source reste lisible par les outils GitHub.

La source de base est **V17.605**. La révision **V17.609** conserve les corrections du parvis de V17.608, rend l’écriture de l’enseigne du complexe aquatique lumineuse la nuit, ajoute quatre sources discrètes dans la butte pour éclairer le monument et élargit les halos des spots au sol afin d’atténuer les quatre zones lumineuses distinctes autour du banc. L’allumage des sources extérieures suit le contrôle nocturne commun de la scène.

## Publication

Chaque commit poussé sur `main` reconstitue et valide l’archive source, puis publie `V17-scene.zip` dans une nouvelle release GitHub. Le paquet contient `benchmark-civic/` et `SCENE_VERSION.json`. Le dernier paquet est téléchargeable ici :

`https://github.com/glaby91/moteur3d-scene/releases/latest/download/V17-scene.zip`

La compilation LumaTrace V17 récupère cet asset, vérifie son manifeste et sa révision, puis l'intègre dans la distribution du moteur. La compilation échoue avant de compiler si le paquet est absent ou incohérent.

## Faire évoluer la scène

Le paquet est produit depuis l'archive de base et les correctifs versionnés dans `tools/`. Le workflow vérifie la révision obtenue puis publie automatiquement `V17-scene.zip` et `SCENE_VERSION.json`, sans compiler le moteur. La révision source de base peut donc rester épinglée pendant que les correctifs de scène avancent.
