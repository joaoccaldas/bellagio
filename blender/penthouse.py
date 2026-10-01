"""THE PENTHOUSE -- an invented full-floor residence on level 36 (z = 107 m), inside the surveyed shell.

Nothing here is claimed as the real Bellagio: it is an artistic layer placed behind the real arcade
windows (107-123.5 m), reached by a private lift from the lobby passage, with a roof terrace ring
around the drum and the (real) open belvedere under the lantern.

Zones (wing-local coordinates: s = metres from the core along the wing, t = metres across, +left):
  N  Lake Como Salon   : salon (fresco vault, chandeliers, piano, fireplace) | dining | Rat Pack bar (end block)
  S  Fiori              : glass gallery | spa with indoor pool | lift foyer + kitchen (end block)
  W  Desert Moon        : library | master bedroom | bath | dressing (end block)
  core                  : rotunda atrium to the lantern, helical stair to the terrace
"""
import math, os, random
import bpy
from mathutils import Vector, noise
import survey as S
import tower
from geo import MB, sweep_profile, balustrade, v2, circle_pts, ccw, offset_closed

TAU = math.tau
DATA = os.path.join(os.path.dirname(__file__), '..', 'data')
rnd = random.Random(36)

FL = 107.02                     # finished floor, level 36
CEIL_MAIN = 122.6               # double-height rooms behind the arcade
CEIL_END = 113.0                # end blocks (one row lower)
TERRACE = 131.6                 # deck ring around the drum, above the hip-roof ridges
LIFT = Vector((16.2, -92.5))    # shaft centre (inside the south end block, opens onto the lobby passage)


# ------------------------------------------------------------------ wing frames
class Wing:
    def __init__(self, pts, depth):
        self.p = [v2(p) for p in pts]
        self.d1 = (self.p[1] - self.p[0]).normalized()
        self.d2 = (self.p[2] - self.p[1]).normalized()
        self.L1 = (self.p[1] - self.p[0]).length
        self.L = self.L1 + (self.p[2] - self.p[1]).length
        self.w = depth

    def frame(self, s):
        if s <= self.L1:
            d = self.d1
            o = self.p[0] + d * s
        else:
            d = self.d2
            o = self.p[1] + d * (s - self.L1)
        n = Vector((-d.y, d.x))
        return o, d, n

    def at(self, s, t, z):
        o, d, n = self.frame(s)
        q = o + n * t
        return (q.x, q.y, z)

    def ang(self, s):
        _, d, _ = self.frame(s)
        return math.atan2(d.y, d.x)


WINGS = {'N': Wing(S.WING_N, S.WING_DEPTH['N']), 'S': Wing(S.WING_S, S.WING_DEPTH['S']), 'W': Wing(S.WING_W, S.WING_DEPTH['W'])}


def img_mat(name, file, rough=.4, coat=0.0, scale=1.0):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = coat
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(os.path.join(DATA, file), check_existing=True)
    uv = nt.nodes.new('ShaderNodeUVMap'); uv.uv_map = 'UVMap'
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale, scale, 1)
    nt.links.new(uv.outputs['UV'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], t.inputs['Vector'])
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    return m


def P(mat, name, color, rough=.5, metal=0., coat=0., emit=None, strength=0., sheen=0.):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Sheen Weight'].default_value = sheen
    b.inputs['Sheen Tint'].default_value = (*[min(1, c * 1.8 + .05) for c in color], 1)
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = strength
    mat[name] = m
    return m


def materials(M):
    X = {}
    X['parquet'] = img_mat('ph_parquet', 'ph_parquet.jpg', .35, .3, scale=1.0)
    X['checker'] = img_mat('ph_checker', 'ph_checker.jpg', .1, .4, scale=1.0)
    X['travertine'] = img_mat('ph_travertine', 'ph_travertine.jpg', .5, 0, scale=.67)
    X['fresco'] = img_mat('ph_fresco', 'ph_fresco.jpg', .8)
    X['books'] = img_mat('ph_books', 'ph_books.jpg', .7)
    P(X, 'damask', (.70, .55, .33), .55, sheen=.4)           # Lake Como silk walls
    P(X, 'burgundy', (.22, .03, .04), .5, sheen=.5)
    P(X, 'walnut', (.10, .045, .02), .35, coat=.5)
    P(X, 'emerald_velvet', (.01, .12, .06), .8, sheen=1.0)
    P(X, 'ivory', (.86, .82, .74), .45)
    P(X, 'white_marble', (.90, .89, .86), .08, coat=.6)
    P(X, 'indigo', (.03, .04, .16), .6, sheen=.4)            # Desert Moon
    P(X, 'midnight_velvet', (.02, .02, .08), .85, sheen=1.0)
    P(X, 'gold', (.85, .64, .30), .22, metal=1.)
    P(X, 'brass', (.72, .52, .24), .3, metal=1.)
    P(X, 'chrome', (.8, .8, .82), .08, metal=1.)
    P(X, 'linen', (.90, .88, .83), .8, sheen=.6)
    P(X, 'cream_sofa', (.82, .76, .64), .75, sheen=.8)
    P(X, 'black_lacquer', (.01, .01, .012), .08, coat=1.)
    P(X, 'onyx', (.85, .60, .30), .1, coat=.6, emit=(1.0, .62, .28), strength=1.2)   # backlit onyx bar
    P(X, 'mirror', (.95, .95, .95), .01, metal=1.)
    P(X, 'crystal', (1, 1, 1), .02, emit=(1.0, .9, .72), strength=8.)
    P(X, 'warm_light', (1, 1, 1), .5, emit=(1.0, .78, .5), strength=18.)
    P(X, 'moon_light', (1, 1, 1), .5, emit=(.85, .9, 1.0), strength=10.)
    P(X, 'fire', (1, .5, .1), .5, emit=(1.0, .45, .1), strength=25.)
    P(X, 'plant', (.03, .09, .02), .8)
    P(X, 'teak', (.30, .16, .07), .6)
    P(X, 'stone', (.72, .65, .54), .7)
    P(X, 'cushion_white', (.88, .87, .84), .85, sheen=.5)
    P(X, 'art1', (.55, .30, .12), .6)
    P(X, 'art2', (.10, .20, .35), .6)
    P(X, 'art3', (.60, .50, .20), .6)
    X['pool'] = M['pool_water']
    X['glass_art'] = M['chihuly']
    return X


# ------------------------------------------------------------------ furniture kit (all in wing-local frames)
class Room:
    """Places geometry in a wing at (s, t, z) with the wing's rotation."""

    def __init__(self, wing, mbs):
        self.w, self.mb = wing, mbs

    def p(self, s, t, z):
        return self.w.at(s, t, z)

    def box(self, key, s, t, z, ds, dt, dz, m=0):
        """Box centred at (s,t) with size along s (ds), across (dt), height dz; z = bottom."""
        c = self.p(s, t, z + dz / 2)
        self.mb[key].box(c, (ds, dt, dz), m, rot=self.w.ang(s))

    def cyl(self, key, s, t, z, r, h, n=16, m=0, r_top=None):
        c = self.p(s, t, z)
        self.mb[key].cylinder(c, r, h, n=n, m=m, r_top=r_top)

    def lathe(self, key, s, t, prof, n=24, m=0):
        c = self.p(s, t, 0)
        self.mb[key].lathe(c, prof, n, m)


def sofa(R, s, t, z, length=3.2, facing=1, mat='cream_sofa'):
    """facing = +1 faces +t (across the wing), -1 faces -t."""
    d = .95
    R.box(mat, s, t, z + .12, length, d, .32)                                    # seat base
    R.box(mat, s, t - facing * .38, z + .44, length, .22, .5)                    # back
    for ds in (-length / 2 + .12, length / 2 - .12):
        R.box(mat, s + ds, t, z + .44, .24, d, .22)                               # arms
    for k in range(3):                                                           # seat cushions
        R.box(mat, s - length / 3 + k * length / 3, t + facing * .08, z + .44, length / 3 - .04, .72, .14)
    for k in range(4):                                                           # scatter cushions
        R.box('cushion', s - length / 2 + .45 + k * (length - .9) / 3, t - facing * .22, z + .58, .42, .14, .4)
    for ds in (-length / 2 + .1, length / 2 - .1):
        for dt in (-.38, .38):
            R.cyl('gold', s + ds, t + dt, z, .035, .12, n=8)


def armchair(R, s, t, z, facing=1, mat='cream_sofa'):
    R.box(mat, s, t, z + .15, .85, .85, .3)
    R.box(mat, s, t - facing * .35, z + .45, .85, .16, .55)
    R.box(mat, s - .38, t, z + .45, .12, .8, .22)
    R.box(mat, s + .38, t, z + .45, .12, .8, .22)
    R.box(mat, s, t + facing * .05, z + .45, .62, .62, .12)


def rug(R, s, t, z, ls, lt, c1='rug_a', border='rug_b'):
    R.box(border, s, t, z, ls, lt, .018)
    R.box(c1, s, t, z + .002, ls - .5, lt - .5, .018)


def coffee_table(R, s, t, z, ls=1.6, lt=.9):
    R.box('white_marble', s, t, z + .38, ls, lt, .05)
    R.box('gold', s, t, z, ls - .2, lt - .2, .04)
    for ds in (-ls / 2 + .15, ls / 2 - .15):
        for dt in (-lt / 2 + .15, lt / 2 - .15):
            R.cyl('gold', s + ds, t + dt, z, .025, .38, n=8)


def chandelier(R, s, t, z_ceiling, r=1.2, tiers=3, drop=3.0):
    """Crystal chandelier: rod, gilt frame rings, crystal drops, candle bulbs."""
    zc = z_ceiling - drop
    R.cyl('gold', s, t, zc, .03, drop, n=6)
    for k in range(tiers):
        rr = r * (1 - k * .28)
        zk = zc + k * .55
        c = R.p(s, t, zk)
        pts = circle_pts((c[0], c[1]), rr, 24)
        sweep_profile(R.mb['gold'], pts, zk, [(-.04, 0), (.04, 0), (.04, .05), (-.04, .05)], 0)
        n = int(10 + rr * 10)
        for i in range(n):
            a = i / n * TAU
            x, y = c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)
            R.mb['crystal'].cylinder((x, y, zk + .05), .025, .09, n=6, m=0)
            R.mb['crystal'].cylinder((x, y, zk - .35), .03, .3, n=6, m=0, r_top=.005)
    R.mb['crystal'].dome(R.p(s, t, 0), r * .35, .5, n=16, rings=4, m=0, z0=zc - .5)


def floor_lamp(R, s, t, z):
    R.cyl('brass', s, t, z, .16, .03, n=16)
    R.cyl('brass', s, t, z, .015, 1.55, n=6)
    R.cyl('linen', s, t, z + 1.45, .24, .32, n=16, r_top=.16)
    R.cyl('warm', s, t, z + 1.5, .1, .18, n=8)


def plant(R, s, t, z, h=2.2):
    """Potted palm / fiddle-leaf: stems with many small blade leaves."""
    R.lathe('stone', s, t, [(.3, z), (.36, z + .1), (.28, z + .55), (.34, z + .6), (0, z + .6)], 16)
    c = Vector(R.p(s, t, z + .6))
    for k in range(9):
        a = k / 9 * TAU + rnd.random() * .5
        tip = c + Vector((.5 * math.cos(a), .5 * math.sin(a), h * (.55 + .45 * rnd.random())))
        R.mb['plant'].box_between(c, tip, .03, .03, 0)
        for j in range(6):
            b = a + rnd.uniform(-1.2, 1.2)
            base = c.lerp(tip, .45 + j * .1)
            L = .35 + rnd.random() * .25
            d = Vector((math.cos(b), math.sin(b), .35 - rnd.random() * .5)).normalized()
            side = d.cross(Vector((0, 0, 1))).normalized() * .09
            p1, p2 = base + d * L * .5, base + d * L
            R.mb['plant'].poly([base, p1 - side, p2, p1 + side], 0)


def blobl(mb, c, s, m=0, n1=8, n2=5):
    rings = []
    seed = Vector(c) * .7
    for i in range(n2 + 1):
        th = math.pi * i / n2
        ring = []
        for j in range(n1):
            ph = TAU * j / n1
            d = Vector((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)))
            k = 1 + .3 * noise.noise(d * 2.3 + seed)
            ring.append((c[0] + d.x * s[0] * k, c[1] + d.y * s[1] * k, c[2] + d.z * s[2] * k))
        rings.append(ring)
    for i in range(n2):
        for j in range(n1):
            k2 = (j + 1) % n1
            mb.quad(rings[i][j], rings[i + 1][j], rings[i + 1][k2], rings[i][k2], m)


def artwork(R, s, t, z, w, h, facing, mat):
    """Framed canvas on a wall plane at t (facing = direction into the room)."""
    R.box('gold', s, t, z, w + .16, .06, h + .16)
    R.box(mat, s, t + facing * .035, z + .08, w, .02, h)


def partition(R, s, z0, z1, mat, door_w=3.2, door_h=5.2, thick=.35):
    """Cross wall at s with a central doorway (gilded architrave)."""
    w = R.w.w - .9
    side = (w - door_w) / 2
    for sg in (-1, 1):
        R.box(mat, s, sg * (door_w / 2 + side / 2), z0, thick, side, z1 - z0)
    R.box(mat, s, 0, z0 + door_h, thick, door_w, z1 - z0 - door_h)
    for sg in (-1, 1):
        R.box('gold', s, sg * (door_w / 2 + .09), z0, thick + .1, .18, door_h + .18)
    R.box('gold', s, 0, z0 + door_h, thick + .1, door_w + .36, .18)


def wall_lining(R, s0, s1, z0, z1, mat, inset=.55):
    """Silk/paneled lining along both long walls between the window bays (piers only) + skirting + cornice."""
    for sg in (-1, 1):
        t = sg * (R.w.w / 2 - inset)
        # piers between the 10.9 m bays: lining panels leave the windows clear (integer bay loop)
        for nb in range(int(math.floor(s0 / S.BAY)), int(math.ceil(s1 / S.BAY))):
            c = (nb + .5) * S.BAY
            win0, win1 = c - 3.3, c + 3.3
            for a, b in ((max(s0, nb * S.BAY), min(s1, win0)), (max(s0, win1), min(s1, (nb + 1) * S.BAY))):
                if b - a > .1:
                    R.box(mat, (a + b) / 2, t, z0, b - a, .08, z1 - z0)
            for dd in (-3.25, 3.25):                                              # silk drapes framing each window
                if s0 < c + dd < s1:
                    R.box('drape', c + dd, t - sg * .12, z0, .7, .18, z1 - z0 - .4)
            if s0 < c < s1:
                R.box('gold', c, t - sg * .1, z1 - .5, 7.6, .16, .16)             # pelmet rod
        R.box('gold', (s0 + s1) / 2, t - sg * .06, z0, s1 - s0, .06, .22)        # skirting
        R.box('gold', (s0 + s1) / 2, t - sg * .08, z1 - .3, s1 - s0, .14, .3)    # cornice


def floor_ceiling(R, s0, s1, z_floor, z_ceil, fmat, cmat, vault=False, vault_mat=None):
    w = R.w.w - .9
    a, b, c, d = R.p(s0, -w / 2, z_floor), R.p(s1, -w / 2, z_floor), R.p(s1, w / 2, z_floor), R.p(s0, w / 2, z_floor)
    L = s1 - s0
    R.mb[fmat].quad(a, b, c, d, 0, uv=[(0, 0), (L / 8, 0), (L / 8, w / 8), (0, w / 8)])
    if not vault:
        a, b, c, d = [R.p(ss, tt, z_ceil) for ss, tt in ((s0, -w / 2), (s0, w / 2), (s1, w / 2), (s1, -w / 2))]
        R.mb[cmat].quad(a, b, c, d, 0)
        return
    # segmental barrel vault (fresco) springing from a gilded cornice
    spring = z_ceil - 3.2
    k = 14
    rise = 3.2
    for i in range(k):
        t0, t1 = -w / 2 + w * i / k, -w / 2 + w * (i + 1) / k
        z0 = spring + rise * math.sin(math.pi * i / k)
        z1 = spring + rise * math.sin(math.pi * (i + 1) / k)
        R.mb[vault_mat].quad(R.p(s0, t0, z0), R.p(s1, t0, z0), R.p(s1, t1, z1), R.p(s0, t1, z1), 0,
                             uv=[(0, i / k), (1, i / k), (1, (i + 1) / k), (0, (i + 1) / k)])
    for sg in (-1, 1):
        R.box('gold', (s0 + s1) / 2, sg * (w / 2 - .2), spring - .35, L, .4, .35)
    # transverse gilded ribs every 5.45 m
    ss = s0 + 2.7
    while ss < s1 - 1:
        for i in range(k):
            t0, t1 = -w / 2 + w * i / k, -w / 2 + w * (i + 1) / k
            R.mb['gold'].box_between(R.p(ss, t0, spring + rise * math.sin(math.pi * i / k) - .05),
                                     R.p(ss, t1, spring + rise * math.sin(math.pi * (i + 1) / k) - .05), .22, .12, 0)
        ss += 5.45


# ------------------------------------------------------------------ zones
def lake_como(R):
    """North wing: grand salon, dining, Rat Pack bar."""
    Wg = R.w
    # --- grand salon s 12..48
    s0, s1 = 12.0, 48.0
    floor_ceiling(R, s0, s1, FL, CEIL_MAIN, 'parquet', 'ivory', vault=True, vault_mat='fresco')
    wall_lining(R, s0, s1, FL, CEIL_MAIN - 3.3, 'damask')
    rug(R, 22, 0, FL, 9, 6.5)
    rug(R, 38, 0, FL, 9, 6.5)
    for sc in (22, 38):
        sofa(R, sc, -2.4, FL, 3.4, 1)
        sofa(R, sc, 2.4, FL, 3.4, -1)
        armchair(R, sc - 3.2, 0, FL, 1)
        armchair(R, sc + 3.2, 0, FL, -1)
        coffee_table(R, sc, 0, FL)
        chandelier(R, sc, 0, CEIL_MAIN - .2, r=1.5, tiers=3, drop=3.6)
    # fireplace on the partition at s 30 (a freestanding marble chimneypiece in the middle)
    R.box('white_marble', 30, -7.6, FL, 3.2, .7, 1.6)
    R.box('fire', 30, -7.4, FL + .25, 1.6, .3, .8)
    R.box('white_marble', 30, -7.8, FL + 1.6, 3.6, .4, 3.6)
    R.box('gold', 30, -7.55, FL + 2.6, 2.0, .06, 1.4)
    # grand piano (black lacquer) by the east windows
    R.box('black_lacquer', 44, 5.2, FL + .72, 2.7, 1.55, .3)
    R.box('black_lacquer', 43.6, 5.6, FL + 1.02, 1.8, 1.0, .06)
    for ds, dt in ((-1.1, -.6), (-1.1, .6), (1.1, 0)):
        R.box('black_lacquer', 44 + ds, 5.2 + dt, FL, .14, .14, .72)
    R.box('ivory', 42.75, 5.2, FL + .8, .22, 1.3, .04)
    for (sa, ta) in ((15, -7.8), (26, 7.8), (34, -7.8), (46, 7.8)):
        artwork(R, sa, ta, FL + 3.2, 2.6, 1.8, -1 if ta > 0 else 1, rnd.choice(['art1', 'art2', 'art3']))
    for (sa, ta) in ((13.5, 7.2), (13.5, -7.2), (47, -7.2)):
        plant(R, sa, ta, FL)
    for (sa, ta) in ((18.5, -3.8), (41.5, 3.8)):
        floor_lamp(R, sa, ta, FL)
    partition(R, 48.0, FL, CEIL_MAIN - 3.3, 'damask')
    # --- dining s 48..83
    s0, s1 = 48.2, Wg.L1 - .3
    floor_ceiling(R, s0, s1, FL, CEIL_MAIN - 3.3, 'checker', 'ivory')
    wall_lining(R, s0, s1, FL, CEIL_MAIN - 3.6, 'burgundy')
    R.box('walnut', 65.5, 0, FL + .72, 12.0, 1.8, .08)                 # table for 16
    for ds in (-5.0, 5.0):
        R.box('walnut', 65.5 + ds, 0, FL, .5, 1.0, .72)
    for k in range(8):
        for sg in (-1, 1):
            sc = 60.25 + k * 1.5
            R.box('burgundy_chair', sc, sg * 1.25, FL + .42, .5, .5, .1)
            R.box('burgundy_chair', sc, sg * 1.52, FL + .52, .5, .08, .75)
            for dd in (-.2, .2):
                R.cyl('gold', sc + dd, sg * 1.25, FL, .025, .42, n=6)
    for sc in (60.5, 70.5):
        chandelier(R, sc, 0, CEIL_MAIN - 3.3, r=1.1, tiers=2, drop=2.4)
    for k in range(7):                                                      # candelabra + flowers
        R.cyl('gold', 60 + k * 1.8, 0, FL + .8, .05, .35, n=8)
        R.cyl('warm', 60 + k * 1.8, 0, FL + 1.15, .02, .08, n=6)
    blobl(R.mb['flowers'], R.p(65.5, 0, FL + 1.05), (.9, .35, .25))
    R.box('walnut', 55, -7.4, FL, 4.0, .6, .95)                             # sideboard
    R.box('mirror', 55, -7.75, FL + 1.3, 3.2, .04, 2.2)
    partition(R, Wg.L1, FL, CEIL_END, 'walnut', door_w=2.6, door_h=3.2)
    # --- Rat Pack bar (end block) s L1..L
    s0, s1 = Wg.L1 + .2, Wg.L - .5
    floor_ceiling(R, s0, s1, FL, CEIL_END, 'parquet', 'walnut')
    wall_lining(R, s0, s1, FL, CEIL_END - .3, 'walnut')
    bs = s0 + 6
    R.box('onyx', bs, -4.8, FL, 8.0, .8, 1.1)                               # backlit onyx bar
    R.box('black_lacquer', bs, -4.8, FL + 1.1, 8.3, 1.0, .06)
    R.box('mirror', bs, -8.4, FL + 1.2, 7.0, .05, 2.6)
    for k in range(6):                                                      # bottle shelves
        for j in range(12):
            R.cyl('bottle', bs - 3.2 + j * .55, -8.2, FL + 1.3 + k * .42, .045, .32, n=6)
        R.box('glass_shelf', bs, -8.2, FL + 1.28 + k * .42, 7.0, .3, .02)
    for k in range(6):                                                      # bar stools
        R.cyl('brass', bs - 3.1 + k * 1.2, -3.8, FL, .03, .75, n=6)
        R.cyl('emerald_velvet', bs - 3.1 + k * 1.2, -3.8, FL + .75, .22, .09, n=12)
    for k in range(3):                                                      # emerald velvet booths
        sb = s0 + 3 + k * 5.5
        R.box('emerald_velvet', sb, 6.6, FL, 3.2, 1.2, .45)
        R.box('emerald_velvet', sb, 7.3, FL + .45, 3.2, .3, .8)
        R.cyl('black_lacquer', sb, 5.5, FL, .45, .72, n=16)
        R.cyl('warm', sb, 5.5, FL + .8, .1, .2, n=8)
    for k in range(4):
        R.cyl('brass', s0 + 3 + k * 5.5, 0, CEIL_END - .6, .35, .12, n=16, r_top=.1)
        R.cyl('warm', s0 + 3 + k * 5.5, 0, CEIL_END - .7, .28, .06, n=16)


def fiori(R):
    """South wing: glass gallery, spa with pool, lift foyer + kitchen."""
    Wg = R.w
    s0, s1 = 12.0, 34.0
    floor_ceiling(R, s0, s1, FL, CEIL_MAIN - 3.3, 'white_marble_floor', 'ivory')
    wall_lining(R, s0, s1, FL, CEIL_MAIN - 3.6, 'white_marble')
    # glass sculptures on plinths (Chihuly-like colour, not reproductions)
    for k in range(6):
        sc = s0 + 2.5 + k * 3.4
        for sg in (-1, 1):
            R.box('white_marble', sc, sg * 3.2, FL, .8, .8, 1.1)
            c = R.p(sc, sg * 3.2, FL + 1.1)
            glass_sculpture(R.mb['glassart'], c, 1.0 + rnd.random() * .8)
    # suspended glass "cloud" down the gallery axis
    for k in range(40):
        sc = s0 + 2 + rnd.random() * (s1 - s0 - 4)
        c = R.p(sc, rnd.uniform(-1.8, 1.8), CEIL_MAIN - 4.2 - rnd.random() * 1.2)
        glass_sculpture(R.mb['glassart'], c, .45, hanging=True)
    partition(R, 34.0, FL, CEIL_MAIN - 3.3, 'white_marble')
    # --- spa s 34..L1
    s0, s1 = 34.2, Wg.L1 - .3
    floor_ceiling(R, s0, s1, FL, CEIL_MAIN, 'travertine', 'ivory', vault=True, vault_mat='ivory')
    wall_lining(R, s0, s1, FL, CEIL_MAIN - 3.3, 'travertine_wall')
    # 22 x 5.2 m pool along the east (arcade) side, infinity edge toward the windows
    ps0, ps1, pt = s0 + 4, s1 - 4, 4.4
    for (sa, sb, ta, tb) in ((ps0, ps1, pt - 2.8, pt - 2.6), (ps0, ps1, pt + 2.6, pt + 2.8), (ps0 - .2, ps0, pt - 2.8, pt + 2.8), (ps1, ps1 + .2, pt - 2.8, pt + 2.8)):
        R.box('travertine_wall', (sa + sb) / 2, (ta + tb) / 2, FL, sb - sa, tb - ta, .45)
    R.box('pool_tile', (ps0 + ps1) / 2, pt, FL - 1.4, ps1 - ps0, 5.2, .02)
    wa, wb, wc, wd = R.p(ps0, pt - 2.6, FL + .38), R.p(ps1, pt - 2.6, FL + .38), R.p(ps1, pt + 2.6, FL + .38), R.p(ps0, pt + 2.6, FL + .38)
    R.mb['water'].quad(wa, wb, wc, wd, 0)
    for k in range(int((ps1 - ps0) / 2.2)):                                 # underwater lights
        R.box('warm', ps0 + 1 + k * 2.2, pt - 2.58, FL - .9, .3, .02, .12)
    for k in range(5):                                                      # loungers
        sc = s0 + 3 + k * 4.4
        R.box('teak', sc, -4.2, FL + .25, .7, 2.0, .08)
        R.box('cushion_white', sc, -4.2, FL + .33, .66, 1.9, .08)
        R.box('cushion_white', sc, -3.4, FL + .45, .66, .5, .35)
        plant(R, sc + 2.2, -6.8, FL, 1.8)
    for sc in (s0 + 8, s1 - 8):
        chandelier(R, sc, 0, CEIL_MAIN - .2, r=1.3, tiers=2, drop=3.4)
    partition(R, Wg.L1, FL, CEIL_END, 'white_marble', door_w=3.0, door_h=3.6)
    # --- lift foyer (end block), black/white marble, round table with a floral centrepiece
    s0, s1 = Wg.L1 + .2, Wg.L - .5
    floor_ceiling(R, s0, s1, FL, CEIL_END, 'checker', 'ivory')
    wall_lining(R, s0, s1, FL, CEIL_END - .3, 'white_marble')
    fs = s0 + 17
    R.cyl('walnut', fs, 0, FL, .9, .78, n=32)
    R.cyl('gold', fs, 0, FL + .74, 1.0, .04, n=32)
    blobl(R.mb['flowers'], R.p(fs, 0, FL + 1.5), (.9, .9, .7))
    chandelier(R, fs, 0, CEIL_END - .1, r=1.0, tiers=2, drop=1.6)


def glass_sculpture(mb, c, h, hanging=False):
    n = 7 if not hanging else 3
    col = rnd.random()
    for k in range(n):
        a = k / n * TAU + rnd.random()
        tilt = .25 + rnd.random() * .5
        L = h * (.5 + rnd.random() * .6)
        d = Vector((math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt), -math.cos(tilt) if hanging else math.cos(tilt)))
        base = Vector(c)
        prev = base
        for j in range(1, 7):
            t = j / 6
            p = base + d * (L * t) + Vector((0, 0, (-.12 if hanging else .12) * math.sin(t * 3)))
            r = .08 * (1 - t) + .015
            mb.box_between(prev, p, r * 2, r * 2, k % 3)
            prev = p


def desert_moon(R):
    """West wing: library, master bedroom, bath, dressing room."""
    Wg = R.w
    s0, s1 = 12.0, 38.0
    floor_ceiling(R, s0, s1, FL, CEIL_MAIN - 3.3, 'parquet', 'indigo')
    # floor-to-ceiling shelves on both long walls, with a rolling brass ladder
    for sg in (-1, 1):
        t = sg * (Wg.w / 2 - 1.0)
        R.box('walnut', (s0 + s1) / 2, t, FL, s1 - s0, .5, CEIL_MAIN - 3.3 - FL)
        R.box('books', (s0 + s1) / 2, t - sg * .26, FL + .4, s1 - s0 - .4, .02, CEIL_MAIN - 3.3 - FL - .8)
        R.mb['brass'].box_between(R.p(s0 + 8, t - sg * .9, FL), R.p(s0 + 8, t - sg * .35, CEIL_MAIN - 4.0), .06, .06, 0)
        R.mb['brass'].box_between(R.p(s0 + 8.6, t - sg * .9, FL), R.p(s0 + 8.6, t - sg * .35, CEIL_MAIN - 4.0), .06, .06, 0)
    rug(R, 25, 0, FL, 10, 7, 'rug_c', 'rug_b')
    R.box('walnut', 25, 0, FL + .74, 3.0, 1.4, .06)                          # partners desk
    R.box('walnut', 25, 0, FL, 2.8, 1.2, .74)
    R.box('green_leather', 25, 0, FL + .8, 2.4, .9, .01)
    armchair(R, 25, -1.6, FL, 1, 'green_leather')
    for sc in (18, 32):
        armchair(R, sc, 1.6, FL, -1, 'green_leather')
        armchair(R, sc, -1.6, FL, 1, 'green_leather')
        R.cyl('walnut', sc, 0, FL, .5, .55, n=24)
        floor_lamp(R, sc + 1.4, 2.6, FL)
    R.lathe('brass', 25, 3.2, [(.3, FL), (.05, FL + .1), (.04, FL + 1.1), (0, FL + 1.1)], 12)
    R.mb['brass'].lathe(R.p(25, 3.2, 0), [(.0, FL + 1.1), (.35, FL + 1.3), (.45, FL + 1.55), (.35, FL + 1.8), (0, FL + 1.9)], 16, 0)   # armillary globe
    partition(R, 38.0, FL, CEIL_MAIN - 3.3, 'indigo')
    # --- master bedroom s 38..74 under a vault painted as the night sky, moon disc
    s0, s1 = 38.2, 74.0
    floor_ceiling(R, s0, s1, FL, CEIL_MAIN, 'midnight_carpet', 'indigo', vault=True, vault_mat='starvault')
    wall_lining(R, s0, s1, FL, CEIL_MAIN - 3.3, 'indigo')
    bs = 60.0
    R.box('walnut', bs, -7.9, FL, 5.2, .4, 4.2)                             # headboard wall with gold deco sunburst
    for k in range(13):
        a = math.pi * k / 12
        R.mb['gold'].box_between(R.p(bs, -7.66, FL + 2.2), R.p(bs + 2.3 * math.cos(a), -7.66, FL + 2.2 + 1.8 * math.sin(a)), .05, .04, 0)
    R.box('midnight_velvet', bs, -5.4, FL, 3.2, 4.4, .45)                   # bed base
    R.box('linen', bs, -5.3, FL + .45, 3.0, 4.1, .35)                       # mattress
    R.box('linen_throw', bs, -4.2, FL + .8, 3.05, 1.2, .05)
    for k in range(4):
        R.box('cushion_white', bs - 1.1 + k * .73, -7.2, FL + .85, .68, .22, .55)
    for dd in (-2.3, 2.3):
        R.box('black_lacquer', bs + dd, -7.3, FL, .8, .6, .6)
        R.lathe('gold', bs + dd, -7.3, [(.12, FL + .6), (.05, FL + .7), (.04, FL + 1.1), (0, FL + 1.1)], 12)
        R.cyl('warm', bs + dd, -7.3, FL + 1.1, .2, .3, n=12, r_top=.14)
    # canopy: four gilt posts + sheer drapes
    for ds in (-1.6, 1.6):
        for dt in (-7.5, -3.2):
            R.cyl('gold', bs + ds, dt, FL, .05, 3.6, n=8)
    R.box('sheer', bs, -5.35, FL + 3.6, 3.3, 4.4, .03)
    R.cyl('moon', bs, 0, CEIL_MAIN - 1.6, 1.4, .06, n=48)                   # moon disc
    rug(R, bs, -1.0, FL, 7, 5, 'rug_c', 'rug_b')
    sofa(R, bs, 1.8, FL, 2.8, -1, 'midnight_velvet')
    for sc in (44, 50):
        armchair(R, sc, 4.5, FL, -1, 'midnight_velvet')
    R.cyl('black_lacquer', 47, 3.2, FL, .55, .5, n=24)
    partition(R, 74.0, FL, CEIL_MAIN - 3.3, 'indigo')
    # --- master bath s 74..L1: onyx, freestanding tub at the window, twin vanities
    s0, s1 = 74.2, Wg.L1 - .3
    floor_ceiling(R, s0, s1, FL, CEIL_MAIN - 3.3, 'white_marble_floor', 'ivory')
    wall_lining(R, s0, s1, FL, CEIL_MAIN - 3.6, 'onyx_wall')
    tb = (s0 + s1) / 2
    R.lathe('white_marble', tb, 7.0, [(0, FL), (.9, FL), (1.0, FL + .25), (.95, FL + .62), (.85, FL + .62), (.8, FL + .15), (0, FL + .15)], 32)
    R.mb['water'].poly([R.p(tb + .8 * math.cos(a), 7.0 + .8 * math.sin(a), FL + .5) for a in [i / 24 * TAU for i in range(24)]], 0)
    for sc in (tb - 3, tb + 3):
        R.box('onyx', sc, -7.6, FL, 2.2, .6, .88)
        R.box('mirror', sc, -7.95, FL + 1.2, 1.8, .04, 1.6)
        R.cyl('chrome', sc, -7.5, FL + .88, .04, .3, n=8)
    partition(R, Wg.L1, FL, CEIL_END, 'indigo', door_w=2.6, door_h=3.4)
    # --- dressing room (end block): walnut wardrobes, island, mirrors
    s0, s1 = Wg.L1 + .2, Wg.L - .5
    floor_ceiling(R, s0, s1, FL, CEIL_END, 'parquet', 'ivory')
    for sg in (-1, 1):
        R.box('walnut', (s0 + s1) / 2, sg * (Wg.w / 2 - 1.1), FL, s1 - s0 - 1, .6, 3.6)
        for k in range(int((s1 - s0 - 1) / 1.2)):
            R.box('brass', s0 + 1.1 + k * 1.2, sg * (Wg.w / 2 - 1.42), FL + 1.2, .03, .03, .9)
    R.box('walnut', (s0 + s1) / 2, 0, FL, 6, 1.4, .95)
    R.box('glass_shelf', (s0 + s1) / 2, 0, FL + .95, 6.1, 1.5, .02)


def rotunda(M, X, mbs):
    """Core atrium: ring of marble columns, helical stair up to the terrace, open to the lantern."""
    c = Vector(S.CORE)
    R0 = S.CORE_R - .6
    mb = mbs
    mb['white_marble_floor'].poly([(c.x + R0 * math.cos(a), c.y + R0 * math.sin(a), FL) for a in [i / 64 * TAU for i in range(64)]], 0)
    # compass-rose inlay
    for k in range(16):
        a = k / 16 * TAU
        r = 6.5 if k % 2 == 0 else 4.0
        mb['gold'].poly([(c.x, c.y, FL + .005), (c.x + .6 * math.cos(a - .2), c.y + .6 * math.sin(a - .2), FL + .005),
                         (c.x + r * math.cos(a), c.y + r * math.sin(a), FL + .005),
                         (c.x + .6 * math.cos(a + .2), c.y + .6 * math.sin(a + .2), FL + .005)], 0)
    for k in range(12):
        a = k / 12 * TAU + TAU / 24
        x, y = c.x + (R0 - .9) * math.cos(a), c.y + (R0 - .9) * math.sin(a)
        mb['white_marble'].cylinder((x, y, FL), .42, 12.5, n=24, m=0, r_top=.38)
        mb['gold'].cylinder((x, y, FL + 12.5), .4, .6, n=16, m=0, r_top=.6)
    sweep_profile(mb['gold'], circle_pts((c.x, c.y), R0 - .9, 64), FL + 13.1, [(-.7, 0), (.7, 0), (.7, .6), (-.7, .6)], 0)
    # helical stair: 22.6 m rise to the terrace, r 1.2..4.2, 3.5 turns, treads 0.19 m
    rise = TERRACE - FL
    n = int(rise / .19)
    turns = 3.5
    for i in range(n):
        a0 = i / n * turns * TAU
        a1 = (i + 1) / n * turns * TAU
        z = FL + rise * i / n
        pts = [(c.x + r * math.cos(a), c.y + r * math.sin(a), z + .19) for r, a in ((1.2, a0), (4.2, a0), (4.2, a1), (1.2, a1))]
        mb['white_marble'].poly(pts, 0)
        mb['white_marble'].poly([(p[0], p[1], p[2] - .06) for p in reversed(pts)], 0)
        mb['white_marble'].quad(pts[1], pts[2], (pts[2][0], pts[2][1], z + .13), (pts[1][0], pts[1][1], z + .13), 0)
        if i % 2 == 0:
            x, y = c.x + 4.1 * math.cos(a0), c.y + 4.1 * math.sin(a0)
            mb['brass'].cylinder((x, y, z + .19), .018, 1.0, n=6, m=0)
    rail = [(c.x + 4.1 * math.cos(i / n * turns * TAU), c.y + 4.1 * math.sin(i / n * turns * TAU), FL + rise * i / n + 1.2) for i in range(n + 1)]
    for p, q in zip(rail, rail[1:]):
        mb['brass'].box_between(p, q, .07, .07, 0)
    mb['white_marble'].cylinder((c.x, c.y, FL), 1.2, rise + .2, n=32, m=0)
    # crystal chandelier dropping through the atrium from the lantern
    for k in range(18):
        zz = FL + 6 + k * .9
        rr = 2.8 - abs(k - 9) * .2
        for j in range(18):
            a = j / 18 * TAU + k * .3
            mb['crystal'].cylinder((c.x + rr * math.cos(a), c.y + rr * math.sin(a), zz), .03, .4, n=6, m=0, r_top=.005)


def terrace(M, X, mbs):
    """Deck ring around the drum above the hip ridges: teak, stone balustrade + glass, spa, fire pit, loungers."""
    c = Vector(S.CORE)
    r_in, r_out = 9.5, 24.0
    deck = mbs['teak']
    n = 96
    for i in range(n):
        a0, a1 = i / n * TAU, (i + 1) / n * TAU
        deck.quad((c.x + r_in * math.cos(a0), c.y + r_in * math.sin(a0), TERRACE), (c.x + r_out * math.cos(a0), c.y + r_out * math.sin(a0), TERRACE),
                  (c.x + r_out * math.cos(a1), c.y + r_out * math.sin(a1), TERRACE), (c.x + r_in * math.cos(a1), c.y + r_in * math.sin(a1), TERRACE), 0)
    mbs['stone'].lathe((c.x, c.y, 0), [(r_out + .3, TERRACE - 1.4), (r_out + .3, TERRACE - .03), (r_in, TERRACE - .03), (r_in, TERRACE - .3)], 96, 0)
    balustrade(mbs['stone'], circle_pts((c.x, c.y), r_out - .1, 120), TERRACE, 0, h=1.1, spacing=.3, closed=True)
    ring = circle_pts((c.x, c.y), r_out - .45, 120)
    for p, q in zip(ring, ring[1:] + ring[:1]):                                                   # glass wind screen
        mbs['glass_rail'].quad((p[0], p[1], TERRACE + 1.1), (q[0], q[1], TERRACE + 1.1), (q[0], q[1], TERRACE + 1.9), (p[0], p[1], TERRACE + 1.9), 0)
    # spa (facing the Strip / fountains, east)
    sx, sy = c.x + 16.5, c.y
    mbs['stone'].lathe((sx, sy, 0), [(2.6, TERRACE), (2.6, TERRACE + .55), (2.3, TERRACE + .55), (2.3, TERRACE + .1), (0, TERRACE + .1)], 48, 0)
    mbs['water'].poly([(sx + 2.3 * math.cos(a), sy + 2.3 * math.sin(a), TERRACE + .45) for a in [i / 48 * TAU for i in range(48)]], 0)
    # fire pit + curved sofas (west, sunset side)
    fx, fy = c.x - 16.5, c.y
    mbs['stone'].cylinder((fx, fy, TERRACE), 1.1, .45, n=32, m=0)
    mbs['fire'].cylinder((fx, fy, TERRACE + .45), .8, .05, n=24, m=0)
    for k in range(10):
        a = math.pi * .2 + k / 9 * math.pi * .6 + math.pi
        for rr in (3.2,):
            mbs['cushion_white'].box((fx + rr * math.cos(a + math.pi), fy + rr * math.sin(a + math.pi), TERRACE + .22), (1.0, .9, .44), 0, rot=a)
    # loungers + umbrellas north and south, planters with cypress between
    for ang in (math.pi / 2, -math.pi / 2, math.pi / 4, -math.pi / 4, 3 * math.pi / 4, -3 * math.pi / 4):
        for k in (-1, 1):
            a = ang + k * .09
            x, y = c.x + 17 * math.cos(a), c.y + 17 * math.sin(a)
            mbs['teak'].box((x, y, TERRACE + .3), (2.0, .75, .1), 0, rot=a)
            mbs['cushion_white'].box((x, y, TERRACE + .38), (1.9, .7, .08), 0, rot=a)
        x, y = c.x + 21.5 * math.cos(ang), c.y + 21.5 * math.sin(ang)
        mbs['stone'].cylinder((x, y, TERRACE), .7, .8, n=16, m=0)
        blobl(mbs['plant'], (x, y, TERRACE + 3.0), (.55, .55, 2.4))
    # wall lanterns on the drum
    for k in range(12):
        a = k / 12 * TAU
        mbs['warm'].box((c.x + 9.55 * math.cos(a), c.y + 9.55 * math.sin(a), TERRACE + 2.4), (.25, .25, .45), 0, rot=a)


def lift(M, X, mbs, coll):
    """Private lift: shaft 0..107 m, cab + four landing door leaves as separate (animated) objects."""
    x, y = LIFT
    sh = mbs['shaft']
    w = 3.0
    top = FL + 4
    for (ax, ay), (bx, by) in (((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
        A = (x + ax * w / 2, y + ay * w / 2)
        B = (x + bx * w / 2, y + by * w / 2)
        sh.quad((A[0], A[1], 0), (B[0], B[1], 0), (B[0], B[1], top), (A[0], A[1], top), 0)
    # south face with door openings (1.9 x 2.8 m) at the lobby and at level 36
    ys = y - w / 2
    dl, dr = x - .95, x + .95
    sh.quad((x - w / 2, ys, 0), (dl, ys, 0), (dl, ys, top), (x - w / 2, ys, top), 0)
    sh.quad((dr, ys, 0), (x + w / 2, ys, 0), (x + w / 2, ys, top), (dr, ys, top), 0)
    for z0, z1 in ((2.8, FL), (FL + 2.8, top)):
        sh.quad((dl, ys, z0), (dr, ys, z0), (dr, ys, z1), (dl, ys, z1), 0)
    out = []
    # cab: walnut panels, bronze mirror, brass rail, crystal ceiling, floor indicator
    cab = MB('DYN_lift_cab', [X['walnut'], X['mirror'], X['brass'], X['crystal'], X['checker'], X['warm_light']])
    cw, cd, chh = 2.4, 2.4, 3.0
    cab.quad((x - cw / 2, y - cd / 2, 0), (x + cw / 2, y - cd / 2, 0), (x + cw / 2, y + cd / 2, 0), (x - cw / 2, y + cd / 2, 0), 4,
             uv=[(0, 0), (.6, 0), (.6, .6), (0, .6)])
    for (ax, ay), (bx, by), m in ((((1, -1), (1, 1), 0)), (((1, 1), (-1, 1), 1)), (((-1, 1), (-1, -1), 0))):
        A = (x + ax * cw / 2, y + ay * cd / 2)
        B = (x + bx * cw / 2, y + by * cd / 2)
        cab.quad((B[0], B[1], 0), (A[0], A[1], 0), (A[0], A[1], chh), (B[0], B[1], chh), m)
    cab.quad((x - cw / 2, y - cd / 2, chh), (x - cw / 2, y + cd / 2, chh), (x + cw / 2, y + cd / 2, chh), (x + cw / 2, y - cd / 2, chh), 3)
    for side in (-1, 1):
        cab.box_between((x + side * (cw / 2 - .06), y - cd / 2 + .2, .95), (x + side * (cw / 2 - .06), y + cd / 2 - .2, .95), .05, .05, 2)
    cab.box((x + .95, y - cd / 2 + .02, 1.35), (.18, .03, .5), 5)
    o = cab.build(coll, props={'nobake': 1, 'dyn': 'lift_cab'})
    out.append(o)
    # landing door leaves (brass with gilt inlay), ground + level 36
    for lvl, z in (('g', 0.0), ('p', FL)):
        for side in (-1, 1):
            d = MB(f'DYN_lift_door_{lvl}_{"L" if side < 0 else "R"}', [X['brass']])
            d.box((x + side * .45, y - w / 2 - .06, z + 1.4), (.9, .06, 2.8), 0)
            out.append(d.build(coll, props={'nobake': 1, 'dyn': 'lift_door', 'side': side, 'level': lvl}))
        fr = mbs['gold']
        fr.box((x, y - w / 2 - .1, z + 2.95), (2.3, .12, .3), 0)
        fr.box((x - 1.0, y - w / 2 - .1, z + 1.4), (.2, .12, 2.9), 0)
        fr.box((x + 1.0, y - w / 2 - .1, z + 1.4), (.2, .12, 2.9), 0)
        mbs['warm'].box((x, y - w / 2 - .17, z + 3.3), (.6, .02, .15), 0)      # floor indicator strip
    return out


def build(coll, M):
    X = materials(M)
    extra = {'cushion': X['cushion_white'], 'rug_a': None, 'rug_b': None, 'rug_c': None}
    P(X, 'rug_a', (.55, .38, .20), .9, sheen=.8)
    P(X, 'rug_b', (.25, .07, .05), .9, sheen=.8)
    P(X, 'rug_c', (.05, .07, .20), .9, sheen=.8)
    P(X, 'drape', (.60, .42, .20), .8, sheen=1.)
    P(X, 'burgundy_chair', (.30, .04, .05), .7, sheen=.8)
    P(X, 'bottle', (.12, .25, .10), .05)
    P(X, 'glass_shelf', (.8, .9, .9), .02)
    P(X, 'green_leather', (.04, .12, .06), .45, coat=.3)
    P(X, 'midnight_carpet', (.03, .03, .09), .95, sheen=.6)
    P(X, 'linen_throw', (.55, .45, .25), .8, sheen=.6)
    P(X, 'sheer', (.92, .92, .95), .9)
    P(X, 'moon', (1, 1, 1), .5, emit=(.9, .93, 1.0), strength=6.)
    P(X, 'starvault', (.02, .025, .08), .7)
    P(X, 'white_marble_floor', (.88, .87, .84), .08, coat=.6)
    P(X, 'travertine_wall', (.78, .70, .58), .6)
    P(X, 'onyx_wall', (.80, .58, .34), .15, coat=.5, emit=(1.0, .7, .4), strength=.4)
    P(X, 'pool_tile', (.10, .35, .45), .3)
    P(X, 'shaft', (.35, .33, .30), .8)
    P(X, 'glass_rail', (.85, .95, .95), .02)
    X['cushion'] = X['cushion_white']
    X['warm'] = X['warm_light']
    X['flowers'] = M['flower_pink']
    X['water'] = M['pool_water']
    X['glassart'] = None
    keys = list(X.keys())
    mbs = {}
    for k in keys:
        if k == 'glassart':
            continue
        if X[k] is None:
            continue
        mbs[k] = MB(f'ph_{k}', [X[k]])
    mbs['glassart'] = MB('GLASS_ph_art', [M['flower_red'], M['flower_yellow'], X['rug_c']])
    for k in ('rug_a', 'rug_b', 'rug_c', 'cushion'):
        mbs.setdefault(k, MB(f'ph_{k}', [X[k]]))
    # every wing uses its themed zones
    lake_como(Room(WINGS['N'], mbs))
    fiori(Room(WINGS['S'], mbs))
    desert_moon(Room(WINGS['W'], mbs))
    rotunda(M, X, mbs)
    terrace(M, X, mbs)
    dyn = lift(M, X, mbs, coll)
    # slab under everything (the main Y + end blocks), just below the room floors
    main, shared, ends, roofs = tower.plan()
    from grounds import curve_fill
    slabs = [curve_fill('ph_slab_main', ccw([(p.x, p.y) for p in main]), [], FL - .40, X['ivory'], coll)]
    for k, q in ends.items():
        slabs.append(curve_fill(f'ph_slab_{k}', ccw([(p.x, p.y) for p in q]), [], FL - .40, X['ivory'], coll))
    out = slabs + dyn
    emit_keys = {'crystal', 'warm', 'warm_light', 'fire', 'moon', 'onyx', 'onyx_wall'}
    for k, mb in mbs.items():
        props = {}
        if k in ('water',):
            props = {'nobake': 1, 'mat': 'water'}
        elif k in ('glass_rail', 'glass_shelf', 'glassart', 'mirror', 'chrome'):
            props = {'nobake': 1, 'mat': k}
        elif k in emit_keys:
            props = {'emit': tuple(mb.mats[0].node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value[:3]),
                     'strength': float(mb.mats[0].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value), 'dyn': 'always'}
        o = mb.build(coll, smooth=k in ('cushion_white', 'cushion', 'flowers', 'plant', 'glassart', 'cream_sofa'), sharp=50, props=props)
        if o:
            out.append(o)
    return out
