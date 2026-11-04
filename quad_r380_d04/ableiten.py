import sys,json,hashlib,csv
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,MeshPart,Import
D=A.openDocument(str(O/'QuadR380_D04_CFK.FCStd'));bom=json.loads((O/'Instanzen.json').read_text());spec=json.loads((O/'Bauteile.json').read_text());meshes={}
for k in dict.fromkeys(r['id'] for r in bom):
 row=next(r for r in bom if r['id']==k);b=D.getObject(row['instance']).LinkedObject;s=b.Shape;assert s.isValid() and len(s.Solids)==1,k
 mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.15,AngularDeflection=.6 if k.startswith('ISO') else .35,Relative=False);v,f=mesh.Topology;meshes[k]=dict(vertices_mm=[[round(y,5) for y in p] for p in v],faces=f,material=spec[k]['material'],label=b.Label);print('Mesh',k,len(f),flush=True)
r=json.loads((O/'Status.json').read_text());r['all_master_solids_valid']=True;r['native_sha256']=hashlib.sha256((O/'QuadR380_D04_CFK.FCStd').read_bytes()).hexdigest();(O/'Status.json').write_text(json.dumps(r,indent=2,ensure_ascii=False));payload=dict(report=r,meshes=meshes,instances=bom);(O/'mesh.js').write_text('globalThis.QD_MODEL='+json.dumps(payload,separators=(',',':'),ensure_ascii=False)+';\n')
fields=list(dict.fromkeys(k for row in bom for k in row))
with (O/'Stueckliste.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fields,delimiter=';');w.writeheader();w.writerows(bom)
Import.export([D.getObject(x['instance']) for x in bom],str(O/'QuadR380_D04_CFK.step'));print('STEP exported',flush=True)
# Reimport verifies instance count. Every unique prototype is checked above; per-instance
# topology check of the reimported STEP is deliberately not claimed here.
back=Part.read(str(O/'QuadR380_D04_CFK.step'));assert len(back.Solids)==len(bom)
(O/'Export_Pruefung.json').write_text(json.dumps(dict(native_sha256=r['native_sha256'],step_sha256=hashlib.sha256((O/'QuadR380_D04_CFK.step').read_bytes()).hexdigest(),expected_solids=len(bom),reimported_solids=len(back.Solids),native_master_solids_valid=True,reimported_each_solid_validity_checked=False),indent=2));print('D04 STEP reimport count passed',len(bom),flush=True)
