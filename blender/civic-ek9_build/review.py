"""Headless build + review renders + scrubbable save:

    blender -b --factory-startup --python blender/civic-ek9_build/review.py -- [tag] [view ...]

Builds the car from the scripts, renders review views into
renders/civic-ek9/<tag>_<view>.png and saves blender/civic-ek9-car.blend."""
import os
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
for name in [m for m in sys.modules if m == 'ek9' or m.startswith('ek9.')]:
    del sys.modules[name]
import bpy
from ek9 import build

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
tag = args[0] if args else 'car'
views = args[1:] or None
t = time.time()
build.car_only()
print('built in %.1fs' % (time.time() - t), 'objects/tris', build.stats('CAR'))
ORTHO_RES = {'side': (1600, 560), 'front': (1000, 700), 'rear': (1000, 700), 'top': (1600, 900)}
if views != ['none']:
    persp = [v for v in (views or build.VIEWS) if not v.startswith('o_')]
    for v in (views or []):
        if v.startswith('o_'):
            print('RENDER', build.ortho(tag, v[2:], ORTHO_RES[v[2:]]))
    if persp:
        for p in build.review(tag, persp):
            print('RENDER', p)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            for sp in area.spaces:
                if sp.type == 'VIEW_3D':
                    sp.shading.type = 'MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(ROOT), 'civic-ek9-car.blend'), copy=True)
print('DONE in %.1fs' % (time.time() - t))
