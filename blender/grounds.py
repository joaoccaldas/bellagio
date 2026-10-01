"""Grounds: terrain (orthophoto albedo), lake basin, Strip promenade, lakeside village, Via Bellagio,
porte-cochere, conservatory roof, pools, podium, trees and context massing."""
import math, json, os, random
import bpy
from mathutils import Vector, noise
import survey as S
from geo import (MB, Straight, facade, sweep_profile, hip_roof, extrude_poly, balustrade, ccw, v2, circle_pts,
                 offset_closed, inside, wall_rect)

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, '..', 'data')
rnd = random.Random(11)


def curve_fill(name, outer, holes, z, mat, coll):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '2D'
    cu.fill_mode = 'BOTH'
    for loop in [outer] + holes:
        sp = cu.splines.new('POLY')
        sp.points.add(len(loop) - 1)
        for p, q in zip(sp.points, loop):
            p.co = (q[0], q[1], 0, 1)
        sp.use_cyclic_u = True
    ob = bpy.data.objects.new(name, cu)
    coll.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    for v in me.vertices:
        v.co.z = z
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


def ortho_uv(o, x0, y0, size):
    """Planar UVs so the orthophoto lands where it was captured."""
    me = o.data
    uv = me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
    for li, lp in enumerate(me.loops):
        co = me.vertices[lp.vertex_index].co
        uv.data[li].uv = ((co.x - x0) / size, (co.y - y0) / size)


def image_mat(name, path, rough=.85, tint=(1, 1, 1)):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(path, check_existing=True)
    t.extension = 'CLIP'
    uv = nt.nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'UVMap'
    nt.links.new(uv.outputs['UV'], t.inputs['Vector'])
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    return m


# ------------------------------------------------------------------ terrain + lake
def terrain(coll, M):
    objs = []
    lake = ccw(S.LAKE)
    # the core orthophoto frame (456 m) -- centre and size in survey metres
    core_x0, core_y0 = S.P(0, 2000)
    core_size = 2000 * S.MPP
    wide_x0 = (400 - 719.2) * .475 - 0          # sat.jpg pixel (0,1600) -> metres (see survey notes)
    wide_px0 = S.P(0, 0)
    # wide frame: sat.jpg covers 760 m; its pixel (719.2, 722.4) is the survey origin
    wx0, wy0 = -719.2 * .475, -(1600 - 722.4) * .475
    gm_core = image_mat('ground_core', os.path.join(DATA, 'ground_core.jpg'))
    gm_wide = image_mat('ground_wide', os.path.join(DATA, 'ground_wide.jpg'))
    sq = [(core_x0, core_y0), (core_x0 + core_size, core_y0), (core_x0 + core_size, core_y0 + core_size), (core_x0, core_y0 + core_size)]
    g = curve_fill('ground_core', sq, [list(reversed(lake))], 0.0, gm_core, coll)
    ortho_uv(g, core_x0, core_y0, core_size)
    objs.append(g)
    wsq = [(wx0, wy0), (wx0 + 760, wy0), (wx0 + 760, wy0 + 760), (wx0, wy0 + 760)]
    gw = curve_fill('ground_wide', wsq, [list(reversed(sq))], -0.02, gm_wide, coll)
    ortho_uv(gw, wx0, wy0, 760)
    objs.append(gw)
    far = [(-3000, -3000), (3000, -3000), (3000, 3000), (-3000, 3000)]
    objs.append(curve_fill('ground_far', far, [list(reversed(wsq))], -0.05, M['desert'], coll))
    # basin
    bed = curve_fill('lake_bed', lake, [], -2.6, M['lakebed'], coll)
    objs.append(bed)
    b = MB('lake_edge', [M['coping'], M['basin']])
    n = len(lake)
    for i in range(n):
        a, c = lake[i], lake[(i + 1) % n]
        b.quad((c[0], c[1], 0), (a[0], a[1], 0), (a[0], a[1], -2.6), (c[0], c[1], -2.6), 1)
    # coping: a stone lip that overhangs the water slightly (inward = negative offset)
    sweep_profile(b, lake, -.35, [(0.0, 0), (-.35, .05), (-.4, .25), (-.35, .45), (.6, .45), (.6, .35)], 0)
    objs.append(b.build(coll, smooth=True, sharp=40))
    w = curve_fill('WATER_lake', lake, [], S.LAKE_LEVEL, M['water'], coll)
    w['nobake'] = 1
    w['mat'] = 'water'
    objs.append(w)
    return objs


def edge_segments(poly, pred):
    """Consecutive runs of polygon edges whose midpoint satisfies pred -> list of polylines."""
    n = len(poly)
    runs, cur = [], []
    for i in range(n):
        a, c = poly[i], poly[(i + 1) % n]
        mid = ((a[0] + c[0]) / 2, (a[1] + c[1]) / 2)
        if pred(mid):
            if not cur:
                cur = [a]
            cur.append(c)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return runs


def promenade(coll, M):
    """Strip-side and south balustrades with the lamp posts (speakers are built into them)."""
    lake = ccw(S.LAKE)
    east_x = min(p[0] for p in lake if p[0] > 240)
    rail = MB('lake_rail', [M['balustrade']])
    posts = MB('lamp_posts', [M['iron']])
    glow = MB('EMIT_lamps', [M['lamp']])
    runs = edge_segments(lake, lambda m: m[0] > 245 or (m[1] < -60 and m[0] > 150))
    lamp_pts = []
    for run in runs:
        pts = offset_closed_open(run, .9)
        balustrade(rail, pts, 0.0, 0, h=1.05, spacing=.34)
        # pedestals every ~14.6 m carry the lamps
        L = sum((v2(b) - v2(a)).length for a, b in zip(pts, pts[1:]))
        k = max(1, int(L / 14.6))
        for j in range(k + 1):
            p = along(pts, L * j / k)
            lamp_pts.append(p)
    for p in lamp_pts:
        x, y = p
        rail.box((x, y, .6), (.7, .7, 1.2), 0)
        posts.cylinder((x, y, 1.2), .16, .5, n=12, m=0, r_top=.1)
        posts.cylinder((x, y, 1.7), .08, 3.2, n=10, m=0, r_top=.06)
        posts.cylinder((x, y, 4.85), .26, .12, n=12, m=0)
        glow.cylinder((x, y, 4.97), .2, .55, n=12, m=0, r_top=.24)
        posts.cylinder((x, y, 5.52), .3, .1, n=12, m=0, r_top=.05)
        posts.cylinder((x, y, 5.62), .03, .3, n=6, m=0)
    return [rail.build(coll), posts.build(coll, smooth=True),
            glow.build(coll, props={'emit': (1.0, .85, .6), 'strength': 30.0, 'dyn': 'night'})]


def offset_closed_open(run, d):
    """Offset an open run of lake-edge points toward the land (right of CCW lake = outward)."""
    out = []
    n = len(run)
    for i in range(n):
        a = v2(run[max(0, i - 1)])
        b = v2(run[min(n - 1, i + 1)])
        t = (b - a).normalized()
        nrm = Vector((t.y, -t.x))
        p = v2(run[i]) + nrm * d
        out.append((p.x, p.y))
    return out


def along(pts, d):
    for a, b in zip(pts, pts[1:]):
        l = (v2(b) - v2(a)).length
        if d <= l or (a, b) == (pts[-2], pts[-1]):
            k = min(1, d / max(l, 1e-6))
            return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
        d -= l
    return pts[-1]


def shoreline_rocks(coll, M):
    """Tan boulders under the village terraces (visible in every lake-level photo)."""
    lake = ccw(S.LAKE)
    rocks = MB('rocks', [M['rock']])
    runs = edge_segments(lake, lambda m: m[0] < 170 and m[1] > -70)
    for run in runs:
        L = sum((v2(b) - v2(a)).length for a, b in zip(run, run[1:]))
        for j in range(int(L / 1.3)):
            x, y = along(run, j * 1.3 + rnd.random() * .8)
            r = .6 + rnd.random() * 1.2
            ox, oy = rnd.uniform(-.6, 1.8), rnd.uniform(-.6, .6)
            rock(rocks, (x + ox, y + oy, S.LAKE_LEVEL - .2 + rnd.random() * .5), r)
    return [rocks.build(coll, smooth=True, sharp=70)]


def rock(mb, c, r):
    n1, n2 = 7, 5
    seed = Vector((rnd.random() * 50, rnd.random() * 50, rnd.random() * 50))
    rings = []
    for i in range(n2 + 1):
        th = math.pi * i / n2
        ring = []
        for j in range(n1):
            ph = TAU * j / n1
            d = Vector((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)))
            k = 1 + .35 * noise.noise(d * 1.6 + seed)
            ring.append((c[0] + d.x * r * k * 1.2, c[1] + d.y * r * k, c[2] + d.z * r * k * .7))
        rings.append(ring)
    for i in range(n2):
        for j in range(n1):
            k2 = (j + 1) % n1
            mb.quad(rings[i][j], rings[i + 1][j], rings[i + 1][k2], rings[i][k2], 0)


TAU = math.tau

# ------------------------------------------------------------------ village
VILLA_WIN = dict(w=1.25, b=1.0, t=3.1, depth=.22, transom=[], mull=.07)
VILLA_ARCH = dict(w=2.7, b=0.0, t=4.3, arch=True, depth=1.1, transom=[], mull=.08)


def villa(parts, rect, h, kind, pal, lake_poly):
    wall, trim, frame, glass, roof, shut, awn = parts
    x0, y0, x1, y1 = rect
    q = ccw(S.PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))
    floors = max(2, int(round((h - 5.0) / 3.8)) + 1)
    zones = [(0, 5.0, None)]
    z = 5.0
    for f in range(1, floors):
        top = min(h - .9, z + 3.8)
        if top - z < 3.0:
            break
        zones.append((z, top, VILLA_WIN))
        z = top
    zones.append((z, h, None))
    for i in range(4):
        a, b = v2(q[i]), v2(q[(i + 1) % 4])
        path = Straight(a, b)
        mid = (a + b) / 2 + path.n * 6
        faces_lake = inside(lake_poly, (mid.x, mid.y)) or kind == 'fan'
        zz = list(zones)
        if faces_lake or rnd.random() < .45:
            zz[0] = (0, 5.0, VILLA_ARCH)
        facade(wall, glass, frame, path, zz, 3.4, dict(wall=pal, reveal=4, sill=4))
        # shutters beside every upper window
        nb = max(1, round(path.L / 3.4))
        w = path.L / nb
        for z0, z1, spec in zz[1:-1]:
            if spec is not VILLA_WIN:
                continue
            for k in range(nb):
                c = (k + .5) * w
                for sgn in (-1, 1):
                    s = c + sgn * (spec['w'] / 2 + .36)
                    p, nn = path.at(s)
                    shut.box((p.x + nn.x * .06, p.y + nn.y * .06, z0 + (spec['b'] + spec['t']) / 2),
                             (.62, .08, spec['t'] - spec['b']), 0, rot=math.atan2(path.t.y, path.t.x))
        # striped awnings over lake-facing arcades
        if faces_lake and rnd.random() < .7:
            col = rnd.choice([0, 1])
            for k in range(nb):
                c = (k + .5) * w
                pa, nn = path.at(c - 1.35)
                pb, _ = path.at(c + 1.35)
                A = (pa.x, pa.y, 4.6)
                B = (pb.x, pb.y, 4.6)
                C = (pb.x + nn.x * 1.8, pb.y + nn.y * 1.8, 3.4)
                D = (pa.x + nn.x * 1.8, pa.y + nn.y * 1.8, 3.4)
                awn.quad(A, B, C, D, col, uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
                awn.quad(D, C, B, A, col, uv=[(0, 1), (1, 1), (1, 0), (0, 0)])
        # terrace balustrade at the eave line on lake side
        if faces_lake:
            pa, nn = path.at(0)
            pb, _ = path.at(path.L)
            balustrade(trim, [(pa.x + nn.x * .5, pa.y + nn.y * .5), (pb.x + nn.x * .5, pb.y + nn.y * .5)], 5.05, 0, h=.95)
    sweep_profile(trim, q, h - .9, [(0, 0), (.15, .1), (.2, .5), (.55, .75), (.75, .9), (0, .9)], 0)
    sweep_profile(trim, q, 4.9, [(0, 0), (.2, .05), (.25, .3), (0, .35)], 0)
    if kind != 'flat':
        rh = hip_roof(roof, q, h, 24, 0, eave=.9)
        if (x1 - x0) * (y1 - y0) > 2600 and rnd.random() < .6:
            cx, cy = S.P((x0 + x1) / 2, (y0 + y1) / 2)
            cupola(parts, (cx, cy), h + rh * .6)
    else:
        balustrade(trim, [p for p in q] + [q[0]], h, 0, h=.9)


def cupola(parts, c, z):
    wall, trim, frame, glass, roof, shut, awn = parts
    r = 2.1
    wall.cylinder((c[0], c[1], z), r, 3.4, n=16, m=2)
    for i in range(8):
        a = i / 8 * TAU
        glass.poly([(c[0] + (r + .02) * math.cos(a + d), c[1] + (r + .02) * math.sin(a + d), z + zz)
                    for d, zz in ((-.18, 1.0), (.18, 1.0), (.18, 2.7), (-.18, 2.7))], 0, uv=[(0, 0), (1, 0), (1, 1), (0, 1)], uv2=[(rnd.random(), .05)] * 4)
    trim.cylinder((c[0], c[1], z + 3.4), r + .3, .35, n=16, m=0)
    roof.dome((c[0], c[1], 0), r + .15, 1.6, n=16, rings=5, m=1, z0=z + 3.75)


def village(coll, M):
    parts = (MB('village_wall', [M['villa_a'], M['villa_b'], M['villa_c'], M['villa_d'], M['trim']]),
             MB('village_trim', [M['trim']]), MB('village_frame', [M['bronze']]),
             MB('GLASS_village', [M['glass']], uv2=True), MB('village_roof', [M['terracotta'], M['lead']]),
             MB('village_shutters', [M['shutter']]), MB('village_awnings', [M['awning_red'], M['awning_blue']]))
    lake = ccw(S.LAKE)
    for x0, y0, x1, y1, h, kind, pal in S.VILLAGE:
        if kind == 'lobbyroof':
            # the terracotta pavilion over the lobby entrance: clerestory walls above the podium + hip roof
            q = ccw(S.PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))
            extrude_poly(parts[0], q, 12.5, h, pal, pal, top=False)
            sweep_profile(parts[1], q, h - .9, [(0, 0), (.15, .1), (.2, .5), (.55, .75), (.75, .9), (0, .9)], 0)
            hip_roof(parts[4], q, h, 24, 0, eave=.9)
            continue
        villa(parts, (x0, y0, x1, y1), h, kind, pal, lake)
    out = []
    for mb in parts:
        props = {'nobake': 1, 'mat': 'glass_village'} if mb.name.startswith('GLASS') else None
        out.append(mb.build(coll, smooth=mb.name in ('village_roof',), props=props))
    return [o for o in out if o]


# ------------------------------------------------------------------ Via Bellagio, domes, porte-cochere, podium
def glass_vault(frame, glass, a, b, w, z, rise, ribs_every=2.2, m_glass=0):
    """Barrel vault of glass on steel ribs from a to b."""
    a, b = v2(a), v2(b)
    t = (b - a)
    L = t.length
    t.normalize()
    n = Vector((-t.y, t.x))
    k = 10
    nr = max(2, int(L / ribs_every))
    prof = [(-w / 2 * math.cos(math.pi * i / k), z + rise * math.sin(math.pi * i / k)) for i in range(k + 1)]
    for r in range(nr + 1):
        s = L * r / nr
        pts = [a + t * s + n * u for u, _ in prof]
        for i in range(k):
            frame.box_between((pts[i].x, pts[i].y, prof[i][1]), (pts[i + 1].x, pts[i + 1].y, prof[i + 1][1]), .12, .2, 0,
                              up=(t.x, t.y, 0))
    for i in range(k):
        (u0, z0), (u1, z1) = prof[i], prof[i + 1]
        A, B = a + n * u0, a + n * u1
        C, D = b + n * u1, b + n * u0
        glass.poly([(A.x, A.y, z0), (D.x, D.y, z0), (C.x, C.y, z1), (B.x, B.y, z1)], m_glass,
                   uv=[(0, 0), (1, 0), (1, 1), (0, 1)], uv2=[(.5, .9)] * 4)


def ribbed_dome(frame, shell, c, r, z, h, n=16, m_shell=0):
    shell.dome((c[0], c[1], 0), r, h, n=48, rings=12, m=m_shell, z0=z)
    for i in range(n):
        a = i / n * TAU
        pts = [(c[0] + r * 1.01 * math.cos(math.pi / 2 * j / 10) * math.cos(a), c[1] + r * 1.01 * math.cos(math.pi / 2 * j / 10) * math.sin(a),
                z + h * math.sin(math.pi / 2 * j / 10)) for j in range(11)]
        for p, q in zip(pts, pts[1:]):
            frame.box_between(p, q, .18, .14, 0, up=(math.cos(a), math.sin(a), 0))


def structures(coll, M):
    wall = MB('podium_wall', [M['stucco'], M['trim'], M['podium_roof'], M['villa_c'], M['context_lit'], M['concrete']])
    trim = MB('podium_trim', [M['trim']])
    frame = MB('steel_frames', [M['verdigris']])
    glass = MB('GLASS_roofs', [M['skylight']], uv2=True)
    shells = MB('dome_shells', [M['dome_white'], M['lead']])
    # casino / lobby podium: walls (the face at the porte-cochere is the lobby's own glazed wall),
    # roof with an opening for the conservatory glass
    pod = ccw(S.PODIUM)
    n = len(pod)
    for i in range(n):
        a, c = pod[i], pod[(i + 1) % n]
        if abs(a[0] - c[0]) < .01 and abs(a[0] - S.LOBBY_BOX[2]) < .5:
            continue
        wall.quad((a[0], a[1], 0), (c[0], c[1], 0), (c[0], c[1], 12.5), (a[0], a[1], 12.5), 0)
    x0, y0, x1, y1, _ = S.CONS_BOX
    hole = [(x0, y0), (x0, y1), (x1, y1), (x1, y0)]
    top = curve_fill('podium_roof', pod, [hole], 12.5, M['podium_roof'], coll)
    sweep_profile(trim, pod, 11.2, [(0, 0), (.2, .1), (.3, .6), (.7, .9), (.9, 1.3), (0, 1.3)], 0)
    balustrade(trim, pod + [pod[0]], 12.5, 0, h=.9, spacing=.5)
    extrude_poly(wall, ccw(S.THEATER), 0, 34, 0, 2)
    sweep_profile(trim, ccw(S.THEATER), 32.6, [(0, 0), (.3, .2), (.4, .9), (.9, 1.2), (1.0, 1.4), (0, 1.4)], 0)
    # parking structure: concrete decks with open bands
    park = ccw(S.PARKING)
    for lvl in range(6):
        z = lvl * 3.1
        extrude_poly(wall, offset_closed(park, 0.0), z, z + .9, 5, 5)
    extrude_poly(wall, offset_closed(park, -1.5), 0, 18.6, 5, 5)
    # Via Bellagio: glass barrel vaults between the four domes (north arcade to the Strip)
    d = S.VIA_DOMES
    for a, b in zip(d, d[1:]):
        wall.box(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 5.0), ((v2(b) - v2(a)).length, 13.0, 10.0), 3,
                 rot=math.atan2(b[1] - a[1], b[0] - a[0]))
        glass_vault(frame, glass, a, b, 11.0, 10.0, 4.5)
    for c in d:
        wall.cylinder((c[0], c[1], 0), S.VIA_DOME_R + .4, 12.5, n=32, m=3)
        trim.cylinder((c[0], c[1], 12.5), S.VIA_DOME_R + 1.0, .6, n=32, m=0)
        ribbed_dome(frame, shells, c, S.VIA_DOME_R + .2, 13.1, 5.8, n=16, m_shell=0)
        shells.cylinder((c[0], c[1], 18.8), .9, 1.4, n=12, m=1)
    (bx, by), br = S.BIG_DOME
    wall.cylinder((bx, by, 0), br + .5, 14.0, n=48, m=3)
    trim.cylinder((bx, by, 14.0), br + 1.2, .8, n=48, m=0)
    ribbed_dome(frame, shells, (bx, by), br + .4, 14.8, 8.5, n=24)
    # porte-cochere: hipped glass canopy on columns
    pc = ccw(S.PORTE)
    xs = [p[0] for p in pc]
    ys = [p[1] for p in pc]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    for i in range(7):
        for j in (0, 1):
            x = x0 + 2 + (x1 - x0 - 4) * i / 6
            y = y0 + 2 if j == 0 else y1 - 2
            trim.cylinder((x, y, 0), .55, .8, n=16, m=0)
            trim.cylinder((x, y, .8), .42, 9.6, n=16, m=0, r_top=.36)
            trim.cylinder((x, y, 10.4), .7, .6, n=16, m=0)
    wall.box(((x0 + x1) / 2, (y0 + y1) / 2, 11.5), (x1 - x0, y1 - y0, 1.2), 1)
    glass_vault(frame, glass, ((x0), (y0 + y1) / 2), ((x1), (y0 + y1) / 2), (y1 - y0) - 2, 12.1, 5.0, 3.0)
    return [top, wall.build(coll), trim.build(coll, smooth=True, sharp=35), frame.build(coll),
            glass.build(coll, props={'nobake': 1, 'mat': 'skylight'}), shells.build(coll, smooth=True, sharp=50)]


def pools(coll, M):
    pb = MB('pools', [M['pool_tile'], M['pool_deck']])
    out = []
    for i, p in enumerate(S.POOLS):
        p = ccw(p)
        extrude_poly(pb, offset_closed(p, .8), 0, .25, 1, 1)
        n = len(p)
        for k in range(n):
            a, c = p[k], p[(k + 1) % n]
            pb.quad((c[0], c[1], .25), (a[0], a[1], .25), (a[0], a[1], -1.6), (c[0], c[1], -1.6), 0)
        pb.poly([(x, y, -1.6) for x, y in p], 0)
        w = MB(f'WATER_pool_{i}', [M['pool_water']])
        w.poly([(x, y, .05) for x, y in p], 0)
        out.append(w.build(coll, props={'nobake': 1, 'mat': 'pool'}))
    out.append(pb.build(coll))
    return out


def context(coll, M):
    """Neighbours as honest massing: height + footprint only, windows from a procedural grid."""
    cb = MB('context', [M['context_lit']])
    for poly, h in S.CONTEXT:
        extrude_poly(cb, ccw(poly), 0, h, 0, 0)
    out = [cb.build(coll)]
    out += eiffel(coll, M)
    return out


def eiffel(coll, M):
    """Paris Las Vegas half-scale Eiffel Tower (164.6 m), across the Strip from the lake."""
    e = MB('eiffel', [M['eiffel']])
    c = Vector(S.EIFFEL)
    H = 164.6
    base = 31.0                        # half of the 125 m original base width, /2 for half-width

    def half(z):                       # half-width of the tower at height z (approx. exponential profile)
        return max(1.2, base * math.exp(-z / 38.0) - 1.6 * (z / H))
    levels = [0, 14, 28, 29.5, 42, 58, 58.5, 80, 100, 115, 116, 135, 150, H]
    for lv in range(len(levels) - 1):
        z0, z1 = levels[lv], levels[lv + 1]
        h0, h1 = half(z0), half(z1)
        for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
            p0 = (c.x + sx * h0, c.y + sy * h0, z0)
            p1 = (c.x + sx * h1, c.y + sy * h1, z1)
            e.box_between(p0, p1, 2.0 if z0 < 58 else 1.2, 2.0 if z0 < 58 else 1.2, 0)
        corners0 = [(c.x + sx * h0, c.y + sy * h0, z0) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        corners1 = [(c.x + sx * h1, c.y + sy * h1, z1) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        nsub = 3 if z0 < 58 else 2
        for k in range(4):
            a0, b0, a1, b1 = [Vector(p) for p in (corners0[k], corners0[(k + 1) % 4], corners1[k], corners1[(k + 1) % 4])]
            e.box_between(a1, b1, .6, .6, 0)
            for s in range(nsub):
                t0, t1 = s / nsub, (s + 1) / nsub
                p00, p10 = a0.lerp(b0, t0), a0.lerp(b0, t1)
                p01, p11 = a1.lerp(b1, t0), a1.lerp(b1, t1)
                e.box_between(p00, p11, .28, .28, 0)
                e.box_between(p10, p01, .28, .28, 0)
                e.box_between(p00, p01, .22, .22, 0)
            # inner leg faces (each of the four legs is itself a lattice box)
            if z1 <= 58:
                inner0, inner1 = a0.lerp(Vector((c.x, c.y, z0)), .22), a1.lerp(Vector((c.x, c.y, z1)), .22)
                e.box_between(inner0, inner1, .9, .9, 0)
                e.box_between(a0, inner1, .22, .22, 0)
                e.box_between(inner0, a1, .22, .22, 0)
    for z, w in ((28, 1.0), (58, .9), (116, .6)):
        hw = half(z) + 1.5
        e.box((c.x, c.y, z + .8), (hw * 2, hw * 2, 1.6), 0)
    # arches under the first platform
    for k in range(4):
        a = k * math.pi / 2
        for i in range(12):
            t0, t1 = i / 12, (i + 1) / 12
            def P(t):
                u = -1 + 2 * t
                hw = half(0) * .72
                z = 12 + 12 * math.sqrt(max(0, 1 - u * u))
                x, y = u * hw, hw * 1.05
                return (c.x + x * math.cos(a) - y * math.sin(a), c.y + x * math.sin(a) + y * math.cos(a), z)
            e.box_between(P(t0), P(t1), .6, .6, 0)
    e.cylinder((c.x, c.y, H - 6), .6, 6, n=8, m=0, r_top=.1)
    return [e.build(coll)]


# ------------------------------------------------------------------ trees
def tree_positions():
    pts = json.load(open(os.path.join(DATA, 'trees.json')))
    out = []
    for x, y, r in pts:
        if abs(x - S.STRIP_X) < 40 and x > 250:
            kind = 'shade'                       # Strip promenade: broad shade trees
        elif x < -20 and -110 < y < -20:
            kind = 'palm'                        # pool garden
        elif rnd.random() < .28:
            kind = 'cypress'
        elif rnd.random() < .5:
            kind = 'pine'                        # Italian stone pine
        else:
            kind = 'shade'
        out.append((x, y, r, kind))
    return out


def tree_protos(coll, M):
    """One mesh per species; instanced in Blender and in the browser."""
    protos = {}
    # cypress: tall spindle
    m = MB('TREE_cypress', [M['bark'], M['leaf_dark']])
    m.cylinder((0, 0, 0), .18, 1.2, n=6, m=0)
    prof = [(0.0, .8)] + [(1.0 * math.sin(math.pi * (t / 12) ** .8) * (1 - t / 13), .8 + 11 * t / 12) for t in range(1, 12)] + [(0, 12.4)]
    lumpy_lathe(m, prof, 1)
    protos['cypress'] = m
    # stone pine: tall trunk, flat umbrella crown
    m = MB('TREE_pine', [M['bark'], M['leaf']])
    m.box_between((0, 0, 0), (.3, .2, 7.0), .45, .45, 0)
    for i in range(7):
        a = i / 7 * TAU
        cx, cy = 2.2 * math.cos(a), 2.2 * math.sin(a)
        lumpy_blob(m, (cx, cy, 8.0), (2.6, 2.6, 1.2), 1)
    lumpy_blob(m, (0, 0, 8.4), (3.0, 3.0, 1.4), 1)
    protos['pine'] = m
    # shade tree (elm/ash-like)
    m = MB('TREE_shade', [M['bark'], M['leaf']])
    m.box_between((0, 0, 0), (0, 0, 3.5), .38, .38, 0)
    for i in range(5):
        a = i / 5 * TAU
        lumpy_blob(m, (1.3 * math.cos(a), 1.3 * math.sin(a), 5.0 + (i % 2) * .8), (2.2, 2.2, 1.9), 1)
    lumpy_blob(m, (0, 0, 6.2), (2.6, 2.6, 2.2), 1)
    protos['shade'] = m
    # palm: curved trunk + fronds
    m = MB('TREE_palm', [M['palm_bark'], M['leaf']])
    pts = [(0.25 * (z / 11) ** 2, 0, z) for z in range(0, 12)]
    for p, q in zip(pts, pts[1:]):
        m.box_between(p, q, .42, .42, 0)
    top = Vector(pts[-1])
    for i in range(14):
        a = i / 14 * TAU
        d = Vector((math.cos(a), math.sin(a), 0))
        droop = .35 + .3 * (i % 2)
        prev = top
        for k in range(1, 6):
            t = k / 5
            p = top + d * (4.2 * t) + Vector((0, 0, 1.2 * t - droop * 4 * t * t))
            side = d.cross(Vector((0, 0, 1))) * (.55 * math.sin(math.pi * t) + .1)
            m.quad(prev - side * .8, p - side, p + side, prev + side * .8, 1)
            m.quad(prev + side * .8, p + side, p - side, prev - side * .8, 1)
            prev = p
    protos['palm'] = m
    objs = {}
    for k, mb in protos.items():
        o = mb.build(coll, smooth=True, sharp=80, props={'nobake': 1, 'proto': k})
        objs[k] = o
    return objs


def lumpy_lathe(mb, prof, m, n=10):
    rings = []
    for i, (r, z) in enumerate(prof):
        ring = []
        for j in range(n):
            a = j / n * TAU
            k = 1 + .22 * noise.noise(Vector((math.cos(a) * 2, math.sin(a) * 2, z * .9)))
            ring.append((r * k * math.cos(a), r * k * math.sin(a), z))
        rings.append(ring)
    for i in range(len(prof) - 1):
        for j in range(n):
            k2 = (j + 1) % n
            mb.quad(rings[i][j], rings[i][k2], rings[i + 1][k2], rings[i + 1][j], m)


def lumpy_blob(mb, c, s, m, n1=10, n2=6):
    seed = Vector((c[0] * 3.1, c[1] * 1.7, c[2] * 2.3))
    rings = []
    for i in range(n2 + 1):
        th = math.pi * i / n2
        ring = []
        for j in range(n1):
            ph = TAU * j / n1
            d = Vector((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)))
            k = 1 + .28 * noise.noise(d * 2.2 + seed)
            ring.append((c[0] + d.x * s[0] * k, c[1] + d.y * s[1] * k, c[2] + d.z * s[2] * k))
        rings.append(ring)
    for i in range(n2):
        for j in range(n1):
            k2 = (j + 1) % n1
            mb.quad(rings[i][j], rings[i + 1][j], rings[i + 1][k2], rings[i][k2], m)


def plant_trees(coll, protos):
    inst = bpy.data.collections.new('TREES')
    coll.children.link(inst)
    placed = []
    for x, y, r, kind in tree_positions():
        src = protos[kind]
        o = bpy.data.objects.new(f'tree_{kind}', src.data)
        s = {'cypress': .75 + r * .12, 'pine': .55 + r * .12, 'shade': .55 + r * .14, 'palm': .8 + r * .06}[kind]
        o.scale = (s, s, s * (1.0 + rnd.random() * .2))
        o.rotation_euler = (0, 0, rnd.random() * TAU)
        o.location = (x, y, 0)
        o['nobake'] = 1
        inst.objects.link(o)
        placed.append({'k': kind, 'x': x, 'y': y, 's': round(s, 3), 'r': round(o.rotation_euler.z, 3)})
    return placed


def build(coll, M):
    objs = []
    objs += terrain(coll, M)
    objs += promenade(coll, M)
    objs += shoreline_rocks(coll, M)
    objs += village(coll, M)
    objs += structures(coll, M)
    objs += pools(coll, M)
    objs += context(coll, M)
    protos = tree_protos(coll, M)
    trees = plant_trees(coll, protos)
    for o in protos.values():
        o.location.z = -500            # prototypes parked out of sight
    return objs, trees, protos
