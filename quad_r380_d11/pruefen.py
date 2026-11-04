from pathlib import Path
import sys,json,math,hashlib,os
H=Path(__file__).resolve().parent;R=H.parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod',str(R/'quad_r380_d07')])
import FreeCAD as A,Part,PartDesign
from geometrie import intersection_volume
V=A.Vector;native=O/'Quad_Motornahe_Reglerhalter.FCStd';D=A.openDocument(str(native));read=lambda p:json.loads(p.read_text());modules=read(O/'Reglerhalter_Instanzen.json');spec=read(O/'Regler_Montage.json');common=read(R/'quad_r380_d10/Ausgabe/Gemeinsame_Instanzen.json');variable=sum([read(R/'quad_r380_d10/Ausgabe'/n) for n in ['Instanzen.json','Hardware.json','Groessen_Instanzen.json','Kabel_Instanzen.json']],[]);old=common+variable;objects={r['instance']:D.getObject(r['instance']) for r in old};bounds={n:o.Shape.BoundBox for n,o in objects.items()};cache={};findings=[];count=0;switch=[];control=D.getObject('Variantensteuerung');cfgs=read(R/'quad_r380_d10/Konfigurationen.json')
def compare(shape,other):
 global count
 if not shape.BoundBox.intersect(other.BoundBox):return 0
 count+=1;return intersection_volume(shape,other)
for c in spec['configurations']:
 pidx=c['propeller_index'];v=c['variant'];
 if os.environ.get('D11_GROUP') and pidx%4!=int(os.environ['D11_GROUP']):continue
 group=[m for m in modules if m['propeller_index']==pidx and m['variant']==v];active=common+[r for r in variable if r['propeller_index']==pidx and r.get('variant',v)==v and r.get('group')!='Rotorhuelle']
 for m in group:
  placement=D.getObject(m['instance']).LinkPlacement
  for part in [p for p in m['parts'] if p['role']!='unidentified_ESC_datum']:
   shape=D.getObject(part['master']).Shape.copy();shape.Placement=placement.multiply(shape.Placement)
   for r in active:
    if not shape.BoundBox.intersect(bounds[r['instance']]):continue
    obj=objects[r['instance']];rel=placement.inverse().multiply(obj.LinkPlacement);key=(part['master'],obj.LinkedObject.Name,tuple(round(x,6) for x in list(rel.Base)+list(rel.Rotation.Q)))
    if key not in cache:
     other=obj.LinkedObject.Shape.copy();other.Placement=rel.multiply(other.Placement);cache[key]=compare(D.getObject(part['master']).Shape,other)
    vol=cache[key]
    if vol>.1:findings.append(dict(propeller_index=pidx,variant=v,part=part['part'],old=r['instance'],volume_mm3=vol));print('CLASH',findings[-1],flush=True)
  box=Part.makeBox(146,74,39.5,V(c['cx']-73,c['cy']-37,-180));box.Placement=placement
  for r in active:
   if box.BoundBox.intersect(bounds[r['instance']]):
    vol=compare(box,objects[r['instance']].Shape)
    if vol>.1:findings.append(dict(propeller_index=pidx,variant=v,part='unconfirmed_ESC_envelope',old=r['instance'],volume_mm3=vol))
 # Exact internal-part check at one arm; other three are rigid copies.
 parts=[p for p in group[0]['parts'] if p['role']!='unidentified_ESC_datum']
 for i,a in enumerate(parts):
  for b in parts[i+1:]:
   xa=D.getObject(a['master']);xb=D.getObject(b['master'])
   if xa.TypeId=='App::Link' and xb.TypeId=='App::Link':
    rel=xa.LinkPlacement.inverse().multiply(xb.LinkPlacement);key=('std_pair',xa.LinkedObject.Name,xb.LinkedObject.Name,tuple(round(v,6) for v in list(rel.Base)+list(rel.Rotation.Q)))
    if key not in cache:
     t=xb.LinkedObject.Shape.copy();t.Placement=rel.multiply(t.Placement);cache[key]=compare(xa.LinkedObject.Shape,t)
    vol=cache[key]
   else:vol=compare(xa.Shape,xb.Shape)
   if vol>.1:findings.append(dict(propeller_index=pidx,variant=v,part=a['part'],other=b['part'],volume_mm3=vol));print('INTERNAL CLASH',findings[-1],flush=True)
 control.Propeller=cfgs[pidx]['label'];control.Variante=v;D.recompute();visible=[m for m in modules if D.getObject(m['instance']).Visibility];assert len(visible)==4 and all(m['propeller_index']==pidx and m['variant']==v for m in visible);switch.append(dict(propeller_index=pidx,variant=v,visible_modules=4,passed=True));print('Check',pidx,v,'findings',len(findings),flush=True)
max_z=max(D.getObject(m['instance']).Shape.BoundBox.ZMax for m in modules);assert max_z<124
(O/('Reglerhalter_Pruefung_'+os.environ['D11_GROUP']+'.json' if os.environ.get('D11_GROUP') else 'Reglerhalter_Pruefung.json')).write_text(json.dumps(dict(native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),nominal_clear=not findings,new_parts_rotor_Z_gap_mm=124-max_z,findings=findings,candidates=count,switch_checks=switch,scope='Actual mounting components vs all selected prior CAD at all4 corners; internal component pairs on one arm per50 state,other corners rigid copies.ESC body checked only as74x146x39.5 envelope.No actual OEM body,ports,thermal,preload or strength release.'),indent=2));print('ESC checks finished',not findings,flush=True)
