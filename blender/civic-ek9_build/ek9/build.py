"""Build orchestration (run inside Blender via run.py)."""
import math
import time
import bpy
from . import kit, scene, dims as D

STATE = bpy.app.driver_namespace.setdefault("ek_state", {})  # survives module reloads


def clear_defaults():
    """Drop the factory startup cube / light / camera."""
    for n in ('Cube', 'Light', 'Camera'):
        o = bpy.data.objects.get(n)
        if o is not None:
            bpy.data.objects.remove(o, do_unlink=True)


def car_only():
    t = time.time()
    clear_defaults()
    scene.setup_stage()
    root = kit.collection('CIVIC')
    c = kit.collection('CAR', root)
    kit.clear_collection(c)
    kit.purge_orphans()
    from . import car
    parts = car.build(c)
    # the body is built on its design datums; it stands D.RIDE higher on the wheels (dims). The lift is
    # kept on the scene for tools/civic-ek9/check_model.py, whose silhouettes are in design space
    for o in c.all_objects:
        if not o.name.startswith('wheel.') and o.parent is None:      # children ride with their parent
            o.location.z += D.RIDE
    bpy.context.scene['ek_ride'] = D.RIDE
    print('car parts:', len(parts), 'in %.1fs' % (time.time() - t))
    STATE['parts'] = parts
    return parts


def stats(coll_name):
    dg = bpy.context.evaluated_depsgraph_get()
    tris = n = 0
    for o in bpy.data.collections[coll_name].all_objects:
        if o.type != 'MESH' or o.hide_render:
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        ev.to_mesh_clear()
        n += 1
    return n, tris


# review cameras: (eye, target, lens) in Blender space (the car faces -Y, +X is its left)
VIEWS = {
    'side': ((9.5, 0.0, 0.72), (0.0, 0.0, 0.62), 45),
    'front3q': ((4.6, -5.6, 1.05), (0.0, -0.35, 0.58), 38),
    'front': ((0.0, -9.5, 0.78), (0.0, 0.0, 0.62), 50),
    'rear3q': ((-4.4, 5.6, 1.45), (0.0, 0.3, 0.6), 38),
    'rear': ((0.0, 9.5, 0.9), (0.0, 0.0, 0.66), 50),
    'top': ((0.0, 0.0001, 13.0), (0.0, 0.0, 0.0), 40),
    'low3q': ((3.6, -4.2, 0.42), (0.0, -0.4, 0.55), 30),
    'nose': ((1.9, -3.9, 0.85), (0.0, -1.75, 0.52), 45),
    'tail': ((-1.8, 4.0, 1.05), (0.0, 1.8, 0.62), 45),
    'mirror': ((2.6, -1.9, 1.05), (0.75, -0.55, 0.78), 40),
    'heroF': ((3.7, -4.7, 0.60), (0.05, -0.25, 0.56), 34),
    'heroR': ((-3.8, 4.9, 1.05), (0.0, 0.15, 0.62), 34),
    'heroS': ((7.2, -1.2, 0.75), (0.0, -0.05, 0.62), 40),
    'rearq': ((2.9, 2.6, 1.05), (0.78, 1.3, 0.75), 40),
    'bonnet': ((1.9, -3.6, 2.1), (0.15, -1.35, 0.62), 32),         # high front-left over the hood (photo 75)
    # the camera fitted to the reference photo's landmarks (lamp ends, grille ends, wheel centres): low
    # on the car's right front, 18.5 mm, rolled 3.9 deg, at the photo's aspect. The photo shows the
    # right side in low sun, so the key light swaps to that side for this view
    'photo': ((-2.3366, -2.6517, 0.5892), (-0.0614, -0.6963, 0.5887), 18.52,
              {'roll': 0.06746, 'side': 'right', 'res': (1422, 930)}),
}


def review(tag, views=None, res=(1280, 720)):
    out = []
    for k in (views or VIEWS):
        eye, target, lens, *extra = VIEWS[k]
        opt = extra[0] if extra else {}
        side = opt.get('side', 'left')
        if side != 'left':
            scene.key_side(side)
        out.append(scene.render('%s_%s' % (tag, k), eye, target, lens, res=opt.get('res', res), roll=opt.get('roll', 0.0)))
        if side != 'left':
            scene.key_side('left')
    return out


# orthographic blueprint-matching views: (camera location, up hint, centre (x, f, z), metres across)
ORTHO = {
    'side': ((10.0, 0.0, 0.70), 'side', 4.6),
    'front': ((0.0, -10.0, 0.70), 'front', 2.3),
    'rear': ((0.0, 10.0, 0.70), 'rear', 2.3),
    'top': ((0.0, 0.0, 10.0), 'top', 4.6),
}


def ortho(tag, view, res=(1600, 560)):
    """Orthographic render framed in design metres (see tools/civic-ek9/overlay.py)."""
    from mathutils import Vector, Matrix
    sc = bpy.context.scene
    cam = scene.camera('ek.ortho')
    loc, kind, span = ORTHO[view]
    cam.location = Vector(loc)
    fwd = -Vector(loc).normalized() if kind != 'top' else Vector((0, 0, -1))
    if kind == 'side':
        fwd = Vector((-1, 0, 0))
        cam.location = Vector((10.0, 0.0, 0.70))
    elif kind in ('front', 'rear'):
        fwd = Vector((0, 1, 0)) if kind == 'front' else Vector((0, -1, 0))
        cam.location = Vector((0.0, -10.0 if kind == 'front' else 10.0, 0.70))
    up = Vector((0, 0, 1)) if kind != 'top' else Vector((-1, 0, 0))
    right = fwd.cross(up).normalized()
    upv = right.cross(fwd).normalized()
    R = Matrix((right, upv, -fwd)).transposed()
    cam.matrix_world = Matrix.Translation(cam.location) @ R.to_4x4()
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = span
    cam.data.clip_start, cam.data.clip_end = 0.1, 40
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    import os
    path = os.path.join(scene.RENDER_DIR, '%s_ortho_%s.png' % (tag, view))
    sc.render.filepath = path
    # stage off: the overlay needs a clean silhouette
    stage = [o for o in (bpy.data.objects.get(n) for n in ('ek.ground',)) if o]
    for o in stage:
        o.hide_render = True
    bpy.ops.render.render(write_still=True)
    for o in stage:
        o.hide_render = False
    sc.render.film_transparent = False
    return path
