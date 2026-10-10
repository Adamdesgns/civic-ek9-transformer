"""Endpoint preservation, stable transforms, and ground sweep for the EK9 rig."""
import bpy,os,math,json
from mathutils import Vector
from mathutils.kdtree import KDTree
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
sc=bpy.context.scene
car=list(bpy.data.collections['CAR'].all_objects)
mechanical=list(bpy.data.collections['EK9 • MECHANICAL FRAME'].objects)
controls=list(bpy.data.collections['EK9 • ARTICULATION CONTROLS'].objects)
assert len(controls)>=60
assert all(o.parent and o.get('conversion_group') for o in car+mechanical)
sc.frame_set(1)
sources=sorted({o['source_part'] for o in car})
with bpy.data.libraries.load(os.path.join(ROOT,'blender','civic-ek9-yellow-refined.blend'),link=False) as (a,b):
    b.objects=list(sources)
reference=b.objects
temp=bpy.data.collections.new('QA.reference');sc.collection.children.link(temp)
for o in reference: temp.objects.link(o)
bpy.context.view_layer.update()
worst=0; verts_checked=0
for name,ref in zip(sources,reference):
    vs=[];fs=[]
    for o in car:
        if o['source_part']!=name: continue
        offset=len(vs)
        vs.extend(o.matrix_world@v.co for v in o.data.vertices)
        fs.extend([offset+i for i in p.vertices] for p in o.data.polygons)
    tree=KDTree(len(vs))
    for i,v in enumerate(vs): tree.insert(v,i)
    tree.balance()
    for v in ref.data.vertices:
        p=ref.matrix_world@v.co
        nearest=tree.find(p)
        assert nearest[0] is not None, name
        worst=max(worst,nearest[2]);verts_checked+=1
        assert nearest[2]<.00015,(name,nearest[2])
for o in reference: bpy.data.objects.remove(o,do_unlink=True)
bpy.data.collections.remove(temp)
print('CAR_SURFACE PASS',verts_checked,'source vertices; maximum deviation',worst,'m',flush=True)
min_z=1e9; low=None
for frame in range(1,211,3):
    sc.frame_set(frame)
    torso=bpy.data.objects['CTRL.torso']
    head_local=torso.matrix_world.inverted()@bpy.data.objects['CTRL.head'].matrix_world.translation
    assert -.17<head_local.z<.72,(frame,'head detached from torso',head_local[:])
    for side in ('L','R'):
        forearm=bpy.data.objects['CTRL.forearm.'+side]
        hand_local=forearm.matrix_world.inverted()@bpy.data.objects['CTRL.hand.'+side].matrix_world.translation
        assert hand_local.length<.68,(frame,'hand detached from forearm',hand_local[:])
    for o in car+mechanical:
        w=o.matrix_world
        assert all(math.isfinite(v) for row in w for v in row),(frame,o.name)
        assert max(abs(v-1) for v in w.to_scale())<.0001,(frame,o.name,'scale')
        assert not o.hide_render,(frame,o.name,'hidden')
        # Exact vertex ground check, not rotated bounding-box corners.
        z=min((w@v.co).z for v in o.data.vertices)
        if z<min_z: min_z=z;low=(frame,o.name)
print('RIG_TRANSFORMS PASS 70 sampled frames; unit scale, finite matrices, all meshes visible',flush=True)
print('DEPLOYMENT_CARRIERS PASS head stays with torso and hands stay with forearms',flush=True)
print('GROUND_SWEEP minimum',min_z,'at',low,flush=True)
assert min_z>-.001,('ground intersection',min_z,low)
sc.frame_set(180)
robot_bounds=[]
for i in range(3):
    values=[(o.matrix_world@v.co)[i] for o in car+mechanical for v in o.data.vertices]
    robot_bounds.append((min(values),max(values)))
print('ROBOT_BOUNDS',robot_bounds,flush=True)
sc.frame_set(1)
protrusions=[]
for o in mechanical:
    xs=[o.matrix_world@v.co for v in o.data.vertices]
    if max(abs(v.x) for v in xs)>.82 or min(v.z for v in xs)<.06 or max(v.z for v in xs)>1.24:
        protrusions.append((o.name,[min(v.z for v in xs),max(v.z for v in xs)],max(abs(v.x) for v in xs)))
print('STOW_EXTENTS',protrusions,flush=True)
assert not protrusions,protrusions
sc.frame_set(180)
print('TRANSFORMER_CHECKS_COMPLETE',flush=True)

