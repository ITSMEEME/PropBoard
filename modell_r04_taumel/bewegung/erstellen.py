#!/usr/bin/env python3
"""Generate M01 editable native motion assembly without changing the H01 source."""
import sys,os,json,collections
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
sys.path[:0]=[os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')),str(H.parent/'cad'),str(H.parent/'halterungen')]
import FreeCAD as App,Part
import erstellen as C
from bewegung_runtime import MotionController,placement
V=App.Vector;OUT=H/'Ausgabe';OUT.mkdir(exist_ok=True)
# The CAD directory precedes this folder so 'erstellen' imports the CAD templates.
d=App.openDocument(str(H.parent/'halterungen/Ausgabe/R04_Taumelmodell_Halterungen_H01.FCStd'));d.Label='Cohexial Study – M01 bewegliche Baugruppe (Schema, keine Freigabe)'
all_original=list(d.Objects)
for o in all_original:
    if hasattr(o,'BauteilID'):
        o.addProperty('App::PropertyString','MotionRole');o.MotionRole='fixed'
        o.addProperty('App::PropertyPlacement','RestPlacement');o.RestPlacement=o.Placement
        o.addProperty('App::PropertyInteger','Rotor');o.addProperty('App::PropertyInteger','MotionIndex')
        o.addProperty('App::PropertyString','Bewegungsstatus');o.Bewegungsstatus='H01 Basis; M01 keine neue Massen- oder Fertigungsfreigabe'

def configure(o,shape,role,l,index=0):
    # A compound keeps any template's internal placement while giving the parent
    # an identity placement suitable for the animation solver.
    o.Shape=Part.makeCompound([shape]);o.Placement=App.Placement();o.MotionRole=role;o.Rotor=l;o.MotionIndex=index
    return o

def new(name,shape,role,l,index=0):
    o=d.addObject('Part::Feature',name);o.addProperty('App::PropertyString','BauteilID');o.BauteilID='M01_'+name
    o.addProperty('App::PropertyString','MotionRole');o.addProperty('App::PropertyPlacement','RestPlacement');o.addProperty('App::PropertyInteger','Rotor');o.addProperty('App::PropertyInteger','MotionIndex')
    o.addProperty('App::PropertyString','Bewegungsstatus');o.Bewegungsstatus='Funktionsschema; keine Herstellergeometrie, Masse oder Fertigungsfreigabe'
    return configure(o,shape,role,l,index)

def ring(ri,ro,z,h):return C.ring(ri,ro,z,h)

def bearing(o,l,which):
    main=which<2;ri,ro,B,rp,rb,count=(15,21,7,18,1.2,18) if main else (22.52,28.98,7,25.75,1.3,24)
    start=-B/2 if not main else 0
    # Local bearing origin is at axial centre. Main bearing z bases are applied below.
    inner=ring(ri,rp-rb,-B/2,B);outer=ring(rp+rb,ro,-B/2,B)
    configure(o,outer,'bearing_outer',l,which*100)
    new(f'L{l}_B{which}_Innenring',inner,'bearing_inner',l,which*100)
    cage=ring(rp-rb+.1,rp+rb-.1,-.35,.7)
    import math
    holes=[C.cyl(rb+.15,2,(rp*math.cos(j*2*math.pi/count),rp*math.sin(j*2*math.pi/count),-1)) for j in range(count)]
    cage=cage.cut(Part.makeCompound(holes));new(f'L{l}_B{which}_Kaefig',cage,'bearing_cage',l,which*100)
    for j in range(count):new(f'L{l}_B{which}_Kugel{j}',Part.makeSphere(rb),'bearing_ball',l,which*100+j)

kine=json.loads((H.parent/'simulation/kinematik.json').read_text())
for l in range(2):
    pre='Rotor_oben_' if l==0 else 'Rotor_unten_';spre='Oben_feststehend_' if l==0 else 'Unten_feststehend_';sign=1 if l==0 else -1
    counts=collections.Counter()
    for o in all_original:
        if not hasattr(o,'BauteilID') or not(o.Name.startswith(pre) or o.Name.startswith(spre)):continue
        ident=o.BauteilID;n=counts[(o.Name.startswith(pre),ident)];counts[(o.Name.startswith(pre),ident)]+=1
        if o.Name.startswith(pre):
            if ident=='TM-NABE':configure(o,C.hub_shape(),'rotor',l)
            elif ident=='TM-DECKEL-ZAHNKRANZ-130':configure(o,C.lid_shape(sign)[0],'rotor',l)
            elif ident=='MITNEHMERSTIFT-D3':configure(o,C.driver_pin(sign),'rotor',l)
            elif ident=='TM-FLUEGEL':configure(o,C.blade_shape(),'blade',l,n)
            elif ident=='TM-PITCHHEBEL':configure(o,C.horn_shape(sign),'pitch_horn',l,n)
            elif ident=='STIFT-D2x18':configure(o,C.pins()[n%2],'hub_pin',l,n//2)
            elif ident=='KUGELBOLZEN-M2':configure(o,Part.makeSphere(2.4),'blade_ball' if n%2==0 else 'ring_ball',l,n//2)
            elif ident=='STEUERSTANGE':configure(o,C.cyl(1.25,15-5.4),'blade_link',l,n)
            elif ident=='LAGER-6806':bearing(o,l,n)
            elif ident=='TM-TAUMEL-DREHRING':configure(o,C.swash_rotating(),'swash_rotating',l)
        else:
            if ident=='TM-TAUMEL-GLEITKUGEL':configure(o,C.swash_sleeve(),'sleeve',l)
            elif ident=='TM-TAUMEL-INNENRING':configure(o,C.swash_stationary(),'swash_stationary',l)
            elif ident=='LAGER-6809':bearing(o,l,2)
            elif ident=='KUGELBOLZEN-M2':configure(o,C.swash_stat_hardware()[n][0],'swash_stationary',l,n)
            elif ident=='FUEHRUNGSSTIFT-D3':configure(o,C.swash_stat_hardware()[-1][0],'swash_stationary',l,3)
            elif ident=='SERVOSTANGE':configure(o,C.cyl(1,kine[l]['link_lengths_mm'][n]-5.4),'servo_link',l,n)
            elif ident=='RITZEL-M1-Z20':
                shp,_=C.spur(20,5.5,2.5,9);shp.translate(V(0,0,11));configure(o,shp,'pinion',l)
            elif ident=='MOTOR-ECO2-2306':
                stator=ring(2.7,11.5,30,10).fuse(ring(2.7,14,40,3));configure(o,stator,'motor_stator',l)
                bell=ring(12,14,25.5,14.2).fuse(ring(2.5,14,24,1.5));new(f'L{l}_Motor_Glocke_Schema',bell,'motor_bell',l)
            elif ident=='MOTORWELLE-M5':configure(o,C.cyl(2.5,32,(0,0,11)),'motor_shaft',l)
            elif ident=='SERVO-PLATZHALTER':
                # Tangential shaft, horn plane y=0; housing is behind that plane.
                body=C.box(52.2,64.4,-25.8,-3,47,69.5);configure(o,body,'servo_housing',l,n)
                # Horn in x/z plane, about a tangential y-axis, inward-pointing at neutral.
                horn=C.box(-8,0,-.8,.8,-2,2).fuse(C.cyl(2,1.6,(0,-.8,0),(0,1,0))).fuse(C.cyl(2,1.6,(-8,-.8,0),(0,1,0)))
                horn=horn.cut(C.cyl(1.6,3,(0,-1.5,0),(0,1,0)))
                new(f'L{l}_Servo{n}_Horn_8mm',horn,'servo_horn',l,n)
                new(f'L{l}_Servo{n}_Abtrieb',C.cyl(1.5,4, (0,-3,0),(0,1,0)),'servo_shaft',l,n)
                new(f'L{l}_Servo{n}_Kugel',Part.makeSphere(2.4),'servo_tip',l,n)
    # Group new internals in the corresponding rotor section for navigation.
    group=d.getObject('M01_Rotor_'+str(l)) or d.addObject('App::DocumentObjectGroup','M01_Rotor_'+str(l))
    for o in d.Objects:
        if hasattr(o,'MotionRole') and o.MotionRole!='fixed' and o.Rotor==l:group.addObject(o)

control=d.addObject('App::FeaturePython','Bewegungssteuerung');MotionController(control)
for typ,name in [('App::PropertyEnumeration','Modus'),('App::PropertyFloat','Zeit_s'),('App::PropertyFloatList','Servo_deg'),('App::PropertyFloatList','Rotorwinkel_deg'),('App::PropertyString','KinematikJSON'),('App::PropertyString','WiedergabeJSON'),('App::PropertyFloat','MaxGestangefehler_mm'),('App::PropertyString','Hinweis'),('App::PropertyEnumeration','ServoTyp'),('App::PropertyString','ServodatenJSON')]:control.addProperty(typ,name)
control.Modus=['Manuell','Kinematik_Demo','Savox_7_4V_Manoever','Savox_6_0V_Boee','Savox_7_4V_Reibung_0_20'];control.Modus='Manuell';control.Servo_deg=[0]*6;control.Rotorwinkel_deg=[0,0]
control.ServoTyp=['Savox_SB2271SG','KST_X15_755X_760us'];control.ServoTyp='Savox_SB2271SG';control.ServodatenJSON=(H.parent/'messdaten/Servodaten_Nutzer.json').read_text()
control.KinematikJSON=json.dumps(kine);control.WiedergabeJSON=(H/'Bewegungsdaten.json').read_text();control.Hinweis='M01 Kinematik und H01-Physikwiedergabe. Herstellergeometrie von Servos/Motor-/Lagerinnerem offen. Keine Kraft-/Kontaktloesung in FreeCAD.'
control.setEditorMode('ServodatenJSON',2);control.setEditorMode('MaxGestangefehler_mm',1);control.setEditorMode('KinematikJSON',2);control.setEditorMode('WiedergabeJSON',2)
d.recompute();control.Proxy.execute(control)
assert all(o.Shape.isValid() for o in d.Objects if hasattr(o,'MotionRole'))
counts=collections.Counter(o.MotionRole for o in d.Objects if hasattr(o,'MotionRole'))
if App.GuiUp:
    for o in d.Objects:
        if hasattr(o,'MotionRole'):
            o.ViewObject.ShapeColor=(.18,.64,.77) if o.Rotor==0 and o.MotionRole!='fixed' else (.88,.53,.26) if o.MotionRole!='fixed' else (.65,.7,.75)
            o.ViewObject.Visibility=not(o.BauteilID.startswith('KEEP_'))
d.Comment=control.Hinweis
d.saveAs(str(OUT/'Cohexial_R04_M01_Bewegung.FCStd'))
Part.export([o for o in d.Objects if hasattr(o,'MotionRole') and not o.BauteilID.startswith('KEEP_')],str(OUT/'Cohexial_R04_M01_Neutral.step'))
(OUT/'Inventar.json').write_text(json.dumps(dict(status='KINEMATIC_SCHEMATIC_NOT_MANUFACTURER_COMPLETE',roles=dict(counts),max_link_error_mm=control.MaxGestangefehler_mm,servo_geometry='Nominal envelopes from supplied Savox/KST drawings; Savox ear bore/thickness and spline dimensions remain unprovided'),indent=2))
print(json.dumps(dict(counts),indent=2));App.closeDocument(d.Name)
