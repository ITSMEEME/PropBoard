import sys,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,Import
D=A.openDocument(str(O/'QuadR380_D02_CFK.FCStd'));rows=json.loads((O/'Instanzen.json').read_text());s=Part.Compound([D.getObject(r['instance']).Shape for r in rows]);Import.export([D.getObject(r['instance']) for r in rows],str(O/'QuadR380_D02_CFK.step'));print('STEP exported',flush=True);back=Part.read(str(O/'QuadR380_D02_CFK.step'));print('STEP read',len(back.Solids),flush=True);assert len(back.Solids)==len(rows)
unique={}
for solid in back.Solids:
 solid.Placement=A.Placement();code=solid.hashCode();bucket=unique.setdefault(code,[])
 if any(solid.isSame(ref) for ref in bucket):continue
 assert solid.isValid();bucket.append(solid)
print('Unique STEP geometries valid',sum(map(len,unique.values())),flush=True)
report=dict(expected_solids=len(rows),reimported_solids=len(back.Solids),individually_validated_solids=sum(map(len,unique.values())),all_valid=True,volume_comparison_performed=False,native_sha256=hashlib.sha256((O/'QuadR380_D02_CFK.FCStd').read_bytes()).hexdigest(),step_sha256=hashlib.sha256((O/'QuadR380_D02_CFK.step').read_bytes()).hexdigest());(O/'STEP_Pruefung.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
