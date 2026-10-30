#!/usr/bin/env python3
"""Import the user-selected purchased servo without inventing validity or specs."""
import hashlib,json,math,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')))
import FreeCAD as App,Part,Import
SRC=HERE/'Quellen/SB-2270SGP.STEP';OUT=HERE/'Ausgabe';OUT.mkdir(exist_ok=True)
source_hash=hashlib.sha256(SRC.read_bytes()).hexdigest()
d=App.newDocument('SB2270SGP_Originalimport');Import.insert(str(SRC),d.Name)
parts=[o for o in d.Objects if hasattr(o,'Shape') and not o.Shape.isNull()]
assert len(parts)==1
source=parts[0].Shape.copy();bbox=source.BoundBox
# Cylinder faces identify the output axis geometrically, rather than guessing
# the centre of the asymmetric case bounding box.
axis_faces=[f for f in source.Faces if isinstance(f.Surface,Part.Cylinder) and abs(f.Surface.Radius-3)<1e-6 and abs(abs(f.Surface.Axis.y)-1)<1e-7 and abs(f.Surface.Center.x)<1e-6 and abs(f.Surface.Center.z)<1e-6]
assert len(axis_faces)==25
assert abs(bbox.YMax-16.8)<1e-6
assert len(source.Solids)==1
original_valid=source.isValid()
try:
    source.check(True);diagnostic='No detailed error returned'
except Exception as e:
    diagnostic=str(e)
repairs=[]
for label in ('Shape.fix 1e-7..1e-3','removeSplitter'):
    t=source.copy()
    try:
        if label.startswith('Shape.fix'):t.fix(1e-7,1e-7,1e-3)
        else:t=t.removeSplitter()
        repairs.append(dict(operation=label,valid=t.isValid(),volume_mm3=t.Volume))
    except Exception as e:repairs.append(dict(operation=label,error=str(e)))
# Preserve the original geometry regardless of healing attempts.
for typ,key,val in [('App::PropertyString','P07_Quelle_SHA256',source_hash),('App::PropertyString','P07_Modell','Savox SB-2270SG+; selected by user'),('App::PropertyBool','P07_ShapeValid',original_valid),('App::PropertyString','P07_Status','GEOMETRIEFEHLER_IM_IMPORT; keine Fertigungsfreigabe' if not original_valid else 'Importiert; Anschlussnachweise offen')]:
    parts[0].addProperty(typ,key);setattr(parts[0],key,val)
d.recompute();native=OUT/'SB2270SGP_Originalimport_GEOMETRIEPRUEFUNG.FCStd';d.saveAs(str(native));App.closeDocument(d.Name)
base=HERE.parent/'fertigung_p06/Ausgabe/P06_Bauteilpruefung_NICHT_FERTIGUNGSBEREIT.FCStd'
d=App.openDocument(str(base));replaced=[];removed=[]
# Source axis is +Y at X=Z=0. Align its free tip with the existing kinematic
# horn reference plane; actual horn seating/retaining screw remains unresolved.
canonical=source.copy();canonical.translate(App.Vector(58.3,-16.8,60))
for o in list(d.Objects):
    if getattr(o,'MotionRole','')=='servo_shaft':
        removed.append(o.Name);d.removeObject(o.Name)
for o in d.Objects:
    if getattr(o,'MotionRole','')!='servo_housing':continue
    rotor=int(o.Rotor);index=int(o.MotionIndex)
    s=canonical.copy();s.rotate(App.Vector(),App.Vector(0,0,1),(60,180,300)[index])
    if rotor==1:
        s.rotate(App.Vector(),App.Vector(1,0,0),180);s.rotate(App.Vector(),App.Vector(0,0,1),180)
    s.translate(App.Vector(0,0,30 if rotor==0 else -30))
    o.Shape=Part.makeCompound([s]);o.Placement=App.Placement()
    o.BauteilID='SERVO-SAVOX-SB2270SGP';o.Label='SB2270SG+_Original_STEP__'+o.Name
    o.P02_Klasse='Kaufteil_User_STEP_SB2270SGP';o.P02_Offen='Imported shape invalid; original geometry retained. Horn/retaining screw, actual mount and electrical data pending.'
    o.P06_Darstellung='Detaillierter STEP-Import mit Geometriefehler'
    o.P06_Offen='Originalimport nicht gueltig; neue Originaldatei oder nachvollziehbare Reparatur erforderlich. Konkretes Horn/Schraube, Servohalter und elektrische SB2270SG+-Daten offen.'
    o.P06_Fertigungsbereit=False
    if hasattr(o,'Masse_g'):o.Masse_g=''
    for typ,key,val in [('App::PropertyString','P07_Quelle_SHA256',source_hash),('App::PropertyBool','P07_QuellgeometrieGueltig',original_valid),('App::PropertyString','P07_Ausrichtung','Original (X0,Z0) output axis; Ytip16.8 -> horn reference y0; radius58.3/local z60; no scaling'),('App::PropertyString','P07_Leistungsdaten','Nicht aus SB2271 uebernommen; SB2270SG+ Masse/Torque/Speed/PWM separat bestaetigen')]:
        o.addProperty(typ,key);setattr(o,key,val)
    if hasattr(o,'Bewegungsstatus'):o.Bewegungsstatus='P07 statischer Originalimport SB2270SG+, kein M01-Laufzeitprofil'
    # Do not let an old motion runtime accidentally reposition this static shape.
    if hasattr(o,'MotionRole'):o.MotionRole='fixed'
    if hasattr(o,'RestPlacement'):o.RestPlacement=App.Placement()
    replaced.append(o.Name)
assert len(replaced)==6 and len(removed)==6
status=d.getObject('P02_Fertigungsstatus');status.Gesamt_Fertigungsfreigabe=False;status.Begruendung='P07: SB2270SG+ vom Nutzer ausgewaehlt und als STEP eingebaut. Originalimport geometrisch ungueltig; Horn/Servohalter und weitere P06-Konstruktionsluecken offen.'
d.Label='P07 SB2270SG+ STEP-Integration – NICHT FERTIGUNGSBEREIT';d.recompute()
assembly=OUT/'P07_SB2270SGP_Baugruppe_GESPERRT.FCStd';d.saveAs(str(assembly));App.closeDocument(d.Name)
d=App.openDocument(str(assembly))
for name in replaced:
    o=d.getObject(name)
    assert o.BauteilID=='SERVO-SAVOX-SB2270SGP' and len(o.Shape.Solids)==1
    assert abs(o.Shape.Volume-source.Volume)<1e-6
    assert o.Shape.isValid()==original_valid
assert all(d.getObject(name) is None for name in removed)
assert not d.getObject('P02_Fertigungsstatus').Gesamt_Fertigungsfreigabe
App.closeDocument(d.Name)
report=dict(model='Savox SB-2270SG+',selection='Explicit user selection in chat; replaces planned SB2271 for CAD',source_file=SRC.name,source_sha256=source_hash,source_provenance='User upload; STEP header SolidWorks2024, 2025-04-15; independent OEM authenticity/licence not established',source_solids=len(source.Solids),source_faces=len(source.Faces),source_valid=original_valid,detailed_check=diagnostic,healing_attempts=repairs,original_geometry_preserved=True,source_bbox_mm=dict(x=[bbox.XMin,bbox.XMax],y=[bbox.YMin,bbox.YMax],z=[bbox.ZMin,bbox.ZMax]),source_overall_dimensions_mm=[bbox.XLength,bbox.YLength,bbox.ZLength],output_axis=dict(origin_source_mm=[0,0,0],direction=[0,1,0],free_tip_y_mm=16.8,cylindrical_tooth_faces_radius_3mm=len(axis_faces)),assembly_replaced_servo_count=len(replaced),removed_dummy_shaft_count=len(removed),native_reopen_pass=True,assembly_sha256=hashlib.sha256(assembly.read_bytes()).hexdigest(),manufacturing_ready=False,performance_data_transferred_from_SB2271=False,simulation_revalidated=False,remaining=['Invalid STEP source topology','Actual horn, seating height, retaining screw and mounting hardware','Servo bracket design and collision checks after valid geometry','SB2270SG+ mass, torque/speed and electrical data','Other P06 manufacturing gaps remain'])
(OUT/'Importpruefung_P07.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(HERE/'Servowahl.json').write_text(json.dumps(dict(selected_model='Savox SB-2270SG+',source_sha256=source_hash,complete_purchased_assembly=True,performance_data_status='SB2270SG+ specifications pending; do not reuse SB2271 data',mass_g=None,supply_v=None,torque_nm=None,speed_rad_s=None,source_geometry_valid=original_valid),indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
