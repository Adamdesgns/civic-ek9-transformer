import bpy, json
from mathutils import Vector
out=[]
for o in bpy.data.collections['CAR'].all_objects:
 if o.type=='MESH':
  vs=[o.matrix_world@Vector(v) for v in o.bound_box]
  out.append(dict(name=o.name,parent=o.parent.name if o.parent else None,lo=[round(min(v[i] for v in vs),3) for i in range(3)],hi=[round(max(v[i] for v in vs),3) for i in range(3)]))
print('INVENTORY',json.dumps(out,indent=1),flush=True)
