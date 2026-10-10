"""EK9 cabin (photos 76-88 of #111040): right-hand drive, the red Recaro buckets with their harness
slot and stitched logo, the grey rear seat, red carpet over the tunnel, the black dash with the
driver's gauge hood, the centre stack with its silver head unit and climate knobs, the console
and gear lever, the MOMO three-spoke wheel with its red H, door cards with red inserts, the roof
lining, the mirror and the belts.

Seats, dash, console and door cards are lofts of 2D sections (kit / shape), capped closed solids.
Everything stays 1.5 cm or more inside the body: the roof lining follows the roof's own crown
(dims.zt, dims.crown) below its skin, the door cards lean in with the flank's tumble under the
glass ledge, the dash stays under the windshield. The steering wheel is its own object with its
origin at the hub, so the game can turn it."""
import math
from mathutils import Vector, Matrix
from . import kit, decal, body as B, dims as D, dash as DASH
from .kit import V
from .shape import loft_rings, squircle, smooth01, lathe

DRIVER_X = -0.35            # right-hand drive: the driver sits on the car's right (x < 0)
SEAT_XS = (0.35, -0.35)
FLOOR_Z = 0.16              # carpet top


def _xs(x0, x1, r, n=10):
    """x samples from x0 to x1: evenly through the middle, packed into the r-wide rounded ends."""
    ends = [0.0, 0.05, 0.18, 0.4, 0.7, 1.0]
    mid = [x0 + r + (x1 - x0 - 2 * r) * k / n for k in range(1, n)]
    return [x0 + r * e for e in ends] + mid + [x1 - r * e for e in reversed(ends)]


def _end_k(x, x0, x1, r, floor=0.15):
    e = max(0.0, (x0 + r - x) / r, (x - (x1 - r)) / r)
    return max(floor, math.sqrt(max(0.0, 1.0 - e * e)))


def _placed(pts, ang, of, oz):
    """(u, v) points rotated by ang (radians, about the origin) and moved to (of, oz)."""
    c, s = math.cos(ang), math.sin(ang)
    return [(of + u * c - v * s, oz + u * s + v * c) for u, v in pts]


def _xloft(b, xs, sec, slot):
    """Loft of the closed (f, z) sections sec(x) across the x samples, capped, into Builder b."""
    b.add_mesh(loft_rings([[(x, f, z) for f, z in sec(x)] for x in xs], True, True), slot)


def _finish(o, name, parts_, bevel=0.0):
    kit.finish(o, bevel, 1, 30.0)
    parts_[name] = o
    return o


# ------------------------------------------------------------------ front seats

SEAT_BACK_ANG = math.radians(14)
SEAT_BACK_O = (-0.36, 0.22)                 # the back section's origin (f, z)
SLOT = (0.815, 0.160, 0.034)                # harness slot: height up the back, width, height
INSERT_HW, INSERT_TOP = 0.105, 0.66          # woven centre panels: half width, top up the back


def _bolster_up(t):
    """How far the back's side wings reach forward at height fraction t: most at the ribs, less at
    the hips (where the cushion's bolsters take over) and at the head."""
    return 0.55 + 0.45 * smooth01(t / 0.22) - 0.40 * smooth01((t - 0.58) / 0.32)


def _back_sec(xc, x, hw=0.27, r=0.075):
    """Back section at x (photos 77, 81): the head slopes diagonally down into the shoulders, the
    side bolsters rise over 8.5 cm to a rolled outer edge (the end rounding), and the centre panel
    between them is dished 1.2 cm below the head."""
    k = _end_k(x, xc - hw, xc + hw, r)
    d = abs(x - xc)
    top = 0.74 + 0.15 * (1.0 - smooth01((d - 0.11) / 0.12))         # head, then down into the shoulders
    wing = 0.11 * smooth01((d - 0.095) / 0.085)                      # side bolsters reach forward
    dish = 0.012 * (1.0 - smooth01(d / 0.10))
    ht = 0.055 + 0.5 * wing
    c = 0.5 * wing
    pts = []
    for u, v in squircle(ht * k, 0.5 * top * k, 3.0, 48, c, 0.5 * top):
        t = v / top
        # the front half pulls back where the bolster is shallower, and in the dished centre panel
        w = smooth01((u - (c - ht * k)) / (2.0 * ht * k + 1e-9))
        pull = wing * (1.0 - _bolster_up(t)) + dish * (1.0 - smooth01((t - 0.62) / 0.10))
        pts.append((u - pull * w, v))
    return _placed(pts, SEAT_BACK_ANG, *SEAT_BACK_O)


def _cushion_sec(xc, x, hw=0.26, r=0.07):
    k = _end_k(x, xc - hw, xc + hw, r)
    d = abs(x - xc)
    bol = 0.08 * smooth01((d - 0.095) / 0.09)                        # thigh bolsters, rolled at the edge
    hz = 0.5 * (0.20 + bol)
    return _placed(squircle(0.21 * k, hz * k, 3.0, 44, 0.0, hz), math.radians(7), -0.19, 0.155)


HEAD_T = 0.89               # the back's height at its centre (the head)


def _head_front(v):
    """The head's front face (u) at height v up the back, on the centreline."""
    hh = 0.5 * HEAD_T
    return 0.055 * max(0.0, 1.0 - abs((v - hh) / hh) ** 3) ** (1.0 / 3.0)


def front_seat(coll, parts_, xc, S):
    """A Recaro bucket: one-piece high back with side wings and the headrest rising out of the
    shoulders, a bolstered cushion, the harness slot through the head, RECARO stitched under it.
    The back's rear shell is black."""
    b = kit.Builder()
    _xloft(b, _xs(xc - 0.26, xc + 0.26, 0.045, 14), lambda x: _cushion_sec(xc, x), 'seatRed')
    back = kit.Builder()
    _xloft(back, _xs(xc - 0.27, xc + 0.27, 0.045, 14), lambda x: _back_sec(xc, x), 'seatRed')
    o = back.build('seatBack.' + S, coll)
    # the back shell: faces looking rearward (Blender +y), along the back's lean
    fwd = Vector((0.0, -math.cos(SEAT_BACK_ANG), math.sin(SEAT_BACK_ANG)))
    me = o.data
    me.materials.append(kit.mats.get('seatBack'))
    for p in me.polygons:
        if p.normal.dot(fwd) < -0.35:
            p.material_index = 1
    # the woven centre panel (photos 77, 81): the dished front between the bolsters, up to under
    # the RECARO band; the suede bolsters and head keep seatRed
    me.materials.append(kit.mats.get('seatInsert'))
    up = Vector((0.0, math.sin(SEAT_BACK_ANG), math.cos(SEAT_BACK_ANG)))
    f0, z0 = SEAT_BACK_O
    O = V(xc, f0, z0)
    for p in me.polygons:
        pc = o.matrix_world @ p.center
        if p.material_index == 0 and p.normal.dot(fwd) > 0.3 and abs(pc.x - xc) < INSERT_HW and \
                (pc - O).dot(up) < INSERT_TOP:
            p.material_index = 2
    # harness slot through the head: a rounded slot cut along the back's forward axis
    c = V(xc, f0, z0) + up * SLOT[0]
    M = Matrix((Vector((1.0, 0.0, 0.0)), up, fwd)).transposed().to_4x4()
    M.translation = c
    slot = kit.fillet_poly(kit.rect(SLOT[1], SLOT[2]), SLOT[2] * 0.49, 6)
    cut = kit.cutter_obj(kit.prism(slot, -0.2, 0.2, M), 'seat.slot')
    kit.boolean(o, cut, 'DIFFERENCE', material_mode='TRANSFER')
    # RECARO under the slot, each point laid on the head's front face (it recedes toward the top)
    pts, faces, hgt = decal.text_mesh('RECARO', 0.085)
    v0 = SLOT[0] - SLOT[2] * 0.5 - 0.035
    base = c + up * (v0 - SLOT[0])
    lb = kit.Builder()
    decal.plate(lb, pts, faces, lambda u, vv: (base + Vector((u, 0.0, 0.0)) + up * vv + fwd * _head_front(v0 + vv), fwd),
                'seatLogo', thick=0.0006, lift=0.0005)
    kit.append_builder(o, lb)
    _finish(o, 'seatBack.' + S, parts_)
    # the cushion and the seat's base frame (black), down to the carpet
    b.add_mesh(kit.box((0.36, 0.40, 0.05), center=V(xc, -0.20, FLOOR_Z + 0.025)), 'seatBack')
    # the recline hinge's black cover on the door side of the back's foot (photos 77, 81)
    so = 1.0 if xc > 0 else -1.0
    b.add_mesh(lathe([(0.0, -0.012 * so), (0.045, -0.012 * so), (0.050, -0.006 * so), (0.050, 0.006 * so),
                      (0.044, 0.010 * so), (0.0, 0.010 * so)], 32, 'x', center=(xc + so * 0.262, -0.345, 0.28)), 'seatBack')
    o = b.build('seat.' + S, coll)
    # the cushion's woven centre panel: its top between the thigh bolsters, behind the front roll
    me = o.data
    me.materials.append(kit.mats.get('seatInsert'))
    k = len(me.materials) - 1
    red = [i for i, m in enumerate(me.materials) if m.name == 'ek.seatRed'][0]
    for p in me.polygons:
        c = o.matrix_world @ p.center
        if p.material_index == red and p.normal.z > 0.6 and abs(c.x - xc) < INSERT_HW and -c.y < -0.03:
            p.material_index = k
    _finish(o, 'seat.' + S, parts_)


# ------------------------------------------------------------------ rear seat

def rear_seat(coll, parts_):
    """Grey rear seat: two contoured places on one cushion and back (photos 79, 86), inboard of the
    rear wheel wells (their walls stand at |x| 0.405)."""
    x0, x1, r = -0.395, 0.395, 0.05

    def contour(x):
        # the outer bolsters and the soft ridge between the two places
        return 0.025 * smooth01((abs(x) - 0.28) / 0.08) + 0.012 * (1.0 - smooth01(abs(x) / 0.06))

    def cushion(x):
        k = _end_k(x, x0, x1, r)
        hz = 0.5 * (0.19 + contour(x))
        return _placed(squircle(0.19 * k, hz * k, 4.0, 36, 0.0, hz), math.radians(6), -0.93, FLOOR_Z)

    def back(x):
        k = _end_k(x, x0, x1, r)
        c = contour(x)
        return _placed(squircle((0.06 + c) * k, 0.33 * k, 4.0, 36, c, 0.33), math.radians(24), -1.10, 0.34)
    b = kit.Builder()
    _xloft(b, _xs(x0, x1, r, 16), cushion, 'fabricGrey')
    _xloft(b, _xs(x0, x1, r, 16), back, 'fabricGrey')
    _finish(b.build('rearSeat', coll), 'rearSeat', parts_)


# ------------------------------------------------------------------ steering wheel

WHEEL_C, WHEEL_TILT, WHEEL_R = (DRIVER_X, 0.38, 0.755), math.radians(25), 0.175
PAD_HW, PAD_HH, PAD_CY = 0.092, 0.072, 0.012      # airbag pad half width / height, centre (local +y is down)
PAD_PROFILE = [(1.0, -0.026), (1.0, 0.010), (0.975, 0.030), (0.92, 0.042), (0.80, 0.050), (0.55, 0.054), (0.25, 0.055)]


def steering_wheel(coll, parts_):
    """MOMO three-spoke (photos 84, 85): leather rim, black spokes at 3, 9 and 6 o'clock, the pad
    with its red H, and the column back into the dash. Built about the hub (local z toward the
    driver), which is the object origin."""
    b = kit.Builder()
    # rim: a slightly oval grip swept round the circle
    ring = [(WHEEL_R + 0.017 * math.cos(t), 0.0, 0.015 * math.sin(t)) for t in [2 * math.pi * k / 16 for k in range(16)]]
    rings = []
    for k in range(72):
        a = 2 * math.pi * k / 72
        rings.append([Vector((r * math.cos(a), r * math.sin(a), z)) for r, _, z in ring])
    v, f = kit.loft(rings + rings[:1], cap_start=False, cap_end=False)
    b.add(v, f, 'leather')
    # spokes: flat, drafted bars from the pad to the rim, dished 2 cm toward the dash
    # (local +y points down the wheel: n x car-x)
    for a in (0.0, math.pi, math.pi / 2):
        u = Vector((math.cos(a), math.sin(a), 0.0))
        w = Vector((0.0, 0.0, 1.0)).cross(u)
        secs = []
        for t, wid in ((0.05, 0.050), (0.11, 0.042), (WHEEL_R - 0.004, 0.034)):
            c = u * t + Vector((0.0, 0.0, 0.012 * (1.0 - (t - 0.05) / (WHEEL_R - 0.05))))
            secs.append([c + w * (s * wid / 2) + Vector((0.0, 0.0, h)) for s, h in ((-1, -0.006), (1, -0.006), (0.8, 0.006), (-0.8, 0.006))])
        b.add_mesh(kit.loft(secs), 'dash')
    # the airbag pad (photo 84): a domed, rounded-trapezoid cushion wider than the hub, centred a
    # little below it (the SRS lettering sits on its lower half), and the column shroud into the dash
    pad = []
    for sc, z in PAD_PROFILE:
        pad.append([Vector((u * sc * (1.0 - 0.10 * v / PAD_HH), PAD_CY + v * sc, z))
                    for u, v in squircle(PAD_HW, PAD_HH, 3.0, 48)])
    b.add(*kit.loft(pad), 'leather')
    b.add_mesh(kit.bar(Vector((0.0, 0.0, -0.02)), Vector((0.0, 0.0, -0.21)), kit.circle2(0.035, 20), kit.circle2(0.048, 20)), 'dash')
    o = b.build('steeringWheel', coll)
    kit.clean(o)                      # welds the rim's closing ring
    n = Vector((0.0, math.cos(WHEEL_TILT), math.sin(WHEEL_TILT)))       # toward the driver (Blender: -f is +y)
    xa = Vector((1.0, 0.0, 0.0))
    ya = n.cross(xa)
    R = Matrix((xa, ya, n)).transposed().to_4x4()
    R.translation = V(*WHEEL_C)
    o.matrix_world = R
    _finish(o, 'steeringWheel', parts_)
    # the red H on the pad, riding with the wheel
    from .parts import badge
    at = R @ Vector((0.0, 0.0, PAD_PROFILE[-1][1] - 0.0008))
    bo = badge(coll, 'steeringBadge', (at.x, -at.y, at.z), front=False, w=0.034, h=0.026, normal=(0.0, -n.y, n.z))
    bo.parent = o
    bo.matrix_parent_inverse = o.matrix_world.inverted()
    parts_['steeringBadge'] = bo


# ------------------------------------------------------------------ floor, console, shifter

def _smax0(a, b, k):
    """max(a, b) rounded over a k-wide crossing, left exact where either is 0 (dims.smax lifts two
    zeros by k / 2, which would raise the flat floor)."""
    h = max(0.0, k - abs(a - b)) / k
    return max(a, b) + 0.25 * k * h * h * smooth01(min(a, b) / k)


def carpet(coll, parts_):
    """Red carpet from behind the rear seat over the transmission tunnel, up the toe board and on up
    the firewall, its end hidden in the dash's underside (the body has no firewall of its own, so
    the toe board closes the footwells). Tunnel and toe board join through a smooth max: a hard
    max creased the carpet where they met."""
    xs = [-0.70 + 1.40 * k / 56 for k in range(57)]

    def tunnel(x, f):
        wf = smooth01((f + 0.55) / 0.15) * (1.0 - smooth01((f - 0.62) / 0.08))
        return 0.13 * wf * (1.0 - smooth01((abs(x) - 0.10) / 0.07))

    def toe(f):
        return 0.26 * smooth01((f - 0.56) / 0.16) + 0.20 * smooth01((f - 0.72) / 0.08)
    rings = []
    for f in [-1.20 + 2.00 * k / 64 for k in range(65)]:
        # full width between the sills, inboard of the rear wheel wells (walls at |x| 0.405) behind f -1.0
        xe = 0.39 + 0.31 * smooth01((f + 1.02) / 0.06)
        top = [(x * xe / 0.70, f, FLOOR_Z + _smax0(tunnel(x * xe / 0.70, f), toe(f), 0.04)) for x in xs]
        rings.append(top + [(x, f, z - 0.012) for x, f, z in reversed(top)])
    b = kit.Builder()
    b.add_mesh(loft_rings(rings, True, True), 'carpetRed')
    _finish(b.build('carpet', coll), 'carpet', parts_)


def console(coll, parts_):
    """The console on the tunnel from the stack back between the seats, the gear lever in its
    stitched boot with the titanium knob (photo 88), and the handbrake."""
    b = kit.Builder()

    def sec(f):
        top = 0.37 + 0.05 * smooth01((f - 0.30) / 0.15)
        return [(x, f, z) for x, z in kit.fillet_poly([(-0.085, 0.25), (0.085, 0.25), (0.085, top), (-0.085, top)], 0.0, 4,
                                                        radii=[0.0, 0.0, 0.02, 0.02])]
    b.add_mesh(loft_rings([sec(f) for f in [-0.12 + 0.62 * k / 20 for k in range(21)]], True, True), 'dash')
    # shift boot (a stitched leather cone) and the lever leaning back to the knob
    base, knob = (0.0, 0.20, 0.375), (0.0, 0.16, 0.54)
    b.add_mesh(lathe([(0.0, 0.0), (0.050, 0.0), (0.045, 0.02), (0.030, 0.05), (0.016, 0.085), (0.0, 0.085)], 24, 'z',
                     center=base), 'leather')
    b.add_mesh(kit.bar(V(*base), V(*knob), kit.circle2(0.007, 10)), 'steel')
    b.add_mesh(lathe([(0.0, -0.028), (0.020, -0.024), (0.028, -0.008), (0.028, 0.008), (0.020, 0.024), (0.0, 0.029)], 24, 'z',
                     center=knob), 'steel')
    # handbrake lever between the seats
    b.add_mesh(kit.bar(V(0.0, -0.02, 0.40), V(0.0, -0.30, 0.47), kit.circle2(0.014, 12)), 'dash')
    _finish(b.build('console', coll), 'console', parts_)


# ------------------------------------------------------------------ door cards, lining, mirror, belts

def _card_out(z):
    """The door card's outer face (toward the door skin): it leans in with the flank's tumble."""
    return 0.785 - 0.035 * smooth01((z - 0.55) / 0.28)


def _card_in(z):
    """The card's cabin face at height z: 1.8 cm in from its outer face, and the armrest ledge."""
    return _card_out(z) - 0.018 - 0.035 * math.exp(-((z - 0.585) / 0.03) ** 2)


CARD_F = (-0.50, 0.60)
# the red fabric insert (side view, f z), above the armrest to under the window ledge, its front
# end raked like the door's (photos 78, 85)
_INSERT = kit.fillet_poly([(-0.30, 0.615), (0.40, 0.615), (0.47, 0.705), (0.43, 0.748), (-0.30, 0.748)], 0.028, 4)
INSERT_LAYERS = ((-0.002, 0.0), (0.004, 0.0), (0.006, 0.0018), (0.007, 0.005))   # (proud of the card, inset)
HANDLE = kit.fillet_poly(kit.rect(0.13, 0.036, 0.36, 0.790), 0.016, 4)          # the inner handle's recess
GRAB = (-0.10, 0.27, 0.660)                                                     # pull bar f0, f1, z
SPEAKER = (0.36, 0.40, 0.068)                                                   # f, z, r


def door_cards(coll, parts_):
    """Black cards on the doors' inner faces (photos 76, 78, 85): the armrest ledge, the red fabric
    insert as a padded panel following the card, the black pull bar across it, the inner handle in
    its recess at the front top and the speaker at the front bottom. The card leans in with the
    flank's tumble so its top stays under the glass ledge."""
    for S, s in (('L', 1), ('R', -1)):
        b = kit.Builder()
        zs = [0.30 + 0.53 * k / 24 for k in range(25)]
        sec = [(_card_out(z), z) for z in zs] + [(_card_in(z), z) for z in reversed(zs)]
        f0, f1 = CARD_F
        rings = []
        for k in range(23):
            f = f0 + (f1 - f0) * k / 22
            e = min(1.0, (f - f0) / 0.04, (f1 - f) / 0.04)
            rings.append([(s * (x + (1.0 - e) * 0.012), f, z) for x, z in sec])
        b.add_mesh(loft_rings(rings, True, True), 'dash')
        o = b.build('doorCard.' + S, coll)
        # the inner handle's recess, 12 mm into the card, dark at the back
        xi = _card_in(0.790)
        x0, x1 = sorted((s * (xi - 0.02), s * (xi + 0.012)))
        v, fs = B.side_prism(HANDLE, x0, x1, shrink=0)
        floor = 1 if s > 0 else 0
        slots = ['dash'] * len(fs)
        slots[floor] = 'grilleDark'
        cb = kit.Builder()
        cb.add_slotted(v, fs, slots)
        kit.boolean(o, cb.build('card.cut'), 'DIFFERENCE', material_mode='TRANSFER')
        o.data.set_sharp_from_angle(angle=math.radians(30))

        lb = kit.Builder()
        # the insert: padded layers following the card's face, the base sunk 2 mm into it
        ins = kit.ccw(_INSERT)
        layers = []
        for t, inset in INSERT_LAYERS:
            ring = kit.offset_poly(ins, -inset) if inset else ins
            layers.append([(s * (_card_in(z) - t), f, z) for f, z in ring])
        lb.add_mesh(loft_rings(layers, True, True), 'seatRed')
        # the pull bar across the insert: a rounded bar standing 1.6 cm proud, ends rounded off
        g0, g1, gz = GRAB
        face = _card_in(gz) - INSERT_LAYERS[-1][0] + 0.001
        bars = []
        for k in range(17):
            f = g0 + (g1 - g0) * k / 16
            kk = _end_k(f, g0, g1, 0.02, 0.2)
            bars.append([(s * (face - 0.008 - u * kk), f, gz + v * kk) for u, v in squircle(0.008, 0.012, 3.0, 20)])
        lb.add_mesh(loft_rings(bars, True, True), 'dash')
        # the lever in the handle recess
        lb.add_mesh(kit.bar(V(s * (xi - 0.004), 0.305, 0.790), V(s * (xi - 0.010), 0.405, 0.790), kit.rect(0.008, 0.012)),
                    'satin')
        # speaker: black grille in a raised bezel on the lower card
        sf, sz, sr = SPEAKER
        xs = s * _card_in(sz)
        prof_grille = [(0.0, 0.001), (sr - 0.010, 0.001), (sr - 0.010, -0.004), (0.0, -0.004)]
        prof_bezel = [(sr - 0.012, 0.002), (sr, 0.002), (sr, -0.003), (sr - 0.004, -0.008), (sr - 0.010, -0.008)]
        lb.add_mesh(lathe([(r, s * h) for r, h in prof_grille], 48, 'x', center=(xs, sf, sz)), 'meshDark')
        lb.add_mesh(lathe([(r, s * h) for r, h in prof_bezel], 48, 'x', center=(xs, sf, sz), closed=True), 'dash')
        kit.append_builder(o, lb)
        _finish(o, 'doorCard.' + S, parts_)


def headliner(coll, parts_):
    """The roof lining: the roof's own crown, 3.5 cm under the outer shape, between the rails."""
    rings = []
    for k in range(41):
        f = D.WS_TOP + 0.005 + (D.ROOF_END + 0.02 - D.WS_TOP - 0.005) * k / 40
        xe = D.glass_edge_x(f) - 0.04
        zt, cr = D.zt(f), D.crown(f)
        top = [(x, f, zt - cr * (x / xe) ** 2 - 0.035) for x in [-xe + 2 * xe * j / 24 for j in range(25)]]
        rings.append(top + [(x, f, z - 0.008) for x, f, z in reversed(top)])
    b = kit.Builder()
    b.add_mesh(loft_rings(rings, True, True), 'headliner')
    _finish(b.build('headliner', coll), 'headliner', parts_)


def mirror(coll, parts_):
    """Rear-view mirror on its stalk from the windshield's top."""
    b = kit.Builder()
    c = (0.0, 0.20, 1.145)
    b.add_mesh(loft_rings([[(x, f, z) for x, z in squircle(0.105, 0.032, 4.0, 32, 0.0, c[2])] for f in (c[1] + 0.015, c[1] - 0.015)],
                          True, True), 'trim')
    b.add_mesh(loft_rings([[(x, c[1] - 0.0155, z) for x, z in squircle(0.098, 0.026, 4.0, 32, 0.0, c[2])],
                           [(x, c[1] - 0.0145, z) for x, z in squircle(0.098, 0.026, 4.0, 32, 0.0, c[2])]], True, True), 'mirror')
    top_f = 0.15
    glass_z = D.zt(top_f) - 0.004        # its pad inside the 5 mm pane
    b.add_mesh(kit.bar(V(0.0, c[1], c[2] + 0.02), V(0.0, top_f, glass_z), kit.circle2(0.008, 12)), 'trim')
    _finish(b.build('rearMirror', coll), 'rearMirror', parts_)


def belts(coll, parts_):
    """The front belts hanging down the B-pillars (grey webbing, photos 77, 79)."""
    b = kit.Builder()
    for s in (1, -1):
        # The pillar leans inward to x ~0.66 at shoulder height. Keep the
        # complete 48 mm webbing section inside it, including its upper anchor.
        top, bot = V(s * 0.60, -0.62, 1.10), V(s * 0.72, -0.58, 0.30)
        b.add_mesh(kit.bar(top, bot, kit.rect(0.048, 0.003), up=(0.0, -1.0, 0.0)), 'belt')
    _finish(b.build('belts', coll), 'belts', parts_)


def cabin(coll, parts_):
    for xc, S in zip(SEAT_XS, ('L', 'R')):
        front_seat(coll, parts_, xc, S)
    rear_seat(coll, parts_)
    DASH.dash(coll, parts_)
    DASH.pedals(coll, parts_)
    steering_wheel(coll, parts_)
    carpet(coll, parts_)
    console(coll, parts_)
    door_cards(coll, parts_)
    headliner(coll, parts_)
    mirror(coll, parts_)
    belts(coll, parts_)
