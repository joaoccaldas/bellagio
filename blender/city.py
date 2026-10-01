"""Las Vegas base layer in the Bellagio survey frame (+X east, +Y north, metres).

Valley and Strip orthophotos (ESRI World Imagery) plus OpenStreetMap building footprints
extruded to their true architectural heights. This expands 3D outwards from Bellagio and Luxor
across the entire Strip corridor and valley, keeping all geometry batched into 4 zero-overhead draw calls.
"""
import json, os, math
import bpy
from geo import MB, extrude_poly, ccw, hip_roof

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
LUXOR_DATA = os.path.join(HERE, "..", "luxor", "data")

# Hero geometry that OSM must not rebuild (Bellagio campus, Eiffel Tower, Luxor)
KEEP = [
    (-170, -265, 305, 175),   # Bellagio campus (tower, spa tower, lake, villas, pools)
    (360, -90, 420, -40),     # Paris Eiffel Tower (built in grounds.py)
    (-42, -2034, 154, -1838), # Luxor pyramid
    (-40, -1858, 200, -1748), # Luxor ziggurat towers
    (140, -2000, 315, -1870), # Luxor front plaza (Sphinx & Obelisk hero geometry)
]


def _inside(x, y, r):
    return r[0] <= x <= r[2] and r[1] <= y <= r[3]


def _uv(o, x0, y0, sx, sy):
    me = o.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for li, lp in enumerate(me.loops):
        co = me.vertices[lp.vertex_index].co
        uv.data[li].uv = ((co.x - x0) / sx, (co.y - y0) / sy)


def _plate(name, path, meta, z, mat_name, coll):
    if not os.path.exists(path):
        print("CITY missing", path)
        return None
    x0, y0, sx, sy = meta["x0"], meta["y0"], meta["sx"], meta["sy"]
    m = bpy.data.materials.new(mat_name)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = .92
    t = m.node_tree.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path, check_existing=True)
    t.extension = "CLIP"
    uv = m.node_tree.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"
    m.node_tree.links.new(uv.outputs["UV"], t.inputs["Vector"])
    m.node_tree.links.new(t.outputs["Color"], b.inputs["Base Color"])
    ring = [(x0, y0), (x0 + sx, y0), (x0 + sx, y0 + sy), (x0, y0 + sy)]
    from grounds import curve_fill
    o = curve_fill(name, ring, [], z, m, coll)
    _uv(o, x0, y0, sx, sy)
    o["nobake"] = 1
    o["ground"] = name.replace("CITY_ground_", "")
    return o


def ground(coll):
    out = []
    specs = [
        ("CITY_ground_wide", os.path.join(DATA, "city_wide.jpg"), os.path.join(DATA, "city_wide.json"), -0.045),
        ("CITY_ground_valley", os.path.join(DATA, "city_valley.jpg"), os.path.join(DATA, "city_valley.json"), -0.035),
        ("CITY_ground_strip", os.path.join(DATA, "city_strip.jpg"), os.path.join(DATA, "city_strip.json"), -0.025),
        ("CITY_ground_luxor", os.path.join(LUXOR_DATA, "luxor_sat.jpg"), os.path.join(LUXOR_DATA, "luxor_sat.json"), -0.015),
    ]
    for name, path, meta_path, z in specs:
        if not os.path.exists(meta_path):
            continue
        meta = json.load(open(meta_path))
        if "x0" not in meta:   # luxor_sat.json is centre/half
            c, h = meta["center"], meta["half"]
            meta = {"x0": c[0] - h, "y0": c[1] - h, "sx": 2 * h, "sy": 2 * h}
        o = _plate(name, path, meta, z, "m_" + name, coll)
        if o:
            out.append(o)
    return out


def _mats(M):
    from mats import windows_grid, principled
    if "city_glass" not in M:
        windows_grid("city_glass", (.05, .055, .06), (.012, .016, .02))
        g = M["city_glass"].node_tree.nodes["Principled BSDF"]
        g.inputs["Metallic"].default_value = .55
        g.inputs["Roughness"].default_value = .18
    if "city_gold" not in M:
        windows_grid("city_gold", (.65, .50, .15), (.08, .06, .02))
        g = M["city_gold"].node_tree.nodes["Principled BSDF"]
        g.inputs["Metallic"].default_value = .82
        g.inputs["Roughness"].default_value = .12
    if "city_castle" not in M:
        windows_grid("city_castle", (.62, .48, .32), (.22, .07, .05))
    if "city_block" not in M:
        windows_grid("city_block", (.42, .40, .37), (.03, .035, .04))
    if "city_steel" not in M:
        principled("city_steel", (.78, .80, .82), rough=.32, metal=.72)
    if "city_coaster" not in M:
        principled("city_coaster", (.85, .08, .06), rough=.22, metal=.35)
    if "city_neon" not in M:
        principled("city_neon", (1.0, .88, .32), rough=.4, emit=(1.0, .88, .32), strength=3.5)
    return (M["city_block"], M["city_glass"], M["city_castle"], M["city_gold"],
            M["city_steel"], M["city_coaster"], M["city_neon"])


def massing(coll, M):
    from asof import built_footprints
    raw = built_footprints()
    if not raw:
        print("CITY no buildings")
        return []
    block, glass, castle, gold, steel, coaster, neon = _mats(M)
    mb = {
        "block": MB("CITY_block", [block]),
        "glass": MB("CITY_glass", [glass]),
        "castle": MB("CITY_castle", [castle]),
        "gold": MB("CITY_gold", [gold]),
        "steel": MB("CITY_steel", [steel]),
        "coaster": MB("CITY_coaster", [coaster]),
        "neon": MB("CITY_neon", [neon]),
    }
    n = 0
    for b in raw:
        cx, cy = b["c"]
        if any(_inside(cx, cy, r) for r in KEEP):
            continue
        ring = b["r"]
        if len(ring) < 3:
            continue
        h = float(b["h"])
        k = b.get("k", "block")
        if k not in mb:
            k = "glass" if k == "gold" else "block"
        name = (b.get("name") or "").lower()

        # Primary building body extrusion
        extrude_poly(mb[k], ccw(ring), 0.0, h, 0, 0)
        n += 1

        # Landmark-specific 3D architectural silhouettes
        # 1. Excalibur Hotel & Casino: conical spires and corner turrets
        if "excalibur" in name and h >= 50:
            # Conical spires on corners
            for pt in ring[::max(1, len(ring)//6)]:
                mb["castle"].cylinder((pt[0], pt[1], h), 3.2, 14.0, n=8, m=0, r_top=0.1)
            # Center grand turret
            mb["castle"].cylinder((cx, cy, h), 5.5, 20.0, n=8, m=0, r_top=0.1)

        # 2. New York-New York: Empire State spire and Chrysler stepped crowns
        elif "new york" in name and h >= 100:
            # Empire State stepped crown and mooring mast
            mb["glass"].box((cx, cy, h + 5), (18, 18, 10), 0)
            mb["glass"].box((cx, cy, h + 12), (12, 12, 6), 0)
            mb["glass"].cylinder((cx, cy, h + 15), 1.8, 22.0, n=8, m=0, r_top=0.3)
            # Chrysler sunburst spire
            mb["glass"].cylinder((cx + 22, cy + 12, h - 8), 7.0, 16.0, n=8, m=0, r_top=0.4)

        # 3. Mandalay Bay: golden mechanical penthouse crown
        elif "mandalay" in name and h >= 100:
            mb["gold"].box((cx, cy, h + 4.5), (36, 36, 9), 0)

        # 4. The STRAT: observation pod and needle spire
        elif ("stratosphere" in name or "the strat" in name) and h >= 150:
            # Tower shaft up to 260m
            mb["block"].cylinder((cx, cy, 0), 12.0, 260.0, n=16, m=0, r_top=8.5)
            # Observation pod (260m - 286m)
            mb["glass"].cylinder((cx, cy, 260.0), 28.0, 26.0, n=24, m=0, r_top=25.0)
            # Thrill-ride antenna mast (286m - 350m)
            mb["block"].cylinder((cx, cy, 286.0), 4.2, 64.0, n=8, m=0, r_top=0.5)

        # 5. Caesars Palace: Roman classical pediments
        elif any(cp in name for cp in ("caesar", "augustus", "octavius")) and h >= 70:
            mb["block"].box((cx, cy, h + 3), (28, 20, 6), 0)

        # 6. Paris Las Vegas: mansard roofline
        elif "paris" in name and h >= 90:
            mb["block"].box((cx, cy, h + 4), (26, 26, 8), 0)

        # 7. Aria / Vdara: curved rooftop mechanical screens
        elif "aria" in name and h >= 100:
            mb["glass"].box((cx, cy, h + 4), (32, 22, 8), 0)

    print("CITY buildings extruded:", n)
    try:
        import landmarks
        landmarks.build_all(mb)
        print("CITY Strip landmarks built")
    except Exception as e:
        print("CITY landmarks error:", e)
    out = []
    for k, m in mb.items():
        o = m.build(coll)
        if o:
            o["nobake"] = 1
            o["city"] = k
            out.append(o)
    return out


def build(coll, M):
    return ground(coll) + massing(coll, M)
