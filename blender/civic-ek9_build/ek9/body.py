"""EK9 body: the outer shape, skins, and region prisms for panel cutting.

The outer shape is the intersection of three closed solids:

* the envelope: a loft of closed sections at stations f (hood, fenders, roof,
  glass, flanks), carried on past both ends of the car at its own shape. Each
  section is a periodic cubic B-spline over a mirrored control polygon. Its
  key vertices (roof / hood edge, glass base, character line, belly, sill
  corner) come from dims.landmarks; each key expands into three control points
  (in, key, out) at its corner radius, so straight runs stay straight and
  corners keep a set radius. Every section has the same control count and
  samples per span, so the loft topology never changes and the paint reads clean.
* the front and rear fascias: stacks of horizontal waterlines. Each waterline
  is the plan outline (dims.PLAN_F / PLAN_R) inset by a height-dependent
  distance that blends from the flank (the envelope section at the seam
  station, plus a small margin so the fascia never cuts the flank) to the face
  profile at the centre (dims.FACE_*). Surfaces that face forward or back are
  single valued in a waterline, so bumpers, lamps and the grille come out clean.

The hood's leading edge, the lamp tops and the hatch glass's lower edge are
where the fascias meet the envelope. Every solid can be inset by a skin
thickness (sections by offsetting their control polygon, waterlines by adding
to the inset), so a skin is shape(0) minus shape(t): an exact shell, clean at
concave and convex edges alike.

Panels are a skin intersected with region prisms (side view, top view or
front view), each shrunk by G so neighbours keep a uniform 2G shut line.
"""
import math
import numpy as np
from mathutils import Vector
from . import kit, dims as D
from .kit import V
from .shape import spline2

G = 0.0022                 # half reveal (4.4 mm shut lines)
SKIN = 0.010               # pressed steel + paint (visible at shut lines)
GLASS = 0.005

# samples per B-spline span, right half, from the top centre round to the bottom centre
# (spans 8 and 9 sit either side of the shoulder crease: two samples each resolve its 7 mm radius)
ALLOC_HALF = [6, 5, 2, 2, 6, 1, 1, 3, 2, 2, 4, 3, 3, 3, 2, 2, 3, 3]


def _lerp(a, b, t):
    return a + (b - a) * t


def _clamp01(t):
    return 0.0 if t < 0 else 1.0 if t > 1 else t


def _smooth01(t):
    t = _clamp01(t)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ envelope

def _corner(prev, k, nxt, r):
    """(in, key, out) control points rounding key k at radius r."""
    k = Vector(k)
    din = k - Vector(prev)
    dout = Vector(nxt) - k
    r = min(r, 0.45 * din.length, 0.45 * dout.length)
    a = k - din.normalized() * r if din.length > 1e-9 else k.copy()
    b = k + dout.normalized() * r if dout.length > 1e-9 else k.copy()
    return [tuple(a), tuple(k), tuple(b)]


# roof edge radius: ROOF_EDGE_R[0] along the roof (between the header and the hatch hinge), [1]
# elsewhere (A / D pillars, hood edge). Along the roof a 4.5 cm roll swallowed the band of roof side
# over the side glass, which the low three-quarter views of the EK show
ROOF_EDGE_R = (0.030, 0.045)
# sill corner: how far the bottom of the flank tucks in under the belly
SILL_TUCK = 0.032


def section_keys(f):
    """Right-half key vertices with corner radii, top centre -> bottom centre."""
    L = D.landmarks(f)
    gh = L['zr'] - L['zbelt']
    t = _clamp01(gh / 0.05)
    roof = _smooth01((f - D.ROOF_END) / 0.15) * _smooth01((D.WS_TOP - f) / 0.15)
    return [
        ((0.0, L['zt']), None),
        ((0.55 * L['xr'], L['zt'] - 0.30 * L['crown']), None),
        ((L['xr'], L['zr']), _lerp(ROOF_EDGE_R[1], ROOF_EDGE_R[0], roof)),   # roof edge / A-D pillar / hood edge
        ((L['xg'], L['zbelt']), _lerp(0.035, 0.012, t)),   # glass base / fender top roll
        ((L['xc'], L['zchar']), 0.007),                    # character line: a crisp shoulder crease
        ((L['W'], L['zw']), 0.16),                         # belly
        ((L['W'] - SILL_TUCK, L['zb']), 0.03),             # sill corner
        ((0.5 * L['W'], L['zb']), None),
        ((0.0, L['zb']), None),
    ]


def section_ctrl(f):
    keys = section_keys(f)
    half = []
    for i, (p, r) in enumerate(keys):
        if i == 0 or i == len(keys) - 1:
            continue
        if r is None:
            half.append(p)
        else:
            half += _corner(keys[i - 1][0], p, keys[i + 1][0], r)
    top, bot = keys[0][0], keys[-1][0]
    return [top] + half + [bot] + [(-x, z) for x, z in reversed(half)]


def bspline_closed(ctrl, alloc):
    """Uniform periodic cubic B-spline; span i (ctrl[i] -> ctrl[i+1]) gets alloc[i] samples."""
    n = len(ctrl)
    assert len(alloc) == n, (len(alloc), n)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = ctrl[(i - 1) % n], ctrl[i], ctrl[(i + 1) % n], ctrl[(i + 2) % n]
        k = alloc[i]
        for s in range(k):
            t = s / k
            t2, t3 = t * t, t * t * t
            b0 = (1 - t) ** 3 / 6
            b1 = (3 * t3 - 6 * t2 + 4) / 6
            b2 = (-3 * t3 + 3 * t2 + 3 * t + 1) / 6
            b3 = t3 / 6
            out.append(tuple(b0 * p0[c] + b1 * p1[c] + b2 * p2[c] + b3 * p3[c] for c in range(2)))
    return out


def ring_alloc(mult=1):
    right = [a * mult for a in ALLOC_HALF]
    return right + list(reversed(right))


def section(f, mult=1, inset=0.0):
    """Closed section ring at station f; inset > 0 offsets the control polygon inward
    (the B-spline keeps it smooth, so no swallowtails at tight convex corners)."""
    ctrl = section_ctrl(f)
    if inset:
        # the ring runs clockwise in (x, z): kit.offset_poly(+d) moves a CW polygon inward
        if kit.poly_area(ctrl) > 0:
            raise RuntimeError('section control polygon expected clockwise')
        ctrl = kit.offset_poly(ctrl, inset)
    return bspline_closed(ctrl, ring_alloc(mult))


# Where the fascias meet the envelope (hood leading edge, lamp tops and sides, hatch-glass lower
# edge, bumper undersides) the stations are kept this close, so the seam relaxation in
# shape_object has envelope vertices to bend on both sides of the edge.
END_STEP = 0.005
END_ZONES = ((-2.12, -1.62), (1.50, 2.12))

_STATIONS = {}


def stations(base=0.04, fine=0.004, f0=None, f1=None):
    """Adaptive stations f0 -> f1: denser where the landmarks move quickly, and at most
    END_STEP apart through END_ZONES."""
    f0 = D.TAIL_EXT if f0 is None else f0
    f1 = D.NOSE_EXT if f1 is None else f1
    key = (base, fine, f0, f1)
    if key in _STATIONS:
        return _STATIONS[key]
    keys = ('zt', 'zb', 'W', 'xr', 'zbelt', 'zchar')
    out = [f0]
    f = f0
    h = 1e-3
    while f < f1:
        a, b = D.landmarks(f), D.landmarks(min(f1, f + h))
        rate = sum(abs(b[k] - a[k]) / h for k in keys)
        step = min(base, max(fine, base / (1.0 + 3.0 * rate)))
        if any(lo - step < f < hi for lo, hi in END_ZONES):
            step = min(step, END_STEP)
        f = min(f1, f + step)
        out.append(f)
    if f1 - out[-2] < fine * 0.5:
        out.pop(-2)
    _STATIONS[key] = out
    return out


def _loft_closed(rings):
    n = len(rings[0])
    verts = [p for r in rings for p in r]
    faces = []
    for i in range(len(rings) - 1):
        for j in range(n):
            j2 = (j + 1) % n
            faces.append([i * n + j, i * n + j2, (i + 1) * n + j2, (i + 1) * n + j])
    faces.append(list(range(n)))
    last = (len(rings) - 1) * n
    faces.append([last + j for j in reversed(range(n))])
    return verts, faces


def envelope_mesh(mult=1, inset=0.0):
    fs = stations()
    return _loft_closed([[V(x, f, z) for (x, z) in section(f, mult, inset)] for f in fs])


def side_profile(f, z, inset=0.0):
    """Half width of the envelope section at station f and height z, or None above / below it."""
    ring = section(f, 2, inset)
    best = None
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        if a[0] < 0 or b[0] < 0:
            continue
        if (a[1] - z) * (b[1] - z) <= 0 and a[1] != b[1]:
            t = (z - a[1]) / (b[1] - a[1])
            x = a[0] + (b[0] - a[0]) * t
            best = x if best is None else max(best, x)
    return best


# ------------------------------------------------------------------ fascias

def _arclen(pts):
    s = [0.0]
    for a, b in zip(pts, pts[1:]):
        s.append(s[-1] + math.dist(a, b))
    return s


def _resample_open(pts, n):
    s = _arclen(pts)
    L = s[-1]
    if L < 1e-9:
        return [pts[0]] * n
    out, j = [], 0
    for k in range(n):
        t = L * k / (n - 1)
        while j < len(pts) - 2 and s[j + 1] < t:
            j += 1
        u = 0.0 if s[j + 1] - s[j] < 1e-12 else (t - s[j]) / (s[j + 1] - s[j])
        out.append(tuple(pts[j][c] + (pts[j + 1][c] - pts[j][c]) * u for c in range(2)))
    return out


def plan_curve(points, n=160, sign=1):
    """Right-half plan outline (x, f), seam -> centreline tip, splined and resampled
    evenly by arc length, with outward unit normals.

    The spline runs on through a mirrored phantom of the second-last point, so it crosses
    x = 0 square to the centreline; the tip normal comes from samples on both sides of it.
    (Splining the right half alone left each waterline a shallow V at x = 0, which showed
    as a fold down the middle of the hatch and bumpers.)"""
    ext = list(points) + [(-points[-2][0], points[-2][1])]
    dense = spline2(ext, 400 * (len(ext) - 1) // (len(points) - 1) + 1)
    half = []
    for a, b in zip(dense, dense[1:]):
        half.append(a)
        if b[0] <= 0.0:
            t = a[0] / (a[0] - b[0]) if a[0] > b[0] else 1.0
            half.append((0.0, a[1] + (b[1] - a[1]) * t))
            break
    pts = _resample_open(half, n)
    pts[-1] = (0.0, pts[-1][1])
    out = []
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[i + 1] if i < n - 1 else (-pts[n - 2][0], pts[n - 2][1])
        tx, tf = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, tf) or 1.0
        out.append((p, (sign * tf / L, -sign * tx / L)))
    return out


def plan_radius(curve, span=4):
    """Local radius of curvature along a plan curve (circumradius over +-span samples, smoothed)."""
    n = len(curve)
    r = []
    for i in range(n):
        a = curve[max(0, i - span)][0]
        b = curve[i][0]
        c = curve[min(n - 1, i + span)][0]
        ab, bc, ca = math.dist(a, b), math.dist(b, c), math.dist(c, a)
        area2 = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
        r.append(1e3 if area2 < 1e-12 else ab * bc * ca / (2 * area2))
    # smoothed twice (moving average) so the clamp below never prints ridges
    for _ in range(2):
        r = [sum(r[max(0, i - 8):i + 9]) / len(r[max(0, i - 8):i + 9]) for i in range(n)]
    return r


def fascia_levels(front=True, z0=0.05, z1=1.9):
    """Waterline heights: fine through the bumper steps and the lamp band (front), the bumper's
    shoulder and the lamp band (rear) and the rear glass edge (the lamp / hood and glass /
    hatch-panel seams follow these facets). The rear adds a medium band through the bumper's
    tuck-under, whose lower corners crumpled between 12 mm waterlines."""
    if front:
        dense, bands, medium = (0.13, 0.20, 0.31, 0.44, 0.50, 0.516, 0.617, 0.62), ((0.54, 0.72), (0.86, 1.02)), ()
    else:
        dense, bands, medium = (0.13, 0.36, 0.39, 0.44, 0.516), ((0.50, 0.72), (0.86, 1.02)), ((0.17, 0.34),)
    out = [z0]
    z = z0
    while z < z1:
        near = min(abs(z - d) for d in dense)
        if any(a <= z <= b for a, b in bands):
            near = 0.0
        top = 0.012 if z < 1.0 else 0.08
        if any(a <= z <= b for a, b in medium):
            top = 0.006
        st = 0.003 + (top - 0.003) * min(1.0, near / 0.02)
        z = min(z1, z + st)
        out.append(z)
    return out


_FASCIA_FIELD = {}


def _fascia_field(front, n_plan, margin):
    """Waterline heights, plan samples and the face inset d[z][i] before any clamp, plus the
    per-sample depth scale s[i] (independent of the skin inset, so cached per end).

    An inset curve swallowtails once d passes the local plan radius R. Clamping each waterline
    on its own (smin(d, 0.75 R)) switched on and off from ring to ring where d changes quickly
    with height, printing lumps into the lower corners. Instead each plan sample scales its whole
    height profile by one factor, s = min(1, 0.75 R / d_max), where d_max is the deepest inset on
    that sample among the waterlines the body actually shows (below the envelope's top line)."""
    key = (front, n_plan, margin)
    if key in _FASCIA_FIELD:
        return _FASCIA_FIELD[key]
    if front:
        plan, seam, sign = D.PLAN_F, D.SEAM_FASCIA_F, 1
        faces_ = (D.FACE_LAMP_F, D.FACE_NOSE_F)
    else:
        plan, seam, sign = D.PLAN_R, D.SEAM_FASCIA_R, -1
        faces_ = (D.FACE_R, D.FACE_R_CORNER)
    curve = plan_curve(plan, n_plan, sign)
    radius = plan_radius(curve)
    x_seam = curve[0][0][0]
    zs = fascia_levels(front)
    # flank inset from the envelope at the seam; clamped to the envelope's height range
    prof = {}
    last = None
    for z in zs:
        x = side_profile(seam, z)
        if x is not None:
            last = x
        prof[z] = last
    first = next(v for v in (prof[z] for z in zs) if v is not None)
    blend = []
    for (x, f), (nx, nf) in curve:
        w = _smooth01((abs(nf) - 0.30) / 0.6)         # flanks untouched until the plan turns ~17 deg
        # second profile: the nose between the lamps (front), the square lamp corners (rear)
        c = _smooth01((0.33 - x) / 0.06) if front else min(1.0, (x / D.REAR_CORNER_X) ** 4)
        blend.append((w, c))
    # rear: between the bumper's shoulder and the rake into the glass, the lamp / hatch-panel face is
    # nearly flat in plan across the plate (blueprint top view: level with the centre out to |x|
    # 0.32, 0.4 cm ahead of it at 0.40) and follows the bumper's curve beyond |x| 0.55. The bumper
    # below and the rake above keep the plan's curve: the blueprint's glass lower edge curves forward
    # like the bumper (a flat rake dipped the glass edge 1.6 cm at |x| 0.35). 90 % of the plan's
    # recession is taken out, so the face stays faintly convex
    flat = [0.0] * len(curve)
    if not front:
        f_tip = curve[-1][0][1]
        flat = [0.9 * (f - f_tip) * (1.0 - _smooth01((x - 0.30) / 0.25)) for (x, f), _ in curve]
    field = []
    for z in zs:
        xs = prof[z] if prof[z] is not None else first
        d_side = min(x_seam - xs - margin, 0.08)
        d_a, d_b = faces_[0](z), faces_[1](z)
        up = 0.0 if front else _smooth01((z - 0.52) / 0.04) * (1.0 - _smooth01((z - 0.80) / 0.13))
        field.append([d_side + (d_a + (d_b - d_a) * c - d_side) * w - fl * up * w for (w, c), fl in zip(blend, flat)])
    # envelope top line, tabulated (zt is a knot-scanning spline)
    f_lo, step = D.TAIL_EXT, 0.002
    ztab = [D.zt(f_lo + k * step) for k in range(int((D.NOSE_EXT - f_lo) / step) + 2)]

    def zt_at(f):
        u = min(max((f - f_lo) / step, 0.0), len(ztab) - 1.001)
        k = int(u)
        return ztab[k] + (ztab[k + 1] - ztab[k]) * (u - k)
    n = len(curve)
    scale = []
    for i, (((x, f), (nx, nf)), R) in enumerate(zip(curve, radius)):
        d_max = 0.0
        for z, row in zip(zs, field):
            d = row[i]
            if z <= zt_at(f - nf * d):
                d_max = max(d_max, d)
        scale.append(1.0 if d_max <= 1e-6 else min(1.0, 0.75 * R / d_max))
    # smoothed along the plan (the visible-height cut moves in waterline steps): a running
    # minimum over the two averaging passes' reach first, so smoothing never raises a sample
    scale = [min(scale[max(0, i - 12):i + 13]) for i in range(n)]
    for _ in range(2):
        scale = [sum(scale[max(0, i - 6):i + 7]) / len(scale[max(0, i - 6):i + 7]) for i in range(n)]
    out = (curve, radius, zs, field, scale, sign, seam)
    _FASCIA_FIELD[key] = out
    return out


def fascia_mesh(front=True, inset=0.0, n_plan=240, margin=0.008):
    """Closed waterline solid for one end (see module docstring)."""
    curve, radius, zs, field, scale, sign, seam = _fascia_field(front, n_plan, margin)
    rings = []
    for z, row in zip(zs, field):
        right = []
        for ((x, f), (nx, nf)), R, d, s in zip(curve, radius, row, scale):
            d *= s
            # waterlines above the body keep their full profile, so guard them against
            # swallowtails too; a soft clamp that is the identity below 0.75 R
            a = 0.75 * R
            if d > a:
                d = a + 0.2 * R * math.tanh((d - a) / (0.2 * R))
            d += inset
            right.append((x - nx * d, f - nf * d))
        right[-1] = (0.0, right[-1][1])
        left = [(-x, f) for x, f in reversed(right[:-1])]
        # out past the flanks at the seam, then along the whole car (the fascia never cuts behind the seam)
        far = -3.0 * sign
        ring = [(1.3 - inset, far), (1.3 - inset, seam)] + right + left + [(-1.3 + inset, seam), (-1.3 + inset, far)]
        rings.append([V(x, f, z + (inset if z == zs[0] else 0.0)) for x, f in ring])
    return _loft_closed(rings)


# ------------------------------------------------------------------ shape and skins

# Rounding where the fascias meet the envelope. A bevel modifier cannot do it on this mesh: the
# fascia side is 3 mm waterline strips and the boolean leaves slivers along the seam, so a clamped
# bevel stops at a few mm (the seam stays a torn stair-step) and an unclamped one folds over.
# Instead the faces within SEAM_BAND of the seam are triangulated and relaxed (Laplacian smooth
# weighted by distance to the seam), which rolls the edge over whatever the local mesh is.
SEAM_BAND = 0.025          # relaxed half-width either side of a fascia / envelope edge
SEAM_SMOOTH = (0.8, 60)    # smooth factor, iterations
ROUND_FADE = (1.0, 4.0)    # seam dihedral (deg) over which the relaxation fades in (a 6 deg crease still
                           # reads as a line on gloss paint, so only near-flat meetings are skipped)
# Round the rear corners the fascia takes over from the flank on a ramp of a few degrees (dims._W), a
# meeting that needs no rolling. The relaxation is a Laplacian smooth, which shrinks a convex surface:
# on the corner (15 cm plan radius) it pressed a groove a few mm deep down the 5 cm band, which read
# as a crumpled fold. There the fade starts at a steeper dihedral, so only real creases are rolled.
ROUND_FADE_CORNER = (9.0, 15.0)
CORNER_ZONE = (-1.72, 0.66)  # rear corners: f below, |x| above
# The front bumper's underside edge (the fascia meeting the envelope floor) is relaxed on a finer,
# quad-dominant band. The floor's section spans are about 14 cm wide, and a fully triangulated band
# there pulled the roll into a sawtooth that read as a crumpled edge (BEAUTY alternates the quads'
# diagonals, and every seam vertex was tied to floor vertices 14 cm away). Inside ROLL_ZONE the band's
# edges longer than ROLL_EDGE are split first, quads stay quads and only n-gons are triangulated.
ROLL_ZONE = (1.30, 0.22)   # front bumper underside: f above, z below (every inset's floor is under 0.22)
ROLL_EDGE = 0.006


def _tag_src(o, value):
    at = o.data.attributes.new('src', 'INT', 'FACE')
    at.data.foreach_set('value', [value] * len(o.data.polygons))


def _src_by_distance(o, mult, inset):
    """Fallback face source (0 envelope, 1 front, 2 rear) when the boolean drops 'src': faces lying
    on the envelope are envelope faces, the rest belong to the fascia on their end."""
    from mathutils.bvhtree import BVHTree
    verts, faces = envelope_mesh(mult, inset)
    tree = BVHTree.FromPolygons([tuple(v) for v in verts], faces)
    src = []
    for p in o.data.polygons:
        hit = tree.find_nearest(p.center)
        on_env = hit[0] is not None and hit[3] < 1e-5
        src.append(0 if on_env else (1 if -p.center.y > 0 else 2))
    return np.array(src)


def _seam_edges(o, mult, inset):
    """Per-edge seam weight: edges between faces of different source (envelope / front / rear
    fascia), faded in over ROUND_FADE so only near-flat meetings are left alone."""
    me = o.data
    npoly, nloop, nedge = len(me.polygons), len(me.loops), len(me.edges)
    at = me.attributes.get('src')
    src = None
    if at is not None and at.domain == 'FACE':
        src = np.empty(npoly, dtype=np.int32)
        at.data.foreach_get('value', src)
        if len(np.unique(src)) < 2:
            src = None
    if src is None:
        print('shape: src attribute lost in the boolean, classifying faces by distance')
        src = _src_by_distance(o, mult, inset)
    nrm = np.empty(npoly * 3)
    me.polygons.foreach_get('normal', nrm)
    nrm = nrm.reshape(-1, 3)
    total = np.empty(npoly, dtype=np.int64)
    me.polygons.foreach_get('loop_total', total)
    loop_poly = np.repeat(np.arange(npoly), total)
    loop_edge = np.empty(nloop, dtype=np.int64)
    me.loops.foreach_get('edge_index', loop_edge)
    order = np.argsort(loop_edge, kind='stable')
    e_sorted = loop_edge[order]
    first = np.searchsorted(e_sorted, np.arange(nedge), 'left')
    last = np.searchsorted(e_sorted, np.arange(nedge), 'right') - 1
    ok = last > first                        # edges with two faces
    fa = loop_poly[order[np.minimum(first, nloop - 1)]]
    fb = loop_poly[order[np.maximum(last, 0)]]
    cosang = np.clip((nrm[fa] * nrm[fb]).sum(1), -1.0, 1.0)
    ang = np.degrees(np.arccos(cosang))
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    ev = np.empty(nedge * 2, dtype=np.int64)
    me.edges.foreach_get('vertices', ev)
    mid = 0.5 * (co[ev[0::2]] + co[ev[1::2]])
    corner = (-mid[:, 1] < CORNER_ZONE[0]) & (np.abs(mid[:, 0]) > CORNER_ZONE[1])
    lo = np.where(corner, ROUND_FADE_CORNER[0], ROUND_FADE[0])
    hi = np.where(corner, ROUND_FADE_CORNER[1], ROUND_FADE[1])
    t = np.clip((ang - lo) / (hi - lo), 0.0, 1.0)
    return np.where(ok & (src[fa] != src[fb]), t * t * (3 - 2 * t), 0.0)


def _round_seams(o, mult, inset):
    """Roll the fascia / envelope edges: vertex weights fall off with distance to the seam
    (times the seam's dihedral fade), the band is triangulated so relaxed faces stay planar
    (in ROLL_ZONE refined and kept quad-dominant instead), then a weighted Smooth modifier is applied. Every inset gets the same band, so a skin's
    inner surface rounds at least as much as its outer one and the shell never thins."""
    import bmesh
    from mathutils.kdtree import KDTree
    me = o.data
    w_edge = _seam_edges(o, mult, inset)
    nv = len(me.vertices)
    co = np.empty(nv * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    ev = np.empty(len(me.edges) * 2, dtype=np.int64)
    me.edges.foreach_get('vertices', ev)
    ev = ev.reshape(-1, 2)
    sel = np.nonzero(w_edge > 0.0)[0]
    if not len(sel):
        return
    # seam sampled every ~2 mm
    pa, pb = co[ev[sel, 0]], co[ev[sel, 1]]
    k = np.maximum(1, np.ceil(np.linalg.norm(pb - pa, axis=1) / 0.002).astype(np.int64))
    rep = np.repeat(np.arange(len(sel)), k + 1)
    tt = np.concatenate([np.linspace(0.0, 1.0, n + 1) for n in k])
    pts = pa[rep] + (pb[rep] - pa[rep]) * tt[:, None]
    fade = w_edge[sel][rep]
    kd = KDTree(len(pts))
    for i, p in enumerate(pts):
        kd.insert(p, i)
    kd.balance()
    # only vertices in the stations the seams span (the front and rear ends) can be near them
    spans = []
    for end in (pts[-pts[:, 1] > 0], pts[-pts[:, 1] <= 0]):
        if len(end):
            spans.append(((-end[:, 1]).min() - SEAM_BAND, (-end[:, 1]).max() + SEAM_BAND))

    def weigh(co):
        w = np.zeros(len(co))
        fy = -co[:, 1]
        near = np.zeros(len(co), dtype=bool)
        for lo, hi in spans:
            near |= (fy > lo) & (fy < hi)
        for i in np.nonzero(near)[0]:
            _, j, d = kd.find(co[i])
            if d < SEAM_BAND:
                s = 1.0 - d / SEAM_BAND
                w[i] = s * s * (3 - 2 * s) * fade[j]
        return w
    wv = weigh(co)
    band = wv > 0.0
    if not band.any():
        return
    # triangulate the band so the relaxation never bends an n-gon; in ROLL_ZONE split the long
    # edges first and keep the quads
    total = np.empty(len(me.polygons), dtype=np.int64)
    me.polygons.foreach_get('loop_total', total)
    lv = np.empty(len(me.loops), dtype=np.int64)
    me.loops.foreach_get('vertex_index', lv)
    starts = np.concatenate(([0], np.cumsum(total)[:-1]))
    touch = np.add.reduceat(band[lv].astype(np.int64), starts) > 0
    out_zone = (co[:, 2] >= ROLL_ZONE[1]) | (-co[:, 1] <= ROLL_ZONE[0])
    in_zone = np.add.reduceat(out_zone[lv].astype(np.int64), starts) == 0
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    faces = [bm.faces[i] for i in np.nonzero(touch & ~in_zone & (total > 3))[0]]
    roll = [bm.faces[i] for i in np.nonzero(touch & in_zone)[0]]
    if roll:
        cuts = {}
        for e in {e for f in roll for e in f.edges}:
            n = int(e.calc_length() / ROLL_EDGE)
            if n:
                cuts.setdefault(min(n, 40), []).append(e)
        split = {f for es in cuts.values() for e in es for f in e.link_faces}
        for n, es in cuts.items():
            bmesh.ops.subdivide_edges(bm, edges=es, cuts=n)
        faces = list(set(faces) | {f for f in split.union(roll) if f.is_valid and len(f.verts) > 4})
    bmesh.ops.triangulate(bm, faces=faces, quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(me)
    bm.free()
    me.update()
    if len(me.vertices) > nv:                # weights for the split vertices (appended after the old ones)
        co2 = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get('co', co2)
        wv = np.concatenate((wv, weigh(co2.reshape(-1, 3)[nv:])))
    vg = o.vertex_groups.new(name='seam')
    q = np.round(wv * 64).astype(np.int64)
    for level in np.unique(q[q > 0]):
        vg.add(np.nonzero(q == level)[0].tolist(), level / 64.0, 'REPLACE')
    m = o.modifiers.new('seam', 'SMOOTH')
    m.factor, m.iterations = SEAM_SMOOTH
    m.vertex_group = 'seam'
    kit.apply_modifiers(o)
    g = o.vertex_groups.get('seam')          # (group names live on the mesh, which apply replaced)
    if g is not None:
        o.vertex_groups.remove(g)


def shape_object(coll, name, inset=0.0, mult=1):
    """Envelope ^ front fascia ^ rear fascia, inset by `inset`, with the meeting edges
    (hood leading edge, lamp tops, fender corners, glass lower edge, bumper undersides) rolled."""
    o = kit.obj_from_pydata(name, *envelope_mesh(mult, inset), ['paint'], coll=coll, smooth=True)
    kit.fix_normals(o)
    _tag_src(o, 0)
    for front in (True, False):
        c = kit.cutter_obj(fascia_mesh(front, inset))
        _tag_src(c, 1 if front else 2)
        kit.boolean(o, c, 'INTERSECT')
    kit.fix_normals(o)
    # the boolean brings the cutters' slot and flat shading onto the fascia faces
    me = o.data
    while len(me.materials) > 1:
        me.materials.pop()
    n = len(me.polygons)
    me.polygons.foreach_set('material_index', [0] * n)
    me.polygons.foreach_set('use_smooth', [True] * n)
    _round_seams(o, mult, inset)
    a = o.data.attributes.get('src')
    if a is not None:
        o.data.attributes.remove(a)
    return o


_SHAPE = {}


def base_shape(coll, mult=1):
    """The outer shape (inset 0), built once and render-hidden; release_shape frees it."""
    key = (0.0, mult)
    if key not in _SHAPE or _SHAPE[key].name not in kit.bpy.data.objects:
        base = shape_object(coll, 'ek.shape0', 0.0, mult)
        base.hide_render = True
        _SHAPE[key] = base
    return _SHAPE[key]


def outer_object(coll, name='ek.outer', slot='paint', mult=1):
    base = base_shape(coll, mult)
    o = base.copy()
    o.data = base.data.copy()
    o.name = name
    o.hide_render = False
    coll.objects.link(o)
    o.data.materials.clear()
    o.data.materials.append(kit.mats.get(slot))
    for p in o.data.polygons:
        p.material_index = 0
    return o


def make_skin(name, thickness, slot, coll, inner='interior', mult=1, keep_inner=False):
    """Shell between the outer shape and the shape inset by `thickness`:
    outer faces `slot`, inner faces `inner`, shut-line rims `slot`.
    keep_inner: also return a copy of the inner solid, (skin, solid)."""
    o = outer_object(coll, name, slot, mult)
    inner_o = shape_object(coll, name + '.in', thickness, mult)
    inner_o.data.materials.clear()
    inner_o.data.materials.append(kit.mats.get(inner if inner else slot))
    kept = None
    if keep_inner:
        # copied before the boolean hides the cutter (a viewport-hidden object is never evaluated)
        kept = inner_o.copy()
        kept.data = inner_o.data.copy()
        kept.name = name + '.solid'
        coll.objects.link(kept)
    kit.boolean(o, inner_o, 'DIFFERENCE', material_mode='TRANSFER')
    return (o, kept) if keep_inner else o


def release_shape():
    for k, o in list(_SHAPE.items()):
        if o.name in kit.bpy.data.objects:
            discard(o)
        del _SHAPE[k]


def discard(o):
    data = o.data
    kit.bpy.data.objects.remove(o, do_unlink=True)
    if data is not None and data.users == 0:
        kit.bpy.data.meshes.remove(data)


# ----------------------------------------------------------------- regions

def _shrunk(poly, shrink):
    return kit.offset_poly(kit.ccw(poly), -shrink) if shrink else kit.ccw(poly)


def side_prism(poly_fz, x0, x1, shrink=G):
    """Side-view (f, z) region extruded across x0..x1."""
    p = _shrunk(poly_fz, shrink)
    n = len(p)
    verts = [V(x0, f, z) for f, z in p] + [V(x1, f, z) for f, z in p]
    faces = [list(range(n)), list(range(n, 2 * n))]
    faces += [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    return verts, faces


def top_prism(poly_xf, z0, z1, shrink=G):
    """Top-view (x, f) region extruded over z0..z1."""
    p = _shrunk(poly_xf, shrink)
    n = len(p)
    verts = [V(x, f, z0) for x, f in p] + [V(x, f, z1) for x, f in p]
    faces = [list(range(n)), list(range(n, 2 * n))]
    faces += [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    return verts, faces


def front_prism(poly_xz, f0, f1, shrink=G):
    """Front-view (x, z) region extruded along f0..f1."""
    p = _shrunk(poly_xz, shrink)
    n = len(p)
    verts = [V(x, f0, z) for x, z in p] + [V(x, f1, z) for x, z in p]
    faces = [list(range(n)), list(range(n, 2 * n))]
    faces += [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    return verts, faces


def cut_region(skin, name, cutters, coll, pockets=(), transfer=False):
    """Copy of `skin` intersected with every cutter, then minus every pocket. Pockets are meshes or
    objects (consumed); with `transfer` a pocket's faces keep its cutter's slot ('interior' for a mesh,
    so an object carries any other slot itself)."""
    o = skin.copy()
    o.data = skin.data.copy()
    o.name = name
    o.hide_render = False
    coll.objects.link(o)
    for m in cutters:
        kit.boolean(o, kit.cutter_obj(m), 'INTERSECT')
    for m in pockets:
        c = m if hasattr(m, 'data') else kit.cutter_obj(m)
        kit.boolean(o, c, 'DIFFERENCE', material_mode='TRANSFER' if transfer else 'INDEX')
    return o


def cut_shell(outer, inner, name, coll, cutters=(), pockets=(), inner_pockets=()):
    """A panel carved from solids instead of a skin: (outer ^ cutters - pockets) - (inner -
    inner_pockets), one closed shell. A pocket that goes deeper than the skin (a recess, a notch)
    gets a grown copy in inner_pockets, so the panel keeps a wall round it instead of opening into
    the hollow body. Pockets and inner pockets are meshes or objects (objects are consumed); inner
    faces take the inner solid's slot, pocket faces the outer's (a recess floor, a notch ceiling).
    The pockets carry that slot themselves: after the first boolean the panel holds the cutters'
    slot as well, and index mode then gave every later pocket's faces 'interior'."""
    o = cut_region(outer, name, cutters, coll)
    slot = outer.data.materials[0]
    for m in pockets:
        c = m if hasattr(m, 'data') else kit.cutter_obj(m)
        c.data.materials.clear()
        c.data.materials.append(slot)
        c.data.polygons.foreach_set('material_index', [0] * len(c.data.polygons))
        kit.boolean(o, c, 'DIFFERENCE', material_mode='TRANSFER')
    if hasattr(inner, 'data'):
        h = cut_region(inner, name + '.in', [], coll)
    else:
        h = kit.cutter_obj(inner, name + '.in')
    for m in inner_pockets:
        kit.boolean(h, m if hasattr(m, 'data') else kit.cutter_obj(m), 'DIFFERENCE')
    kit.boolean(o, h, 'DIFFERENCE', material_mode='TRANSFER')
    return o


def solid_minus(mesh, solid, coll, name='cutter'):
    """Cutter object: a (verts, faces) mesh minus a copy of a kept solid (e.g. a prism minus the shape
    12 mm in leaves the part of the prism within 12 mm of the surface)."""
    c = kit.cutter_obj(mesh, name)
    s = solid.copy()
    s.data = solid.data.copy()
    coll.objects.link(s)
    kit.boolean(c, s, 'DIFFERENCE')
    return c


def mirror_x(poly_xf):
    return [(-x, f) for x, f in poly_xf]


def bool_mesh(a, b, op='DIFFERENCE'):
    """(verts, faces) of a boolean between two closed meshes (for compound cutters)."""
    o = kit.cutter_obj(a, 'bool_a')
    kit.boolean(o, kit.cutter_obj(b), op)
    verts = [o.matrix_world @ v.co for v in o.data.vertices]
    faces = [list(p.vertices) for p in o.data.polygons]
    discard(o)
    return verts, faces


_FASCIA = {}


def fascia_in(front, inset):
    """Cached fascia solid inset by `inset`: skin minus fascia_in(t) is the skin within t of
    the fascia face (lamps, grille, hatch panel); skin intersect fascia_in(t) is the rest."""
    key = (front, round(inset, 5))
    if key not in _FASCIA:
        _FASCIA[key] = fascia_mesh(front, inset)
    return _FASCIA[key]
