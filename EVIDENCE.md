# Bellagio digital twin — evidence ledger

Every element of the model is classified by the strength of its evidence. The model is an
artistic reconstruction built from public sources, not a survey-grade or licensed MGM Resorts model.

| Class | Meaning |
|---|---|
| **M – measured** | traced from georeferenced satellite imagery at stated resolution |
| **P – published** | a number taken from a published source |
| **F – photographed** | shape/colour read from reference photos (Wikimedia Commons) |
| **I – inferred** | plausible reconstruction where no evidence was available |
| **X – invented** | deliberate artistic addition that is *not* the real building |

## Sources

- ESRI World Imagery export (public), frames `data/sat.jpg` (760 m, 0.475 m/px) and `data/hi_core.jpg` (456 m, 0.2227 m/px), `data/eiffel_sat.jpg` (220 m).
- CTBUH Skyscraper Center: height 155.8 m, 36 floors, 3,005 rooms, architect Jerde Partnership.
- Wikipedia “Bellagio (resort)”: spa tower 33 floors / 928 rooms (2004), casino 156,000 sq ft, conservatory 13,500 sq ft, *Fiori di Como* 2,000 sq ft, 65 × 29 ft, >2,100 glass pieces.
- Wikipedia “Fountains of Bellagio”: lake 8.5 acres ≈ 1,200 × 600 ft, depth 4–13 ft; 1,214 nozzles = 208 oarsmen (77 ft), 798 mini-shooters (100 ft), 192 super-shooters (240 ft), 16 extreme-shooters (460 ft); 4,792 lights.
- Wikimedia Commons photos (night panorama Dec 2013, 2011 dusk front, 2019 night, conservatory 2019/2022/2026, fountains, lakefront village, Eiffel/Paris). Local copies in the session scratch `ref/` and `ref/ev/`.

## Ledger

| Element | Class | Evidence / method | Known error |
|---|---|---|---|
| Tower footprint (Y plan, three wings, kinks, end blocks) | M | traced wing centre-lines on hi_core; depth 20.5 / 23 m from roof widths | ±1.5 m (roof overhang, off-nadir lean) |
| Tower height 155.8 m, 36 floors | P | CTBUH | — |
| Façade grammar: 1 window = 2 rooms × 2 floors, row 6.1 m, bay 10.9 m | F + M | window rows counted on the 2013 panorama, scaled so the core drum matches its satellite diameter (19 m) | ±5 % |
| Belt courses 42.7 / 93 m, arcade 107–123.5 m, cornice 129 m | F | panorama at 0.111 m/px anchored at 155.8 m | ±1.5 m |
| End blocks two rows lower (117 m) | F + M | dusk and 2019 photos; separate roofs in imagery | ±3 m |
| Core cylinder, drum, BELLAGIO sign, lantern arcade, copper dome, finial | F | close-up photo `dome.jpg`, panorama | lettering font is Times, real is a custom Trajan-like serif |
| Diamond frieze, bifora arcade windows, oculi | F | photos | pattern approximate |
| Stucco / trim colours | F | day photos, tuned by eye | ±10 % in albedo |
| Hip roofs, grey-green metal | M + F | satellite roof tone and ridge lines | pitch inferred (11°) |
| Spa Tower footprint / 33 floors | M + P | satellite; height 118 m inferred from 33 floors | façade treated like the main tower (I) |
| Lake outline, fountain rings, the long arc, the front line | M | traced on hi_core (pipe rings visible under water) | ±1 m |
| Nozzle count and mix, jet heights | P | Fountains of Bellagio | positions along the pipes are distributed evenly (I) |
| Fountain choreography | I | shapes from photos (oarsmen fans, super-shooter walls); not the real show files | — |
| Lakefront village footprints and heights | M + F | footprints from imagery; 10–17 m heights from lake photos | façade details generic Italianate (I) |
| Shoreline boulders, awnings (red/blue), terraces, lamp posts | F | lake-level photos | counts/placement approximate |
| Via Bellagio domes and glass vaults, big dome | M + F | four domes and vaults visible in imagery | rib count inferred |
| Porte-cochère glass canopy | M + F | imagery (glass roof), photos | column count inferred |
| Lobby position (east face at the porte-cochère, terracotta pavilion over it) | M + I | pavilion roof in imagery; interior plan inferred | room size inferred |
| *Fiori di Como* | P + F | 65 × 29 ft, 2,100 pieces; colour mix from photos | piece shapes procedural |
| Lobby columns, coffers, desk, medallion floor | I | generic grand-hotel treatment | — |
| Conservatory size, glass barrel vault, green steel, cream arcades | P + M + F | 13,500 sq ft; glass roof in imagery; interior photos | seasonal display is a generic spring garden (I) |
| Conservatory scroll mosaic floor | F | photo shows flowing black scrolls on cream marble | procedural pattern, not the real layout |
| Pools (5 basins) | M | imagery | depth inferred |
| Trees (178) | M | vegetation classifier on hi_core, excludes roofs/lake/tower footprints; species by zone (I) | missed understorey, some shadows |
| Ground albedo (roads, markings, lawns, pavers) | M | the orthophoto itself, cast shadows lifted | residual shadows, flattened cars |
| Eiffel Tower replica position | M | base located on `eiffel_sat.jpg` | lattice simplified |
| Neighbouring resorts (Caesars, Cosmopolitan, Paris, Bally’s, Aria edge) | I | footprint + height massing only | not modelled architecture |
| **Penthouse (level 36), private lift, themed rooms, roof terrace** | **X** | invented at the owner’s request; fits inside the real shell and uses the real arcade windows and belvedere | not a real Bellagio space |
| Luxor pyramid | M + P | corners point N/E/S/W; they land on the OSM bounding box (184 × 182 m, centre 56 m east and 1,936 m south of the Bellagio core). Height 109 m (Wikipedia 357 ft); OSM tag 111 m | glass is one material, not the real mullion grid |
| Luxor ziggurat towers, Sphinx, obelisk | M + P + I | towers traced on the same orthophoto; Sphinx 106 × 80 × 262 ft; obelisk height inferred | Sphinx is still blocked out, not sculpted |
| Strip and valley | M + P + I | ESRI orthophoto; 7,300 OSM footprints. Tagged height used when present. Excalibur towers 79.5 m (Skyscraper Center) | most small buildings have an inferred height; several resorts are a single podium outline, so New York-New York and the MGM Grand read too low |

## Validation

- Render-vs-photo sheets: `renders/v3/compare_reference_v3.jpg` (and later versions).
- Fountain nozzle mix is asserted exactly equal to the published counts in `survey.fountain_nozzles()`.
