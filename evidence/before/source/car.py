"""EK9 exterior panels cut from the envelope skins (see body), plus the bumper
lofts, arches and wheels.

Side-view openings are measured from the blueprint (dims docstring). Regions
are written for the car's left side (x > 0) and mirrored.
"""
import math
from . import kit, body as B, dims as D, parts, wheels, side, cabin
from .body import G
from .shape import spline_centripetal

BIG = 1.6
Z_HI = 2.2


def side_x(s):
    return (0.25, BIG) if s > 0 else (-BIG, -0.25)


def mx(poly, s):
    return poly if s > 0 else B.mirror_x(poly)


def lerp(a, b, t):
    return a + (b - a) * t


def samples(f0, f1, n):
    return [lerp(f0, f1, k / n) for k in range(n + 1)]


# --------------------------------------------------------------- seam curves

hood_seam_x = D.hood_seam_x


def hood_rear_f(x):
    return 0.93 - 0.075 * (x / 0.606) ** 2


def ws_base_f(x):
    return 0.905 - 0.185 * (min(abs(x), 0.72) / 0.70) ** 2.2


def header_f(x):
    return D.WS_TOP - 0.035 * (x / 0.57) ** 2


glass_edge_x = D.glass_edge_x


# Window tops sit WIN_DROP under the blueprint's glass line (1.268). There the glass ran up into the
# roof edge's rounding (zr about 1.27), so no roof side was left above it: from the low three-quarter
# cameras (and in the reference photo) the EK shows a band of body-colour roof over the side glass,
# and without it the greenhouse read as a tall box. The door window keeps the A-pillar edge's line and
# turns into the lower top sooner; on the quarter window the drop fades out below WIN_FADE, so its rear
# sweep and tip keep the blueprint's lines.
WIN_DROP, WIN_FADE = 0.045, (1.05, 1.24)


def _win_top(pts):
    lo, hi = WIN_FADE
    out = []
    for f, z in pts:
        t = min(1.0, max(0.0, (z - lo) / (hi - lo)))
        out.append((f, z - WIN_DROP * t * t * (3 - 2 * t)))
    return out


# door window opening (side view), front-lower corner at the mirror sail, clockwise
SILL = 0.012            # black sill molding between the door top and the door glass
DWIN_UPPER = [(0.50, 0.878), (0.30, 0.99), (0.10, 1.105), (0.01, 1.155), (-0.04, 1.183), (-0.10, 1.205),
              (-0.18, 1.2165), (-0.30, 1.221), (-0.59, 1.268 - WIN_DROP)]
# quarter window: the B-pillar edge, then one centripetal spline from the top-front corner round the
# rear sweep and the rounded tip (about 4.5 cm radius, the blueprint's glass line) along the sill,
# which sits 1 cm above the belt (a polygon tip read as facets and a hard point)
QWIN = [(-0.645, 0.891)] + spline_centripetal(_win_top(
    [(-0.665, 1.268), (-0.80, 1.272), (-1.00, 1.268), (-1.12, 1.243), (-1.21, 1.18), (-1.28, 1.10), (-1.312, 1.05),
     (-1.335, 1.00), (-1.345, 0.96), (-1.33, 0.925), (-1.29, 0.912), (-1.00, 0.908), (-0.80, 0.901)]), 5)
DOOR_FRONT = [(0.70, D.DOOR_BOTTOM), (0.70, 0.668), (0.685, 0.715), (0.655, 0.755), (0.615, 0.79), (0.56, 0.83)]
DOOR_REAR = [(-0.555, D.DOOR_BOTTOM), (-0.565, 0.60), (-0.58, D.belt(-0.58))]
SASH = 0.018
# fuel lid on the left rear quarter (photo 64, back-projected through the fitted side camera): a rounded
# square, its own panel inside a pocket in the quarter, so it reads as a shut line
FUEL_LID = kit.fillet_poly(kit.rect(0.172, 0.160, -1.585, 0.750), 0.026, 6)


RUN_OUT, RUN_IN = 0.010, 0.008     # glass run band: past a pane's edge, under the pane


def _band(prism, poly, *args):
    """Band round a pane's outline (RUN_OUT out, RUN_IN in), as a prism mesh (side, top view)."""
    p = kit.ccw(poly)
    return B.bool_mesh(prism(kit.offset_poly(p, RUN_OUT), *args, shrink=0),
                       prism(kit.offset_poly(p, -RUN_IN), *args, shrink=0), 'DIFFERENCE')


def belt_line(f0, f1, n=24, lift=0.0):
    return [(f, D.belt(f) + lift) for f in samples(f0, f1, n)]


# door glass opening: the measured upper outline, closed along the sill molding (belt + SILL)
DWIN = [(0.56, D.belt(0.56) + SILL)] + DWIN_UPPER + belt_line(-0.49, 0.56, 20, SILL)[:-1]


# front bumper / fender seam (side view), from the bumper line at the lamp corner down and back to
# the arch, which it meets at about (1.524, 0.44): both panels take this one line, so they close
# with the usual shut line (a vertical bumper edge left a wedge above the arch that neither owned)
BUMPER_SEAM = [(D.BUMPER_SEAM_F, D.BUMPER_TOP_F), (1.30, -0.1)]


arch_cutter = parts.arch_cutter_mesh


class Skins:
    """The skins, split once along the fascias (see parts.py): `*_env` away from the
    fascia faces. Plus cropped solids for the nose, the lower front bumper and the tail
    (`nose*`, `bump*`, `rear*`)."""

    def __init__(self, coll):
        self.coll = coll
        self.temp = []
        # rear solids (the outer shape, and the shape 10 / 12 / 30 mm in) cropped to the tail, for the
        # rear bumper and hatch panel, which are carved from solids (B.cut_shell: the valance notch and
        # the plate recess go deeper than the skin)
        rbox = B.top_prism([(-1.0, -2.4), (1.0, -2.4), (1.0, -1.45), (-1.0, -1.45)], 0.0, 1.2, shrink=0)
        paint, in10 = B.make_skin('skin.paint', B.SKIN, 'paint', coll, keep_inner=True)
        self.paint = self.keep(paint)
        self.rear10 = self.crop(in10, 'rear.10', rbox, own=True)
        kit.cut(self.paint, *[arch_cutter(a, s) for a in (D.FA, D.RA) for s in (1, -1)])
        self.glass = self.keep(B.make_skin('skin.glass', B.GLASS, 'glass', coll, inner='glass'))
        self.trim = self.keep(B.make_skin('skin.trim', 0.008, 'trim', coll, inner='trim'))
        self.deep = self.keep(B.make_skin('skin.deep', 0.05, 'reflector', coll, inner='reflector'))
        # solid shape 12 mm in: parts.layer intersects with it to keep the 12-50 mm band of `deep`
        self.in12 = self.keep(B.shape_object(coll, 'shape.in12', 0.012))
        F_IN, R_IN = B.fascia_in(True, 0.008 + G), B.fascia_in(False, 0.008 + G)
        R_NEAR = B.fascia_in(False, 0.008)
        # (the front's fascia part is the nose, cut along the hood's front edge (parts.hood_front_prism);
        # the rear's is the hatch panel, carved from the solids: parts.hatch_panel)
        self.F_IN, self.R_IN, self.R_NEAR = F_IN, R_IN, R_NEAR
        self.paint_env = self.split(self.paint, 'env', [F_IN, R_IN])
        self.glass_env = self.split(self.glass, 'env', [F_IN, R_IN])
        # nose solids for the headlamps and the grille recess (parts.py), cropped to the front so
        # their booleans stay cheap: the outer shape, the shape 3 mm and 30 mm in, the 50 mm skin.
        # The `bump*` set is the same four, cropped to the lower bumper face (intake and corner vents).
        box = B.top_prism([(-1.0, 1.30), (1.0, 1.30), (1.0, 2.3), (-1.0, 2.3)], 0.35, 0.95, shrink=0)
        low = B.top_prism([(-0.80, 1.75), (0.80, 1.75), (0.80, 2.3), (-0.80, 2.3)], 0.18, 0.44, shrink=0)
        base, in3, in30 = B.base_shape(coll), B.shape_object(coll, 'shape.in3', 0.003), B.shape_object(coll, 'shape.in30', 0.030)
        self.rear0, self.rear12, self.rear30 = (self.crop(base, 'rear.0', rbox), self.crop(self.in12, 'rear.12', rbox),
                                                self.crop(in30, 'rear.30', rbox))
        # 6 mm in: just behind the 5 mm tail lenses (their housing lip) and inside the 10 mm skins (the
        # rear bumper seam backing), and 1 mm behind the glazing (the glass runs, cabin.glass_runs)
        self.in6 = self.keep(B.shape_object(coll, 'shape.in6', 0.006))
        self.rear6 = self.crop(self.in6, 'rear.6', rbox)
        self.rear_tree = parts.tri_tree(self.rear0.data)
        self.nose0, self.bump0 = self.crop(base, 'nose.0', box), self.crop(base, 'bump.0', low)
        self.nose3, self.bump3 = self.crop(in3, 'nose.3', box), self.crop(in3, 'bump.3', low, own=True)
        self.nose30, self.bump30 = self.crop(in30, 'nose.30', box), self.crop(in30, 'bump.30', low, own=True)
        self.nose_deep, self.bump_deep = self.crop(self.deep, 'nose.deep', box), self.crop(self.deep, 'bump.deep', low)
        self.nose_tree = parts.tri_tree(self.nose0.data)
        self.bump_tree = parts.tri_tree(self.bump0.data)

    def crop(self, o, name, box, own=False):
        c = self.keep(B.cut_region(o, name, [box], self.coll))
        if own:
            B.discard(o)
        return c

    def keep(self, o):
        # render-hidden only: a viewport-hidden object is not evaluated, so booleans on its copies do nothing
        o.hide_render = True
        self.temp.append(o)
        return o

    def split(self, skin, tag, cutters, pockets=()):
        return self.keep(B.cut_region(skin, skin.name + '.' + tag, cutters, self.coll, pockets))

    def release(self):
        for o in self.temp:
            B.discard(o)
        B.release_shape()


def build(coll):
    parts_ = {}
    K = Skins(coll)
    paint, glass, trim = K.paint, K.glass, K.trim

    def done(name, o, finish=0.0025, weld=2e-5):
        o.hide_render = False
        # flat undersides: the boolean fans them into slivers that streak under smooth shading
        for p in o.data.polygons:
            if p.normal.z < -0.95:
                p.use_smooth = False
        kit.clean(o, weld)
        kit.finish(o, finish, 2, 25.0)
        parts_[name] = o
        return o

    def panel(name, skin, cutters, pockets=(), finish=0.0025, transfer=False, weld=2e-5):
        return done(name, B.cut_region(skin, name, cutters, coll, pockets, transfer), finish, weld)

    # ------------------------------------------------------------ hood
    # the hood spans the car between the fender tops (D.HOOD_SEAM), and its front edge runs under the
    # grille and over the lamp tops (parts.hood_edge_xz): the grille slot and the lamp windows are its
    # pockets
    f0 = hood_rear_f(D.HOOD_REAR_X)
    hood_plan = [(x, hood_rear_f(x)) for x in samples(0.0, D.HOOD_REAR_X, 8)]
    hood_plan += [(hood_seam_x(f), f) for f in samples(f0, 2.3, 30)[1:]]
    hood_plan = hood_plan + [(0.0, 2.3)]
    full = [(-x, f) for x, f in reversed(hood_plan)] + hood_plan[1:]
    panel('hood', paint, [B.top_prism(full, 0.3, Z_HI), parts.hood_front_prism(0.3, 2.6)],
          pockets=[parts.lamp_pocket(s) for s in (1, -1)] + [parts.grille_pocket()], transfer=True)

    # ------------------------------------------------------------ cowl + windshield
    cowl_poly = [(x, ws_base_f(x)) for x in samples(-0.70, 0.70, 20)] + \
                [(x, hood_rear_f(min(abs(x), D.HOOD_REAR_X)) - 2 * G) for x in samples(0.70, -0.70, 20)]
    panel('cowl', trim, [B.top_prism(cowl_poly, 0.3, Z_HI, shrink=0)], finish=0.0015)

    ws_plan = [(x, ws_base_f(x) - G) for x in samples(-0.66, 0.66, 20)]
    ws_plan += [(glass_edge_x(f), f) for f in samples(D.A_BASE, D.WS_TOP + 0.02, 16)]
    ws_plan += [(x, header_f(x)) for x in samples(0.57, -0.57, 16)]
    ws_plan += [(-glass_edge_x(f), f) for f in samples(D.WS_TOP + 0.02, D.A_BASE, 16)]
    panel('windshield', K.glass_env, [B.top_prism(ws_plan, 0.6, Z_HI, shrink=G)], finish=0.0)

    # ------------------------------------------------------------ roof
    roof_plan = [(x, header_f(x) - 2 * G) for x in samples(-0.52, 0.52, 16)]
    roof_plan += [(glass_edge_x(f) - 0.004, f) for f in samples(D.WS_TOP - 0.03, D.ROOF_END, 20)]
    roof_plan += [(-glass_edge_x(f) + 0.004, f) for f in samples(D.ROOF_END, D.WS_TOP - 0.03, 20)]
    panel('roof', K.paint_env, [B.top_prism(roof_plan, 1.0, Z_HI)])

    # ------------------------------------------------------------ hatch glass + lower panel
    hg_plan = [(glass_edge_x(f), f) for f in samples(D.ROOF_END - 0.01, -2.3, 24)]
    hg_plan = hg_plan + [(-x, f) for x, f in reversed(hg_plan)]
    # the quarter and hatch glass are the dark-tinted panes (mats.GLASS_TINT)
    parts.recolor(panel('hatchGlass', K.glass_env, [B.top_prism(hg_plan, 0.8, Z_HI, shrink=G)], finish=0.0), 'glassDark')
    # hatch lower panel, the solid within 8 mm of the rear face: between the lamps from the bumper
    # up, and over the lamps up to the glass, inboard of the quarters (glass_edge_x - G).
    # Without the part over the lamps nothing owned the corners between the lamp tops and the glass,
    # which left a hole into the cabin above each lamp. Plate recess and crease: parts.hatch_panel
    T, lx, lo = parts.TAIL_LAMP_TOP, parts.tail_lamp_x, D.HATCH_PANEL_LOW
    hp_front = [(-lx(lo), lo), (lx(lo), lo), (lx(T), T), (0.80, T), (0.80, 1.2), (-0.80, 1.2), (-0.80, T), (-lx(T), T)]
    hp_plan = [(glass_edge_x(f) - G, f) for f in samples(-2.6, -1.5, 24)]
    hp_plan = hp_plan + [(-x, f) for x, f in reversed(hp_plan)]
    done('hatchPanel', parts.hatch_panel(coll, K, [B.front_prism(hp_front, -2.6, -1.80),
                                                   B.top_prism(hp_plan, 0.3, Z_HI, shrink=0)]))

    # glass runs: the pane outlines, as bands for glass_runs below (the hatch glass's lower edge is left
    # out: the tail housing's pillar strip lies there on the shape 12 mm in)
    runs = [_band(B.top_prism, ws_plan, 0.6, Z_HI), _band(B.top_prism, hg_plan, 0.97, Z_HI)]

    # ------------------------------------------------------------ sides
    for S, s in (('L', 1), ('R', -1)):
        sx = side_x(s)
        up = B.top_prism(mx([(glass_edge_x(f), f) for f in samples(D.TAIL - 0.3, D.NOSE + 0.3, 60)] +
                            [(BIG, D.NOSE + 0.3), (BIG, D.TAIL - 0.3)], s), -0.5, Z_HI, shrink=0)
        runs += [B.bool_mesh(_band(B.side_prism, w, *sx), up, 'INTERSECT') for w in (DWIN, QWIN)]

        # front fender: behind the lamp and grille, above the bumper line, outboard of the hood seam.
        # It shares BUMPER_SEAM with the bumper, so the two close with one shut line
        fender_top = mx([(hood_seam_x(f) + G, f) for f in samples(0.45, 2.3, 40)] + [(BIG, 2.3), (BIG, 0.45)], s)
        fender_side = DOOR_FRONT + [(0.745, 0.86), (0.745, Z_HI), (2.5, Z_HI), (2.5, D.BUMPER_TOP_F)] + \
            BUMPER_SEAM + [(1.0, -0.1), (1.0, D.DOOR_BOTTOM)]
        panel('fender.' + S, paint, [B.top_prism(fender_top, 0.2, Z_HI, shrink=0), B.side_prism(fender_side, *sx)],
              pockets=[parts.lamp_pocket(s)])

        # door skin (window sill up), with the handle's pocket (side.door_handles closes it behind)
        door_side = DOOR_FRONT + belt_line(0.56, -0.58, lift=0.004) + list(reversed(DOOR_REAR))
        panel('door.' + S, K.paint_env, [B.side_prism(door_side, *sx)],
              pockets=[B.side_prism(side.HANDLE_POCKET, *sx, shrink=0)])

        # glazing: door glass, quarter glass, sash, B-pillar garnish
        panel('winF.' + S, K.glass_env, [up, B.side_prism(DWIN, *sx)], finish=0.0)
        parts.recolor(panel('winR.' + S, K.glass_env, [up, B.side_prism(QWIN, *sx)], finish=0.0), 'glassDark')
        dwin_out = kit.offset_poly(kit.ccw(DWIN), SASH)
        below_sill = belt_line(-0.75, 0.75, 30, SILL) + [(0.75, -1.0), (-0.75, -1.0)]
        panel('sash.' + S, trim, [up, B.side_prism(dwin_out, *sx, shrink=G)],
              pockets=[B.side_prism(DWIN, *sx, shrink=-G), B.side_prism(below_sill, *sx, shrink=0)], finish=0.0015)
        # the molding's top edge meets the door glass's bottom edge (belt + SILL + G after the glass's
        # shrink): a slot there opened into the hollow body, and where the slots on both sides lined
        # up the camera saw the sky through the car (white dots along the belt)
        sill = belt_line(-0.49, 0.56, 20, 0.004) + belt_line(0.56, -0.49, 20, SILL + G + 0.0008)
        panel('sill.' + S, trim, [up, B.side_prism(sill, *sx, shrink=0.0008)], finish=0.001)
        # up to the roof panel's edge (about z 1.275), over the A-pillar / quarter shut line above it
        bpil = [(-0.49 - 0.012, 0.874), (-0.59 - 0.012, 1.275), (-0.665 + 0.002, 1.275), (-0.645 + 0.002, 0.889)]
        # gloss black garnish: it reads as one dark band with the glass (the textured trim turned a flat
        # mid-grey in the sun and broke the glasshouse). Welded at 0.1 mm: the cut leaves micron-tall
        # cap triangles along its bottom edge, across the skin's thickness. It runs on up to the roof
        # panel over the A-pillar / quarter shut line, but above the window tops it is body colour, so
        # the band of roof side over the glass reads unbroken from the A- to the D-pillar
        o = panel('bpillar.' + S, trim, [up, B.side_prism(bpil, *sx)], finish=0.0015, weld=1e-4)
        z_top = 1.268 - WIN_DROP + SASH * 0.5
        parts.slot_faces(o, lambda p, z_top=z_top: 'paint' if p.center.z > z_top else 'paintBlack')

        # A-pillar and roof rail ahead of the B-pillar
        ap_side = [(0.56, 0.83), (0.745, 0.86), (0.745, Z_HI), (-0.62, Z_HI), (-0.62, 0.87)] + belt_line(-0.60, 0.56, lift=0.004)
        panel('apillar.' + S, K.paint_env, [up, B.side_prism(ap_side, *sx)],
              pockets=[B.side_prism(dwin_out, *sx, shrink=-G), B.side_prism(bpil, *sx, shrink=-G)])

        # quarter: behind the door up to the roof and hatch-glass edges, down to the rear bumper's
        # horizontal seam (which steps up under the lamp's front corner). It keeps the D-pillar's rear
        # end above the tail lamp; the lamp is its pocket, so the two share the lamp's rounded outline
        q_side = list(DOOR_REAR) + [(-0.62, 0.87), (-0.62, Z_HI), (-2.6, Z_HI), (-2.6, D.TAIL_LAMP_LOW),
                                    (D.BUMPER_STEP_F, D.TAIL_LAMP_LOW), (D.BUMPER_STEP_F, D.BUMPER_TOP_R),
                                    (D.BUMPER_SEAM_R, D.BUMPER_TOP_R), (D.BUMPER_SEAM_R, D.DOOR_BOTTOM)]
        # outboard of the hatch panel only near the tail: further forward the glass edge runs inboard
        # of TAIL_LAMP_X, and a full-length limit left a 3 cm slot along the roof rail / D-pillar top
        # (the lamp's inner edge leans out to lx(T) at the top; below T the lamp pocket covers the rest)
        q_plan = mx([(lx(T) + G, -2.6), (BIG, -2.6), (BIG, 0.0), (0.30, 0.0), (0.30, -1.62),
                     (lx(T) + G, -1.72)], s)
        lid = [B.side_prism(FUEL_LID, *sx, shrink=-G)] if s > 0 else []
        panel('quarter.' + S, paint, [up, B.side_prism(q_side, *sx), B.top_prism(q_plan, -0.5, Z_HI, shrink=0)],
              pockets=[B.side_prism(QWIN, *sx, shrink=-G), B.side_prism(bpil, *sx, shrink=-G),
                       parts.tail_lamp_cutter(s, shrink=-G)] + lid)
        if s > 0:
            panel('fuelLid', paint, [B.side_prism(FUEL_LID, *sx)])

        # side skirt under the doors, arch to arch. From the whole skin: near the rear bumper seam the
        # fascia split (paint_env) had taken the outer skin, leaving the inner face showing behind the arch
        skirt = [(D.BUMPER_SEAM_R, -0.2), (1.0, -0.2), (1.0, D.DOOR_BOTTOM), (D.BUMPER_SEAM_R, D.DOOR_BOTTOM)]
        panel('skirt.' + S, paint, [B.side_prism(skirt, *((0.66, BIG) if s > 0 else (-BIG, -0.66)))])

    # glass runs: a black band from 6 to 12 mm in (1 mm behind the 5 mm glass) along every pane's edge.
    # The glass is see-through, and its shut lines to the sash, pillars and roof opened into the cabin:
    # through the near glass the far side's slots showed as light lines. Seen through the glass, the
    # band reads as the black edge (frit, channel) real glazing has
    band = runs[0]
    for m in runs[1:]:
        band = B.bool_mesh(band, m, 'UNION')
    o = B.cut_region(K.in6, 'glassRun', [band], coll)
    kit.boolean(o, parts.dup(K.in12, coll), 'DIFFERENCE')
    parts.recolor(o, 'trim')
    done('glassRun', o, finish=0.0)

    # ------------------------------------------------------------ bumpers
    # the front bumper runs to the body bottom in paint; the black splitter is a separate part
    # (parts.front_lip). Its rear edge is the fender's seam line, so it forms the front of the arch
    bf = [(1.30, -1.0), (2.6, -1.0), (2.6, D.BUMPER_TOP_F)] + BUMPER_SEAM
    # the intake's cut edge stays dark (the black band along its top in the photo); the corner vents'
    # cut edges are paint, the first centimetre of the scoops' body-colour walls
    vents = []
    for s in (1, -1):
        c = kit.cutter_obj(parts.corner_vent(s, K)[0])
        parts.recolor(c, 'paint')
        vents.append(c)
    panel('bumperF', paint, [B.side_prism(bf, -BIG, BIG)], transfer=True,
          pockets=[B.front_prism(parts.INTAKE_XZ, 1.80, 2.6, shrink=0)] + vents)
    parts.front_bumper_details(coll, parts_, K)
    parts.seam_backing(coll, parts_, K, BUMPER_SEAM)

    # rear bumper: wraps forward to the rear arch under one horizontal seam (its front end hides in the
    # arch opening), steps up to the lamp bottom under the lamp's front corner, and between the lamps
    # comes up to the hatch panel. Carved from the solids so the valance notch keeps a closed ceiling
    br = [(-2.6, -1.0), (D.BUMPER_SEAM_R, -1.0), (D.BUMPER_SEAM_R, D.BUMPER_TOP_R), (D.BUMPER_STEP_F, D.BUMPER_TOP_R),
          (D.BUMPER_STEP_F, D.TAIL_LAMP_LOW), (-2.6, D.TAIL_LAMP_LOW)]
    hp_notch = B.front_prism([(-lx(lo), lo), (lx(lo), lo), (lx(1.0), 1.0), (-lx(1.0), 1.0)], -2.6, -1.80, shrink=-G)
    o = B.cut_shell(K.rear0, K.rear10, 'bumperR', coll, [B.side_prism(br, -BIG, BIG)],
                    [arch_cutter(D.RA, s) for s in (1, -1)] + [parts.valance_notch(), hp_notch],
                    [parts.valance_notch(B.SKIN)])
    parts.valance_wall(o)
    done('bumperR', o)
    parts.rear_bumper_details(coll, parts_, K)
    parts.rear_seam_backing(coll, parts_, K)

    # ------------------------------------------------------------ lamps, grille, trim, wheels
    parts.build(coll, parts_, K)
    wheels.build(coll, parts_)
    K.release()
    # the see-through glass is alpha-blended, which EEVEE sorts per object by origin: give each pane its
    # own (every panel is cut in place, so all origins sat at the car's centre and the far windows
    # could draw over the near ones). Last, as the wipers ray-cast the windshield in mesh space.
    for name, o in parts_.items():
        if name == 'windshield' or name == 'hatchGlass' or name.startswith(('winF.', 'winR.')):
            kit.recentre(o)
    return parts_
