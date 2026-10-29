#!/usr/bin/python3
"""Check that the numerical inventory matches the actual saved model."""
import csv,json,sys
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as App
ROOT=Path(__file__).resolve().parents[1]
name='00_PropBoard_Detail_Stehen.FCStd'
rows=[r for r in csv.DictReader((ROOT/'konstruktion/Stueckliste_Instanzen.csv').open(encoding='utf-8-sig')) if r['Datei']==name]
d=App.openDocument(str(ROOT/'konstruktion'/name));d.recompute()
maximum=0.
for r in rows:
    obj=d.getObject(r['Instanz']);assert obj is not None,r['Instanz']
    assert obj.BauteilID==r['ID'],r['Instanz']
    error=abs(obj.Shape.Volume-float(r['Volumen_mm3']));maximum=max(maximum,error)
    assert error<.002,(r['Instanz'],error)
out={'instances_checked':len(rows),'max_rounding_difference_mm3':maximum,'tolerance_mm3':.002,
     'inventory_matches_native_CAD':True,'material_density_verified':False}
(ROOT/'tragfaehigkeit/CAD_Volumenpruefung.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
