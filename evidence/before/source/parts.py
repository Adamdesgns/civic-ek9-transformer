"""EK9 lamps, grille, bumper details, spoiler, mirrors, wipers, liners and
small trim. Lamp lenses and grille pieces are cut from the same envelope as
the panels, so they sit flush in the openings the panels leave."""
import math
import bpy
import numpy as np
from mathutils import Vector, Matrix
from . import kit, body as B, dims as D
from .body import G
from .kit import V
from .shape import lathe, spline2, loft_rings, squircle, lerp, smooth01, curve1, TAU

BIG = 1.6
Z_HI = 2.2


def side_x(s):
    return (0.25, BIG) if s > 0 else (-BIG, -0.25)


def mx(poly, s):
    return poly if s > 0 else B.mirror_x(poly)


def samples(a, b, n):
    return [a + (b - a) * k / n for k in range(n + 1)]


hood_seam_x = D.hood_seam_x


# ------------------------------------------------------------------ headlamps
#
# car.build splits every skin once along the fascias (see Skins): `env` is the
# skin away from the fascia faces (hood, fenders, glass), `fF` / `fR` the skin
# within a few mm of the front / rear fascia face (grille surround, hatch panel).
#
# The headlamp is bounded explicitly instead: a front-view outline (the almond) intersected with
# a side-view outline (the D-shaped wrap onto the flank), cut through the whole skin. The lens is
# the outer surface inside that window and the fender's pocket is the same window grown by G, so
# hole and lens come from one shape and no fender sheet stays behind the lens. (The wrap lies on
# the envelope, where the fascia meets the flank almost tangentially, so a fascia-face split
# cannot reach it.)

# front view (x, z), left lamp: from the fender corner the top arcs over and falls to a sharp, low
# inboard tip beside the grille (reference photo; the base-EK blueprint tip is blunter and higher).
# The top is one arc with a single peak (x 0.66), evenly spaced knots so the spline cannot ripple.
# It carries the whole top edge, round the corner and along the flank: outboard of the peak it
# eases down monotonically under the rolled hood / fender edge, which dips to about z 0.653 at the
# corner (x 0.76), so a level top ran up the roll into a horn.
_LAMP_TOP = [(0.86, 0.6478), (0.80, 0.6487), (0.78, 0.6494), (0.76, 0.6508), (0.74, 0.6532), (0.72, 0.6556),
             (0.70, 0.6578), (0.68, 0.6594), (0.66, 0.6600), (0.64, 0.6597), (0.62, 0.6587), (0.60, 0.657),
             (0.56, 0.651), (0.52, 0.641), (0.49, 0.629), (0.46, 0.611), (0.435, 0.591), (0.412, 0.570),
             (0.392, 0.549), (0.374, 0.531), (0.357, 0.516)]
LAMP_TIP_R = 0.010        # the inner end is a small round, not a point; > HOUSING_SHRINK, so every inset keeps it
# side view (f, z): only the blueprint's D-shaped rear end on the flank. Its top rounds over into the
# front outline's flank height (about 0.649 at f 1.64) and then climbs clear of it, so the front
# outline alone bounds the top forward of f 1.64: the two hand over once, at the D. (A side top
# that bounded the corner as well switched with the front one three times: a hump and a step.)
LAMP_SIDE_FZ = [(2.3, 0.516), (1.592, 0.516), (1.587, 0.530), (1.588, 0.558), (1.593, 0.596), (1.600, 0.616),
                (1.611, 0.634), (1.622, 0.6425), (1.634, 0.6475), (1.648, 0.6503), (1.67, 0.6525), (1.70, 0.656),
                (1.73, 0.661), (1.76, 0.670), (1.80, 0.700), (2.3, 0.700)]


# The hood's front edge in front view (x, z), right half from the centreline outward (Adam's markup on
# the bonnet view; photos 67, 75). The facelift's grille is the hood's: the edge runs along the bumper
# top under the grille, round each headlamp's inner tip and along the lamp top to the side seam
# (dims.HOOD_SEAM), which meets it about 10 cm inboard of the lamp's outer corner. The hood is the skin above this line, and its
# front prism shrinks by G, so its edge sits one reveal off the bumper and the lamp pockets
def hood_edge_xz():
    return [(0.0, D.BUMPER_TOP_F), (0.30, D.BUMPER_TOP_F)] + list(reversed(_LAMP_TOP)) + [(BIG, _LAMP_TOP[0][1])]


def hood_front_prism(f0, f1):
    """The region above the hood's front edge (hood_edge_xz), extruded along f0..f1."""
    e = hood_edge_xz()
    edge = [(x, z) for x, z in reversed(e)] + [(-x, z) for x, z in e[1:]]      # +BIG .. -BIG
    return B.front_prism([(-BIG, Z_HI), (BIG, Z_HI)] + edge, f0, f1)


def _almond():
    """Closed front outline: bottom along the bumper line, the splined top, and a LAMP_TIP_R arc
    at the tip (a sharp polygon tip would swallowtail when the window is shrunk or grown)."""
    top = spline2(_LAMP_TOP, 3 * len(_LAMP_TOP))
    ax, az = top[-1]
    px, pz = _LAMP_TOP[-2]
    u2 = Vector((px - ax, pz - az)).normalized()
    u1 = Vector((1.0, 0.0))
    half = 0.5 * math.acos(max(-1.0, min(1.0, u1.dot(u2))))
    d = LAMP_TIP_R / math.tan(half)
    apex = Vector((ax, az))
    c = apex + (u1 + u2).normalized() * (LAMP_TIP_R / math.sin(half))
    t2 = apex + u2 * d
    top = [p for p in top[:-1] if (Vector(p) - apex).length > d + 0.004]
    # round the tip counter-clockwise, from the top edge's tangent point to the bottom line's
    a0 = math.atan2(t2.y - c.y, t2.x - c.x)
    a1 = a0 + (1.5 * math.pi - a0) % (2 * math.pi)
    arc = [(c.x + LAMP_TIP_R * math.cos(a0 + (a1 - a0) * k / 6), c.y + LAMP_TIP_R * math.sin(a0 + (a1 - a0) * k / 6))
           for k in range(7)]
    return [(BIG, 0.516), (BIG, _LAMP_TOP[0][1])] + top + arc


LAMP_FRONT_XZ = _almond()
_WINDOW = {}


def lamp_window(s, shrink=G):
    """The left / right lamp solid, (verts, faces): front outline x side outline, shrunk by
    `shrink` (< 0 grows it: the fender pocket, the housing)."""
    key = (s, round(shrink, 6))
    if key not in _WINDOW:
        front = B.front_prism(mx(LAMP_FRONT_XZ, s), 1.40, 2.6, shrink=shrink)
        side = B.side_prism(LAMP_SIDE_FZ, *side_x(s), shrink=shrink)
        _WINDOW[key] = B.bool_mesh(front, side, 'INTERSECT')
    return _WINDOW[key]


def lamp_pocket(s):
    """The fender's cut-out for a lamp: the lamp window grown by G, through the whole skin."""
    return lamp_window(s, shrink=-G)


# Tail lamps: from the rear face round the square corner and 16 cm down the flank (back from
# D.TAIL_LAMP_SIDE_F), between the bumper (D.TAIL_LAMP_LOW) and TAIL_LAMP_TOP. The top sits on the
# rear face's knee at z 0.90, about 2 cm under the rolled edge where the face meets the hatch glass
# (a lamp cut into that rounding tore the lamp tops).
TAIL_LAMP_TOP = 0.90
TAIL_LAMP_R = 0.03        # the lamp's lower front corner on the flank (side view)
_TAIL = {}


def tail_lamp_x(z):
    """Tail lamp inner edge (the hatch panel's side) in the rear view: it leans in toward the bottom,
    from x 0.600 at the lamp top to 0.568 at the bottom (blueprint)."""
    return 0.568 + (z - 0.60) * (0.032 / 0.30)


def tail_lamp_cutter(s, shrink=G):
    """Left / right tail lamp solid: the rear-view outline (outboard of tail_lamp_x) x the side-view
    outline (a rectangle with its lower front corner rounded), shrunk by `shrink` (< 0 grows it: the
    quarter's pocket)."""
    key = (s, round(shrink, 6))
    if key not in _TAIL:
        front = [(tail_lamp_x(0.4), 0.4), (BIG, 0.4), (BIG, 1.2), (tail_lamp_x(1.2), 1.2)]
        side = kit.fillet_poly([(-2.6, D.TAIL_LAMP_LOW), (D.TAIL_LAMP_SIDE_F, D.TAIL_LAMP_LOW),
                                (D.TAIL_LAMP_SIDE_F, TAIL_LAMP_TOP), (-2.6, TAIL_LAMP_TOP)], 0.0, 8,
                               radii=[0.0, TAIL_LAMP_R, 0.0, 0.0])
        _TAIL[key] = B.bool_mesh(B.front_prism(mx(front, s), -2.6, -1.5, shrink=shrink),
                                 B.side_prism(side, *side_x(s), shrink=shrink), 'INTERSECT')
    return _TAIL[key]


def recolor(o, slot):
    o.hide_render = False
    o.data.materials.clear()
    o.data.materials.append(kit.mats.get(slot))
    for p in o.data.polygons:
        p.material_index = 0


def dup(o, coll):
    """Linked copy of a kept solid, to be consumed as a boolean cutter."""
    c = o.copy()
    c.data = o.data.copy()
    coll.objects.link(c)
    return c


def tri_tree(me):
    """BVH over a mesh's triangles (boolean n-gons are often concave: a BVH built from the
    polygons fans them into wrong triangles and leaves holes)."""
    from mathutils.bvhtree import BVHTree
    me.calc_loop_triangles()
    return BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(t.vertices) for t in me.loop_triangles])


def shape_tree(coll, lo, hi):
    """BVH over the outer shape's triangles inside the design box lo..hi ((x, f, z) corners). The
    panels share this surface, but a ray cast on the panels drops through their 4.4 mm shut lines."""
    from mathutils.bvhtree import BVHTree
    me = B.base_shape(coll).data
    me.calc_loop_triangles()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    tv = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
    me.loop_triangles.foreach_get('vertices', tv)
    tv = tv.reshape(-1, 3)
    blo, bhi = np.array([lo[0], -hi[1], lo[2]]), np.array([hi[0], -lo[1], hi[2]])
    c = co[tv]
    sel = tv[((c.max(axis=1) >= blo) & (c.min(axis=1) <= bhi)).all(axis=1)]
    used, inv = np.unique(sel.ravel(), return_inverse=True)
    return BVHTree.FromPolygons([Vector(p) for p in co[used]], inv.reshape(-1, 3).tolist())


def surface_x(tree, f, z, s=1):
    """|x| of the outer surface at side-view (f, z), from a ray along -s x (None off the body)."""
    loc = tree.ray_cast(V(s * 1.5, f, z), Vector((-s, 0.0, 0.0)))[0]
    return None if loc is None else abs(loc.x)


def surface_z(tree, x, f):
    """z of the outer surface under plan point (x, f), from a ray straight down."""
    loc = tree.ray_cast(V(x, f, 3.0), Vector((0.0, 0.0, -1.0)))[0]
    return None if loc is None else loc.z


def keep_outer(o, tree, eps=2e-5):
    """Keep only the faces lying on the outer shape (`tree`, facing the same way): a window cut
    from the solid shape becomes the single-sided surface inside the window."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(o.data)
    # judged by vertices, not face centres: the boolean leaves long curved n-gons along the
    # waterlines whose centres lie off the surface
    on = {}
    for v in bm.verts:
        loc, n, _, d = tree.find_nearest(v.co)
        on[v.index] = (loc is not None and d <= eps, n)
    drop = []
    for f in bm.faces:
        vs = [on[v.index] for v in f.verts]
        if not all(ok for ok, _ in vs) or f.normal.dot(sum((n for _, n in vs), Vector())) < 0.5 * len(vs):
            drop.append(f)
    bmesh.ops.delete(bm, geom=drop, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()


def slot_faces(o, slot_of):
    """Material per face: slot_of(polygon) -> slot name."""
    me = o.data
    names, idx = [], []
    for p in me.polygons:
        s = slot_of(p)
        if s not in names:
            names.append(s)
        idx.append(names.index(s))
    me.materials.clear()
    for s in names:
        me.materials.append(kit.mats.get(s))
    me.polygons.foreach_set('material_index', idx)


# reflector cups: (x, z, rim radius, centre-cap slot, cap radius / rim radius). The low beam's cap is
# the darker round element the photo shows in the chrome.
LAMP_CUPS = ((0.505, 0.569, 0.040, 'chrome', 0.22), (0.630, 0.590, 0.055, 'darkSteel', 0.34))
CUP_SET, CUP_DEPTH, CUP_LIP = 0.012, 0.032, 0.003   # rim behind the lens (along f), apex below the rim, lip
LENS_T = 0.0015
HOUSING_GROW, HOUSING_SHRINK = 0.003, 0.004         # black gasket ring: window grown / shrunk


def _warped_lathe(prof, xc, zc, r, plane, e, n):
    """Lathe along f about (xc, zc), each vertex shifted along f by the rim's plane plus the rim's
    deviation from it (fading in as (rho / r)^2), so the rim follows the lens exactly."""
    v, faces = lathe(prof, n, 'f', center=(xc, 0.0, zc))
    for co in v:
        dx, dz = co.x - xc, co.z - zc
        rho = math.hypot(dx, dz)
        dev = 0.0
        if rho > 1e-7:
            dev = e[int(round(math.atan2(dz, dx) / TAU * n)) % n] * min(1.0, rho / r) ** 2
        co.y -= plane[0] + plane[1] * dx + plane[2] * dz + dev
    return v, faces


def lamp_cup(xc, zc, r, lens_tree, n=48):
    """Concave paraboloid cup opening along +f, a closed solid: (cup, hole, apex f). The rim sits
    CUP_SET behind the lens at every rim point (the lens sweeps back about 0.4 m/m outboard, so a
    flat rim would poke through outboard and bury inboard); a collar runs back into the housing's
    back wall. `hole` is the matching bore for the back wall, stopping just behind the apex."""
    rim = []
    for k in range(n):
        a = TAU * k / n
        dx, dz = r * math.cos(a), r * math.sin(a)
        hit = lens_tree.ray_cast(V(xc + dx, 3.0, zc + dz), Vector((0.0, 1.0, 0.0)))
        if hit[0] is None:
            raise RuntimeError('lamp cup rim off the lens at (%.3f, %.3f)' % (xc + dx, zc + dz))
        rim.append((dx, dz, -hit[0].y - CUP_SET))
    A = np.array([[1.0, dx, dz] for dx, dz, _ in rim])
    fs = np.array([f for _, _, f in rim])
    plane = np.linalg.lstsq(A, fs, rcond=None)[0]
    e = fs - A @ plane
    back = -(CUP_DEPTH + 0.004)
    dish = [(r * t, -CUP_DEPTH * (1 - t * t)) for t in (0.2, 0.38, 0.54, 0.67, 0.78, 0.87, 0.94, 1.0)]
    prof = [(0.0, -CUP_DEPTH)] + dish + [(r + CUP_LIP, 0.0), (r + CUP_LIP, back), (0.0, back)]
    cup = _warped_lathe(prof, xc, zc, r, plane, e, n)
    hole = _warped_lathe([(0.0, 0.08), (r - 0.002, 0.08), (r - 0.002, -(CUP_DEPTH + 0.002)), (0.0, -(CUP_DEPTH + 0.002))],
                         xc, zc, r, plane, e, n)
    return cup, hole, plane[0] - CUP_DEPTH


def headlamps(coll, parts_, K):
    """Clear lens (the outer surface in the window), and behind it one housing: a black gasket
    ring just behind the shut line, chrome walls and back wall 30 mm in, two concave chrome cups."""
    for S, s in (('L', 1), ('R', -1)):
        lens = B.cut_region(K.nose0, 'lamp.' + S, [lamp_window(s)], coll)
        keep_outer(lens, K.nose_tree)
        recolor(lens, 'lens')
        kit.clean(lens)
        lens_tree = tri_tree(lens.data)
        # the lens's cut edge sits in the black gasket: a clear rim caught the sun as specks and a
        # pale line along the top edge
        lens.data.materials.append(kit.mats.get('trim'))
        kit.solidify(lens, LENS_T, offset=-1.0).material_offset_rim = 1
        kit.finish(lens, 0.0, 1, 30.0)
        parts_['lamp.' + S] = lens

        o = B.cut_region(K.nose_deep, 'lampReflector.' + S, [lamp_window(s, -HOUSING_GROW)], coll)
        kit.boolean(o, dup(K.nose3, coll), 'INTERSECT')
        recolor(o, 'trim')
        cav = B.cut_region(K.nose0, 'lamp.cav', [lamp_window(s, HOUSING_SHRINK)], coll)
        kit.boolean(cav, dup(K.nose30, coll), 'DIFFERENCE')
        recolor(cav, 'reflector')
        kit.boolean(o, cav, 'DIFFERENCE', material_mode='TRANSFER')
        for xc, zc, r, cap_slot, cap in LAMP_CUPS:
            cup, hole, apex = lamp_cup(s * xc, zc, r, lens_tree)
            kit.boolean(o, kit.cutter_obj(hole), 'DIFFERENCE')
            b = kit.Builder()
            b.add_mesh(cup, 'lampCup')
            kit.boolean(o, b.build('lamp.cup', coll), 'UNION', material_mode='TRANSFER')
            # bulb cap on a short stem that runs into the cup's apex
            R = cap * r
            prof = [(0.0, 0.012), (R * 0.75, 0.0115), (R, 0.010), (R, 0.008), (0.0035, 0.007), (0.0035, -0.002), (0.0, -0.002)]
            b = kit.Builder()
            b.add_mesh(lathe(prof, 32, 'f', center=(s * xc, apex, zc)), cap_slot)
            kit.boolean(o, b.build('lamp.cap', coll), 'UNION', material_mode='TRANSFER')
        kit.clean(o)
        kit.finish(o, 0.0012, 1, 30.0)
        parts_['lampReflector.' + S] = o


# ------------------------------------------------------------------ grille + nose

# The dark grille slot under the hood's rolled nose (reference photo): a trapezoid wider at the top,
# about a third of the lamp height, with a slight smile along the bottom. The nose panel around it is
# body colour and sits on the bumper line between the lamp tips.
_SLOT_R = [(0.0, 0.592), (0.15, 0.5915), (0.26, 0.5905), (0.295, 0.589), (0.303, 0.5855), (0.3045, 0.580),
           (0.298, 0.566), (0.289, 0.551), (0.283, 0.543), (0.274, 0.5395), (0.20, 0.5375), (0.10, 0.5355), (0.0, 0.535)]
GRILLE_SLOT = _SLOT_R + [(-x, z) for x, z in reversed(_SLOT_R[1:-1])]


def grille_pocket():
    return B.front_prism(GRILLE_SLOT, 1.80, 2.6, shrink=0)


def grille(coll, parts_, K):
    """The recess and black mesh behind the grille slot, which is cut through the hood (car.build)."""
    # recess behind the slot: black walls from 3 mm in (a 1.5 mm ledge inside the slot's cut edge)
    # back to the floor 30 mm in; its outer ring hides inside the nose skin. The floor is matte
    # dielectric black ('grilleDark'): a metallic floor mirrored the sky and read mid-grey from the
    # front three-quarter view
    g = B.cut_region(K.nose_deep, 'grilleMesh', [B.front_prism(kit.offset_poly(kit.ccw(GRILLE_SLOT), 0.004), 1.80, 2.6, shrink=0)], coll)
    kit.boolean(g, dup(K.nose3, coll), 'INTERSECT')
    recolor(g, 'trim')
    cav = B.cut_region(K.nose0, 'grille.cav', [B.front_prism(GRILLE_SLOT, 1.80, 2.6, shrink=0.0015)], coll)
    kit.boolean(cav, dup(K.nose30, coll), 'DIFFERENCE')
    slot_faces(cav, lambda p: 'trim' if abs(p.normal.y) < 0.3 else 'grilleDark')
    kit.boolean(g, cav, 'DIFFERENCE', material_mode='TRANSFER')
    # the black mesh across the slot (the Type R grille), 12 mm in. No badge: #111040's grille and FRP
    # bonnet carry none
    lat = lattice(coll, K.nose_tree, GRILLE_SLOT, 'grille', GRILLE_PITCH, GRILLE_W, GRILLE_DEPTH)
    _clip_to(lat, GRILLE_SLOT)
    kit.boolean(g, lat, 'UNION', material_mode='TRANSFER')
    kit.clean(g)
    kit.finish(g, 0.001, 1, 30.0)
    parts_['grilleMesh'] = g


def badge_on(coll, name, surface, z, front=True, **kw):
    """badge() seated on `surface` at x = 0, height z: found by a ray along f (from the front or the
    back), tilted flush with the surface there and sunk 0.8 mm into it, so it never floats."""
    loc, nrm, _, _ = tri_tree(surface.data).ray_cast(V(0.0, 3.0 if front else -3.0, z), Vector((0.0, 1.0 if front else -1.0, 0.0)))
    if loc is None:
        raise RuntimeError('%s: no %s surface at z %.3f' % (name, surface.name, z))
    n = Vector((nrm.x, -nrm.y, nrm.z))
    at = Vector((loc.x, -loc.y, loc.z)) - n * 0.0008
    return badge(coll, name, tuple(at), front=front, normal=tuple(n), **kw)


# Honda 'H' with flared uprights, in a unit box
_H = [(-0.50, 0.50), (-0.27, 0.50), (-0.235, 0.09), (0.235, 0.09), (0.27, 0.50), (0.50, 0.50), (0.40, -0.50),
      (0.22, -0.50), (0.20, -0.13), (-0.20, -0.13), (-0.22, -0.50), (-0.40, -0.50)]


def _ring_solid(rings):
    """Closed tube through rings of Blender points, the last ring joined back to the first."""
    n, m = len(rings[0]), len(rings)
    verts = [p for r in rings for p in r]
    faces = []
    for i in range(m):
        i2 = (i + 1) % m
        for j in range(n):
            j2 = (j + 1) % n
            faces.append([i * n + j, i * n + j2, i2 * n + j2, i2 * n + j])
    return verts, faces


def badge(coll, name, at, front=True, w=0.05, h=0.038, normal=None):
    """Type R emblem: red plate, chrome rim and chrome Honda 'H', each a closed piece (rim and H sunk
    0.8 mm into the plate). `at` is the centre of the plate's back face; `normal` (design x, f, z)
    tilts it flush onto a raked face (default: straight forward or back)."""
    nrm = Vector(normal if normal else (0.0, 1.0 if front else -1.0, 0.0)).normalized()
    up = Vector((0.0, 0.0, 1.0))
    up = (up - nrm * up.dot(nrm)).normalized()
    side = up.cross(nrm)
    bl = lambda d: Vector((d.x, -d.y, d.z))           # design direction -> Blender
    M = Matrix((bl(side), bl(up), bl(nrm))).transposed().to_4x4()
    M.translation = V(*at)
    hw, hh = w / 2, h / 2

    def ring(a, c, depth, n=40):
        return [M @ Vector((u, v, depth)) for u, v in squircle(a, c, 3.0, n)]
    b = kit.Builder()
    t = 0.0038
    b.add_mesh(kit.loft([ring(hw, hh, 0.0), ring(hw, hh, t - 0.0008), ring(hw - 0.0008, hh - 0.0008, t)]), 'badgeRed')
    b.add_mesh(_ring_solid([ring(hw - 0.0004, hh - 0.0004, t - 0.0008), ring(hw - 0.0004, hh - 0.0004, t + 0.0012),
                            ring(hw - 0.0016, hh - 0.0016, t + 0.0018), ring(hw - 0.0036, hh - 0.0036, t + 0.0012),
                            ring(hw - 0.0036, hh - 0.0036, t - 0.0008)]), 'badge')
    sx, sz = 1.24 * (hw - 0.0045), 1.24 * (hh - 0.0045)
    b.add_mesh(kit.prism([(u * sx, v * sz) for u, v in _H], t - 0.0008, t + 0.0016, M), 'badge')
    return b.build(name, coll)


# ------------------------------------------------------------------ tail lamps

# lens bands, top down (the facelift lamp, photo 57): tail / brake, the clear turn / reverse band, tail
TAIL_BANDS = [('lensRed', 0.738, 1.2), ('lensClear', 0.668, 0.738), ('lensRed', 0.0, 0.668)]


TAIL_LIP_GROW = 0.001      # the housing's lip, 6 mm in (just behind the 5 mm lens): the lamp grown 1 mm
# the lamp's plan corner (rear face about 11 deg outboard of -f, flank 18 deg back of +x): its outward
# bisector (x, f), the fin's thickness and its reach in from the corner
TAIL_CORNER_N = Vector((math.sin(math.radians(41.5)), -math.cos(math.radians(41.5))))
TAIL_FIN_T, TAIL_FIN_IN = 0.003, 0.040


def _tail_corner(K, s, z):
    """Plan corner of the lamp at height z: where rear0 reaches furthest along TAIL_CORNER_N (its normal
    is the bisector there), from rays cast in along -TAIL_CORNER_N across the corner. The support is
    flat at its peak, so the corner is the middle of the hits within 0.5 mm of it: the single best hit
    wandered a few mm from height to height."""
    n = TAIL_CORNER_N
    t = Vector((-n.y, n.x))
    c0, hits = Vector((0.76, -1.935)), []
    for k in range(-60, 61):
        p = c0 + n * 0.3 + t * (0.001 * k)
        loc = K.rear_tree.ray_cast(V(s * p.x, p.y, z), Vector((-s * n.x, n.y, 0.0)))[0]
        if loc is not None:
            hits.append(Vector((s * loc.x, -loc.y)))
    if not hits:
        raise RuntimeError('no tail lamp corner at z %.3f' % z)
    top = max(q.dot(n) for q in hits)
    near = [q for q in hits if q.dot(n) > top - 0.0005]
    return sum(near, Vector((0.0, 0.0))) / len(near)


def tail_corner_fin(K, s, coll):
    """Chrome divider on the lamp's plan-corner bisector: a ruled slab through the corner at each height,
    TAIL_FIN_T thick, from 6 mm in (K.rear6) to TAIL_FIN_IN in (into the floor). It stops 2 mm short
    of the cavity's top and bottom walls: ending inside the housing's lip put its front face on the
    lip's (both on rear6), and the bevel modifier emitted garbage vertices from that union."""
    n = TAIL_CORNER_N
    lo, hi = D.TAIL_LAMP_LOW + HOUSING_SHRINK + 0.002, TAIL_LAMP_TOP - HOUSING_SHRINK - 0.002
    t = Vector((-n.y, n.x)) * (TAIL_FIN_T / 2)
    zs = [lo + (hi - lo) * k / 12 for k in range(13)]
    cs = [_tail_corner(K, s, z) for z in zs]
    cs = [cs[0]] + [(cs[k - 1] + 2 * cs[k] + cs[k + 1]) / 4 for k in range(1, 12)] + [cs[12]]
    rings = []
    for z, c in zip(zs, cs):
        a, b = c + n * 0.004, c - n * TAIL_FIN_IN
        rings.append([(s * p.x, p.y, z) for p in (a - t, b - t, b + t, a + t)])
    fin = kit.cutter_obj(loft_rings(rings), 'tail.fin')
    kit.boolean(fin, dup(K.rear6, coll), 'INTERSECT')
    recolor(fin, 'tailReflector')
    return fin


def pillar_strip(s):
    """Plan band round the D-pillar / hatch panel shut line above the lamp (the quarter from
    glass_edge_x, the hatch panel to glass_edge_x - G), from just under the lamp top to the glass."""
    fs = [-2.15 + 0.35 * k / 8 for k in range(9)]
    band = [(D.glass_edge_x(f) - G - 0.010, f) for f in fs] + [(D.glass_edge_x(f) + 0.010, f) for f in reversed(fs)]
    return B.top_prism(mx(band, s), TAIL_LAMP_TOP - 0.007, D.HATCH_PANEL_TOP + 0.005, shrink=0)


def tail_housing(coll, K, s, name):
    """The housing behind a tail lamp ('trim'), which closes every shut line round the lamp (they
    opened into the hollow body, and from behind a ray went through the car to the windshield):
    - a ring: the deep skin from 12 mm in under the lamp grown by HOUSING_GROW, carried up behind the
      D-pillar shut line to the glass (pillar_strip; one cutter, so the two share one rear12 face);
    - a lip from 6 mm in (1 mm behind the lens) under the lamp grown TAIL_LIP_GROW, so a ray running
      along inside the lens meets the housing at the lamp's edge instead of the quarter's pocket rim;
    minus a chrome cavity 30 mm deep inside the lamp shrunk by HOUSING_SHRINK, plus a chrome fin on
    the plan corner's bisector: the cavity wraps a convex corner, and a chord from the flank lens to
    the rear lens stayed inside it, so the lamp's rear end read as a see-through glass fin."""
    ring = B.bool_mesh(tail_lamp_cutter(s, -HOUSING_GROW), pillar_strip(s), 'UNION')
    o = B.cut_region(K.deep, name, [ring], coll)
    kit.boolean(o, dup(K.rear12, coll), 'INTERSECT')
    lip = B.cut_region(K.rear6, 'tail.lip', [tail_lamp_cutter(s, -TAIL_LIP_GROW)], coll)
    kit.boolean(lip, dup(K.rear30, coll), 'DIFFERENCE')
    kit.boolean(o, lip, 'UNION')
    recolor(o, 'trim')
    cav = B.cut_region(K.rear0, 'tail.cav', [tail_lamp_cutter(s, HOUSING_SHRINK)], coll)
    kit.boolean(cav, dup(K.rear30, coll), 'DIFFERENCE')
    recolor(cav, 'tailReflector')
    kit.boolean(o, cav, 'DIFFERENCE', material_mode='TRANSFER')
    kit.boolean(o, tail_corner_fin(K, s, coll), 'UNION', material_mode='TRANSFER')
    return o


def tail_lamps(coll, parts_, K):
    """Stacked lenses on the rear corners (TAIL_BANDS), each cut from the glass skin, and behind
    them one housing (tail_housing)."""
    bands = TAIL_BANDS
    for S, s in (('L', 1), ('R', -1)):
        reg = tail_lamp_cutter(s)
        for k, (slot, z0, z1) in enumerate(bands):
            lo = z0 + (G if k < len(bands) - 1 else 0.0)
            hi = z1 - (G if k > 0 else 0.0)
            band = B.front_prism(mx([(0.3, lo), (BIG, lo), (BIG, hi), (0.3, hi)], s), -2.6, -1.5, shrink=0)
            o = B.cut_region(K.glass, 'tailLamp%d.%s' % (k, S), [reg, band], coll)
            recolor(o, slot)
            parts_[o.name] = o
        o = tail_housing(coll, K, s, 'tailReflector.' + S)
        kit.clean(o)
        kit.finish(o, 0.0012, 1, 30.0)
        parts_[o.name] = o


# ------------------------------------------------------------------ bumpers

# Type R centre opening, kept inside the face (the bumper corners turn back beyond x = 0.5)
INTAKE_XZ = [(-0.50, 0.262), (-0.488, 0.244), (-0.46, 0.240), (0.46, 0.240), (0.488, 0.244), (0.50, 0.262),
             (0.50, 0.364), (0.488, 0.382), (0.46, 0.386), (-0.46, 0.386), (-0.488, 0.382), (-0.50, 0.364)]
# dark diamond mesh set back in the opening: strips at +-45 deg, `pitch` apart, `w` wide (seen from the
# front) and MESH_T deep, the two sets a fraction apart in depth so they never share a face. In the
# photo the intake is a dark recess (a black top wall, a fine mesh with no legible pattern) crossed by
# one bright bar: a coarse silver mesh near the face read as a chrome grating
MESH_PITCH, MESH_W, MESH_T, MESH_DEPTH = 0.009, 0.0025, 0.0015, 0.022
BAR_Z, BAR_H, BAR_T, BAR_DEPTH = 0.300, 0.008, 0.005, 0.010        # the bar stands proud of the mesh
# the grille slot's black mesh: finer, 12 mm behind the nose skin (the floor is 30 mm in)
GRILLE_PITCH, GRILLE_W, GRILLE_DEPTH = 0.007, 0.002, 0.012

# corner vents: small vertical recesses on the bumper corners, outboard of the intake (reference
# photo; taller than wide). Front-view centre and size; the pocket stands square to the face.
# Measured by back-projecting the photo through a camera fitted to its landmarks: the vent spans
# about z 0.22-0.34 and sits one vent width outboard of the intake's end.
VENT_XZ, VENT_W, VENT_H, VENT_R = (0.600, 0.282), 0.075, 0.115, 0.016
_VENT = {}


def face_frame(tree, x, z, s=1):
    """Point and horizontal outward normal (design) of the outer shape at front-view (s * x, z)."""
    loc, nrm, _, _ = tree.ray_cast(V(s * x, 3.0, z), Vector((0.0, 1.0, 0.0)))
    if loc is None:
        raise RuntimeError('no bumper face at (%.3f, %.3f)' % (s * x, z))
    n = Vector((nrm.x, -nrm.y, 0.0)).normalized()
    return Vector((loc.x, -loc.y, loc.z)), n


def face_f(tree, x, z, back=False):
    """f of the outer shape at front-view (x, z): a ray along -f from the front, or (back) along +f
    from behind."""
    if back:
        loc = tree.ray_cast(V(x, -3.0, z), Vector((0.0, -1.0, 0.0)))[0]
    else:
        loc = tree.ray_cast(V(x, 3.0, z), Vector((0.0, 1.0, 0.0)))[0]
    if loc is None:
        raise RuntimeError('no %s face at (%.3f, %.3f)' % ('rear' if back else 'bumper', x, z))
    return -loc.y


def normal_prism(poly_uv, c, n, t0, t1):
    """Prism of a (u, v) outline in the plane through design point c square to the horizontal
    normal n (u horizontal, v up), from t0 to t1 along n."""
    up = Vector((0.0, 0.0, 1.0))
    u = up.cross(n).normalized()
    p = kit.ccw(poly_uv)
    k = len(p)
    verts = [V(*(c + u * a + up * b + n * t)) for t in (t0, t1) for a, b in p]
    faces = [list(range(k)), list(range(k, 2 * k))] + [[i, (i + 1) % k, k + (i + 1) % k, k + i] for i in range(k)]
    return verts, faces


def corner_vent(s, K, grow=0.0):
    """(pocket prism, centre, normal) of the left / right corner vent, grown by `grow` (< 0 shrinks)."""
    key = (s, round(grow, 6))
    if key not in _VENT:
        c, n = face_frame(K.bump_tree, VENT_XZ[0], VENT_XZ[1], s)
        rr = kit.fillet_poly(kit.rect(VENT_W, VENT_H), VENT_R, 4)
        poly = kit.offset_poly(kit.ccw(rr), grow) if grow else rr
        _VENT[key] = (normal_prism(poly, c, n, -0.07, 0.07), c, n)
    return _VENT[key]


def recess(coll, name, K, grow_region, cav_region, floor30=True):
    """A closed dark pocket behind an opening in the bumper skin, from the lower-bumper solids:
    walls from 3 mm in (a 1.5 mm ledge inside the opening's cut edge; the outer ring hides in the
    paint skin) back to a floor 30 mm in (or, floor30=False, wherever cav_region's back face lies)."""
    o = B.cut_region(K.bump_deep, name, [grow_region], coll)
    kit.boolean(o, dup(K.bump3, coll), 'INTERSECT')
    recolor(o, 'trim')
    cav = B.cut_region(K.bump0, name + '.cav', [cav_region], coll)
    if floor30:
        kit.boolean(cav, dup(K.bump30, coll), 'DIFFERENCE')
    return o, cav


# the corner vent is a scoop (photo): its floor ramps from VENT_DEPTH[0] under the face at the inboard
# edge to VENT_DEPTH[1] at the outboard one, where the last VENT_DARK of the width is the dark duct
# mouth. A square pocket 30 mm deep showed only shadowed walls and read as a black sticker.
VENT_DEPTH, VENT_DARK = (0.008, 0.042), 0.30


def vent_scoop(s, K):
    """(cavity prism with the ramped back face, Blender axis, Blender centre, Blender u, s): the vent
    outline shrunk 1.5 mm, from 7 cm proud of the face back to the ramp."""
    _, c, n = corner_vent(s, K)
    rr = kit.offset_poly(kit.ccw(kit.fillet_poly(kit.rect(VENT_W, VENT_H), VENT_R, 4)), -0.0015)
    up = Vector((0.0, 0.0, 1.0))
    u = up.cross(n).normalized()
    k = len(rr)

    def depth(a):
        r = min(1.0, max(0.0, (s * a + 0.5 * VENT_W) / VENT_W))     # 1 at the inboard edge, 0 outboard
        return VENT_DEPTH[1] + (VENT_DEPTH[0] - VENT_DEPTH[1]) * r
    verts = [V(*(c + u * a + up * b + n * 0.07)) for a, b in rr] + [V(*(c + u * a + up * b - n * depth(a))) for a, b in rr]
    faces = [list(range(k)), list(range(k, 2 * k))] + [[i, (i + 1) % k, k + (i + 1) % k, k + i] for i in range(k)]
    bl = lambda d: Vector((d.x, -d.y, d.z))
    return (verts, faces), bl(n), V(*c), bl(u)


def _strip_rings(tree, p0, p1, depth, w, t, step=0.012):
    """Rings of a flat strip from front-view point p0 to p1 (x, z), `w` wide in the face and `t` deep,
    its front face `depth` behind the outer shape (`tree`) at every corner."""
    d = Vector((p1[0] - p0[0], p1[1] - p0[1]))
    L = d.length
    d /= L
    q = Vector((-d.y, d.x)) * (w / 2)
    n = max(2, int(math.ceil(L / step)))
    rings = []
    for k in range(n + 1):
        c = Vector(p0) + d * (L * k / n)
        ring = []
        for sq, dt in ((-1, 0.0), (1, 0.0), (1, t), (-1, t)):
            x, z = c + q * sq
            ring.append((x, face_f(tree, x, z) - depth - dt, z))
        rings.append(ring)
    return rings


def lattice(coll, tree, poly, name, pitch, w, depth, slot='meshDark'):
    """Diamond mesh behind a front opening `poly`: two sets of strips at +-45 deg unioned into one
    lattice, `depth` behind the outer shape, clipped to the opening grown by 1 mm (so every strip end
    sits in the recess wall)."""
    xs = [x for x, _ in poly]
    zs = [z for _, z in poly]
    x0, x1, z0, z1 = min(xs) - 0.01, max(xs) + 0.01, min(zs) - 0.01, max(zs) + 0.01
    sets = []
    step = pitch * math.sqrt(2.0)
    for sgn, dz in ((1, 0.0), (-1, MESH_T * 0.8)):
        # lines x = c + sgn * z over the bounding box (the clip below trims them to the opening)
        b = kit.Builder()
        c_lo, c_hi = (x0 - z1, x1 - z0) if sgn > 0 else (x0 + z0, x1 + z1)
        c = c_lo + 0.5 * step
        while c < c_hi:
            za, zb = (max(z0, x0 - c), min(z1, x1 - c)) if sgn > 0 else (max(z0, c - x1), min(z1, c - x0))
            if zb - za > 0.004:
                p0, p1 = (c + sgn * za, za), (c + sgn * zb, zb)
                b.add_mesh(loft_rings(_strip_rings(tree, p0, p1, depth + dz, w, MESH_T)), slot)
            c += step
        sets.append(b.build('%s.mesh%d' % (name, len(sets)), coll))
    lat = sets[0]
    kit.boolean(lat, sets[1], 'UNION')
    return lat


def _clip_to(o, poly):
    kit.boolean(o, kit.cutter_obj(B.front_prism(kit.offset_poly(kit.ccw(poly), 0.001), 1.80, 2.6, shrink=0)), 'INTERSECT')


def intake_mesh(coll, K):
    """The intake's dark mesh and its one bright bar, clipped to the opening grown by 1 mm."""
    lat = lattice(coll, K.bump_tree, INTAKE_XZ, 'intake', MESH_PITCH, MESH_W, MESH_DEPTH)
    xs = [x for x, _ in INTAKE_XZ]
    bar = kit.Builder()
    bar.add_mesh(loft_rings(_strip_rings(K.bump_tree, (min(xs) - 0.002, BAR_Z), (max(xs) + 0.002, BAR_Z),
                                         BAR_DEPTH, BAR_H, BAR_T, 0.02)), 'mesh')
    kit.boolean(lat, bar.build('intake.bar', coll), 'UNION', material_mode='TRANSFER')
    _clip_to(lat, INTAKE_XZ)
    return lat


def front_bumper_details(coll, parts_, K):
    """Intake recess with the silver mesh and bar, the corner vents, and the Type R lip."""
    o, cav = recess(coll, 'intake', K,
                    B.front_prism(kit.offset_poly(kit.ccw(INTAKE_XZ), 0.004), 1.80, 2.6, shrink=0),
                    B.front_prism(kit.offset_poly(kit.ccw(INTAKE_XZ), -0.0015), 1.80, 2.6, shrink=0))
    # the floor is the dark bay behind the mesh ('grilleDark', as behind the grille slot)
    slot_faces(cav, lambda p: 'trim' if abs(p.normal.y) < 0.3 else 'grilleDark')
    kit.boolean(o, cav, 'DIFFERENCE', material_mode='TRANSFER')
    m = intake_mesh(coll, K)
    kit.boolean(o, m, 'UNION', material_mode='TRANSFER')
    kit.clean(o)
    kit.finish(o, 0.0006, 1, 30.0)
    parts_['intake'] = o
    for S, s in (('L', 1), ('R', -1)):
        # a scoop moulded into the bumper (photo): body-colour walls and ramp, dark only in the duct
        # mouth along the deep outboard edge (vent_scoop)
        scoop, axis, cb, ub = vent_scoop(s, K)
        v, cav = recess(coll, 'vent.' + S, K, corner_vent(s, K, 0.004)[0], scoop, floor30=False)
        recolor(v, 'paint')

        def vent_slot(p, axis=axis, cb=cb, ub=ub, s=s):
            r = (s * (p.center - cb).dot(ub) + 0.5 * VENT_W) / VENT_W
            return 'grilleDark' if abs(p.normal.dot(axis)) > 0.5 and r < VENT_DARK else 'paint'
        slot_faces(cav, vent_slot)
        kit.boolean(v, cav, 'DIFFERENCE', material_mode='TRANSFER')
        kit.clean(v)
        kit.finish(v, 0.001, 1, 30.0)
        parts_['vent.' + S] = v
    front_lip(coll, parts_)


def seam_backing(coll, parts_, K, seam):
    """Dark strips behind the bumper / fender shut lines above each front arch (the diagonal `seam`
    and the short run along the bumper line behind the lamp), from 3 mm in (inside the paint skin)
    to 50 mm in. The body is hollow: an open shut line there showed the liner, or the sky through
    the car where the slots on both sides lined up. Kept 4 mm clear of the arch cut."""
    (f0, z0), (f1, z1) = seam
    L = math.hypot(f1 - f0, z1 - z0)
    u = ((f1 - f0) / L, (z1 - z0) / L)                   # down the seam
    p = (-u[1], u[0])                                    # across it, toward the bumper
    w = 0.015

    def on(line_off, z):                                 # point on the seam line offset across it, at height z
        t = (z - z0) / u[1]
        return (f0 + u[0] * t + p[0] * line_off, z0 + u[1] * t + p[1] * line_off)
    fl = on(0.0, 0.42)
    a = (fl[0] - p[0] * w, fl[1] - p[1] * w)
    b = (fl[0] + p[0] * w, fl[1] + p[1] * w)
    ta = (0.53 - a[1]) / -u[1]
    tb = (0.50 - b[1]) / -u[1]
    poly = [a, b, (b[0] - u[0] * tb, 0.50), (1.582, 0.50), (1.582, 0.53), (a[0] - u[0] * ta, 0.53)]
    region, arches = kit.Builder(), kit.Builder()
    for s in (1, -1):
        region.add_mesh(B.side_prism(poly, *side_x(s), shrink=0), 'interior')
        arches.add_mesh(arch_cutter_mesh(D.FA, s, 0.004), 'interior')
    o = B.cut_region(K.nose_deep, 'seamBacking', [], coll)
    kit.boolean(o, region.build('seam.region', coll, smooth=False), 'INTERSECT')
    kit.boolean(o, dup(K.nose3, coll), 'INTERSECT')
    kit.boolean(o, arches.build('seam.arches', coll, smooth=False), 'DIFFERENCE')
    recolor(o, 'trim')
    kit.clean(o, 1e-4)
    kit.finish(o, 0.0, 1, 30.0)
    parts_['seamBacking'] = o


def rear_seam_backing(coll, parts_, K):
    """The rear counterpart of seam_backing: dark strips 2 cm tall behind the rear bumper / quarter
    shut line (horizontal at BUMPER_TOP_R from the arch, the step up at BUMPER_STEP_F, and the short
    run along the lamp bottom), from 6 mm in (inside the 10 mm skins) to 30 mm in. From 6 mm so they
    also cover the liners' ends (12 mm in) next to the arch. Kept 4 mm clear of the arch cut and
    clear of the tail lamp housing. Without them a seam-height side view saw through the car."""
    w, f0, f1 = 0.010, D.BUMPER_SEAM_R + 0.02, D.BUMPER_STEP_F
    z0, z1 = D.BUMPER_TOP_R, D.TAIL_LAMP_LOW
    poly = [(f0, z0 - w), (f1 - w, z0 - w), (f1 - w, z1 - w), (f1 - 0.03, z1 - w), (f1 - 0.03, z1 + w),
            (f1 + w, z1 + w), (f1 + w, z0 + w), (f0, z0 + w)]
    region, clear = kit.Builder(), kit.Builder()
    for s in (1, -1):
        region.add_mesh(B.side_prism(poly, *side_x(s), shrink=0), 'interior')
        clear.add_mesh(arch_cutter_mesh(D.RA, s, 0.004), 'interior')
    o = B.cut_region(K.rear6, 'seamBackingR', [], coll)
    kit.boolean(o, region.build('seamR.region', coll, smooth=False), 'INTERSECT')
    kit.boolean(o, dup(K.rear30, coll), 'DIFFERENCE')
    kit.boolean(o, clear.build('seamR.arches', coll, smooth=False), 'DIFFERENCE')
    for s in (1, -1):
        kit.boolean(o, kit.cutter_obj(tail_lamp_cutter(s, -(HOUSING_GROW + 0.001))), 'DIFFERENCE')
    recolor(o, 'trim')
    kit.clean(o, 1e-4)
    kit.finish(o, 0.0, 1, 30.0)
    parts_['seamBackingR'] = o


def arch_cutter_mesh(a, s, grow=0.0):
    """The arch cut (car.arch_cutter) as a lathe mesh: x from 0.40 outboard, radius ARCH_R + grow."""
    x0, x1 = (0.40, BIG) if s > 0 else (-BIG, -0.40)
    return lathe([(0.0, x0), (D.ARCH_R + grow, x0), (D.ARCH_R + grow, x1), (0.0, x1)], 128, 'x',
                 center=(0.0, a, D.ARCH_Z))


# Type R lip (photos 49, 62, 64, 89): a body-colour chin under the whole bumper, from the front arch
# round the nose to the other arch, where it ends in a flat face. In the side profile its front runs
# on flush with the bumper face above the seam (LIP_OUT proud of it), upright, and rounds under into a
# flat bottom at LIP_BOT; it is 10 cm tall at the nose and 8.5 cm at the arch ends (LIP_TOP), with
# the seam just under the intake and the corner vents. Just under the seam the face leans back to it,
# standing LIP_STEP proud, so the seam reads as a fine line with a highlight on the lip's rounded top
# edge. Every section is laid off the bumper's own surface, found by ray casts at each height and
# smoothed along the outline (the bumper's lower corner carries a crease that would print a step into
# the lip). Its back runs LIP_BACK inside the bumper skin and its bottom just under the underside, so
# no slot opens into the body.
LIP_OUT = (0.010, 0.008)          # front face proud of the bumper at the seam: centre, corners
LIP_TOP = (0.230, 0.215)          # seam height: centre, corners
LIP_BOT, LIP_LEAN = 0.128, 0.022  # bottom; the face's lean back to the seam starts this far under it
LIP_STEP, LIP_BACK = 0.002, 0.030
LIP_REF = 0.15                    # outline reference height
LIP_END_F = 1.595                 # ends about 3 cm ahead of the front arch (flat end face in the arch's shadow)


def _lip_outline(tree):
    """Bumper outline at LIP_REF, right half: (x, f) from the arch end to the tip, resampled every
    8 mm, with outward normals. Ray casts along the plan normals give the bumper's inset from the
    plan outline; the inset is smoothed along the outline (the bumper's lower corner carries a
    crease that would print a step into the lip), then laid off the smooth plan curve."""
    raw = []
    for (x, f), (nx, nf) in B.plan_curve(D.PLAN_F, 240):
        if f < LIP_END_F - 0.03:
            continue
        hit = tree.ray_cast(V(x + nx * 0.3, f + nf * 0.3, LIP_REF), Vector((-nx, nf, 0.0)))[0]
        # (a ray that finds no face near the plan outline went through the arch opening)
        if hit is not None and math.hypot(hit.x - x, -hit.y - f) < 0.08:
            raw.append(((x, f), (nx, nf), math.hypot(hit.x - x, -hit.y - f)))
    d = [r[2] for r in raw]
    for _ in range(4):
        d = [sum(d[max(0, i - 6):i + 7]) / len(d[max(0, i - 6):i + 7]) for i in range(len(d))]
    pts = [(x - nx * di, f - nf * di) for ((x, f), (nx, nf), _), di in zip(raw, d)]
    # trim to LIP_END_F, close on x = 0, resample evenly
    k = next(i for i, p in enumerate(pts) if p[1] >= LIP_END_F)
    if k > 0:
        (xa, fa), (xb, fb) = pts[k - 1], pts[k]
        t = (LIP_END_F - fa) / (fb - fa)
        pts = [(xa + (xb - xa) * t, LIP_END_F)] + pts[k:]
    pts[-1] = (0.0, pts[-1][1])
    L = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    pts = B._resample_open(pts, max(8, int(L / 0.008)))
    pts[-1] = (0.0, pts[-1][1])
    # normals from the whole (mirrored) outline, so the tip's is square to the centreline
    full = pts + [(-x, f) for x, f in reversed(pts[:-1])]
    out = []
    for i, p in enumerate(pts):
        a, b = full[max(0, i - 2)], full[i + 2]
        tx, tf = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, tf)
        out.append((p, (tf / l, -tx / l)))
    return out


def _surface_offsets(tree, outline, zs):
    """The bumper surface at heights zs (one per outline station), as offsets along each outline normal
    from the outline point (outward +), smoothed along the outline. A station whose ray misses keeps
    its neighbour's."""
    d, last = [], 0.0
    for ((x, f), (nx, nf)), z in zip(outline, zs):
        hit = tree.ray_cast(V(x + nx * 0.3, f + nf * 0.3, z), Vector((-nx, nf, 0.0)))[0]
        if hit is not None and math.hypot(hit.x - x, -hit.y - f) < 0.12:
            last = (hit.x - x) * nx + (-hit.y - f) * nf
        d.append(last)
    for _ in range(4):
        d = [sum(d[max(0, i - 6):i + 7]) / len(d[max(0, i - 6):i + 7]) for i in range(len(d))]
    return d


def front_lip(coll, parts_):
    tree = tri_tree(parts_['bumperF'].data)
    outline = _lip_outline(tree)
    ks = [smooth01((abs(x) - 0.25) / 0.50) for (x, f), _ in outline]
    tops = [LIP_TOP[0] + (LIP_TOP[1] - LIP_TOP[0]) * k for k in ks]
    rings = []
    for ((x, f), (nx, nf)), k, zt, dt in zip(outline, ks, tops, _surface_offsets(tree, outline, tops)):
        p = dt + LIP_OUT[0] + (LIP_OUT[1] - LIP_OUT[0]) * k
        top = min(dt + LIP_STEP, p - 0.006)         # the face's upper part always leans back to the seam
        sec = [(-LIP_BACK, LIP_BOT), (p, LIP_BOT), (p, zt - LIP_LEAN), (top, zt - 0.004), (top, zt), (-LIP_BACK, zt)]
        sec = kit.fillet_poly(sec, 0.0, 4, radii=[0.0, 0.028, 0.02, 0.004, 0.0015, 0.0])
        rings.append([(x + nx * d, f + nf * d, z) for d, z in sec])
    # the other half is the mirror (the tip ring is shared)
    rings = rings + [[(-x, f, z) for x, f, z in r] for r in reversed(rings[:-1])]
    v, fc = loft_rings(rings, True, True)
    o = kit.obj_from_pydata('lip', v, fc, ['paint'], coll=coll)
    kit.fix_normals(o)
    kit.finish(o, 0.0015, 2, 30.0)
    parts_['lip'] = o


# ------------------------------------------------------------------ rear face and bumper

# licence-plate recess (the blueprint's outer ring), carved PLATE solid-deep into the hatch panel, and
# the crease running from its top corners out to the lamps
PLATE_XZ = kit.fillet_poly(kit.rect(0.638, 0.241, 0.0, 0.7155), 0.05, 6)
PLATE_WALL = 0.008              # wall round the recess, from the panel's 8 mm skin back to the 30 mm floor
CREASE_Z, CREASE_W, CREASE_D = 0.808, 0.004, 0.0015


def _crease(K, s):
    """V groove along the rear face at CREASE_Z, from inside the plate recess out past the lamp edge:
    rings of a triangle, its apex CREASE_D under the face at every x (found by ray casts)."""
    rings = []
    x0, x1 = 0.30, tail_lamp_x(CREASE_Z) + 0.01
    for k in range(15):
        x = x0 + (x1 - x0) * k / 14
        fa = face_f(K.rear_tree, s * x, CREASE_Z, back=True)
        h, o = CREASE_W / 2, 0.008                          # half opening at the face; reaches 8 mm outside
        k_out = 1.0 + o / CREASE_D
        rings.append([(s * x, fa + CREASE_D, CREASE_Z), (s * x, fa + CREASE_D - k_out * CREASE_D, CREASE_Z + k_out * h),
                      (s * x, fa + CREASE_D - k_out * CREASE_D, CREASE_Z - k_out * h)])
    return loft_rings(rings)


def hatch_panel(coll, K, cutters):
    """Hatch lower panel carved from the rear solids (B.cut_shell): the plate recess 12 mm deep (floor on
    the shape 12 mm in), walled back to the shape 30 mm in, and the crease grooves."""
    recess = B.solid_minus(B.front_prism(PLATE_XZ, -2.6, -1.80, shrink=0), K.rear12, coll, 'plate.cut')
    block = B.solid_minus(B.front_prism(kit.offset_poly(kit.ccw(PLATE_XZ), PLATE_WALL), -2.6, -1.80, shrink=0),
                          K.rear30, coll, 'plate.block')
    creases = [kit.cutter_obj(_crease(K, s), 'crease') for s in (1, -1)]
    return B.cut_shell(K.rear0, K.R_NEAR, 'hatchPanel', coll, cutters, [recess] + creases, [block])


# valance notch: the bumper's lower edge steps up from z 0.19 at the corners to 0.246 across the centre
# (blueprint rear view), with S ramps at |x| 0.36-0.54; it runs forward to f -1.93, where a wall closes it
_VALANCE_R = [(0.0, 0.246), (0.34, 0.246), (0.38, 0.2435), (0.42, 0.234), (0.46, 0.219), (0.50, 0.203),
              (0.53, 0.19), (0.56, 0.17), (0.56, 0.10), (0.0, 0.10)]
VALANCE_XZ = _VALANCE_R[:-1] + [(-x, z) for x, z in reversed(_VALANCE_R[1:-1])]
VALANCE_F = -1.93


def valance_notch(grow=0.0):
    """The notch prism, grown by `grow` (the bumper's inner solid takes it grown by the skin, so the
    notch gets a 10 mm ceiling and front wall instead of opening into the hollow bumper)."""
    poly = kit.offset_poly(kit.ccw(VALANCE_XZ), grow) if grow else VALANCE_XZ
    return B.front_prism(poly, -2.6, VALANCE_F + grow, shrink=0)


def valance_wall(o):
    """The notch's front wall (on the plane f = VALANCE_F, facing back) stands for the dark underbody
    behind the bumper: 'trim'. In paint the step barely read from behind."""
    me = o.data
    names = [m.name for m in me.materials]
    slot = kit.mats.get('trim')
    if slot.name not in names:
        me.materials.append(slot)
        names.append(slot.name)
    k, y = names.index(slot.name), -VALANCE_F
    for p in me.polygons:
        if p.normal.y > 0.9 and all(abs(me.vertices[i].co.y - y) < 1e-4 for i in p.vertices):
            p.material_index = k


# exhaust (blueprint rear view, car's right): the silencer's oval end under the valance step, and the
# tip, a hollow pipe with a rolled lip whose bore is closed by a dark disc
MUFFLER_XZ, MUFFLER_HW, MUFFLER_HH = (-0.39, 0.184), 0.115, 0.060
MUFFLER_F = (VALANCE_F + 0.003, -1.975)       # front end buried 3 mm in the notch's front wall
TIP_XZ, TIP_R, TIP_WALL, TIP_OUT = (-0.388, 0.180), 0.042, 0.005, 0.030   # TIP_OUT: lip behind the bumper face


def rear_bumper_details(coll, parts_, K):
    # silencer: a superellipse can clipped 3 mm inside the notch, so it hangs just under the ceiling
    ring = squircle(MUFFLER_HW, MUFFLER_HH, 2.6, 48, *MUFFLER_XZ)
    can = B.front_prism(ring, MUFFLER_F[1], MUFFLER_F[0], shrink=0)
    o = kit.obj_from_pydata('muffler', *can, ['mech'], coll=coll)
    kit.fix_normals(o)
    kit.boolean(o, kit.cutter_obj(B.front_prism(kit.offset_poly(kit.ccw(VALANCE_XZ), -0.003), -2.6, -1.0, shrink=0)),
                'INTERSECT')
    recolor(o, 'mech')
    kit.clean(o)
    kit.finish(o, 0.004, 2, 30.0)
    parts_['muffler'] = o
    # tip: out TIP_OUT behind the bumper's lower face, back into the silencer
    x, z = TIP_XZ
    lip = face_f(K.rear_tree, x, z + TIP_R + 0.012, back=True) - TIP_OUT     # face above the tip (the tuck-under)
    r, ri = TIP_R, TIP_R - TIP_WALL
    prof = [(r, MUFFLER_F[0] - lip - 0.01), (r, 0.004), (r - 0.0008, 0.0012), (r - 0.0025, 0.0),
            (ri + 0.0015, 0.0003), (ri, 0.0025), (ri, MUFFLER_F[0] - lip - 0.01)]
    b = kit.Builder()
    b.add_mesh(lathe(prof, 48, 'f', center=(x, lip, z), closed=True), 'steel')
    tip = b.build('exhaust', coll)
    # the bore's dark end, just inside the silencer's face ('grilleDark', the dark-cavity proxy:
    # 'interior' is reserved for faces a hole would show)
    d = kit.Builder()
    d.add_mesh(lathe([(0.0, 0.0), (ri + 0.001, 0.0), (ri + 0.001, 0.002), (0.0, 0.002)], 48, 'f',
                     center=(x, MUFFLER_F[1] - 0.004, z)), 'grilleDark')
    kit.boolean(tip, d.build('exhaust.bore', coll), 'UNION', material_mode='TRANSFER')
    kit.clean(tip)
    kit.finish(tip, 0.0, 1, 30.0)
    parts_['exhaust'] = tip


# ------------------------------------------------------------------ spoiler
#
# Roof spoiler (blueprint side and rear views): a body-colour wedge that carries the roof line on, seated
# on the roof and the top of the hatch glass back to the lift line, then lifting off the glass into a
# lip with a rounded trailing edge. Its ends roll down over the D-pillars as side caps: a flat top to
# |x| SPOILER_X0, a rolled shoulder (1.265 at |x| 0.575), then a steep side face down to the pillar at
# about |x| 0.61. The caps leave the pillar earlier than the centre leaves the glass (SPOILER_LIFT), and
# behind that their lower edge follows the blueprint's (SPOILER_CAP).
#
# It is built as a blob of per-x sections whose underside runs 2 cm below the body in the seated zone,
# minus the outer shape raised by SPOILER_SEAT: the seat is the body surface itself, 1 mm up, with no
# gap to float over and nothing sunk into the roof.
SPOILER_TOP = [(-1.17, 1.3105), (-1.195, 1.312), (-1.25, 1.307), (-1.31, 1.302), (-1.40, 1.293), (-1.45, 1.288),
               (-1.48, 1.283), (-1.50, 1.2795)]
SPOILER_TIP = (-1.4925, 0.025)            # trailing edge (centreline) and its thickness there
SPOILER_TIP_Z = 1.268                     # trailing edge centre height
SPOILER_LIFT = (-1.40, -1.33)             # the underside leaves the body: centre, caps (|x| >= 0.58)
SPOILER_CAP = [(-1.30, 1.201), (-1.33, 1.201), (-1.35, 1.209), (-1.38, 1.215), (-1.40, 1.219), (-1.42, 1.224),
               (-1.44, 1.229), (-1.46, 1.235), (-1.48, 1.247), (-1.50, 1.258), (-1.52, 1.268)]
SPOILER_X0, SPOILER_ROLL, SPOILER_CROWN = 0.47, (0.14, 0.11), 0.008   # flat top, shoulder (a, b), crown
SPOILER_SEAT, SPOILER_BURY = 0.001, 0.02
_SP_TOP = curve1(SPOILER_TOP)
_SP_CAP = curve1(SPOILER_CAP)


def _sp_drop(x):
    """How far the top sits under the centreline at |x|: a slight crown, then the rolled shoulder (an
    ellipse quadrant, vertical at SPOILER_X0 + a) and, past it, the side face straight down."""
    a, b = SPOILER_ROLL
    d = SPOILER_CROWN * (min(x, SPOILER_X0 + a) / SPOILER_X0) ** 2
    if x > SPOILER_X0:
        e = min(1.0, (x - SPOILER_X0) / a)
        d += b * (1.0 - math.sqrt(max(0.0, 1.0 - e * e)))
    return d


def _sp_front(x):
    """Leading edge f: slightly swept across the flat top, then back along the shoulder as the caps
    wrap down the pillars (blueprint side view: the cap's front runs down and back to f -1.30)."""
    if x <= SPOILER_X0:
        return -1.18 - 0.03 * (x / SPOILER_X0) ** 2
    e = min(1.0, (x - SPOILER_X0) / SPOILER_ROLL[0])
    return -1.21 - 0.09 * e * e


def _sp_plan_back(x):
    """Rear outline in plan: the full trailing edge to |x| 0.50, then rounding forward over the caps."""
    f_tip, f_end = SPOILER_TIP[0], -1.33
    if x <= 0.50:
        return f_tip
    e = min(1.0, (x - 0.50) / (SPOILER_X0 + SPOILER_ROLL[0] - 0.50))
    return f_tip + (f_end - f_tip) * (1.0 - math.sqrt(max(0.0, 1.0 - e * e)))


def _sp_section(tree, x, drop):
    """Closed (f, z) section at |x| (design), `drop` below the centre top: front face, rounded front
    corner, top, round trailing nose, underside."""
    f_tip, t_tip = SPOILER_TIP
    f_lift = SPOILER_LIFT[0] + (SPOILER_LIFT[1] - SPOILER_LIFT[0]) * smooth01((x - 0.50) / 0.08)
    z_lift = surface_z(tree, x, f_lift)
    # lip underside at the trailing edge: the centreline's, following the glass's crown
    z_tip = SPOILER_TIP_Z - 0.5 * t_tip + surface_z(tree, x, SPOILER_LIFT[0]) - surface_z(tree, 0.0, SPOILER_LIFT[0])

    def top(f):
        return _SP_TOP(f) - drop

    def under(f):
        if f >= f_lift:
            # buried in front of the lift line (the boolean with the body makes this the seat)
            u = surface_z(tree, x, f) - SPOILER_BURY * smooth01((f - f_lift) / 0.02)
            return min(u, top(f) - 0.01)
        u = z_lift + (z_tip - z_lift) * (f_lift - f) / (f_lift - f_tip)
        # never under the blueprint's cap line (fades in over 2 cm behind the lift: no crease)
        cap = _SP_CAP(f) - 0.1 * (1.0 - smooth01((f_lift - f) / 0.02))
        k = 0.004
        return 0.5 * (u + cap + math.sqrt((u - cap) ** 2 + k * k))
    f_le = _sp_front(x)
    # rear end: the plan outline, or further forward where the lip would get thinner than 5 mm
    f_te = max(_sp_plan_back(x), f_tip)
    f = f_le - 0.03
    while f > f_te:
        if top(f) - under(f) < 0.005:
            f_te = f + 0.001
            break
        f -= 0.001
    zt_le, zu_le = top(f_le), under(f_le)
    r = max(0.001, min(0.006, 0.45 * (zt_le - zu_le)))
    pts = [(f_le, zu_le), (f_le, zt_le - r)]
    for k in range(1, 5):
        a = 0.5 * math.pi * k / 4
        pts.append((f_le - r + r * math.cos(a), zt_le - r + r * math.sin(a)))
    n_top = 36
    fs = [f_le - r + (f_te - (f_le - r)) * (1 - math.cos(math.pi * k / n_top)) / 2 for k in range(1, n_top + 1)]
    pts += [(f, top(f)) for f in fs]
    zt, zu = top(f_te), under(f_te)
    m, rr = 0.5 * (zt + zu), 0.5 * (zt - zu)
    for k in range(1, 12):
        p = math.pi * k / 12
        pts.append((f_te - rr * math.sin(p), m + rr * math.cos(p)))
    pts += [(f, under(f)) for f in reversed(fs)]
    return pts


def spoiler(coll, parts_):
    tree = shape_tree(coll, (-0.8, -1.60, 1.05), (0.8, -1.05, 1.40))
    a, b = SPOILER_ROLL
    xs = [(x, _sp_drop(x)) for x in samples(0.0, SPOILER_X0, 12)]
    for k in range(1, 15):
        x = SPOILER_X0 + a * math.sin(0.5 * math.pi * k / 14)
        xs.append((x, _sp_drop(x)))
    # past the vertical, the side face runs on down into the pillar, so the end ring is inside the body
    xe, de = xs[-1]
    xs += [(xe + 0.0005, de + 0.02), (xe + 0.001, de + 0.05)]
    half = [[(x, f, z) for f, z in _sp_section(tree, x, d)] for x, d in xs]
    rings = [[(-x, f, z) for x, f, z in r] for r in reversed(half[1:])] + half
    v, fc = loft_rings(rings, True, True)
    o = kit.obj_from_pydata('spoiler', v, fc, ['paint'], coll=coll)
    kit.fix_normals(o)
    seat = dup(B.base_shape(coll), coll)
    seat.location.z += SPOILER_SEAT
    kit.boolean(o, seat, 'DIFFERENCE')
    recolor(o, 'paint')
    o.data.shade_smooth()
    # the seat faces meet the blob at a hard edge: split it, or smooth shading averaged the normals
    # across it and the 8 mm leading face shaded in dark teeth
    o.data.set_sharp_from_angle(angle=math.radians(30.0))
    kit.clean(o)
    kit.finish(o, 0.0, 1, 30.0)
    parts_['spoiler'] = o
    parts_['brakeLamp'] = brake_lamp(coll, o)


def brake_lamp(coll, spoiler_o, hw=0.12, z0=1.2625, z1=1.2735):
    """Third brake lamp: a red lens strip hugging the trailing edge's round, 1.2 mm proud, its back 4 mm
    inside the spoiler (rings found by rays along +f onto the nose), with rounded ends."""
    tree = tri_tree(spoiler_o.data)
    rings = []
    ends = [0.0, 0.002, 0.005, 0.009, 0.014]
    xs = [-hw + d for d in ends] + samples(-hw + 0.02, hw - 0.02, 10) + [hw - d for d in reversed(ends)]
    for x in xs:
        e = max(0.0, (abs(x) - (hw - 0.012)) / 0.012)
        k = math.sqrt(max(0.04, 1.0 - e * e))
        zc, h = 0.5 * (z0 + z1), 0.5 * (z1 - z0) * k
        outer, inner = [], []
        for j in range(6):
            z = zc - h + 2 * h * j / 5
            loc, nrm, _, _ = tree.ray_cast(V(x, -1.7, z), Vector((0.0, -1.0, 0.0)))
            if loc is None:
                raise RuntimeError('brake lamp off the spoiler at (%.3f, %.3f)' % (x, z))
            outer.append(loc + nrm * (0.0012 * k))
            inner.append(loc - nrm * 0.004)
        rings.append(outer + list(reversed(inner)))
    b = kit.Builder()
    b.add_mesh(kit.loft(rings), 'lensRed')
    o = b.build('brakeLamp', coll)
    kit.finish(o, 0.0, 1, 30.0)
    return o


# ------------------------------------------------------------------ wipers

def _sweep_rect(path, normals, w, h, lift=0.0):
    """Closed loft of a w x h rectangle along a Blender-space path: h along the given normals, w across
    (normal x tangent), the section's underside `lift` off the path."""
    rings = []
    n = len(path)
    for i, (p, nrm) in enumerate(zip(path, normals)):
        t = (path[min(n - 1, i + 1)] - path[max(0, i - 1)]).normalized()
        nn = (nrm - t * nrm.dot(t)).normalized()
        side = t.cross(nn).normalized()
        c = p + nn * lift
        rings.append([c + side * (a * w / 2) + nn * (b * h) for a, b in ((-1, 0), (1, 0), (1, 1), (-1, 1))])
    return kit.loft(rings)


def wipers(coll, parts_):
    """Front wipers parked along the windshield base. Each is one closed piece: a blade swept along
    the glass (rings square to the glass, found by ray casts), an arm down to a pivot on the cowl."""
    glass, cowl = tri_tree(parts_['windshield'].data), tri_tree(parts_['cowl'].data)
    up = Vector((0.0, 0.0, 1.0))
    pieces = []
    for x0, x1 in ((-0.56, 0.02), (0.06, 0.60)):
        path, nrms = [], []
        for k in range(11):
            x = lerp(x0, x1, k / 10)
            f = 0.905 - 0.185 * (min(abs(x), 0.72) / 0.70) ** 2.2 - 0.045
            loc, nrm, _, _ = glass.ray_cast(V(x, f, 2.0), -up)
            if loc is None:
                raise RuntimeError('wiper off the windshield at x %.3f' % x)
            path.append(loc)
            nrms.append(nrm)
        # the blade: 12 x 16 mm, its underside 0.6 mm off the glass
        o = kit.obj_from_pydata('wiper', *_sweep_rect(path, nrms, 0.012, 0.016, 0.0006), ['trim'], coll=coll)
        kit.fix_normals(o)
        # arm from the pivot on the cowl to the blade's outer third, seated 2.6 mm into the blade's top;
        # its first ring is buried in the boss (4-12 mm up, boss top at 14 mm). The arm and the boss
        # are swept / lathed inside out, so their normals are fixed before the unions: an inverted
        # solid left doubled vertices that kit.clean welded into non-manifold edges
        k = 7 if x1 > 0.3 else 3
        px = x1 - 0.08 if x1 > 0.3 else x0 + 0.08
        piv = cowl.ray_cast(V(px, 0.86, 2.0), -up)[0]
        if piv is None:
            raise RuntimeError('wiper pivot off the cowl at x %.3f' % px)
        a0, a1 = piv + up * 0.008, path[k] + nrms[k] * 0.018
        mid = a0.lerp(a1, 0.5) + up * 0.006
        arm = _sweep_rect([a0, mid, a1], [up, up, nrms[k]], 0.014, 0.008, -0.004)
        kit.boolean(o, kit.cutter_obj(arm, 'wiper.arm'), 'UNION')
        # pivot boss standing on the cowl (its base 4 mm down in the cowl skin)
        cap = lathe([(0.0, 0.0), (0.018, 0.0), (0.018, 0.018), (0.0, 0.018)], 24, 'z', center=(piv.x, -piv.y, piv.z - 0.004))
        kit.boolean(o, kit.cutter_obj(cap, 'wiper.pivot'), 'UNION')
        pieces.append(o)
    o = pieces[0]
    kit.boolean(o, pieces[1], 'UNION')
    o.name = 'wipers'
    recolor(o, 'trim')
    kit.clean(o)
    o.data.shade_smooth()          # (the unions bring the arm and boss in flat shaded)
    kit.finish(o, 0.0015, 1, 30.0)
    parts_['wipers'] = o


# washer jets on the hood just ahead of the wipers (photo 67): small black nozzles on its top at
# |x| WASHER_X, their base sunk 2 mm into the hood, their nose pointing back at the glass
WASHER_X, WASHER_F = 0.21, 0.97


def washer_jets(coll, parts_):
    hood = tri_tree(parts_['hood'].data)
    b = kit.Builder()
    for s in (1, -1):
        loc, nrm, _, _ = hood.ray_cast(V(s * WASHER_X, WASHER_F, 2.0), Vector((0.0, 0.0, -1.0)))
        if loc is None:
            raise RuntimeError('washer jet off the hood at x %.2f' % (s * WASHER_X))
        n = Vector((nrm.x, nrm.y, nrm.z)).normalized()
        back = Vector((0.0, 1.0, 0.0))                          # toward the glass (Blender +y is -f)
        back = (back - n * back.dot(n)).normalized()
        side = n.cross(back)
        rings = []
        for t, w, h in ((-0.009, 0.0075, 0.004), (-0.004, 0.009, 0.008), (0.004, 0.009, 0.009), (0.009, 0.006, 0.007)):
            c = loc + back * t - n * 0.002
            rings.append([c + side * (w * u) + n * (h * (v + 1.0) / 2) for u, v in squircle(1.0, 1.0, 3.0, 20)])
        b.add_mesh(kit.loft(rings), 'trim')
    o = b.build('washerJets', coll)
    kit.finish(o, 0.0, 1, 30.0)
    parts_['washerJets'] = o


# ------------------------------------------------------------------ liners, floor, trim

def liners(coll, parts_, K):
    """Wheel-well liners: a band over each arch just inside the arch cut, and a wall behind the
    wheel. The band is built well past the body's side and clipped to the shape 12 mm in (K.in12),
    so its outer end follows the skin's inner face everywhere, round the bumper corner too (a
    constant outer x poked through the bumper just ahead of the front arch)."""
    bands, walls = kit.Builder(), kit.Builder()
    # upper arc only: from where the arch meets the sill line, over the top
    a0 = math.asin(max(-1.0, (0.15 - D.ARCH_Z) / D.ARCH_R))
    for a in (D.FA, D.RA):
        for s in (1, -1):
            prof = [(D.ARCH_R + 0.012, 0.40), (D.ARCH_R - 0.003, 0.40), (D.ARCH_R - 0.003, 1.0), (D.ARCH_R + 0.012, 1.0)]
            if s < 0:
                prof = [(r, -x) for r, x in reversed(prof)]
            v, f = lathe(prof, 96, 'x', center=(0.0, a, D.ARCH_Z), arc=math.pi - 2 * a0, phase=a0, closed=True)
            # cap both arc ends: the boolean below needs a closed solid
            f = f + [list(range(len(prof))), [len(v) - len(prof) + j for j in range(len(prof))]]
            bands.add(v, f, 'interior')
            # inner wall behind the wheel: the arch circle's segment above the sill line
            seg = [(a + (D.ARCH_R + 0.02) * math.cos(a0 + (math.pi - 2 * a0) * k / 96),
                    D.ARCH_Z + (D.ARCH_R + 0.02) * math.sin(a0 + (math.pi - 2 * a0) * k / 96)) for k in range(97)]
            walls.add_mesh(B.side_prism(seg, 0.405 * s, 0.42 * s, shrink=0), 'interior')
    o = bands.build('liners', coll)
    kit.boolean(o, dup(K.in12, coll), 'INTERSECT')
    recolor(o, 'interior')
    kit.append_builder(o, walls)
    kit.clean(o)
    kit.finish(o, 0.0015, 1, 30.0)
    parts_['liners'] = o
    # floor pan
    parts_['floor'] = kit.obj_from_pydata('floor', *kit.box((1.44, 3.25, 0.02), center=V(0.0, -0.125, 0.145)), ['interior'], coll=coll, smooth=False)


def build(coll, parts_, K):
    from . import side, cabin
    headlamps(coll, parts_, K)
    grille(coll, parts_, K)
    tail_lamps(coll, parts_, K)
    spoiler(coll, parts_)
    side.build(coll, parts_)
    wipers(coll, parts_)
    washer_jets(coll, parts_)
    liners(coll, parts_, K)
    cabin.cabin(coll, parts_)
    # red-backed H centred between the plate recess and the glass (blueprint: z 0.849-0.900, 6.5 cm wide)
    parts_['badgeR'] = badge_on(coll, 'badgeR', parts_['hatchPanel'], 0.875, front=False, w=0.065, h=0.05)
