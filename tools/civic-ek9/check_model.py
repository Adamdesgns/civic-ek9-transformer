"""Model checks for the saved EK9 car (run inside Blender on blender/civic-ek9-car.blend):

    blender -b blender/civic-ek9-car.blend --python-exit-code 1 --python tools/civic-ek9/check_model.py [-- holes|mesh]

* mesh: every mesh in the CAR collection keeps zero-area faces (< 0.01 mm^2, on the object's own
  mesh) under 1 %, and the layered parts (lamp / tail reflectors, grille mesh) and the parts cut against
  the body (spoiler, mirror sails) are one piece each.
* holes: a 1 cm ray grid over the side (both sides), front and rear silhouettes. Inside the
  wheel-arch openings anything may show (tyre, spokes, liners, floor). Elsewhere a ray fails when
  its first hit is the floor, a liner, a face in the 'interior' material (skin inner walls), the
  windshield from behind or more than 10 cm inside the side outline, or nothing at all inside
  the side silhouette. A failing ray only counts as a hole when its four neighbours 8 mm away
  fail too: shut lines (4.4 mm, wider only at grazing angles) pass, real holes are 2 cm+.

Exits non-zero (with --python-exit-code) when a check fails. Design (x, f, z) is Blender (x, -f, z);
the body stands the scene's 'ek_ride' (dims.RIDE) higher, so rays run at design z + ride.
"""
import math
import os
import sys
import bmesh
import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'blender', 'civic-ek9_build')))
from ek9 import dims as D, body as B  # noqa: E402

ZERO_AREA = 1e-8
MAX_ZERO_FRAC = 0.01
ONE_PIECE = ('lampReflector.L', 'lampReflector.R', 'tailReflector.L', 'tailReflector.R', 'grilleMesh', 'spoiler',
             'mirrorBase.L', 'mirrorBase.R')
STEP, NEIGH = 0.01, 0.008
RIDE = bpy.context.scene.get('ek_ride', 0.0)


def islands(me):
    """Connected pieces by shared vertices (union-find over edges)."""
    n = len(me.vertices)
    if n == 0:
        return 0
    parent = np.arange(n)

    def find(a):
        root = a
        while parent[root] != root:
            root = parent[root]
        while parent[a] != root:
            parent[a], a = root, parent[a]
        return root
    ev = np.empty(len(me.edges) * 2, dtype=np.int64)
    me.edges.foreach_get('vertices', ev)
    for a, b in ev.reshape(-1, 2):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    return len({find(i) for i in range(n)})


def mesh_check(coll):
    ok = True
    print('MESH  %-18s %8s %8s %7s %s' % ('object', 'faces', 'zero', '%', 'pieces'))
    for o in sorted(coll.all_objects, key=lambda o: o.name):
        if o.type != 'MESH' or o.hide_render:
            continue
        bm = bmesh.new()
        bm.from_mesh(o.data)
        nf = len(bm.faces)
        zero = sum(1 for f in bm.faces if f.calc_area() < ZERO_AREA)
        bm.free()
        frac = zero / nf if nf else 0.0
        pieces = islands(o.data) if o.name in ONE_PIECE else None
        bad = frac >= MAX_ZERO_FRAC or (pieces is not None and pieces != 1)
        ok &= not bad
        if bad or zero or pieces is not None:
            print('MESH  %-18s %8d %8d %6.2f%% %s%s' % (o.name, nf, zero, 100 * frac,
                                                     '' if pieces is None else pieces, '  FAIL' if bad else ''))
    print('MESH', 'PASS' if ok else 'FAIL')
    return ok


# ------------------------------------------------------------------ holes

def in_arch(f, z, grow=0.006):
    return any(math.hypot(f - a, z - D.ARCH_Z) < D.ARCH_R + grow for a in (D.FA, D.RA))


def in_side_silhouette(f, z, margin=0.03):
    """Well inside the body's side outline: between the underside and the top line, and behind
    the front / ahead of the rear face at this height (centreline face profiles)."""
    if in_arch(f, z):
        return False
    if not (D.zb(f) + margin < z < D.zt(f) - margin):
        return False
    return -D.TIP + D.FACE_R(z) + margin < f < D.TIP - D.FACE_NOSE_F(z) - margin


def in_arch_front(x, z):
    """Front / rear rays outboard of the bumper corners that look into a wheel arch."""
    return abs(x) > 0.60 and z < D.ARCH_Z + D.ARCH_R + 0.03


def classify(sc, dg, origin, direction, view, uv):
    """None if the ray is fine, else a short reason."""
    side = view.startswith('side')
    if (side and in_arch(*uv)) or (not side and in_arch_front(*uv)):
        return None
    hit, loc, nrm, idx, obj, _ = sc.ray_cast(dg, origin, direction)
    if not hit:
        return 'through' if side and in_side_silhouette(*uv) else None
    name = obj.name
    if name in ('floor', 'liners'):
        return name
    if name == 'windshield':
        if view == 'rear':
            return 'windshield'
        if side:
            outer = B.side_profile(uv[0], uv[1])
            if outer is not None and outer - abs(loc.x) > 0.10:
                return 'windshield'
    ev = obj.evaluated_get(dg)
    me = ev.data
    if 0 <= idx < len(me.polygons):
        mi = me.polygons[idx].material_index
        mat = me.materials[mi] if mi < len(me.materials) else None
        if mat is not None and mat.name == 'ek.interior':
            return 'interior:' + name
    return None


def ray_setup(view, u, v):
    """(origin, direction, (a, b)) for grid coordinates u, v in design space. Side: (f, z); front /
    rear: (x, z). The ray runs at the body's height, z + RIDE."""
    z = v + RIDE
    if view == 'sideL':
        return Vector((2.0, -u, z)), Vector((-1, 0, 0)), (u, v)
    if view == 'sideR':
        return Vector((-2.0, -u, z)), Vector((1, 0, 0)), (u, v)
    if view == 'front':
        return Vector((u, -3.0, z)), Vector((0, 1, 0)), (u, v)
    return Vector((u, 3.0, z)), Vector((0, -1, 0)), (u, v)


def grid(view):
    zs = np.arange(0.14, 1.345, STEP)
    if view.startswith('side'):
        us = np.arange(-2.12, 2.125, STEP)
    else:
        us = np.arange(-0.86, 0.865, STEP)
    return [(round(float(u), 4), round(float(z), 4)) for u in us for z in zs]


def hole_check():
    sc = bpy.context.scene
    # the ground would catch rays that pass through the car
    stage = [o for o in (bpy.data.objects.get(n) for n in ('ek.ground',)) if o is not None]
    for o in stage:
        o.hide_viewport = True
    dg = bpy.context.evaluated_depsgraph_get()
    ok = True
    for view in ('sideL', 'sideR', 'front', 'rear'):
        failed = {}
        for u, v in grid(view):
            o, d, uv = ray_setup(view, u, v)
            r = classify(sc, dg, o, d, view, uv)
            if r:
                failed[(u, v)] = r
        holes = []
        for (u, v), why in failed.items():
            n = 0
            for du, dv in ((NEIGH, 0), (-NEIGH, 0), (0, NEIGH), (0, -NEIGH)):
                o, d, uv = ray_setup(view, u + du, v + dv)
                n += classify(sc, dg, o, d, view, uv) is not None
            if n == 4:
                holes.append((u, v, why))
        # group holes into clusters (grid neighbours) for a readable report
        left = {(u, v): w for u, v, w in holes}
        clusters = []
        while left:
            seed = next(iter(left))
            stack, members = [seed], []
            while stack:
                p = stack.pop()
                if p not in left:
                    continue
                members.append((p, left.pop(p)))
                for du in (-STEP, 0, STEP):
                    for dv in (-STEP, 0, STEP):
                        q = (round(p[0] + du, 4), round(p[1] + dv, 4))
                        if q in left:
                            stack.append(q)
            clusters.append(members)
        axis = '(f, z)' if view.startswith('side') else '(x, z)'
        print('HOLES %-5s rays %6d failing %5d holes %4d clusters %d' % (view, len(grid(view)), len(failed), len(holes), len(clusters)))
        for members in sorted(clusters, key=len, reverse=True):
            us = [p[0] for p, _ in members]
            vs = [p[1] for p, _ in members]
            whys = sorted({w for _, w in members})
            print('HOLES   %s %s u %.2f..%.2f v %.2f..%.2f  %d rays  %s' % (view, axis, min(us), max(us), min(vs), max(vs),
                                                                         len(members), ', '.join(whys)))
        ok &= not holes
    for o in stage:
        o.hide_viewport = False
    print('HOLES', 'PASS' if ok else 'FAIL')
    return ok


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    which = set(args) or {'mesh', 'holes'}
    coll = bpy.data.collections.get('CAR')
    if coll is None:
        raise SystemExit('no CAR collection: open blender/civic-ek9-car.blend')
    ok = True
    if 'mesh' in which:
        ok &= mesh_check(coll)
    if 'holes' in which:
        ok &= hole_check()
    print('CHECK', 'PASS' if ok else 'FAIL')
    if not ok:
        raise SystemExit(1)


main()
