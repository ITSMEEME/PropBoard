"""D02 structural interference screen; fastener fits remain explicitly open."""
import sys,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
D=A.openDocument(str(O/'QuadR380_D02_CFK.FCStd'));rows=json.loads((O/'Instanzen.json').read_text());items=[(r,D.getObject(r['instance'])) for r in rows if not r["id"].startswith("ISO")];cache={};findings=[];candidate=0
for i,(a,x) in enumerate(items):
 for b,y in items[i+1:]:
  if not x.Shape.BoundBox.intersect(y.Shape.BoundBox):continue
  candidate+=1;rel=x.LinkPlacement.inverse().multiply(y.LinkPlacement);sig=(a['id'],b['id'],tuple(round(z,5) for z in list(rel.Base)+list(rel.Rotation.Q)))
  if sig not in cache:
   s=y.LinkedObject.Shape.copy();s.Placement=rel;cache[sig]=max(0,x.LinkedObject.Shape.common(s).Volume)
  volume=cache[sig]
  if volume>.1:findings.append(dict(a=a['instance'],a_id=a['id'],a_label=a['label'],b=b['instance'],b_id=b['id'],b_label=b['label'],volume_mm3=volume))
 if i%40==0:print('Checked',i,'candidates',candidate,'findings',len(findings),flush=True)
result=dict(candidate_pairs=candidate,unique_relative_pairs=len(cache),reporting_threshold_mm3=.1,interferences=findings,scope='Structural solids only; ISO fasteners excluded explicitly. All fastener/inner-thread fits and their clearance to neighbors remain unverified. Not a whole-assembly collision release.',native_sha256=hashlib.sha256((O/'QuadR380_D02_CFK.FCStd').read_bytes()).hexdigest());(O/'Struktur_Kollisionen.json').write_text(json.dumps(result,indent=2,ensure_ascii=False));print('Done',candidate,len(findings),flush=True)
