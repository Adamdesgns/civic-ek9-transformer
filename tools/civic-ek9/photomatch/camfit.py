"""Fit a pinhole camera (Blender world, car faces -Y, +X = car's left) to photo landmarks.

    python camfit.py <marks.json> <out.json>

marks.json: {"W": 1280, "H": 853, "init": {"eye": [...], "yaw": deg, "pitch": deg, "fpx": ...},
             "points": {"name": [[x, y, z], [u, v]], ...}}
Camera convention: R = Rz(yaw) Rx(pitch) Ry(roll); columns = right, forward, up (world)."""
import json
import sys
import numpy as np
from scipy.optimize import least_squares

spec = json.load(open(sys.argv[1]))
W, H = spec['W'], spec['H']
names = list(spec['points'])
P3 = np.array([spec['points'][k][0] for k in names], float)
UV = np.array([spec['points'][k][1] for k in names], float)
wts = np.array([spec.get('weights', {}).get(k, 1.0) for k in names], float)


def rot(yaw, pitch, roll):
    cy, sy, cp, sp, cr, sr = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch), np.cos(roll), np.sin(roll)
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    Ry = np.array([[cr, 0, sr], [0, 1, 0], [-sr, 0, cr]])
    return Rz @ Rx @ Ry


def project(p, X):
    ex, ey, ez, yaw, pitch, roll, fpx = p
    R = rot(yaw, pitch, roll)
    c = (X - np.array([ex, ey, ez])) @ R          # rows: (right, forward, up)
    return np.stack([W / 2 + fpx * c[:, 0] / c[:, 1], H / 2 - fpx * c[:, 2] / c[:, 1]], 1)


def resid(p):
    return ((project(p, P3) - UV) * wts[:, None]).ravel()


ini = spec['init']
best = None
for dyaw in np.radians([-8, -4, 0, 4, 8]):
    for fpx in (ini['fpx'] * 0.6, ini['fpx'], ini['fpx'] * 1.6):
        for dist in (0.7, 1.0, 1.4):
            e = np.array(ini['eye'], float)
            c = np.array(ini.get('target', [0, 0, 0.6]), float)
            e = c + (e - c) * dist
            x0 = np.array([*e, np.radians(ini['yaw']) + dyaw, np.radians(ini.get('pitch', 0)), 0.0, fpx * dist])
            r = least_squares(resid, x0, loss='soft_l1', f_scale=3.0)
            if best is None or r.cost < best.cost:
                best = r
p = best.x
R = rot(*p[3:6])
uv = project(p, P3)
print('eye', np.round(p[:3], 3), 'yaw/pitch/roll', np.round(np.degrees(p[3:6]), 2), 'fpx %.1f lens %.1f mm' % (p[6], p[6] / W * 36))
for k, o, f in zip(names, UV, uv):
    print('  %-10s obs %7.1f %7.1f  fit %7.1f %7.1f  err %5.1f' % (k, o[0], o[1], f[0], f[1], np.hypot(*(f - o))))
print('rms px %.2f' % np.sqrt(np.mean(np.sum((uv - UV) ** 2, 1))))
json.dump({'W': W, 'H': H, 'eye': list(p[:3]), 'R': R.tolist(), 'fpx': p[6]}, open(sys.argv[2], 'w'))
