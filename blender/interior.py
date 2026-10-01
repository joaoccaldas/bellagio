"""Interiors: main lobby with Fiori di Como (Chihuly), passage, Conservatory & Botanical Gardens."""
import math, os, random
import bpy
from mathutils import Vector, noise
import survey as S
from geo import MB, Straight, facade, sweep_profile, balustrade, v2, circle_pts, wall_rect

TAU = math.tau
DATA = os.path.join(os.path.dirname(__file__), '..', 'data')
rnd = random.Random(21)
PIECES = []          # (x, y, z, R, tilt_a, tilt_b, r, g, b, horn) exported for the browser


def img_mat(name, file, rough=.25, coat=.0):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = coat
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(os.path.join(DATA, file), check_existing=True)
    uv = nt.nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'UVMap'
    nt.links.new(uv.outputs['UV'], t.inputs['Vector'])
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    return m


def floor(mb, x0, y0, x1, y1, z, m):
    mb.quad((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z), m, uv=[(0, 0), (1, 0), (1, 1), (0, 1)])


def room(mb, frame, x0, y0, x1, y1, zones_by_side, bay, M, openings=None):
    """Four inward-facing walls (CW order => the geo 'outward' normal points into the room).
    openings: {side: (lo, hi, z_top)} spans (along y or x) left fully open for passages."""
    cw = [(x0, y0), (x0, y1), (x1, y1), (x1, y0)]
    names = ['W', 'N', 'E', 'S']
    openings = openings or {}
    for i in range(4):
        a, b = v2(cw[i]), v2(cw[(i + 1) % 4])
        path = Straight(a, b)
        op = openings.get(names[i])

        def skip(path, s, z0, z1, op=op):
            if not op:
                return False
            p, _ = path.at(s)
            u = p.y if abs(path.t.y) > .5 else p.x
            return op[0] <= u <= op[1] and z1 <= op[2] + .01
        facade(mb, None, frame, path, zones_by_side[names[i]], bay, M, skip=skip)
        if op:
            # lintel over the opening
            lo, hi, zt = op
            pa = a + path.t * 0
            if abs(path.t.y) > .5:
                mb.quad((a.x, lo, zt), (a.x, hi, zt), (a.x, hi, zt + .01), (a.x, lo, zt + .01), 0)


def column(mb, trim, gold, x, y, z0, h, r=.45):
    trim.box((x, y, z0 + .35), (r * 2.6, r * 2.6, .7), 0)                    # plinth
    trim.cylinder((x, y, z0 + .7), r * 1.18, .25, n=24, m=0, r_top=r * 1.05)   # torus-ish base
    # fluted shaft: 20 flutes as a star-ish cross-section
    n = 40
    prof = []
    for i in range(n):
        a = i / n * TAU
        rr = r * (1 - .04 * (i % 2))
        prof.append(a)
    zs, ze = z0 + .95, z0 + h - 1.0
    ring0 = [(x + r * (1 - .045 * (i % 2)) * math.cos(a), y + r * (1 - .045 * (i % 2)) * math.sin(a), zs) for i, a in enumerate(prof)]
    ring1 = [(x + r * .9 * (1 - .045 * (i % 2)) * math.cos(a), y + r * .9 * (1 - .045 * (i % 2)) * math.sin(a), ze) for i, a in enumerate(prof)]
    for i in range(n):
        j = (i + 1) % n
        mb.quad(ring0[i], ring0[j], ring1[j], ring1[i], 0)
    # gilded corinthian-ish capital: flared bell + leaf ring + abacus
    gold.cylinder((x, y, ze), r * .9, .75, n=24, m=0, r_top=r * 1.35)
    for k in range(8):
        a = k / 8 * TAU
        gold.box((x + r * 1.05 * math.cos(a), y + r * 1.05 * math.sin(a), ze + .45), (.22, .12, .5), 0, rot=a)
    trim.box((x, y, ze + .88), (r * 3.0, r * 3.0, .26), 0)


# ------------------------------------------------------------------ Fiori di Como
PALETTE = [((.02, .10, .55), .20), ((.95, .62, .05), .18), ((.95, .30, .02), .12), ((.70, .03, .02), .10),
           ((.10, .50, .08), .12), ((.40, .12, .60), .10), ((.85, .10, .40), .08), ((.85, .88, .85), .05), ((.02, .55, .55), .05)]


def pick_color():
    r = rnd.random()
    for c, w in PALETTE:
        if r < w:
            return c
        r -= w
    return PALETTE[0][0]


def chihuly(coll, M, cx, cy, L, W, z_top):
    """~2,100 hand-blown pieces (published count >2,100) packed under the ceiling recess."""
    verts, faces, cols = [], [], []

    def add_piece(c, R, tilt, col, horn=False):
        base = len(verts)
        n, rings = 18, 4
        ax = Vector((math.sin(tilt[0]) * math.cos(tilt[1]), math.sin(tilt[0]) * math.sin(tilt[1]), -math.cos(tilt[0])))
        u = ax.orthogonal().normalized()
        v = ax.cross(u).normalized()
        if horn:                                   # twisted horn / spire
            L = R * 3.2
            for k in range(rings + 3):
                t = k / (rings + 2)
                rr = R * .35 * (1 - t) + .01
                for j in range(n):
                    a = j / n * TAU + t * 2.5
                    p = Vector(c) + ax * (L * t) + (u * math.cos(a) + v * math.sin(a)) * rr * (1 + .25 * math.sin(a * 3))
                    verts.append(p[:])
            nr = rings + 3
        else:                                      # ruffled "Persian" saucer, rim curling down
            for k in range(rings):
                t = (k + 1) / rings
                rr = R * t
                for j in range(n):
                    a = j / n * TAU
                    ruffle = .18 * R * t ** 2 * math.sin(a * 7 + c[0] * 3)
                    depth = R * .45 * t * t + ruffle
                    p = Vector(c) + (u * math.cos(a) + v * math.sin(a)) * rr + ax * depth
                    verts.append(p[:])
            nr = rings
            ci = len(verts)
            verts.append(c[:] if isinstance(c, tuple) else tuple(c))
            for j in range(n):
                faces.append((ci, base + (j + 1) % n, base + j))
                cols.append(col)
        for k in range(nr - 1):
            for j in range(n):
                a = base + k * n + j
                b = base + k * n + (j + 1) % n
                faces.append((a, b, b + n, a + n))
                cols.append(col)

    count = 0
    target = 2100
    # dense layered packing: a jittered grid per layer, 3 layers
    nx, ny = 72, 32
    for layer in range(4):
        for i in range(nx):
            for j in range(ny):
                if count >= target or rnd.random() > .24:
                    continue
                x = cx - L / 2 + (i + rnd.random()) / nx * L
                y = cy - W / 2 + (j + rnd.random()) / ny * W
                edge = min(x - (cx - L / 2), (cx + L / 2) - x, y - (cy - W / 2), (cy + W / 2) - y)
                z = z_top - .2 - layer * .3 - rnd.random() * .25 - (0.35 if edge < .8 else 0)
                R = .2 + rnd.random() * .3
                tilt = (rnd.uniform(.15, .9), rnd.uniform(0, TAU))
                col = pick_color()
                horn = rnd.random() < .09
                add_piece((x, y, z), R, tilt, col, horn=horn)
                PIECES.append([round(x, 3), round(y, 3), round(z, 3), round(R, 3), round(tilt[0], 3), round(tilt[1], 3), *[round(c, 3) for c in col], int(horn)])
                count += 1
    me = bpy.data.meshes.new('CHIHULY')
    me.from_pydata(verts, [], faces)
    attr = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    li = 0
    for pi, p in enumerate(me.polygons):
        for l in p.loop_indices:
            attr.data[l].color = (*cols[pi], 1)
    me.color_attributes.active_color = attr
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(M['chihuly'])
    o = bpy.data.objects.new('GLASS_chihuly', me)
    coll.objects.link(o)
    o['nobake'] = 1
    o['mat'] = 'chihuly'
    print('chihuly pieces', count)
    return o


# ------------------------------------------------------------------ garden pieces
def flower_bed(mb, curb, x0, y0, x1, y1, m_flowers, rad=1.2, z=0.0):
    """Raised bed: curb + dense mounded flower carpet (vertex-level noise so it reads as blooms)."""
    # curb
    pts = rounded_rect(x0, y0, x1, y1, rad)
    sweep_profile(curb, pts, z, [(0, 0), (.22, 0), (.22, .38), (.05, .45), (0, .45)], 0)
    # carpet grid
    nxs = max(2, int((x1 - x0) / .25))
    nys = max(2, int((y1 - y0) / .25))
    grid = {}
    for i in range(nxs + 1):
        for j in range(nys + 1):
            x = x0 + (x1 - x0) * i / nxs
            y = y0 + (y1 - y0) * j / nys
            d = min(x - x0, x1 - x, y - y0, y1 - y)
            h = .35 + .25 * min(1, d / 1.2) + .12 * noise.noise(Vector((x * 2.7, y * 2.7, 0))) + .06 * noise.noise(Vector((x * 9, y * 9, 1)))
            grid[i, j] = (x, y, z + h)
    for i in range(nxs):
        for j in range(nys):
            cx = (i + .5) / nxs
            mi = m_flowers[0] if len(m_flowers) == 1 else m_flowers[int((noise.noise(Vector((grid[i, j][0] * .35, grid[i, j][1] * .35, 3))) * .5 + .5) * len(m_flowers)) % len(m_flowers)]
            mb.quad(grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1], mi)


def rounded_rect(x0, y0, x1, y1, r, n=5):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -math.pi / 2), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, math.pi / 2), (x0 + r, y0 + r, math.pi)):
        for k in range(n + 1):
            a = a0 + math.pi / 2 * k / n
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def blossom_tree(trunk, crown, x, y, s=1.0):
    pts = [(x, y, 0), (x + .3 * s, y + .1 * s, 1.6 * s), (x - .2 * s, y + .3 * s, 3.2 * s), (x + .2 * s, y, 4.2 * s)]
    for a, b in zip(pts, pts[1:]):
        trunk.box_between(a, b, .45 * s, .45 * s, 0)
    for k in range(9):
        a = k / 9 * TAU
        r = 2.2 * s * (.6 + .4 * rnd.random())
        c = (x + r * math.cos(a), y + r * math.sin(a), (4.4 + rnd.random() * 1.6) * s)
        blob(crown, c, (1.5 * s, 1.5 * s, 1.0 * s), 0)
        trunk.box_between(pts[-1], (c[0], c[1], c[2] - .5 * s), .18 * s, .18 * s, 0)
    blob(crown, (x, y, 5.6 * s), (2.0 * s, 2.0 * s, 1.3 * s), 0)


def blob(mb, c, s, m, n1=10, n2=6):
    seed = Vector((c[0] * 1.3, c[1] * 2.1, c[2]))
    rings = []
    for i in range(n2 + 1):
        th = math.pi * i / n2
        ring = []
        for j in range(n1):
            ph = TAU * j / n1
            d = Vector((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)))
            k = 1 + .3 * noise.noise(d * 2.5 + seed)
            ring.append((c[0] + d.x * s[0] * k, c[1] + d.y * s[1] * k, c[2] + d.z * s[2] * k))
        rings.append(ring)
    for i in range(n2):
        for j in range(n1):
            k2 = (j + 1) % n1
            mb.quad(rings[i][j], rings[i + 1][j], rings[i + 1][k2], rings[i][k2], m)


def fountain(stone, water, x, y):
    stone.lathe((x, y, 0), [(3.6, 0), (3.8, .1), (3.8, .55), (3.5, .7), (3.3, .7), (3.3, .15), (0, .15)], 48, 0)
    stone.lathe((x, y, 0), [(.9, .15), (.6, .6), (.45, 1.6), (.35, 2.0), (1.6, 2.1), (1.8, 2.35), (1.5, 2.45), (.3, 2.35),
                            (.25, 3.2), (.8, 3.3), (.9, 3.45), (.2, 3.5), (.12, 4.1), (.3, 4.3), (0, 4.45)], 32, 0)
    water.poly([(x + 3.3 * math.cos(a), y + 3.3 * math.sin(a), .5) for a in [i / 48 * TAU for i in range(48)]], 0)
    water.poly([(x + 1.55 * math.cos(a), y + 1.55 * math.sin(a), 2.3) for a in [i / 32 * TAU for i in range(32)]], 0)


# ------------------------------------------------------------------ build
def build(coll, M):
    M['floor_lobby'] = img_mat('floor_lobby', 'floor_lobby.jpg', .12, .25)
    M['floor_cons'] = img_mat('floor_cons', 'floor_conservatory.jpg', .15, .2)
    wall = MB('int_wall', [M['int_plaster'], M['trim'], M['marble_dark'], M['wood'], M['int_ceiling']])
    trim = MB('int_trim', [M['trim']])
    gold = MB('int_gold', [M['gold']])
    frame = MB('int_frame', [M['verdigris']])
    flo = MB('int_floor', [M['floor_lobby'], M['floor_cons'], M['marble_dark']])
    glass = MB('GLASS_interior', [M['skylight']], uv2=True)
    light = MB('EMIT_chihuly_box', [M['lightbox']])
    downl = MB('EMIT_int_lamps', [M['lamp']])
    garden = MB('int_garden', [M['flower_pink'], M['flower_white'], M['flower_yellow'], M['flower_red'], M['flower_purple'],
                               M['leaf'], M['blossom'], M['bark'], M['topiary']])
    curb = MB('int_curb', [M['trim']])
    stone = MB('int_stone', [M['trim']])
    iwater = MB('WATER_int', [M['pool_water']])

    # ---------------- lobby
    x0, y0, x1, y1, H = S.LOBBY_BOX
    floor(flo, x0, y0, x1, y1, .10, 0)
    ARCH = dict(w=3.4, b=0, t=6.2, arch=True, depth=.6, transom=[], mull=.1, back=2)
    NICHE = dict(w=2.4, b=.0, t=5.4, arch=True, depth=.9, transom=[], mull=.05, back=2)
    DOOR = dict(w=4.0, b=0, t=7.0, arch=True, depth=.6, transom=[3.0], mull=.12)
    lower = lambda spec: [(0, 7.6, spec), (7.6, H, 1)]
    Mw = dict(wall=0, reveal=1, sill=1)
    room(wall, frame, x0, y0, x1, y1, {'W': lower(ARCH), 'N': lower(ARCH), 'E': lower(DOOR), 'S': lower(NICHE)}, 5.5, Mw,
         openings={'W': (S.PASSAGE[1], S.PASSAGE[3], 7.6)})
    # glazed entrance doors on the east wall (to the porte-cochere) + west opening to the passage
    for k in range(int((y1 - y0) / 5.5)):
        yc = y0 + 5.5 * (k + .5)
        glass.poly([(x1 + .5, yc - 2.0, 0), (x1 + .5, yc + 2.0, 0), (x1 + .5, yc + 2.0, 5.0), (x1 + .5, yc, 7.0), (x1 + .5, yc - 2.0, 5.0)], 0,
                   uv=[(0, 0), (1, 0), (1, .7), (.5, 1), (0, .7)], uv2=[(.3, .02)] * 5)
    sweep_profile(trim, [(x0, y0), (x0, y1), (x1, y1), (x1, y0)], 7.6, [(0, 0), (.1, .1), (.15, .5), (.45, .8), (.6, 1.2), (0, 1.3)], 0)
    # coffered ceiling with the Chihuly recess
    cx, cy, L, W = S.CHIHULY
    rx0, rx1, ry0, ry1 = cx - L / 2 - .4, cx + L / 2 + .4, cy - W / 2 - .4, cy + W / 2 + .4
    for (a0, b0, a1, b1) in ((x0, y0, x1, ry0), (x0, ry1, x1, y1), (x0, ry0, rx0, ry1), (rx1, ry0, x1, ry1)):
        wall.quad((a0, b0, H), (a0, b1, H), (a1, b1, H), (a1, b0, H), 4)
        # coffer grid
        gx = a0
        while gx < a1 - .1:
            trim.box_between((gx, b0, H - .25), (gx, b1, H - .25), .3, .5, 0)
            gx += 2.4
        gy = b0
        while gy < b1 - .1:
            trim.box_between((a0, gy, H - .25), (a1, gy, H - .25), .3, .5, 0)
            gy += 2.4
    zr = H + 2.3
    for (a, b) in (((rx0, ry0), (rx1, ry0)), ((rx1, ry0), (rx1, ry1)), ((rx1, ry1), (rx0, ry1)), ((rx0, ry1), (rx0, ry0))):
        wall.quad((a[0], a[1], H), (b[0], b[1], H), (b[0], b[1], zr), (a[0], a[1], zr), 4)
    sweep_profile(gold, [(rx0, ry0), (rx0, ry1), (rx1, ry1), (rx1, ry0)], H - .35, [(0, 0), (.25, 0), (.3, .2), (.18, .35), (0, .35)], 0)
    light.quad((rx0, ry0, zr), (rx0, ry1, zr), (rx1, ry1, zr), (rx1, ry0, zr), 0)
    chi = chihuly(coll, M, cx, cy, L, W, zr - .1)
    # colonnade along the long walls
    for x in [x0 + 3.0 + 5.5 * k for k in range(8) if x0 + 3.0 + 5.5 * k < x1 - 1]:
        for y in (y0 + 1.6, y1 - 1.6):
            column(wall, trim, gold, x, y, 0, 7.6)
    # registration desk (south wall): marble top, wood panelled front, back wall in dark marble
    dx0, dx1, dy = x0 + 8, x1 - 8, y0 + 3.0
    wall.box(((dx0 + dx1) / 2, dy, .55), (dx1 - dx0, .9, 1.1), 3)
    trim.box(((dx0 + dx1) / 2, dy, 1.14), (dx1 - dx0 + .1, 1.0, .08), 0)
    for k in range(int((dx1 - dx0) / 1.6)):
        gold.box((dx0 + .8 + k * 1.6, dy + .46, .55), (1.3, .02, .75), 0)
    wall.box(((dx0 + dx1) / 2, y0 + .15, 3.5), (dx1 - dx0 + 2, .1, 7.0), 2)
    # floral urns (the lobby is known for its arrangements)
    for (ux, uy) in ((cx - 12, cy), (cx + 12, cy), (cx, cy + 7.5)):
        stone.lathe((ux, uy, 0), [(.9, 0), (1.0, .2), (.6, .5), (.5, 1.0), (1.1, 1.3), (1.2, 1.5), (0, 1.5)], 24, 0)
        blob(garden, (ux, uy, 2.2), (1.3, 1.3, .9), 0)
        blob(garden, (ux + .4, uy, 2.6), (.8, .8, .7), 6)
        blob(garden, (ux - .3, uy + .2, 2.0), (1.0, 1.0, .5), 5)
    for k in range(10):
        downl.cylinder((x0 + 4 + k * 4.0, y0 + 5.5, H - .05), .18, .05, n=12, m=0)
        downl.cylinder((x0 + 4 + k * 4.0, y1 - 5.5, H - .05), .18, .05, n=12, m=0)

    # ---------------- passage (arched gallery)
    px0, py0, px1, py1, ph = S.PASSAGE
    floor(flo, px0, py0, px1, py1, .10, 2)
    for x in [px0 + 1.5 + 3.0 * k for k in range(7)]:
        for y in (py0 + .8, py1 - .8):
            column(wall, trim, gold, x, y, 0, ph - .5, r=.32)
    wall.quad((px0, py0, 0), (px1, py0, 0), (px1, py0, ph), (px0, py0, ph), 0)
    # north wall, with the private lift's doorway (lift centre x = 16.2)
    lx0, lx1 = 16.2 - .95, 16.2 + .95
    wall.quad((px1, py1, 0), (lx1, py1, 0), (lx1, py1, ph), (px1, py1, ph), 0)
    wall.quad((lx0, py1, 0), (px0, py1, 0), (px0, py1, ph), (lx0, py1, ph), 0)
    wall.quad((lx1, py1, 2.8), (lx0, py1, 2.8), (lx0, py1, ph), (lx1, py1, ph), 0)
    # barrel vault ceiling
    k = 12
    for i in range(k):
        a0, a1 = math.pi * i / k, math.pi * (i + 1) / k
        ya0, ya1 = (py0 + py1) / 2 - (py1 - py0) / 2 * math.cos(a0), (py0 + py1) / 2 - (py1 - py0) / 2 * math.cos(a1)
        za0, za1 = ph + 2.0 * math.sin(a0), ph + 2.0 * math.sin(a1)
        wall.quad((px0, ya0, za0), (px1, ya0, za0), (px1, ya1, za1), (px0, ya1, za1), 4)
    for x in [px0 + 1.5 + 3.0 * k2 for k2 in range(7)]:
        for i in range(k):
            a0, a1 = math.pi * i / k, math.pi * (i + 1) / k
            gold.box_between((x, (py0 + py1) / 2 - (py1 - py0) / 2 * math.cos(a0), ph + 2.0 * math.sin(a0) - .1),
                             (x, (py0 + py1) / 2 - (py1 - py0) / 2 * math.cos(a1), ph + 2.0 * math.sin(a1) - .1), .25, .15, 0)

    # ---------------- conservatory
    cx0, cy0, cx1, cy1, CH = S.CONS_BOX
    floor(flo, cx0, cy0, cx1, cy1, .10, 1)
    WALL_H = 10.0
    ARC = dict(w=4.0, b=0, t=7.4, arch=True, depth=.8, transom=[4.6], mull=.1, back=0)
    zones = [(0, 8.4, ARC), (8.4, WALL_H, 1)]
    room(wall, frame, cx0, cy0, cx1, cy1, {'W': zones, 'N': zones, 'E': zones, 'S': zones}, 5.2, Mw,
         openings={'E': (S.PASSAGE[1], S.PASSAGE[3], 8.4)})
    # fanlight grilles (radial bars) in every arch head: already framed; add bronze grille ribs
    sweep_profile(trim, [(cx0, cy0), (cx0, cy1), (cx1, cy1), (cx1, cy0)], WALL_H - .2, [(0, 0), (.2, .1), (.3, .5), (.8, .8), (1.0, 1.2), (0, 1.3)], 0)
    sweep_profile(gold, [(cx0, cy0), (cx0, cy1), (cx1, cy1), (cx1, cy0)], WALL_H - .6, [(0, 0), (.32, 0), (.32, .12), (0, .12)], 0)
    # nave (along x) on two colonnades of green steel columns
    nave0, nave1 = -108.0, -92.0
    spring = 12.3
    for x in [cx0 + 1.5 + 3.0 * k for k in range(14)]:
        for y in (nave0, nave1):
            frame.cylinder((x, y, 0), .38, .5, n=12, m=0)
            frame.cylinder((x, y, .5), .22, spring - .5, n=12, m=0)
            gold.cylinder((x, y, spring - .6), .24, .6, n=12, m=0, r_top=.45)
    # side aisle glass roofs (pitched) + nave barrel vault with lattice trusses
    zs = WALL_H + 1.1
    for (ya, yb) in ((cy0, nave0), (cy1, nave1)):
        glass.poly([(cx0, ya, zs), (cx1, ya, zs), (cx1, yb, spring), (cx0, yb, spring)], 0,
                   uv=[(0, 0), (1, 0), (1, 1), (0, 1)], uv2=[(.5, .9)] * 4)
        for x in [cx0 + 1.5 + 3.0 * k for k in range(14)]:
            frame.box_between((x, ya, zs), (x, yb, spring), .18, .3, 0)
        for t in (.33, .66):
            frame.box_between((cx0, ya + (yb - ya) * t, zs + (spring - zs) * t), (cx1, ya + (yb - ya) * t, zs + (spring - zs) * t), .1, .12, 0)
    rise = CH + 2.5 - spring
    k = 16
    half = (nave1 - nave0) / 2
    ym = (nave0 + nave1) / 2

    def arc(i, inset=0.0):
        a = math.pi * i / k
        return ym - (half - inset) * math.cos(a), spring + (rise - inset) * math.sin(a)
    for i in range(k):
        (ya, za), (yb, zb) = arc(i), arc(i + 1)
        glass.poly([(cx0, ya, za), (cx0, yb, zb), (cx1, yb, zb), (cx1, ya, za)], 0, uv=[(0, 0), (1, 0), (1, 1), (0, 1)], uv2=[(.5, .9)] * 4)
    for x in [cx0 + 1.5 + 3.0 * k2 for k2 in range(14)]:
        for i in range(k):
            (ya, za), (yb, zb) = arc(i), arc(i + 1)
            (yi, zi), (yj, zj) = arc(i, .9), arc(i + 1, .9)
            frame.box_between((x, ya, za - .05), (x, yb, zb - .05), .2, .2, 0)
            frame.box_between((x, yi, zi), (x, yj, zj), .16, .16, 0)
            frame.box_between((x, ya, za - .05), (x, yj, zj), .07, .07, 0)
            frame.box_between((x, yb, zb - .05), (x, yi, zi), .07, .07, 0)
    for i in range(0, k + 1, 2):
        ya, za = arc(i)
        frame.box_between((cx0, ya, za - .1), (cx1, ya, za - .1), .12, .16, 0)
    # end lunettes (glazed half-discs) above the end walls
    for x in (cx0, cx1):
        pts = [(x, *arc(i)) for i in range(k + 1)]
        glass.poly([(p[0], p[1], p[2]) for p in pts], 0, uv=[(i / k, 0) for i in range(k + 1)], uv2=[(.5, .9)] * (k + 1))
        for i in range(k + 1):
            y, z = arc(i)
            frame.box_between((x, y, spring), (x, y, z), .08, .08, 0)
    for x in (cx0, cx1):
        wall.quad((x, cy0, WALL_H), (x, nave0, WALL_H), (x, nave0, spring), (x, cy0, zs), 0)
        wall.quad((x, nave1, WALL_H), (x, cy1, WALL_H), (x, cy1, zs), (x, nave1, spring), 0)
    # garden: formal beds around a central fountain, blossom trees, topiary, pergola, benches
    fx, fy = (cx0 + cx1) / 2, ym
    fountain(stone, iwater, fx, fy)
    F = [0, 1, 2, 3, 4]
    beds = [(cx0 + 2, cy0 + 1.5, cx0 + 14, cy0 + 6), (cx0 + 17, cy0 + 1.5, cx1 - 17, cy0 + 6), (cx1 - 14, cy0 + 1.5, cx1 - 2, cy0 + 6),
            (cx0 + 2, cy1 - 6, cx0 + 14, cy1 - 1.5), (cx0 + 17, cy1 - 6, cx1 - 17, cy1 - 1.5), (cx1 - 14, cy1 - 6, cx1 - 2, cy1 - 1.5),
            (cx0 + 3, nave0 + 2.5, fx - 6, ym - 2.2), (fx + 6, nave0 + 2.5, cx1 - 3, ym - 2.2),
            (cx0 + 3, ym + 2.2, fx - 6, nave1 - 2.5), (fx + 6, ym + 2.2, cx1 - 3, nave1 - 2.5)]
    for i, (a, b, c, d) in enumerate(beds):
        flower_bed(garden, curb, a, b, c, d, [F[i % 5], F[(i + 2) % 5], 5], rad=1.0)
    for (tx, ty) in ((cx0 + 8, nave0 + 4.5), (cx1 - 9, nave0 + 4.5), (cx0 + 8, nave1 - 4.5), (cx1 - 9, nave1 - 4.5), (fx - 9, nave0 + 4.5), (fx + 9, nave1 - 4.5)):
        blossom_tree(garden, garden, tx, ty, 1.0) if False else None
        trunk_mb = garden
        pts = [(tx, ty, .5), (tx + .25, ty + .1, 2.0), (tx - .2, ty + .2, 3.6), (tx + .1, ty, 4.4)]
        for p, q in zip(pts, pts[1:]):
            garden.box_between(p, q, .4, .4, 7)
        # gnarled limbs carrying many small blossom clusters (reads as a cherry tree, not a cloud)
        for kk in range(7):
            a = kk / 7 * TAU + rnd.random() * .4
            L1 = 1.6 + rnd.random() * 1.2
            p1 = (tx + L1 * math.cos(a), ty + L1 * math.sin(a), 4.9 + rnd.random() * .8)
            garden.box_between(pts[-1], p1, .2, .2, 7)
            for kc in range(4):
                b2 = a + rnd.uniform(-.9, .9)
                L2 = .8 + rnd.random() * 1.1
                p2 = (p1[0] + L2 * math.cos(b2), p1[1] + L2 * math.sin(b2), p1[2] + rnd.uniform(-.3, .9))
                garden.box_between(p1, p2, .09, .09, 7)
                blob(garden, p2, (.55 + rnd.random() * .3, .55 + rnd.random() * .3, .4), 6, n1=8, n2=5)
    for k2 in range(8):
        x = cx0 + 4 + k2 * 5.0
        for y in (nave0 + .9, nave1 - .9):
            stone.lathe((x, y, 0), [(.45, 0), (.5, .15), (.35, .3), (.3, .6), (.55, .8), (0, .8)], 16, 0)
            blob(garden, (x, y, 1.6), (.55, .55, .8), 8)
    # pergola (timber) over the west path
    for x in (cx0 + 4, cx0 + 7, cx0 + 10):
        for y in (ym - 1.8, ym + 1.8):
            wall.box((x, y, 1.6), (.3, .3, 3.2), 3)
    for y in (ym - 1.8, ym + 1.8):
        wall.box((cx0 + 7, y, 3.3), (7.0, .25, .3), 3)
    for k2 in range(12):
        wall.box((cx0 + 3.8 + k2 * .56, ym, 3.55), (.14, 4.6, .2), 3)
    # benches
    for (bx, by) in ((fx - 5, ym - 4.5), (fx + 5, ym - 4.5), (fx - 5, ym + 4.5), (fx + 5, ym + 4.5)):
        wall.box((bx, by, .45), (2.0, .55, .08), 3)
        frame.box((bx - .85, by, .22), (.08, .5, .44), 0)
        frame.box((bx + .85, by, .22), (.08, .5, .44), 0)

    out = [wall.build(coll), trim.build(coll, smooth=True, sharp=35), gold.build(coll, smooth=True, sharp=40),
           frame.build(coll), flo.build(coll), glass.build(coll, props={'nobake': 1, 'mat': 'skylight'}),
           light.build(coll, props={'emit': (1.0, .97, .9), 'strength': 12.0, 'dyn': 'always'}),
           downl.build(coll, props={'emit': (1.0, .85, .6), 'strength': 40.0, 'dyn': 'always'}),
           garden.build(coll, smooth=True, sharp=80), curb.build(coll), stone.build(coll, smooth=True, sharp=40),
           iwater.build(coll, props={'nobake': 1, 'mat': 'water'}), chi]
    return [o for o in out if o]
