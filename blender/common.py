import bpy, bmesh, math
from mathutils import Vector

MATS = {}


def mat(name, color=(.5, .5, .5), metal=0.0, rough=.5, coat=0.0, emit=None, strength=0.0, alpha=1.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = coat
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = strength
    MATS[name] = m
    return m


def link(obj, parent=None, coll=None):
    (coll or bpy.context.scene.collection).objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def empty(name, parent=None):
    o = bpy.data.objects.new(name, None)
    return link(o, parent, parent.users_collection[0] if parent else None)


def set_parent(o, p):
    o.parent = p


def obj_from(name, verts, faces, face_uvs=None, mats=None, parent=None, sharp_angle=None, coll=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    if face_uvs:
        uv = me.uv_layers.new(name='UVMap')
        k = 0
        for poly, fu in zip(me.polygons, face_uvs):
            for li, c in zip(poly.loop_indices, fu):
                uv.data[li].uv = c
    me.validate(clean_customdata=False)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = smooth
    if sharp_angle is not None:
        lim = math.radians(sharp_angle)
        for e in bm.edges:
            if len(e.link_faces) == 2 and e.calc_face_angle(0) > lim:
                e.smooth = False
    bm.to_mesh(me)
    bm.free()
    for m in (mats or []):
        me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    c = coll or (parent.users_collection[0] if parent is not None else bpy.context.scene.collection)
    c.objects.link(o)
    if parent is not None:
        o.parent = parent
    return o


def loft(rings, closed=True, u_vals=None, v_vals=None, cap0=False, cap1=False):
    n, m = len(rings), len(rings[0])
    verts = [p.copy() if hasattr(p, 'copy') else Vector(p) for r in rings for p in r]
    faces, fuv = [], []
    cols = m if closed else m - 1
    for i in range(n - 1):
        u0 = u_vals[i] if u_vals else i / (n - 1)
        u1 = u_vals[i + 1] if u_vals else (i + 1) / (n - 1)
        for j in range(cols):
            j2 = (j + 1) % m
            a, b, c, d = i * m + j, i * m + j2, (i + 1) * m + j2, (i + 1) * m + j
            v0 = v_vals[j] if v_vals else j / cols
            v1 = v_vals[j + 1] if v_vals else (j + 1) / cols
            faces.append((a, b, c, d))
            fuv.append(((u0, v0), (u0, v1), (u1, v1), (u1, v0)))
    for cap, ri in ((cap0, 0), (cap1, n - 1)):
        if cap:
            ids = [ri * m + j for j in range(m)]
            ctr = sum((verts[k] for k in ids), Vector()) / m
            ci = len(verts)
            verts.append(ctr)
            for j in range(m):
                a, b = ids[j], ids[(j + 1) % m]
                faces.append((a, b, ci))
                fuv.append(((.5 + .5 * math.cos(j / m * 6.283), .5 + .5 * math.sin(j / m * 6.283)),
                            (.5 + .5 * math.cos((j + 1) / m * 6.283), .5 + .5 * math.sin((j + 1) / m * 6.283)), (.5, .5)))
    return verts, faces, fuv


def superellipse(ry, rz, n=48, e=2.0):
    out = []
    for i in range(n):
        t = i / n * 2 * math.pi
        c, s = math.cos(t), math.sin(t)
        out.append((ry * math.copysign(abs(s) ** (2 / e), s), rz * math.copysign(abs(c) ** (2 / e), c)))
    return out


def prism(name, poly, x0, x1, material, parent=None, coll=None):
    # make CCW
    area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    if area < 0:
        poly = list(reversed(poly))
    n = len(poly)
    verts = [Vector((x0, y, z)) for y, z in poly] + [Vector((x1, y, z)) for y, z in poly]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    fuv = []
    for f in faces:
        fuv.append([(.5 + verts[k].y * 10, .5 + verts[k].z * 10) for k in f])
    return obj_from(name, verts, faces, fuv, [material], parent=parent, coll=coll, smooth=False)


def sweep(pts, radius, sides=10, flat=(1.0, 1.0), axis=None, closed=False, twist_ref=None):
    """Tube along a polyline. flat=(a,b) scales the section; axis fixes the section's 'b' direction."""
    rings, us = [], []
    n = len(pts)
    prev_n = None
    total = 0
    lens = [0]
    for i in range(1, n):
        total += (pts[i] - pts[i - 1]).length
        lens.append(total)
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        if closed and (i == 0 or i == n - 1):
            a, b = pts[-2], pts[1]
        t = (b - a).normalized()
        if axis is not None:
            nb = axis.normalized()
            nn = t.cross(nb).normalized()
            nb = nn.cross(t).normalized()
        else:
            if prev_n is None:
                ref = Vector((0, 0, 1)) if abs(t.z) < .9 else Vector((0, 1, 0))
                nn = t.cross(ref).normalized()
            else:
                nn = (prev_n - t * prev_n.dot(t)).normalized()
            prev_n = nn
            nb = t.cross(nn).normalized()
        u = lens[i] / max(total, 1e-9)
        r = radius(u)
        ring = []
        for j in range(sides):
            th = j / sides * 2 * math.pi
            ring.append(p + nn * (math.cos(th) * r * flat[0]) + nb * (math.sin(th) * r * flat[1]))
        rings.append(ring)
        us.append(u)
    return loft(rings, closed=True, u_vals=us, cap0=not closed, cap1=not closed)


def lemniscate_lobe(a, zscale, lobe, n):
    pts = []
    for i in range(n):
        t = -math.pi / 2 + math.pi * i / n
        d = 1 + math.sin(t) ** 2
        pts.append((lobe * a * math.cos(t) / d, zscale * a * math.sin(t) * math.cos(t) / d))
    return pts


def offset_poly(pts, d, inward=True):
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    sgn = 1 if area > 0 else -1
    out = []
    for i in range(n):
        a, b = pts[i - 1], pts[(i + 1) % n]
        ty, tz = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(ty, tz) or 1
        # left normal of CCW polygon points inward
        ny, nz = -tz / ln * sgn, ty / ln * sgn
        k = d if inward else -d
        out.append((pts[i][0] + ny * k, pts[i][1] + nz * k))
    return out
