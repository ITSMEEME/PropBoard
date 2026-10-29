#!/usr/bin/python3
"""Triangle meshes from actual FCStd objects, no reconstructed illustrations."""
import json,sys,hashlib
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as App
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
models=[]
for title,file in [('A – vertikale Bahnen nebeneinander','cad/Gegenlaeufiger_Fluegelumlauf.FCStd'),
                   ('B – horizontale Bahnen übereinander','vergleich_horizontal/Horizontal_Z_gegenlaeufig.FCStd')]:
    path=ROOT/file;doc=App.openDocument(str(path));doc.recompute();parts=[]
    for o in doc.Objects:
        if not hasattr(o,'Shape') or o.TypeId=='App::DocumentObjectGroup' or o.Name.startswith('Profil'):continue
        if o.Shape.isNull():continue
        assert o.Shape.isValid(),o.Name
        vertices,faces=o.Shape.tessellate(1.5)
        kind='wing' if o.Name.startswith('Fluegel') else 'structure'
        if kind=='wing':color='#ce6b32' if o.Name.startswith('Fluegel_1') else '#14919b'
        else:color='#808997' if o.Name=='Standdeck' else '#435166'
        parts.append({'name':o.Name,'kind':kind,'color':color,
                      'vertices':[[round(v.x,3),round(v.y,3),round(v.z,3)] for v in vertices],
                      'faces':faces})
    models.append({'title':title,'file':file,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'parts':parts})
    App.closeDocument(doc.Name)
(HERE/'Modelldaten.json').write_text(json.dumps(models,separators=(',',':')))
print([(m['title'],len(m['parts']),sum(len(p['faces']) for p in m['parts'])) for m in models])
