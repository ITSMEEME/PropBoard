import sys,json,hashlib
from pathlib import Path
sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
h=Path(__file__).resolve().parent;o=h/'Ausgabe';r=json.loads((o/'Pruefung.json').read_text());assert r['native_sha256']==hashlib.sha256((o/'QuadR380_D01_Mechanik.FCStd').read_bytes()).hexdigest()
checks=[]
for row in json.loads((o/'Bauteilpruefdaten.json').read_text()):
 d=A.openDocument(str(o/'Einzelteile'/(row['id']+'.FCStd')));b=[x for x in d.Objects if x.TypeId=='PartDesign::Body'];assert len(b)==1;assert b[0].Shape.isValid() and len(b[0].Shape.Solids)==1;assert len(b[0].Group)==row['feature_count'];checks.append(dict(id=row['id'],valid_single_solid=True,history_features=len(b[0].Group)));A.closeDocument(d.Name)
bom=json.loads((o/'Instanzen.json').read_text());assert abs(sum(x['mass_kg'] for x in bom)-r['mass_modeled_kg'])<1e-8
(o/'Export_Pruefung.json').write_text(json.dumps(dict(native_sha256_matches=True,bom_mass_matches=True,individual_native_parts=checks),indent=2));print('12 native exports valid, mass and hash match')
