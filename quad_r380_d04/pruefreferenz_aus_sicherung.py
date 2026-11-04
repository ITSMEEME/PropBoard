"""Rehash the exact saved native file named by the prior passing proof, never a new geometry."""
import sys,json,hashlib,shutil
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';proof=json.loads((O/'Gewindepruefung.json').read_text());assert proof['passed'];matches=[p for p in O.glob('QuadR380_D04_CFK*.FCBak') if hashlib.sha256(p.read_bytes()).hexdigest()==proof['native_sha256']];assert len(matches)==1
source=Path('/tmp/quad_d04_verified_thread_source.FCStd');shutil.copyfile(matches[0],source);assert hashlib.sha256(source.read_bytes()).hexdigest()==proof['native_sha256'];sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
D=A.openDocument(str(source));hashes={};refs=[]
for r in proof['pairs']:
 a=D.getObject(r['bolt']);b=D.getObject(r['mate'])
 for obj in [a.LinkedObject,b.LinkedObject]:
  if obj.Name not in hashes:hashes[obj.Name]=hashlib.sha256(obj.Shape.exportBrepToString().encode()).hexdigest()
 rel=a.LinkPlacement.inverse().multiply(b.LinkPlacement);refs.append(dict(result=r,master_a_sha256=hashes[a.LinkedObject.Name],master_b_sha256=hashes[b.LinkedObject.Name],relative_placement=list(rel.Base)+list(rel.Rotation.Q),verified_native_sha256=proof['native_sha256']))
(O/'D04_Gewindereferenzen_vor_Korrektur.json').write_text(json.dumps(refs,indent=2));print('References refreshed from exact hash-matched previously verified native file:',len(refs),flush=True)
