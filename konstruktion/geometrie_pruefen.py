#!/usr/bin/python3
import sys,json
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as App
HERE=Path(__file__).resolve().parent
d=App.openDocument(str(HERE/'00_PropBoard_Detail_Stehen.FCStd'));d.recompute()
parts=[o for o in d.Objects if hasattr(o,'BauteilID')]
get=lambda ids:[o for o in parts if o.BauteilID in ids]
packs=get(['BAT-MOD-REF']);beams=get(['CFK-Q01','CFK-L01'])
cables=get(['HV-CABLE-REF','LV-CABLE-REF']);wings=get(['FL-CFK-REF'])
checks={}
def distance_check(name,aa,bb):
    minimum=1e9;pair=None
    for a in aa:
        for b in bb:
            # Bounding-box lower bound, exact distance for potential nearest pairs.
            value=a.Shape.distToShape(b.Shape)[0]
            if value<minimum:minimum=value;pair=[a.Name,b.Name]
    checks[name]={'minimum_distance_mm':minimum,'pair':pair,'pairs_checked':len(aa)*len(bb),
                   'strictly_positive_clearance':minimum>1e-6}
distance_check('Akku_zu_CFK_Traegern',packs,beams)
distance_check('Akku_zu_Kabelraeumen',packs,cables)
distance_check('Fluegel_zu_Kabelraeumen',wings,cables)
distance_check('Fluegel_zu_statischen_C_Profilen',wings,get(['FUEHR-C','FUEHR-F']))
report={'checks':checks,'scope':'Nur gespeicherte Hauptbaugruppe. Keine kontinuierliche Kollisions-, Verformungs-, Luftspalt- oder EM-Pruefung.',
        'intended_overlaps':['Knoten-Referenzhuellen','Wicklungsraeume in Statortraegern ohne fertig ausgearbeitete Taschen',
                             'Scheiben-/Schellen-Halteraeume','CFK-Wurzelanschluesse'],
        'mass_budget_closed':False,'manufacturing_release':False}
(HERE/'Abstandspruefung.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
