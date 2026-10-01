"""Luxor Las Vegas in the city frame (origin = Bellagio core, +X east, +Y north, metres).

Evidence: the glass pyramid is a square rotated 45° so its corners point north, east, south and west.
The OpenStreetMap outline is that square's axis-aligned bounding box: 184 x 180.5 m, centred at (54, -1938), height tag 111 m.
Wikipedia 357 ft (109 m), 30 storeys, black glass, inclinators at 39°, Sky Beam.
Twin ziggurat towers (1996-97) sit against the north corner, 22 storeys.
Sphinx 106 ft high, 80 ft wide, 262 ft long, east of the east corner. Obelisk height: inferred.
"""
import math
import bpy
from mathutils import Vector
from geo import MB, extrude_poly, sweep_profile, ccw

TAU = math.tau
C = Vector((56.3, -1936.0))      # centre of the OSM bounding box (M)
HALF = (92.3, 91.0)               # centre-to-corner, east and north (M). Corners point N/E/S/W.
H = 109.0                         # apex height (P)
LAT0, LON0 = 36.11298, -115.17643
PX = .296875                      # m per px of luxor_sat.jpg


def img2local(dx, dy):
    """Display px of the 1200-wide tower crop -> local metres (see luxor/tools notes)."""
    ox, oy = 822.9 + dx * 1.0217, 694.9 + dy * 1.0217
    return (-350.0 + ox * PX, -1520.0 - oy * PX)


def mats(M):
    def P(name, col, rough=.5, metal=0., emit=None, strength=0.):
        m = bpy.data.materials.new(name)
        b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (*col, 1)
        b.inputs['Roughness'].default_value = rough
        b.inputs['Metallic'].default_value = metal
        if emit:
            b.inputs['Emission Color'].default_value = (*emit, 1)
            b.inputs['Emission Strength'].default_value = strength
        M[name] = m
        return m
    P('lux_glass', (.015, .014, .012), .12, .85)
    P('lux_stucco', (.72, .63, .50), .8)
    P('lux_band', (.05, .05, .05), .3, .5)
    P('lux_sand', (.70, .58, .40), .85)
    P('lux_stone', (.62, .52, .38), .85)
    P('lux_gold', (.80, .60, .25), .3, 1.)
    P('lux_edge', (1, 1, 1), .5, emit=(1., .97, .9), strength=0.)
    P('lux_beam', (1, 1, 1), .5, emit=(.9, .95, 1.), strength=0.)


def pyramid(coll, M):
    g = MB('LUXOR_pyramid_glass', [M['lux_glass']])
    # south, east, north, west — corners on the OSM bounding box
    base = [(C.x, C.y - HALF[1]), (C.x + HALF[0], C.y), (C.x, C.y + HALF[1]), (C.x - HALF[0], C.y)]
    apex = (C.x, C.y, H)
    # each face subdivided into 30 horizontal bands (storeys) so the glass catches light floor by floor
    n = 30
    for i in range(4):
        a, b = base[i], base[(i + 1) % 4]
        for k in range(n):
            t0, t1 = k / n, (k + 1) / n
            A = (a[0] + (apex[0] - a[0]) * t0, a[1] + (apex[1] - a[1]) * t0, H * t0)
            B = (b[0] + (apex[0] - b[0]) * t0, b[1] + (apex[1] - b[1]) * t0, H * t0)
            Cc = (b[0] + (apex[0] - b[0]) * t1, b[1] + (apex[1] - b[1]) * t1, H * t1)
            D = (a[0] + (apex[0] - a[0]) * t1, a[1] + (apex[1] - a[1]) * t1, H * t1)
            g.quad(A, B, Cc, D, 0)
    edges = MB('EMIT_luxor_edges', [M['lux_edge']])
    for a in base:                      # LED lines along the four arrises (visible at night)
        edges.box_between((a[0], a[1], 0), apex, .5, .5, 0)
    cap = MB('LUXOR_apex', [M['lux_gold']])
    cap.cylinder((C.x, C.y, H - 1.2), 1.6, 1.4, n=12, m=0, r_top=.4)
    beam = MB('EMIT_luxor_beam', [M['lux_beam']])
    # Visual width of the scattered beam (the lamp itself is much narrower). Night only.
    beam.cylinder((C.x, C.y, H), 14.0, 1400, n=16, m=0, r_top=36.0, cap=False)
    return [g.build(coll, props={'nobake': 1, 'mat': 'luxor_glass'}), edges.build(coll, props={'emit': (1, .97, .9), 'strength': 30.0, 'dyn': 'night'}),
            cap.build(coll, smooth=True), beam.build(coll, props={'emit': (.9, .95, 1.), 'strength': 20.0, 'dyn': 'night', 'nobake': 1, 'beam': 1})]


def towers(coll, M):
    """Twin ziggurat towers north of the pyramid: full-height slab + terraces stepping down one side (traced)."""
    w = MB('LUXOR_towers', [M['lux_stucco'], M['lux_band']])
    FLOORS, FH, PODIUM = 22, 3.2, 6.0

    def slab(p0, p1, z1):
        (x0, y1), (x1, y0) = img2local(*p0), img2local(*p1)
        q = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        extrude_poly(w, q, 0, z1, 0, 0)
        for f in range(2, int((z1 - PODIUM) / FH)):   # dark window bands on every floor
            z = PODIUM + f * FH
            if z + 1.4 < z1:
                sweep_profile(w, ccw(q), z, [(0, 0), (.06, 0), (.06, 1.4), (0, 1.4)], 1)
    top = PODIUM + FLOORS * FH
    # west tower: slab + stepped mass descending east toward the pyramid axis
    slab((262, 95), (330, 395), top)
    for s in range(8):
        x0 = 330 + s * 46
        slab((x0, 150 + s * 28), (x0 + 46, 395), top - (s + 1) * 8.5)
    # east tower: slab + stepped wing descending east
    slab((720, 95), (790, 395), top)
    for s in range(5):
        x0 = 790 + s * 36
        slab((x0, 130), (x0 + 36, 265), top - (s + 1) * 12.0)
    return [w.build(coll)]


def sphinx(coll, M):
    """Sphinx (P: 106 ft high, 80 ft wide, 262 ft long) facing east toward the Strip, 141 m east of the pyramid centre."""
    s = MB('LUXOR_sphinx', [M['lux_sand'], M['lux_stone'], M['lux_gold']])
    cx, cy = 195.0, -1935.0
    L, W, Hh = 80.0, 24.4, 32.3
    # 1. Tiered plinth
    s.box((cx, cy, 1.5), (L + 14, W + 16, 3.0), 1)
    s.box((cx, cy, 3.5), (L + 8, W + 10, 1.5), 1)

    # 2. Lion hindquarters & flanks (stepped muscular body contours)
    s.box((cx - 16, cy, 4 + 7.0), (L * .52, W * .82, 14), 0)
    s.box((cx - 24, cy, 4 + 6.0), (L * .34, W * .90, 12), 0)
    # Haunch rounded sides
    for sy in (-1, 1):
        s.cylinder((cx - 20, cy + sy * (W * .41), 4), 6.5, 12.0, n=8, m=0)

    # 3. Extended forelegs and paws
    for sy in (-1, 1):
        py = cy + sy * 7.5
        # Foreleg beam
        s.box_between((cx - 2, py, 4 + 3.2), (cx + 34, py, 4 + 2.8), 7.2, 5.6, 0)
        # Rounded lion paw with claws
        s.cylinder((cx + 34, py, 4), 3.8, 3.6, n=8, m=0, r_top=3.2)
        s.box((cx + 36.5, py, 4 + 1.2), (3.0, 6.0, 2.4), 1)

    # 4. Muscular chest rising to shoulders
    s.box((cx + 6, cy, 4 + 11.5), (20, W * .72, 23), 0)
    s.cylinder((cx + 8, cy, 4 + 10), W * .34, 18.0, n=12, m=0, r_top=W * .28)

    # 5. Head and face
    s.cylinder((cx + 10, cy, 4 + 23.5), 5.5, 9.5, n=12, m=0)                # head core
    s.box((cx + 14.5, cy, 4 + 25.5), (2.2, 5.8, 6.5), 0)                    # facial plane
    s.box((cx + 15.6, cy, 4 + 26.2), (1.2, 2.4, 2.8), 1)                    # nose ridge
    s.box((cx + 13.8, cy, 4 + 21.8), (2.2, 2.0, 5.0), 2)                    # royal braided beard

    # 6. Nemes royal headdress (flared crown + draped lappets)
    # Top crown curve
    s.cylinder((cx + 9, cy, 4 + 27.5), 8.2, 6.5, n=12, m=2, r_top=6.8)      # gold striped nemes
    s.box((cx + 8, cy, 4 + 29.5), (14, 18, 5.5), 2)
    # Side lappets draped over chest
    for sy in (-1, 1):
        s.box_between((cx + 10, cy + sy * 7.8, 4 + 28), (cx + 11, cy + sy * 6.8, 4 + 16), 3.6, 3.2, 2)
        s.box((cx + 11, cy + sy * 6.8, 4 + 15), (4.2, 3.8, 3.0), 1)

    # 7. Uraeus (sacred royal cobra emblem at brow)
    s.box((cx + 15.2, cy, 4 + 31.8), (2.5, 1.8, 2.4), 2)
    s.cylinder((cx + 15.8, cy, 4 + 32.2), 0.7, 1.8, n=6, m=2)
    return [s.build(coll)]


def obelisk(coll, M):
    o = MB('LUXOR_obelisk', [M['lux_stone'], M['lux_gold']])
    x, y, h = 300.0, -1938.0, 43.0      # I: in front of the Sphinx on the Strip axis; ~140 ft
    o.box((x, y, 1.5), (9, 9, 3), 0)
    o.cylinder((x, y, 3), 2.9, h - 6, n=4, m=0, r_top=1.9)
    o.cylinder((x, y, 3 + h - 6), 1.9, 3.2, n=4, m=1, r_top=0.0)
    return [o.build(coll)]


def build(coll, M):
    mats(M)
    return pyramid(coll, M) + towers(coll, M) + sphinx(coll, M) + obelisk(coll, M)
