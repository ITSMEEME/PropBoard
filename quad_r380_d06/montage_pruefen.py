"""Straight approach corridors for root joints and previous motor/carrier bolts."""
import sys,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
from geometrie import intersection_volume
V=A.Vector;native=O/'QuadR380_D06_Propeller.FCStd';D=A.openDocument(str(native));rows=json.loads((O/'Instanzen.json').read_text());shapes={r['instance']:D.getObject(r['instance']).Shape for r in rows};checks=[]
for r in rows:
    labels=['Blattwurzel M5x35','Sicherungsmutter Blattwurzel','MN1330 Statorschraube M6x12','Motorträger Schott M6']
    if r['label'] not in labels:continue
    p=D.getObject(r['instance']).LinkPlacement.Base;s=shapes[r['instance']];nut=r['label']=='Sicherungsmutter Blattwurzel';down=nut or r['label']=='MN1330 Statorschraube M6x12';direction=V(0,0,-1 if down else 1);z=s.BoundBox.ZMin-.1 if down else s.BoundBox.ZMax+.1;outer=6.2 if nut else 2.6 if r['label']=='Blattwurzel M5x35' else 3.6;tool=Part.makeCylinder(outer,35,V(p.x,p.y,z),direction)
    if nut:tool=tool.cut(Part.makeCylinder(3,37,V(p.x,p.y,z)-direction,direction))
    hits=[]
    for q in rows:
        if not tool.BoundBox.intersect(shapes[q['instance']].BoundBox):continue
        volume=intersection_volume(tool,shapes[q['instance']])
        if volume>.1:hits.append(dict(instance=q['instance'],part=q['id'],volume_mm3=volume))
    checks.append(dict(instance=r['instance'],label=r['label'],direction=list(direction),outer_radius_mm=outer,inner_radius_mm=3 if nut else 0,length_mm=35,interferences=hits,passed=not hits))
    print('Tool corridor',r['instance'],not hits,flush=True)
assert len(checks)==72
report=dict(native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),passed=all(r['passed'] for r in checks),check_count=len(checks),checks=checks,scope='Straight35mm approach corridors at default phase, including24 root bolt keys,24 hollow socket corridors below root nuts and24 prior motor/carrier tools. Socket annulus R6.2/R3 clears protruding bolt; no wrench handle, engagement geometry, human hand, assembly order, torque, preload, rotor position range or motor-to-hub bolt release.')
(O/'Montage_Pruefung.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print('D06 assembly corridors passed',report['passed'],flush=True)
