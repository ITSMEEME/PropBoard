#!/usr/bin/env python3
"""Extract the actual unpitched CAD blade section, including blunt trailing edge."""
import os,sys,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
sys.path[:0]=[os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')),str(H.parent/'cad')]
import FreeCAD as App,erstellen as C
s=C.blade_shape();w=s.slice(App.Vector(1,0,0),110);assert len(w)==1
pts=[((15-v.Point.y)/30,v.Point.z/30) for v in w[0].Vertexes]
upper=sorted([p for p in pts if p[1]>=-1e-10],reverse=True);lower=sorted([p for p in pts if p[1]<-1e-10]);pts=upper+lower
# Geometric coordinates are from the BRep, not a replacement ideal sharp NACA section.
text='H01 actual CAD section x=110 mm, 2 percent blunt TE\n'+''.join(f'{x:.9f} {y:.9f}\n' for x,y in pts)
(H/'H01_CAD_Profil.dat').write_text(text)
info=dict(status='CAD_GEOMETRY_EXTRACTED_NOT_EXPERIMENTAL_POLAR',section_radius_mm=110,chord_mm=30,points=len(pts),trailing_edge_thickness_mm=(upper[0][1]-lower[-1][1])*30,profile_sha256=hashlib.sha256(text.encode()).hexdigest())
(H/'Profilherkunft.json').write_text(json.dumps(info,indent=2));print(info)
