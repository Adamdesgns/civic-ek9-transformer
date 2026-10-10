import bpy, json, os
out = {}
for name in ('lamp.L', 'hood', 'bpillar.L', 'apillar.L'):
    ob = bpy.data.objects[name]
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    bins = []
    if name == 'lamp.L':
        for i in range(36, 84, 2):
            x = i / 100
            pts = [v for v in vs if abs(v.x-x) < .008]
            if pts:
                p = max(pts, key=lambda v: v.z)
                bins.append([x, round(-p.y,4), round(p.z,4)])
    out[name] = bins
print('EDGE_DATA', json.dumps(out), flush=True)
