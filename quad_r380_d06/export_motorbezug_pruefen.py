"""Independently confirm that STEP retains the corrected motor height datum."""
import sys,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD,Part
step=O/'QuadR380_D06_Propeller.step';shape=Part.read(str(step));spec=json.loads((O/'Bauteile.json').read_text());vol=spec['D05_MN1330_LEGACY_REF']['volume_mm3']
candidates=[s for s in shape.Solids if all(abs(a-b)<.01 for a,b in zip([s.BoundBox.XLength,s.BoundBox.YLength,s.BoundBox.ZLength],[150,150,66]))]
motors=[s for s in candidates if abs(s.Volume-vol)<vol*1e-5];assert len(motors)==4
checks=[]
for s in motors:
    b=s.BoundBox;assert abs(b.ZMin-88)<.01 and abs(b.ZMax-154)<.01
    checks.append(dict(zmin_mm=b.ZMin,zmax_mm=b.ZMax,centre_x_mm=(b.XMin+b.XMax)/2,centre_y_mm=(b.YMin+b.YMax)/2))
assert {(round(x['centre_x_mm']),round(x['centre_y_mm'])) for x in checks}=={(425,425),(-425,425),(-425,-425),(425,-425)}
r=dict(passed=True,native_sha256=hashlib.sha256((O/'QuadR380_D06_Propeller.FCStd').read_bytes()).hexdigest(),step_sha256=hashlib.sha256(step.read_bytes()).hexdigest(),motor_reference_checks=checks,scope='Four STEP solids identified by unique motor-reference volume, at the four specified axes and corrected z88..154. Nominal reference geometry only; not detailed OEM validation.')
(O/'STEP_Motorbezug_Pruefung.json').write_text(json.dumps(r,indent=2));print('STEP motor reference datum verified')
