"""Preview materials. Slot names are the contract with the game: every slot will
map to a TSL node material of the same key in src/content/civic-ek9/materials.ts."""
import bpy

# slot: (base color sRGB hex, metallic, roughness, emission hex or None, emission strength, clearcoat, transmission)
SLOTS = {
    'paint': (0xf7c200, 0.0, 0.30, None, 0, 1.0, 0.0),        # yellow (#111040's respray, hue 46 in the studio shots), solid under clearcoat
    'paintBlack': (0x0c0d0f, 0.0, 0.28, None, 0, 1.0, 0.0),   # gloss black accents, B-pillar garnish
    'trim': (0x141516, 0.0, 0.62, None, 0, 0.0, 0.0),         # black textured plastic: seals, cowl, sashes, grille frame
    'satin': (0x1b1c1e, 0.2, 0.38, None, 0, 0.3, 0.0),        # satin black: spoiler blade edge, mirror base
    'mesh': (0xb8bcc2, 0.8, 0.30, None, 0, 0.0, 0.0),         # the intake's one bright bar
    'meshDark': (0x2a2c30, 0.3, 0.50, None, 0, 0.0, 0.0),     # intake / grille lattice: dark satin, reads as texture
    'grilleDark': (0x0a0a0b, 0.0, 0.80, None, 0, 0.0, 0.0),   # upper grille floor: black mesh over the dark bay (see build)
    'glass': (0x000000, 0.0, 0.0, None, 0, 0.0, 0.0),         # glazing: full Fresnel reflection over a tinted see-through (GLASS_TINT)
    'glassDark': (0x000000, 0.0, 0.0, None, 0, 0.0, 0.0),     # quarter and hatch glass: the same, darker tint
    'lens': (0x000000, 0.0, 0.02, None, 0, 0.0, 0.0),         # clear headlight lens: Fresnel reflection over a transparent BSDF (see build)
    'lensRed': (0xb8121a, 0.0, 0.04, None, 0, 0.0, 0.0),      # tail lamp lenses: tinted, part see-through (LENS_ALPHA)
    'lensClear': (0xf4f4f4, 0.0, 0.02, None, 0, 0.0, 0.0),    # turn / reverse band: the chrome reflector shows through
    'marker': (0xf07814, 0.35, 0.14, None, 0, 1.0, 0.0),      # amber side marker over its reflector
    'reflector': (0xeef0f2, 1.0, 0.18, None, 0, 0.0, 0.0),    # aluminised housing with shallow optical flutes
    'lampCup': (0xf2f3f5, 1.0, 0.14, None, 0, 0.0, 0.0),      # headlamp reflector bowls: smooth bright chrome
    'tailReflector': (0xe6e8eb, 1.0, 0.20, None, 0, 0.0, 0.0),  # tail lamp reflector: fluted chrome
    'lightWhite': (0xf4f7ff, 0.0, 0.3, 0xf4f7ff, 0.0, 0.0, 0.0),   # headlight bulb (off in daylight)
    'lightRed': (0xff1a12, 0.0, 0.3, 0xff1a12, 6.0, 0.0, 0.0),
    'rubber': (0x151515, 0.0, 0.88, None, 0, 0.0, 0.0),
    'rim': (0xeeeeea, 0.0, 0.32, None, 0, 1.0, 0.0),          # white five-spoke Volks (white paint under clear)
    'rimLip': (0xeeeeea, 0.0, 0.32, None, 0, 1.0, 0.0),       # the wheel's outer lip ring, painted with the face
    'decalBlue': (0x1d3fc8, 0.0, 0.35, None, 0, 1.0, 0.0),    # the spokes' VOLK / RAYS decals, the valve cap
    'rotor': (0x44464a, 1.0, 0.55, None, 0, 0.0, 0.0),        # cast iron: a bright disc filled the spoke gaps
    'caliper': (0xa3161c, 0.0, 0.45, None, 0, 0.3, 0.0),      # red painted calipers
    'steel': (0xb4b7ba, 1.0, 0.26, None, 0, 0.0, 0.0),        # exhaust tip, fasteners
    'mirror': (0xd8dde2, 1.0, 0.04, None, 0, 0.0, 0.0),
    'interior': (0x0c0c0d, 0.0, 0.88, None, 0, 0.0, 0.0),     # liners, inner faces, hidden structure
    # cabin (photos 77-88): the Type R's red Recaros and carpet, grey rear seat, black dash and trim
    'seatRed': (0xb0121b, 0.0, 0.86, None, 0, 0.0, 0.0),      # Recaro fabric (FABRIC: sheen)
    'seatInsert': (0x7e0c14, 0.0, 0.92, None, 0, 0.0, 0.0),   # the buckets' woven centre panels, darker than the suede
    'seatBack': (0x151516, 0.0, 0.70, None, 0, 0.0, 0.0),     # the buckets' black back shells
    'seatLogo': (0x4a070c, 0.0, 0.80, None, 0, 0.0, 0.0),     # stitched RECARO
    'carpetRed': (0x6e0b12, 0.0, 0.95, None, 0, 0.0, 0.0),    # red carpet
    'fabricGrey': (0x2f3236, 0.0, 0.92, None, 0, 0.0, 0.0),   # rear seat fabric
    'dash': (0x1e2023, 0.0, 0.62, None, 0, 0.0, 0.0),         # dash, console, door cards: grained black plastic
    'leather': (0x111111, 0.0, 0.42, None, 0, 0.3, 0.0),      # steering wheel rim, shift boot
    'headliner': (0x8c8a84, 0.0, 0.93, None, 0, 0.0, 0.0),    # roof lining
    'belt': (0x55585d, 0.0, 0.80, None, 0, 0.0, 0.0),         # seatbelt webbing
    'gaugeFace': (0x0c0c0e, 0.0, 0.35, None, 0, 0.3, 0.0),    # black dial faces (photo 84)
    'gaugeTick': (0xf0f0ec, 0.0, 0.40, None, 0, 0.0, 0.0),    # the dials' white ticks
    'needle': (0xffa01a, 0.0, 0.40, 0xffa01a, 0.6, 0.0, 0.0), # yellow-orange needles
    'screen': (0x223238, 0.3, 0.18, 0x5a8c9a, 0.15, 1.0, 0.0),  # head unit display
    'badge': (0xd8dadc, 1.0, 0.18, None, 0, 0.0, 0.0),
    'badgeRed': (0xd0101c, 0.0, 0.25, None, 0, 1.0, 0.0),     # Type R emblem plate
    'graphite': (0x26292d, 0.8, 0.40, None, 0, 0.0, 0.0),     # robot structural castings
    'darkSteel': (0x5a5f65, 1.0, 0.30, None, 0, 0.0, 0.0),    # machined joints
    'chrome': (0xe0e3e6, 1.0, 0.08, None, 0, 0.0, 0.0),       # hydraulic rods
    'mech': (0x3a3e44, 0.9, 0.42, None, 0, 0.0, 0.0),         # secondary mechanism parts
    'eye': (0x1f6fff, 0.0, 0.25, 0x1f6fff, 2.2, 0.0, 0.0),
}


# tinted lenses: this share is the lens's own coloured plastic, the rest passes what is behind (the
# chrome reflector) through a filter of the lens colour, so red reads deep and the reflector glints red
LENS_ALPHA = {'lensRed': 0.78, 'lensClear': 0.15}
# fabrics: a sheen lobe over the diffuse base, so the pile catches grazing light
FABRIC = {'seatRed': 0.7, 'seatInsert': 0.45, 'seatLogo': 0.4, 'carpetRed': 0.6, 'fabricGrey': 0.6, 'headliner': 0.5, 'belt': 0.3}
# glazing (alpha-blended, back faces culled, so a pane is one surface however thick). The panes are a
# black-based dielectric (only its Fresnel reflection of the sky) added to a transparent BSDF tinted
# GLASS_TINT, which shows the cabin and the far windows. An alpha-blended dark glass scaled the sky's
# reflection down with its opacity: the side glass read as near-black holes, where the reference
# photo's side glass is the brightest part of the upper car. The quarter and hatch glass are tinted
# dark (the photos show the seats through the door glass, and only reflections in the quarter)
GLASS_TINT = {'glass': (0.40, 0.44, 0.42), 'glassDark': (0.11, 0.12, 0.12)}
# structured reflector facets: (band pitch in m, normal tilt, axis). Bands along z tilted about the
# horizontal: the headlamp housing's multi-reflector strips, the tail reflector's flutes. Random
# Voronoi cells read as crushed glass / confetti in the headlamp and as grit in the reverse band
REFLECTOR_BANDS = {'reflector': (0.009, 0.035), 'tailReflector': (0.006, 0.15)}


def srgb(h):
    def ch(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (ch((h >> 16) & 255), ch((h >> 8) & 255), ch(h & 255), 1.0)


def get(slot):
    if slot not in SLOTS:
        raise KeyError('unknown material slot ' + slot)
    name = 'ek.' + slot
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        build(m, slot)
    return m


def build(m, slot):
    col, metal, rough, emit, strength, coat, trans = SLOTS[slot]
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = srgb(col)
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Coat Weight'].default_value = coat
    bsdf.inputs['Coat Roughness'].default_value = 0.03
    bsdf.inputs['Transmission Weight'].default_value = trans
    m.diffuse_color = srgb(col)
    if slot in ('rim', 'rimLip', 'marker', 'decalBlue'):
        bsdf.inputs['Coat Roughness'].default_value = 0.03
    if slot in ('paint', 'paintBlack'):
        # pigment under a full clear coat: a weak base interface, so the coat alone gives the
        # sharp highlight and the base keeps its saturated colour
        bsdf.inputs['Specular IOR Level'].default_value = 0.25
        bsdf.inputs['Coat Roughness'].default_value = 0.02
        bsdf.inputs['Coat IOR'].default_value = 1.5
    if slot == 'grilleDark':
        # optical proxy for a mesh over the dark engine bay: the open area reflects nothing, so the
        # floor keeps about 40 % of solid plastic's specular (a plain plastic floor caught the low
        # sun's sheen and read mid-grey from the front three-quarter view)
        bsdf.inputs['Specular IOR Level'].default_value = 0.2
    if emit is not None:
        bsdf.inputs['Emission Color'].default_value = srgb(emit)
        bsdf.inputs['Emission Strength'].default_value = strength
    if trans > 0:
        if hasattr(m, 'thickness_mode'):
            m.thickness_mode = 'SLAB'        # thin lens: no refraction swim through the reflector
    if slot == 'lens':
        # thin clear lens, no refraction: the black-based BSDF gives only its Fresnel reflection, a
        # transparent BSDF passes what is behind (EEVEE's screen-space refraction fell back to the sky)
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        add = nt.nodes.new('ShaderNodeAddShader')
        out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        nt.links.new(bsdf.outputs['BSDF'], add.inputs[0])
        nt.links.new(tr.outputs['BSDF'], add.inputs[1])
        nt.links.new(add.outputs['Shader'], out.inputs['Surface'])
    if slot in LENS_ALPHA:
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        tr.inputs['Color'].default_value = srgb(col)
        mix = nt.nodes.new('ShaderNodeMixShader')
        mix.inputs['Fac'].default_value = LENS_ALPHA[slot]
        out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        nt.links.new(tr.outputs['BSDF'], mix.inputs[1])
        nt.links.new(bsdf.outputs['BSDF'], mix.inputs[2])
        nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    if slot in GLASS_TINT:
        # a single dielectric lobe (a clear coat on top stacked a second one, and the raked windshield
        # went white at grazing angles)
        bsdf.inputs['IOR'].default_value = 1.52
        m.surface_render_method = 'BLENDED'
        m.use_backface_culling = True
    if slot in GLASS_TINT:
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        tr.inputs['Color'].default_value = GLASS_TINT[slot] + (1.0,)
        add = nt.nodes.new('ShaderNodeAddShader')
        out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        nt.links.new(bsdf.outputs['BSDF'], add.inputs[0])
        nt.links.new(tr.outputs['BSDF'], add.inputs[1])
        nt.links.new(add.outputs['Shader'], out.inputs['Surface'])
        if hasattr(m, 'use_transparent_shadow'):
            m.use_transparent_shadow = True
    if slot.startswith('lens'):
        m.surface_render_method = 'BLENDED'
        if hasattr(m, 'use_transparent_shadow'):
            m.use_transparent_shadow = True
    if slot in REFLECTOR_BANDS:
        # horizontal facet bands (object z): each band tilts the normal up or down by its own fixed
        # amount, so the housing reads as a stack of flat reflector strips, each mirroring a different
        # height of the sky. Pure world normal + tilt * (0, 0, k - 0.5), k per band from white noise
        pitch, t = REFLECTOR_BANDS[slot]
        tc = nt.nodes.new('ShaderNodeTexCoord')
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        sep = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(tc.outputs['Object'], sep.inputs['Vector'])
        div = nt.nodes.new('ShaderNodeMath')
        div.operation = 'DIVIDE'
        div.inputs[1].default_value = pitch
        nt.links.new(sep.outputs['Z'], div.inputs[0])
        flo = nt.nodes.new('ShaderNodeMath')
        flo.operation = 'FLOOR'
        nt.links.new(div.outputs['Value'], flo.inputs[0])
        wn = nt.nodes.new('ShaderNodeTexWhiteNoise')
        wn.noise_dimensions = '1D'
        nt.links.new(flo.outputs['Value'], wn.inputs['W'])
        k = nt.nodes.new('ShaderNodeMath')
        k.operation = 'MULTIPLY_ADD'
        k.inputs[1].default_value = 2.0 * t
        k.inputs[2].default_value = -t
        nt.links.new(wn.outputs['Value'], k.inputs[0])
        comb = nt.nodes.new('ShaderNodeCombineXYZ')
        nt.links.new(k.outputs['Value'], comb.inputs['Z'])
        add = nt.nodes.new('ShaderNodeVectorMath')
        add.operation = 'ADD'
        nt.links.new(geo.outputs['Normal'], add.inputs[0])
        nt.links.new(comb.outputs['Vector'], add.inputs[1])
        nrm = nt.nodes.new('ShaderNodeVectorMath')
        nrm.operation = 'NORMALIZE'
        nt.links.new(add.outputs['Vector'], nrm.inputs[0])
        nt.links.new(nrm.outputs['Vector'], bsdf.inputs['Normal'])
    if slot in FABRIC:
        bsdf.inputs['Sheen Weight'].default_value = FABRIC[slot]
        bsdf.inputs['Sheen Roughness'].default_value = 0.35
        bsdf.inputs['Specular IOR Level'].default_value = 0.2
    if slot in ('trim', 'grilleDark', 'dash'):
        # moulded grain: fine noise on roughness, about the slot's own roughness
        tc = nt.nodes.new('ShaderNodeTexCoord')
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = 900.0
        mr = nt.nodes.new('ShaderNodeMapRange')
        mr.inputs['To Min'].default_value = rough - 0.10
        mr.inputs['To Max'].default_value = rough + 0.10
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
        nt.links.new(mr.outputs['Result'], bsdf.inputs['Roughness'])


def ensure_all():
    for s in SLOTS:
        get(s)
