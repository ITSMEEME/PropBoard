#!/usr/bin/env python3
import sys,os,json,math,csv,hashlib,importlib.util
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')),str(H)]
import FreeCAD as A,Part
import geometrie as G
import runtime as R
V=A.Vector;OUT=H/'Ausgabe'
spec=importlib.util.spec_from_file_location('_p08_cad',H.parent/'cad/erstellen.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
profile=Part.read(str(OUT/'Abtriebsprofil_Schnittwerkzeug.brep'))
shapes=dict(horn=G.horn(profile),ball_low=G.ball_stud(),ball_high=G.ball_stud(),body_low=G.socket_body(),body_high=G.socket_body(),cap_low=G.socket_cap(),cap_high=G.socket_cap(),jam_low=G.nut(),jam_high=G.nut(),horn_nut=G.nut(),clamp_bolt=G.bolt(),clamp_nut=G.nut(),washer_high=G.washer(),washer_low=G.washer())
# Swash arm ends: actual boss and M2 nominal tapped-hole spaces, not floating balls.
swash=C.swash_stationary().copy()
for a in (60,180,300):
    boss=G.cyl(3,4,(40,0,9.5),(1,0,0));boss.rotate(V(),V(0,0,1),a);swash=swash.fuse(boss)
    bore=G.cyl(1,4.5,(39.5,0,9.5),(1,0,0));bore.rotate(V(),V(0,0,1),a);swash=swash.cut(bore)
swash=swash.removeSplitter();assert swash.isValid() and len(swash.Solids)==1
catalog=A.newDocument('P08_Einzelteile');specs={
'horn':'8mm Lochradius; geteilte Klemmnabe nach lokalem 25T-Schnitt; radiale 1%-Zugabe ist zu pruefender Passungsentwurf. M2 Durchgang fuer Kugelbolzen und Klemmschraube.',
'ball_low':'Kugel D4.80; Hals D2; M2x0.4 RH x4; AF4 x1.5; Kugelmitte/Anlage6.30. Werkstoff/Oberflaeche und Festigkeit offen.',
'body_low':'Aussen D8 x6.7; Kugelsitz R2.43; Mund M6x0.5 RH, Tiefe2.2; Stangenanschluss M2x0.4 RH, nutzbar3.5.',
'cap_low':'M6x0.5 RH aussen x2.2; AF6.4; Kugelsitz R2.43; Halsfreistellung konisch; Montage vor Einschrauben der Kappe.',
'jam_low':'M2x0.4 RH, nominal AF4 x1.6.',
'clamp_bolt':'M2x12, nominal ISO4762 head D3.8x2, SW1.5. Guete/Anzug/Sicherung offen.',
'washer_low':'M2 Scheibe D2.2/D5 x0.3, Nennreferenz.',
'swash':'P08 stationaerer Taumelring: 3x radiale D6-Bosse; M2x0.4 RH, Gewinde4 tief; Bohrraum4.5. Material-/Passungs-/Kugelmontageauslegung weiter offen.'}
for name in ('horn','ball_low','body_low','cap_low','jam_low','clamp_bolt','washer_low','swash','rod_upper','rod_lower','body_high','jam_high'):
    if name=='swash':s=swash
    elif name.startswith('rod_'):s=G.turnbuckle(R.K[0 if name.endswith('upper') else 1]['link_lengths_mm'][0])
    else:s=shapes[name]
    assert s.isValid() and len(s.Solids)==1,(name,s.isValid(),len(s.Solids))
    o=catalog.addObject('Part::Feature',name);o.Shape=s.copy();o.addProperty('App::PropertyString','Fertigungsangabe')
    o.Fertigungsangabe=specs.get(name,'Stange M2 RH/LH; AF3x4; individuelle Kugelmittenlaenge siehe Anschlussdaten. Gewinde nominal dargestellt.' if name.startswith('rod_') else 'Wie unteres Bauteil, aber M2x0.4 LH am Stangenanschluss. M6-Kappe weiterhin RH.')
    Part.export([o],str(OUT/(name+'.step')));o.Placement.Base.x=80*(len(catalog.Objects)-1)
catalog.recompute();catalog.saveAs(str(OUT/'P08_Anschluss_Einzelteile_ENTWURF.FCStd'));A.closeDocument(catalog.Name)
base=H.parent/'fertigung_p07/Ausgabe/P07_SB2270SGP_Baugruppe_GESPERRT.FCStd';d=A.openDocument(str(base))
remove=[]
for o in list(d.Objects):
    role=getattr(o,'MotionRole','');ident=getattr(o,'BauteilID','')
    if role in ('servo_horn','servo_tip','servo_link') or (role=='swash_stationary' and ident=='KUGELBOLZEN-M2'):
        remove.append(o.Name);d.removeObject(o.Name)
assert len(remove)==24
# Servo tip shifts tangentially -5.5mm to clear the actual clamping horn hub.
for o in d.Objects:
    if getattr(o,'BauteilID','')=='SERVO-SAVOX-SB2270SGP':
        l=int(o.Rotor);i=int(o.MotionIndex);a=R.M.AZ[i];direction=R.M.local_world(1 if l==0 else -1).Rotation.multVec(V(5.5*math.sin(a),-5.5*math.cos(a),0))
        s=o.Shape.copy();s.translate(direction);o.Shape=Part.makeCompound([s]);o.Placement=A.Placement();o.P07_Ausrichtung+='; P08 tangential shift -5.5mm for actual horn hub; mounts must follow.'
# Enlarge the actual through ports from D10 to D14 for the new socket envelope.
for o in d.Objects:
    if getattr(o,'BauteilID','')!='TM-HALTEPLATTE':continue
    l=0 if o.Name.startswith('Oben_') else 1;s=o.Shape.copy();world=R.M.local_world(1 if l==0 else -1)
    for a in (60,180,300):
        tool=G.cyl(7,6,(50.3,0,42));tool.rotate(V(),V(0,0,1),a);tool.Placement=world.multiply(tool.Placement);s=s.cut(tool)
    assert s.isValid();o.Shape=Part.makeCompound([s]);o.Placement=A.Placement()
    o.addProperty('App::PropertyString','P08_Aenderung');o.P08_Aenderung='3x Gestangedurchlass D14 stattD10; Restquerschnitt/Festigkeit nicht freigegeben.'
neutral,_,_=R.transforms([0]*6);created=[]
def assign(o,s,pl):
    s=s.copy();s.Placement=pl.multiply(s.Placement);o.Shape=Part.makeCompound([s]);o.Placement=A.Placement()
def annotate(o,l,i,role,pl):
    for typ,key,val in [('App::PropertyInteger','P08_Rotor',l),('App::PropertyInteger','P08_Index',i),('App::PropertyString','P08_Rolle',role),('App::PropertyPlacement','P08_Neutralrahmen',pl),('App::PropertyBool','P08_Fertigungsfreigabe',False)]:o.addProperty(typ,key);setattr(o,key,val)
for o in d.Objects:
    if getattr(o,'BauteilID','')=='TM-TAUMEL-INNENRING':
        l=0 if o.Name.startswith('Oben_') else 1;pl=neutral[(l,-1,'swash')];assign(o,swash,pl);annotate(o,l,-1,'swash',pl)
        o.P06_Offen='P08 Kugelbolzenaufnahme modelliert. Zentrale Kugelmontage, Ringpassungen und Fertigungstoleranzen weiter offen.'
for l in range(2):
 for i in range(3):
  unit=dict(shapes,rod=G.turnbuckle(R.K[l]['link_lengths_mm'][i]))
  for role,s in unit.items():
    assert s.isValid() and len(s.Solids)==1
    o=d.addObject('Part::Feature',f'P08_R{l}_S{i}_{role}');pl=neutral[(l,i,role)];assign(o,s,pl);annotate(o,l,i,role,pl)
    o.addProperty('App::PropertyString','BauteilID');o.BauteilID='P08_'+role
    o.addProperty('App::PropertyString','Hinweis');o.Hinweis='Detaillierter Anschlussentwurf; nominale Gewinde; Toleranzen/Material/Anzug und Nachweise noch offen.';created.append(o.Name)
assert len(created)==90
info=d.getObject('P02_Fertigungsstatus');info.Gesamt_Fertigungsfreigabe=False;info.Begruendung='P08 mechanische Servoverbindung detailliert modelliert; Anschlussentwurf mit nominalen Gewinden. Importservo ungueltig; Servohalter, Material/Passung/Anzug und weitere P06-Punkte offen.'
d.Label='P08 Servo–Taumelscheibe Anschlussentwurf – keine Gesamtfreigabe';d.recompute();full=OUT/'P08_Baugruppe_Servoverbindung_ENTWURF.FCStd';d.saveAs(str(full))
# Standalone mechanism is explicitly isolated: no frozen blade linkage presented as moving.
iso=A.newDocument('P08_Anschlussbewegung')
for o in d.Objects:
    if not(hasattr(o,'P08_Rolle') or getattr(o,'BauteilID','')=='SERVO-SAVOX-SB2270SGP'):continue
    n=iso.addObject('Part::Feature',o.Name);n.Shape=Part.makeCompound([o.Shape.copy()]);n.Placement=A.Placement()
    if hasattr(o,'P08_Rolle'):annotate(n,o.P08_Rotor,o.P08_Index,o.P08_Rolle,o.P08_Neutralrahmen)
    n.addProperty('App::PropertyString','Hinweis');n.Hinweis='Isolierte Anschlussbewegung; Servo-Originalgeometrie ungueltig; keine Fertigungsfreigabe.'
iso.Label='P08 isolierte Servoverbindung – beweglicher Entwurf';iso.recompute();isolated=OUT/'P08_Isolierte_Anschlussbewegung.FCStd';iso.saveAs(str(isolated));A.closeDocument(iso.Name);A.closeDocument(d.Name)
d=A.openDocument(str(full));assert len([o for o in d.Objects if hasattr(o,'P08_Rolle')])==92;assert all(d.getObject(n).Shape.isValid() for n in created);assert not d.getObject('P02_Fertigungsstatus').Gesamt_Fertigungsfreigabe;A.closeDocument(d.Name)
report=dict(full_native_sha256=hashlib.sha256(full.read_bytes()).hexdigest(),isolated_native_sha256=hashlib.sha256(isolated.read_bytes()).hexdigest(),new_linkage_objects=90,modified_swash_rings=2,removed_schematic_objects=24,modified_passage_plates=2,servo_tangential_shift_mm=-5.5,link_centres_mm=[k['link_lengths_mm'] for k in R.K],new_parts_valid=True,native_reopen_pass=True,full_manufacturing_release=False,thread_representation='Nominal BRep spaces, M2x0.4 RH/LH and M6x0.5 RH callouts govern',important_open_items=['All material/process/tolerance and assembly-torque definitions are design proposals','Clamping spline 1% radial allowance needs physical fit gauge and strength/endurance validation','Invalid original complete servo remains in assembly','Final servo mounting brackets and earlier P06 issues remain'])
(OUT/'Aufbaupruefung_P08.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
