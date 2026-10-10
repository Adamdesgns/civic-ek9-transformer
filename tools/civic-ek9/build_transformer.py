"""Build and render the separate EK9 transformer from the corrected source car."""
import os,sys,math
import bpy
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
sys.path.insert(0,os.path.join(ROOT,'blender','civic-ek9_build'))
from ek9 import transformer,scene,kit
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if 'render-only' not in args:
    transformer.build()
sc=bpy.context.scene
for ob in bpy.data.objects:
    if ob.type=='LIGHT': ob.hide_render=True
world=bpy.data.worlds.new('EK9 robot studio');world.use_nodes=True
world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.15,.18,.23,1)
world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.4
sc.world=world
for name,loc,power,size,target in [('key',(3,-4,6),1100,4,(0,0,2)),('fill',(-3,-2,4),850,3,(0,0,2)),('rim',(2,3,5),1500,3,(0,0,2)),('top',(-2,1,6),850,3,(0,0,2))]:
    d=bpy.data.lights.new('robot.'+name,'AREA');d.energy=power;d.shape='DISK';d.size=size
    o=bpy.data.objects.new('robot.'+name,d);sc.collection.objects.link(o);o.location=loc
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
ground=bpy.data.objects.get('ek.ground')
if ground:
    m=bpy.data.materials.new('Robot stage');m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.045,.055,.071,1);bs.inputs['Roughness'].default_value=.55
    ground.data.materials.clear();ground.data.materials.append(m);ground.scale.x=20;ground.scale.y=20
if not bpy.data.objects.get('robot.cyclorama'):
    rings=[]
    for i in range(13):
        a=math.pi/2*i/12;r=8+4*math.sin(a);z=4*(1-math.cos(a))
        rings.append([Vector((r*math.cos(j*math.tau/128),r*math.sin(j*math.tau/128),z-.002)) for j in range(128)])
    rings.append([Vector((12*math.cos(j*math.tau/128),12*math.sin(j*math.tau/128),12)) for j in range(128)])
    vs,fs=kit.loft(rings,False,False)
    mesh=bpy.data.meshes.new('robot.cyclorama');mesh.from_pydata(vs,[],fs);mesh.update()
    o=bpy.data.objects.new('robot.cyclorama',mesh);sc.collection.objects.link(o);o.data.materials.append(m)
    for f in mesh.polygons: f.use_smooth=True
sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices: d.use=d.type!='CPU'
    if any(d.use for d in prefs.devices): sc.cycles.device='GPU'
except Exception: pass
sc.view_settings.view_transform='Khronos PBR Neutral';sc.view_settings.look='None';sc.view_settings.exposure=-1.15
out=os.path.join(ROOT,'evidence','transformer');os.makedirs(out,exist_ok=True);scene.RENDER_DIR=out
views={'hero':(180,(5,-9,4.1),(0,0,1.98),52),'front':(180,(0,-10,2.8),(0,0,2),55),'back':(180,(5,8,3.5),(0,0,2),52),'car':(1,(5,-7,2.4),(0,0,.6),52),'mid':(100,(5,-8,3.5),(0,0,1.6),52)}
requested=[a for a in args if a in views] or ['hero']
for name in requested:
    frame,pos,target,lens=views[name];sc.frame_set(frame)
    scene.render(name,pos,target,lens,res=(1100,1100))
sc.frame_set(180);scene.look_at(sc.camera,*views['hero'][1:])
sc.render.resolution_x=1100;sc.render.resolution_y=1100
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.shading.type='MATERIAL';sp.shading.use_scene_world=True;sp.shading.use_scene_lights=True
            sp.overlay.show_overlays=False;sp.region_3d.view_perspective='CAMERA'
        if area.type=='DOPESHEET_EDITOR':
            area.spaces.active.dopesheet.show_only_selected=False
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','civic-ek9-transformer.blend'))
print('TRANSFORMER_READY',flush=True)
