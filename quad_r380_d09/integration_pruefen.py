"""Native shared-joint and cable integration across all40 configurations."""
import sys,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';R=H.parent;sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod',str(R/'quad_r380_d07')])
import FreeCAD as A,Part,PartDesign
from geometrie import intersection_volume
native=O/'Quad_HEPS_Parametrisch.FCStd';D=A.openDocument(str(native));read=lambda n:json.loads((O/n).read_text());common=read('Gemeinsame_Instanzen.json');sized=read('Groessen_Instanzen.json');arms=read('Instanzen.json')+read('Hardware.json');cables=read('Kabel_Instanzen.json');objects={r['instance']:D.getObject(r['instance']) for r in common+sized+arms+cables};bounds={n:o.Shape.BoundBox for n,o in objects.items()};cache={};reports=[]
def volume(a,b):
 x=objects[a['instance']];y=objects[b['instance']];rel=x.LinkPlacement.inverse().multiply(y.LinkPlacement);key=(x.LinkedObject.Name,y.LinkedObject.Name,tuple(round(v,6) for v in list(rel.Base)+list(rel.Rotation.Q)))
 if key not in cache:
  s=y.LinkedObject.Shape.copy();s.Placement=rel.multiply(s.Placement);cache[key]=intersection_volume(x.LinkedObject.Shape,s)
 return cache[key]
for pidx in range(10):
 hits=[];count=0;fixed=common+[r for r in sized+cables if r['propeller_index']==pidx and r.get('group')!='Rotorhuelle'];wires=[r for r in cables if r['propeller_index']==pidx];seen=set()
 for a in wires:
  for b in fixed:
   key=tuple(sorted([a['instance'],b['instance']]))
   if a['instance']==b['instance'] or key in seen:continue
   seen.add(key)
   if not bounds[a['instance']].intersect(bounds[b['instance']]):continue
   count+=1;v=volume(a,b)
   if v>.1:hits.append(dict(a=a['instance'],b=b['instance'],volume_mm3=v))
 for variant in ['V1','V2','V3','V4']:
  active=[r for r in arms if r['propeller_index']==pidx and r['variant']==variant]
  for i,a in enumerate(active):
   for b in active[i+1:]+fixed:
    if not bounds[a['instance']].intersect(bounds[b['instance']]):continue
    count+=1;v=volume(a,b)
    if v>.1:hits.append(dict(variant=variant,a=a['instance'],b=b['instance'],volume_mm3=v));print('STATIC CONFLICT',pidx,hits[-1],flush=True)
  print('Integration',pidx,variant,count,len(hits),'cached pairs',len(cache),flush=True)
 reports.append(dict(propeller_index=pidx,passed=not hits,candidates=count,findings=hits))
(O/'Integration_Pruefung.json').write_text(json.dumps(dict(native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),configurations=reports,passed=all(r['passed'] for r in reports),threshold_mm3=.1,scope='All changed arm parts including clamp hardware vs each other and shared frame/motors/cables for all40 selections; cable pairs against shared parts. Shared-frame/shared-frame joints inherited,not fully retested. Nominal geometry only; no preload,manufacturing tolerance,tool access or wiring termination release.'),indent=2));print('Full integration report saved',flush=True)
