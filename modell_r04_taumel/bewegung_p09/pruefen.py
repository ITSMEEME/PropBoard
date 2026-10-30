#!/usr/bin/env python3
"""Check complete P09 native chain endpoints and selected actual BRep contacts."""
import sys,os,json,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')),str(H)]
import FreeCAD as A,Part
import voll_runtime as R
V=A.Vector
path=H/'Ausgabe/P09_Servo_bis_Rotorblatt_Bewegung.FCStd';d=A.openDocument(str(path));ctl=d.getObject('P09_Animation');ctl.Proxy=R.Controller(ctl)
parts=[o for o in d.Objects if hasattr(o,'P09_Rahmen')];byframe={}
for o in parts:byframe.setdefault(o.P09_Rahmen,[]).append(o)
links=[o for o in parts if o.P09_Rahmen.startswith('link:')];assert len(links)==112
outputs=[o for o in parts if o.P09_Rahmen.startswith('output:')];assert len(outputs)==6
assert len([o for o in parts if getattr(o,'BauteilID','')=='P09_Axialschraube'])==16
assert all(o.Shape.isValid() for o in parts if getattr(o,'BauteilID','')!='SERVO-SAVOX-SB2270SGP')
# Existing historical flight angles are only mechanical input samples, not new
# SB2270 flight performance evidence.
old=json.loads((H.parent/'bewegung/Bewegungsdaten.json').read_text());states=[]
for i in range(161):
    t=i*.05;servos,angles=R.demo(t if i<160 else 0);states.append((f'Demo_{i}',servos,angles))
for name,series in old.items():
    fs=series['frames']
    for i in (0,len(fs)//4,len(fs)//2,3*len(fs)//4,len(fs)-1):
        f=fs[i];states.append((name+'_'+str(i),f['servoDeg'],f['angles']))
max_closure=0.;max_native=0.;pitch_min=999;pitch_max=-999;native_states=0

def actual_origin(o):return o.Placement.multiply(o.P09_Neutralrahmen).Base

def sphere_centres(o):
    return [f.Surface.Center for f in o.Shape.Faces if isinstance(f.Surface,Part.Sphere) and abs(f.Surface.Radius-2.4)<1e-6]
for n,(name,servos,angles) in enumerate(states):
    r=R.state(servos,angles);max_closure=max(max_closure,r['max_error']);pitch_min=min(pitch_min,min(x for row in r['pitches'] for x in row));pitch_max=max(pitch_max,max(x for row in r['pitches'] for x in row))
    if n%8==0 or n>=161:
        R.apply(d,servos,angles);native_states+=1
        assert list(ctl.Servo_deg)==list(servos) and list(ctl.Rotor_deg)==list(angles)
        for endpoint in r['endpoints']:
            l,j=endpoint['rotor'],endpoint['blade']
            for suffix,target in [('stud_low',endpoint['low']),('stud_high',endpoint['high'])]:
                o=d.getObject(f'P09_R{l}_B{j}_{suffix}');centres=sphere_centres(o);assert centres
                max_native=max(max_native,min((c-target).Length for c in centres))
            low=actual_origin(d.getObject(f'P09_R{l}_B{j}_body_low'));high=actual_origin(d.getObject(f'P09_R{l}_B{j}_body_high'))
            max_native=max(max_native,(low-endpoint['low']).Length,(high-endpoint['high']).Length,abs((high-low).Length-15))
        for l in range(2):
          for i in range(3):
            output=byframe[f'output:{l}:{i}'][0];horn=byframe[f'p08:{l}:{i}:horn'][0]
            max_native=max(max_native,(actual_origin(output)-actual_origin(horn)).Length)
assert max_closure<1e-6 and max_native<1e-6,(max_closure,max_native)
# Choose four representative, non-aliased rotor phases for actual new contacts.
contact_states=[('Neutral',[0]*6,[0,0])]+[(f'Demo_t{t}',*R.demo(t)) for t in (1.35,3.1,5.65)]
collisions=[];checks=0

def overlap(a,b):
    global checks
    checks+=1;aa=a.BoundBox;bb=b.BoundBox
    if aa.XMax<bb.XMin or bb.XMax<aa.XMin or aa.YMax<bb.YMin or bb.YMax<aa.YMin or aa.ZMax<bb.ZMin or bb.ZMax<aa.ZMin:return 0.
    return a.common(b).Volume

def record(name,a,b,tag=None):
    volume=overlap(a.Shape,b.Shape)
    if volume>1e-3:collisions.append(dict(state=name,a=a.Name,b=b.Name,volume_mm3=volume,interface=tag or 'new_blade_linkage'))
for name,servos,angles in contact_states:
    R.apply(d,servos,angles)
    for l in range(2):
        ring=next(o for o in byframe[f'swashrot:{l}'] if getattr(o,'BauteilID','')=='TM-TAUMEL-DREHRING')
        carrier=d.getObject(f'P09_Blattgelenktraeger_R{l}')
        bearing=next(o for o in byframe[f'swashrot:{l}'] if getattr(o,'BauteilID','')=='LAGER-6809')
        hub=next(o for o in byframe[f'rotor:{l}'] if getattr(o,'BauteilID','')=='TM-NABE')
        driver=next(o for o in byframe[f'rotor:{l}'] if getattr(o,'BauteilID','')=='MITNEHMERSTIFT-D3')
        record(name,ring,bearing,'actual_bearing_seat');record(name,carrier,bearing,'bearing_retainer');record(name,driver,ring,'drive_pin_slot')
        for j in range(8):
            get=lambda role:d.getObject(f'P09_R{l}_B{j}_{role}')
            horn=next(o for o in byframe[f'blade:{l}:{j}'] if getattr(o,'MotionRole','')=='pitch_horn')
            for a,b in [('stud_low','body_low'),('stud_low','cap_low'),('stud_high','body_high'),('stud_high','cap_high'),('rod','body_low'),('rod','body_high')]:record(name,get(a),get(b))
            for role in ('body_low','cap_low'):
                record(name,get(role),horn);record(name,get(role),hub)
            for role in ('body_high','cap_high'):
                record(name,get(role),ring);record(name,get(role),carrier);record(name,get(role),bearing)
            record(name,get('stud_low'),horn);record(name,get('stud_high'),carrier)
            record(name,get('Axialscheibe'),horn);record(name,get('Axialschraube'),get('Gewindeeinsatz'))
    print('Contacts',name,'done',checks,'interferences',len(collisions),flush=True)
# Invalid input must never leave half the assembly updated.
R.apply(d,[0]*6,[0,0]);before=[o.Placement.toMatrix().A for o in parts]
try:R.apply(d,[float('nan')]*6,[0,0]);raise AssertionError('Invalid input accepted')
except ValueError:pass
assert before==[o.Placement.toMatrix().A for o in parts]
assert all(o.Placement.Base.Length<1e-6 and abs(o.Placement.Rotation.Angle)<1e-7 for o in parts if o.P09_Rahmen!='fixed')
A.closeDocument(d.Name)
report=dict(status='CLOSED_CHAIN_PASS_CONTACT_REVIEW_REQUIRED' if collisions else 'CLOSED_CHAIN_PASS_SELECTED_CONTACTS_CLEAR_NOT_RELEASE',native_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),numerical_states=len(states),native_states=native_states,max_closure_error_mm=max_closure,max_actual_sphere_centre_error_mm=max_native,pitch_range_deg=[pitch_min,pitch_max],selected_contact_states=len(contact_states),actual_brep_checks=checks,collisions=collisions,invalid_input_atomic_rejection=True,neutral_return_pass=True,flight_revalidated=False,manufacturing_release=False,scope='Servo spline/horn axes,16 actual captured blade-joint endpoint pairs and selected bearing/retainer/driver/root interfaces. Not all-pairs continuous collision or structural validation; invalid OEM case retained and servo mount brackets remain open.')
(H/'Ausgabe/Bewegungspruefung_P09.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='collisions'},indent=2));print('COLLISIONS',len(collisions));print(json.dumps(collisions[:16],indent=2))
