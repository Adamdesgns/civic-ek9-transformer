"""Render the cabin alone (body hidden) from a few angles, plus two views through the glass, into
renders/civic-ek9/<tag>_<view>.png:

    blender -b blender/civic-ek9-car.blend --python tools/civic-ek9/cabin_views.py -- <tag>

Cameras are (eye, target, lens) in Blender space (the car faces -Y, +X is its left)."""
import os
import sys
import bpy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'blender', 'civic-ek9_build')))
from ek9 import scene  # noqa: E402

tag = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'cab'
CABIN = ('seat.', 'seatBack.', 'rearSeat', 'dash', 'pedals', 'steeringWheel', 'steeringBadge', 'carpet', 'console', 'doorCard.',
         'headliner', 'rearMirror', 'belts', 'floor')
body = [o for o in bpy.data.collections['CAR'].all_objects if not o.name.startswith(CABIN)]
ALONE = {
    'cabFL': ((2.4, -2.6, 2.3), (0.0, -0.25, 0.55), 32),
    'cabR': ((-1.6, 3.0, 2.2), (0.0, -0.4, 0.55), 32),
    'cabDash': ((-0.33, 0.25, 1.05), (-0.30, -0.60, 0.78), 30),      # the driver's eye (right-hand drive)
    'cabSeat': ((0.30, -0.45, 1.00), (0.35, 0.30, 0.62), 18),        # the passenger seat from the dash
    'cab80': ((0.70, 0.05, 1.15), (-0.15, -0.55, 0.70), 17),         # photo 80: the dash from the passenger door
    'cab84': ((0.02, 0.02, 1.02), (-0.28, -0.55, 0.74), 24),         # photo 84: the binnacle, stack and wheel
    'cabDoor': ((-0.05, -0.10, 1.00), (0.78, 0.05, 0.62), 20),       # photo 78: the passenger door card
}
THRU = {
    'thruFront': ((0.0, -6.5, 1.35), (0.0, -0.3, 0.85), 45),
    'thruSide': ((5.5, -0.3, 1.25), (0.0, -0.3, 0.85), 40),
}
for o in body:
    o.hide_render = True
for k, (eye, tgt, lens) in ALONE.items():
    print('RENDER', scene.render('%s_%s' % (tag, k), eye, tgt, lens, res=(1000, 700)))
for o in body:
    o.hide_render = False
for k, (eye, tgt, lens) in THRU.items():
    print('RENDER', scene.render('%s_%s' % (tag, k), eye, tgt, lens, res=(1000, 700)))
