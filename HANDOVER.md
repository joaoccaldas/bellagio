# Bellagio digital twin — handover (paused 2026-09-27)

Status: **paused by the owner** to start the Kona world. Nothing is deployed or published. All work is local in
`~/Downloads/BELLAGIO_source/`. The latest honest self-assessment is ~45% of "almost being there" (scorecard below).

## What exists

| Path | What it is |
|---|---|
| `blender/survey.py` | All site data in metres (origin = tower core, +X east, +Y north): Y-plan wing centre-lines, façade heights, lake outline, fountain pipe layout, podium, village, pools, context, interiors. `fountain_nozzles()` returns the published 1,214-nozzle mix exactly. |
| `blender/geo.py` | Mesh toolkit: batched `MB` builder, `facade()` window cutter (reveals, glass with per-window UVs + random tag, mullions, arches, bifora), molding sweeps, hip roofs, balustrades. |
| `blender/tower.py` | Main tower (Y plan, stepped end blocks, core cylinder, drum with bent BELLAGIO text, lantern arcade, copper dome), Spa Tower, `floodlights()` for the night wash. |
| `blender/grounds.py` | Orthophoto ground (shadow-lifted), lake basin + coping, promenade balustrade + lamp posts, shoreline boulders, 26 villas, podium with conservatory opening, Via Bellagio domes, porte-cochère, pools, context massing, Eiffel replica, trees (178, from imagery). |
| `blender/interior.py` | Lobby (coffers, columns, desk, medallion floor), Fiori di Como (2,100 pieces; `PIECES` exported for the browser), passage with the lift doorway, Conservatory (vault, arcades, scroll mosaic floor, beds, fountain, blossom trees). |
| `blender/penthouse.py` | **Invented** level-36 residence (Lake Como salon, dining, Rat Pack bar, glass gallery, spa pool, library, Desert Moon bedroom/bath/dressing, rotunda with helical stair, roof terrace, private lift with animated cab/doors). |
| `blender/fountains.py` | Static volumetric fountain "moment" for Cycles hero renders. |
| `blender/mats.py` | Materials, day/night switch (`set_night`), room glass with night rooms, shadow-clear skylights. |
| `blender/textures.py`, `ground_tex.py`, `trees_from_sat.py` | Procedural floor/fresco/book textures; orthophoto shadow lift; satellite tree detector. |
| `blender/preview.py` | Cycles previews. Env: `VIEWS`, `SPP`, `RES`, `OUT`, `LIGHTING=day|night`, `FOUNTAIN=finale`, `PENTHOUSE=0|1`. |
| `blender/build.py` | Bake + export: joins static geometry into 5 atlases (TOWER, SITE, VILLAGE, INTERIOR, PENTHOUSE), bakes day/night lightmaps (sqrt(x/(x+1)) encoded PNG), renders env_day/night.hdr, exports `bellagio.glb` + `manifest.json`. Env: `RES_<GROUP>`, `SPP`, `GROUPS`, `PANO`, `OUT`. |
| `pack_assets.py` | `out/` → `web/dist/assets/` (WebP lightmaps, GLB, HDR, manifest). |
| `web/` | Three.js r186 viewer (`src/main.js`, `fountains.js`, `places.js`, `index.template.html`, `build.mjs`). Walk mode with BVH collisions, lift ride, day/night slider, GPU fountain shows with launch-time schedule history, interior-mapped hotel windows with shader mullions, evidence panel. |
| `EVIDENCE.md` | Evidence ledger (M measured / P published / F photographed / I inferred / X invented) with sources. |
| `renders/v3..v5` | Versioned previews + `v3/compare_reference_v3.jpg` (reference vs render). |

## How to run

```bash
cd ~/Downloads/BELLAGIO_source
VIEWS=front_lake,lobby SPP=48 blender -b --python blender/preview.py        # previews -> renders/
OUT=out SPP=384 blender -b --python blender/build.py                       # full bake (~20-40 min on M5)
python3 pack_assets.py && (cd web && node build.mjs)                       # -> web/dist (index.html + assets/)
cd web/dist && python3 -m http.server 8765                                 # open http://localhost:8765
```

## Verified vs not verified

- Verified: Blender builds (tower 4 s, penthouse 2 s), Cycles previews day/night/interiors/penthouse, low-res bake of all 5 groups + panoramas + GLB export (`out_test/`, 19.6 MB before the last size fixes).
- **Not verified**: the browser viewer has never been run against baked assets. Last edits (shader mullions, JS Chihuly, removal of frame meshes from export, gltfpack) were made but the export was not re-run. First step on resume: re-run the low-res bake, `npx gltfpack -i out/bellagio.glb -o out/bellagio.glb -cc -kn -km -ke -vp 16`, pack, open in the browser and fix.

## Scorecard at pause (closeness to the real Bellagio)

Tower massing 85 · façade grammar 62 · crown 65 · night lighting 35 (floodlights added, not yet rendered) · lake/fountain layout 85 ·
fountain look 45 · choreography 20 · village 40 · trees 30 · ground 55 · neighbours 15 · lobby 30 · Fiori di Como 55 ·
conservatory 45 · casino/restaurants/rooms 0 · art 10 · textures 35 · browser world unverified. Overall ≈ 45 %.

## Next steps (in order)

1. Browser end-to-end test (above), then full-resolution bake.
2. Render night with the new floodlights and fountain fixes; compare with `ref/pano_tower.jpg`.
3. Casino floor (striped canopies, chandeliers, slots, carpet); public-domain paintings (Monet, Canaletto) in lobby/penthouse.
4. Village detail (loggias, iron balconies, bell tower, water-level terraces); proper tree species.
5. Publish as a multi-file Artifact (GLB must stay < 16 MB per file) — only when the owner asks.

## Known issues

- Neighbouring resorts are honest massing only. Sign font is Times (real: custom Trajan-like).
- Fountain choreography is invented (no show files or music).
- Lobby/penthouse/casino plans are inferred or invented, not surveyed.
