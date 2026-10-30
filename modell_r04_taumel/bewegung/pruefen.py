#!/usr/bin/env python3
"""Reopen native assembly, verify closed motions, screen selected real BRep contacts."""
import sys,os,json,math,collections,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')),str(H)]
import FreeCAD as A
from bewegung_runtime import MotionController,apply,local_world,horn_ball,DEG
source=H/'Ausgabe/Cohexial_R04_M01_Bewegung.FCStd';d=A.openDocument(str(source));ctl=d.getObject('Bewegungssteuerung');ctl.Proxy=MotionController(ctl)
parts=[o for o in d.Objects if hasattr(o,'MotionRole') and not o.BauteilID.startswith('KEEP_')];roles=collections.Counter(o.MotionRole for o in parts)
required={'blade':16,'pitch_horn':16,'blade_link':16,'servo_horn':6,'servo_link':6,'servo_shaft':6,'pinion':2,'motor_bell':2,'motor_shaft':2,'bearing_inner':6,'bearing_outer':6,'bearing_cage':6,'bearing_ball':120}
for role,count in required.items():assert roles[role]==count,(role,roles[role],count)
assert all(o.Shape.isValid() for o in parts)
frames=json.loads(ctl.WiedergabeJSON);states=[]
for scenario in frames:
    f=frames[scenario]['frames']
    for index in (0,len(f)//4,len(f)//2,3*len(f)//4,len(f)-1):states.append((scenario,f[index]))
# A complete rotor turn with a fixed swash tilt tests actual cyclic pitching.
demo=frames['Kinematik_Demo']['frames'][55]
for angle in range(0,360,15):states.append(('Rotation_360',dict(demo,angles=[angle,angle])))
max_error=0.;sphere_error=0.;collisions=[];pair_checks=0;gear_checks=0
# Small, named set of meaningful candidate interfaces. Deliberately not a blanket collision clearance.
def overlap(a,b):
    global pair_checks
    pair_checks+=1
    aa,bb=a.Shape.BoundBox,b.Shape.BoundBox
    if aa.XMax<bb.XMin or bb.XMax<aa.XMin or aa.YMax<bb.YMin or bb.YMax<aa.YMin or aa.ZMax<bb.ZMin or bb.ZMax<aa.ZMin:return 0
    return a.Shape.common(b.Shape).Volume
for variant in ('Savox_SB2271SG','KST_X15_755X_760us'):
    ctl.ServoTyp=variant;ctl.Modus='Manuell';d.recompute();ctl.Proxy.execute(ctl)
    for number,(name,f) in enumerate(states):
        info=apply(d,ctl,f['servoDeg'],f['angles']);max_error=max(max_error,info['max_link_error_mm'])
        for l,s in enumerate((1,-1)):
            by=lambda role:[o for o in parts if o.MotionRole==role and o.Rotor==l]
            for ball in by('blade_ball'):
                k=ball.MotionIndex;a=(f['angles'][l]+45*k)*DEG;pos=local_world(s).multVec(A.Vector(*horn_ball(info['pitches_deg'][l][k]*DEG,a,s)))
                actual=ball.Shape.Solids[0].CenterOfMass;sphere_error=max(sphere_error,(actual-pos).Length)
            # Check all servo interfaces and selected lower mechanism contacts at representative poses.
            if number<5 or number in (len(states)-1,):
                plate=d.getObject(('Oben_feststehend_' if l==0 else 'Unten_feststehend_')+'9')
                plates=[o for o in parts if o.BauteilID=='TM-HALTEPLATTE' and o.Name.startswith('Oben_' if l==0 else 'Unten_')]
                pairs=[]
                for horn in by('servo_horn'):
                    pairs += [(horn,h) for h in by('servo_housing')]
                for tip in by('servo_tip'):pairs += [(tip,h) for h in by('servo_housing')]
                for rod in by('servo_link'):pairs += [(rod,p) for p in plates]+[(rod,h) for h in by('servo_housing')]
                for pin in [o for o in by('rotor') if o.BauteilID=='MITNEHMERSTIFT-D3']:pairs += [(pin,r) for r in by('swash_rotating')]
                for pin in [o for o in by('swash_stationary') if o.BauteilID=='FUEHRUNGSSTIFT-D3']:pairs += [(pin,p) for p in plates]
                lid=[o for o in by('rotor') if o.BauteilID=='TM-DECKEL-ZAHNKRANZ-130'][0]
                pairs += [(rod,lid) for rod in by('blade_link')]
                pairs += [(bell,st) for bell in by('motor_bell') for st in by('motor_stator')]
                for a,b in pairs:
                    vol=overlap(a,b)
                    if vol>1e-3:collisions.append(dict(variant=variant,state=name,frame=number,a=a.Name,b=b.Name,volume_mm3=vol))
            if variant=='Savox_SB2271SG' and number in (0,25,26,27):
                lid=[o for o in by('rotor') if o.BauteilID=='TM-DECKEL-ZAHNKRANZ-130'][0];pinion=by('pinion')[0];vol=overlap(lid,pinion);gear_checks+=1
                if vol>1e-3:collisions.append(dict(variant=variant,state=name,frame=number,a=lid.Name,b=pinion.Name,volume_mm3=vol,interface='gear_mesh'))
assert max_error<1e-6 and sphere_error<1e-6,(max_error,sphere_error)
# Save/reopen proves persistence and pure-Python proxy restoration, using a temporary copy.
ctl.ServoTyp='Savox_SB2271SG';ctl.Modus='Kinematik_Demo';ctl.Zeit_s=1.25;d.recompute();before=next(o for o in parts if o.MotionRole=='servo_horn').Placement.toMatrix().A
import tempfile
with tempfile.TemporaryDirectory(prefix='m01-reopen-') as tmp:
    p=Path(tmp)/'check.FCStd';d.saveAs(str(p));A.closeDocument(d.Name);d=A.openDocument(str(p));ctl=d.getObject('Bewegungssteuerung');ctl.Proxy=MotionController(ctl);d.recompute();ctl.Proxy.execute(ctl)
    after=next(o for o in d.Objects if getattr(o,'MotionRole',None)=='servo_horn').Placement.toMatrix().A
    assert max(abs(a-b) for a,b in zip(before,after))<1e-8
    A.closeDocument(d.Name)
report=dict(status='KINEMATICS_PASS_INTERFACES_REQUIRE_REVIEW' if collisions else 'KINEMATICS_PASS_SELECTED_CONTACTS_CLEAR_NOT_RELEASE',native_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),roles=dict(roles),states_per_variant=len(states),variants=2,max_fixed_link_error_mm=max_error,max_native_ball_position_error_mm=sphere_error,native_reopen_pass=True,pair_checks=pair_checks,gear_checks=gear_checks,collisions=collisions,coverage='Named servo/housing/plate, driver/guide, blade-link/deck, motor bell/stator interfaces plus 8 gear mesh positions. Not an all-pairs full-range collision or strength proof.',open_mounting='Actual servo brackets, horn-to-spline fastener and complete ball-joint seats/axial locks remain undefined')
(H/'Ausgabe/Validierung_M01.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('roles','collisions')},indent=2));print('interferences',len(collisions))
