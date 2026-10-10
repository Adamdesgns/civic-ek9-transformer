"""EK9 body-side details: the door mirrors on their sails, the body-side mouldings, the recessed door
handles and the front side repeaters.

Parts that sit on the skin are placed by ray casts on the outer shape (parts.shape_tree), so they
keep the same depth all round a curved panel: a point at depth d lies d inside the surface along the
ray. Positions are the blueprint's (side view) unless noted."""
import math
from mathutils import Vector
from . import kit, body as B, dims as D
from .body import G
from .kit import V
from .shape import loft_rings, squircle
from .parts import shape_tree, surface_x, samples, dup, recolor, _ring_solid


def _on_side(tree, s, pts_fz, depth):
    """Blender points of side-view (f, z) points `depth` inside the outer surface (along -x)."""
    out = []
    for f, z in pts_fz:
        x = surface_x(tree, f, z, s)
        if x is None:
            raise RuntimeError('no body side at (%.3f, %.3f)' % (f, z))
        out.append(V(s * (x - depth), f, z))
    return out


# ------------------------------------------------------------------ mirrors
#
# A large body-colour housing low on the door glass's front corner, sitting on the black sail (blueprint:
# head f 0.33-0.515, z 0.835-0.965; sail f 0.50-0.60 on the belt; the photo's housing hugs the glass
# corner). The housing is lofted from its rear rim to a blunt nose; its rings shrink toward an anchor
# on the inner, lower side, so the nose runs down into the sail instead of pulling away from it (the two
# overlap by 1.5 cm in f). The glass sits in a recess in the rear face.
MIRROR_F = (0.33, 0.515)                  # rear face, nose
MIRROR_XZ, MIRROR_HALF, MIRROR_EXP = (0.886, 0.90), (0.084, 0.066), 3.2
MIRROR_RECESS, MIRROR_RIM = 0.012, 0.006  # glass recess depth, rim width
SAIL_X = 0.835                            # sail's outer face


def _sail_outline():
    return kit.fillet_poly([(0.50, D.belt(0.50)), (0.60, D.belt(0.60)), (0.60, D.belt(0.60) + 0.02), (0.515, 0.885)],
                           0.0, 4, radii=[0.004, 0.006, 0.004, 0.010])


def mirrors(coll, parts_):
    f0, f1 = MIRROR_F
    xc, zc = MIRROR_XZ
    hw, hh = MIRROR_HALF
    ax, az = xc - 0.75 * hw, zc - 0.5 * hh
    ts = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6] + [0.6 + 0.4 * math.sin(0.5 * math.pi * k / 10) for k in range(1, 11)]
    sail = kit.ccw(_sail_outline())
    for S, s in (('L', 1), ('R', -1)):
        def ring(f, k, inset=0.0):
            cx, cz = ax + (xc - ax) * k, az + (zc - az) * k
            return [(s * x, f, z) for x, z in squircle(hw * k - inset, hh * k - inset, MIRROR_EXP, 48, cx, cz)]
        # recess floor, recess wall, rounded rim, then the shell forward to the nose
        rings = [ring(f0 + MIRROR_RECESS, 1.0, MIRROR_RIM), ring(f0 + 0.002, 1.0, MIRROR_RIM),
                 ring(f0, 1.0, MIRROR_RIM - 0.0015), ring(f0, 1.0, 0.0015), ring(f0 + 0.0015, 1.0)]
        for t in ts:
            k = 1.0 if t < 0.6 else math.sqrt(max(0.0025, 1.0 - ((t - 0.6) / 0.4) ** 2))
            rings.append(ring(f0 + (f1 - f0) * t, k))
        v, fc = loft_rings(rings, True, True)
        o = kit.obj_from_pydata('mirror.' + S, v, fc, ['paint'], coll=coll)
        kit.fix_normals(o)
        kit.finish(o, 0.0, 1, 30.0)
        parts_['mirror.' + S] = o
        # glass: a slab in the recess, 1.5 mm clear of its wall, its back sunk 2 mm into the floor
        g = squircle(hw - MIRROR_RIM - 0.0015, hh - MIRROR_RIM - 0.0015, MIRROR_EXP, 48, xc, zc)
        b = kit.Builder()
        b.add_mesh(loft_rings([[(s * x, f, z) for x, z in g] for f in (f0 + 0.004, f0 + MIRROR_RECESS + 0.002)]), 'mirror')
        parts_['mirrorGlass.' + S] = b.build('mirrorGlass.' + S, coll, smooth=False)
        # sail: the side-view triangle from inside the body out to SAIL_X, its outer edges rounded,
        # minus the outer shape, so it sits on the door top, the glass corner and the A-pillar
        rings = []
        for x, inset in ((0.70, 0.0), (SAIL_X - 0.004, 0.0), (SAIL_X - 0.0012, 0.0012), (SAIL_X, 0.004)):
            rings.append([V(s * x, f, z) for f, z in kit.offset_poly(sail, -inset)])
        o = kit.obj_from_pydata('mirrorBase.' + S, *kit.loft(rings), ['trim'], coll=coll)
        kit.fix_normals(o)
        kit.boolean(o, dup(B.base_shape(coll), coll), 'DIFFERENCE')
        recolor(o, 'trim')
        kit.clean(o)
        o.data.shade_smooth()
        o.data.set_sharp_from_angle(angle=math.radians(30.0))
        kit.finish(o, 0.0, 1, 30.0)
        parts_['mirrorBase.' + S] = o


# ------------------------------------------------------------------ body-side mouldings
#
# Body-colour protective strips along the door and the front of the quarter (photo; the blueprint's
# double line 3.4 cm apart), from behind the front arch to ahead of the rear arch, broken at the door
# shut lines. The section is a squircle standing MOULDING_PROUD out of the skin and 4 mm into it at
# every height (each point is laid off the surface found at its own height), so its rounded top and
# bottom edges meet the skin all along the tumbling flank.
MOULDING_F = (0.82, -1.02)
MOULDING_Z = (0.450, 0.463)               # centre height at the front and rear ends
MOULDING_HALF, MOULDING_PROUD, MOULDING_BURY = 0.017, 0.007, 0.004
MOULDING_SHUTS = (D.DOOR_F, -0.5612)      # door shut lines at the moulding (DOOR_REAR leans 1 cm)
MOULDING_END, MOULDING_CUT = 0.017, 0.004  # end rounding: the outer ends, the ends at a shut line


def side_mouldings(coll, parts_, tree):
    fa, fb = MOULDING_F
    hd = 0.5 * (MOULDING_PROUD + MOULDING_BURY)
    # each piece stops 0.5 mm short of its panel's edge (the panels stop G short of the shut line)
    gap = G + 0.0005
    pieces = [(fa, MOULDING_SHUTS[0] + gap, MOULDING_END, MOULDING_CUT),
              (MOULDING_SHUTS[0] - gap, MOULDING_SHUTS[1] + gap, MOULDING_CUT, MOULDING_CUT),
              (MOULDING_SHUTS[1] - gap, fb, MOULDING_CUT, MOULDING_END)]
    for S, s in (('L', 1), ('R', -1)):
        b = kit.Builder()
        for p0, p1, l0, l1 in pieces:
            ends = [0.0, 0.06, 0.2, 0.45, 0.75, 1.0]
            fs = [p0 - l0 * e for e in ends] + samples(p0 - l0, p1 + l1, max(2, int((p0 - p1 - l0 - l1) / 0.02)))[1:-1] + \
                 [p1 + l1 * e for e in reversed(ends)]
            rings = []
            for f in fs:
                e = max(0.0, (f - (p0 - l0)) / l0, ((p1 + l1) - f) / l1)
                k = max(0.12, math.sqrt(max(0.0, 1.0 - e * e)))
                zc = MOULDING_Z[0] + (MOULDING_Z[1] - MOULDING_Z[0]) * (fa - f) / (fa - fb)
                dc = -MOULDING_BURY + hd * k
                sec = squircle(MOULDING_HALF * k, hd * k, 3.0, 24)
                rings.append(_on_side(tree, s, [(f, zc + dz) for dz, _ in sec], 0.0))
                for p, (_, dd) in zip(rings[-1], sec):
                    p.x += s * (dc + dd)
            b.add_mesh(kit.loft(rings), 'paint')
        o = b.build('moulding.' + S, coll)
        kit.finish(o, 0.0, 1, 30.0)
        parts_['moulding.' + S] = o


# ------------------------------------------------------------------ door handles
#
# EK pull-up handle, about 4 cm under the shoulder crease (blueprint: f -0.462 to -0.272, z 0.687-0.724):
# a rounded pocket through the door skin (car.build), closed behind by a black cup (the skin is only
# 10 mm, so the pocket alone opened into the hollow door), a body-colour flap in its upper half (hinged
# on the cup's top wall) and the key barrel behind it.
HANDLE_FZ, HANDLE_SIZE, HANDLE_R = (-0.367, 0.7055), (0.19, 0.070), 0.032
HANDLE_POCKET = kit.fillet_poly(kit.rect(HANDLE_SIZE[0], HANDLE_SIZE[1], *HANDLE_FZ), HANDLE_R, 6)
HANDLE_FLOOR = kit.fillet_poly(kit.rect(0.16, 0.045, *HANDLE_FZ), 0.020, 6)
HANDLE_FLAP = kit.fillet_poly(kit.rect(0.145, 0.0312, -0.352, 0.718), 0.013, 6)
HANDLE_KEY = (-0.445, 0.705, 0.006)


def door_handles(coll, parts_, tree):
    P0 = kit.ccw(HANDLE_POCKET)
    for S, s in (('L', 1), ('R', -1)):
        cup = kit.Builder()
        rings = [_on_side(tree, s, kit.ccw(HANDLE_FLOOR), 0.012),          # floor
                 _on_side(tree, s, kit.offset_poly(P0, -0.0005), 0.003),   # recess wall's outer edge (a 0.5 mm ledge)
                 _on_side(tree, s, kit.offset_poly(P0, 0.003), 0.003),     # flange under the skin round the hole
                 _on_side(tree, s, kit.offset_poly(P0, 0.003), 0.016)]     # back
        cup.add_mesh(kit.loft(rings), 'paint')
        # key barrel: a short cylinder from the floor up to 2.5 mm under the skin, its face rounded
        kf, kz, kr = HANDLE_KEY
        circ = lambda r: [(kf + r * math.cos(2 * math.pi * j / 24), kz + r * math.sin(2 * math.pi * j / 24)) for j in range(24)]
        cup.add_mesh(kit.loft([_on_side(tree, s, circ(kr - 0.0015), 0.0025), _on_side(tree, s, circ(kr), 0.0035),
                               _on_side(tree, s, circ(kr), 0.015)]), 'trim')
        o = cup.build('handleCup.' + S, coll)
        kit.finish(o, 0.0, 1, 30.0)
        parts_['handleCup.' + S] = o
        F = kit.ccw(HANDLE_FLAP)
        flap = kit.Builder()
        flap.add_mesh(kit.loft([_on_side(tree, s, kit.offset_poly(F, -0.001), 0.002), _on_side(tree, s, F, 0.003),
                                _on_side(tree, s, F, 0.007), _on_side(tree, s, kit.offset_poly(F, -0.001), 0.008)]), 'paint')
        o = flap.build('handle.' + S, coll)
        kit.finish(o, 0.0, 1, 30.0)
        parts_['handle.' + S] = o


# ------------------------------------------------------------------ side repeaters
#
# Oval side marker on each front fender behind the arch (blueprint: f 0.808-0.897, z 0.59, 89 x 35 mm):
# a lens domed 2.5 mm proud in a 2 mm black bezel, both laid on the fender along its normal. Clear, as on
# the reference car (a small silvery oval); a solid amber one was the brightest spot on the flank.
REPEATER_FZ, REPEATER_HALF, REPEATER_EXP = (0.853, 0.59), (0.044, 0.017), 2.5
# (scale, grow, depth): the lens from 4 mm inside up its wall and over the dome; the bezel's closed
# profile (proud rim round the lens, both ends 4 mm inside)
LENS_RINGS = ((1.0, 0.0006, 0.004), (1.0, 0.0006, -0.0010), (0.93, 0.0, -0.0017), (0.75, 0.0, -0.0022), (0.45, 0.0, -0.0025))
BEZEL_RINGS = ((1.0, 0.002, 0.004), (1.0, 0.002, -0.0008), (1.0, 0.0012, -0.0016), (1.0, 0.0003, -0.0010),
               (1.0, -0.0002, 0.004))


def side_repeaters(coll, parts_, tree):
    f, z = REPEATER_FZ
    hw, hh = REPEATER_HALF
    for S, s in (('L', 1), ('R', -1)):
        loc, nrm, _, _ = tree.ray_cast(V(s * 1.5, f, z), Vector((-s, 0.0, 0.0)))
        if loc is None:
            raise RuntimeError('no fender at the repeater')
        n = nrm.normalized()
        a = Vector((0.0, -1.0, 0.0))
        a = (a - n * a.dot(n)).normalized()
        v = n.cross(a).normalized()
        if v.z < 0:
            v = -v

        def ring(scale, grow, depth):
            # grow: added to both half sizes (a squircle offset, near enough at these sizes)
            out = []
            for u, w in squircle((hw + grow) * scale, (hh + grow) * scale, REPEATER_EXP, 48):
                p = loc + a * u + v * w
                h = tree.ray_cast(p + n * 0.05, -n)[0]
                if h is None:
                    raise RuntimeError('repeater off the fender')
                out.append(h - n * depth)
            return out
        b = kit.Builder()
        b.add_mesh(kit.loft([ring(*r) for r in LENS_RINGS]), 'marker')
        o = b.build('repeater.' + S, coll)
        kit.finish(o, 0.0, 1, 30.0)
        parts_['repeater.' + S] = o
        b = kit.Builder()
        b.add_mesh(_ring_solid([ring(*r) for r in BEZEL_RINGS]), 'trim')
        o = b.build('repeaterBezel.' + S, coll)
        kit.finish(o, 0.0, 1, 30.0)
        parts_['repeaterBezel.' + S] = o


def build(coll, parts_):
    tree = shape_tree(coll, (-1.0, -1.10, 0.38), (1.0, 0.95, 0.80))
    mirrors(coll, parts_)
    side_mouldings(coll, parts_, tree)
    door_handles(coll, parts_, tree)
    side_repeaters(coll, parts_, tree)
