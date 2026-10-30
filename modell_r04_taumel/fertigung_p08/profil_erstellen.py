#!/usr/bin/env python3
"""Extract a valid local 25T section; do not certify the invalid whole STEP."""
import sys,os,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
sys.path.insert(0,os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')))
import FreeCAD as A,Part
src=H.parent/'fertigung_p07/Quellen/SB-2270SGP.STEP'
s=Part.read(str(src));local=s.common(Part.makeCylinder(4,4.5,A.Vector(0,12.3,0),A.Vector(0,1,0)))
assert local.isValid()
s=max(local.Solids,key=lambda x:x.Volume)
p=Part.makePlane(30,30);p.rotate(A.Vector(),A.Vector(1,0,0),90);p.translate(A.Vector(-15,14,-15))
section=s.section(p);wires=[Part.Wire(es) for es in Part.sortEdges(section.Edges)]
faces=[Part.Face(w) for w in wires if w.isClosed()]
f=max(faces,key=lambda x:x.Area);assert f.isValid() and len(f.Edges)==100
# Radial 1% allowance is a prototype design choice, not an ISO spline fit.
m=A.Matrix();m.A11=1.01;m.A33=1.01
face=f.transformGeometry(m);face.translate(A.Vector(0,-23.5,0));tool=face.extrude(A.Vector(0,4,0));assert tool.isValid()
tool.exportBrep(str(H/'Ausgabe/Abtriebsprofil_Schnittwerkzeug.brep'))
(H/'Ausgabe/Abtriebsprofil.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),full_source_valid=False,local_extraction_valid=True,section_y_mm=14,section_edges=100,radial_enlargement_factor=1.01,radial_allowance_at_3mm_mm=.03,fit_status='Design proposal; physical fit/gauge and clamping endurance pending',profile_tool_sha256=hashlib.sha256((H/'Ausgabe/Abtriebsprofil_Schnittwerkzeug.brep').read_bytes()).hexdigest()),indent=2)+'\n')
print('Local section and profile valid; allowance NOT a certified spline fit')
