#!/usr/bin/env python3
import sys,os,json,gzip
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')),str(H)]
import FreeCAD as A,MeshPart,bewegung_runtime
p=H/'Ausgabe/Cohexial_R04_M01_Bewegung.FCStd';d=A.openDocument(str(p));o=d.getObject('Bewegungssteuerung');o.Proxy=bewegung_runtime.MotionController(o);o.ServoTyp='Savox_SB2271SG';o.Modus='Kinematik_Demo';o.Zeit_s=1.5;d.recompute();o.Proxy.execute(o)
parts=[]
for x in d.Objects:
    if not hasattr(x,'MotionRole') or x.BauteilID.startswith('KEEP_'):continue
    mesh=MeshPart.meshFromShape(Shape=x.Shape.copy().cleaned(),LinearDeflection=1.5,AngularDeflection=.8,Relative=False);vs,fs=mesh.Topology
    parts.append(dict(name=x.Name,role=x.MotionRole,rotor=x.Rotor,vertices=[[v.x,v.y,v.z] for v in vs],faces=fs))
with gzip.open(H/'Ausgabe/Meshvorschau.json.gz','wt') as f:json.dump(parts,f,separators=(',',':'))
print('Preview meshes',len(parts),'triangles',sum(len(x['faces']) for x in parts));A.closeDocument(d.Name)
