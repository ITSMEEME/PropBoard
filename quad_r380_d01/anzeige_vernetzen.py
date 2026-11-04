"""Retessellate display surfaces only; native CAD and proof bodies stay exact."""
import sys,json
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,MeshPart
j=json.loads((O/'Renderdaten.json').read_text());d=A.openDocument(str(O/'QuadR380_D01_Mechanik.FCStd'))
for k,x in j['meshes'].items():
 row=next(r for r in j['instances'] if r['id']==k);s=d.getObject(row['instance']).LinkedObject.Shape
 mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.15,AngularDeflection=.6 if k.startswith('ISO') else .35,Relative=False);v,f=mesh.Topology;x['vertices_mm']=[[round(y,5) for y in p] for p in v];x['faces']=f;print(k,len(f),flush=True)
j['report']=json.loads((O/'Pruefung.json').read_text());j['display_mesh_settings']=dict(linear_deflection_mm=.15,angular_deflection_rad_norm=.6,angular_deflection_rad_custom=.35)
(O/'Renderdaten.json').write_text(json.dumps(j,separators=(',',':'),ensure_ascii=False));(O/'mesh.js').write_text('globalThis.QD_MODEL='+json.dumps(j,separators=(',',':'),ensure_ascii=False)+';\n')
