#!/usr/bin/env python3
"""Latest purchased-motor mounting model, from supplied dimensioned EMAX drawing."""
import os,sys,json,math,csv,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')),str(H.parent/'cad')]
import FreeCAD as A,Part,erstellen as C
V=A.Vector;OUT=H/'Ausgabe';data=json.loads((H/'Motordaten_EMAX_Zeichnung_P04.json').read_text());m=data['motor']
# Original PCD16 remains the default. Do not enable the unsupported rectangular mode.
assert C.MO.get('mount_pattern','pcd')=='pcd' and C.MO['mount_pcd']==16
centres=C.motor_mount_points();plate,z=C.plate_shape();assert plate.isValid()
for x,y in centres:assert not plate.isInside(V(x,y,z+C.PL['t']/2),1e-7,True)
for sx in (-1,1):
 for sy in (-1,1):assert plate.isInside(V(C.CDIST+sx*8,sy*8,z+C.PL['t']/2),1e-7,True)
# Complete purchased component with known mounting/axial dimensions. Outer boundary
# is conservative where the foot/vent contours are not dimensioned.
body=Part.makeCylinder(14,m['derived_mount_face_to_bell_front_mm'])
output=Part.makeCylinder(2.5,13,V(0,0,m['derived_mount_face_to_bell_front_mm']))
motor=Part.makeCompound([body,output]);assert abs(motor.BoundBox.ZLength-31.6)<1e-6
motor_doc=A.newDocument('EMAX_ECOII2306_Anschlussmodell_P04');mobj=motor_doc.addObject('Part::Feature','EMAX_ECOII2306_Kaufteil');mobj.Shape=motor
for name,value in [('Artikel',m['item']),('Darstellung','Vollständiges Kaufteil, Anschluss-/Grenzhüllenmodell nach Zeichnung; keine Innenfertigungsdaten'),('Gewinde','4xM3 auf PCD16; M5-Abtrieb, Gewindelängen/Einschraubtiefe nicht bemaßt'),('Masse_g','30.2 ohne Silikonkabel'),('Freigabe','Motor-Anschlussmaße teilweise belegt; Gesamtmontage nicht freigegeben')]:mobj.addProperty('App::PropertyString',name);setattr(mobj,name,value)
markers=motor_doc.addObject('Part::Feature','Anschlusspunkte_4xM3_PCD16');markers.Shape=Part.makeCompound([Part.Wire(Part.makeCircle(1.5,V(x-C.CDIST,y,0))) for x,y in centres]);markers.addProperty('App::PropertyString','Hinweis');markers.Hinweis='Gewindepositionen auf Montageebene, keine erfundene Gewindetiefe'
motor_doc.saveAs(str(OUT/'EMAX_ECOII2306_Anschlussmodell_P04.FCStd'));Part.export([mobj],str(OUT/'EMAX_ECOII2306_Anschlussmodell_P04.step'));A.closeDocument(motor_doc.Name)
plate_doc=A.newDocument('P04_Motorplatte_PCD16');p=plate_doc.addObject('Part::Feature','Motorplatte_PCD16');p.Shape=plate;p.addProperty('App::PropertyString','Status');p.Status='Lochbild nach EMAX-Zeichnung bestätigt, sonstige Fertigungs-/Klemmschnittstellen offen';plate_doc.saveAs(str(OUT/'TM08_P04_Motorplatte_PCD16_ENTWURF.FCStd'));Part.export([p],str(OUT/'TM08_P04_Motorplatte_PCD16_ENTWURF.step'));A.closeDocument(plate_doc.Name)
d=A.openDocument(str(H.parent/'fertigung_p02/Ausgabe/P02_Kaufteile_Integration_GESPERRT.FCStd'));motors=[];plates=[]
for o in d.Objects:
 if not hasattr(o,'BauteilID'):continue
 if o.BauteilID=='MOTOR-ECO2-2306':
  sign=1 if o.Name.startswith('Oben_') else -1
  s=motor.copy();s.rotate(V(),V(1,0,0),180);s.translate(V(C.CDIST,0,z))
  if sign<0:s.rotate(V(),V(1,0,0),180);s.rotate(V(),V(0,0,1),180)
  s.translate(V(0,0,30*sign));o.Shape=Part.makeCompound([s]);o.Placement=A.Placement();o.Masse_g='30.2'
  o.addProperty('App::PropertyString','P04_Zeichnungsdaten');o.P04_Zeichnungsdaten='ECOII2306: PCD16, 4-M3, D28, H31.6, Abtrieb13, Innenwelle4, PropelleranschlussM5; 30.2g ohne Silikonkabel'
  o.P02_Offen='Maximale M3-Einschraubtiefe, M5-Gewindelänge und Ritzelklemmung offen; Hüllmodell kein Detailmodell von Lüftung/Motorfuß';o.Label='EMAX_ECOII2306_Kaufteil_nach_Zeichnung_'+str(sign);motors.append(o.Name)
 if o.BauteilID=='TM-HALTEPLATTE':
  # P02 already has the original, now confirmed, PCD16 geometry.
  plates.append(o.Name);o.addProperty('App::PropertyString','P04_Lochbild');o.P04_Lochbild='4x D3.4 auf Lochkreis16, Winkel45/135/225/315; EMAX-Zeichnung 4-M3 PCD16'
assert len(motors)==2 and len(plates)==2
info=d.getObject('P02_Fertigungsstatus');info.Motorlochbild_IST='P04: 4xM3 auf PCD16 bestätigt durch bereitgestellte EMAX-Zeichnung; 16x16-Recherche verworfen';info.Gesamt_Fertigungsfreigabe=False
info.Begruendung='Motor-Lochbild jetzt belegt. Einschraubtiefe/M5-Länge, Ritzelklemmung, Servo-/Horn-/Gelenkdetails, Lageranschlüsse sowie offene Eigenfertigung noch zu klären.'
d.Label='P04 nach EMAX-Zeichnung PCD16 – Gesamtfreigabe GESPERRT';d.recompute();parts=[o for o in d.Objects if hasattr(o,'BauteilID') and hasattr(o,'Shape') and not o.BauteilID.startswith('KEEP_')];assert all(o.Shape.isValid() for o in parts)
# Check motor-body clearance to nominal pinions; exact thread/retention is still open.
contacts=[]
for name in motors:
 o=d.getObject(name);prefix='Oben_' if o.Name.startswith('Oben_') else 'Unten_';pin=next(x for x in parts if x.BauteilID=='RITZEL-M1-Z20' and x.Name.startswith(prefix));volume=o.Shape.common(pin.Shape).Volume;assert volume<1e-3,(name,volume);contacts.append(dict(motor=name,pinion=pin.Name,nominal_intersection_mm3=volume,retention_not_validated=True))
path=OUT/'P04_Baugruppe_PCD16_GESPERRT.FCStd';d.saveAs(str(path));A.closeDocument(d.Name)
d=A.openDocument(str(path));assert not d.getObject('P02_Fertigungsstatus').Gesamt_Fertigungsfreigabe;assert all(d.getObject(n).Shape.isValid() for n in motors+plates);A.closeDocument(d.Name)
with (OUT/'Motorbohrbild_P04.csv').open('w',newline='') as f:
 w=csv.writer(f,delimiter=';');w.writerow(['hole','x_mm_plate_frame','y_mm_plate_frame','clearance_diameter_mm','PCD_mm']);w.writerows([[i+1,x,y,3.4,16] for i,(x,y) in enumerate(centres)])
lines=['0','SECTION','2','HEADER','9','$INSUNITS','70','4','0','ENDSEC','0','SECTION','2','ENTITIES']
for x,y in centres:lines+=['0','CIRCLE','8','MOTORBOHRUNGEN_PCD16','10',str(x),'20',str(y),'30','0','40','1.7']
lines+=['0','ENDSEC','0','EOF'];(OUT/'Nur_Motorbohrbild_P04_PCD16_ENTWURF.dxf').write_text('\n'.join(lines)+'\n')
report=dict(status='DRAWING_MOUNT_DATA_APPLIED_FULL_PRODUCTION_BLOCKED',source_class=data['source_kind'],drawing_PCD_mm=16,square_pitch_mm=16/math.sqrt(2),hole_centres_mm=centres,wrong_16x16_probe_material_pass=True,motor_overall_height_mm=motor.BoundBox.ZLength,motor_body_and_output_solids_valid=True,native_assembly_reopen_pass=True,motors_replaced=motors,original_correct_plates_retained=plates,nominal_motor_pinion_checks=contacts,native_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),full_production_release=False,mass_note='30.2g per purchased motor excludes silicone wire; earlier H01/M01 full mass/flight budget not silently changed')
(OUT/'Pruefbericht_P04.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
