#!/usr/bin/python3
import sys,json,hashlib
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as App
HERE=Path(__file__).resolve().parent
models=[]
specs=[('Hauptbaugruppe – Stehen','00_PropBoard_Detail_Stehen.FCStd'),('CFK-Rahmen und Klemmknoten','01_CFK_Rahmen.FCStd'),
       ('Führung, Linearantrieb und Pitch – Detail','02_Fuehrung_Antrieb_Detail.FCStd'),('Batterie und feste Kabelwege','03_Batterie_Kabel.FCStd'),
       ('Ergonomiekonzept – niedriger Langsitz','04_Ergonomie_Sitzen.FCStd'),('Ergonomiekonzept – Bauchlage','04_Ergonomie_Liegen.FCStd'),
       ('Vergrößerter Schlitten-/Pitchauszug','02a_Schlitten_Detail.FCStd')]
for title,name in specs:
    path=HERE/name;d=App.openDocument(str(path));d.recompute();parts=[]
    for o in d.Objects:
        if not hasattr(o,'BauteilID'):continue
        assert o.Shape.isValid()
        kind='pilot' if o.BauteilID=='PILOT-REF' else 'wing' if o.BauteilID=='FL-CFK-REF' else 'structure'
        if o.BauteilID in ['FUEHR-C-PROBE','FUEHR-F-PROBE','LM-SPULE-REF','FUEHR-C','FUEHR-F','MAG-JOCH','LM-STATOR-REF','IPT-PRI-REF']:kind='stator'
        color='#303945' if 'CFK' in o.Material_Annahme else '#8c99a8'
        if o.BauteilID=='FL-CFK-REF':color='#007f89'
        if kind=='pilot':color='#dba376'
        if o.BauteilID in ['HV-CABLE-REF','LM-STATOR-REF','LM-SPULE-REF']:color='#ec771e'
        if o.BauteilID=='LV-CABLE-REF':color='#1b9764'
        if o.BauteilID=='BAT-MOD-REF':color='#5376b0'
        if o.BauteilID=='ISO-01':color='#d8bb36'
        vertices,faces=o.Shape.tessellate(2)
        parts.append({'name':o.Name,'kind':kind,'color':color,'vertices':[[round(v.x,3),round(v.y,3),round(v.z,3)] for v in vertices],'faces':faces})
    models.append({'title':title,'file':'konstruktion/'+name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'parts':parts})
    App.closeDocument(d.Name)
(HERE/'Modelldaten.json').write_text(json.dumps(models,separators=(',',':')))
print([(m['title'],len(m['parts']),sum(len(p['faces']) for p in m['parts'])) for m in models],flush=True)
