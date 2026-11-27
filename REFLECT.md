# Scène principale V17.631 — données optiques

The validated Reflect scene is promoted to main and latest without rewriting its existing release assets. V17.631 derives from V17.629 geometry, changing only the scene revision and embedded author policy (lift planar reflection disabled, shared probe metadata preserved, facade and pool AUTO). The build uses the exact pinned native engine commit, generates and roundtrips CSP001 and the optical index, compares all 29 views with the exhaustive reference, checks sidecar hashes and publishes an official scene release. The probe is only a declaration, not rendered yet. Use a new revision/tag for future incompatible changes; update the revision/tag, policy and pinned compiler commit accordingly. Do not commit generated binaries into Git history; the release ZIP contains them.

Schema 2 includes the pool water plane in the same runtime index as glazing, five planes total. Schema 1 is rejected by the new loader.

V17.632 : nettoyage géométrique ciblé, politique optique inchangée hors numéro de version ; recalcul obligatoire des caches. [Rapport](docs/V17.632-nettoyage.md).

V17.633 : vitraux décoratifs transmissifs, exclus des caméras de réflexion planaires. Caches régénérés.
