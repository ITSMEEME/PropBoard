#!/usr/bin/env python3
"""Export the checked saved native assembly and record its exact provenance."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as A,Part,Import
H=Path(__file__).resolve().parent;O=H/'Ausgabe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    global O
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=O);O=ap.parse_args().output
    native=O/'P13_Mechanik.FCStd';before=sha(native)
    doc=A.openDocument(str(native));objects=[o for o in doc.Objects if 'P13Key' in o.PropertiesList]
    target=O/'P13_Mechanik.step';Import.export(objects,str(target))
    assert sha(native)==before
    imported=Part.read(str(target));solids=imported.Solids
    original_volume=sum(o.Shape.Volume for o in objects)
    error=abs(sum(s.Volume for s in solids)-original_volume)/original_volume
    passed=len(solids)==len(objects) and error<1e-6
    result=dict(passed=passed,native_sha256=before,step_sha256=sha(target),exported_bodies=len(objects),step_roundtrip_solids=len(solids),volume_relative_error=error,note='Gesamt-STEP aus genau diesem gespeicherten FCStd; STEP erneut eingelesen und Körperzahl/Volumensumme geprüft; bei Fehler nicht ins Lieferpaket übernehmen')
    (O/'Gesamt_STEP_Pruefung.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps(result))
    if not passed:raise SystemExit(1)
if __name__=='__main__':main()
