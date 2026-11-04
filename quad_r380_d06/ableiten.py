"""Native surface meshes and verified STEP round trip for the D06 proposal."""
import sys,json,hashlib,csv
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,MeshPart,Import
D=A.openDocument(str(O/'QuadR380_D06_Propeller.FCStd'));bom=json.loads((O/'Instanzen.json').read_text());spec=json.loads((O/'Bauteile.json').read_text());meshes={}
for k in dict.fromkeys(r['id'] for r in bom):
    row=next(r for r in bom if r['id']==k);b=D.getObject(row['instance']).LinkedObject;s=b.Shape;assert s.isValid() and len(s.Solids)==1,k
    mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.12,AngularDeflection=.6 if k.startswith('ISO') else .25,Relative=False);v,f=mesh.Topology;meshes[k]=dict(vertices_mm=[[round(y,5) for y in p] for p in v],faces=f,material=spec[k]['material'],label=b.Label)
    print('Mesh',k,len(f),flush=True)
r=json.loads((O/'Status.json').read_text());assert r['native_sha256']==hashlib.sha256((O/'QuadR380_D06_Propeller.FCStd').read_bytes()).hexdigest();r['all_master_solids_valid']=True;(O/'Status.json').write_text(json.dumps(r,indent=2,ensure_ascii=False));payload=dict(report=r,meshes=meshes,instances=bom);(O/'mesh_geometrie.json').write_text(json.dumps(payload,separators=(',',':'),ensure_ascii=False))
fields=list(dict.fromkeys(k for row in bom for k in row))
with (O/'Stueckliste.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fields,delimiter=';');w.writeheader();w.writerows(bom)
step=O/'QuadR380_D06_Propeller.step';Import.export([D.getObject(x['instance']) for x in bom],str(step));print('STEP exported',flush=True)
back=Part.read(str(step));assert len(back.Solids)==len(bom)
# Every newly designed propeller prototype is also independently STEP-reimported.
new=[]
for k in spec:
    f=O/(k+'.step')
    if not f.exists():continue
    s=Part.read(str(f));ok=s.isValid() and len(s.Solids)==1;assert ok,k;new.append(dict(part=k,valid=True,volume_delta_mm3=abs(s.Volume-spec[k]['volume_mm3'])))
assert len(new)==10
(O/'Export_Pruefung.json').write_text(json.dumps(dict(native_sha256=r['native_sha256'],step_sha256=hashlib.sha256(step.read_bytes()).hexdigest(),expected_solids=len(bom),reimported_solids=len(back.Solids),native_master_solids_valid=True,new_propeller_step_prototypes=new,assembly_reimport_each_solid_validity_checked=False),indent=2));print('D06 STEP checks passed',len(bom),len(new),flush=True)
