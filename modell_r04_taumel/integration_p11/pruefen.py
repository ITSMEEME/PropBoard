#!/usr/bin/env python3
"""P11 exact BRep screening: introduced geometry against the retained full assembly."""
import json,hashlib,sys,math
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
sys.path[:0]=['/usr/lib/freecad-python3/lib',str(H),str(H.parent/'integration_p10')]
import FreeCAD as A,Part
import p11_runtime as RT
P=RT.P;V=A.Vector;SRC=H/'Ausgabe/P11_Gesamtbaugruppe.FCStd'
d=A.openDocument(str(SRC));d.getObject('P09_Animation').Proxy=None
parts=[o for o in d.Objects if hasattr(o,'P09_Rahmen') and not o.BauteilID.startswith('KEEP_')]
new=[o for o in parts if hasattr(o,'P11_Hinweis')];bad=[o.Name for o in parts if not o.Shape.isValid()]
assert all(o.Shape.isValid() for o in new)
assert len([o for o in parts if o.BauteilID=='P11-FUEHRUNGSROLLE-POM'])==4
assert len([o for o in parts if o.BauteilID=='MR85ZZ'])==8
assert not any(o.P09_Rahmen.startswith(('planet:','pinion:')) for o in parts)
proxy={}
def shape(o):
    if o.Name not in bad:return o.Shape
    assert o.BauteilID=='SERVO-SAVOX-SB2270SGP','Unexpected invalid solid'
    if o.Name not in proxy:
        def box(x0,x1,y0,y1,z0,z1):return Part.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))
        s=box(-10.3,30,-25.9,7.77,-10.05,10.05).fuse([box(-17.15,36.85,0,2.2,-10,10),Part.makeCylinder(11.75,.41,V(0,12.39,0),V(0,1,0))]).removeSplitter()
        s.Placement=o.Placement.multiply(o.Shape.SubShapes[0].Placement);proxy[o.Name]=s
    return proxy[o.Name]
def nearby(a,b):
    a=a.BoundBox;b=b.BoundBox
    return not(a.XMax<b.XMin or b.XMax<a.XMin or a.YMax<b.YMin or b.YMax<a.YMin or a.ZMax<b.ZMin or b.ZMax<a.ZMin)
def allowed(a,b):
    ids={a.BauteilID,b.BauteilID};names=[a.Name,b.Name]
    if 'P11-M3-GEWINDESTIFT' in ids and ids&{'P11-ROLLENTRAEGER','P11-EXZENTERBOLZEN-D5'}:return 'Nominales M3-Klemmgewinde / Kontakt am Exzenter'
    if any('P11_Stator_Schraube' in n for n in names) and ids&{'P11-STATOR-BAURAUM','P11-HALTEPLATTE'}:return 'Stator-Befestigungsgewinde / Schraubendurchgang'
    if 'P11-HALTEPLATTE' in ids and any(n.startswith(('P10_Servohalter','P10_Traeger')) for n in names) and any(i.startswith(('ISO','M3')) for i in ids):return 'Wiederverwendete Halteplatten-Befestigung'
    if any(i.startswith('P11-KABEL') for i in ids) and 'P11-STATOR-BAURAUM' in ids:return 'Leitungsende am Statoranschluss'
    if any(i.startswith('P11-KABEL') for i in ids) and 'REF_ESC' in ids:return 'Leitungsende an unveraendertem ESC-Phasenpad'
    return None
report={'source_native_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'introduced_or_changed_parts':len(new),'inherited_invalid_servo_cases':bad,'servo_proxy':'Same measured bounding solids as P10, invalid source STEP is NOT silently certified','collisions':[],'intended_contacts':[],'states':[]}
states=[([0]*6,[0,0])]
for t in [0,.5,1,1.35,2,3.1,4,5,5.65,6,7]:
    s,a=RT.demo(t);states.append((list(s),list(a)))
for servos,angles in [([3,3,3,-3,-3,-3],[0,22.5]),([-3,3,0,3,-3,0],[123,234])]:states.append((servos,angles))
if '--neutral-only' in sys.argv:states=states[:1]
for si,(servos,angles) in enumerate(states):
    RT.apply(d,servos,angles,False);seen=set();count=0
    for a in new:
        sa=shape(a)
        for b in parts:
            # No placement or geometry of fixed parts changes between states.
            if si and a.P09_Rahmen=='fixed' and b.P09_Rahmen=='fixed':continue
            key=tuple(sorted([a.Name,b.Name]))
            if a is b or key in seen:continue
            seen.add(key);sb=shape(b)
            if not nearby(sa,sb):continue
            count+=1;vol=sa.common(sb).Volume
            if vol>1e-5:
                row={'state':si,'a':a.Name,'b':b.Name,'volume_mm3':vol};reason=allowed(a,b)
                if reason:row['reason']=reason;report['intended_contacts'].append(row)
                else:report['collisions'].append(row);print('COLLISION',row,flush=True)
    report['states'].append({'servos':servos,'rotors':angles,'exact_pairs':count});print('state',si,'new collisions',len(report['collisions']),flush=True)
    (H/'Ausgabe/Pruefung_Zwischenstand.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
RT.apply(d,[0]*6,[0,0],False)
clearances=[]
for lvl,l in [('Oben',0),('Unten',1)]:
    track=d.getObject('P11_Laufbahneinsatz_'+lvl)
    for k in range(2):
        roller=d.getObject(f'P11_Fuehrungsrolle_{lvl}_{k}');gap=track.Shape.distToShape(roller.Shape)[0]
        assert .045<gap<.055,gap
        clearances.append({'level':lvl,'roller':k,'radial_gap_mm':gap,'roller_rpm_at_3000':3000*RT.RATIO})
    carrier=d.getObject('Rotor_oben_1' if l==0 else 'Rotor_unten_1');stator=d.getObject('P11_Stator_Bauraum_'+lvl);mag=d.getObject('P11_Motorrotor_Bauraum_'+lvl)
    assert stator.Shape.distToShape(mag.Shape)[0]>.49
    assert stator.Shape.distToShape(carrier.Shape)[0]>.49
report['guide_clearances']=clearances;report['complete_motion_screen']=len(states)==14
report['status']=('PASS' if len(states)==14 else 'PASS_NEUTRAL_ONLY') if not report['collisions'] else 'FAIL_COLLISIONS'
report['limitations']=['No strength, bearing life, thermal or manufacturing release','Full original P10 checks remain historical; this run checks all introduced geometry against the retained full assembly in 14 states','Motor geometry is an envelope, not a selected commercial motor']
(H/'Ausgabe/Pruefbericht_P11.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
(H/'Ausgabe/Pruefung_Zwischenstand.json').unlink(missing_ok=True)
print(report['status'],len(report['collisions']),'collisions',flush=True)
if report['collisions']:raise SystemExit(1)
