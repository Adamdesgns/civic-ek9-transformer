"""Measure the EK hatch blueprint (refs/ref_images/civic-ek-hatch.png) into
design-space outlines for blender/civic-ek9_build/ek9/dims.py.

    python tools/civic-ek9/measure_blueprint.py

Prints the side-view top/bottom silhouettes (f, z), the plan half width (f, x)
and the front / rear view half widths (z, x), all in metres, scaled so the side
view is 4.18 m long. f = forward from mid-length, z = up from the tyre contact.
"""
import os
import sys
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
IMG = os.path.join(ROOT, 'refs', 'ref_images', 'civic-ek-hatch.png')
LENGTH = 4.18

# view boxes in the original 5100 x 2180 image (x0, y0, x1, y1)
SIDE = (0, 1240, 2700, 2180)
TOP = (2380, 0, 5100, 1260)
FRONT = (560, 150, 1920, 1100)
REAR = (3350, 1250, 4720, 2170)


def load():
    a = np.asarray(Image.open(IMG).convert('L'), dtype=np.uint8)
    return a < 140


def crop(dark, box):
    x0, y0, x1, y1 = box
    return dark[y0:y1, x0:x1]


def cols(d):
    """Per column: first and last dark row (or -1)."""
    any_ = d.any(axis=0)
    top = np.where(any_, d.argmax(axis=0), -1)
    bot = np.where(any_, d.shape[0] - 1 - d[::-1].argmax(axis=0), -1)
    return top, bot


def main():
    dark = load()
    s = crop(dark, SIDE)
    top, bot = cols(s)
    xs = np.where(top >= 0)[0]
    x_nose, x_tail = xs.min(), xs.max()
    ppm = (x_tail - x_nose) / LENGTH
    ground = bot.max()
    print('side: nose px %d tail px %d  %.1f px/m  ground row %d' % (x_nose, x_tail, ppm, ground))

    def f_of(x):          # nose on the left of the side view
        return LENGTH / 2 - (x - x_nose) / ppm

    def z_of(y):
        return (ground - y) / ppm

    print('height (roof top) %.3f m' % z_of(top[top >= 0].min()))
    step = int(round(ppm * 0.05))
    print('\n# side top outline (f, z)')
    print(', '.join('(%.3f, %.3f)' % (f_of(x), z_of(top[x])) for x in range(x_nose, x_tail + 1, step)))
    print('\n# side bottom outline (f, z) (tyres included)')
    print(', '.join('(%.3f, %.3f)' % (f_of(x), z_of(bot[x])) for x in range(x_nose, x_tail + 1, step)))

    # wheels: columns where the lowest dark pixel is within 2 px of the ground are tyre contacts
    contact = [x for x in range(s.shape[1]) if bot[x] >= ground - 2]
    groups = []
    for x in contact:
        if groups and x - groups[-1][-1] <= 3:
            groups[-1].append(x)
        else:
            groups.append([x])
    for g in groups:
        c = 0.5 * (g[0] + g[-1])
        print('tyre contact f %.3f (span %.3f m)' % (f_of(c), (g[-1] - g[0]) / ppm))

    # tyre radius: the tyre is a circle; scan the column through each contact centre upward for the arch gap
    t = crop(dark, TOP)
    ttop, tbot = cols(t)
    txs = np.where(ttop >= 0)[0]
    tn, tt = txs.min(), txs.max()
    tppm = (tt - tn) / LENGTH
    mid = 0.5 * (ttop[txs].min() + tbot[txs].max())
    print('\ntop view: %.1f px/m, width incl mirrors %.3f' % (tppm, (tbot[txs].max() - ttop[txs].min()) / tppm))
    print('# plan half width (f, x) from the upper and lower edges')
    tstep = int(round(tppm * 0.05))
    print(', '.join('(%.3f, %.3f/%.3f)' % (LENGTH / 2 - (x - tn) / tppm, (mid - ttop[x]) / tppm, (tbot[x] - mid) / tppm)
                    for x in range(tn, tt + 1, tstep)))

    for name, box in (('front', FRONT), ('rear', REAR)):
        d = crop(dark, box)
        rows_any = d.any(axis=1)
        ys = np.where(rows_any)[0]
        y_top, y_bot = ys.min(), ys.max()
        left = np.where(rows_any, d.argmax(axis=1), -1)
        right = np.where(rows_any, d.shape[1] - 1 - d[:, ::-1].argmax(axis=1), -1)
        # assume the same scale as the side view; centre from the tyre bottoms
        cx = 0.5 * (left[y_bot] + right[y_bot])
        print('\n%s view: height %.3f m, centre col %.1f' % (name, (y_bot - y_top) / ppm, cx))
        print('# (z, half width left / right)')
        rstep = int(round(ppm * 0.03))
        print(', '.join('(%.3f, %.3f/%.3f)' % ((y_bot - y) / ppm, (cx - left[y]) / ppm, (right[y] - cx) / ppm)
                        for y in range(y_top, y_bot + 1, rstep)))


if __name__ == '__main__':
    sys.exit(main())
