"""Lookdev stage and review renders: the car on a rural asphalt road under a sunny sky.

The world is Poly Haven's 'rural_asphalt_road' HDRI (CC0; `refs/hdri`, gitignored). Measured from the
2k file with the disc clamped at HDRI_CLAMP: the sun sits at elevation 45.4 deg, 36.1 deg off the
image-centre road, and carries HDRI_SUN_E of irradiance at normal incidence; the clamped sky gives
HDRI_SKY_E on a horizontal plane (about 4 : 1 sun to sky).

- Mapping: the image-centre road runs ahead of the nose along the car's axis, and the HDRI's sun lands
  36.1 deg off the nose on the key side (key_side): left for the review cameras, right for the camera
  fitted to the reference photo, which shows the car's right side.
- The world is clamped, so the disc leaves the world probe, and ek.sun carries exactly that energy with
  crisp shadows, lower than the capture's sun (SUN_EL 28): the low sun lights the flanks the hero
  cameras see, as in the photo. EEVEE's own sun extraction is off.
- White balance (HDRI_WB) scales the light, world and sun, so lit asphalt reads a near-neutral grey, as
  in the photo: the capture is warm (road radiance 1.19 : 1 : 0.79).
- Ground: the HDRI projected from its capture height onto the plane, divided per channel by the
  capture's own sun + sky irradiance: that is the road's albedo (about 0.09), which the stage's lights
  re-light, the car's shadow included.

Without the HDRI file the stage falls back to a Nishita sky over plain asphalt. Khronos PBR Neutral is
the operator behind THREE.NeutralToneMapping, so review renders keep the game's saturation."""
import math
import os
import bpy
from mathutils import Vector, Quaternion

RENDER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'renders', 'civic-ek9'))
HDRI_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'refs', 'hdri',
                                         'rural_asphalt_road_2k.hdr'))

SUN_AZ, SUN_EL = 36.1, 28.0          # degrees off the nose / above the horizon; the HDRI's sun azimuth
HDRI_SUN_EL = 45.4                   # the capture's own sun, for the road albedo
HDRI_SUN_E = (7.468, 6.000, 5.141)   # disc irradiance at normal incidence (strength 1)
HDRI_SKY_E = (0.966, 1.136, 1.496)   # clamped sky on a horizontal plane
HDRI_CLAMP = 8.0
HDRI_CAPTURE_H = 1.6                 # capture height (the road reads about 3.8 h wide)
HDRI_WB = (0.871, 1.0, 1.185)
GROUND_HALF = 500.0
SKY_STRENGTH = 0.06                  # fallback sky, against a 5.0 sun
KEY = {'side': 'left'}


def _principled(m):
    m.use_nodes = True
    return next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def _asphalt():
    """Fallback ground: plain dark asphalt with a little roughness grain."""
    m = bpy.data.materials.get('ek.asphalt') or bpy.data.materials.new('ek.asphalt')
    b = _principled(m)
    nt = m.node_tree
    for n in [n for n in nt.nodes if n.type in ('TEX_COORD', 'TEX_NOISE', 'MAP_RANGE')]:
        nt.nodes.remove(n)
    b.inputs['Base Color'].default_value = (0.085, 0.085, 0.09, 1)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 40.0
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['To Min'].default_value = 0.75
    mr.inputs['To Max'].default_value = 0.95
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    return m


def _vmath(nt, op, a, b):
    n = nt.nodes.new('ShaderNodeVectorMath')
    n.operation = op
    nt.links.new(a, n.inputs[0])
    n.inputs[1].default_value = b
    return n.outputs['Vector']


def _env(nt, img, vec_socket):
    """Environment texture looked up through the stage mapping (a node named 'ek.map')."""
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.name = 'ek.map'
    mp.vector_type = 'POINT'
    nt.links.new(vec_socket, mp.inputs['Vector'])
    et = nt.nodes.new('ShaderNodeTexEnvironment')
    et.image = img
    et.interpolation = 'Linear'
    nt.links.new(mp.outputs['Vector'], et.inputs['Vector'])
    return et


def _hdri_image():
    if not os.path.isfile(HDRI_FILE):
        return None
    img = bpy.data.images.get('ek.hdri')
    if img is None:
        img = bpy.data.images.load(HDRI_FILE, check_existing=True)
        img.name = 'ek.hdri'
    return img


def _world_hdri(nt, img):
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    et = _env(nt, img, tc.outputs['Generated'])
    c = _vmath(nt, 'MINIMUM', et.outputs['Color'], (HDRI_CLAMP,) * 3)
    nt.links.new(_vmath(nt, 'MULTIPLY', c, HDRI_WB), bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 1.0
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])


def _world_sky(nt):
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.name = 'ek.sky'
    try:
        sky.sky_type = 'MULTIPLE_SCATTERING'
    except TypeError:
        pass
    if hasattr(sky, 'sun_elevation'):
        sky.sun_elevation = math.radians(SUN_EL)
    bg.inputs['Strength'].default_value = SKY_STRENGTH
    nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])


def _road(img):
    s = math.sin(math.radians(HDRI_SUN_EL))
    k = tuple(math.pi / (e * s + k_) for e, k_ in zip(HDRI_SUN_E, HDRI_SKY_E))
    m = bpy.data.materials.get('ek.road') or bpy.data.materials.new('ek.road')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    d = _vmath(nt, 'SUBTRACT', geo.outputs['Position'], (0.0, 0.0, HDRI_CAPTURE_H))
    et = _env(nt, img, d)
    nt.links.new(_vmath(nt, 'MULTIPLY', et.outputs['Color'], k), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.9
    b.inputs['Specular IOR Level'].default_value = 0.2   # the photo already holds the road's sheen
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    return m


def key_side(side='left'):
    """Put the sun (and the HDRI's sun with it) 36.1 deg off the nose on the car's `side`. The image
    road stays ahead of the nose either way: mirror y then rotate z -90 deg (left), or rotate z +90
    deg (right)."""
    KEY['side'] = side
    sgn = 1.0 if side == 'left' else -1.0
    sun = bpy.data.objects.get('ek.sun')
    if sun is not None:
        sun.rotation_euler = (math.radians(90.0 - SUN_EL), 0, sgn * math.radians(SUN_AZ))
    trees = [bpy.context.scene.world.node_tree] if bpy.context.scene.world else []
    road = bpy.data.materials.get('ek.road')
    if road is not None and road.node_tree:
        trees.append(road.node_tree)
    for nt in trees:
        mp = nt.nodes.get('ek.map')
        if mp is not None:
            mp.inputs['Rotation'].default_value = (0.0, 0.0, -sgn * math.radians(90.0))
            mp.inputs['Scale'].default_value = (1.0, -sgn, 1.0)
        sky = nt.nodes.get('ek.sky')
        if sky is not None and hasattr(sky, 'sun_rotation'):
            # the sky's sun sits at atan2(y, x) = 90 deg - rotation; the lamp's to-sun azimuth is its
            # z rotation - 90 deg
            sky.sun_rotation = math.radians(180.0 - sgn * SUN_AZ)


def setup_stage():
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.fps = 30
    sc.view_settings.view_transform = 'Khronos PBR Neutral'
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = 0.0
    ee = sc.eevee
    for attr, val in (('use_shadows', True), ('use_raytracing', True), ('shadow_ray_count', 2)):
        if hasattr(ee, attr):
            setattr(ee, attr, val)
    rto = getattr(ee, 'ray_tracing_options', None)
    if rto is not None:
        rto.resolution_scale = '1'           # full-resolution screen tracing: crisp paint reflections
        rto.screen_trace_quality = 0.75

    img = _hdri_image()
    world = bpy.data.worlds.get('ek.world') or bpy.data.worlds.new('ek.world')
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes.clear()
    if img is not None:
        _world_hdri(world.node_tree, img)
        if hasattr(world, 'sun_threshold'):
            world.sun_threshold = 1.0e4      # the clamp removed the disc; no second, extracted sun
    else:
        _world_sky(world.node_tree)

    coll = bpy.data.collections.get('STAGE')
    if coll is None:
        coll = bpy.data.collections.new('STAGE')
        sc.collection.children.link(coll)
    sun = bpy.data.objects.get('ek.sun')
    if sun is None:
        ld = bpy.data.lights.new('ek.sun', 'SUN')
        sun = bpy.data.objects.new('ek.sun', ld)
        coll.objects.link(sun)
    if img is not None:
        e = [x * w for x, w in zip(HDRI_SUN_E, HDRI_WB)]
        sun.data.energy = max(e)
        sun.data.color = tuple(x / max(e) for x in e)
        sun.data.angle = math.radians(0.53)
    else:
        sun.data.energy = 5.0
        sun.data.color = (1.0, 0.92, 0.80)
        sun.data.angle = math.radians(1.2)

    # retired stage pieces (a reopened blend may still hold them): the fill sat behind every hero
    # camera; the tree-line cylinder and its probe stood in for a horizon the HDRI now provides
    for name in ('ek.fill', 'ek.surround', 'ek.probe'):
        o = bpy.data.objects.get(name)
        if o is not None:
            bpy.data.objects.remove(o, do_unlink=True)

    ground = bpy.data.objects.get('ek.ground')
    if ground is None:
        me = bpy.data.meshes.new('ek.ground')
        me.from_pydata([(0, 0, 0)] * 4, [], [(0, 1, 2, 3)])
        ground = bpy.data.objects.new('ek.ground', me)
        coll.objects.link(ground)
    s = GROUND_HALF
    for v, co in zip(ground.data.vertices, ((-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0))):
        v.co = co
    # material set every run, so a reopened blend never keeps an old ground
    ground.data.materials.clear()
    ground.data.materials.append(_road(img) if img is not None else _asphalt())
    key_side('left')
    return sc


def camera(name='ek.cam'):
    cam = bpy.data.objects.get(name)
    if cam is None:
        cd = bpy.data.cameras.new(name)
        cam = bpy.data.objects.new(name, cd)
        bpy.data.collections['STAGE'].objects.link(cam)
    return cam


def look_at(cam, eye, target, lens=50, roll=0.0):
    cam.location = Vector(eye)
    d = Vector(target) - Vector(eye)
    q = d.to_track_quat('-Z', 'Y')
    if roll:
        q = q @ Quaternion((0.0, 0.0, 1.0), -roll)
    cam.rotation_euler = q.to_euler()
    cam.data.type = 'PERSP'
    cam.data.sensor_fit = 'AUTO'
    cam.data.sensor_width = 36.0
    cam.data.lens = lens
    cam.data.clip_start = 0.05
    cam.data.clip_end = 1200


def render(name, eye, target, lens=50, res=(1280, 720), frame=None, hide=(), roll=0.0):
    sc = bpy.context.scene
    cam = camera()
    look_at(cam, eye, target, lens, roll)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    if frame is not None:
        sc.frame_set(frame)
    hidden = []
    for n in hide:
        c = bpy.data.collections.get(n)
        if c and not c.hide_render:
            c.hide_render = True
            hidden.append(c)
    os.makedirs(RENDER_DIR, exist_ok=True)
    path = os.path.join(RENDER_DIR, name + '.png')
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for c in hidden:
        c.hide_render = False
    return path


CAR_VIEWS = {
    '3q': ((5.6, -6.2, 2.6), (0, 0.15, 0.35), 38),
    'side': ((9.2, 0.25, 0.55), (0, 0.25, 0.42), 38),
    'front': ((0.0, -9.0, 1.2), (0, 0.0, 0.40), 34),
    'rear3q': ((-5.0, 6.8, 2.6), (0, -0.5, 0.40), 38),
    'top': ((0.0, 0.25, 11.5), (0, 0.25, 0.0), 38),
    'low': ((3.4, -4.2, 0.35), (0, 0.4, 0.35), 34),
}


def car_views(tag, views=None, res=(1400, 800)):
    out = []
    for k in (views or CAR_VIEWS):
        eye, target, lens = CAR_VIEWS[k]
        out.append(render('%s_%s' % (tag, k), eye, target, lens, res=res))
    return out
