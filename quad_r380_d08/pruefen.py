"""Nominal static QA of all four arms and all shared frame neighbours."""
import sys,json,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod',str(H.parent/'quad_r380_d07')])
import FreeCAD as A,Part,PartDesign
from geometrie import intersection_volume
V=A.Vector;native=O/'Quad_Parametrisch_V1_V4.FCStd';D=A.openDocument(str(native));geometry=json.loads((O/'Instanzen.json').read_text());hardware=json.loads((O/'Hardware.json').read_text());common=json.loads((O/'Gemeinsame_Instanzen.json').read_text());spec=json.loads((O/'Varianten_Pruefung.json').read_text());cache={};reports=[]
objects={r['instance']:D.getObject(r['instance']) for r in geometry+hardware+common};bounds={n:o.Shape.BoundBox for n,o in objects.items()};rotor_min=min(objects[r['instance']].Shape.BoundBox.ZMin for r in common if r.get('rotor_id'));foot_min=min(objects[r['instance']].Shape.BoundBox.ZMin for r in common if r.get('foot_side'))
def volume(a,b):
 x=objects[a['instance']];y=objects[b['instance']];rel=x.LinkPlacement.inverse().multiply(y.LinkPlacement);m=rel.Rotation.toMatrix();key=(x.LinkedObject.Name,y.LinkedObject.Name,tuple(round(v,6) for v in list(rel.Base)+[getattr(m,'A'+str(i)+str(j)) for i in range(1,4) for j in range(1,4)]))
 if key not in cache:
  s=y.LinkedObject.Shape.copy();s.Placement=rel.multiply(s.Placement);cache[key]=intersection_volume(x.LinkedObject.Shape,s)
 return cache[key]
for variant in ['V1','V2','V3','V4']:
 active=[r for r in geometry+hardware if r['variant']==variant];one=active;findings=[];count=0
 for i,a in enumerate(one):
  for b in one[i+1:]+common:
   if not bounds[a['instance']].intersect(bounds[b['instance']]):continue
   count+=1;v=volume(a,b)
   if v>.1:
    finding=dict(a=a['instance'],b=b['instance'],volume_mm3=v);findings.append(finding);print('INTERFERENCE',variant,finding,flush=True)
  if i%15==0:print('QA',variant,i,len(one),count,len(findings),flush=True)
 maxz=max(bounds[r['instance']].ZMax for r in active);report=dict(variant=variant,all_four_arms_static_candidates=count,all_four_arms_findings=findings,all_four_arms_passed=not findings,new_part_max_z_mm=maxz,rotor_min_z_mm=rotor_min,all_new_parts_rotor_sweep_Z_gap_mm=rotor_min-maxz,all_new_parts_moving_foot_Z_gap_mm=foot_min-maxz,all_new_parts_clear_of_rotor_and_foot_in_Z=rotor_min>maxz and foot_min>maxz);reports.append(report);print('QA complete',variant,report,flush=True)
(O/'Freiraum_Pruefung.json').write_text(json.dumps(dict(native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),variants=reports,threshold_mm3=.1,scope='All four connections including actual clamp hardware against each other and every shared current frame neighbour,at static default pose. Full-Z-separation screen of every new arm component at every corner versus the retained rotor sweep and moving foot systems. Nominal rigid shapes only; no preload,tolerance,deflection or global-flight release. Rotor clearance evaluated separately in Rotor_Pruefung.json.'),indent=2,ensure_ascii=False));print('All QA reports written',flush=True)
