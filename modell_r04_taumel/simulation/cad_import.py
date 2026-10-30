#!/usr/bin/env python3
"""Reproducible CAD-to-flight mass tensor import. Run with official FreeCAD Python."""
import os,sys,json,hashlib,math
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
sys.path.insert(0,os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')))
sys.path.insert(0,str(H.parent/'halterungen'))
import FreeCAD as App
import MeshPart
source=H.parent/'halterungen/Ausgabe/R04_Taumelmodell_Halterungen_H01.FCStd'
d=App.openDocument(str(source));items=[];mesh=[]
# Represent uniformly distributed component mass, preserving CAD volume and tensor.
def add(name,m,solids,group):
    volume=sum(s.Volume for s in solids);cg=[sum(s.Volume*getattr(s.CenterOfMass,a) for s in solids)/volume/1000 for a in ('x','y','z')]
    J=[[0.]*3 for _ in range(3)]
    for s in solids:
        ms=m*s.Volume/volume;c=[getattr(s.CenterOfMass,a)/1000-cg[i] for i,a in enumerate(('x','y','z'))];mat=s.MatrixOfInertia
        for i in range(3):
            for j in range(3):J[i][j]+=getattr(mat,'A%d%d'%(i+1,j+1))*m/volume*1e-6+ms*((sum(v*v for v in c) if i==j else 0)-c[i]*c[j])
    items.append(dict(name=name,mass_kg=m,cg_m=cg,inertia_cg_kgm2=J,group=group))
for o in d.Objects:
    if not hasattr(o,'BauteilID') or o.BauteilID.startswith('KEEP_'):continue
    m=float(o.Masse_g)/1000;ident=o.BauteilID
    if ident=='REF_AKKU':m=.254
    elif ident=='REF_ESC':m=.016
    elif ident=='REF_FC':m=.010
    elif ident=='REF_POLSTER':continue # included below in 10 g straps/pads budget
    if m<=0:continue
    group='upper' if o.Name.startswith('Rotor_oben_') else 'lower' if o.Name.startswith('Rotor_unten_') else 'body'
    add(o.Name,m,o.Shape.Solids,group)
    items[-1]['part_id']=ident
    coarse=MeshPart.meshFromShape(Shape=o.Shape.copy().cleaned(),LinearDeflection=1.5,AngularDeflection=0.8,Relative=False)
    vs,fs=coarse.Topology
    # Native surface mesh for visual inspection, not a collision solver.
    mesh.append({'name':o.Name,'group':group,'vertices':[[round(v.x/1000,5),round(v.y/1000,5),round(v.z/1000,5)] for v in vs], 'faces':fs})
# Missing budget masses have explicit, reviewable spatial assumptions, not silently zero inertia.
for name,m,c,size in [('receiver',.003,[0,0,.135],[.025,.015,.008]),('wiring',.045,[0,0,0],[.09,.09,.18]),('heads_nuts',.015,[0,0,-.07],[.07,.06,.20]),('straps_pads',.010,[0,0,-.145],[.09,.05,.05])]:
    J=[[0.]*3 for _ in range(3)]
    for i in range(3):J[i][i]=m*sum(size[j]**2 for j in range(3) if j!=i)/12
    items.append(dict(name=name,mass_kg=m,cg_m=c,inertia_cg_kgm2=J,group='assumed'))
M=sum(x['mass_kg'] for x in items);cg=[sum(x['mass_kg']*x['cg_m'][i] for x in items)/M for i in range(3)];J=[[0.]*3 for _ in range(3)]
for x in items:
    c=[x['cg_m'][i]-cg[i] for i in range(3)]
    for i in range(3):
        for j in range(3):J[i][j]+=x['inertia_cg_kgm2'][i][j]+x['mass_kg']*((sum(v*v for v in c) if i==j else 0)-c[i]*c[j])
rotor=[]
for group in ('upper','lower'):
    parts=[x for x in items if x['group']==group]
    rotor.append(sum(x['inertia_cg_kgm2'][2][2]+x['mass_kg']*(x['cg_m'][0]**2+x['cg_m'][1]**2) for x in parts))
par=json.loads((H.parent/'cad/parameter.json').read_text())
out=dict(revision='H01',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),mass_kg=M,cg_m=cg,inertia_cg_kgm2=J,rotor_spin_inertia_kgm2=rotor,components=items,geometry=par,
 assumptions=['CAD mass attributes, homogeneous effective infill; no measured mass distribution','ESC/FC 16/10 g split is assumed within known 26 g total','Missing receiver/wiring/fasteners/straps spatial distributions explicitly assumed','Existing 9 g servo placeholders; no real servo brackets/BEC mass included'])
budget=json.loads((H.parent/'halterungen/Ausgabe/Geometriepruefung_H01.json').read_text())['assembly']['mass_budget']['total_nominal_g']/1000
assert abs(M-budget)<1e-7,(M,budget)
(H/'modell_h01.json').write_text(json.dumps(out,indent=2));(H/'modell_h01.js').write_text('globalThis.H01_MODEL='+json.dumps(out,separators=(',',':'))+';\n')
(H/'cad_mesh.js').write_text('globalThis.H01_MESH='+json.dumps(mesh,separators=(',',':'))+';\n')
print(json.dumps({k:out[k] for k in ('mass_kg','cg_m','inertia_cg_kgm2','rotor_spin_inertia_kgm2')},indent=2));print('mesh triangles',sum(len(x['faces']) for x in mesh))
