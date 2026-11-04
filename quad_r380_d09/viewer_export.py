from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;O=H/'Ausgabe';R=H.parent;sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,MeshPart
native=O/'Quad_HEPS_Parametrisch.FCStd';D=A.openDocument(str(native));read=lambda n:json.loads((O/n).read_text());base=json.loads((R/'quad_r380_d06/Ausgabe/mesh_geometrie.json').read_text())['meshes'];common=read('Gemeinsame_Instanzen.json');rows=common+read('Groessen_Instanzen.json')+read('Instanzen.json')+read('Hardware.json')+read('Kabel_Instanzen.json');meshes={};instances=[]
for r in rows:
 obj=D.getObject(r['instance']);key=r.get('id') or obj.LinkedObject.Name
 # Source id can refer to identical motor/norm geometry; actual new root masters are reused.
 if key not in meshes:
  if key in base:meshes[key]=base[key]
  else:
   mesh=MeshPart.meshFromShape(Shape=obj.LinkedObject.Shape,LinearDeflection=.25,AngularDeflection=.5,Relative=False);v,f=mesh.Topology;meshes[key]=dict(vertices_mm=[[round(x,5) for x in p] for p in v],faces=f,label=obj.LinkedObject.Label)
  print('Mesh',key,len(meshes[key]['faces']),flush=True)
 instances.append(dict(r,id=key))
proof=read('Umschalter_Pruefung.json');data=dict(native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),meshes=meshes,instances=instances,common_count=len(common),configurations=proof['checks'],propeller_configurations=json.loads((H/'Konfigurationen.json').read_text()),rotor_checks=read('Freiraum_Pruefung.json'))
(O/'projekt.js').write_text('globalThis.QD_MODEL='+json.dumps(data,separators=(',',':'),ensure_ascii=False)+';\n');print('Viewer',len(instances),'instances',len(meshes),'meshes',flush=True)
