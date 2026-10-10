"""Crop a blueprint view with a design-coordinate grid for reading internal lines.

    python tools/civic-ek9/grid_crop.py side f0 f1 z0 z1 out.png [scale]
    python tools/civic-ek9/grid_crop.py top  f0 f1 x0 x1 out.png [scale]

side: f = forward (nose at +2.09), z = up from the tyre contact (blueprint units).
top:  f as above, x = left of the centreline.
Grid lines every 0.05 m, labelled every 0.1 m.
"""
import os
import sys
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
IMG = os.path.join(ROOT, 'refs', 'ref_images', 'civic-ek-hatch.png')
# calibration from measure_blueprint.py (original pixels)
SIDE = dict(x_nose=17, y_ground=1240 + 922, ppm=631.1)
TOP = dict(x_nose=2380 + (2410 - 2380), y_mid=None, ppm=633.3)


def main():
    view, a0, a1, b0, b1, out = sys.argv[1], *map(float, sys.argv[2:6]), sys.argv[6]
    scale = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
    im = Image.open(IMG).convert('RGB')
    if view == 'side':
        c = SIDE
        px = lambda f: c['x_nose'] + (2.09 - f) * c['ppm']
        py = lambda z: c['y_ground'] - z * c['ppm']
    else:
        # top view: find the centre row and nose column once
        import numpy as np
        d = np.asarray(im.convert('L'))[0:1260, 2380:5100] < 140
        cols = np.where(d.any(axis=0))[0]
        rows = np.where(d.any(axis=1))[0]
        x_nose = 2380 + cols.min()
        # centre: the half-way line of the body at mid-length
        mid_col = d[:, (cols.min() + cols.max()) // 2]
        r = np.where(mid_col)[0]
        y_mid = 0.5 * (r.min() + r.max())
        px = lambda f: x_nose + (2.09 - f) * TOP['ppm']
        py = lambda x: y_mid - x * TOP['ppm']
    X0, X1 = sorted((px(a0), px(a1)))
    Y0, Y1 = sorted((py(b0), py(b1)))
    crop = im.crop((int(X0), int(Y0), int(X1), int(Y1)))
    dr = ImageDraw.Draw(crop)
    step = 0.05
    k0 = int(min(a0, a1) / step) - 1
    k1 = int(max(a0, a1) / step) + 1
    for k in range(k0, k1 + 1):
        v = k * step
        x = px(v) - X0
        major = abs(round(v * 10) - v * 10) < 1e-6
        dr.line([(x, 0), (x, crop.height)], fill=(255, 60, 60) if major else (255, 190, 190), width=1)
        if major:
            dr.text((x + 2, 2), '%.1f' % v, fill=(200, 0, 0))
    k0 = int(min(b0, b1) / step) - 1
    k1 = int(max(b0, b1) / step) + 1
    for k in range(k0, k1 + 1):
        v = k * step
        y = py(v) - Y0
        major = abs(round(v * 10) - v * 10) < 1e-6
        dr.line([(0, y), (crop.width, y)], fill=(60, 60, 255) if major else (190, 190, 255), width=1)
        if major:
            dr.text((2, y + 2), '%.1f' % v, fill=(0, 0, 200))
    if scale != 1.0:
        crop = crop.resize((int(crop.width * scale), int(crop.height * scale)), Image.LANCZOS)
    crop.save(out)
    print(out, crop.size)


if __name__ == '__main__':
    main()
