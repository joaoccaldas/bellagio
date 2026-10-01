"""Fast look at the Luxor and the Strip base layer, without rebuilding the Bellagio interior.

OVERLAY=1 renders a transparent top-down of the same 760 m square as luxor/data/luxor_sat.jpg
so the model can be checked against the orthophoto. Beauty views use Cycles.

Env: VIEWS, SPP, RES, OUT, OVERLAY=1
"""
import sys, os, math, time
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector

OUT = os.environ.get('OUT', os.path.join(os.path.dirname(__file__), '..', 'renders', 'city'))
os.makedirs(OUT, exist_ok=True)
SPP = int(os.environ.get('SPP', 32))
RES = [int(x) for x in os.environ.get('RES', '1280x720').split('x')]

bpy.ops.wm.read_factory_settings(use_empty=True)
import mats, luxor, city, grounds

sc = bpy.context.scene
M = mats.build()
coll = bpy.data.collections.new('CITY'); sc.collection.children.link(coll)
t0 = time.time()
luxor.build(coll, M)
city.build(coll, M)
grounds.eiffel(coll, M)
# Sky Beam and edge lights are night-only. Day renders hide them so the column is not a solid tube.
if os.environ.get('LIGHTING', 'day') != 'night':
    for o in list(coll.all_objects):
        if o.get('dyn') == 'night':
            o.hide_render = True
print('built', round(time.time() - t0, 1), 's', len(bpy.data.objects), 'objects')

world = bpy.data.worlds.new('W'); sc.world = world
nt = world.node_tree
sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'
sun_el, sun_az = math.radians(42), math.radians(200)   # afternoon, west light on the east faces
sky.sun_elevation = sun_el; sky.sun_rotation = math.radians(90) - sun_az + math.pi / 2
sky.altitude = 610; sky.sun_disc = False
nt.links.new(sky.outputs[0], nt.nodes['Background'].inputs[0])
nt.nodes['Background'].inputs[1].default_value = .4
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.6; sd.angle = math.radians(.55); sd.color = (1, .95, .88)
so = bpy.data.objects.new('sun', sd); sc.collection.objects.link(so)
dvec = Vector((math.sin(sun_az) * math.cos(sun_el), math.cos(sun_az) * math.cos(sun_el), math.sin(sun_el)))
so.rotation_euler = dvec.to_track_quat('Z', 'Y').to_euler()


def cam(name, loc, tgt, lens):
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(c)
    c.location = loc
    c.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    c.data.lens = lens
    c.data.clip_end = 8000
    return c


views = {
    'pyramid': cam('pyramid', (430, -1760, 28), (54, -1938, 55), 28),
    'sphinx': cam('sphinx', (270, -1935, 14), (195, -1935, 18), 35),
    'aerial': cam('aerial', (480, -1550, 380), (60, -2050, 10), 28),
    'mandalay': cam('mandalay', (500, -2500, 40), (150, -2300, 70), 32),
    'south_strip': cam('south_strip', (520, -500, 180), (150, -1350, 60), 30),
    'north_strip': cam('north_strip', (450, -50, 120), (120, 750, 70), 32),
    'valley_wide': cam('valley_wide', (1800, -800, 950), (100, 200, 50), 24),
    'eiffel': cam('eiffel', (240, -80, 25), (389, -66, 65), 35),
    'high_roller': cam('high_roller', (920, 488, 90), (730, 488, 90), 38),
    'roller_coaster': cam('roller_coaster', (330, -1520, 35), (200, -1500, 35), 30),
    'skyways': cam('skyways', (270, -1480, 24), (255, -1560, 8), 32),
    'welcome_sign': cam('welcome_sign', (328, -3400, 6), (328, -3430, 7.5), 35),
}

sc.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type = 'METAL'; prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == 'METAL'
    sc.cycles.device = 'GPU'
except Exception as e:
    print('CPU fallback', e)
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = -0.6
sc.cycles.samples = SPP
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = RES
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
want = os.environ.get('VIEWS', 'pyramid,sphinx,aerial').split(',')
for n in want:
    if n not in views:
        print('skip', n); continue
    sc.camera = views[n]
    sc.render.filepath = os.path.join(OUT, n + '.png')
    t = time.time(); bpy.ops.render.render(write_still=True)
    print('RENDER', n, round(time.time() - t, 1))

if os.environ.get('OVERLAY', '1') == '1':
    # After the beauty renders: flat red footprints on the same 760 m square as luxor_sat.jpg.
    red = bpy.data.materials.new('overlay_red')
    red.diffuse_color = (1, 0.05, 0.05, 1)
    for o in list(coll.all_objects):
        if o.type != 'MESH':
            continue
        if o.name.startswith('CITY_ground'):
            o.hide_render = True
            continue
        o.data.materials.clear()
        o.data.materials.append(red)
    oc = bpy.data.objects.new('overlay', bpy.data.cameras.new('overlay')); sc.collection.objects.link(oc)
    oc.data.type = 'ORTHO'
    oc.data.ortho_scale = 760
    oc.location = (30, -1900, 900)
    oc.rotation_euler = (0, 0, 0)
    oc.data.clip_end = 2000
    sc.camera = oc
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = 1200
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.filepath = os.path.join(OUT, 'overlay.png')
    sc.display.shading.light = 'FLAT'
    sc.display.shading.color_type = 'MATERIAL'
    t = time.time(); bpy.ops.render.render(write_still=True)
    print('OVERLAY', round(time.time() - t, 1))
print('DONE', round(time.time() - t0, 1))
