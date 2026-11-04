"""Derive surfaces, BOM and STEP from the hash-matched V3 native assembly."""
import sys,json,hashlib,csv
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,MeshPart,Import
native=O/'QuadR380_D07_V3.FCStd';D=A.openDocument(str(native));rows=json.loads((O/'Instanzen.json').read_text());spec=json.loads((O/'Bauteile.json').read_text());meshes={};sha=hashlib.sha256(native.read_bytes()).hexdigest()
for key in dict.fromkeys(r['id'] for r in rows):
    row=next(r for r in rows if r['id']==key);obj=D.getObject(row['instance']).LinkedObject;s=obj.Shape;assert s.isValid() and len(s.Solids)==1,key
    mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.12,AngularDeflection=.6 if key.startswith('ISO') else .25,Relative=False);v,f=mesh.Topology;meshes[key]=dict(vertices_mm=[[round(x,5) for x in p] for p in v],faces=f,material=spec[key]['material'],label=obj.Label);print('V3 mesh',key,len(f),flush=True)
report=json.loads((O/'Status.json').read_text());assert report['native_sha256']==sha;report['all_master_solids_valid']=True;(O/'Status.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));(O/'mesh_geometrie.json').write_text(json.dumps(dict(report=report,meshes=meshes,instances=rows),separators=(',',':'),ensure_ascii=False))
fields=list(dict.fromkeys(k for r in rows for k in r))
with (O/'Stueckliste.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fields,delimiter=';');w.writeheader();w.writerows(rows)
step=O/'QuadR380_D07_V3.step';Import.export([D.getObject(r['instance']) for r in rows],str(step));print('V3 STEP exported',flush=True);back=Part.read(str(step));assert len(back.Solids)==len(rows)
new=[]
for key in [key for key in spec if key.startswith('D07_')]:
    s=Part.read(str(O/(key+'.step')));assert s.isValid() and len(s.Solids)==1,key;new.append(dict(part=key,valid=True,volume_difference_mm3=abs(s.Volume-spec[key]['volume_mm3'])))
assert len(new)==7
motors=[s for s in back.Solids if all(abs(a-b)<.01 for a,b in zip([s.BoundBox.XLength,s.BoundBox.YLength,s.BoundBox.ZLength],[150,150,66]))];assert len(motors)==4
assert all(abs(s.BoundBox.ZMin-88)<.01 and abs(s.BoundBox.ZMax-154)<.01 for s in motors)
(O/'Export_Pruefung.json').write_text(json.dumps(dict(native_sha256=sha,step_sha256=hashlib.sha256(step.read_bytes()).hexdigest(),expected_solids=len(rows),reimported_solids=len(back.Solids),native_master_solids_valid=True,new_V3_step_prototypes=new,motor_reference_z88_154_preserved=True,assembly_each_reimported_solid_validity_checked=False),indent=2));print('V3 STEP count,new prototypes,motor datum passed',len(rows),flush=True)
