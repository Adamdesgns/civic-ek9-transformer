import json, sys
import numpy as np
from PIL import Image
cam = json.load(open(sys.argv[1]))
W, H, eye, R, fpx = cam['W'], cam['H'], np.array(cam['eye']), np.array(cam['R']), cam['fpx']
RIDE = 0.010
def ray(u, v):
    d = R @ np.array([(u - W / 2) / fpx, 1.0, -(v - H / 2) / fpx])
    return d / np.linalg.norm(d)
def on_plane_x(u, v, x0=0.0):
    d = ray(u, v); t = (x0 - eye[0]) / d[0]; p = eye + t * d
    return -p[1], p[2] - RIDE          # design f, design z
P = np.array(Image.open(sys.argv[2]).convert('HSV')).astype(int)
yel = (P[:, :, 0] > 20) & (P[:, :, 0] < 45) & (P[:, :, 1] > 120) & (P[:, :, 2] > 120)
A = np.array(Image.open(sys.argv[3]))[:, :, 3] > 128
side = sys.argv[4]
print(' z_design  f_photo  f_model  diff(cm)')
for v in range(430, 690, 6):
    py = np.where(yel[v])[0]; my = np.where(A[v])[0]
    if not len(py) or not len(my): continue
    pu = py.min() if side == 'front' else py.max(); mu = my.min() if side == 'front' else my.max()
    fp, zp = on_plane_x(pu, v); fm, zm = on_plane_x(mu, v)
    print('%7.3f %8.3f %8.3f %7.1f' % (zp, fp, fm, 100 * (fm - fp)))
