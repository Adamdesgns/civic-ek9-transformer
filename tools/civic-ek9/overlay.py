"""Overlay the EK hatch blueprint (red) on an orthographic review render.

    python tools/civic-ek9/overlay.py <render.png> side|front|rear|top <out.png>

Renders come from ek9.build.ortho (design metres, fixed framing); the blueprint
is mapped with the same design transform as dims.py
(x = 0.9855 x_bp, z = 1.0144 z_bp - 0.093).
"""
import os
import sys
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
IMG = os.path.join(ROOT, 'refs', 'ref_images', 'civic-ek-hatch.png')
PPM_BP = 631.1
ZS, ZO, XS = 1.0144, -0.093, 0.9855
BOX = {'front': (560, 150, 1920, 1100), 'rear': (3350, 1250, 4720, 2170), 'top': (2380, 0, 5100, 1260)}
# render framing (must match ek9.build.ORTHO / ortho())
FRAME = {'side': (4.6, 0.70), 'front': (2.3, 0.70), 'rear': (2.3, 0.70), 'top': (4.6, 0.0)}


def view_origin(dark, view):
    x0, y0, x1, y1 = BOX[view]
    d = dark[y0:y1, x0:x1]
    ys = np.where(d.any(axis=1))[0]
    xs = np.where(d.any(axis=0))[0]
    if view == 'top':
        mid = d[:, (xs.min() + xs.max()) // 2]
        r = np.where(mid)[0]
        return x0 + xs.min(), y0 + 0.5 * (r.min() + r.max())
    yb = ys.max()
    row = np.where(d[yb])[0]
    return x0 + 0.5 * (row.min() + row.max()), y0 + yb


def main():
    render, view, out = sys.argv[1], sys.argv[2], sys.argv[3]
    r = Image.open(render).convert('RGBA')
    W, H = r.size
    span, zc = FRAME[view]
    ppm = W / span
    bp = Image.open(IMG).convert('L')
    dark = np.asarray(bp) < 140
    # inverse affine: render pixel (u, v) -> blueprint pixel (X, Y)
    if view == 'side':
        # u = W/2 - f ppm ; v = H/2 - (z - zc) ppm ; X = 17 + (2.09 - f) P ; Y = 2162 - (z - ZO)/ZS P
        a = PPM_BP / ppm
        c = 17 + 2.09 * PPM_BP - (W / 2) * a
        b = PPM_BP / (ZS * ppm)
        d = 2162 - PPM_BP * (zc - ZO) / ZS - (H / 2) * b
        coeffs = (a, 0, c, 0, b, d)
    elif view == 'top':
        xn, ym = view_origin(dark, 'top')
        # u = W/2 - f ppm ; v = H/2 + x ppm ; X = xn + (2.09 - f) P ; Y = ym - x/XS P
        a = PPM_BP / ppm
        c = xn + 2.09 * PPM_BP - (W / 2) * a
        b = -PPM_BP / (XS * ppm)
        d = ym - (H / 2) * b
        coeffs = (a, 0, c, 0, b, d)
    else:
        cx, yb = view_origin(dark, view)
        # u = W/2 + h ppm (h = +x front, -x rear: blueprint right == render right)
        a = PPM_BP / (XS * ppm)
        c = cx - (W / 2) * a
        b = PPM_BP / (ZS * ppm)
        d = yb - PPM_BP * (zc - ZO) / ZS - (H / 2) * b
        coeffs = (a, 0, c, 0, b, d)
    warped = bp.transform((W, H), Image.AFFINE, coeffs, resample=Image.BILINEAR, fillcolor=255)
    lines = np.asarray(warped) < 170
    base = Image.new('RGBA', (W, H), (255, 255, 255, 255))
    base.alpha_composite(r)
    px = np.array(base)
    px[lines] = (230, 20, 20, 255)
    Image.fromarray(px).save(out)
    print(out)


if __name__ == '__main__':
    main()
