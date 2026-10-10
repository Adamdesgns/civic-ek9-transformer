"""Text decals as thin closed plates laid on a surface: the wheels' VOLK / RAYS, the seats' RECARO."""
import bmesh
import bpy


def text_mesh(text, length, shear=0.0):
    """Flat outline mesh of `text` in Blender's bundled font: (u, v) verts with the baseline along u,
    scaled to `length` and centred on the origin, its faces, and its height."""
    cu = bpy.data.curves.new('ek.decal', 'FONT')
    cu.body = text
    cu.shear = shear
    cu.fill_mode = 'BOTH'
    cu.resolution_u = 3
    ob = bpy.data.objects.new('ek.decal', cu)
    bpy.context.scene.collection.objects.link(ob)
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    # the font fill is a fan of thin triangles: weld, then beautify it into well-shaped ones (thin
    # slivers fail the model check's zero-area test at decal scale)
    bm = bmesh.new()
    bm.from_mesh(ev.to_mesh())
    ev.to_mesh_clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.curves.remove(cu)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bmesh.ops.beautify_fill(bm, faces=bm.faces, edges=bm.edges)
    bm.verts.index_update()
    pts = [(v.co.x, v.co.y) for v in bm.verts]
    faces = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    u0, u1 = min(p[0] for p in pts), max(p[0] for p in pts)
    v0, v1 = min(p[1] for p in pts), max(p[1] for p in pts)
    k = length / (u1 - u0)
    return [((u - 0.5 * (u0 + u1)) * k, (v - 0.5 * (v0 + v1)) * k) for u, v in pts], faces, (v1 - v0) * k


def plate(b, pts, faces, place, slot, thick=0.0003, lift=0.0004):
    """Add a text mesh to Builder b as a closed plate: `place(u, v)` gives the surface point and its
    outward normal (Blender space) for each text point; the top face stands `lift` off the surface,
    the underside `thick` below it, and a wall runs along every outline edge. The text's faces must
    face out (its baseline x its up = the surface normal)."""
    top, under = [], []
    for u, v in pts:
        p, n = place(u, v)
        top.append(p + n * lift)
        under.append(p + n * (lift - thick))
    count = {}
    for f in faces:
        for i, j in zip(f, f[1:] + f[:1]):
            e = (min(i, j), max(i, j))
            count[e] = count.get(e, 0) + 1
    m = len(top)
    walls = [[j, i, i + m, j + m] for f in faces for i, j in zip(f, f[1:] + f[:1]) if count[(min(i, j), max(i, j))] == 1]
    b.add(top + under, faces + [[i + m for i in reversed(f)] for f in faces] + walls, slot)
