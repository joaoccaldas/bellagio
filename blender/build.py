"""Bake + export for the browser twin.

STAGE=bake : build everything, bake day/night lightmaps per group, export out/bellagio.glb + out/manifest.json
Env: RES_<GROUP> (lightmap size), SPP, GROUPS (comma list to bake), OUT
"""
import sys, os, math, time, json
sys.path.insert(0, os.path.dirname(__file__))
import bpy
import numpy as np
from mathutils import Vector

OUT = os.environ.get('OUT', os.path.join(os.path.dirname(__file__), '..', 'out'))
SPP = int(os.environ.get('SPP', 384))
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
import survey as S, mats, tower, grounds, interior, penthouse, fountains, luxor, city

sc = bpy.context.scene
sc.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'; prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == 'METAL'
sc.cycles.device = 'GPU'
sc.view_settings.view_transform = 'Standard'

t0 = time.time()
M = mats.build()
coll = bpy.data.collections.new('BELLAGIO'); sc.collection.children.link(coll)
tower.build(coll, M); tower.build_spa(coll, M)
gobjs, trees, protos = grounds.build(coll, M)
interior.build(coll, M)
penthouse.build(coll, M)
luxor.build(coll, M)
city.build(coll, M)
print('BUILT', round(time.time() - t0, 1), 's', len(bpy.data.objects), 'objects')

# ------------------------------------------------------------------ lights
world = bpy.data.worlds.new('W'); sc.world = world
nt = world.node_tree
bg = nt.nodes['Background']
sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'; sky.sun_disc = False; sky.altitude = 610
sun_el, sun_az = math.radians(38), math.radians(118)
sky.sun_elevation = sun_el; sky.sun_rotation = math.radians(90) - sun_az + math.pi / 2
night_ramp = nt.nodes.new('ShaderNodeValToRGB')
tcw = nt.nodes.new('ShaderNodeTexCoord'); sepw = nt.nodes.new('ShaderNodeSeparateXYZ')
nt.links.new(tcw.outputs['Generated'], sepw.inputs['Vector']); nt.links.new(sepw.outputs['Z'], night_ramp.inputs['Fac'])
night_ramp.color_ramp.elements[0].color = (.03, .02, .012, 1); night_ramp.color_ramp.elements[1].position = .22
night_ramp.color_ramp.elements[1].color = (.0015, .0022, .0055, 1)
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.4; sd.angle = math.radians(.55); sd.color = (1, .96, .9)
sun = bpy.data.objects.new('sun', sd); sc.collection.objects.link(sun)
sun.rotation_euler = Vector((math.sin(sun_az) * math.cos(sun_el), math.cos(sun_az) * math.cos(sun_el), math.sin(sun_el))).to_track_quat('Z', 'Y').to_euler()


def add_light(name, kind, loc, energy, color, size=None, size_y=None):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    if kind == 'AREA':
        ld.shape = 'RECTANGLE'; ld.size = size; ld.size_y = size_y or size
    o = bpy.data.objects.new(name, ld); sc.collection.objects.link(o); o.location = loc
    return o


# interior lights (on in both states)
for i, (x, y) in enumerate([(35, -94), (55, -94), (35, -106), (55, -106)]):
    add_light(f'lob{i}', 'AREA', (x, y, 9.3), 6000, (1, .85, .65), 7)
add_light('chi', 'AREA', (S.CHIHULY[0], S.CHIHULY[1], 11.7), 5000, (1, .96, .9), 19, 8.5)
for i in range(6):
    add_light(f'cons{i}', 'AREA', (-37 + i * 7, -100, 16), 1500, (1, .88, .7), 5)
for wk, W in penthouse.WINGS.items():
    s = 14.0
    while s < W.L - 4:
        zc = (penthouse.CEIL_MAIN - 4.1 if s < W.L1 else penthouse.CEIL_END - .6)
        add_light(f'ph_{wk}_{s:.0f}', 'AREA', W.at(s, 0, zc), 1800, (1, .86, .68), 4)
        s += 8.0
add_light('ph_rot', 'POINT', (S.CORE[0], S.CORE[1], penthouse.FL + 20), 12000, (1, .85, .6))


FLOODS = []
for i, (loc, d) in enumerate(tower.floodlights()):
    ld = bpy.data.lights.new(f'flood{i}', 'SPOT'); ld.energy = 5200; ld.color = (1.0, .78, .48)
    ld.spot_size = math.radians(70); ld.spot_blend = .8; ld.shadow_soft_size = .4
    lo = bpy.data.objects.new(ld.name, ld); sc.collection.objects.link(lo); lo.location = loc
    lo.rotation_euler = Vector(d).to_track_quat('-Z', 'Y').to_euler(); FLOODS.append(lo)


def set_state(night):
    mats.set_night(night)
    for lo in FLOODS:
        lo.hide_render = not night
    sun.hide_render = night
    for l in list(nt.links):
        if l.to_node == bg:
            nt.links.remove(l)
    nt.links.new((night_ramp if night else sky).outputs[0], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 1.0 if night else .35


# ------------------------------------------------------------------ groups
def group_of(o):
    n = o.name
    if o.type != 'MESH' or o.get('nobake') or o.get('emit') or n.startswith(('GLASS', 'WATER', 'EMIT', 'DYN', 'TREE', 'tree_', 'FOUNTAIN', 'CHIHULY')):
        return None
    if n.endswith('_frame') or n in ('steel_frames',):
        return None                                   # mullions / steel: real-time
    if n.startswith(('tower_', 'spa_')):
        return 'TOWER'
    if n.startswith(('village_', 'rocks', 'lake_rail', 'lamp_posts', 'dome_shells', 'pools')):
        return 'VILLAGE'
    if n.startswith(('int_', 'floor_')):
        return 'INTERIOR'
    if n.startswith('ph_'):
        return 'PENTHOUSE'
    if n.startswith('LUXOR_'):
        return 'LUXOR'
    return 'SITE'


RES = {'TOWER': 4096, 'SITE': 4096, 'VILLAGE': 4096, 'INTERIOR': 4096, 'PENTHOUSE': 4096, 'LUXOR': 2048}
for k in RES:
    RES[k] = int(os.environ.get('RES_' + k, RES[k]))
GAIN = {'TOWER': 1.0, 'SITE': 1.0, 'VILLAGE': 1.0, 'INTERIOR': 1.0, 'PENTHOUSE': 1.0}


def select_only(objs, active=None):
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        if o and o.name in bpy.context.view_layer.objects:
            o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]


def encode_save(img, path, scale):
    """Linear HDR -> 8-bit with a soft shoulder: e = x/(x+scale) then sRGB-ish sqrt.
    Browser inverts: x = scale * e2/(1-e2), e2 = e^2."""
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    rgb = np.clip(px.reshape(-1, 4)[:, :3], 0, None)
    e = np.sqrt(rgb / (rgb + scale))
    out = bpy.data.images.new(os.path.basename(path), w, h, alpha=False)
    out.colorspace_settings.name = 'Non-Color'
    o = np.ones((w * h, 4), dtype=np.float32)
    o[:, :3] = e
    out.pixels.foreach_set(o.ravel())
    out.filepath_raw = path
    out.file_format = 'PNG'
    out.save()


def bake_group(name, objs, states):
    objs = [o for o in objs if len(o.data.polygons)]
    select_only(objs)
    bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.name = 'BAKED_' + name
    me = j.data
    lm = me.uv_layers.new(name='LM')
    me.uv_layers.active = lm
    t = time.time()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    nf = len(me.polygons)
    if nf > 250000:
        bpy.ops.uv.lightmap_pack(PREF_CONTEXT='ALL_FACES', PREF_PACK_IN_ONE=True, PREF_MARGIN_DIV=.25)
    else:
        bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=.001, area_weight=0, correct_aspect=True, scale_to_bounds=False)
        bpy.ops.uv.pack_islands(margin=.003, rotate=True, shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    import numpy as _np
    _a = _np.empty(len(me.loops) * 2); me.uv_layers['LM'].data.foreach_get('uv', _a); _a = _a.reshape(-1, 2)
    print('UV', name, nf, 'faces', round(time.time() - t, 1), 's', 'bbox', _a.min(0).round(3).tolist(), _a.max(0).round(3).tolist())
    res = RES[name]
    img = bpy.data.images.new('LM_' + name, res, res, float_buffer=True, alpha=False)
    mset = {m for m in me.materials if m}
    for m in mset:
        n = m.node_tree.nodes.new('ShaderNodeTexImage'); n.image = img; n.name = 'BAKE_TARGET'
        m.node_tree.nodes.active = n
    sc.cycles.samples = SPP
    sc.cycles.use_denoising = False
    for suffix, night in states:
        set_state(night)
        t = time.time()
        bpy.ops.object.bake(type='COMBINED', pass_filter={'EMIT', 'DIRECT', 'INDIRECT', 'DIFFUSE', 'TRANSMISSION'}, margin=16, use_clear=True)
        print('BAKED', name + suffix, round(time.time() - t, 1), 's')
        encode_save(img, f'{OUT}/lm_{name.lower()}{suffix}.png', 1.0)
    for m in mset:
        n = m.node_tree.nodes.get('BAKE_TARGET')
        if n:
            m.node_tree.nodes.remove(n)
    # keep only the lightmap UVs; one material per atlas
    for l in [l for l in me.uv_layers if l.name != 'LM']:
        me.uv_layers.remove(l)
    me.materials.clear()
    me.materials.append(bpy.data.materials.new('baked_' + name.lower()))
    j['baked'] = name.lower()
    return j


def apply_modifiers():
    pass


groups = {}
for o in list(coll.all_objects):
    g = group_of(o)
    if g:
        groups.setdefault(g, []).append(o)
only = [g for g in os.environ.get('GROUPS', ','.join(RES)).split(',') if g]
for g, objs in groups.items():
    if g not in only:
        continue
    print('GROUP', g, len(objs), 'objects')
    bake_group(g, objs, [('_day', False), ('_night', True)])
set_state(False)

# ------------------------------------------------------------------ reflection panoramas
def panorama(path, night, loc=(70.0, -30.0, 45.0)):
    set_state(night)
    cam = bpy.data.objects.new('PANO', bpy.data.cameras.new('PANO')); sc.collection.objects.link(cam)
    cam.data.type = 'PANO'; cam.data.panorama_type = 'EQUIRECTANGULAR'
    cam.location = loc; cam.rotation_euler = (math.pi / 2, 0, -math.pi / 2)
    sc.camera = cam
    sc.render.image_settings.file_format = 'HDR'
    sc.render.resolution_x, sc.render.resolution_y = 1024, 512
    sc.cycles.samples = 96; sc.cycles.use_denoising = True
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)


if int(os.environ.get('PANO', 1)):
    panorama(f'{OUT}/env_day.hdr', False)
    panorama(f'{OUT}/env_night.hdr', True)
set_state(False)

# ------------------------------------------------------------------ export
for o in [o for o in coll.all_objects if o.name.startswith('tree_')]:
    bpy.data.objects.remove(o)
for o in protos.values():
    o.location.z = 0
NOEXPORT = ('GLASS_chihuly', 'tower_frame', 'spa_frame', 'village_frame')
for o in [o for o in bpy.data.objects if o.name.startswith(NOEXPORT)]:
    bpy.data.objects.remove(o)
exp = [o for o in bpy.data.objects if o.type == 'MESH' and o.users]
select_only(exp)
bpy.ops.export_scene.gltf(filepath=f'{OUT}/bellagio.glb', export_format='GLB', use_selection=True, export_apply=True,
                          export_extras=True, export_yup=True, export_texcoords=True, export_normals=True,
                          export_vertex_color='ACTIVE', export_materials='EXPORT', export_image_format='NONE',
                          export_lights=False, export_cameras=False,
                          export_meshopt_compression_enable=bool(int(os.environ.get('MESHOPT', 1))))
man = {
    'nozzles': S.fountain_nozzles(), 'trees': trees, 'lake_level': S.LAKE_LEVEL, 'core': S.CORE,
    'lift': {'x': penthouse.LIFT.x, 'y': penthouse.LIFT.y, 'top': penthouse.FL}, 'penthouse': {'fl': penthouse.FL, 'terrace': penthouse.TERRACE},
    'chihuly': S.CHIHULY, 'chihuly_pieces': interior.PIECES, 'lobby': S.LOBBY_BOX, 'conservatory': S.CONS_BOX, 'passage': S.PASSAGE, 'strip_x': S.STRIP_X,
    'wings': {k: {'p': [list(p) for p in W.p], 'w': W.w, 'L1': W.L1, 'L': W.L} for k, W in penthouse.WINGS.items()},
}
json.dump(man, open(f'{OUT}/manifest.json', 'w'))
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/bellagio_master.blend')
print('DONE', round(time.time() - t0, 1), 's')
