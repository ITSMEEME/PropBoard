from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod',str(H.parent/'quad_r380_d07')])
import FreeCAD as A,Part,PartDesign
from geometrie import intersection_volume
native=O/'Quad_HEPS_Innenverkabelung.FCStd';D=A.openDocument(str(native));rows=json.loads((O/'Instanzen.json').read_text());motors=json.loads((O/'Groessen_Instanzen.json').read_text());checks=[]
for r in [r for r in rows if r['part']=='Motor' and r['instance'].endswith('_45')]:
 a=D.getObject(r['instance']).Shape
 for s in [s for s in motors if s['propeller_index']==r['propeller_index'] and s.get('id')=='ISO4762_M6x12' and s['placement_mm'][0]>0 and s['placement_mm'][1]>0]:
  b=D.getObject(s['instance']).Shape;volume=intersection_volume(a,b) if a.BoundBox.intersect(b.BoundBox) else 0;checks.append(dict(propeller_index=r['propeller_index'],variant=r['variant'],carrier=r['instance'],bolt=s['instance'],intersection_mm3=volume,passed=volume<=.1))
 print('Stator fit',r['propeller_index'],r['variant'],flush=True)
(O/'Statorfit_Pruefung.json').write_text(json.dumps(dict(native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),checks=checks,passed=all(x['passed'] for x in checks),scope='Actual bolt/carrier solid pairs at45-degree arm,for all50 size/layout states.Other corners are rigid copies,not independently rechecked here.Nominal fit only;no preload,strength or OEM thread-depth release.'),indent=2));print('Stator fit',all(x['passed'] for x in checks),flush=True)
