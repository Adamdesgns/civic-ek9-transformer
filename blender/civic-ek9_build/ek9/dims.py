"""Civic Type R (EK9, 1999-2000 facelift) datums, metres, authoring frame.

Production figures: 4.18 m long, 1.695 m wide, 2.62 m wheelbase, 1.48 m track.
The reference car is TopRank stock #111040 (refs/ref_images/ek9-gallery/yellow-111040_*): 195/50 R15
tyres on white five-spoke Volks, the body RIDE above the design datums (which put the sills at 0.13 m).
f = forward (nose +), x = car left, z = up, origin midway along the length.

Outlines are measured from refs/ref_images/civic-ek-hatch.png with
tools/civic-ek9/measure_blueprint.py and grid_crop.py, mapped as
f = f_bp, x = 0.9855 x_bp (1.695 m width), z = 1.0144 z_bp - 0.093
(roof 1.325 m, sills 0.13 m). Keep new datums in blueprint proportion.

The body is one lofted outer surface. Each station f has a closed section
built from a control polygon (body.section_ctrl) whose landmarks follow the
tracks below; the tracks are monotone cubics, so moving a knot slides a
feature without ripples.
"""
from .shape import Track, curve1

LENGTH, WIDTH, HEIGHT = 4.18, 1.695, 1.325
NOSE, TAIL = LENGTH / 2, -LENGTH / 2
FA, RA = 1.22, -1.40                 # front / rear axle stations (2.62 m wheelbase)
# wheel centre half track per axle: the tyre faces (WX + TYRE_W / 2) sit just inside the fender
# lips, which a ray cast puts at x 0.831 (front) and 0.842 (rear) over the arch tops
WX_F, WX_R = 0.732, 0.742
TYRE_R, TYRE_W = 0.288, 0.195        # 195/50 R15 (read off the sidewall in photo 62)
RIM_R = 0.1905                       # 15 in bead seat
# wheel-arch circle, in design space (the body datums)
ARCH_Z, ARCH_R = 0.245, 0.36
# The body stands RIDE above its datums on the wheels (build.car_only lifts every non-wheel part).
# Measured in the side profile (photo 64, 3.44 mm/px from the wheelbase): 3.8 cm (front) and 4.1 cm
# (rear) from the tyre top to the arch top, with the arch circle 1-3.5 cm under the hub. Most of the
# gap is the smaller tyre: 1 cm of lift puts the arch top 3.9 cm over the 195/50 R15
RIDE = 0.010
XS = WIDTH / 2


def bp_z(z):
    return 1.0144 * z - 0.093


# landmark stations
WS_BASE = 0.822                      # windshield base at the centreline (curves back to A_BASE at the pillars)
A_BASE = 0.72                        # A-pillar base
HOOD_REAR = 0.915                    # hood rear edge at the centreline (cowl between it and the glass)
WS_TOP = 0.10                        # windshield header at the centreline
ROOF_END = -1.26                     # roof rear edge / hatch hinge line
HATCH_LOW = -1.935                   # hatch glass lower edge (centreline, z 0.945; see _FACE_R)
HOOD_FRONT = 1.97                    # hood leading edge (top of the grille)
DOOR_F, DOOR_R = 0.70, -0.555        # door shut lines at the sill
B_PILLAR = -0.60                     # door / quarter shut line up the B-pillar
QTR_WIN_R = -1.36                    # quarter window rear tip
TAIL_FACE = -2.012                   # tail lamp / hatch panel face (centreline, z 0.56-0.80)

# seams and openings (design units)
BUMPER_TOP_F = 0.516                 # front bumper top line (headlight / grille bottoms)
BUMPER_SEAM_F = 1.555                # front bumper / fender seam station at the arch
# rear bumper / quarter seam (side view): horizontal at BUMPER_TOP_R from inside the rear arch
# (BUMPER_SEAM_R, hidden in the opening) back to BUMPER_STEP_F under the lamp's front corner, where it
# steps up to the lamp bottom; between the lamps the hatch panel comes down to HATCH_PANEL_LOW
BUMPER_TOP_R = 0.572
BUMPER_SEAM_R = -1.50
BUMPER_STEP_F = -1.817
TAIL_LAMP_LOW = 0.600                # tail lamp bottom = bumper top under the lamps
HATCH_PANEL_LOW = 0.555              # hatch panel bottom between the lamps
DOOR_BOTTOM = 0.221                  # door skin bottom (skirt top)
# hood / fender seam in plan (f, x), rear corner forward (photos 67, 75, 89): one straight line from the
# hood's rear corner at the cowl along the fender tops, 2-3 cm inboard of the shoulder crest, into the
# headlamp's top about 10 cm inboard of its outer corner (x ~0.69). It does not turn out toward the
# corner: the fender wraps the lamp's outer end, and the hood's edge inboard of the seam is the lamp top
HOOD_SEAM = [(0.841, 0.660), (2.60, 0.717)]
HOOD_REAR_X = HOOD_SEAM[0][1]        # the hood's rear corners (cowl)


def hood_seam_x(f):
    """Half width of the hood / fender seam at station f (clamped to its ends)."""
    pts = HOOD_SEAM
    if f <= pts[0][0]:
        return pts[0][1]
    for (fa, xa), (fb, xb) in zip(pts, pts[1:]):
        if f <= fb:
            return xa + (xb - xa) * (f - fa) / (fb - fa)
    return pts[-1][1]


# documentation only (parts.GRILLE_SLOT, LAMP_FRONT_XZ and LAMP_SIDE_FZ are the shapes)
GRILLE = (0.305, 0.535, 0.592)       # grille slot: half width, bottom, top
LAMP_F = (0.365, 0.80, 0.516, 0.660) # headlight front view: tip x, corner x, z bottom, z top (peak)
LAMP_REAR_F = 1.587                  # headlight rear end on the flank
TAIL_LAMP_X = 0.575                  # tail lamp inner edge at mid-height (parts.tail_lamp_x leans it 0.568-0.600)
TAIL_LAMP_SIDE_F = -1.793            # tail lamp leading edge on the quarter (about 16 cm of lamp side)
HATCH_PANEL_TOP = 0.945              # hatch lower panel top (glass bottom, centreline)

# ---------------------------------------------------------------- tracks
# The envelope is the body WITHOUT its ends: hood, fenders, roof, hatch glass and
# flanks carry on past the car's length (to NOSE_EXT / TAIL_EXT) at their own
# shape. The front and rear fascias (waterline solids, see body) carve the real
# ends out of it, so the hood's leading edge, the lamp tops and the hatch-glass
# lower edge are where the two surfaces meet.
NOSE_EXT, TAIL_EXT = 2.30, -2.30

# zt: centreline top (hatch glass, roof, windshield, hood), extended past both ends
_ZT = [(TAIL_EXT, 0.718), (-2.10, 0.841), (-2.00, 0.903), (-1.916, 0.955), (-1.814, 1.018), (-1.713, 1.082),
       (-1.611, 1.147), (-1.51, 1.208), (-1.42, 1.254), (-1.34, 1.280), (ROOF_END, 1.296), (-1.155, 1.310),
       (-1.00, 1.319), (-0.70, 1.325), (-0.40, 1.323), (-0.19, 1.317), (-0.09, 1.309), (0.011, 1.290),
       (0.062, 1.274), (WS_TOP, 1.257), (0.265, 1.174), (0.467, 1.064), (0.670, 0.954), (0.772, 0.897),
       (WS_BASE, 0.874), (0.873, 0.861), (0.974, 0.844), (1.177, 0.811), (1.380, 0.773), (1.583, 0.733),
       (1.684, 0.709), (1.786, 0.680), (1.836, 0.663), (1.887, 0.641), (1.95, 0.612), (2.05, 0.566),
       (2.15, 0.52), (NOSE_EXT, 0.451)]

# zb: underside (sills; the rear valance rises to the rear bumper's bottom)
_ZB = [(TAIL_EXT, 0.19), (-2.0, 0.19), (-1.95, 0.19),(-1.90, 0.15), (-1.85, 0.138), (-1.75, 0.132),
       (-1.0, 0.13), (1.0, 0.13), (NOSE_EXT, 0.13)]

# W: widest half width (flanks only; the fascias round the corners in plan)
# At the rear the flank eases out from the plan (PLAN_R) behind the arch, by 13 mm at f -1.94, and
# then turns with the plan's corner arc, staying outside it. The rear fascia's waterlines start 8 mm
# outside the flank at the seam station (its margin), so they cross the flank on that gentle ramp
# (about 3-4 degrees, near f -1.84, at every height) and carry the whole corner: its surface is the
# flank's own section swept round the plan arc, blending into the face profile as the plan turns.
# A flank running straight on to 0.765 at f -2.0 was cut by the turning fascia at 20-30 degrees
# (turning in, back out, then creased), and the seam roll left a crumpled fold down both rear corners.
_W = [(TAIL_EXT, 0.70), (-2.05, 0.712), (-2.0, 0.734), (-1.98, 0.7565), (-1.96, 0.7766), (-1.94, 0.793),
      (-1.91, 0.8068), (-1.88, 0.8152), (-1.85, 0.8216), (-1.80, 0.8313), (-1.75, 0.835),
      (-1.70, 0.838), (-1.40, 0.8475), (0.40, 0.845), (1.20, 0.842), (1.40, 0.838), (1.484, 0.834), (1.56, 0.826),
      (1.625, 0.812), (1.686, 0.795), (1.745, 0.776), (1.80, 0.758), (2.0, 0.70), (NOSE_EXT, 0.62)]
# (the flanks follow the plan outline PLAN_F / PLAN_R up to the lamps, so the fascias
# only carve the corners: the lamps' side edges are where a fascia first cuts the flank)

# zw: height of the widest point
_ZW = [(TAIL_EXT, 0.47), (-1.6, 0.52), (0.0, 0.52), (1.6, 0.50), (NOSE_EXT, 0.48)]

# char: flank character line (the side wall's top crease)
_CHAR = [(TAIL_EXT, 0.84), (-1.80, 0.835), (-1.50, 0.826), (-0.80, 0.795),
         (0.0, 0.75), (0.60, 0.734), (1.00, 0.707), (1.20, 0.69), (1.70, 0.667), (1.90, 0.648), (NOSE_EXT, 0.62)]

# belt: window sill / D-pillar base / fender top (clamped under the top surface)
# (behind the B-pillar: the blueprint's upper sill line, 0.887 / 0.896 / 0.905 at f -0.8 / -1.0 / -1.2)
_BELT = [(TAIL_EXT, 0.95), (-1.90, 0.945), (-1.60, 0.935), (-1.35, 0.912), (-1.10, 0.902), (-0.65, 0.885),
         (-0.50, 0.876), (0.0, 0.855), (0.60, 0.835), (0.80, 0.845), (0.90, 1.2), (NOSE_EXT, 1.2)]

# crown: drop from the centreline to the roof / hood edge
_CROWN = [(TAIL_EXT, 0.03), (HATCH_LOW, 0.03), (-1.50, 0.04), (ROOF_END, 0.05), (-0.60, 0.05),
          (WS_TOP, 0.045), (0.50, 0.035), (WS_BASE, 0.03), (1.30, 0.025), (1.90, 0.02), (NOSE_EXT, 0.02)]

# xr: roof edge / A-pillar / D-pillar / hood-to-fender edge half width
_XR = [(TAIL_EXT, 0.68), (-1.93, 0.68), (-1.85, 0.69), (-1.75, 0.685), (-1.60, 0.66),
       (-1.50, 0.63), (-1.42, 0.60), (-1.30, 0.585), (ROOF_END, 0.575), (-0.60, 0.545), (0.0, 0.545),
       (WS_TOP, 0.57), (0.40, 0.63), (A_BASE, 0.70), (0.80, 0.705), (1.20, 0.70), (1.60, 0.69), (NOSE_EXT, 0.68)]

# ledge: glass-base (or fender-top) inset from the character line
_LEDGE = [(TAIL_EXT, 0.035), (-1.93, 0.035), (-1.4, 0.04), (0.0, 0.04), (0.70, 0.04), (0.90, 0.05), (NOSE_EXT, 0.05)]

# tumble: character-line inset from the belly. Along the doors and quarters the upper flank leans in
# about 6 degrees, so the sides curve (sky above, ground below in the paint) instead of reading as a
# flat slab; the ends keep the lamps' original flank
_TUMBLE = [(TAIL_EXT, 0.016), (-1.75, 0.016), (-1.40, 0.024), (0.0, 0.027), (1.10, 0.024), (1.45, 0.017),
           (NOSE_EXT, 0.016)]

TRACK = Track(zt=_ZT, zb=_ZB, W=_W, zw=_ZW, char=_CHAR, belt=_BELT, crown=_CROWN, xr=_XR,
              ledge=_LEDGE, tumble=_TUMBLE)

zt = curve1(_ZT)
zb = curve1(_ZB)
W = curve1(_W)
xr = curve1(_XR)
crown = curve1(_CROWN)


def smin(a, b, k):
    """Smooth minimum (blend width k): C1 where a crosses b, no crease in the loft."""
    return 0.5 * (a + b - ((a - b) ** 2 + k * k) ** 0.5)


def smax(a, b, k):
    return -smin(-a, -b, k)


def landmarks(f):
    """Resolved section landmarks at station f (all clamps smooth, so the loft never creases)."""
    p = TRACK(f)
    zt_, zb_, Wd = p['zt'], p['zb'], p['W']
    zr = zt_ - p['crown']
    zbelt = smin(p['belt'], zr, 0.03)
    zchar = smin(p['char'], zbelt - 0.02, 0.03)
    zchar = smax(zchar, zb_ + 0.4 * (zbelt - zb_), 0.03)
    xc = Wd - min(p['tumble'], 0.2 * Wd)
    xg = xc - min(p['ledge'], 0.3 * xc)
    xr_ = smin(p['xr'], xg - 0.006, 0.02)
    lo, hi = zb_ + 0.3 * (zchar - zb_), zb_ + 0.75 * (zchar - zb_)
    zw = smin(smax(p['zw'], lo, 0.03), hi, 0.03)
    return dict(zt=zt_, zb=zb_, W=Wd, zr=zr, zbelt=zbelt, zchar=zchar, zw=zw, xc=xc, xg=xg, xr=xr_,
                crown=p['crown'])


def belt(f):
    return landmarks(f)['zbelt']


def glass_edge_x(f):
    """Windshield / hatch glass side edge in plan (inside the A / D pillar)."""
    return landmarks(f)['xr'] - 0.022


# ------------------------------------------------------------ fascias
# plan outlines (x, f), right half, seam -> centreline tip (blueprint top view)
PLAN_F = [(0.838, 1.40), (0.834, 1.484), (0.826, 1.56), (0.812, 1.625), (0.795, 1.686), (0.776, 1.745),
          (0.748, 1.80), (0.706, 1.862), (0.639, 1.93), (0.558, 1.985), (0.432, 2.036), (0.33, 2.064),
          (0.22, 2.081), (0.10, 2.090), (0.0, 2.092)]
# (the rear corner is one 0.15 m arc, about 8 deg per point: a single knot turning ~24 deg printed
# a groove down the bumper and through both tail lamps)
PLAN_R = [(0.838, -1.70), (0.826, -1.80), (0.813, -1.85), (0.800, -1.895), (0.786, -1.930), (0.764, -1.960),
          (0.735, -1.984), (0.702, -2.000), (0.62, -2.03), (0.50, -2.058), (0.36, -2.076), (0.20, -2.087),
          (0.0, -2.092)]
SEAM_FASCIA_F, SEAM_FASCIA_R = 1.40, -1.70
TIP = 2.092

# face insets behind the plan tip by height.
# Front: the bumper (z <= 0.516) is one profile; above it the lamps slope back
# harder than the hood's nose between them, which comes down to the grille top.
# The bumper is #111040's Type R face (photo 64, the centreline silhouette measured against the nose
# just above it, so the camera's depth drops out): nearly upright from z 0.31 to 0.50, 4 cm behind the
# plan tip at its fullest, where the blueprint's base bumper carried a ridge 4.5 cm prouder at z 0.40.
# Under z 0.23 it tucks away behind the lip (parts.front_lip)
_BUMPER_F = [(0.05, 0.110), (0.13, 0.100), (0.161, 0.094), (0.20, 0.088), (0.232, 0.080), (0.27, 0.071),
             (0.31, 0.066), (0.333, 0.060), (0.355, 0.052), (0.376, 0.047), (0.40, 0.043), (0.44, 0.040),
             (0.462, 0.040), (0.483, 0.044), (0.50, 0.058), (0.516, 0.080)]
_LAMP_F = _BUMPER_F + [(0.53, 0.113), (0.56, 0.135), (0.60, 0.165), (0.63, 0.19), (0.663, 0.23), (0.70, 0.285),
                       (0.72, 0.30), (1.9, 0.30)]
_NOSE_F = _BUMPER_F + [(0.53, 0.108), (0.56, 0.121), (0.612, 0.146), (0.65, 0.162), (0.75, 0.20), (1.0, 0.25),
                       (1.9, 0.25)]
# Rear (blueprint side silhouette): the bumper's tuck-under, its vertical face (z 0.36-0.50), a tight
# shoulder (0.52-0.56) up to the lamp / hatch-panel plane 8 cm behind the tip, which rakes back over
# the top of the lamps into the hatch glass. No ledge: the bumper top seam is a line on that plane.
# Above 0.90 the face runs just under the glass (0.2-0.8 cm) and meets it at about 0.945, so the
# glass edge sits 2.5 cm above the blueprint's 0.92; a seam at 0.92 would pull the 25 mm seam roll
# into the tail lamp tops (0.90).
_FACE_R = [(0.05, 0.10), (0.19, 0.085), (0.21, 0.083), (0.24, 0.076), (0.27, 0.056), (0.30, 0.037), (0.33, 0.018),
           (0.36, 0.004), (0.40, 0.0), (0.46, 0.002), (0.50, 0.002), (0.52, 0.006), (0.54, 0.044), (0.56, 0.080),
           (0.575, 0.080), (0.80, 0.080), (0.90, 0.111), (0.93, 0.143), (0.942, 0.155), (1.0, 0.18),
           (1.2, 0.22), (1.3, 0.25), (1.9, 0.25)]
# ... and at the rear corners (blended in by REAR_CORNER_X): the bumper is the same, but the lamp level
# stands only 2 cm inside the bumper's plan, so the lamp / hatch face is flatter in plan than the
# bumper and the lamps wrap round a square corner onto the flank (the blueprint's corner line at
# f -1.954); above the lamps it rakes back parallel to the centre
_FACE_R_CORNER = _FACE_R[:12] + [(0.535, 0.014), (0.55, 0.019), (0.56, 0.020), (0.80, 0.020), (0.90, 0.051),
                                 (0.93, 0.083), (0.942, 0.095), (1.0, 0.12), (1.2, 0.16), (1.3, 0.19), (1.9, 0.19)]
REAR_CORNER_X = 0.78                 # corner blend (x / REAR_CORNER_X) ** 4: 0.17 at x 0.5, 0.65 at 0.7
FACE_LAMP_F = curve1(_LAMP_F)
FACE_NOSE_F = curve1(_NOSE_F)
FACE_R = curve1(_FACE_R)
FACE_R_CORNER = curve1(_FACE_R_CORNER)
