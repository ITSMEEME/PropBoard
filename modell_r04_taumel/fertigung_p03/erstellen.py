#!/usr/bin/env python3
import os,sys,json,csv,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')),str(H)]
if '--historical-invalid-layout' not in sys.argv:
    raise SystemExit('P03 16x16 verworfen: EMAX-Zeichnung verlangt PCD16. Aktuell fertigung_p04 verwenden.')
import FreeCAD as A,Part
from platte_runtime import Plate,shape,templates
C=templates();OUT=H/'Ausgabe';OUT.mkdir(exist_ok=True)
legacy,z=C.plate_shape();revised=shape(16,16);assert legacy.isValid() and revised.isValid() and len(revised.Solids)==1
probe_z=z+C.PL['t']/2;centres=[(C.CDIST+sx*8,sy*8) for sx in (-1,1) for sy in (-1,1)]
for x,y in centres:
    assert not revised.isInside(A.Vector(x,y,probe_z),1e-7,True)
    assert legacy.isInside(A.Vector(x,y,probe_z),1e-7,True)
for x,y in C.motor_mount_points():
    assert not legacy.isInside(A.Vector(x,y,probe_z),1e-7,True)
    assert revised.isInside(A.Vector(x,y,probe_z),1e-7,True)
assert abs(revised.Volume-legacy.Volume)<1e-5
plate_doc=A.newDocument('P03_Halteplatte');o=plate_doc.addObject('PartDesign::FeaturePython','Halteplatte_P03');Plate(o)
for name in ('MotorRasterX_mm','MotorRasterY_mm'):o.addProperty('App::PropertyLength',name);setattr(o,name,16)
for name,value in [('Quelle','Nutzerrecherche 2026-10-30, ohne Originalzeichnung'),('Freigabe','ENTWURF: Motorpilot, Einschraubtiefe, weitere Befestigungen und Toleranzen offen')]:o.addProperty('App::PropertyString',name);setattr(o,name,value)
plate_doc.recompute();plate_doc.saveAs(str(OUT/'TM08_P03_Motorplatte_16x16_ENTWURF.FCStd'));Part.export([o],str(OUT/'TM08_P03_Motorplatte_16x16_ENTWURF.step'))
o.MotorRasterX_mm=17;plate_doc.recompute();assert not o.Shape.isInside(A.Vector(C.CDIST+8.5,8,probe_z),1e-7,True)
o.MotorRasterX_mm=16;plate_doc.recompute();assert abs(o.Shape.Volume-revised.Volume)<1e-5
A.closeDocument(plate_doc.Name)
d=A.openDocument(str(H.parent/'fertigung_p02/Ausgabe/P02_Kaufteile_Integration_GESPERRT.FCStd'));replaced=[]
for o in d.Objects:
    if getattr(o,'BauteilID','')!='TM-HALTEPLATTE':continue
    sign=1 if o.Name.startswith('Oben_') else -1
    s=revised.copy()
    if sign<0:s.rotate(A.Vector(),A.Vector(1,0,0),180);s.rotate(A.Vector(),A.Vector(0,0,1),180)
    s.translate(A.Vector(0,0,30*sign));o.Shape=Part.makeCompound([s]);o.Placement=A.Placement()
    o.addProperty('App::PropertyString','P03_Motoranschluss');o.P03_Motoranschluss='Raster 16 x 16 mm, M3-Freibohrungen D3.4, Nutzerangabe; Originaldatum/Schraubentiefe offen';replaced.append(o.Name)
assert len(replaced)==2
info=d.getObject('P02_Fertigungsstatus');info.Motorlochbild_IST='P03: Raster 16 x 16 mm, vier D3.4; Nutzerrecherche, nicht unabhängig herstellerverifiziert';info.Gesamt_Fertigungsfreigabe=False
d.Label='P03 Motorlochbild 16x16 – Gesamtfreigabe GESPERRT';d.recompute();parts=[o for o in d.Objects if hasattr(o,'BauteilID') and hasattr(o,'Shape') and not o.BauteilID.startswith('KEEP_')];assert all(o.Shape.isValid() for o in parts)
path=OUT/'P03_Baugruppe_16x16_GESPERRT.FCStd';d.saveAs(str(path));A.closeDocument(d.Name)
d=A.openDocument(str(path));assert not d.getObject('P02_Fertigungsstatus').Gesamt_Fertigungsfreigabe
for name in replaced:assert d.getObject(name).Shape.isValid()
A.closeDocument(d.Name)
with (OUT/'Motorbohrungen_P03.csv').open('w',newline='') as f:
 w=csv.writer(f,delimiter=';');w.writerow(['hole','x_mm_plate_frame','y_mm_plate_frame','diameter_mm','source']);w.writerows([[i+1,x,y,3.4,'User research, original drawing missing'] for i,(x,y) in enumerate(centres)])
# Drawing exchange contains ONLY the revised motor-hole group, not a full released part.
lines=['0','SECTION','2','HEADER','9','$INSUNITS','70','4','0','ENDSEC','0','SECTION','2','ENTITIES']
for x,y in centres:lines+=['0','CIRCLE','8','MOTORBOHRUNGEN_P03','10',str(x),'20',str(y),'30','0','40','1.7']
lines+=['0','ENDSEC','0','EOF'];(OUT/'Nur_Motorbohrbild_P03_16x16_ENTWURF.dxf').write_text('\n'.join(lines)+'\n')
report=dict(status='USER_INPUT_APPLIED_GEOMETRY_TESTED_FULL_PRODUCTION_BLOCKED',motor_pitch_mm=[16,16],hole_diameter_mm=3.4,legacy_pcd_mm=16,legacy_square_pitch_mm=16/math.sqrt(2),hole_centres_mm=centres,min_nominal_outer_pad_edge_distance_mm=C.PL['pad_d']/2-math.hypot(8,8)-1.7,source_class='USER_RESEARCH_WITHOUT_PRIMARY_DRAWING',legacy_default_preserved=True,legacy_and_revised_probe_checks_pass=True,plate_volume_change_mm3=revised.Volume-legacy.Volume,parameter_edit_16_to17_to16_pass=True,native_assembly_reopen_pass=True,plates_replaced=replaced,native_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),full_production_release=False,open='Motor mounting datum/pilot, screw depth, shaft/pinion retention and all other P02 interface blockers remain')
(OUT/'Pruefbericht_P03.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
