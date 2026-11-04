import sys,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
D=A.openDocument(str(O/'QuadR380_D04_CFK.FCStd'));rows=json.loads((O/'Instanzen.json').read_text());assert D.getObject('D02_CENTRAL_TOP') is None;assert D.getObject('D02_CENTRAL_BOTTOM') is None;assert not any(r['id'].startswith('D02_CENTRAL') for r in rows)
boxes=[D.getObject(r['instance']).Shape.BoundBox for r in rows];lo=[min(getattr(b,k) for b in boxes) for k in ['XMin','YMin','ZMin']];hi=[max(getattr(b,k) for b in boxes) for k in ['XMax','YMax','ZMax']];core=[r for r in rows if r['id'] in ['D04_TUBE_RING','D04_TUBE_VERTICAL']];assert len(core)==12
r=dict(native_sha256=hashlib.sha256((O/'QuadR380_D04_CFK.FCStd').read_bytes()).hexdigest(),old_central_plate_instances_absent=True,old_central_plate_master_bodies_absent=True,central_cfk_tubes=len(core),nominal_module_min_mm=lo,nominal_module_max_mm=hi,nominal_module_bounds_mm=[b-a for a,b in zip(lo,hi)],scope='Physical CAD assembly only, excluding unmodeled OEM drives/rotors/battery/guards/landing gear')
(O/'Plattenentfall_Pruefung.json').write_text(json.dumps(r,indent=2));print(r)
