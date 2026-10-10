"""Small animation preview; does not overwrite the authored Blender scene."""
import os,sys
import bpy
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
sys.path.insert(0,os.path.join(ROOT,'blender','civic-ek9_build'))
from ek9 import scene
sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.samples=8;sc.render.use_persistent_data=True;sc.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices: d.use=d.type!='CPU'
    if any(d.use for d in prefs.devices): sc.cycles.device='GPU'
except Exception: pass
out=os.path.join(ROOT,'evidence','transformer','animation-final');os.makedirs(out,exist_ok=True)
scene.RENDER_DIR=out
for f in range(1,211,10):
    sc.frame_set(f)
    scene.render('%03d'%f,(5.5,-10,4.2),(0,0,1.9),52,res=(560,560))
print('ANIMATION_PREVIEW_COMPLETE',flush=True)

