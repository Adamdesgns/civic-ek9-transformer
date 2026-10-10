"""EK9 dash (photos 80, 84, 85, 87 of #111040): one lofted dash body, with the driver's gauge
binnacle, the centre stack and the outboard vent bezels unioned onto it as their own solids, and
every opening (dial recess, vents, head unit, glovebox shut line and handle, defrost slot) cut
into it as a pocket that carries its own wall and floor slots. The pedals hang from under it.

The binnacle is a separate solid (a front-view arch intersected with its side-view visor profile)
rather than a blend of dash sections: blending two sections whose points mean different things
folded the dash into spikes at the hood's ends."""
import math
from . import kit, body as B
from .kit import V
from .shape import smooth01, lathe

# ------------------------------------------------------------------ dash body

DASH_X = 0.72               # the dash's half width (door cards' inner faces at about 0.75)
END_R = 0.03                # the ends round over by this much
# centreline section (f, z), from the rear bottom corner up the occupants' face, over the top to the
# windshield base, down the firewall side and back along the underside. The lower face (glovebox /
# knee panel) slants forward from the break at z 0.738 to the underside.
_DASH = [(0.572, 0.600), (0.512, 0.738), (0.503, 0.800), (0.506, 0.872), (0.560, 0.905), (0.700, 0.889),
         (0.835, 0.832), (0.848, 0.700), (0.800, 0.600)]
_DASH_R = [0.008, 0.012, 0.0, 0.035, 0.09, 0.12, 0.012, 0.02, 0.0]
LOWER = (1, 0)              # the lower face runs from _DASH[1] down to _DASH[0]


def _taper(x):
    """Per-x section control points: toward the pillars the windshield falls, so the top drops and
    the front pulls back (smoothly, so neighbouring points move together)."""
    q = (x / 0.70) ** 2
    return [(f - 0.05 * q * smooth01((f - 0.62) / 0.15), z - 0.03 * q * smooth01((z - 0.70) / 0.10)) for f, z in _DASH]


def _dash_ring(x):
    sec = kit.ccw(kit.fillet_poly(_taper(x), 0.0, 5, radii=_DASH_R))
    e = min(1.0, max(0.0, (abs(x) - (DASH_X - END_R)) / END_R))
    d = END_R * (1.0 - math.sqrt(1.0 - e * e))
    return kit.offset_poly(sec, -d) if d > 1e-6 else sec


def face_f(x, z):
    """The lower face's f at height z (for cuts that must follow it: the glovebox groove)."""
    p = _taper(x)
    (f1, z1), (f0, z0) = p[LOWER[0]], p[LOWER[1]]
    return f0 + (f1 - f0) * (z - z0) / (z1 - z0)


def _xs(x0, x1, r, n):
    ends = [0.0, 0.05, 0.18, 0.4, 0.7, 1.0]
    mid = [x0 + r + (x1 - x0 - 2 * r) * k / n for k in range(1, n)]
    return [x0 + r * e for e in ends] + mid + [x1 - r * e for e in reversed(ends)]


# ------------------------------------------------------------------ binnacle

POD_C = -0.355              # the driver's side (right-hand drive: x < 0)
POD_W = 0.386
# front view (x, z): an arch round the dials, square-ish at the bottom


def _arch(cx, w, z0, z_side, z1, p=2.5, n=36):
    """Front-view dome: straight sides from z0 to z_side, then a superellipse up to z1 (a soft cowl
    rather than a rounded box), with small rounds at the bottom corners."""
    hw = w / 2
    top = [(cx + hw * u, z_side + (z1 - z_side) * (1.0 - abs(u) ** p) ** (1.0 / p))
           for u in [1.0 - 2.0 * k / n for k in range(n + 1)]]
    pts = [(cx - hw, z0), (cx + hw, z0)] + top
    return kit.fillet_poly(pts, 0.0, 4, radii=[0.02, 0.02] + [0.0] * len(top))


# The dials sit about 10 cm above the wheel's centre (photo 84), which also keeps the binnacle's
# bottom lip clear of the steering column's shroud under it.
_POD_FRONT = _arch(POD_C, POD_W, 0.750, 0.800, 0.975)
# side view (f, z): the visor's lip leans back 3 cm over the dials, the top falls toward the
# windshield (1.8 cm or more under the glass) and dives into the dash top. Its bottom is below the
# front outline's, so the two prisms never share a face.
_POD_SIDE = kit.fillet_poly([(0.505, 0.600), (0.745, 0.600), (0.745, 0.868), (0.720, 0.885), (0.660, 0.925),
                             (0.610, 0.955), (0.555, 0.975), (0.490, 0.972), (0.472, 0.955)], 0.0, 5,
                            radii=[0.0, 0.0, 0.01, 0.02, 0.04, 0.04, 0.03, 0.012, 0.008])
RECESS = kit.offset_poly(kit.ccw(_POD_FRONT), -0.030)       # a 3 cm wall all round, the visor on top
GAUGE_BACK = 0.600          # the recess's back wall: the dials' patterned surround
# tach, speedo, fuel, temp (x, z, r): tach inboard, the two small dials outboard (photo 84)
GAUGES = ((-0.255, 0.855, 0.045), (-0.352, 0.855, 0.048), (-0.432, 0.868, 0.022), (-0.476, 0.842, 0.022))

# ------------------------------------------------------------------ centre stack

STACK_F = 0.476             # the stack's face, 2.7 cm proud of the dash's
_STACK = kit.fillet_poly([(-0.115, 0.585), (0.115, 0.585), (0.140, 0.865), (-0.140, 0.865)], 0.0, 4,
                         radii=[0.02, 0.02, 0.03, 0.03])
_STACK_LOW = kit.fillet_poly([(-0.100, 0.26), (0.100, 0.26), (0.115, 0.600), (-0.115, 0.600)], 0.0, 4,
                             radii=[0.0, 0.0, 0.015, 0.015])
LOW_F = 0.490               # the lower stack's face, round the console's cubby
STACK_VENTS = ((0.0745, 0.812), (-0.0325, 0.812))
STACK_VENT_WH = (0.095, 0.052)
HEAD_UNIT = (0.021, 0.7185, 0.202, 0.107)          # x, z, w, h of its pocket
KNOB_X, KNOB_ZS = -0.108, (0.800, 0.752, 0.704)    # climate knobs on the driver's side of the stack

# ------------------------------------------------------------------ outboard vents, glovebox

SIDE_VENTS = (0.605, -0.628)                       # passenger, driver (outboard of the binnacle)
SIDE_VENT_Z = 0.785
GLOVEBOX = kit.fillet_poly(kit.rect(0.39, 0.100, 0.405, 0.678), 0.015, 4)
GLOVE_HANDLE = kit.fillet_poly(kit.rect(0.13, 0.026, 0.405, 0.708), 0.012, 4)


def _cutter(v, faces, slots, name='dash.cut'):
    b = kit.Builder()
    b.add_slotted(v, faces, slots)
    return b.build(name, smooth=True)


def _prism_front(poly, f0, f1, cap0='dash', cap1='dash', wall='dash'):
    """A front-view prism as a cutter: cap0 at f0, cap1 at f1."""
    v, fs = B.front_prism(poly, f0, f1, shrink=0)
    return _cutter(v, fs, [cap0, cap1] + [wall] * (len(fs) - 2))


def _union(o, cutter):
    kit.boolean(o, cutter, 'UNION', material_mode='TRANSFER')


def _pocket(o, cutter):
    kit.boolean(o, cutter, 'DIFFERENCE', material_mode='TRANSFER')


def _ring_tube(rings):
    """Closed tube through the cross-section rings (each 4 points, design space), path closed."""
    n, m = len(rings), len(rings[0])
    verts = [V(*p) for r in rings for p in r]
    faces = [[i * m + j, i * m + (j + 1) % m, ((i + 1) % n) * m + (j + 1) % m, ((i + 1) % n) * m + j]
             for i in range(n) for j in range(m)]
    return verts, faces


def _groove(poly_xz, width, depth):
    """A shut-line cutter round poly on the lower face: `width` wide, `depth` into the face at every
    point (it follows the slanted face), reaching 2 cm out of it."""
    p = kit.ccw(poly_xz)
    outer, inner = kit.offset_poly(p, width / 2), kit.offset_poly(p, -width / 2)
    rings = []
    for (xo, zo), (xi, zi) in zip(outer, inner):
        fo, fi = face_f(xo, zo), face_f(xi, zi)
        rings.append([(xo, fo - 0.02, zo), (xo, fo + depth, zo), (xi, fi + depth, zi), (xi, fi - 0.02, zi)])
    v, fs = _ring_tube(rings)
    return _cutter(v, fs, ['dash'] * len(fs))


def _slats(b, x0, x1, f0, f1, zs, t=0.003):
    """Horizontal louvre blades across an opening (ends 1 mm into its walls)."""
    for z in zs:
        b.add_mesh(kit.box((x1 - x0 + 0.002, f1 - f0, t), center=V(0.5 * (x0 + x1), 0.5 * (f0 + f1), z)), 'dash')


def dash(coll, parts_):
    b = kit.Builder()
    xs = _xs(-DASH_X, DASH_X, END_R, 28)
    rings = [_dash_ring(x) for x in xs]
    assert len({len(r) for r in rings}) == 1, 'dash sections changed point count'
    from .shape import loft_rings
    b.add_mesh(loft_rings([[(x, f, z) for f, z in r] for x, r in zip(xs, rings)], True, True), 'dash')
    o = b.build('dash', coll)

    # solids unioned on: the binnacle, the stack (upper and lower), the outboard vent bezels
    pod = B.bool_mesh(B.front_prism(_POD_FRONT, 0.45, 0.76, shrink=0),
                      B.side_prism(_POD_SIDE, POD_C - 0.25, POD_C + 0.25, shrink=0), 'INTERSECT')
    _union(o, _cutter(*pod, ['dash'] * len(pod[1])))
    _union(o, _prism_front(_STACK, STACK_F, 0.60))
    _union(o, _prism_front(_STACK_LOW, LOW_F, 0.62))
    for x in SIDE_VENTS:
        _union(o, _prism_front(kit.fillet_poly(kit.rect(0.13, 0.085, x, SIDE_VENT_Z), 0.015, 4), 0.492, 0.53))

    # pockets: the dial recess (its back is the patterned surround), vents, head unit, cubby
    _pocket(o, _prism_front(RECESS, 0.40, GAUGE_BACK, cap1='meshDark'))
    for x, z in STACK_VENTS:
        _pocket(o, _prism_front(kit.fillet_poly(kit.rect(*STACK_VENT_WH, x, z), 0.008, 3), 0.44, STACK_F + 0.03,
                                cap1='grilleDark'))
    hx, hz, hw, hh = HEAD_UNIT
    _pocket(o, _prism_front(kit.fillet_poly(kit.rect(hw, hh, hx, hz), 0.006, 3), 0.44, STACK_F + 0.012))
    _pocket(o, _prism_front(kit.fillet_poly(kit.rect(0.15, 0.105, 0.0, 0.505), 0.02, 4), 0.44, LOW_F + 0.09))
    for x in SIDE_VENTS:
        _pocket(o, _prism_front(kit.fillet_poly(kit.rect(0.11, 0.065, x, SIDE_VENT_Z), 0.01, 3), 0.44, 0.53,
                                cap1='grilleDark'))
    # defrost slot on the top, under the windshield: a plan-view pocket
    v, fs = B.top_prism(kit.fillet_poly(kit.rect(0.34, 0.05, 0.02, 0.730), 0.012, 3), 0.850, 1.0, shrink=0)
    _pocket(o, _cutter(v, fs, ['grilleDark', 'dash'] + ['dash'] * (len(fs) - 2)))
    # glovebox: its shut line round the door on the slanted lower face, and the handle's pocket
    _pocket(o, _groove(GLOVEBOX, 0.003, 0.004))
    _pocket(o, _prism_front(GLOVE_HANDLE, 0.44, face_f(0.405, 0.695) + 0.012))
    o.data.set_sharp_from_angle(angle=math.radians(30))

    # parts laid into the openings after the booleans (their ends sink into the walls)
    lb = kit.Builder()
    for x, z in STACK_VENTS:
        w, h = STACK_VENT_WH
        _slats(lb, x - w / 2, x + w / 2, STACK_F + 0.006, STACK_F + 0.012, [z - h / 4, z, z + h / 4])
    for x in SIDE_VENTS:
        _slats(lb, x - 0.055, x + 0.055, 0.498, 0.504, [SIDE_VENT_Z - 0.018, SIDE_VENT_Z, SIDE_VENT_Z + 0.018])
    for k in range(6):
        f = 0.712 + 0.0072 * k
        top = 0.889 - (f - 0.70) * 0.42 - 0.006
        lb.add_mesh(kit.box((0.34, 0.002, top - 0.849), center=V(0.02, f, 0.5 * (top + 0.849))), 'dash')
    _gauges(lb)
    _stack_parts(lb)
    kit.append_builder(o, lb)
    kit.clean(o)
    kit.finish(o, 0.0025, 2, 30.0)
    parts_['dash'] = o
    return o


# (start angle, sweep, major ticks, minor per major, red from) per dial; needle angle
_DIALS = ((225.0, 270.0, 10, 2, 0.8, 200.0), (225.0, 270.0, 9, 2, None, 205.0),
          (150.0, 120.0, 2, 1, None, 70.0), (150.0, 120.0, 2, 1, None, 110.0))


def _tick(x, z, r0, r1, a, w, f0, f1):
    c, s = math.cos(a), math.sin(a)
    px, pz = -s * w / 2, c * w / 2
    p0, p1 = (x + r0 * c, z + r0 * s), (x + r1 * c, z + r1 * s)
    return B.front_prism([(p0[0] - px, p0[1] - pz), (p0[0] + px, p0[1] + pz), (p1[0] + px, p1[1] + pz),
                          (p1[0] - px, p1[1] - pz)], f0, f1, shrink=0)


def _gauges(b):
    """Black dials sunk 1 mm into the patterned surround (photo 84), white ticks with a red zone on
    the tach, bright rims, yellow-orange needles."""
    face = GAUGE_BACK - 0.004
    for (x, z, r), (a0, sweep, major, minor, red, needle) in zip(GAUGES, _DIALS):
        b.add_mesh(lathe([(0.0, 0.001), (r, 0.001), (r, -0.004), (0.0, -0.004)], 48, 'f', center=(x, GAUGE_BACK, z)),
                   'gaugeFace')
        b.add_mesh(lathe([(r - 0.001, -0.006), (r + 0.004, -0.006), (r + 0.004, 0.001), (r - 0.001, 0.001)], 48, 'f',
                         center=(x, GAUGE_BACK, z), closed=True), 'steel')
        n = major * minor
        for k in range(n + 1):
            t = k / n
            big = k % minor == 0
            a = math.radians(a0 - sweep * t)
            slot = 'badgeRed' if red is not None and t >= red else 'gaugeTick'
            b.add_mesh(_tick(x, z, r * (0.74 if big else 0.82), r * 0.92, a, 0.0028 if big else 0.0014,
                             face - 0.0006, face + 0.0002), slot)
        a = math.radians(needle)
        tip = (x + 0.85 * r * math.cos(a), z + 0.85 * r * math.sin(a))
        nf = face - 0.0012
        b.add_mesh(kit.bar(V(x, nf, z), V(tip[0], nf, tip[1]), kit.circle2(0.0011, 6)), 'needle')
        b.add_mesh(lathe([(0.0, 0.0), (0.006, 0.0), (0.006, -0.003), (0.0, -0.003)], 16, 'f', center=(x, face + 0.0002, z)),
                   'gaugeFace')


def _stack_parts(b):
    """The head unit in its pocket, the climate knobs, the switch row and the Type R plate."""
    hx, hz, hw, hh = HEAD_UNIT
    b.add_mesh(B.front_prism(kit.fillet_poly(kit.rect(hw - 0.006, hh - 0.006, hx, hz), 0.004, 3),
                             STACK_F - 0.0025, STACK_F + 0.0125, shrink=0), 'steel')
    b.add_mesh(B.front_prism(kit.fillet_poly(kit.rect(0.110, 0.050, hx - 0.01, hz + 0.01), 0.003, 3),
                             STACK_F - 0.0035, STACK_F - 0.0020, shrink=0), 'screen')
    for z in KNOB_ZS:
        b.add_mesh(lathe([(0.0, 0.003), (0.015, 0.003), (0.017, -0.001), (0.017, -0.020), (0.013, -0.024), (0.0, -0.024)],
                         32, 'f', center=(KNOB_X, STACK_F, z)), 'dash')
        b.add_mesh(lathe([(0.0, -0.0237), (0.011, -0.0237), (0.011, -0.0245), (0.0, -0.0245)], 32, 'f',
                         center=(KNOB_X, STACK_F, z)), 'steel')
    for x in (-0.045, 0.0, 0.045):
        b.add_mesh(B.front_prism(kit.fillet_poly(kit.rect(0.034, 0.018, x, 0.630), 0.004, 2), STACK_F - 0.003,
                                 STACK_F + 0.002, shrink=0), 'dash')
    b.add_mesh(B.front_prism(kit.fillet_poly(kit.rect(0.036, 0.011, 0.090, 0.630), 0.002, 2), STACK_F - 0.0012,
                             STACK_F + 0.0008, shrink=0), 'badgeRed')


# ------------------------------------------------------------------ pedals

# (x, pad centre f, pad centre z, pad width, pad height): clutch, brake, accelerator from the
# driver's left (right-hand drive, driver at x -0.35)
PEDALS = ((-0.225, 0.560, 0.330, 0.070, 0.060), (-0.320, 0.560, 0.330, 0.085, 0.060),
          (-0.445, 0.605, 0.260, 0.050, 0.110))
PEDAL_TILT = math.radians(35)       # the pads' faces lean back toward the driver
PIVOT = (0.66, 0.612)               # the arms' pivots, inside the dash's underside


def _slab(C, X, U, N, poly, t0, t1):
    """poly (a, b) laid in the plane through C spanned by X and U, extruded t0..t1 along N (design)."""
    p = kit.ccw(poly)
    n = len(p)
    verts = [V(*(C[i] + a * X[i] + bb * U[i] + t * N[i] for i in range(3))) for t in (t0, t1) for a, bb in p]
    faces = [list(reversed(range(n))), list(range(n, 2 * n))] + [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    return verts, faces


def pedals(coll, parts_):
    b = kit.Builder()
    c, s = math.cos(PEDAL_TILT), math.sin(PEDAL_TILT)
    X, U, N = (1.0, 0.0, 0.0), (0.0, s, c), (0.0, -c, s)       # N toward the driver's foot
    for x, f, z, w, h in PEDALS:
        C = (x, f, z)
        b.add_mesh(_slab(C, X, U, N, kit.fillet_poly(kit.rect(w, h), 0.008, 3), -0.006, 0.006), 'rubber')
        for k in range(-2, 3):          # raised ribs across the pad
            b.add_mesh(_slab(C, X, U, N, kit.fillet_poly(kit.rect(w - 0.014, 0.004, 0.0, k * h / 6), 0.0015, 2),
                             0.005, 0.008), 'rubber')
        # the arm: from the pad's back (sunk 2 mm into it) up and forward to the pivot under the dash
        back = (x, f + 0.004 * c, z - 0.004 * s)
        b.add_mesh(kit.bar(V(*back), V(x, *PIVOT), kit.rect(0.012, 0.016), kit.rect(0.012, 0.024), up=(1, 0, 0)), 'satin')
    o = b.build('pedals', coll)
    kit.finish(o, 0.0, 1, 30.0)
    parts_['pedals'] = o
    return o
