"""Gridded crop of the blueprint front or rear view (x = left of centre, z = up), blueprint metres.

    python tools/civic-ek9/grid_front.py front|rear out.png [scale]
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
IMG = os.path.join(ROOT, 'refs', 'ref_images', 'civic-ek-hatch.png')
BOX = {'front': (560, 150, 1920, 1100), 'rear': (3350, 1250, 4720, 2170)}
PPM = 631.1

view, out = sys.argv[1], sys.argv[2]
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
im = Image.open(IMG).convert('RGB')
x0, y0, x1, y1 = BOX[view]
crop = im.crop(BOX[view])
d = np.asarray(crop.convert('L')) < 140
ys = np.where(d.any(axis=1))[0]
yb = ys.max()
row = np.where(d[yb])[0]
cx = 0.5 * (row.min() + row.max())
dr = ImageDraw.Draw(crop)
for k in range(-22, 23):
    v = k * 0.05
    x = cx + v * PPM
    major = k % 2 == 0
    dr.line([(x, 0), (x, crop.height)], fill=(255, 60, 60) if major else (255, 200, 200))
    if major:
        dr.text((x + 2, 2), '%.1f' % v, fill=(200, 0, 0))
for k in range(0, 30):
    v = k * 0.05
    y = yb - v * PPM
    major = k % 2 == 0
    dr.line([(0, y), (crop.width, y)], fill=(60, 60, 255) if major else (200, 200, 255))
    if major:
        dr.text((2, y + 2), '%.1f' % v, fill=(0, 0, 200))
if scale != 1.0:
    crop = crop.resize((int(crop.width * scale), int(crop.height * scale)), Image.LANCZOS)
crop.save(out)
print(out, crop.size)
