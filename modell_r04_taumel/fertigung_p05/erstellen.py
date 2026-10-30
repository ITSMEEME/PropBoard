#!/usr/bin/env python3
import sys,os,json,math,hashlib,csv
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')),str(H),str(H.parent/'cad')]
import FreeCAD as A,Part
import importlib.util
_spec=importlib.util.spec_from_file_location("_p05_cad_templates",H.parent/"cad/erstellen.py");C=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(C)
import geometrie as G
V=A.Vector;OUT=H/'Ausgabe';cfg=json.loads((H/'anschlussdaten.json').read_text());m=json.loads((H.parent/'fertigung_p04/Motordaten_EMAX_Zeichnung_P04.json').read_text())['motor'];data=json.loads((H.parent/'fertigung_p04/Motordaten_EMAX_Zeichnung_P04.json').read_text());data['motor']['M5_thread_length_mm']=9;data['motor']['maximum_M3_insertion_mm']=3;data['interface_clarification']=cfg['source'];(H/'Motordaten_P05.json').write_text(json.dumps(data,indent=2))
centres=C.motor_mount_points();motor=G.motor(m,[(x-C.CDIST,y) for x,y in centres]);pinion,gear_info=G.pinion();screw=G.screw7();washer=G.washer();nut=G.thin_nut()
zplate=C.plate_shape()[1];face_mm=C.PL['t'];assert abs(face_mm-4)<1e-9
thread_tip=zplate-m['total_height_mm'];thread_end=thread_tip+9;pinion_z=thread_tip;nut_z=pinion_z+5.5
assert abs(thread_tip-11.4)<1e-8 and abs(thread_end-(zplate-22.6))<1e-8
assert nut_z+2.7<thread_end
ring_z=C.LID['z0'];ring_top=ring_z+C.GR['face'];mesh_overlap=min(ring_top,pinion_z+5.5)-max(ring_z,pinion_z);assert mesh_overlap>=5.0

def world(shape,sign):
    s=shape.copy()
    if sign<0:s.rotate(V(),V(1,0,0),180);s.rotate(V(),V(0,0,1),180)
    s.translate(V(0,0,30*sign));return s

def at(shape,x,y,z):
    s=shape.copy();s.translate(V(x,y,z));return s

# Standalone references have identity parent placements and explicit scope.
cat=A.newDocument('P05_Anschlussbauteile')
for name,shape,note in [('M3x7_Referenz',screw,'Derived from CC-BY FreeCAD-library M3x10 by shortening only shank. Not an original CAD of supplied kit screw.'),('Scheibe_M3',washer,'Nominal ISO7089 3.2x7x0.5 reference'),('Kontermutter_M5',nut,'Nominal ISO4035 M5 AF8 h2.7, no helical thread/chamfer detail'),('Ritzel_M1_Z20_M5',pinion,'Custom steel pinion; internal M5x0.8-6H defined by drawing, not a smooth-bore substitute'),('EMAX_ECOII2306_Anschlussmodell_P05',motor,'Purchased motor mounting envelope; nominal M3 insertion allowance 3mm and usable M5 length9mm from user; not OEM internal CAD')]:
    o=cat.addObject('Part::Feature',name);o.Shape=shape.copy();o.addProperty('App::PropertyString','Hinweis');o.Hinweis=note
    Part.export([o],str(OUT/(name+'.step')))
    o.Placement.Base.x=30*(len(cat.Objects)-1)
cat.recompute();cat.saveAs(str(OUT/'P05_Anschlussbauteile.FCStd'));A.closeDocument(cat.Name)
d=A.openDocument(str(H.parent/'fertigung_p04/Ausgabe/P04_Baugruppe_PCD16_GESPERRT.FCStd'));added=[];motors=[];gears=[];nuts=[];screws=[];washers=[]
def assign(o,s):o.Shape=Part.makeCompound([s]);o.Placement=A.Placement()
def feature(name,s,ident,note):
    o=d.addObject('Part::Feature',name);assign(o,s)
    for key,val in [('BauteilID',ident),('P02_Klasse','P05_Anschlussentwurf'),('P02_Freigabe','GEOMETRISCH_GEPRUEFT_KEINE_GESAMTFREIGABE'),('P05_Hinweis',note)]:o.addProperty('App::PropertyString',key);setattr(o,key,val)
    o.addProperty('App::PropertyString','Masse_g');o.Masse_g=f'{s.Volume*.00785:.5f}';o.addProperty('App::PropertyString','Massenquelle');o.Massenquelle='Nominal CAD steel density 7850 kg/m3, not weighed';added.append(o.Name);return o
for sign,prefix in ((1,'Oben_'),(-1,'Unten_')):
    mo=next(o for o in d.Objects if getattr(o,'BauteilID','')=='MOTOR-ECO2-2306' and o.Name.startswith(prefix))
    s=motor.copy();s.rotate(V(),V(1,0,0),180);s.translate(V(C.CDIST,0,zplate));assign(mo,world(s,sign));mo.P02_Offen='User limits: M3 max3mm, M5 usable9mm. Nominal mounting model, actual thread flanks/torques/runout not certified.';mo.addProperty('App::PropertyString','P05_Gewinde');mo.P05_Gewinde='4xM3 max3; M5x0.8 usable9 from free end; 4mm thread-free output interval as derived envelope';motors.append(mo)
    pi=next(o for o in d.Objects if getattr(o,'BauteilID','')=='RITZEL-M1-Z20' and o.Name.startswith(prefix));assign(pi,world(at(pinion,C.CDIST,0,pinion_z),sign));pi.Label='P05_Ritzel_M1_Z20_M5_'+prefix;pi.addProperty('App::PropertyString','P05_Gewinde');pi.P05_Gewinde='M5x0.8-6H through, predrill4.2; model shows nominal diameter5 without helical flanks';pi.addProperty('App::PropertyString','Werkstoff_P05');pi.Werkstoff_P05='C45E proposed, machining/process qualification pending';pi.Masse_g=f'{pinion.Volume*.00785:.5f}';pi.P02_Offen='Threaded custom pinion and jam nut proposed. Runout, preload, torque, coating/lubrication, tooth quality and endurance pending';gears.append(pi)
    nu=feature('P05_Kontermutter_M5_'+prefix,world(at(nut,C.CDIST,0,nut_z),sign),'ISO4035-M5','Jam directly against steel threaded pinion; no washer included in 9mm thread stack; tightening not qualified');nuts.append(nu)
    for i,(x,y) in enumerate(centres):
        w=feature('P05_Motorscheibe_'+prefix+str(i),world(at(washer,x,y,zplate+face_mm),sign),'ISO7089-M3','Nominal washer 3.2x7x0.5');washers.append(w)
        sc=feature('P05_Motorschraube_'+prefix+str(i),world(at(screw,x,y,zplate+face_mm+.5),sign),'M3x7-P05-REFERENZ','7mm under-head, 4mm plate plus0.5mm washer ->2.5mm nominal penetration; actual fastener/head and torque to check');screws.append(sc)
# Geometric contacts and actual bores, including the maximum insertion boundary.
contacts=[]
for sc in screws:
    upper='Oben_' in sc.Name;sign=1 if upper else -1;mo=motors[0 if upper else 1];plate=next(o for o in d.Objects if getattr(o,'BauteilID','')=='TM-HALTEPLATTE' and o.Name.startswith('Oben_' if upper else 'Unten_'))
    for other in (mo,plate):
        vol=sc.Shape.common(other.Shape).Volume;assert vol<1e-3,(sc.Name,other.Name,vol);contacts.append(dict(a=sc.Name,b=other.Name,nominal_intersection_mm3=vol))
    wa=d.getObject(sc.Name.replace('Motorschraube','Motorscheibe'));v=sc.Shape.common(wa.Shape).Volume;assert v<1e-3,(sc.Name,wa.Name,v);assert sc.Shape.distToShape(wa.Shape)[0]<1e-6
    contacts.append(dict(a=sc.Name,b=wa.Name,nominal_intersection_mm3=v,bearing_contact=True))
    tip=sc.Shape.BoundBox.ZMin if upper else sc.Shape.BoundBox.ZMax;mount=sign*(30+zplate);penetration=(mount-tip)*sign;assert abs(penetration-2.5)<1e-5
for sign,prefix in ((1,'Oben_'),(-1,'Unten_')):
    plate=next(o for o in d.Objects if getattr(o,'BauteilID','')=='TM-HALTEPLATTE' and o.Name.startswith(prefix))
    for w in [w for w in washers if prefix in w.Name]:
        assert w.Shape.common(plate.Shape).Volume<1e-3
        assert w.Shape.distToShape(plate.Shape)[0]<1e-6
    nu=nuts[0 if sign>0 else 1];mo=motors[0 if sign>0 else 1];pi=gears[0 if sign>0 else 1]
    for a,b in ((nu,mo),(nu,pi),(pi,mo)):
        vol=a.Shape.common(b.Shape).Volume;assert vol<1e-3,(a.Name,b.Name,vol);contacts.append(dict(a=a.Name,b=b.Name,nominal_intersection_mm3=vol))
# Test a full gear-tooth engagement period at 8 phases, rather than aliased angles.
mesh=[]
for sign,prefix in ((1,'Oben_'),(-1,'Unten_')):
    main=next(o for o in d.Objects if getattr(o,'BauteilID','')=='TM-DECKEL-ZAHNKRANZ-130' and o.Name.startswith('Rotor_oben_' if sign>0 else 'Rotor_unten_'))
    for i in range(8):
        angle=(360/130)*i/8;ring=main.Shape.copy();ring.rotate(V(0,0,30*sign),V(0,0,sign),angle)
        p=pinion.copy();p.rotate(V(),V(0,0,1),-6.5*angle);p=world(at(p,C.CDIST,0,pinion_z),sign)
        v=ring.common(p).Volume;assert v<1e-3,(sign,angle,v);mesh.append(dict(rotor=sign,angle_deg=angle,intersection_mm3=v))
info=d.getObject('P02_Fertigungsstatus');info.Begruendung='M3 max3/M5 usable9 from user applied; M3x7+0.5 washer and threaded pinion+thin jam nut checked. Torque/runout/thread strength and remaining servo/bearing/joint/manufacturing interfaces remain open.';info.Gesamt_Fertigungsfreigabe=False
d.Label='P05 Motorverschraubung und M5-Ritzel – Gesamtfreigabe gesperrt';d.recompute();parts=[o for o in d.Objects if hasattr(o,'BauteilID') and hasattr(o,'Shape') and not o.BauteilID.startswith('KEEP_')];assert all(o.Shape.isValid() for o in parts)
path=OUT/'P05_Baugruppe_Motoranschluss_GESPERRT.FCStd';d.saveAs(str(path));A.closeDocument(d.Name);d=A.openDocument(str(path));assert not d.getObject('P02_Fertigungsstatus').Gesamt_Fertigungsfreigabe;assert all(d.getObject(n).Shape.isValid() for n in added);A.closeDocument(d.Name)
tol=cfg['selected_mounting']['acceptance_budget_assumptions_mm'];max_depth=tol['screw_length'][1]-tol['finished_plate'][0]-tol['washer'][0];min_depth=tol['screw_length'][0]-tol['finished_plate'][1]-tol['washer'][1];assert max_depth<3 and min_depth>2
report=dict(status='DIMENSIONAL_MOTOR_CONNECTION_CHECKS_PASS_NOT_TORQUE_OR_FLIGHT_RELEASE',source=cfg['source'],screw_count=len(screws),washer_count=len(washers),pinions=2,jam_nuts=len(nuts),nominal_M3_insertion_mm=2.5,nominal_M3_depth_reserve_mm=.5,assumed_tolerance_penetration_range_mm=[min_depth,max_depth],tolerance_budget_is_design_acceptance_requirement_not_verified_supplier_values=True,M5_usable_mm=9,M5_stack_mm=8.2,M5_nominal_unused_thread_mm=.8,M5_max_stack_with_pinion_face_plus_0_05_mm=8.25,M5_nominal_nut_to_bell_gap_mm=m['total_height_mm']-m['derived_mount_face_to_bell_front_mm']-8.2,axial_mesh_overlap_mm=mesh_overlap,gear=gear_info,nominal_contacts=contacts,gear_period_checks=mesh,native_reopen_pass=True,native_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),full_production_release=False,limitations=['Cosmetic/nominal M3/M5 thread interfaces, actual helical flanks not verified','Jam nut retention requires defined tightening/preload, thread condition, radial runout and endurance verification','External gear involute from FreeCAD; supplier tooth quality not certified','Other P04 servo/bearing/joint/clamp/assembly issues remain','Earlier flight and full mass budgets not silently recalculated'])
(OUT/'Pruefbericht_P05.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('nominal_contacts','gear_period_checks')},indent=2))
