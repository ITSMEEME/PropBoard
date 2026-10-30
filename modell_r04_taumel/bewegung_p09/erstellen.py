#!/usr/bin/env python3
import sys,os,json,math,hashlib,importlib.util
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')),str(H)]
import FreeCAD as A,Part
import geometrie_p09 as G
import voll_runtime as R
V=A.Vector;OUT=H/'Ausgabe'
spec=importlib.util.spec_from_file_location('_p09_templates',H.parent/'cad/erstellen.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
C.HO['r_center']=33;C.LID['driver_angle']=7;C.LID['slot']=[9,12];C.LID['slot_y0']=1.5
source=H.parent/'fertigung_p08/Ausgabe/P08_Baugruppe_Servoverbindung_ENTWURF.FCStd';d=A.openDocument(str(source))
neutral=R.state([0]*6,[0,0])['frames'];removed=[]
for o in list(d.Objects):
    if getattr(o,'MotionRole','') in ('blade_ball','ring_ball','blade_link'):
        removed.append(o.Name);d.removeObject(o.Name)
assert len(removed)==48

def bake(o,s):o.Shape=Part.makeCompound([s.copy()]);o.Placement=A.Placement()
def set_shape(o,s,key):
    pl=neutral[key];s=s.copy();s.Placement=pl.multiply(s.Placement);bake(o,s)
def annotate(o,key):
    o.addProperty('App::PropertyString','P09_Rahmen','P09 Bewegung');o.P09_Rahmen=key
    o.addProperty('App::PropertyPlacement','P09_Neutralrahmen','P09 Bewegung');o.P09_Neutralrahmen=neutral.get(key,A.Placement())
    o.addProperty('App::PropertyString','P09_Hinweis');o.P09_Hinweis='Durchgaengige P09-Kinematik; konstruktive Passungen und Lastnachweise weiterhin offen.'

def add(name,s,key,ident):
    o=d.addObject('Part::Feature',name);set_shape(o,s,key);annotate(o,key);o.addProperty('App::PropertyString','BauteilID');o.BauteilID=ident
    assert o.Shape.isValid(),name
    return o

# Separate actual moving output geometry from the supplied purchased servo case.
original=Part.read(str(H.parent/'fertigung_p07/Quellen/SB-2270SGP.STEP'))
region=Part.makeCylinder(3.6,4.0001,V(0,12.7999,0),V(0,1,0))
shaft=original.common(region);case=original.cut(region);assert shaft.isValid() and len(shaft.Solids)>0
shaft.translate(V(0,-22.3,0));case.translate(V(58.3,-22.3,60))
modified=[];fixed=0
for o in list(d.Objects):
    if not hasattr(o,'BauteilID'):continue
    ident=o.BauteilID;role=getattr(o,'MotionRole','');l=int(getattr(o,'Rotor',0));j=int(getattr(o,'MotionIndex',0));sign=1 if l==0 else -1
    # Preserve every neutral world shape before assigning delta-frame animation.
    bake(o,o.Shape.copy())
    key='fixed'
    if ident=='SERVO-SAVOX-SB2270SGP':
        pl=R.M.local_world(sign).multiply(R.M.placement(rotation=R.M.rotz((60,180,300)[j])))
        s=case.copy();s.Placement=pl.multiply(s.Placement);bake(o,s)
        o.P06_Offen='P09 originaler Gehaeuserest nach Abtriebsabtrennung weiterhin ungueltig; keine Fertigungsfreigabe.'
        add(f'P09_Servoabtrieb_R{l}_S{j}',shaft,f'output:{l}:{j}','P09_SB2270_Originalabtrieb')
    elif hasattr(o,'P08_Rolle'):
        key=f'p08:{o.P08_Rotor}:{o.P08_Index}:{o.P08_Rolle}'
    elif role in ('blade','pitch_horn'):
        key=f'blade:{l}:{j}';set_shape(o,G.blade(C) if role=='blade' else G.pitch_horn(C,sign),key);modified.append(o.Name)
    elif ident=='TM-NABE':
        key=f'rotor:{l}';set_shape(o,G.hub(C,sign),key);modified.append(o.Name)
    elif ident=='TM-DECKEL-ZAHNKRANZ-130':
        key=f'rotor:{l}';set_shape(o,C.lid_shape(sign)[0],key);modified.append(o.Name)
    elif ident=='MITNEHMERSTIFT-D3':
        key=f'rotor:{l}';set_shape(o,C.driver_pin(sign),key);modified.append(o.Name)
    elif role=='rotor':key=f'rotor:{l}'
    elif role=='hub_pin':key=f'pin:{l}:{j}'
    elif role=='swash_rotating':
        key=f'swashrot:{l}';set_shape(o,G.rotating_ring(C,sign),key);modified.append(o.Name)
    elif role=='swash_stationary':key=f'swash:{l}'
    elif role=='sleeve':key=f'sleeve:{l}'
    elif role=='bearing_outer':key=f'swashrot:{l}' if j//100==2 else f'rotor:{l}'
    elif role=='pinion':key=f'pinion:{l}'
    elif ident=='ISO4035-M5':key=f'pinion:{0 if "Oben_" in o.Name else 1}'
    if not hasattr(o,'P09_Rahmen'):annotate(o,key)
    if key=='fixed':fixed+=1
# Fully captured short blade links; every ball now has a mounted stem and socket.
linkshapes=dict(stud_low=G.stud(),stud_high=G.stud(),body_low=G.body(),body_high=G.body(),cap_low=G.cap(),cap_high=G.cap(),rod=G.rod())
for l in range(2):
    sign=1 if l==0 else -1
    add(f'P09_Blattgelenktraeger_R{l}',G.ring_retainer(C,sign),f'swashrot:{l}','P09_Blattgelenktraeger')
    for j in range(8):
        for role,s in linkshapes.items():add(f'P09_R{l}_B{j}_{role}',s,f'link:{l}:{j}:{role}','P09_Blatt_'+role)
        for role,s in [('Axialschraube',G.axial_bolt()),('Axialscheibe',G.axial_washer()),('Gewindeeinsatz',G.insert()),('Klebefuge',G.bond())]:add(f'P09_R{l}_B{j}_{role}',s,f'blade:{l}:{j}','P09_'+role)
        bolt=G.retainer_bolt();bolt.rotate(V(),V(0,0,1),j*45);add(f'P09_R{l}_Traegerschraube{j}',bolt,f'swashrot:{l}','P09_M2x4_Traeger')
# Export a compact design catalogue of new parts, never labeled production release.
cat=A.newDocument('P09_Anschlussdetails')
for name,s,note in [('Kugelbolzen',G.stud(),'D4.8; Mitte/Anlage4.8; AF3x0.8; M2 RH x3'),('Pfanne_RH',G.body(),'Mund M5.5x0.35 RH; Stange M2 RH, Tiefe2.7'),('Pfanne_LH',G.body(),'Mund M5.5x0.35 RH; Stange M2 LH, Tiefe2.7'),('Haltekappe',G.cap(),'M5.5x0.35 RH x1.8; AF6'),('Stange15',G.rod(),'Kugelmitten15; M2 RH/LH; Stangenlaenge8.6; AF2.5x2'),('Axialschraube',G.axial_bolt(),'M2x8 nominal; Anzug offen'),('Axialscheibe',G.axial_washer(),'D2.2/D11.5x0.7'),('Gewindeeinsatz',G.insert(),'D3.5x7, innen M2; Klebefuge radial0.05'),('Pitchhebel_oben',G.pitch_horn(C,1),'Vierkant7.2 nominal; radiale M2-Aufnahme fuer Kugelbolzen'),('Drehring_oben',G.rotating_ring(C,1),'Lagersitz D58.06 nominal; Schulter erst ausserhalb7mm Lagerbreite'),('Gelenktraeger_oben',G.ring_retainer(C,1),'Acht M2x4 zur Verbindung mit Drehring; Kugelbolzen M2x3')]:
    assert s.isValid() and len(s.Solids)==1,name
    q=cat.addObject('Part::Feature',name);q.Shape=s.copy();q.addProperty('App::PropertyString','Anschlussangabe');q.Anschlussangabe=note+'; Konstruktion, nicht freigegeben.';Part.export([q],str(OUT/(name+'.step')));q.Placement.Base.x=80*(len(cat.Objects)-1)
cat.recompute();cat.saveAs(str(OUT/'P09_Anschlussdetails_ENTWURF.FCStd'));A.closeDocument(cat.Name)
ctl=d.addObject('App::FeaturePython','P09_Animation');R.Controller(ctl)
for typ,name,val in [('App::PropertyEnumeration','Modus',['Manuell','Demo']),('App::PropertyFloat','Zeit_s',0.),('App::PropertyFloatList','Servo_deg',[0.]*6),('App::PropertyFloatList','Rotor_deg',[0.,0.]),('App::PropertyFloat','Gelenkfehler_mm',0.),('App::PropertyFloatList','Blattpitch_deg',[14.]*8+[16.7]*8),('App::PropertyString','Status','')]:ctl.addProperty(typ,name,'P09 Animation');setattr(ctl,name,val)
ctl.Modus='Manuell';ctl.setEditorMode('Gelenkfehler_mm',1);ctl.setEditorMode('Blattpitch_deg',1)
info=d.getObject('P02_Fertigungsstatus');info.Gesamt_Fertigungsfreigabe=False;info.Begruendung='P09 durchgaengige modellierte Kinematik; lokale Gelenk-/Lager-/Blattaufnahmen ausgearbeitet. Kein Material-/Festigkeits-/Reibungsnachweis; Servogehaeuse weiterhin ungueltiger Originalimport und Servohalter offen.'
d.Label='P09 durchgaengige Bewegung Servo bis Rotorblatt – Entwurf';d.recompute();R.apply(d,[0]*6,[0,0]);target=OUT/'P09_Servo_bis_Rotorblatt_Bewegung.FCStd';d.saveAs(str(target))
counts={};invalid=[]
for o in d.Objects:
    if hasattr(o,'P09_Rahmen'):
        counts[o.P09_Rahmen.split(':')[0]]=counts.get(o.P09_Rahmen.split(':')[0],0)+1
        if not o.Shape.isValid():invalid.append(o.Name)
assert len(invalid)==6,invalid
A.closeDocument(d.Name)
d=A.openDocument(str(target));ctl=d.getObject('P09_Animation');ctl.Proxy=R.Controller(ctl);R.apply(d,[0]*6,[0,0]);assert not d.getObject('P02_Fertigungsstatus').Gesamt_Fertigungsfreigabe;A.closeDocument(d.Name)
report=dict(native_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),frame_classes=counts,removed_schematic_blade_items=len(removed),moving_servo_outputs=6,captured_blade_links=16,root_retainer_sets=16,modified_parts=modified,known_invalid_servo_cases=invalid,native_reopen_pass=True,manufacturing_release=False,design_changes=dict(blade_link_ball_radius_mm=33,previous_radius_mm=32,drive_pin_opposite_window_angle_deg=7,lid_windows_mm=[9,12],bearing_seat_diameter_mm=58.06,bearing_top_shoulder_z_mm=3.5,root_insert_bond_radial_mm=.05,ball_stud_wrench_relief_radius_mm=1.85),source_step_valid=False,local_output_valid=True,servo_case_partition_volume_error_mm3=abs(original.Volume-(case.Volume+shaft.Volume)))
(OUT/'Aufbaupruefung_P09.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
