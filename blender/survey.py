"""Site survey for the Bellagio, traced from ESRI World Imagery (public, nadir-ish).

Trace image: hi_core.jpg, 456 m square exported at 2048 px, read at 2000 px display
=> 0.228 m per display pixel.  Origin = centre of the tower's core cylinder.
Blender axes: +X east (toward Las Vegas Blvd / the Strip), +Y north (toward Flamingo Rd), Z up.

Published figures used as hard constraints:
  tower 155.8 m / 36 floors (CTBUH), lake 8.5 acres ~ 1,200 x 600 ft, 1,214 nozzles,
  Fiori di Como 65 x 29 ft, conservatory 13,500 sq ft, spa tower 33 floors.
"""
import math

MPP = 0.228
CX, CY = 665, 755


def P(px, py):
    return ((px - CX) * MPP, (CY - py) * MPP)


def PL(pts):
    return [P(*p) for p in pts]


# ------------------------------------------------------------------ tower (Y plan)
# centre-lines; the outer segment of each wing is a lower "end block"
WING_N = PL([(665, 755), (700, 390), (758, 268)])
WING_S = PL([(665, 755), (700, 1060), (750, 1212)])
WING_W = PL([(665, 745), (222, 745), (125, 745)])
WING_DEPTH = {'N': 20.5, 'S': 20.5, 'W': 23.0}
CORE = (3.0, 0.0)          # cylinder sits slightly proud of the concave east facade
CORE_R = 10.5

# vertical grammar (m), read from the Dec-2013 panorama at 0.111 m/px, anchored at 155.8 m
ROW = 6.1                  # one visible window = two floors
BAY = 10.9                 # one visible window = two rooms wide
H_BELT1 = 42.7
H_BELT2 = 93.0
H_ARCH0 = 107.0
H_ARCH1 = 123.5
H_CORNICE = 129.0
H_END = 117.0              # end blocks step down two rows
H_DRUM = 139.0
H_LANTERN = 150.0
H_TOP = 155.8

# ------------------------------------------------------------------ spa tower (2004)
SPA = PL([(277, 1425), (277, 1995)])
SPA_DEPTH = 24.0
SPA_H = 118.0

# ------------------------------------------------------------------ lake (clockwise from NW corner)
LAKE = PL([
    (1655, 196), (1600, 238), (1540, 262), (1492, 300), (1470, 345), (1445, 400), (1385, 425), (1300, 425),
    (1255, 468), (1232, 520), (1240, 598), (1205, 650), (1190, 760), (1196, 850), (1236, 918), (1250, 1000),
    (1298, 1018), (1320, 1080), (1330, 1200), (1368, 1318), (1430, 1430), (1510, 1540), (1600, 1628),
    (1690, 1690), (1780, 1722), (1812, 1732), (1818, 1500), (1822, 1000), (1830, 500), (1838, 165), (1760, 158),
])
LAKE_LEVEL = -0.8

# fountain layout, visible as submerged pipe rings in the imagery
RING_BIG = (P(1465, 745), 85 * MPP, 125 * MPP)
RING_N = (P(1562, 522), 42 * MPP)
RING_S = (P(1598, 950), 42 * MPP)
ARC = PL([(1755, 275), (1700, 380), (1640, 480), (1590, 590), (1560, 690), (1545, 800), (1545, 900), (1560, 1050),
          (1575, 1150), (1590, 1250), (1600, 1330)])
FRONT_LINE = PL([(1790, 215), (1790, 1690)])

# ------------------------------------------------------------------ streets
STRIP_X = (1932 - CX) * MPP          # Las Vegas Blvd centre line
STRIP_W = 44.0
FLAMINGO_Y = 186.0                   # from the wider 0.475 m/px frame
DRIVE = PL([(1990, 1700), (1840, 1690), (1700, 1650), (1560, 1560), (1440, 1470), (1350, 1370), (1300, 1280),
            (1240, 1250), (1150, 1235), (1060, 1225), (985, 1215)])

# ------------------------------------------------------------------ podium, pavilions, glass roofs
PODIUM = PL([(800, 250), (985, 250), (985, 410), (1050, 410), (1050, 1135), (965, 1135), (965, 1260), (920, 1260),
             (920, 1330), (360, 1330), (360, 1100), (520, 1100), (560, 820), (600, 790), (600, 700), (800, 700)])
THEATER = PL([(155, 195), (520, 195), (520, 500), (155, 500)])       # "O" theatre fly tower
PARKING = PL([(360, 1380), (1090, 1380), (1090, 1720), (360, 1720)])
CONSERVATORY = PL([(485, 1125), (670, 1125), (670, 1265), (485, 1265)])
LOBBY = PL([(690, 1140), (960, 1140), (960, 1250), (690, 1250)])
PORTE = PL([(970, 1140), (1175, 1140), (1175, 1250), (970, 1250)])
VIA_DOMES = [P(1195, 305), P(1345, 220), P(1500, 225), P(1655, 180)]
VIA_DOME_R = 30 * MPP
BIG_DOME = (P(1010, 610), 45 * MPP)

# lakeside village: (x0,y0,x1,y1) display px, eave height m, roof kind, palette index
VILLAGE = [
    (1050, 370, 1110, 440, 17, 'hip', 0), (1140, 420, 1262, 500, 13, 'hip', 1), (1270, 318, 1332, 362, 11, 'hip', 2),
    (1340, 282, 1450, 380, 15, 'hip', 3), (1580, 228, 1648, 300, 13, 'hip', 1), (1050, 500, 1132, 612, 15, 'hip', 2),
    (1140, 540, 1222, 640, 13, 'hip', 0), (980, 668, 1092, 832, 14, 'fan', 3), (1090, 650, 1152, 722, 12, 'hip', 1),
    (1170, 850, 1256, 926, 13, 'hip', 2), (1050, 850, 1120, 905, 10, 'hip', 0), (915, 1130, 970, 1250, 16, 'lobbyroof', 3),
    (930, 1265, 995, 1360, 14, 'hip', 1), (1250, 55, 1332, 112, 12, 'hip', 2), (1470, 55, 1522, 98, 11, 'hip', 0),
    (1605, 48, 1705, 96, 12, 'hip', 3), (1718, 52, 1762, 92, 12, 'hip', 1), (1050, 90, 1110, 140, 14, 'hip', 2),
    (1300, 60, 1780, 150, 9, 'flat', 0), (1382, 358, 1470, 418, 8, 'flat', 0), (1135, 1000, 1180, 1060, 10, 'hip', 2),
    (1100, 380, 1135, 420, 12, 'hip', 1), (1340, 1680, 1410, 1730, 9, 'hip', 0), (1230, 1590, 1300, 1640, 9, 'hip', 3),
    (1480, 1700, 1540, 1750, 9, 'hip', 2), (1630, 1760, 1790, 1800, 9, 'hip', 1),
]

POOLS = [PL([(270, 915), (410, 915), (410, 1000), (270, 1000)]), PL([(125, 1090), (185, 1090), (185, 1265), (125, 1265)]),
         PL([(270, 1080), (322, 1080), (322, 1136), (270, 1136)]), PL([(270, 1200), (322, 1200), (322, 1258), (270, 1258)]),
         PL([(60, 1045), (110, 1045), (110, 1085), (60, 1085)])]

# neighbours (low-detail context massing): polygon, height
CONTEXT = [
    (PL([(130, -560), (560, -560), (560, -330), (130, -330)]), 105),       # Caesars Palace towers (north)
    (PL([(660, -520), (1060, -520), (1060, -390), (660, -390)]), 88),
    (PL([(2080, -300), (2300, -300), (2300, 60), (2080, 60)]), 95),        # Bally's (NE)
    ([(330, -160), (470, -160), (470, 30), (330, 30)], 22),                # Paris casino block (legs pass through)
    ([(480, -210), (570, -210), (570, -60), (480, -60)], 115),             # Paris hotel tower (approximate)
    (PL([(560, 2100), (880, 2100), (880, 2350), (560, 2350)]), 184),       # Cosmopolitan east tower
    (PL([(960, 2080), (1260, 2080), (1260, 2330), (960, 2330)]), 184),     # Cosmopolitan west tower
    (PL([(-420, 1500), (-120, 1500), (-120, 2200), (-420, 2200)]), 60),    # Aria / CityCenter edge (SW)
]

# Paris Las Vegas half-scale Eiffel Tower: base centre located on ESRI imagery (data/eiffel_sat.jpg)
EIFFEL = (389.0, -66.0)

# ------------------------------------------------------------------ interior (inside the podium)
LOBBY_BOX = (22.0, -112.0, 68.4, -88.0, 9.5)       # east wall = podium face at the porte-cochere        # x0,y0,x1,y1, ceiling height
CHIHULY = (45.2, -100.0, 65 * .3048, 29 * .3048)      # centre x,y, length, width
CONS_BOX = (-41.0, -116.0, 1.0, -84.0, 17.0)         # conservatory, 42 x 32 m = 13.5k sq ft
PASSAGE = (1.0, -106.0, 22.0, -94.0, 7.5)


def fountain_nozzles():
    """1,214 nozzles distributed over the traced pipe layout (oarsmen, mini, super, extreme)."""
    out = []

    def add(x, y, kind, group, u):
        out.append({'x': round(x, 2), 'y': round(y, 2), 'k': kind, 'g': group, 'u': round(u, 4)})

    (cx, cy), r0, r1 = RING_BIG
    for i in range(120):
        a = i / 120 * math.tau
        add(cx + r0 * math.cos(a), cy + r0 * math.sin(a), 'mini', 'ring_in', i / 120)
    for i in range(160):
        a = i / 160 * math.tau
        add(cx + r1 * math.cos(a), cy + r1 * math.sin(a), 'oar' if i % 2 else 'mini', 'ring_out', i / 160)
    for key, (c, r) in (('ring_n', RING_N), ('ring_s', RING_S)):
        for i in range(56):
            a = i / 56 * math.tau
            add(c[0] + r * math.cos(a), c[1] + r * math.sin(a), 'mini', key, i / 56)
    # the long double arc: supers every 4th, extremes spaced along it
    seg = []
    for a, b in zip(ARC, ARC[1:]):
        seg.append((a, b, math.dist(a, b)))
    L = sum(s[2] for s in seg)

    def along(t):
        d = t * L
        for a, b, l in seg:
            if d <= l:
                k = d / l
                return a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, (b[0] - a[0]) / l, (b[1] - a[1]) / l
            d -= l
        a, b, l = seg[-1]
        return b[0], b[1], (b[0] - a[0]) / l, (b[1] - a[1]) / l

    n_arc = 400
    for i in range(n_arc):
        t = i / (n_arc - 1)
        x, y, tx, ty = along(t)
        side = 1.2 if i % 2 else -1.2
        kind = 'super' if i % 4 == 0 else ('oar' if i % 4 == 2 else 'mini')
        add(x - ty * side, y + tx * side, kind, 'arc', t)
    for i in range(16):
        x, y, _, _ = along((i + .5) / 16)
        add(x, y, 'extreme', 'arc_x', (i + .5) / 16)
    (x0, y0), (x1, y1) = FRONT_LINE
    n = 1214 - len(out)
    # fill the published mix exactly: 208 oarsmen, 798 mini, 192 super, 16 extreme
    have = {}
    for o in out:
        have[o['k']] = have.get(o['k'], 0) + 1
    need = {'super': 192 - have.get('super', 0), 'oar': 208 - have.get('oar', 0)}
    need['mini'] = n - need['super'] - need['oar']
    kinds = sorted([((j + .5) / c, k) for k, c in need.items() for j in range(c)])
    for i, (_, kind) in enumerate(kinds):
        t = i / (n - 1)
        add(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, kind, 'front', t)
    return out
