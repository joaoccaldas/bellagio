import sys, os, math, time
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
import survey as S, mats, tower
OUT = os.environ.get('OUT', os.path.join(os.path.dirname(__file__), '..', 'renders'))
SPP = int(os.environ.get('SPP', 48))
RES = [int(x) for x in os.environ.get('RES', '1280x720').split('x')]
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'; prefs.get_devices()
for d in prefs.devices: d.use = d.type == 'METAL'
sc.cycles.device = 'GPU'
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = -1.1
M = mats.build()
coll = bpy.data.collections.new('BELLAGIO'); sc.collection.children.link(coll)
t0 = time.time()
tower.build(coll, M); tower.build_spa(coll, M)
print('tower built', round(time.time() - t0, 1), 's')
import grounds
gobjs, trees, protos = grounds.build(coll, M)
import interior
iobjs = interior.build(coll, M)
import luxor
luxor.build(coll, M)
import city
city.build(coll, M)
import fountains
FNT = os.environ.get('FOUNTAIN', '')
if FNT:
    M['spray'] = fountains.spray_material()
    fountains.build(coll, M['spray'], FNT)
NIGHTMODE = os.environ.get('LIGHTING', 'day') == 'night'
PH = os.environ.get('PENTHOUSE', '1') == '1'
if PH:
    import penthouse as PHM
    PHM.build(coll, M)
    for wk, W in PHM.WINGS.items():
        s = 14.0
        while s < W.L - 4:
            zc = (PHM.CEIL_MAIN - 4.1 if s < W.L1 else PHM.CEIL_END - .6)
            ld = bpy.data.lights.new(f'ph_{wk}_{s:.0f}', 'AREA'); ld.energy = 1800; ld.size = 4; ld.color = (1, .86, .68)
            lo = bpy.data.objects.new(ld.name, ld); sc.collection.objects.link(lo); lo.location = W.at(s, 0, zc)
            s += 8.0
    ld = bpy.data.lights.new('ph_rot', 'POINT'); ld.energy = 12000; ld.shadow_soft_size = 2; ld.color = (1, .85, .6)
    lo = bpy.data.objects.new('ph_rot', ld); sc.collection.objects.link(lo); lo.location = (S.CORE[0], S.CORE[1], PHM.FL + 20)
print('grounds built', round(time.time() - t0, 1), 's', len(trees), 'trees')
# sky
world = bpy.data.worlds.new('W'); sc.world = world
nt = world.node_tree
sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'
sun_el, sun_az = math.radians(38), math.radians(118)     # ~10:00 in Las Vegas, facade in sun
sky.sun_elevation = sun_el; sky.sun_rotation = math.radians(90) - sun_az + math.pi / 2
sky.altitude = 610; sky.sun_disc = False
nt.links.new(sky.outputs[0], nt.nodes['Background'].inputs[0])
nt.nodes['Background'].inputs[1].default_value = .35
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.4; sd.angle = math.radians(.55); sd.color = (1, .96, .9)
so = bpy.data.objects.new('sun', sd); sc.collection.objects.link(so)
dvec = Vector((math.sin(sun_az) * math.cos(sun_el), math.cos(sun_az) * math.cos(sun_el), math.sin(sun_el)))
so.rotation_euler = dvec.to_track_quat('Z', 'Y').to_euler()

for i, (x, y) in enumerate([(35, -94), (55, -94), (35, -106), (55, -106)]):
    ld = bpy.data.lights.new(f'lob{i}', 'AREA'); ld.energy = 6000; ld.size = 7; ld.color = (1, .85, .65)
    lo = bpy.data.objects.new(f'lob{i}', ld); sc.collection.objects.link(lo); lo.location = (x, y, 9.3)
ld = bpy.data.lights.new('chi', 'AREA'); ld.energy = 5000; ld.shape = 'RECTANGLE'; ld.size = 19; ld.size_y = 8.5; ld.color = (1, .96, .9)
lo = bpy.data.objects.new('chi', ld); sc.collection.objects.link(lo); lo.location = (S.CHIHULY[0], S.CHIHULY[1], 11.7)


def cam(name, loc, tgt, lens):
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(c)
    c.location = loc; c.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    c.data.lens = lens; c.data.clip_end = 5000
    return c
views = {
    'front_lake': cam('front_lake', (259, 6, 3.2), (0, 0, 64), 26),
    'aerial_se': cam('aerial_se', (520, -430, 330), (40, -10, 40), 35),
    'low_close': cam('low_close', (175, -14, 3), (0, 0, 95), 18),
    'night_front': cam('night_front', (273, 4, 2.4), (0, 0, 70), 24),
    'fountain_side': cam('fountain_side', (272, -175, 3.0), (110, 0, 40), 26),
    **({} if not PH else {
        'ph_salon': cam('ph_salon', PHM.WINGS['N'].at(14.5, -6.0, PHM.FL + 1.7), PHM.WINGS['N'].at(40, 3.0, PHM.FL + 4.5), 16),
        'ph_bedroom': cam('ph_bedroom', PHM.WINGS['W'].at(44, 6.0, PHM.FL + 1.7), PHM.WINGS['W'].at(62, -6.0, PHM.FL + 2.6), 16),
        'ph_spa': cam('ph_spa', PHM.WINGS['S'].at(37, -6.5, PHM.FL + 1.7), PHM.WINGS['S'].at(62, 5.0, PHM.FL + 2.5), 16),
        'ph_library': cam('ph_library', PHM.WINGS['W'].at(13.5, 3.0, PHM.FL + 1.7), PHM.WINGS['W'].at(34, -1.0, PHM.FL + 4.0), 16),
        'ph_bar': cam('ph_bar', PHM.WINGS['N'].at(PHM.WINGS['N'].L1 + 1.5, 5.5, PHM.FL + 1.6), PHM.WINGS['N'].at(PHM.WINGS['N'].L1 + 14, -4.5, PHM.FL + 1.6), 16),
        'ph_rotunda': cam('ph_rotunda', (S.CORE[0] + 7.4, S.CORE[1] - 2.0, PHM.FL + 1.7), (S.CORE[0], S.CORE[1], PHM.FL + 16), 14),
        'ph_terrace': cam('ph_terrace', (S.CORE[0] + 12, S.CORE[1] + 6, PHM.TERRACE + 1.7), (S.CORE[0] + 200, S.CORE[1] - 30, 40), 22),
        'ph_terrace_back': cam('ph_terrace_back', (S.CORE[0] + 22, S.CORE[1] - 5, PHM.TERRACE + 1.7), (S.CORE[0], S.CORE[1], PHM.TERRACE + 6), 18),
    }),
    'luxor': cam('luxor', (420, -1780, 40), (60, -1938, 50), 28),
    'luxor_sphinx': cam('luxor_sphinx', (280, -1905, 6), (190, -1935, 18), 24),
    'luxor_aerial': cam('luxor_aerial', (520, -1500, 420), (40, -2000, 20), 28),
    'strip_south': cam('strip_south', (900, -600, 520), (80, -1600, 30), 32),
    'lobby': cam('lobby', (64.5, -109.5, 1.65), (40, -97, 8.8), 16),
    'chihuly_up': cam('chihuly_up', (40, -103, 1.6), (47, -99.5, 11), 18),
    'conservatory': cam('conservatory', (-1.0, -97.5, 1.7), (-30, -101, 6.5), 17),
}
if NIGHTMODE:
    mats.set_night(True)
    for i, (loc, d) in enumerate(tower.floodlights()):
        ld = bpy.data.lights.new(f'flood{i}', 'SPOT'); ld.energy = 5200; ld.color = (1.0, .78, .48)
        ld.spot_size = math.radians(70); ld.spot_blend = .8; ld.shadow_soft_size = .4
        lo = bpy.data.objects.new(ld.name, ld); sc.collection.objects.link(lo); lo.location = loc
        lo.rotation_euler = Vector(d).to_track_quat('-Z', 'Y').to_euler()
    so.hide_render = True
    nt.nodes.remove(sky)
    bg = nt.nodes['Background']
    tcw = nt.nodes.new('ShaderNodeTexCoord')
    sepw = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tcw.outputs['Generated'], sepw.inputs['Vector'])
    rampw = nt.nodes.new('ShaderNodeValToRGB')
    rampw.color_ramp.elements[0].position = .0; rampw.color_ramp.elements[0].color = (.030, .020, .012, 1)   # sodium city glow
    rampw.color_ramp.elements[1].position = .22; rampw.color_ramp.elements[1].color = (.0015, .0022, .0055, 1)
    nt.links.new(sepw.outputs['Z'], rampw.inputs['Fac'])
    nt.links.new(rampw.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 1.0
    sc.view_settings.exposure = 0.3
    for o in [o for o in sc.objects if o.type == 'LIGHT' and o.name.startswith(('lob', 'chi'))]:
        pass
sc.cycles.samples = SPP; sc.cycles.use_denoising = True
sc.cycles.volume_step_rate = 4.0; sc.cycles.volume_max_steps = 256
sc.render.resolution_x, sc.render.resolution_y = RES
for n in os.environ.get('VIEWS', ','.join(views)).split(','):
    sc.camera = views[n]
    sc.render.filepath = f'{OUT}/prev_{n}.png'
    t = time.time(); bpy.ops.render.render(write_still=True); print('RENDER', n, round(time.time() - t, 1))
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/preview.blend')
