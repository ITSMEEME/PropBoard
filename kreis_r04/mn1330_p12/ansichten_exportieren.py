#!/usr/bin/env python3
"""Tessellate actual saved BRep, no generative rendering."""
import json,sys,argparse
from pathlib import Path
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as A
H=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=H/'Ausgabe');args=ap.parse_args();O=args.output
d=A.openDocument(str(O/'P12_MN1330.FCStd'));rows=[]
for o in d.Objects:
    if not hasattr(o,'BauteilID'):continue
    vs,fs=o.Shape.tessellate(1.5)
    rows.append({'name':o.P12Key if 'P12Key' in o.PropertiesList else o.Name,'id':o.BauteilID,'vertices':[[v.x,v.y,v.z] for v in vs],'triangles':fs})
(O/'Ansichten_Mesh.json').write_text(json.dumps(rows,separators=(',',':')))
print(len(rows),'BRep objects tessellated')
