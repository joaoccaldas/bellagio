"""Main tower (Y plan, 36 floors, 155.8 m) and the 2004 Spa Tower."""
import math
import bpy
from mathutils import Vector
import survey as S
from geo import (MB, Straight, Arc, facade, sweep_profile, hip_roof, offset_polyline, line_x, ccw, inside,
                 circle_pts, v2, wall_rect)

# window types (b/t are measured from the bottom of the row)
WIN = dict(w=5.5, b=.55, t=5.55, depth=.45, transom=[3.05], slab=3.05, mull=.2)
WIN_CYL = dict(w=3.6, b=.55, t=5.55, depth=.4, transom=[3.05], slab=3.05, mull=.14)
ARCH = dict(w=6.2, b=.8, t=14.6, arch=True, depth=.6, transom=[6.1], slab=6.1, mull=.24, bifora=True)
ARCH_CYL = dict(w=3.4, b=.8, t=13.0, arch=True, depth=.5, transom=[6.1], slab=6.1, mull=.14)

BELT = [(0.0, 0.0), (0.243, 0.046), (0.324, 0.345), (0.54, 0.483), (0.621, 1.092), (0.405, 1.242), (0.405, 1.495), (0.162, 1.725), (0.0, 1.725)]
BELT2 = [(0.0, 0.0), (0.27, 0.057), (0.351, 0.402), (0.675, 0.575), (0.756, 1.38), (0.486, 1.552), (0.486, 1.84), (0.162, 2.07), (0.0, 2.07)]
CORNICE = [(0, 0), (.15, 0), (.2, .35), (.38, .5), (.42, .95), (.62, 1.05), (.66, 1.45), (1.1, 1.75), (1.4, 2.35),
           (1.55, 2.62), (1.55, 3.0), (0, 3.0)]
ATTIC_CORNICE = [(0, 0), (.12, 0), (.16, .3), (.34, .45), (.38, .9), (.9, 1.3), (1.2, 1.9), (1.3, 2.1), (1.3, 2.4), (0, 2.4)]

# material slots of the wall builder
WALL, TRIM, SILL, FRIEZE, DARK = range(5)
MW = dict(wall=WALL, reveal=TRIM, sill=SILL)


def zones(top='main', row_from=1):
    Z = [(0, S.ROW * row_from, None)]
    for k in range(row_from, 7):
        Z.append((k * S.ROW, (k + 1) * S.ROW, WIN))
    Z.append((S.H_BELT1, S.H_BELT1 + 1.5, None))
    z = S.H_BELT1 + 1.5
    for k in range(8):
        Z.append((z, z + S.ROW, WIN))
        z += S.ROW
    Z.append((S.H_BELT2, S.H_BELT2 + 1.8, None))
    z = S.H_BELT2 + 1.8
    for k in range(2):
        Z.append((z, z + S.ROW, WIN))
        z += S.ROW
    if top == 'main':
        Z.append((S.H_ARCH0, S.H_ARCH1, ARCH))
        Z.append((S.H_ARCH1, 126.0, FRIEZE))
        Z.append((126.0, S.H_CORNICE, None))
    else:
        Z.append((S.H_ARCH0, S.H_ARCH0 + S.ROW, WIN))
        Z.append((S.H_ARCH0 + S.ROW, S.H_END - 2.4, FRIEZE))
        Z.append((S.H_END - 2.4, S.H_END, None))
    return Z


def cyl_zones():
    out = []
    for z0, z1, w in zones('main'):
        if w is WIN:
            w = WIN_CYL
        elif w is ARCH:
            w = ARCH_CYL
        out.append((z0, z1, w))
    return out


def plan():
    """Main Y outline (CCW) + three end blocks, from the traced centre-lines."""
    wings = {'N': S.WING_N, 'W': S.WING_W, 'S': S.WING_S}
    side = {}
    for k, pts in wings.items():
        h = S.WING_DEPTH[k] / 2
        L = offset_polyline(pts, h)      # left when walking outward from the core
        R = offset_polyline(pts, -h)
        d = (v2(pts[1]) - v2(pts[0])).normalized()
        side[k] = dict(L=L, R=R, d=d)
    X_E = line_x(side['S']['L'][0], side['S']['d'], side['N']['R'][0], side['N']['d'])
    X_NW = line_x(side['N']['L'][0], side['N']['d'], side['W']['R'][0], side['W']['d'])
    X_SW = line_x(side['W']['L'][0], side['W']['d'], side['S']['R'][0], side['S']['d'])
    N, W, Sx = side['N'], side['W'], side['S']
    main = [X_E, N['R'][1], N['L'][1], X_NW, W['R'][1], W['L'][1], X_SW, Sx['R'][1], Sx['L'][1]]
    shared = {1, 4, 7}                  # edge index i -> (main[i], main[i+1]) touches an end block
    ends = {k: [side[k]['R'][1], side[k]['R'][2], side[k]['L'][2], side[k]['L'][1]] for k in wings}
    roofs = []
    for k, pts in wings.items():
        s = side[k]
        back = -s['d'] * (S.WING_DEPTH[k] * .5)
        roofs.append([s['R'][0] + back, s['R'][1], s['L'][1], s['L'][0] + back])
    return main, shared, ends, roofs


def text_mesh(txt, font_path, size):
    cu = bpy.data.curves.new('txt', 'FONT')
    cu.body = txt
    try:
        cu.font = bpy.data.fonts.load(font_path, check_existing=True)
    except Exception:
        pass
    cu.size = size
    cu.extrude = .14
    cu.align_x = 'CENTER'
    ob = bpy.data.objects.new('txt', cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    return me


def bend_text(mb, me, c, R, ang, z, m):
    """Wrap a text mesh around a vertical cylinder, centred at angle `ang`, facing outward."""
    for p in me.polygons:
        pts = []
        for vi in p.vertices:
            x, y, zz = me.vertices[vi].co
            a = ang + x / R
            r = R + .16 + zz
            pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a), z + y))
        mb.poly(pts, m)


def floodlights():
    """(location, direction) pairs for facade wash lights: one every ~11 m along each belt, aimed up the wall."""
    main, shared, ends, roofs = plan()
    out = []
    for poly, zs in ((ccw([v2(p) for p in main]), (8.0, S.H_BELT1 + 1.8, S.H_BELT2 + 2.1, S.H_ARCH0)),):
        n = len(poly)
        for i in range(n):
            a, b = v2(poly[i]), v2(poly[(i + 1) % n])
            L = (b - a).length
            t = (b - a) / L
            nrm = Vector((t.y, -t.x))
            k = max(1, int(L / 11))
            for j in range(k):
                p = a + t * (L * (j + .5) / k) + nrm * 2.2
                for z in zs:
                    out.append(((p.x, p.y, z), (-nrm.x * .45, -nrm.y * .45, 1.0)))
    for q in ends.values():
        q = ccw([v2(p) for p in q])
        for i in range(3):
            a, b = q[i], q[i + 1]
            L = (b - a).length; t = (b - a) / L; nrm = Vector((t.y, -t.x))
            for j in range(max(1, int(L / 11))):
                p = a + t * (L * (j + .5) / max(1, int(L / 11))) + nrm * 2.2
                for z in (8.0, S.H_BELT1 + 1.8, S.H_BELT2 + 2.1):
                    out.append(((p.x, p.y, z), (-nrm.x * .45, -nrm.y * .45, 1.0)))
    return out


def build(coll, M):
    wall = MB('tower_wall', [M['stucco'], M['trim'], M['sill'], M['frieze'], M['dark']])
    trim = MB('tower_trim', [M['trim']])
    frame = MB('tower_frame', [M['bronze']])
    glass = MB('GLASS_tower', [M['glass']], uv2=True)
    roof = MB('tower_roof', [M['roof'], M['copper'], M['dark']])
    up = MB('EMIT_uplight', [M['uplight']])
    lant = MB('EMIT_lantern', [M['lantern_in']])
    sign = MB('tower_sign', [M['bronze']])

    main, shared, ends, roofs = plan()
    main = [v2(p) for p in main]
    core = v2(S.CORE)

    def under_podium(path, s, z0, z1):
        p, n = path.at(s)
        q = p + n * 1.0
        return z1 <= S.ROW * 2 + .01 and inside(S.PODIUM, (q.x, q.y))

    def not_in_core(path, s):
        p, _ = path.at(s)
        return (p - core).length > S.CORE_R + 1.2

    Zm = zones('main')
    n = len(main)
    for i in range(n):
        a, b = main[i], main[(i + 1) % n]
        path = Straight(a, b)
        facade(wall, glass, frame, path, Zm, S.BAY, MW, zmin=S.H_END if i in shared else -1e9, bay_filter=not_in_core, skip=under_podium)
    Ze = zones('end')
    for k, q in ends.items():
        q = [v2(p) for p in q]
        for i in range(3):          # edge 3 (back to the main block) is interior
            facade(wall, glass, frame, Straight(q[i], q[i + 1]), Ze, S.BAY, MW, skip=under_podium)

    # core cylinder: find the arc that is outside the Y
    angs = [a / 360 * math.tau for a in range(-180, 180)]
    outs = [not inside(main, (core.x + (S.CORE_R + .05) * math.cos(a), core.y + (S.CORE_R + .05) * math.sin(a))) for a in angs]
    run = [a for a, o in zip(angs, outs) if o]
    a0, a1 = min(run), max(run)
    cyl = Arc(core, S.CORE_R, a0, a1)
    facade(wall, glass, frame, cyl, cyl_zones(), 7.0, MW, skip=under_podium)

    # mouldings + night uplight strips
    for z, prof in ((S.H_BELT1, BELT), (S.H_BELT2, BELT2), (126.0, CORNICE)):
        sweep_profile(trim, ccw(main), z, prof, 0)
        top = z + prof[-1][1]
        sweep_profile(up, ccw(main), top + .02, [(.2, 0), (.34, 0)], 0) if z < 120 else None
    for k, q in ends.items():
        for z, prof in ((S.H_BELT1, BELT), (S.H_BELT2, BELT2), (S.H_END - 2.4, ATTIC_CORNICE)):
            sweep_profile(trim, ccw(q), z, prof, 0)
        sweep_profile(up, ccw(q), S.H_BELT1 + 1.52, [(.2, 0), (.34, 0)], 0)
        sweep_profile(up, ccw(q), S.H_BELT2 + 1.82, [(.2, 0), (.34, 0)], 0)
    ring = circle_pts(core, S.CORE_R, 64)
    for z, prof in ((S.H_BELT1, BELT), (S.H_BELT2, BELT2), (126.0, CORNICE)):
        sweep_profile(trim, ring, z, prof, 0)
    # a lit band under the arcade (reads as the bright ring of light in night photos)
    sweep_profile(up, ccw(main), S.H_ARCH0 - .15, [(.12, 0), (.26, 0)], 0)

    # roofs
    for q in roofs:
        hip_roof(roof, q, S.H_CORNICE, 11, 0, eave=.2)
    for q in ends.values():
        hip_roof(roof, q, S.H_END, 11, 0, eave=.2)

    # ---- drum, sign, lantern, dome
    zc = S.H_CORNICE
    Rd = 9.4
    drum = Arc(core, Rd, 0, math.tau)
    wall_rect(wall, drum, 0, drum.L, zc, zc + 2.2, WALL, seg=1.5)
    wall_rect(wall, drum, 0, drum.L, zc + 2.2, zc + 5.0, FRIEZE, seg=1.5)    # diamond frieze band
    wall_rect(wall, drum, 0, drum.L, zc + 5.0, zc + 10.2, WALL, seg=1.5)     # sign band
    wall_rect(wall, drum, 0, drum.L, zc - 2, zc, WALL, seg=1.5)
    sweep_profile(trim, circle_pts(core, Rd, 72), zc + 10.2, [(0, 0), (.2, .1), (.3, .5), (.7, .8), (.95, 1.3), (1.0, 1.6), (0, 1.6)], 0)
    sweep_profile(trim, circle_pts(core, Rd, 72), zc + 4.8, [(0, 0), (.25, .05), (.3, .25), (0, .3)], 0)
    sweep_profile(up, circle_pts(core, Rd, 72), zc + 5.05, [(.9, 0), (1.3, 0)], 0)   # floods the sign band
    font = '/System/Library/Fonts/Supplemental/Times New Roman.ttf'
    me = text_mesh('BELLAGIO', font, 3.4)
    for ang in (0.0, math.pi):
        bend_text(sign, me, core, Rd, ang, zc + 6.2, 0)
    bpy.data.meshes.remove(me)
    zl = zc + 11.8                       # lantern floor, ~140.8
    Rl = 8.4
    wall.lathe(core, [(Rd + 1.0, zc + 11.8), (Rl + .6, zl), (Rl + .6, zl + .5), (0, zl + .5)], 72, TRIM)
    lan = Arc(core, Rl, 0, math.tau)
    facade(wall, None, None, lan, [(zl + .5, zl + 7.6, dict(w=2.9, b=.3, t=6.6, arch=True, depth=.9))], lan.L / 12,
           dict(wall=TRIM, reveal=TRIM, sill=TRIM))
    # inner glowing drum with ribs (reads yellow at night)
    lant.cylinder((core.x, core.y, 0), Rl - 1.6, 7.6, n=48, m=0, z0=zl + .5, cap=False)
    lant.lathe((core.x, core.y, 0), [(Rl - 1.6, zl + 8.1), (Rl * .55, zl + 9.4), (0, zl + 9.9)], 48, 0)
    # balustrade ring in front of the arches
    from geo import balustrade
    balustrade(trim, circle_pts(core, Rl + .35, 36), zl + .5, 0, h=1.0, spacing=.35, closed=True)
    zt = zl + 7.6
    wall.lathe(core, [(Rl, zt), (Rl + .6, zt + .3), (Rl + 1.1, zt + .9), (Rl + 1.35, zt + 1.5), (Rl + 1.35, zt + 1.9),
                      (Rl + .2, zt + 1.9), (Rl + .2, zt + 1.6), (0, zt + 1.6)], 72, TRIM)
    zdome = zt + 1.9
    roof.dome((core.x, core.y, 0), Rl + .3, 2.8, n=64, rings=10, m=1, z0=zdome)
    ztop = zdome + 2.6
    roof.cylinder((core.x, core.y, 0), 1.35, 1.25, n=16, m=2, z0=ztop, cap=False)
    wall.lathe(core, [(1.65, ztop + 1.25), (1.65, ztop + 1.45), (0, ztop + 1.45)], 24, TRIM)
    roof.dome((core.x, core.y, 0), 1.2, .55, n=16, rings=4, m=1, z0=ztop + 1.45)
    roof.cylinder((core.x, core.y, 0), .06, S.H_TOP - (ztop + 2.0), n=6, m=2, z0=ztop + 2.0)
    lant.cylinder((core.x, core.y, 0), 1.2, 1.1, n=16, m=0, z0=ztop + .1, cap=True)

    objs = [wall.build(coll), trim.build(coll, smooth=True, sharp=35), frame.build(coll),
            glass.build(coll, props={'nobake': 1, 'mat': 'glass_tower'}),
            roof.build(coll, smooth=True, sharp=30), sign.build(coll),
            up.build(coll, props={'emit': (1.0, .72, .42), 'strength': 60.0, 'dyn': 'night'}),
            lant.build(coll, props={'emit': (1.0, .78, .25), 'strength': 16.0, 'dyn': 'night'})]
    return [o for o in objs if o]


def build_spa(coll, M):
    wall = MB('spa_wall', [M['stucco'], M['trim'], M['sill'], M['frieze'], M['dark']])
    trim = MB('spa_trim', [M['trim']])
    frame = MB('spa_frame', [M['bronze']])
    glass = MB('GLASS_spa', [M['glass']], uv2=True)
    roof = MB('spa_roof', [M['roof']])
    up = MB('EMIT_spa_uplight', [M['uplight']])
    a, b = v2(S.SPA[0]), v2(S.SPA[1])
    L = offset_polyline([a, b], S.SPA_DEPTH / 2)
    R = offset_polyline([a, b], -S.SPA_DEPTH / 2)
    q = ccw([R[0], R[1], L[1], L[0]])
    q = [v2(p) for p in q]
    Z = zones('end', row_from=2)
    for i in range(4):
        facade(wall, glass, frame, Straight(q[i], q[(i + 1) % 4]), Z, S.BAY, MW)
    for z, prof in ((S.H_BELT1, BELT), (S.H_BELT2, BELT2), (S.H_END - 2.4, ATTIC_CORNICE)):
        sweep_profile(trim, q, z, prof, 0)
    sweep_profile(up, q, S.H_BELT2 + 1.82, [(.2, 0), (.34, 0)], 0)
    hip_roof(roof, q, S.H_END, 20, 0, eave=.2)
    return [o for o in (wall.build(coll), trim.build(coll, smooth=True, sharp=35), frame.build(coll),
                        glass.build(coll, props={'nobake': 1, 'mat': 'glass_tower'}), roof.build(coll),
                        up.build(coll, props={'emit': (1.0, .72, .42), 'strength': 60.0, 'dyn': 'night'})) if o]
