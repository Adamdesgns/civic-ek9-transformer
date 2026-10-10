import sys
import numpy as np
from PIL import Image, ImageFilter, ImageChops
photo, render, out = sys.argv[1:4]
P = Image.open(photo).convert('RGB')
Rr = Image.open(render).convert('RGBA')
a = np.array(Rr)[:, :, 3]
# model silhouette + internal edges in cyan over the photo; model faded at 35 %
edges = Image.fromarray(a).filter(ImageFilter.FIND_EDGES)
g = Image.fromarray(np.array(Rr.convert('L'))).filter(ImageFilter.FIND_EDGES)
E = np.maximum(np.array(edges), (np.array(g) > 40) * 120 * (a > 0))
base = np.array(P).astype(float)
m = np.array(Rr.convert('RGB')).astype(float)
k = (a[:, :, None] / 255.0) * 0.35
comp = base * (1 - k) + m * k
e = (E > 60)[:, :, None]
comp = np.where(e, np.array([0, 255, 255]), comp)
Image.fromarray(comp.astype(np.uint8)).save(out)
print('ok', out)
