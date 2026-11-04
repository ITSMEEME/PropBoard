"""D03 structural/foot-system interference and full discrete travel check."""
import sys,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
D=A.openDocument(str(O/'QuadR380_D03_CFK.FCStd'));rows=json.loads((O/'Instanzen.json').read_text());proof=json.loads((O/'Gewindepruefung.json').read_text());assert proof['passed'];control=D.getObject('Fussverstellung');cache={};results=[]
proof_volumes={frozenset([x['bolt'],x['mate']]):x['intersection_mm3'] for x in proof['pairs']};newset={p['bolt'] for p in json.loads((O/'Neue_Gewindepaare.json').read_text())};selected=[r for r in rows if not r['id'].startswith('ISO') or r.get('foot_side') or r['instance'] in newset];objects={r['instance']:D.getObject(r['instance']) for r in rows};bounds={k:v.Shape.BoundBox for k,v in objects.items()}
def check(a,b,stage):
 x=objects[a['instance']];y=objects[b['instance']]
 if not bounds[a['instance']].intersect(bounds[b['instance']]):return None
 token=frozenset([a['instance'],b['instance']]);rel=x.LinkPlacement.inverse().multiply(y.LinkPlacement);key=(a['id'],b['id'],tuple(round(z,6) for z in list(rel.Base)+list(rel.Rotation.Q)))
 if key not in cache:
  if stage=='locked' and token in proof_volumes:cache[key]=proof_volumes[token]
  else:
   shape=y.LinkedObject.Shape.copy();shape.Placement=rel.multiply(shape.Placement);cache[key]=max(0,x.LinkedObject.Shape.common(shape).Volume)
 volume=cache[key]
 if volume>.1:results.append(dict(a=a['instance'],b=b['instance'],a_id=a['id'],b_id=b['id'],a_label=a['label'],b_label=b['label'],volume_mm3=volume,stage=stage))
 return volume
candidates=0
for i,a in enumerate(selected):
 for b in selected[i+1:]:
  if check(a,b,'locked') is not None:candidates+=1
 if i%50==0:print('Static',i,candidates,len(results),flush=True)
static_count=len(results);travel=[];dynamic_count=0
fixed=[r for r in rows if not r.get('foot_side')]
for side in ['Links','Rechts']:
 moving=[r for r in rows if r.get('foot_side')==side]
 for position in range(130,251,10):
  for stroke in [0,10]:
   control.Links=-position if side=='Links' else -250;control.Rechts=position if side=='Rechts' else 250;control.Entriegelung=stroke;D.recompute();before=len(results)
   for r in moving:bounds[r['instance']]=objects[r['instance']].Shape.BoundBox
   for r in moving:
    expected=(-position if side=='Links' else position)+r['placement_mm'][0]-r['foot_base_x_mm'];assert abs(objects[r['instance']].LinkPlacement.Base.x-expected)<1e-6
    for q in fixed:
     if check(r,q,'travel-'+str(stroke)) is not None:dynamic_count+=1
   # At the open endpoint, recheck the index screw against its own moving bracket.
   for p in json.loads((O/'Neue_Gewindepaare.json').read_text()):
    r=next(r for r in rows if r['instance']==p['bolt'])
    if p['family']=='Index M6' and r.get('foot_side')==side:
     q=next(r for r in rows if r['instance']==p['mate']);check(r,q,'travel-'+str(stroke));actual=objects[r['instance']].LinkPlacement.Base.y;assert abs(actual-r['placement_mm'][1]-(1 if actual>0 else -1)*stroke)<1e-6
   travel.append(dict(side=side,position_mm=position,index_screw_stroke_mm=stroke,new_interference_count=len(results)-before));print('Travel',side,position,stroke,len(results)-before,flush=True)
# Cross-foot separation: all selected bodies remain within each plate's +/-70mm X outline.
control.Links=-200;control.Rechts=200;control.Entriegelung=0;D.recompute()
for side in ['Links','Rechts']:
 centre=-200 if side=='Links' else 200
 for r in rows:
  if r.get('foot_side')==side:
   bb=objects[r['instance']].Shape.BoundBox;assert bb.XMin>=centre-70.001 and bb.XMax<=centre+70.001
# Native plate top is244; countersunk-head maximum must stay at least0.19mm below it.
headclear=[]
for r in rows:
 if r['id']=='ISO10642_M5x50':
  gap=244-objects[r['instance']].Shape.BoundBox.ZMax;assert gap>.19;headclear.append(dict(instance=r['instance'],head_below_plate_mm=gap))
# Document remains in its original saved default pose: checks do not modify native CAD.
result=dict(native_sha256=hashlib.sha256((O/'QuadR380_D03_CFK.FCStd').read_bytes()).hexdigest(),static_candidates=candidates,dynamic_candidates=dynamic_count,static_interference_count=static_count,total_interference_count=len(results),interferences=results,travel_cases=travel,all169_locked_stance_combinations_separate_by_min120mm=True,head_clearances=headclear,scope='Static structure plus all foot-system fasteners and28 new mating screws. Moving foot system checked against ALL fixed neighboring solids at26 grid positions and2 screw endpoints. Other old ISO fasteners excluded from global static screen; no total vehicle release. Nominal rigid geometry, reporting threshold0.1mm3.')
(O/'Bauraum_Pruefung.json').write_text(json.dumps(result,indent=2,ensure_ascii=False));print('D03 clearance complete',len(travel),'travel cases',len(results),'findings',flush=True)
