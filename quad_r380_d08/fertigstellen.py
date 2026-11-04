"""Add nominal clamp hardware and verify the native configuration selector."""
import sys,json,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod',str(H.parent/'quad_r380_d07')])
import FreeCAD as A,Part,Import
from geometrie import frame,intersection_volume
V=A.Vector;native=O/'Quad_Parametrisch_V1_V4.FCStd';proof=json.loads((O/'Varianten_Pruefung.json').read_text());assert len(proof['variants'])==4 and all(v['local_geometry_passed'] for v in proof['variants']),proof
D=A.openDocument(str(native));D.Label='Quad R380 – CAD-Konfigurationen V1 bis V4';lib=D.getObject('Bauteilbibliothek');assembly=D.getObject('Montage');control=D.getObject('Variantensteuerung');records=json.loads((O/'Instanzen.json').read_text());variants=json.loads((H.parent/'motoranschluss_varianten/Varianten.json').read_text())[:4];norms={}
for key,path in [('Bolt',H/'Quellen/Normteile/ISO4762_M4x30.brep'),('Nut',H/'Quellen/Normteile/ISO4032_M4.brep'),('Washer',H.parent/'quad_r380_d01/Quellen/Normteile/ISO7089_M4.brep')]:
 s=Part.Shape();s.read(str(path));assert s.isValid() and len(s.Solids)==1;o=D.addObject('Part::Feature','Klemmung_'+key);o.Shape=s;lib.addObject(o);o.Visibility=False;norms[key]=o
norm_mass={key:obj.Shape.Volume*7850e-9 for key,obj in norms.items()}
w=norms['Washer'].Shape.BoundBox.ZLength;stack=21+2*w;best=None
for phase in range(0,360,15):
 n=norms['Nut'].Shape.copy();n.Placement=A.Placement(V(0,0,-stack),A.Rotation(V(0,0,1),phase).multiply(A.Rotation(V(0,1,0),180)))
 try:vol=intersection_volume(norms['Bolt'].Shape,n)
 except (ValueError,Part.OCCError):continue
 if best is None or vol<best[0]:best=(vol,phase)
 if vol<=.1:break
if best and best[0]>.1:
 seed=best[1]
 for phase in [seed+d for d in range(-15,16)]:
  n=norms['Nut'].Shape.copy();n.Placement=A.Placement(V(0,0,-stack),A.Rotation(V(0,0,1),phase).multiply(A.Rotation(V(0,1,0),180)))
  try:vol=intersection_volume(norms['Bolt'].Shape,n)
  except (ValueError,Part.OCCError):continue
  if vol<best[0]:best=(vol,phase)
  if vol<=.1:break
assert best and best[0]<=.1,best
hardware=[]
for idx,v in enumerate(variants):
 od=v['od'];ro=(od+8)/2;ear=od/2+6;starts=[V(*p) for p in v['start']];ends=[V(p[0]-30+45*math.sqrt(2),p[1],min(p[2],-(ro+8))) for p in v['end']]
 for angle in [45,135,225,315]:
  a=math.radians(angle);u=V(math.cos(a),math.sin(a),0);t=V(-u.y,u.x,0);gr=A.Rotation(u,t,V(0,0,1),'ZXY');origin=u*210+V(0,0,88)
  for j,(start,end) in enumerate(zip(starts,ends)):
   axis=end-start;axis.normalize();sr=frame(axis);hr=sr.multiply(A.Rotation(V(1,0,0),-90))
   for side,base in [('root',start),('motor',end-axis*35)]:
    for sign in [-1,1]:
     for kind,y,rr in [('Washer',10.5,hr),('Washer',-10.5-w,hr),('Bolt',10.5+w,hr),('Nut',-10.5-w,hr.multiply(A.Rotation(V(0,0,1),best[1])).multiply(A.Rotation(V(0,1,0),180)))]:
      local=base+sr.multVec(V(sign*ear,y,17.5));pos=origin+gr.multVec(local);rotation=gr.multiply(rr);o=D.addObject('App::Link',v['id']+'_Hardware');o.setLink(norms[kind]);o.LinkPlacement=A.Placement(pos,rotation);assembly.addObject(o);o.Visibility=True;o.setExpression('Visibility',f'Variantensteuerung.Variante == {idx} ? 1 : 0');hardware.append(dict(instance=o.Name,variant=v['id'],part=kind,mass_kg=norm_mass[kind],placement_mm=list(pos),placement_quaternion=list(rotation.Q)))
# Remove the obsolete lower Schott support while retaining its original port geometry.
source=A.openDocument(str(H.parent/'quad_r380_d07/Ausgabe/QuadR380_D07_V3.FCStd'));compact=D.addObject('Part::Feature','Unterer_Kernknoten_Kompakt');compact.Shape=source.getObject('D07_CORE_BOTTOM').Shape.copy();lib.addObject(compact);compact.Visibility=False
oldrows=json.loads((O/'Common_Basis.json').read_text());common=[]
for r in oldrows:
 o=D.getObject(r['instance'])
 if o is None:continue
 if r['id']=='D04_CORE_BOTTOM':o.setLink(compact);r['mass_kg']=compact.Shape.Volume*2810e-9;r['id']='Unterer_Kernknoten_Kompakt'
 common.append(r)
checks=[]
for v in variants:
 control.Variante=v['id'];D.recompute();visible=[r for r in records+hardware if D.getObject(r['instance']).Visibility]
 assert set(r['variant'] for r in visible)=={v['id']}
 assert sum(r['part'].startswith('Tube') for r in visible)==4*v['count']
 assert sum(r['part']=='Motor' for r in visible)==4
 assert sum(r['part']=='Root' for r in visible)==4
 assert sum(r['part']=='Bolt' for r in visible)==16*v['count']
 checks.append(dict(variant=v['id'],visible_variant_instances=len(visible),arm_tubes=4*v['count'],motor_nodes=4,root_nodes=4,clamp_bolt_nut_pairs=16*v['count'],mass_modeled_kg=sum(r['mass_kg'] for r in visible+common),passed=True))
 print('Selector verified',v['id'],checks[-1],flush=True)
control.Variante='V3';D.recompute();D.saveAs(str(native));sha=hashlib.sha256(native.read_bytes()).hexdigest();proof['native_sha256']=sha;proof['clamp_hardware_modeled']=True;proof['nominal_M4_nut_pair_intersection_mm3']=best[0];proof['nominal_M4_nut_phase_deg']=best[1];proof['switch_checks']=checks;proof['complete_connection_release']=False;proof['limits']='Nominal hardware geometry; clamp preload,CFK laminate/contact strengths and manufacturing tolerances unverified. Rotor clearance is evaluated separately in Rotor_Pruefung.json; service-tool validation outstanding.'
for row in proof['variants']:row['scope']='Anschlussgeometrien einschließlich Klemmverschraubungen und nominaler M4-Gewindepaarung modelliert. Freiraumergebnisse in Freiraum_Pruefung.json; keine Festigkeits- oder Fertigungsfreigabe.'
(O/'Varianten_Pruefung.json').write_text(json.dumps(proof,indent=2,ensure_ascii=False));(O/'Hardware.json').write_text(json.dumps(hardware,indent=2));(O/'Gemeinsame_Instanzen.json').write_text(json.dumps(common,indent=2));print('Final native configuration file',sha,flush=True)
