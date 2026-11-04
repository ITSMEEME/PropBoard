import sys,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,MeshPart
D=A.openDocument(str(O/'Quad_Parametrisch_V1_V4.FCStd'));base=json.loads((H.parent/'quad_r380_d06/Ausgabe/mesh_geometrie.json').read_text());common=json.loads((O/'Gemeinsame_Instanzen.json').read_text());rows=json.loads((O/'Instanzen.json').read_text())+json.loads((O/'Hardware.json').read_text());meshes={};instances=[]
for r in common+rows:
 obj=D.getObject(r['instance']);key=r.get('id') or obj.LinkedObject.Name
 if key not in meshes:
  if key in base['meshes']:meshes[key]=base['meshes'][key]
  else:
   m=MeshPart.meshFromShape(Shape=obj.LinkedObject.Shape,LinearDeflection=.15,AngularDeflection=.45,Relative=False);v,f=m.Topology;meshes[key]=dict(vertices_mm=[[round(x,5) for x in p] for p in v],faces=f,label=obj.LinkedObject.Label)
   print('Mesh',key,len(f),flush=True)
 row=dict(r,id=key);instances.append(row)
proof=json.loads((O/'Varianten_Pruefung.json').read_text());data=dict(meshes=meshes,instances=instances,common_count=len(common),configurations=proof['switch_checks'],rotor_checks=json.loads((O/'Rotor_Pruefung.json').read_text()),native_sha256=proof['native_sha256'])
(O/'projekt.js').write_text('globalThis.QD_MODEL='+json.dumps(data,separators=(',',':'),ensure_ascii=False)+';\n');print('Actual CAD viewer exported',len(instances),len(meshes),flush=True)
