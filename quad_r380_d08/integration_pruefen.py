"""Check changed shared end nodes and routed cable solids against shared parts."""
import sys,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod',str(H.parent/'quad_r380_d07')])
import FreeCAD as A,Part,PartDesign
from geometrie import intersection_volume
native=O/'Quad_Parametrisch_V1_V4.FCStd';D=A.openDocument(str(native));common=json.loads((O/'Gemeinsame_Instanzen.json').read_text());new=[r for r in common if r['id'].startswith('D08_D04_HIGH_') or r.get('group')=='Kabelplanung'];shapes={r['instance']:D.getObject(r['instance']).Shape for r in common};seen=set();hits=[];count=0
for a in new:
 for b in common:
  key=tuple(sorted([a['instance'],b['instance']]))
  if a['instance']==b['instance'] or key in seen:continue
  seen.add(key);x=shapes[a['instance']];y=shapes[b['instance']]
  if not x.BoundBox.intersect(y.BoundBox):continue
  count+=1;v=intersection_volume(x,y)
  if v>.1:hits.append(dict(a=a['instance'],b=b['instance'],volume_mm3=v));print('Shared conflict',hits[-1],flush=True)
 print('Shared check',a['instance'],count,len(hits),flush=True)
(O/'Integration_Pruefung.json').write_text(json.dumps(dict(native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),candidates=count,findings=hits,passed=not hits,scope='Changed end-node solids and all routed cable core/jacket solids vs all shared parts at default pose; arm variants checked separately. No connector insertion,clamp retention or flexible cable dynamics.'),indent=2));print('Shared integration',not hits,flush=True)
