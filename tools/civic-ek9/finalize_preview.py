"""Restore the outdoor authoring stage and pack the saved model for opening."""
import os
import sys
import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'blender', 'civic-ek9_build'))
from ek9 import scene, build

for ob in list(bpy.data.objects):
    if ob.name.startswith('review.'):
        bpy.data.objects.remove(ob, do_unlink=True)
scene.setup_stage()
bpy.data.objects['ek.sun'].hide_render = False
scene.RENDER_DIR = os.path.join(ROOT, 'evidence', 'final')
scene.render('outdoor-hero', *build.VIEWS['heroF'], res=(1600, 1000))
scene.render('outdoor-hood', (2.0, -3.2, 2.45), (.18, -1.18, .73), 48, res=(1280,853))
scene.render('outdoor-roof', (2.9, -1.25, 2.2), (.36, .32, 1.17), 60, res=(1280,853))
sc = bpy.context.scene
eye, target, lens = build.VIEWS['heroF']
scene.look_at(sc.camera, eye, target, lens)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            sp = area.spaces.active
            sp.shading.type = 'MATERIAL'
            sp.shading.use_scene_world = True
            sp.shading.use_scene_lights = True
            sp.overlay.show_overlays = False
            sp.region_3d.view_rotation = (Vector(target)-Vector(eye)).to_track_quat('-Z','Y')
            sp.region_3d.view_location = Vector(target)
            sp.region_3d.view_distance = 6.2
            sp.region_3d.view_perspective = 'PERSP'
            sp.lens = 42
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.file.pack_all()
sc['ek9_revision'] = '2026-09-30 reference corrections: hood lamps roof rail belt anchors wheels handles vents'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'blender', 'civic-ek9-yellow-refined.blend'))
print('FINAL_PREVIEW_SAVED', flush=True)
