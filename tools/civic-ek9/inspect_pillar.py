import bpy, os, sys, json
from mathutils import Vector
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'blender', 'civic-ek9_build'))
from ek9 import scene
sc = bpy.context.scene
cam = sc.camera
scene.look_at(cam, (2.9,-1.25,2.2), (.36,.32,1.17), 60)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
for u,v in ((931,541),(917,566),(901,459),(945,630),(939,693),(877,380)):
    d = (cam.matrix_world.to_3x3() @ Vector(((u-640)/(1280*60/36), (426.5-v)/(1280*60/36), -1))).normalized()
    origin = cam.location.copy()
    hits=[]
    for _ in range(4):
        hit,p,n,idx,ob,m = sc.ray_cast(dg, origin, d)
        if not hit: break
        hits.append([ob.name, list(p), list(n)])
        origin=p+d*.001
    print('HIT',u,v,json.dumps(hits),flush=True)
for ob in bpy.data.objects:
    if ob.name.startswith('bpillar.'):
        print('PILLAR',ob.name, [(m.name,m.type) for m in ob.modifiers],flush=True)
        ob.modifiers.clear()
scene.RENDER_DIR=os.path.join(ROOT,'evidence','pillar-test')
scene.render('roof', (2.9,-1.25,2.2), (.36,.32,1.17), 60, res=(1280,853))
