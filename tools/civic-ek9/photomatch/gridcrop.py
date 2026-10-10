import sys
from PIL import Image, ImageDraw
def grid(src, box, out, s=4, step=10):
    im = Image.open(src).convert('RGB')
    c = im.crop(box); c = c.resize((c.width * s, c.height * s), Image.LANCZOS); dr = ImageDraw.Draw(c)
    for y in range(0, box[3] - box[1] + 1, step // 2):
        Y = box[1] + y
        if Y % step: 
            continue
        dr.line([(0, y * s), (c.width, y * s)], fill=(0, 255, 255) if Y % 50 == 0 else (0, 110, 110), width=1)
        if Y % 50 == 0: dr.text((2, y * s + 2), str(Y), fill=(0, 255, 255))
    for x in range(0, box[2] - box[0] + 1):
        X = box[0] + x
        if X % step:
            continue
        dr.line([(x * s, 0), (x * s, c.height)], fill=(255, 0, 255) if X % 50 == 0 else (110, 0, 110), width=1)
        if X % 50 == 0: dr.text((x * s + 2, 2), str(X), fill=(255, 0, 255))
    c.save(out)
if __name__ == '__main__':
    src, x0, y0, x1, y1, out = sys.argv[1], *map(int, sys.argv[2:6]), sys.argv[6]
    s = int(sys.argv[7]) if len(sys.argv) > 7 else 4
    grid(src, (x0, y0, x1, y1), out, s)
