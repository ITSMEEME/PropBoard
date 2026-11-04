"""Straight tool approach checks for16 bottom stator and8 top carrier screws."""
import sys,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
D=A.openDocument(str(O/'QuadR380_D05_MN1330.FCStd'));rows=json.loads((O/'Instanzen.json').read_text());shapes={r['instance']:D.getObject(r['instance']).Shape for r in rows};result=[]
for r in rows:
 if r['label'] not in ['MN1330 Statorschraube M6x12','Motorträger Schott M6']:continue
 obj=D.getObject(r['instance']);p=obj.LinkPlacement.Base;down=r['label']=='MN1330 Statorschraube M6x12';z=shapes[r['instance']].BoundBox.ZMin-.1 if down else shapes[r['instance']].BoundBox.ZMax+.1;tool=Part.makeCylinder(3.6,35,A.Vector(p.x,p.y,z),A.Vector(0,0,-1 if down else 1));hits=[]
 for q in rows:
  if not tool.BoundBox.intersect(shapes[q['instance']].BoundBox):continue
  v=max(0,tool.common(shapes[q['instance']]).Volume)
  if v>.1:hits.append(dict(instance=q['instance'],id=q['id'],volume_mm3=v))
 result.append(dict(screw=r['instance'],label=r['label'],approach='from below' if down else 'from above',tool_radius_mm=3.6,straight_length_mm=35,interferences=hits,passed=not hits));print('Motor tool',r['instance'],not hits,flush=True)
assert len(result)==24
(O/'Motor_Montage_Pruefung.json').write_text(json.dumps(dict(native_sha256=hashlib.sha256((O/'QuadR380_D05_MN1330.FCStd').read_bytes()).hexdigest(),passed=all(r['passed'] for r in result),checks=result,scope='Straight nominal socket-tool cylinders; legacy motor reference only, not real OEM ventilation/cable/tool-grip envelopes; no torque/depth/strength release'),indent=2));print('Motor assembly screen',all(r['passed'] for r in result),flush=True)
