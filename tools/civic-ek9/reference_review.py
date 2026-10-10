"""Repeatable exterior review under broad studio lights, using real model geometry."""
import os
import sys
import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'blender', 'civic-ek9_build'))
from ek9 import build, scene

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['before']
tag = args[0]
if 'build' in args:
    try:
        build.car_only()
    except Exception:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'evidence', tag + '-failed.blend'))
        raise

# Neutral studio makes the panel edges readable independently of tree reflections.
sc = bpy.context.scene
for ob in bpy.data.objects:
    if ob.type == 'LIGHT':
        ob.hide_render = True
world = bpy.data.worlds.new('EK9 review studio')
world.use_nodes = True
world.node_tree.nodes.get('Background').inputs['Color'].default_value = (0.22, 0.22, 0.22, 1)
world.node_tree.nodes.get('Background').inputs['Strength'].default_value = 0.4
sc.world = world
for name, loc, power, size, target in [
    ('key', (3, -4, 5), 500, 4, (0, 0, .5)),
    ('roof', (-2, 0, 5), 400, 4, (0, 0, .5)),
    ('side', (4, 2, 2.8), 400, 3, (0, 0, .6)),
    ('front', (-3, -5, 2), 300, 3, (0, -1, .6)),
]:
    data = bpy.data.lights.new('review.' + name, 'AREA')
    data.energy, data.shape, data.size = power, 'RECTANGLE', size
    data.size_y = .45
    ob = bpy.data.objects.new('review.' + name, data)
    sc.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat('-Z', 'Y').to_euler()
ground = bpy.data.objects.get('ek.ground')
if ground:
    mat = bpy.data.materials.new('review.floor')
    mat.diffuse_color = (.10, .10, .10, 1)
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (.10, .10, .10, 1)
    bs.inputs['Roughness'].default_value = .7
    ground.data.materials.clear()
    ground.data.materials.append(mat)
sc.render.engine = 'CYCLES'
sc.cycles.samples = 32
sc.cycles.use_denoising = True
# GPU where available; CPU stays a valid fallback on the same renderer.
prefs = bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for device in prefs.devices:
        device.use = device.type != 'CPU'
    if any(d.use for d in prefs.devices):
        sc.cycles.device = 'GPU'
except Exception:
    pass
sc.view_settings.view_transform = 'Khronos PBR Neutral'
sc.view_settings.look = 'None'
sc.view_settings.exposure = -0.8
sc.render.film_transparent = False
out = os.path.join(ROOT, 'evidence', tag)
os.makedirs(out, exist_ok=True)
scene.RENDER_DIR = out
views = {
    'hero': ((5.5, -7.2, 1.65), (0, -.05, .64), 56),
    'hood': ((2.0, -3.2, 2.45), (.18, -1.18, .73), 48),
    'roof': ((2.9, -1.25, 2.2), (.36, .32, 1.17), 60),
    'side': ((11.2, -.25, .95), (0, -.05, .66), 65),
    'front': ((0, -7.0, 1.0), (0, -1.0, .5), 60),
}
requested = [a for a in args[1:] if a != 'build'] or list(views)
for name in requested:
    scene.render(name, *views[name], res=(1280, 853))
if 'build' in args:
    # Open on a clean full-car view, with the studio available in rendered shading.
    scene.look_at(sc.camera, *views['hero'])
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.shading.type = 'MATERIAL'
                space.shading.use_scene_world = True
                space.shading.use_scene_lights = True
                space.region_3d.view_perspective = 'CAMERA'
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'blender', 'civic-ek9-car.blend'))
print('REVIEW_COMPLETE', tag, flush=True)
