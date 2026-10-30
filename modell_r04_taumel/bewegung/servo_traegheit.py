#!/usr/bin/env python3
"""Replace just the six servo mass distributions for a candidate flight profile.

M01 bearing/motor interior geometry remains illustrative and is NOT reinterpreted
as a new mass model. All other H01 mass/inertia assumptions remain unchanged.
"""
import os,sys,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')),str(H)]
import FreeCAD as A,bewegung_runtime,MeshPart
from bewegung_runtime import MotionController
source=H/'Ausgabe/Cohexial_R04_M01_Bewegung.FCStd';d=A.openDocument(str(source));ctl=d.getObject('Bewegungssteuerung');ctl.Proxy=MotionController(ctl);ctl.ServoTyp='Savox_SB2271SG';ctl.Modus='Manuell';ctl.Servo_deg=[0]*6;ctl.Rotorwinkel_deg=[0,0];d.recompute();ctl.Proxy.execute(ctl)
parts=[];meshes=[]
for o in d.Objects:
    if getattr(o,'MotionRole',None)!='servo_housing':continue
    ss=o.Shape.Solids;volume=sum(s.Volume for s in ss);cg=[sum(s.Volume*getattr(s.CenterOfMass,a) for s in ss)/volume/1000 for a in ('x','y','z')];J=[[0.]*3 for _ in range(3)];m=.069
    for s in ss:
        r=[getattr(s.CenterOfMass,a)/1000-cg[i] for i,a in enumerate(('x','y','z'))];I=s.MatrixOfInertia;ms=m*s.Volume/volume
        for i in range(3):
            for j in range(3):J[i][j]+=getattr(I,'A%d%d'%(i+1,j+1))*m/volume*1e-6+ms*((sum(v*v for v in r) if i==j else 0)-r[i]*r[j])
    parts.append(dict(name=o.Name,mass_kg=m,cg_m=cg,inertia_cg_kgm2=J))
    mesh=MeshPart.meshFromShape(Shape=o.Shape.copy().cleaned(),LinearDeflection=1,AngularDeflection=.8,Relative=False);vs,fs=mesh.Topology
    meshes.append(dict(name=o.Name,group='body',vertices=[[round(v.x/1000,5),round(v.y/1000,5),round(v.z/1000,5)] for v in vs],faces=fs))
assert len(parts)==6
out={'Savox_SB2271SG_USER':dict(components=parts,mass_g=69,source='User supplied drawing/specification table, 2026-10-30',m01_geometry_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),limitations='Nominal envelope, uniform internal density assumed; bracket/BEC mass absent; 25T spline dimensions and Savox ear bore/thickness unprovided')}
S=H.parent/'simulation';(S/'servo_profiles.json').write_text(json.dumps(out,indent=2));(S/'servo_profiles.js').write_text('globalThis.H01_SERVO_PROFILES='+json.dumps(out)+';\n');(S/'servo_mesh.js').write_text('globalThis.H01_SERVO_MESH='+json.dumps(meshes,separators=(',',':'))+';\n');print('Exported six Savox CAD envelope inertias');A.closeDocument(d.Name)
