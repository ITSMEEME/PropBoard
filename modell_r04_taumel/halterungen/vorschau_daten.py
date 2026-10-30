#!/usr/bin/env python3
import sys,os
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));sys.path.insert(0,os.environ.get('FREECAD_LIB',str(HERE.parents[1]/'.cfd-tools/freecad/usr/lib')))
import FreeCAD as App
import numpy as np
import halterungen_features
OUT=HERE/'Ausgabe';d=App.openDocument(str(OUT/'R04_Taumelmodell_Halterungen_H01.FCStd'))
triangles=[];groups=[]
for o in d.Objects:
 if not hasattr(o,'BauteilID') or o.BauteilID.startswith('KEEP_'):continue
 pts,faces=o.Shape.tessellate(.7)
 if not faces:continue
 p=np.array([[v.x,v.y,v.z] for v in pts]);t=p[np.array(faces,dtype=int)]
 ident=o.BauteilID
 group=3 if ident=='REF_AKKU' else 4 if ident.startswith('REF_') else 2 if ident.startswith('H') else 0 if o.Name.startswith('Rotor_oben') else 1 if o.Name.startswith('Rotor_unten') else 5
 triangles.extend(t);groups.extend([group]*len(t))
np.savez_compressed(OUT/'Vorschau_Daten.npz',triangles=np.array(triangles),groups=np.array(groups))
App.closeDocument(d.Name);print('Preview triangles:',len(triangles))
