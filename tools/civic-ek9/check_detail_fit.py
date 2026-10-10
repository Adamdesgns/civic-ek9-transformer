"""Regression checks for the protruding belts and the roof-rail interruption."""
import os
import sys
import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'blender', 'civic-ek9_build'))
from ek9 import body

sc = bpy.context.scene
ride = sc.get('ek_ride', 0)
belts = bpy.data.objects['belts']
minimum = 10.0
for v in belts.data.vertices:
    p = belts.matrix_world @ v.co
    section = body.section(-p.y)
    z = p.z - ride
    xs = []
    for a, b in zip(section, section[1:] + section[:1]):
        if min(a[1], b[1]) <= z <= max(a[1], b[1]) and abs(a[1]-b[1]) > 1e-8:
            xs.append(a[0] + (b[0]-a[0]) * (z-a[1])/(b[1]-a[1]))
    assert xs, 'Belt vertex outside body height'
    minimum = min(minimum, max(xs) - abs(p.x))
assert minimum > .010, f'Seat belt protrudes or lacks interior clearance: {minimum:.5f} m'
print(f'BELT_CLEARANCE PASS minimum {minimum * 1000:.1f} mm', flush=True)

dg = bpy.context.evaluated_depsgraph_get()
for s in (-1, 1):
    for f in (-.70, -.64, -.62, -.60, -.56):
        for z in (1.25, 1.26):
            hit, p, n, idx, ob, matrix = sc.ray_cast(dg, Vector((s*1.5, -f, z+ride)), Vector((-s, 0, 0)))
            assert hit and ob.name in ('quarter.L', 'quarter.R', 'roof'), \
                f'Roof rail interruption at {s, f, z}: {ob.name if hit else "no surface"}'
print('ROOF_RAIL PASS 20 surface probes across the old seam', flush=True)
