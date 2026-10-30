#!/usr/bin/env python3
"""Exact closure plus selected BRep contacts of the P08 linkage, not full release."""
import sys,os,json,hashlib,math
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')),str(H)]
import FreeCAD as A,Part
import runtime as R
import geometrie as G
P=H/'Ausgabe/P08_Isolierte_Anschlussbewegung.FCStd';d=A.openDocument(str(P));parts=[o for o in d.Objects if hasattr(o,'P08_Rolle')];assert len(parts)==92
assert all(o.Shape.isValid() for o in parts)
frames=json.loads((H.parent/'bewegung/Bewegungsdaten.json').read_text());states=[]
for name,series in frames.items():
    f=series['frames']
    for index in (0,len(f)//4,len(f)//2,3*len(f)//4,len(f)-1):states.append((name+'_'+str(index),f[index]['servoDeg']))
# Azimuth does not alter stationary servo rods. Add joint command combinations.
for deg in (10,-10,15,-15):states.append(('Alle_'+str(deg),[deg]*6))
for i in range(6):
    for deg in (-15,15):
        v=[0]*6;v[i]=deg;states.append((f'Einzel_{i}_{deg}',v))
max_error=0.;max_angle=0.;worst=None
for name,degrees in states:
    _,err,angles=R.transforms(degrees);max_error=max(err,max_error)
    if max(angles)>max_angle:max_angle=max(angles);worst=(name,degrees)
assert max_error<1e-6
# Dynamic neck clearance/capture with exact solids. Ball/cap interpenetration is not
# waived as a 'joint contact': the sphere has intentional radial clearance .03.
selected=[('Neutral',[0]*6),worst]+states[-12:]
collisions=[];checks=0

def overlap(a,b):
    global checks
    checks+=1
    aa,bb=a.BoundBox,b.BoundBox
    if aa.XMax<bb.XMin or bb.XMax<aa.XMin or aa.YMax<bb.YMin or bb.YMax<aa.YMin or aa.ZMax<bb.ZMin or bb.ZMax<aa.ZMin:return 0.
    return a.common(b).Volume

for name,degrees in selected:
    R.update(d,degrees)
    for l in range(2):
      for i in range(3):
        objs={o.P08_Rolle:o for o in parts if o.P08_Rotor==l and o.P08_Index==i}
        pairs=[('ball_low','body_low'),('ball_low','cap_low'),('ball_high','body_high'),('ball_high','cap_high'),('rod','body_low'),('rod','body_high'),('rod','jam_low'),('rod','jam_high'),('horn','ball_high'),('horn','clamp_bolt'),('horn','clamp_nut'),('horn','horn_nut')]
        for x,y in pairs:
            vol=overlap(objs[x].Shape,objs[y].Shape)
            if vol>1e-3:collisions.append(dict(state=name,rotor=l,servo=i,a=x,b=y,volume_mm3=vol))
# Check rod/socket travel through actual modified motor-plate ports at a subset.
full=A.openDocument(str(H/'Ausgabe/P08_Baugruppe_Servoverbindung_ENTWURF.FCStd'))
plates=[o for o in full.Objects if getattr(o,'BauteilID','')=='TM-HALTEPLATTE']
for name,degrees in selected[:2]+selected[-2:]:
    R.update(d,degrees)
    for o in parts:
        if o.P08_Rolle not in ('body_low','body_high','cap_low','cap_high','rod','jam_low','jam_high'):continue
        plate=next(p for p in plates if p.Name.startswith('Oben_' if o.P08_Rotor==0 else 'Unten_'))
        vol=overlap(o.Shape,plate.Shape)
        if vol>1e-3:collisions.append(dict(state=name,rotor=o.P08_Rotor,servo=o.P08_Index,a=o.P08_Rolle,b='Motorplatte_D14',volume_mm3=vol))
A.closeDocument(full.Name)
# Reopen movement returns precisely to saved neutral shape frames.
R.update(d,[0]*6)
assert all(o.Placement.Base.Length<1e-6 and abs(o.Placement.Rotation.Angle)<1e-7 for o in parts)
A.closeDocument(d.Name)
report=dict(status='KINEMATIK_OK_KONTAKTE_OFFEN' if collisions else 'KINEMATIK_OK_AUSGEWAEHLTE_KONTAKTE_FREI_KEINE_FREIGABE',native_sha256=hashlib.sha256(P.read_bytes()).hexdigest(),states=len(states),contact_states=len(selected),max_closure_error_mm=max_error,max_joint_angle_deg=max_angle,selected_brep_checks=checks,collisions=collisions,neutral_return_pass=True,manufacturing_release=False,scope='Actual detailed linkage solids, neck/socket clearance, nominal threaded fastener spaces and selected modified-plate contacts. Not all assembly pairs, continuous full-range, OEM servo collision or strength validation; original servo invalid.')
(H/'Ausgabe/Bewegungspruefung_P08.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='collisions'},indent=2));print('COLLISIONS',len(collisions));print(json.dumps(collisions[:12],indent=2))
