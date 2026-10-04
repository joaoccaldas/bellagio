// Guided places. Coordinates are survey metres (x east, y north, z up), converted in main.js.
function wingAt(w, s, t, z) {
  const [p0, p1, p2] = w.p;
  const n1 = Math.hypot(p1[0] - p0[0], p1[1] - p0[1]), n2 = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]);
  let o, d;
  if (s <= w.L1) { d = [(p1[0] - p0[0]) / n1, (p1[1] - p0[1]) / n1]; o = [p0[0] + d[0] * s, p0[1] + d[1] * s]; }
  else { d = [(p2[0] - p1[0]) / n2, (p2[1] - p1[1]) / n2]; o = [p1[0] + d[0] * (s - w.L1), p1[1] + d[1] * (s - w.L1)]; }
  return [o[0] - d[1] * t, o[1] + d[0] * t, z];
}

export function makePlaces(m) {
  const FL = m.penthouse.fl, TER = m.penthouse.terrace, E = 1.65, c = m.core;
  const N = m.wings.N, Sw = m.wings.S, Ww = m.wings.W;
  return [
    { group: 'Exterior', name: 'From the Strip', pos: [276, -40, 3], look: [0, 0, 70], tod: .42, note: 'Las Vegas Blvd sidewalk, morning light on the east facade.', evidence: 'M · surveyed' },
    { group: 'Exterior', name: 'Fountain show at night', pos: [274, 18, 3.2], look: [120, 0, 45], tod: .9, show: 'Grand finale', note: '1,214 nozzles on the surveyed pipe layout; heights up to 460 ft.', evidence: 'P · published specs' },
    { group: 'Exterior', name: 'Aerial over the lake', pos: [470, -380, 300], look: [40, -10, 40], note: 'The Y-plan tower, the lake, the Lake Como village and Via Bellagio.', evidence: 'M · surveyed' },
    { group: 'Exterior', name: 'Across the lake at dusk', pos: [262, 110, 22], look: [0, 0, 80], tod: .79, note: 'Golden hour to blue hour: floodlit bands switch on.', evidence: 'F · photographed' },
    { group: 'Exterior', name: 'Walk the Strip promenade', pos: [279, -80, E], look: [200, -60, 10], walk: true, note: 'Walk: drag to look, WASD / arrows (Shift runs). Mobile: the stick.', evidence: 'M · surveyed' },
    { group: 'Exterior', name: 'Porte-cochère', pos: [96, -100, E], look: [66, -100, 3.5], walk: true, note: 'Glass canopy on columns; the lobby doors ahead.', evidence: 'M · imagery' },
    { group: 'Las Vegas Strip', name: 'Walk toward the Luxor', pos: [300, -80, 1.7], look: [240, -600, 4], walk: true, tod: .45, note: 'On the sidewalk. Drag to look, WASD to walk, Shift to run. The Bellagio is behind you; the Luxor is about 1.8 km south.', evidence: 'M' },
    { group: 'Las Vegas Strip', name: 'Luxor pyramid', pos: [460, -1760, 45], look: [54, -1938, 50], tod: .45, note: '109 m black-glass pyramid (1993), Sphinx and obelisk facing the Strip; twin ziggurat towers behind. Press Walk to step down onto the street.', evidence: 'M + P' },
    { group: 'Las Vegas Strip', name: 'Sphinx at the Luxor', pos: [285, -1900, 5], look: [192, -1935, 20], tod: .72, note: 'The Sphinx: 106 ft high, 262 ft long, facing Las Vegas Blvd.', evidence: 'P · published size' },
    { group: 'Las Vegas Strip', name: 'Luxor Sky Beam at night', pos: [900, -1300, 180], look: [54, -1938, 300], tod: .93, note: 'The brightest beam of light on Earth, from the apex of the pyramid. The column is drawn wide enough to read; the real lamp is much narrower.', evidence: 'P' },
    { group: 'Las Vegas Strip', name: 'South Strip from above', pos: [780, -900, 680], look: [80, -1900, 20], tod: .4, note: 'Bellagio to Mandalay Bay. Resorts other than the Bellagio and the Luxor are OpenStreetMap footprints at their tagged height.', evidence: 'M · OSM' },
    { group: 'Las Vegas Strip', name: 'Mandalay Bay', pos: [480, -2550, 30], look: [150, -2320, 70], tod: .5, note: 'Gold tower south of the Luxor, 146 m, from OpenStreetMap.', evidence: 'M + P' },
    { group: 'Las Vegas Strip', name: 'Excalibur Castle & Spires', pos: [420, -1450, 42], look: [120, -1590, 75], tod: .48, note: 'Four 79.5 m castle towers with royal blue and crimson conical spires, turrets, and medieval gatehouse.', evidence: 'M + P' },
    { group: 'Las Vegas Strip', name: 'New York-New York Skyline', pos: [380, -1120, 45], look: [180, -1214, 90], tod: .74, note: 'Stepped Manhattan skyline, 161 m Empire State spire, Chrysler sunburst crown, and Brooklyn Bridge.', evidence: 'M + P' },
    { group: 'Las Vegas Strip', name: 'Aria & CityCenter', pos: [220, -480, 55], look: [-40, -608, 110], tod: .52, note: 'Sleek sweeping curved glass hotel towers rising 183 m along Harmon Ave.', evidence: 'M + P' },
    { group: 'Las Vegas Strip', name: 'The Cosmopolitan', pos: [300, -260, 45], look: [120, -350, 110], tod: .82, note: 'Twin 184 m Boulevard and Chelsea towers immediately flanking the Bellagio south boundary.', evidence: 'M + P' },
    { group: 'Las Vegas Strip', name: 'Caesars Palace & Colosseum', pos: [320, 320, 55], look: [80, 440, 70], tod: .44, note: 'Augustus (111 m) and Octavius (107 m) towers, Roman pediment rooflines, and the Colosseum arena.', evidence: 'M + P' },
    { group: 'Las Vegas Strip', name: 'The Mirage & Volcano', pos: [300, 840, 45], look: [112, 922, 65], tod: .78, note: 'The iconic 102 m gold Y-plan resort and front lagoon, as it stood in October 2022.', evidence: 'M + P' },
    { group: 'Las Vegas Strip', name: 'The STRAT Observation Needle', pos: [2150, 3500, 280], look: [1882, 3807, 260], tod: .86, note: '350 m observation needle tower, 12-story pod, and thrill rides overlooking the north Strip.', evidence: 'M + P' },
    { group: 'Las Vegas Strip', name: 'Welcome to Fabulous Las Vegas Sign', pos: [328, -3400, 5], look: [328, -3430, 7.5], tod: .84, note: 'The iconic 1959 Googie neon diamond sign, yellow star, and turquoise columns on the Las Vegas Blvd median.', evidence: 'P · landmark' },
    { group: 'Las Vegas Strip', name: 'Paris Eiffel Tower & Balloon', pos: [240, -90, 25], look: [370, -66, 75], tod: .76, note: 'The 164.6 m half-scale Eiffel Tower, Arc de Triomphe, and Montgolfier balloon across from the Bellagio lake.', evidence: 'M + P' },
    { group: 'Las Vegas Strip', name: 'High Roller Observation Wheel', pos: [610, 488, 55], look: [730, 488, 90], tod: .82, note: 'The 167.6 m (550 ft) observation wheel at The LINQ / Flamingo, with 28 spherical glass passenger cabins.', evidence: 'P' },
    { group: 'Las Vegas Strip', name: 'Big Apple Roller Coaster (NY-NY)', pos: [300, -1520, 22], look: [210, -1500, 35], tod: .62, note: 'Bright red tubular steel track looping and swooping past the Manhattan skyscraper towers.', evidence: 'P' },
    { group: 'Las Vegas Strip', name: 'Tropicana Elevated Skywalk', pos: [214, -1525, 8.5], look: [296, -1525, 8.5], walk: true, tod: .75, note: 'Walkable 4-way pedestrian skyway bridge over Tropicana Ave & Las Vegas Blvd connecting NY-NY, MGM, Excalibur, and Tropicana.', evidence: 'M' },
    { group: 'Las Vegas Strip', name: 'Flamingo Elevated Skywalk', pos: [165, 55, 8.5], look: [235, 55, 8.5], walk: true, tod: .75, note: 'Walkable 4-way pedestrian skyway bridge over Flamingo Rd & Las Vegas Blvd connecting Caesars, Cromwell, Bellagio, and Bally\'s.', evidence: 'M' },
    { group: 'Las Vegas Strip', name: 'The Venetian & Rialto Bridge', pos: [380, 890, 25], look: [457, 944, 70], tod: .70, note: '96 m St. Mark\'s Campanile copper spire and stone Rialto bridge spanning the Venetian canal.', evidence: 'M + P' },
    { group: 'Las Vegas Strip', name: 'Las Vegas Valley Panorama', pos: [2800, -600, 1600], look: [100, 200, 30], tod: .45, note: 'Full 12 km valley orthophoto ground texturing from south of Mandalay to downtown and mountain ring.', evidence: 'M · ESRI' },
    { group: 'Inside', name: 'Main lobby', pos: [64, -109, E], look: [40, -97, 5], walk: true, note: 'Coffered hall, gilded columns, medallion floor.', evidence: 'I · inferred plan' },
    { group: 'Inside', name: 'Fiori di Como', pos: [40, -103, E], look: [46, -99.5, 11], walk: true, note: 'Dale Chihuly, 1998: 65 × 29 ft, ~2,100 hand-blown glass flowers.', evidence: 'P · published size' },
    { group: 'Inside', name: 'Conservatory & Botanical Gardens', pos: [-1.5, -97.5, E], look: [-30, -101, 5], walk: true, note: '13,500 sq ft under a green-steel glass vault; the display changes five times a year.', evidence: 'P + F' },
    { group: 'The Penthouse (invented)', name: 'Take the private lift up', lift: 'up' },
    { group: 'The Penthouse (invented)', name: 'Lift foyer', pos: wingAt(Sw, Sw.L1 + 10, 0, FL + E), look: wingAt(Sw, 40, 0, FL + 2.5), walk: true, note: 'Black and white marble, a floral centrepiece.', evidence: 'X · invented' },
    { group: 'The Penthouse (invented)', name: 'Lake Como salon', pos: wingAt(N, 14.5, -6, FL + E), look: wingAt(N, 40, 3, FL + 4.5), walk: true, note: 'Fresco sky vault, crystal chandeliers, piano by the arcade windows over the lake.', evidence: 'X · invented' },
    { group: 'The Penthouse (invented)', name: 'Dining room', pos: wingAt(N, 50, 5, FL + E), look: wingAt(N, 75, -2, FL + 2), walk: true, note: 'A table for sixteen.', evidence: 'X · invented' },
    { group: 'The Penthouse (invented)', name: 'Rat Pack bar', pos: wingAt(N, N.L1 + 1.5, 5.5, FL + E), look: wingAt(N, N.L1 + 14, -4.5, FL + 1.6), walk: true, note: 'Backlit onyx, emerald velvet booths.', evidence: 'X · invented' },
    { group: 'The Penthouse (invented)', name: 'Glass gallery', pos: wingAt(Sw, 13, 0, FL + E), look: wingAt(Sw, 33, 0, FL + 3), walk: true, note: 'Blown-glass sculptures under a suspended glass cloud.', evidence: 'X · invented' },
    { group: 'The Penthouse (invented)', name: 'Spa & indoor pool', pos: wingAt(Sw, 37, -6.5, FL + E), look: wingAt(Sw, 62, 5, FL + 2.5), walk: true, note: 'A 22 m pool along the arcade windows.', evidence: 'X · invented' },
    { group: 'The Penthouse (invented)', name: 'Library', pos: wingAt(Ww, 13.5, 3, FL + E), look: wingAt(Ww, 34, -1, FL + 4), walk: true, evidence: 'X · invented' },
    { group: 'The Penthouse (invented)', name: 'Desert Moon bedroom', pos: wingAt(Ww, 44, 6, FL + E), look: wingAt(Ww, 62, -6, FL + 2.6), walk: true, note: 'A night-sky vault with a moon.', evidence: 'X · invented' },
    { group: 'The Penthouse (invented)', name: 'Master bath', pos: wingAt(Ww, (74.2 + Ww.L1 - .3) / 2, 0, FL + E), look: wingAt(Ww, (74.2 + Ww.L1 - .3) / 2, 7, FL + 1.4), walk: true, note: 'Onyx walls, a freestanding marble tub and twin vanities.', evidence: 'X · invented' },
    { group: 'The Penthouse (invented)', name: 'Dressing room', pos: wingAt(Ww, (Ww.L1 + .2 + Ww.L - .5) / 2, 0, FL + E), look: wingAt(Ww, Ww.L - 1.2, 0, FL + 2.2), walk: true, note: 'Walnut wardrobes, brass rails, a central island and mirrors.', evidence: 'X · invented' },
    { group: 'The Penthouse (invented)', name: 'Rotunda', pos: [c[0] + 7.4, c[1] - 2, FL + E], look: [c[0], c[1], FL + 16], walk: true, note: 'The atrium rises 34 m into the lantern; the stair climbs to the roof.', evidence: 'X · invented' },
    { group: 'The Penthouse (invented)', name: 'Roof terrace', pos: [c[0] - 6, c[1] + 16, TER + E], look: [c[0] + 260, c[1] - 30, 25], walk: true, tod: .78, note: '360° over the Strip, the lake and the mountains.', evidence: 'X · invented' },
    { group: 'The Penthouse (invented)', name: 'Belvedere (lantern)', pos: [c[0] + 7.6, c[1] + .6, 142.6], look: [c[0] + 320, c[1] + 40, 40], walk: true, tod: .88, note: 'Inside the real open lantern arcade, 150 m up.', evidence: 'F + X' },
  ];
}

export const INFO = `
<h3>How to explore</h3>
<p><b>Orbit</b>: drag to rotate, scroll to zoom. <b>Walk</b>: drag to look, WASD or arrows to move (Shift to run); on phones use the stick. Press <b>F</b> for a fountain show.</p>
<h3>What is real and what is not</h3>
<p>Every element carries an evidence class:
<span class="ev ev-M">M</span> measured on satellite imagery,
<span class="ev ev-P">P</span> published figure,
<span class="ev ev-F">F</span> read from photographs,
<span class="ev ev-I">I</span> inferred,
<span class="ev ev-X">X</span> invented.</p>
<ul>
<li>Tower: Y plan traced on imagery; 155.8 m / 36 floors (CTBUH); façade rhythm counted on photos (each window is two rooms by two floors).</li>
<li>Lake and fountain layout traced on imagery; 1,214 nozzles in the published mix; jet heights 77 / 100 / 240 / 460 ft.</li>
<li>Village, Via Bellagio domes, porte-cochère, pools and 178 trees placed from imagery; detailing from photos.</li>
<li>Lobby, Fiori di Como (65 × 29 ft) and the Conservatory (13,500 sq ft) sized from published figures; interior plans inferred.</li>
<li><b>The Penthouse, its lift and roof terrace are invented</b>: a residence imagined inside the real shell and arcade windows.</li>
<li>The Luxor pyramid, Sphinx, obelisk and ziggurat towers are modelled to published size on a footprint traced from imagery. The Sky Beam is widened so it reads on a phone.</li>
<li>The rest of the Strip, from Mandalay Bay to the Stratosphere plus downtown, is OpenStreetMap massing on an ESRI orthophoto. Tagged heights are used where OpenStreetMap has them; the others are inferred from the footprint.</li>
</ul>
<p class="fine">An independent artistic reconstruction from public sources. Not affiliated with or endorsed by MGM Resorts.</p>`;
