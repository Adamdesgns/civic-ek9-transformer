"""Render the saved EK9 through a fitted photo camera (camfit.py output), transparent film, no ground.

    blender -b blender/civic-ek9-car.blend --python camrender.py -- cam.json out.png"""
import json
import sys
import bpy
from mathutils import Matrix, Vector

args = sys.argv[sys.argv.index('--') + 1:]
c = json.load(open(args[0]))
sc = bpy.context.scene
cam_data = bpy.data.cameras.new('fit')
cam = bpy.data.objects.new('fit', cam_data)
sc.collection.objects.link(cam)
R = Matrix(c['R'])                       # columns: right, forward, up
right, fwd, up = R.col[0], R.col[1], R.col[2]
M = Matrix((right, up, -fwd)).transposed().to_4x4()
M.translation = Vector(c['eye'])
cam.matrix_world = M
cam_data.sensor_fit = 'HORIZONTAL'
cam_data.sensor_width = 36.0
cam_data.lens = c['fpx'] / c['W'] * 36.0
cam_data.clip_start, cam_data.clip_end = 0.1, 200.0
sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = c['W'], c['H']
sc.render.resolution_percentage = 100
sc.render.film_transparent = True
for n in ('ek.ground',):
    o = bpy.data.objects.get(n)
    if o:
        o.hide_render = True
sc.render.filepath = args[1]
bpy.ops.render.render(write_still=True)
print('WROTE', args[1])
