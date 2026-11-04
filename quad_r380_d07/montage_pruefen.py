"""Stage-specific tool access for32 clamps and16 motor-base bolts."""
import sys,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
from geometrie import intersection_volume
V=A.Vector;native=O/'QuadR380_D07_V3.FCStd';D=A.openDocument(str(native));rows=json.loads((O/'Instanzen.json').read_text());shapes={r['instance']:D.getObject(r['instance']).Shape for r in rows};checks=[]
for row in rows:
    if row['label'] not in ['V3 Rohrklemmung M4x20','MN1330 Statorschraube M6x12']:continue
    obj=D.getObject(row['instance']);axis=obj.LinkPlacement.Rotation.multVec(V(0,0,1));p=obj.LinkPlacement.Base;master=obj.LinkedObject.Shape;start=p+axis*(master.BoundBox.ZMax+.1);radius=2.6 if row['label'].startswith('V3') else 3.6;tool=Part.makeCylinder(radius,35,start,axis);hits=[]
    # Clamp caps are tightened before motor/rotor installation. Motor-base bolts
    # are then inserted from below. Motor removal is required for cap servicing.
    before_motor=row['label'].startswith('V3')
    for other in rows:
        if before_motor and (other['id']=='D05_MN1330_LEGACY_REF' or other.get('rotor_id')):continue
        s=shapes[other['instance']]
        if not tool.BoundBox.intersect(s.BoundBox):continue
        volume=intersection_volume(tool,s)
        if volume>.1:hits.append(dict(instance=other['instance'],id=other['id'],volume_mm3=volume))
    checks.append(dict(screw=row['instance'],label=row['label'],stage='Before motor/rotor installation' if before_motor else 'Motor on node,from below',tool_radius_mm=radius,straight_length_mm=35,interferences=hits,passed=not hits));print('Tool',row['instance'],not hits,flush=True)
assert len(checks)==48
report=dict(native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),passed=all(c['passed'] for c in checks),checks=checks,sequence=['Assemble central CFK frame and V3 nodes','Insert two tubes per arm with liners/end pads and35mm engagement','Fit cap halves and tighten M4 only after preload/contact design is released','Fit motors and insert4M6 base screws from below','Fit propellers only after OEM attachment depth and rotor/frame clearance are closed'],scope='Only48 straight35mm approach corridors at default pose. Clamp access assumes motor/propeller removal; no in-place clamp-service claim. No hands,tool grip,engagement torque/preload or assembly-order load release.')
(O/'Montage_Pruefung.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print('V3 assembly access passed',report['passed'],flush=True)
