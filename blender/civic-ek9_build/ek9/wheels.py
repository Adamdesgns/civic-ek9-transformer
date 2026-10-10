"""Wheels: 195/50 R15 tyres on white five-spoke Volk Racing 15s (photos 50, 52, 62, 63): straight
spokes flaring into the rim, a nearly flat face over a shallow dish, a raised hub pad with five dark
lug nuts on the EK9's 114.3 mm circle and no centre cap, blue VOLK / RAYS decals on two spokes and a
blue valve cap. Red calipers on discs sized for the 15 in barrel.

Each corner is one object built in design space about its hub; profiles are (r, h) with h along
the axle, positive outboard. The hub is the object origin, so the game can spin and steer it as a
hub-centred node.
"""
import math
from mathutils import Vector, Matrix
from . import kit, decal, dims as D
from .kit import V
from .shape import lathe, spline2

SPOKES = 5
SPOKE0 = math.radians(18)           # first spoke's angle (from +f toward up): photo 62's spoke layout
# spoke face heights (outboard of the tyre's centre plane): the hub pad, and the lip ring's inner edge
PAD_H, R0 = 0.064, 0.058            # hub pad face, spoke root radius (buried in the pad)
DISH = 1.25                         # face rise exponent: near flat, a shallow dish toward the lip
# decals: (text, sub-text, spoke index, centre radius, length, sub-text length)
DECALS = (('VOLK', 'Racing Wheel', 0, 0.118, 0.050, 0.034), ('RAYS', 'ENGINEERING', 2, 0.122, 0.046, 0.044))
VALVE_ANGLE = math.radians(292)          # about 7 o'clock on the left side, next to a spoke (photo 62)


def tyre_profile(R, hw, rim):
    """Half section bead -> tread centre, mirrored. Knots are placed by the sidewall height, so they
    stay ordered for any rim."""
    hs = R - rim
    # the sidewall runs up from the bead behind the lip flange, widest at 0.45 hs, into a squarish
    # shoulder and a tread flat to 0.85 hw (a rounder shoulder read as a ballooning doughnut)
    k = [(rim + 0.004, hw * 0.86), (rim + 0.15 * hs, hw * 0.97), (rim + 0.45 * hs, hw * 1.0), (rim + 0.68 * hs, hw * 0.99),
         (R - 0.018, hw * 0.975), (R - 0.006, hw * 0.94), (R - 0.0015, hw * 0.89), (R, hw * 0.85), (R, 0.0)]
    half = spline2(k, 22)
    return half + [(r, -h) for r, h in reversed(half[:-1])]


def face_h(r, hw, rim):
    """Height of a spoke's face at radius r: flat at the hub pad, rising along a shallow dish to the
    lip ring's inner edge."""
    r_lip, top_lip = rim - 0.008, hw * 0.93
    s = min(1.0, max(0.0, (r - R0) / (r_lip - R0)))
    return PAD_H - 0.002 + (top_lip - PAD_H + 0.002) * s ** DISH


def spoke_dir(theta):
    return Vector((0.0, -math.cos(theta), math.sin(theta)))    # radial (Blender: f -> -y)


def spoke(theta, hw, rim, n=10):
    """One spoke, a closed loft along the radius (Blender points). Its face follows face_h; the root
    is buried in the hub pad and the tip in the barrel wall, so neither end shows a cut face. The
    section is drafted (the face narrower than the back) with chamfered face edges that catch a
    highlight line, and it flares toward the rim as the Volk's spokes do."""
    u = spoke_dir(theta)
    w = Vector((1.0, 0.0, 0.0)).cross(u)                       # tangential
    ax = Vector((1.0, 0.0, 0.0))
    r_lip, r1 = rim - 0.008, rim + 0.001
    rings = []
    for r in [R0 + (r_lip - R0) * k / (n - 1) for k in range(n)] + [r1]:
        t = (r - R0) / (r1 - R0)
        top = face_h(r, hw, rim) if r <= r_lip else hw * 0.93 + 0.0012
        width = 0.047 + 0.010 * t + 0.018 * max(0.0, (t - 0.70) / 0.30) ** 2
        depth = 0.030 + (0.022 - 0.030) * t
        c = u * r
        ring = []
        ch = min(0.005, 0.12 * width) / max(1e-6, depth)
        for a, b in ((-0.5, 0.0), (0.5, 0.0), (0.46, 1.0 - ch), (0.44 - 0.10, 1.0), (-0.44 + 0.10, 1.0), (-0.46, 1.0 - ch)):
            ring.append(c + w * (a * width) + ax * (top - depth + b * depth))
        rings.append(ring)
    return kit.loft(rings)


def decals(s, hw, rim):
    """The blue decals for the corner on side s, in its final (unmirrored) object space: laid on the
    spoke's face along its axis, reading left to right from outside the car, as in photo 62."""
    b = kit.Builder()
    out = Vector((float(s), 0.0, 0.0))
    right = Vector((0.0, float(s), 0.0))                        # screen right, seen from outside
    up = Vector((0.0, 0.0, 1.0))
    for text, sub, k, rc, length, sub_len in DECALS:
        u = spoke_dir(SPOKE0 + 2 * math.pi * k / SPOKES)
        base = u if u.dot(right) > 0 else -u                  # baseline reads left to right
        tup = right * (-base.dot(up)) + up * base.dot(right)   # the baseline turned +90 deg on screen
        # the name on the spoke's axis, the sub-text under it
        pts, faces, hgt = decal.text_mesh(text, length, shear=0.18)
        spts, sfaces, shgt = decal.text_mesh(sub, sub_len, shear=0.10)
        for P, F, dv in ((pts, faces, 0.2 * hgt), (spts, sfaces, -0.5 * hgt - 0.6 * shgt)):
            def place(a, c, u=u, base=base, tup=tup, dv=dv):
                q = u * rc + base * a + tup * (c + dv)
                return out * face_h(q.length, hw, rim) + q, out
            decal.plate(b, P, F, place, 'decalBlue')
    return b


def corner(a, s, wx, name, coll):
    R, hw, rim = D.TYRE_R, D.TYRE_W / 2, D.RIM_R
    b = kit.Builder()
    b.add_mesh(lathe(tyre_profile(R, hw, rim), 96, 'x', closed=True), 'rubber')
    # barrel with the outer and inner flanges (closed section)
    barrel = [(rim + 0.013, hw * 0.93), (rim + 0.013, hw * 0.80), (rim - 0.004, hw * 0.76), (rim - 0.012, hw * 0.66),
              (rim - 0.012, -hw * 0.66), (rim - 0.004, -hw * 0.76), (rim + 0.011, -hw * 0.82), (rim + 0.011, -hw * 0.90),
              (rim - 0.014, -hw * 0.90), (rim - 0.014, hw * 0.95)]
    b.add_mesh(lathe(barrel, 96, 'x', closed=True), 'rim')
    # the outer lip ring the spokes land on (white, with the face)
    lip = [(rim - 0.008, hw * 0.93), (rim - 0.003, hw * 0.955), (rim + 0.011, hw * 0.955), (rim + 0.013, hw * 0.93),
           (rim + 0.011, hw * 0.90), (rim - 0.008, hw * 0.88)]
    b.add_mesh(lathe(lip, 96, 'x', closed=True), 'rimLip')
    # hub pad: a raised disc round a centre recess (no cap: the hub and its nut show, photo 62)
    hub = [(0.030, 0.046), (0.030, PAD_H - 0.003), (0.033, PAD_H), (0.064, PAD_H), (0.070, PAD_H - 0.006),
           (0.070, hw * 0.10), (0.030, hw * 0.10)]
    b.add_mesh(lathe(hub, 64, 'x', closed=True), 'rim')
    b.add_mesh(lathe([(0.0, 0.046), (0.030, 0.046), (0.030, 0.040), (0.0, 0.040)], 32, 'x'), 'darkSteel')
    b.add_mesh(lathe([(0.0, 0.058), (0.0125, 0.058), (0.0125, 0.045), (0.0, 0.045)], 6, 'x'), 'darkSteel')
    # five dark lug nuts on the 114.3 mm circle, standing 4 mm proud of the pad
    for k in range(5):
        t = SPOKE0 + 2 * math.pi * (k + 0.5) / 5
        cc = (0.0, 0.05715 * math.cos(t), 0.05715 * math.sin(t))
        b.add_mesh(lathe([(0.0, PAD_H + 0.004), (0.0085, PAD_H + 0.004), (0.0085, PAD_H - 0.006), (0.0, PAD_H - 0.006)], 6, 'x',
                         center=cc), 'darkSteel')
    for k in range(SPOKES):
        b.add_mesh(spoke(SPOKE0 + 2 * math.pi * k / SPOKES, hw, rim), 'rim')
    # valve stem through the barrel between two spokes, with its blue cap
    ang = VALVE_ANGLE
    vr = rim - 0.010
    vc = (hw * 0.80, vr * math.cos(ang), vr * math.sin(ang))
    radial = Vector((0.0, -math.cos(ang), math.sin(ang)))
    root = V(*vc) - radial * 0.004
    tip = root + (Vector((1.0, 0.0, 0.0)) * 0.70 + radial * -0.72).normalized() * 0.020
    b.add_mesh(kit.bar(root, tip, kit.circle2(0.0028, 12)), 'steel')
    b.add_mesh(kit.bar(tip, tip + (tip - root).normalized() * 0.010, kit.circle2(0.0040, 12)), 'decalBlue')
    # disc, hat and caliper inside the 15 in barrel (inner radius rim - 0.024), and a black dust shield
    # behind the disc that closes the ring between disc and barrel, so the spoke gaps read dark
    rotor = [(0.034, -0.012), (0.128, -0.012), (0.131, -0.016), (0.131, -0.032), (0.128, -0.036), (0.034, -0.036)]
    b.add_mesh(lathe(rotor, 64, 'x', closed=True), 'rotor')
    b.add_mesh(lathe([(0.0, 0.004), (0.06, 0.004), (0.06, -0.012), (0.0, -0.012)], 32, 'x'), 'darkSteel')
    b.add_mesh(lathe([(0.0, -0.040), (rim - 0.030, -0.040), (rim - 0.030, -0.044), (0.0, -0.044)], 64, 'x'), 'trim')
    cal = [(0.094, 0.004), (0.150, 0.004), (0.156, -0.02), (0.150, -0.050), (0.094, -0.050)]
    v, f = lathe(cal, 12, 'x', arc=math.radians(52), phase=math.radians(118), closed=True)
    m = len(cal)                                                # (a partial arc is open at its ends: cap them)
    b.add(v, f + [list(range(m)), [len(v) - 1 - j for j in range(m)]], 'caliper')
    o = b.build(name, coll)
    # built about the hub, outboard +x; the right side is mirrored (baked, so the normals stay outward)
    if s < 0:
        o.data.transform(Matrix.Scale(-1, 4, Vector((1, 0, 0))))
        o.data.flip_normals()
    # the decals go on after the mirror, so the right side's read the right way round too
    kit.append_builder(o, decals(s, hw, rim))
    o.matrix_world = Matrix.Translation(V(s * wx, a, D.TYRE_R))
    kit.finish(o, 0.0015, 1, 35.0)
    return o


def build(coll, parts_):
    for tag, a, wx in (('F', D.FA, D.WX_F), ('R', D.RA, D.WX_R)):
        for S, s in (('L', 1), ('R', -1)):
            n = 'wheel.%s%s' % (tag, S)
            parts_[n] = corner(a, s, wx, n, coll)
