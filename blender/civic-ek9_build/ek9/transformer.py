"""EK9 Sentinel: rigid-panel conversion and articulated mechanical character.

Input is the finished reference car. Exterior pieces retain unit scale throughout.
Coordinates in authoring helpers are (x, forward, z), with forward = Blender -Y.
"""
import math
import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector, Euler
from . import kit, rkit, mats
from .kit import V
from .rkit import Part

CONTROLS = {}
ASSIGNED = set()
COLL = None
RIG = None


def matrix(p, angles=(0, 0, 0)):
    return Matrix.Translation(V(*p)) @ Euler(tuple(math.radians(a) for a in angles), 'XYZ').to_matrix().to_4x4()


def control(name, start, finish, angles=(0, 0, 0), folded=(0, 0, 0), timing=(35, 155), parent=None, via=None, carry=False):
    o = bpy.data.objects.new('CTRL.' + name, None)
    RIG.objects.link(o)
    o.empty_display_type = 'ARROWS'
    o.empty_display_size = .12
    o.rotation_mode = 'QUATERNION'
    if parent:
        o.parent = CONTROLS[parent]['object']
    o['purpose'] = name.replace('.', ' ')
    CONTROLS[name] = dict(object=o, start=matrix(start, folded), finish=matrix(finish, angles), timing=timing, via=via, carry=carry)
    o.matrix_world = matrix(finish, angles)
    bpy.context.view_layer.update()
    return o


def mount(o, name, source=None):
    c = CONTROLS[name]
    w = o.matrix_world.copy()
    o.parent = c['object']
    o.matrix_parent_inverse = Matrix.Identity(4)
    o.matrix_basis = (source or c['finish']).inverted() @ w
    ASSIGNED.add(o.name)
    o['conversion_group'] = name


def panel_group(name, names, pivot, destination, angles=(0, 0, 0), timing=(35, 155), parent=None, via=None):
    control(name, pivot, destination, angles, timing=timing, parent=parent, via=via)
    for n in names:
        o = bpy.data.objects.get(n)
        if o:
            mount(o, name, matrix(pivot))


def split(name, axis, plane, suffixes):
    """Bisect the actual mesh in world coordinates; no proxy/replacement panels."""
    original = bpy.data.objects[name]
    world = original.matrix_world.copy()
    out = []
    for side, suffix in enumerate(suffixes):
        o = original.copy()
        o.data = original.data.copy()
        o.name = suffix
        for c in original.users_collection:
            c.objects.link(o)
        o.parent = None
        o.matrix_world = Matrix.Identity(4)
        o.data.transform(world)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        normal = Vector((0, 0, 0)); normal[axis] = 1
        point = normal * plane
        bmesh.ops.bisect_plane(bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces), dist=.000001,
                              plane_co=point, plane_no=normal, clear_inner=side == 1, clear_outer=side == 0)
        bm.normal_update()
        bm.to_mesh(o.data); bm.free()
        o.data.update()
        out.append(o.name)
    bpy.data.objects.remove(original, do_unlink=True)
    return out


def emit(p, ctrl, bevel=.004):
    o = p.build(COLL, bevel, 2, 30)
    # Mechanical meshes are authored in the controller's local robot frame.
    o.parent = CONTROLS[ctrl]['object']
    o.matrix_parent_inverse = Matrix.Identity(4)
    o.matrix_basis = Matrix.Identity(4)
    o['conversion_group'] = ctrl
    return o


def plate(p, outline, front, depth=.045, material='paint'):
    p.add(rkit.plate_f(outline, front-depth, front, .007), material)


def joint(p, center, radius, width, axis='x'):
    p.add(rkit.drum(center, radius, width, axis), 'darkSteel')
    p.add(rkit.cylinder(center, radius*.49, width+.035, axis), 'chrome')
    for side in (-1, 1):
        c = list(center)
        c[{'x': 0, 'f': 1, 'z': 2}[axis]] += side*(width/2+.018)
        p.many(rkit.bolt_ring(c, axis, radius*.68, 6, .012, .008), 'graphite')


def strut(p, a, b, radius=.034, material='chrome'):
    p.add(kit.tube([V(*a), V(*b)], radius, 12), material)


def torso():
    control('pelvis', (0, -.35, .48), (0, 0, 1.96), timing=(55, 138))
    p=Part('MECH.pelvis')
    p.add(rkit.frame([(-.17,.59,.39,.09,0),(.03,.80,.46,.12,0),(.15,.65,.39,.09,0)]), 'graphite')
    plate(p,[(-.35,.09),(-.19,.15),(.19,.15),(.35,.09),(.23,-.13),(0,-.20),(-.23,-.13)], .27)
    for s in (-1,1):
        joint(p,(s*.38,0,-.06),.17,.16)
        p.add(rkit.hose([(s*.18,-.18,.07),(s*.29,-.25,-.10),(s*.32,-.16,-.23)],.024),'rubber')
    emit(p,'pelvis')
    control('torso', (0, .68, .50), (0, 0, 2.64), folded=(90,0,0), timing=(45, 133), parent='pelvis')
    p=Part('MECH.torso.frame')
    p.add(rkit.frame([(-.52,.48,.42,.1,0),(-.1,.85,.48,.12,0),(.28,1.27,.42,.13,0),(.46,1.1,.36,.1,0)]),'graphite')
    for z,w in [(-.42,.43),(-.27,.52),(-.1,.61)]:
        plate(p,[(-w/2,z+.07),(0,z+.03),(w/2,z+.07),(w/2-.035,z-.06),(0,z-.12),(-w/2+.035,z-.06)],.30,.055,'darkSteel')
        strut(p,(-w/2+.02,.313,z),(w/2-.02,.313,z),.014,'chrome')
    for s in (-1,1):
        strut(p,(s*.20,-.22,-.48),(s*.48,-.23,.32),.045,'darkSteel')
        strut(p,(s*.23,.22,-.48),(s*.43,.22,-.07),.025)
        p.add(rkit.hose([(s*.3,-.26,-.40),(s*.52,-.32,-.03),(s*.6,-.24,.32)],.025),'rubber')
    joint(p,(0,0,-.5),.20,.17,'z')
    emit(p,'torso')
    control('sternum',(0,.65,.78),(0,0,2.64),folded=(90,0,0),timing=(72,146),parent='torso',carry=True)
    p=Part('MECH.sternum')
    plate(p,[(-.12,.50),(0,.57),(.12,.50),(.09,.16),(0,.05),(-.09,.16)],.55,.07,'paintBlack')
    plate(p,[(-.07,.42),(0,.46),(.07,.42),(.052,.29),(0,.24),(-.052,.29)],.565,.012,'steel')
    plate(p,[(-.04,.40),(.04,.40),(0,.31)],.581,.01,'eye')
    emit(p,'sternum')
    control('backFrame',(0,-.40,.5),(0,-.50,2.64),folded=(90,0,0),timing=(45,137),parent='torso')
    p=Part('MECH.backpack.frame')
    for side in (-1,1):
        p.add(rkit.plate_x([(-.36,-.59),(.19,-.59),(.19,.51),(-.32,.62)],*sorted((side*.55,side*.59)),.01),'graphite')
        for z in (-.3,-.18,-.06,.06,.18,.30):
            p.add(rkit.plate_x([(-.29,z),(.11,z),(.11,z+.036),(-.29,z+.036)],*sorted((side*.592,side*.606)),.006),'darkSteel')
    p.add(rkit.plate_z([(-.57,-.36),(.57,-.36),(.57,.19),(-.57,.19)],-.61,-.57,.008),'graphite')
    emit(p,'backFrame')
    for side,S in [(1,'L'),(-1,'R')]:
        control('clavicle.'+S,(side*.32,.82,.5),(side*.75,-.08,3.0),folded=(0,0,90),timing=(44,132),parent='torso')
        p=Part('MECH.clavicle.'+S)
        strut(p,(-.27,0,0),(.27,.04,.04),.074,'darkSteel')
        strut(p,(-.25,-.04,-.11),(.23,0,-.01),.028)
        emit(p,'clavicle.'+S)


def limbs(s, S):
    # Independent hip/knee/ankle and shoulder/elbow/wrist controls remain editable.
    control('thigh.'+S,(s*.34,-.64,.48),(s*.38,0,1.93),angles=(0,-s*7,0),folded=(90,0,0),timing=(60,140),parent='pelvis')
    p=Part('MECH.thigh.'+S)
    p.add(rkit.frame([(-.09,.29,.30,.06,0),(-.21,.40,.38,.08,0),(-.64,.29,.30,.05,0),(-.78,.25,.25,.05,0)]),'graphite')
    joint(p,(0,0,-.02),.16,.35)
    for x in (-.13,.13):
        strut(p,(x,.17,-.18),(x,.17,-.67),.036,'darkSteel')
        strut(p,(x,.20,-.35),(x,.20,-.74),.018)
    plate(p,[(-.12,-.24),(.12,-.24),(.13,-.60),(0,-.70),(-.13,-.60)],.22,.05,'mech')
    emit(p,'thigh.'+S)
    control('shin.'+S,(s*.41,-1.03,.47),(s*.48,.01,1.12),folded=(-90,0,0),timing=(75,148),parent='thigh.'+S)
    p=Part('MECH.shin.'+S)
    p.add(rkit.frame([(-.07,.30,.34,.05,0),(-.22,.40,.39,.09,0),(-.64,.34,.30,.08,0),(-.83,.28,.30,.06,0)]),'graphite')
    joint(p,(0,0,0),.145,.41)
    plate(p,[(-.21,.08),(-.10,.16),(.10,.16),(.21,.08),(.17,-.16),(0,-.23),(-.17,-.16)],.30,.06)
    for x in (-.13,.13):
        strut(p,(x,-.20,-.18),(x,-.20,-.65),.034,'darkSteel')
        strut(p,(x,-.20,-.49),(x,-.20,-.86),.020)
    for z in (-.35,-.44,-.53):
        plate(p,[(-.15,z+.028),(.15,z+.028),(.13,z-.028),(-.13,z-.028)],.205,.03,'steel')
    emit(p,'shin.'+S)
    control('foot.'+S,(s*.4,-1.61,.30),(s*.53,.08,.22),angles=(0,0,-s*7),folded=(0,0,180),timing=(86,151),parent='shin.'+S)
    p=Part('MECH.foot.'+S)
    p.add(rkit.frame([(-.16,.54,.72,.09,.14),(-.12,.55,.80,.10,.18),(.06,.40,.50,.07,.08)]),'graphite')
    joint(p,(0,-.02,.035),.12,.37)
    plate(p,[(-.22,-.11),(.22,-.11),(.18,.005),(-.18,.005)],.61,.09,'darkSteel')
    for x in (-.17,0,.17):
        p.add(rkit.plate_z([(x-.025,.17),(x+.025,.17),(x+.025,.53),(x-.025,.53)],-.055,-.028,.007),'chrome')
    emit(p,'foot.'+S)
    control('upperarm.'+S,(s*.53,.59,.49),(s*1.02,-.04,3.04),angles=(0,-s*13,0),folded=(-90,0,0),timing=(44,132),parent='torso')
    p=Part('MECH.upperarm.'+S)
    p.add(rkit.frame([(-.09,.29,.30,.08,0),(-.22,.35,.36,.09,0),(-.49,.28,.29,.06,0),(-.64,.22,.25,.05,0)]),'graphite')
    joint(p,(0,0,0),.19,.33)
    plate(p,[(-.15,-.20),(.15,-.20),(.12,-.48),(0,-.55),(-.12,-.48)],.21,.06)
    for x in (-.12,.12):
        strut(p,(x,-.18,-.12),(x,-.18,-.47),.030,'darkSteel')
        strut(p,(x,-.18,-.36),(x,-.18,-.63),.016)
    emit(p,'upperarm.'+S)
    control('forearm.'+S,(s*.54,.98,.46),(s*1.16,.02,2.39),angles=(-12,0,s*3),folded=(90,0,0),timing=(64,150),parent='upperarm.'+S)
    p=Part('MECH.forearm.'+S)
    p.add(rkit.frame([(-.04,.22,.25,.05,0),(-.19,.40,.41,.10,.01),(-.50,.32,.33,.08,0),(-.60,.25,.27,.06,0)]),'graphite')
    joint(p,(0,0,0),.125,.33)
    plate(p,[(-.19,-.16),(-.12,-.10),(.12,-.10),(.19,-.16),(.14,-.51),(0,-.59),(-.14,-.51)],.235,.065)
    plate(p,[(-.035,-.17),(.035,-.17),(.035,-.47),(-.035,-.47)],.242,.013,'paintBlack')
    for z in (-.22,-.30,-.38):
        p.add(rkit.cylinder((s*.18,.02,z),.025,.055,'x',12),'steel')
    p.add(rkit.hose([(-s*.11,-.14,-.08),(-s*.19,-.22,-.28),(-s*.10,-.14,-.55)],.017),'rubber')
    emit(p,'forearm.'+S)
    control('hand.'+S,(s*.54,.73,.46),(s*1.14,.155,1.80),angles=(-8,0,s*3),folded=(90,0,0),timing=(113,166),parent='forearm.'+S,carry=True)
    p=Part('MECH.hand.'+S)
    joint(p,(0,0,0),.080,.19)
    p.add(rkit.frame([(-.06,.23,.15,.04,0),(-.22,.25,.18,.04,0)]),'graphite')
    plate(p,[(-.115,-.07),(.115,-.07),(.12,-.20),(-.12,-.20)],.105,.025,'darkSteel')
    for i in range(4):
        x=(i-1.5)*.065
        joint(p,(x,.025,-.23),.037,.055)
        p.add(rkit.hose([(x,.02,-.23),(x,.07,-.315),(x,.15,-.32),(x,.17,-.26)],.027,8,2),'darkSteel')
        p.add(rkit.cylinder((x,.065,-.295),.031,.059,'x',12),'steel')
    p.add(rkit.hose([(-s*.13,0,-.1),(-s*.20,.05,-.17),(-s*.16,.14,-.24)],.042,10,2),'darkSteel')
    emit(p,'hand.'+S,.002)


def head():
    control('head',(0,.53,.50),(0,.015,3.34),folded=(90,0,0),timing=(126,174),parent='torso',carry=True)
    p=Part('MECH.head.neck')
    joint(p,(0,0,.055),.10,.17,'z')
    for s in (-1,1):
        strut(p,(s*.09,0,-.04),(s*.08,.02,.12),.025)
    emit(p,'head')
    p=Part('MECH.head.helmet')
    rings=[]
    for z,w,d in [(.10,.36,.33),(.22,.48,.41),(.43,.48,.42),(.56,.36,.33),(.60,.20,.23)]:
        rings.append([V(x,f,z) for x,f in kit.chamfer_rect(w,d,.065)])
    cut=rkit.plate_f([(-.175,.13),(.175,.13),(.18,.45),(-.18,.45)],.06,.40,.006)
    p.add(kit.loft(rings,True,True),'paint',cuts=[cut])
    p.add(rkit.plate_x([(.16,.43),(.12,.60),(-.1,.63),(-.2,.46)],-.036,.036,.008),'paintBlack')
    for s in (-1,1):
        joint(p,(s*.242,-.045,.32),.090,.065)
        p.add(rkit.plate_x([(-.09,.40),(-.08,.66),(-.015,.58),(.04,.40)],*sorted((s*.20,s*.25)),.009),'paint')
        plate(p,[(s*.08,.42),(s*.19,.45),(s*.23,.40),(s*.17,.38)],.235,.055)
    emit(p,'head',.003)
    p=Part('MECH.head.face')
    plate(p,[(-.16,.15),(-.18,.35),(-.12,.43),(.12,.43),(.18,.35),(.16,.15),(0,.095)],.145,.07,'graphite')
    for s in (-1,1):
        plate(p,[(s*.023,.36),(s*.155,.395),(s*.145,.335),(s*.047,.325)],.178,.025,'eye')
        plate(p,[(s*.16,.30),(s*.19,.25),(s*.11,.13),(s*.055,.19)],.203,.040,'steel')
    plate(p,[(-.055,.32),(0,.37),(.055,.32),(.035,.25),(-.035,.25)],.215,.035,'darkSteel')
    plate(p,[(-.092,.245),(.092,.245),(.105,.19),(.045,.125),(-.045,.125),(-.105,.19)],.206,.035,'steel')
    for x in (-.055,-.018,.018,.055):
        plate(p,[(x-.008,.224),(x+.008,.224),(x+.006,.17),(x-.006,.17)],.210,.006,'graphite')
    emit(p,'head',.002)


def exterior():
    # Original front becomes paired pectoral plates. The aft bonnet becomes thigh armor.
    split('hood',1,-1.48,('hood.nose','hood.aft'))
    for n in ['hood.nose','hood.aft','bumperF','intake','lip','seamBacking','grilleMesh','washerJets','bumperR','seamBackingR','hatchPanel']:
        split(n,0,0,(n+'.R',n+'.L'))
    for s,S in [(1,'L'),(-1,'R')]:
        panel_group('chest.'+S,[n+'.'+S for n in ['hood.nose','bumperF','intake','lip','seamBacking','grilleMesh','lamp','lampReflector','vent']],
                    (s*.36,1.78,.50),(s*.405,.39,2.94),(25,-s*4,-s*5),timing=(53,140),parent='torso')
        panel_group('thighArmor.'+S,['hood.aft.'+S,'washerJets.'+S],(s*.34,1.10,.81),(s*.39,.27,1.62),(90,0,0),timing=(70,145),parent='thigh.'+S)
        panel_group('shoulderArmor.'+S,['fender.'+S,'repeater.'+S,'repeaterBezel.'+S],(s*.75,1.12,.65),(s*.99,-.04,3.15),(75,0,0),timing=(32,125),parent='upperarm.'+S)
        panel_group('shoulderWheel.'+S,['wheel.F'+S],(s*.734,1.22,.288),(s*1.24,-.06,3.17),(0,0,0),timing=(35,126),parent='upperarm.'+S)
        door=['door','winF','sash','sill','bpillar','mirror','mirrorGlass','mirrorBase','handleCup','handle','doorCard']
        panel_group('wing.'+S,[n+'.'+S for n in door],(s*.80,.55,.90),(s*.69,-.40,3.04),(33,-s*8,-s*43),timing=(20,115),parent='torso',via=(s*1.35,.30,1.30))
        split('quarter.'+S,2,.90,('quarter.lower.'+S,'quarter.rail.'+S))
        split('quarter.lower.'+S,1,.58,('quarter.aBase.'+S,'quarter.rear.'+S))
        split('quarter.rail.'+S,1,.60,('quarter.railFront.'+S,'quarter.railRear.'+S))
        panel_group('calfArmor.'+S,['quarter.rear.'+S]+(['fuelLid'] if s==1 else []),
                    (s*.77,-1.26,.55),(s*.62,-.02,.79),(90,0,0),timing=(65,147),parent='shin.'+S)
        panel_group('calfWheel.'+S,['wheel.R'+S],(s*.744,-1.40,.288),(s*.83,-.025,.67),(0,0,0),timing=(67,146),parent='shin.'+S)
        panel_group('shinArmor.'+S,['hatchPanel.'+S]+[n+'.'+S for n in ['tailLamp0','tailLamp1','tailLamp2','tailReflector']],
                    (s*.42,-1.94,.76),(s*.48,.36,.70),(0,0,180),timing=(70,151),parent='shin.'+S)
        panel_group('toeArmor.'+S,['bumperR.'+S,'seamBackingR.'+S]+(['muffler','exhaust'] if s==-1 else []),
                    (s*.42,-1.85,.30),(s*.53,.18,.24),(0,0,180),timing=(85,151),parent='foot.'+S)
        # Long sill rails telescope as two rigid overlapping lengths along the back.
        split('skirt.'+S,1,.05,('skirt.front.'+S,'skirt.rear.'+S))
        for i,n in enumerate(('front','rear')):
            panel_group('spineRail.'+n+'.'+S,['skirt.'+n+'.'+S],(s*.74,.42 if i==0 else -.55,.18),
                        (s*.49,-.56,2.12+i*.67),(-90,0,0),timing=(50,142),parent='torso')
        panel_group('roofRail.'+S,['quarter.railRear.'+S,'winR.'+S],(s*.64,-1.25,1.1),(s*.60,-.79,2.65),(-90,0,0),timing=(45,135),parent='torso')
        panel_group('aRail.'+S,['quarter.railFront.'+S,'quarter.aBase.'+S],(s*.64,.07,1.1),(s*.56,-.70,2.80),(-90,0,0),timing=(38,130),parent='torso')
        panel_group('seatPack.'+S,['seatBack.'+S,'seat.'+S],(s*.35,-.38,.61),(s*.28,-.44,2.60),(0,0,180),timing=(45,136),parent='torso')
        panel_group('moulding.'+S,['moulding.'+S],(s*.84,-.1,.47),(s*.49,-.54,2.59),(-90,0,0),timing=(45,140),parent='torso')
    panel_group('backRoof',['roof','headliner'],(0,-.58,1.28),(0,-.94,2.80),(-90,0,0),timing=(25,128),parent='torso')
    panel_group('backGlass',['hatchGlass','spoiler','brakeLamp'],(0,-1.57,1.12),(0,-.92,2.25),(-40,0,0),timing=(38,132),parent='torso')
    panel_group('collar',['windshield','cowl','wipers','rearMirror'],(0,.48,1.05),(0,-.39,2.96),(110,0,0),timing=(25,126),parent='torso')
    panel_group('internalDash',['dash','pedals','steeringWheel','steeringBadge','console'],(0,.50,.60),(0,-.21,2.70),(70,0,0),timing=(40,125),parent='torso')
    panel_group('internalRear',['rearSeat','belts','badgeR'],(0,-1.10,.6),(0,-.37,2.22),(-90,0,0),timing=(50,140),parent='torso')
    # Underfloor and seals are cut into folding cassettes so no car-length slab remains.
    for name in ('floor','carpet','liners','glassRun'):
        left_right=split(name,0,0,(name+'.sliceR',name+'.sliceL'))
        for n,s in zip(left_right,(-1,1)):
            a,b=split(n,1,.50,(n+'.front',n+'.rear'))
            if name in ('floor','carpet','glassRun'):
                aa,ab=split(a,1,-.40,(a+'.nose',a+'.middle'))
                pieces=(aa,ab,b)
            else: pieces=(a,b)
            for part in pieces:
                o=bpy.data.objects[part]
                if not len(o.data.vertices):
                    bpy.data.objects.remove(o,do_unlink=True); continue
                vs=[o.matrix_world@v.co for v in o.data.vertices]
                center=sum(vs,Vector())/len(vs)
                if name=='liners':
                    ctrl=('shoulderWheel.' if part.endswith('front') else 'calfWheel.')+('L' if s==1 else 'R')
                    mount(o,ctrl,CONTROLS[ctrl]['start'])
                else:
                    panel_group(part,[part],(center.x,-center.y,center.z),(s*.25,-.44,2.65),(-90,0,0),timing=(40,140),parent='torso')


def smooth(t):
    t=max(0,min(1,t)); return t*t*(3-2*t)


def animate():
    sc=bpy.context.scene
    sc.frame_start=1; sc.frame_end=210; sc.render.fps=30
    for frame in range(1,211):
        for name,c in CONTROLS.items():
            a,b=c['timing']; t=smooth((frame-a)/(b-a))
            start=c['start']
            if c['carry']:
                parent=c['object'].parent
                parent_start=CONTROLS[parent.name.removeprefix('CTRL.')]['start']
                start=parent.matrix_world@parent_start.inverted()@start
            p0,q0,_=start.decompose(); p1,q1,_=c['finish'].decompose()
            if c['via'] is not None:
                via=V(*c['via']); p=(1-t)**2*p0+2*(1-t)*t*via+t*t*p1
            else:
                p=p0.lerp(p1,t)
            q=q0.slerp(q1,t)
            world=Matrix.LocRotScale(p,q,Vector((1,1,1)))
            o=c['object']
            o.matrix_basis=o.parent.matrix_world.inverted()@world if o.parent else world
            bpy.context.view_layer.update()
            o.keyframe_insert('location',frame=frame,group=name)
            o.keyframe_insert('rotation_quaternion',frame=frame,group=name)
        # Every piece stays present; no visibility swapping and no scale keys.
    for name,f in [('CAR',1),('UNLOCK PANELS',25),('UNFOLD FRAME',65),('PLANT FEET',145),('ROBOT',180)]:
        sc.timeline_markers.new(name,frame=f)
    sc['Transform instructions']='Frames 1-20: car. 25-174: conversion. 180-210: robot. Named CTRL objects articulate rigid parts; no scaling or visibility swaps.'
    sc.frame_set(180)


def ground_contact():
    """Bake one common vertical carrier so unfolding panels never enter the floor."""
    sc=bpy.context.scene
    root=bpy.data.objects.new('CTRL.groundContact',None);RIG.objects.link(root)
    root.empty_display_type='CIRCLE';root.empty_display_size=1.5
    pelvis=CONTROLS['pelvis']['object'];pelvis.parent=root
    cache=[]
    for o in list(bpy.data.collections['CAR'].all_objects)+list(COLL.objects):
        coords=np.empty(len(o.data.vertices)*3,dtype=np.float64)
        o.data.vertices.foreach_get('co',coords)
        cache.append((o,coords.reshape(-1,3)))
    for frame in range(1,211):
        sc.frame_set(frame);root.location.z=0;bpy.context.view_layer.update()
        low=min(float((coords@np.asarray(o.matrix_world[2][:3])+o.matrix_world[2][3]).min()) for o,coords in cache)
        root.location.z=0 if frame<=20 else .0005-low
        root.keyframe_insert('location',frame=frame,group='Ground contact')
    sc.frame_set(180)


def build():
    global COLL,RIG
    CONTROLS.clear(); ASSIGNED.clear()
    COLL=kit.collection('EK9 • MECHANICAL FRAME')
    RIG=kit.collection('EK9 • ARTICULATION CONTROLS')
    # Bake existing parenting before assigning panels (steering badge is a child).
    car=list(bpy.data.collections['CAR'].all_objects)
    worlds={o.name:o.matrix_world.copy() for o in car}
    for o in car:
        o.parent=None; o.matrix_world=worlds[o.name]; o['source_part']=o.name
    torso()
    for s,S in [(1,'L'),(-1,'R')]: limbs(s,S)
    head(); exterior()
    unassigned=[o.name for o in bpy.data.collections['CAR'].all_objects if o.type=='MESH' and o.name not in ASSIGNED]
    assert not unassigned, 'Unassigned exterior parts: '+str(unassigned)
    animate();ground_contact()
    print('TRANSFORMER_BUILT',len(CONTROLS),'controllers',len(COLL.objects),'mechanical assemblies',flush=True)
