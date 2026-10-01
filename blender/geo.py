"""Geometry toolkit: batched mesh builder, facade generator, molding sweeps, roofs."""
import math
import bpy
import bmesh
from mathutils import Vector

TAU = math.tau


# ------------------------------------------------------------------ batched mesh
class MB:
    """Accumulates polygons per material; one Blender object per builder keeps bakes fast."""

    def __init__(self, name, mats, uv2=False):
        self.name, self.mats = name, list(mats)
        self.v, self.f, self.mi, self.uv, self.uv2 = [], [], [], [], []
        self.has_uv2 = uv2

    def poly(self, pts, m=0, uv=None, uv2=None):
        base = len(self.v)
        self.v.extend(tuple(p) for p in pts)
        self.f.append(tuple(range(base, base + len(pts))))
        self.mi.append(m)
        self.uv.append(uv)
        self.uv2.append(uv2)

    def quad(self, a, b, c, d, m=0, uv=None, uv2=None):
        self.poly((a, b, c, d), m, uv, uv2)

    def tri(self, a, b, c, m=0):
        self.poly((a, b, c), m)

    def box(self, c, size, m=0, rot=0.0):
        """Axis-aligned (optionally z-rotated) box."""
        sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
        co, si = math.cos(rot), math.sin(rot)

        def p(x, y, z):
            return (c[0] + x * co - y * si, c[1] + x * si + y * co, c[2] + z)
        v = [p(-sx, -sy, -sz), p(sx, -sy, -sz), p(sx, sy, -sz), p(-sx, sy, -sz),
             p(-sx, -sy, sz), p(sx, -sy, sz), p(sx, sy, sz), p(-sx, sy, sz)]
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self.poly([v[i] for i in f], m)

    def box_between(self, a, b, w, h, m=0, up=(0, 0, 1)):
        """Beam of width w (horizontal) and height h (along `up`) from a to b."""
        a, b, up = Vector(a), Vector(b), Vector(up)
        t = (b - a)
        if t.length < 1e-6:
            return
        t.normalize()
        s = t.cross(up)
        if s.length < 1e-6:
            s = t.cross(Vector((1, 0, 0)))
        s.normalize()
        u = s.cross(t).normalized()
        c = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
        ra = [a + s * x + u * y for x, y in c]
        rb = [b + s * x + u * y for x, y in c]
        for i in range(4):
            j = (i + 1) % 4
            self.quad(ra[i], ra[j], rb[j], rb[i], m)
        self.poly(list(reversed(ra)), m)
        self.poly(rb, m)

    def cylinder(self, c, r, h, n=16, m=0, r_top=None, cap=True, z0=0.0):
        r_top = r if r_top is None else r_top
        lo = [(c[0] + r * math.cos(i / n * TAU), c[1] + r * math.sin(i / n * TAU), c[2] + z0) for i in range(n)]
        hi = [(c[0] + r_top * math.cos(i / n * TAU), c[1] + r_top * math.sin(i / n * TAU), c[2] + z0 + h) for i in range(n)]
        for i in range(n):
            j = (i + 1) % n
            self.quad(lo[i], lo[j], hi[j], hi[i], m)
        if cap:
            self.poly(list(reversed(lo)), m)
            if r_top > 1e-4:
                self.poly(hi, m)

    def lathe(self, c, prof, n=32, m=0, a0=0.0, a1=TAU):
        """Revolve a (r, z) profile around the z axis through c."""
        c = (c[0], c[1], c[2] if len(c) > 2 else 0.0)
        full = abs(a1 - a0 - TAU) < 1e-6
        cols = n if full else n + 1
        rings = []
        for i in range(cols):
            a = a0 + (a1 - a0) * i / n
            ca, sa = math.cos(a), math.sin(a)
            rings.append([(c[0] + r * ca, c[1] + r * sa, c[2] + z) for r, z in prof])
        for i in range(n):
            j = (i + 1) % cols if full else i + 1
            for k in range(len(prof) - 1):
                a, b = rings[i][k], rings[i][k + 1]
                cc, d = rings[j][k + 1], rings[j][k]
                if prof[k][0] < 1e-5 and prof[k + 1][0] < 1e-5:
                    continue
                self.quad(a, d, cc, b, m)

    def dome(self, c, r, h, n=32, rings=8, m=0, z0=0.0):
        prof = [(r * math.cos(k / rings * math.pi / 2), z0 + h * math.sin(k / rings * math.pi / 2)) for k in range(rings + 1)]
        prof[-1] = (0.0, z0 + h)
        self.lathe(c, prof, n, m)

    def build(self, coll, smooth=False, sharp=40, props=None):
        if not self.f:
            return None
        me = bpy.data.meshes.new(self.name)
        me.from_pydata(self.v, [], self.f)
        me.polygons.foreach_set('material_index', self.mi)
        uvl = me.uv_layers.new(name='UVMap')
        uv2l = me.uv_layers.new(name='WIN') if self.has_uv2 else None
        # default UVs: box projection in metres / 4 (for procedural detail)
        loops = me.loops
        verts = self.v
        for pi, poly in enumerate(me.polygons):
            given = self.uv[pi]
            if given is None:
                n = poly.normal
                ax = max(range(3), key=lambda k: abs(n[k]))
            for k, li in enumerate(poly.loop_indices):
                if given is not None:
                    uvl.data[li].uv = given[k]
                else:
                    co = verts[loops[li].vertex_index]
                    if ax == 0:
                        uvl.data[li].uv = (co[1] * .25, co[2] * .25)
                    elif ax == 1:
                        uvl.data[li].uv = (co[0] * .25, co[2] * .25)
                    else:
                        uvl.data[li].uv = (co[0] * .25, co[1] * .25)
                if uv2l is not None:
                    g2 = self.uv2[pi]
                    uv2l.data[li].uv = g2[k] if g2 is not None else (0, 0)
        for mt in self.mats:
            me.materials.append(mt)
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        for fc in bm.faces:
            fc.smooth = smooth
        if smooth and sharp:
            lim = math.radians(sharp)
            for e in bm.edges:
                if len(e.link_faces) == 2 and e.calc_face_angle(0) > lim:
                    e.smooth = False
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(self.name, me)
        coll.objects.link(o)
        for k, v in (props or {}).items():
            o[k] = v
        return o


# ------------------------------------------------------------------ 2D helpers
def v2(p):
    return Vector((p[0], p[1]))


def signed_area(poly):
    return .5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))


def ccw(poly):
    return list(poly) if signed_area(poly) > 0 else list(reversed(poly))


def line_x(p, d, q, e):
    """Intersection of lines p+t d and q+s e."""
    den = d[0] * e[1] - d[1] * e[0]
    if abs(den) < 1e-9:
        return None
    t = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
    return Vector((p[0] + d[0] * t, p[1] + d[1] * t))


def offset_polyline(pts, d):
    """Offset an open polyline to its left by d with mitred joints."""
    pts = [v2(p) for p in pts]
    out = []
    n = len(pts)
    for i in range(n):
        if i == 0:
            t = (pts[1] - pts[0]).normalized()
            out.append(pts[0] + Vector((-t.y, t.x)) * d)
        elif i == n - 1:
            t = (pts[-1] - pts[-2]).normalized()
            out.append(pts[-1] + Vector((-t.y, t.x)) * d)
        else:
            t1 = (pts[i] - pts[i - 1]).normalized()
            t2 = (pts[i + 1] - pts[i]).normalized()
            n1, n2 = Vector((-t1.y, t1.x)), Vector((-t2.y, t2.x))
            m = (n1 + n2).normalized()
            out.append(pts[i] + m * (d / max(m.dot(n1), .2)))
    return out


def offset_closed(poly, d):
    """Offset a CCW polygon outward by d (mitred)."""
    n = len(poly)
    out = []
    for i in range(n):
        a, b, c = v2(poly[i - 1]), v2(poly[i]), v2(poly[(i + 1) % n])
        t1, t2 = (b - a).normalized(), (c - b).normalized()
        n1, n2 = Vector((t1.y, -t1.x)), Vector((t2.y, -t2.x))
        m = (n1 + n2)
        m = m.normalized() if m.length > 1e-6 else n1
        out.append(b + m * (d / max(m.dot(n1), .25)))
    return out


def inside(poly, p):
    x, y = p[0], p[1]
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            c = not c
    return c


# ------------------------------------------------------------------ wall paths
class Straight:
    def __init__(self, a, b):
        self.a, self.b = v2(a), v2(b)
        self.L = (self.b - self.a).length
        self.t = (self.b - self.a) / self.L
        self.n = Vector((self.t.y, -self.t.x))   # outward for a CCW polygon
        self.curved = False

    def at(self, s):
        return self.a + self.t * s, self.n


class Arc:
    """Convex arc around centre c from angle a0 to a1 (radians, CCW), outward normal radial."""

    def __init__(self, c, r, a0, a1):
        self.c, self.r, self.a0, self.a1 = v2(c), r, a0, a1
        self.L = r * (a1 - a0)
        self.curved = True

    def at(self, s):
        a = self.a0 + s / self.r
        n = Vector((math.cos(a), math.sin(a)))
        return self.c + n * self.r, n


def P3(path, s, z, depth=0.0):
    p, n = path.at(s)
    q = p - n * depth
    return (q.x, q.y, z)


def wall_rect(mb, path, s0, s1, z0, z1, m, depth=0.0, seg=2.5):
    if s1 - s0 < 1e-4 or z1 - z0 < 1e-4:
        return
    k = max(1, math.ceil((s1 - s0) / seg)) if path.curved else 1
    for i in range(k):
        a = s0 + (s1 - s0) * i / k
        b = s0 + (s1 - s0) * (i + 1) / k
        mb.quad(P3(path, a, z0, depth), P3(path, b, z0, depth), P3(path, b, z1, depth), P3(path, a, z1, depth), m)


def opening_outline(c, ww, zb, zt, arch, nseg=10):
    """Outline (s, z) of an opening, CCW starting bottom-left."""
    pts = [(c - ww / 2, zb), (c + ww / 2, zb)]
    if arch:
        r = ww / 2
        spring = zt - r
        pts.append((c + ww / 2, spring))
        for i in range(1, nseg):
            a = math.pi * i / nseg
            pts.append((c + r * math.cos(a), spring + r * math.sin(a)))
        pts.append((c - ww / 2, spring))
    else:
        pts += [(c + ww / 2, zt), (c - ww / 2, zt)]
    return pts


def facade_cell(mb, glass, frame, path, s0, s1, z0, z1, win, M, tag=0.0):
    """One bay/row cell: wall with a recessed opening, glass, mullions.

    win = dict(w, b, t, arch, depth, mull, transom)  (b/t = opening bottom/top above z0)
    M   = dict(wall, reveal, sill, frame) material indices of `mb` / `frame`.
    """
    c = (s0 + s1) / 2
    ww = min(win['w'], (s1 - s0) - .6)
    zb, zt = z0 + win['b'], z0 + win['t']
    arch = win.get('arch', False)
    d = win.get('depth', .45)
    wm, rm = M['wall'], M['reveal']
    L, R = c - ww / 2, c + ww / 2
    # wall around the opening
    wall_rect(mb, path, s0, s1, z0, zb, wm)
    wall_rect(mb, path, s0, L, zb, zt, wm)
    wall_rect(mb, path, R, s1, zb, zt, wm)
    wall_rect(mb, path, s0, s1, zt, z1, wm)
    outl = opening_outline(c, ww, zb, zt, arch)
    if arch:
        # infill between the semicircle and the square head of the cell
        arc_pts = sorted([outl[2]] + outl[3:-1] + [outl[-1]], key=lambda q: q[0])
        for (sa, za), (sb, zb2) in zip(arc_pts, arc_pts[1:]):
            mb.quad(P3(path, sa, za), P3(path, sb, zb2), P3(path, sb, zt), P3(path, sa, zt), wm)
    # reveals
    n = len(outl)
    for i in range(n):
        (sa, za), (sb, zb2) = outl[i], outl[(i + 1) % n]
        mat = M.get('sill', rm) if i == 0 else rm
        mb.quad(P3(path, sb, zb2, 0), P3(path, sa, za, 0), P3(path, sa, za, d), P3(path, sb, zb2, d), mat)
    if glass is None and win.get('back') is not None:
        mb.poly([P3(path, s, z, d) for s, z in outl][::-1], win['back'])
    # glass (own mesh: real-time material, per-window uv + random tag)
    if glass is not None:
        uv = [((s - L) / ww, (z - zb) / (zt - zb)) for s, z in outl]
        import random
        g = (random.random(), tag)
        glass.poly([P3(path, s, z, d) for s, z in outl], 0, uv=uv, uv2=[g] * n)
    # mullions / transoms in bronze
    if frame is not None:
        fd = d - .06
        mw = win.get('mull', .22)
        up = tuple(path.at(c)[1].to_3d())
        frame.box_between(Vector(P3(path, c, zb, fd)), Vector(P3(path, c, zt, fd)), mw, .12, 0, up=up)
        for tz in win.get('transom', []):
            zz = z0 + tz
            frame.box_between(Vector(P3(path, L, zz, fd)), Vector(P3(path, R, zz, fd)), .5 if tz == win.get('slab') else .18, .12, 0, up=up)
        for i in range(n):
            (sa, za), (sb, zb2) = outl[i], outl[(i + 1) % n]
            frame.box_between(Vector(P3(path, sa, za, fd)), Vector(P3(path, sb, zb2, fd)), .12, .12, 0, up=up)
        if arch and win.get('bifora'):
            # two lancets under the main arch, each with its own small round head
            r2 = ww / 4
            spring = zt - ww / 2
            for cc in (c - r2, c + r2):
                pts = [(cc + r2 * math.cos(math.pi * k / 8), spring + r2 * math.sin(math.pi * k / 8)) for k in range(9)]
                for (sa, za), (sb, zb2) in zip(pts, pts[1:]):
                    frame.box_between(Vector(P3(path, sa, za, fd)), Vector(P3(path, sb, zb2, fd)), mw * .9, .12, 0, up=up)
            # oculus in the tympanum
            rr = ww * .09
            oc = spring + ww / 2 * .62
            pts = [(c + rr * math.cos(TAU * k / 12), oc + rr * math.sin(TAU * k / 12)) for k in range(13)]
            for (sa, za), (sb, zb2) in zip(pts, pts[1:]):
                frame.box_between(Vector(P3(path, sa, za, fd)), Vector(P3(path, sb, zb2, fd)), .1, .12, 0, up=up)


def facade(mb, glass, frame, path, zones, bay, M, s_from=0.0, s_to=None, zmin=-1e9, bay_filter=None, skip=None):
    """zones: list of (z0, z1, win|None). Bays are distributed evenly over the path length."""
    s_to = path.L if s_to is None else s_to
    L = s_to - s_from
    nb = max(1, round(L / bay))
    w = L / nb
    for z0, z1, win in zones:
        if z1 <= zmin:
            continue
        z0c = max(z0, zmin)
        for i in range(nb):
            a, b = s_from + i * w, s_from + (i + 1) * w
            if skip and skip(path, (a + b) / 2, z0, z1):
                continue
            if isinstance(win, int):
                wall_rect(mb, path, a, b, z0c, z1, win)
            elif win is None or z0 < zmin or (bay_filter and not bay_filter(path, (a + b) / 2)):
                wall_rect(mb, path, a, b, z0c, z1, M['wall'])
            else:
                facade_cell(mb, glass, frame, path, a, b, z0, z1, win, M, tag=z0 / 160)


# ------------------------------------------------------------------ mouldings
def sweep_profile(mb, poly, z, prof, m, closed=True, cap=True):
    """Sweep an (out, dz) profile along a plan polyline (CCW for closed; outward = right side)."""
    pts = [v2(p) for p in poly]
    n = len(pts)
    rings = []
    for i in range(n):
        if closed:
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        else:
            a = pts[i - 1] if i > 0 else pts[i] - (pts[1] - pts[0])
            b = pts[i]
            c = pts[i + 1] if i < n - 1 else pts[i] + (pts[-1] - pts[-2])
        t1, t2 = (b - a).normalized(), (c - b).normalized()
        n1, n2 = Vector((t1.y, -t1.x)), Vector((t2.y, -t2.x))
        mv = (n1 + n2)
        mv = mv.normalized() if mv.length > 1e-6 else n1
        k = 1 / max(mv.dot(n1), .25)
        rings.append([(b.x + mv.x * o * k, b.y + mv.y * o * k, z + dz) for o, dz in prof])
    cnt = n if closed else n - 1
    for i in range(cnt):
        j = (i + 1) % n
        for k in range(len(prof) - 1):
            mb.quad(rings[i][k], rings[j][k], rings[j][k + 1], rings[i][k + 1], m)
    if cap and not closed:
        for r, rev in ((rings[0], True), (rings[-1], False)):
            mb.poly(list(reversed(r)) if rev else r, m)


def circle_pts(c, r, n=48, a0=0.0, a1=TAU):
    full = abs(a1 - a0 - TAU) < 1e-6
    k = n if full else n + 1
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * i / n), c[1] + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(k)]


def hip_roof(mb, quad, z, pitch_deg, m, eave=.6):
    """Hip roof over a convex quad (CCW). Ridge runs along the longer axis."""
    q = [v2(p) for p in offset_closed(ccw(quad), eave)]
    e = [(q[(i + 1) % 4] - q[i]).length for i in range(4)]
    k = 0 if e[0] + e[2] >= e[1] + e[3] else 1     # long edges are k and k+2
    a, b, c, d = q[k], q[(k + 1) % 4], q[(k + 2) % 4], q[(k + 3) % 4]
    w = ((d - a).length + (c - b).length) / 2
    h = w / 2 * math.tan(math.radians(pitch_deg))
    m_ad, m_bc = (a + d) / 2, (b + c) / 2
    ax = (m_bc - m_ad)
    Lr = ax.length
    ax.normalize()
    inset = min(w / 2, Lr / 2 - .01)
    r0, r1 = m_ad + ax * inset, m_bc - ax * inset
    A, B, C, D = [(p.x, p.y, z) for p in (a, b, c, d)]
    R0, R1 = (r0.x, r0.y, z + h), (r1.x, r1.y, z + h)
    mb.quad(A, B, R1, R0, m)
    mb.quad(C, D, R0, R1, m)
    mb.tri(B, C, R1, m)
    mb.tri(D, A, R0, m)
    mb.poly([D, C, B, A], m)   # soffit
    return h


def extrude_poly(mb, poly, z0, z1, m_side, m_top=None, top=True, bottom=False):
    poly = ccw(poly)
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        mb.quad((a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1), m_side)
    if top:
        mb.poly([(p[0], p[1], z1) for p in poly], m_top if m_top is not None else m_side)
    if bottom:
        mb.poly([(p[0], p[1], z0) for p in reversed(poly)], m_side)


def balustrade(mb, pts, z, m, h=1.05, spacing=.32, closed=False):
    """Rail + plinth + turned balusters (octagonal prisms) along a polyline."""
    pts = [v2(p) for p in pts]
    segs = list(zip(pts, pts[1:])) + ([(pts[-1], pts[0])] if closed else [])
    for a, b in segs:
        L = (b - a).length
        if L < .05:
            continue
        A, B = a.to_3d(), b.to_3d()
        mb.box_between(A + Vector((0, 0, z + .09)), B + Vector((0, 0, z + .09)), .36, .18, m)
        mb.box_between(A + Vector((0, 0, z + h - .07)), B + Vector((0, 0, z + h - .07)), .34, .14, m)
        n = max(1, int(L / spacing))
        t = (b - a) / L
        for i in range(n):
            p = a + t * (L * (i + .5) / n)
            mb.cylinder((p.x, p.y, z + .18), .07, h - .32, n=6, m=m, r_top=.05, cap=False)
