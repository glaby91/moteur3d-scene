# Experimental Reflect scene branch

Stable main and its latest release are not changed. V17.631 derives from V17.629 geometry, changing only the scene revision and embedded author policy (lift planar reflection disabled, shared probe metadata preserved, facade and pool AUTO). The build uses the exact pinned native engine commit, generates and roundtrips CSP001 and the optical index, compares all 29 views with the exhaustive reference, checks sidecar hashes and publishes a separate prerelease. The probe is only a declaration, not rendered yet. Use a new revision/tag for future incompatible changes; update the engine Reflect channel selector and the pinned compiler commit accordingly. Do not commit generated binaries into Git history; the release ZIP contains them.

Schema 2 includes the pool water plane in the same runtime index as glazing, five planes total. Schema 1 is rejected by the new loader.
