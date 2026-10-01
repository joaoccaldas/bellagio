"""Export the Luxor and the city base layer without rebaking the Bellagio.

Writes out/city.glb. The viewer loads it beside the baked bellagio.glb and skips it
once a full bake has folded the same objects into the main file.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
import bpy

OUT = os.environ.get('OUT', os.path.join(os.path.dirname(__file__), '..', 'out'))
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
import mats, luxor, city, grounds

sc = bpy.context.scene
M = mats.build()
coll = bpy.data.collections.new('CITY'); sc.collection.children.link(coll)
t0 = time.time()
luxor.build(coll, M)
city.build(coll, M)
grounds.eiffel(coll, M)
print('built', round(time.time() - t0, 1), 's')

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
path = os.path.join(OUT, 'city.glb')
bpy.ops.export_scene.gltf(
    filepath=path, export_format='GLB', use_selection=True, export_apply=True,
    export_extras=True, export_yup=True, export_texcoords=True, export_normals=True,
    export_materials='EXPORT', export_image_format='NONE', export_lights=False, export_cameras=False,
)
print('WROTE', path, round(os.path.getsize(path) / 1e6, 2), 'MB', round(time.time() - t0, 1), 's')
