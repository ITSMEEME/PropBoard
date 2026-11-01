#!/usr/bin/env python3
"""Build the CURRENT P11 direct-drive assembly from the immutable P10 archive."""
import csv,hashlib,json,math,sys
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1];SIM=H.parent/'simulation';OUT=H/'Ausgabe'
sys.path[:0]=['/usr/lib/freecad-python3/lib',str(H),str(H.parent/'integration_p10')]
import FreeCAD as A,Part
import p11_runtime as RT
import geometrie as G
import kabel_p10 as K
P=G.P;V=A.Vector
OUT.mkdir(exist_ok=True);(OUT/'STEP').mkdir(exist_ok=True)
SRC=H.parent/'integration_p10/Ausgabe/P10_Gesamtbaugruppe.FCStd'
source_hash=hashlib.sha256(SRC.read_bytes()).hexdigest()
base=json.loads((SIM/'p10_massen.json').read_text());cad=json.loads((SIM/'modell_h01.json').read_text())
oldmass={x['name']:x for x in cad['components']};oldmass.update({x['name']:x for x in base['add_components']})
d=A.openDocument(str(SRC));d.getObject('P09_Animation').Proxy=None
neutral=RT.state([0]*6,[0,0])['frames'];group=d.addObject('App::DocumentObjectGroup','P11_Direktantrieb')
records=[];removed={};changes=[];unbudgeted_legacy_removals=[]
def prop(o,k,v,t='App::PropertyString'):
    if not hasattr(o,k):o.addProperty(t,k,'P11')
    setattr(o,k,v)
def mark_old(o):
    if o.Name not in oldmass:
        # Some P05 fasteners were never itemized in the inherited P10 model.
        # Removing them must NOT invent a mass saving from that model.
        unbudgeted_legacy_removals.append(o.Name)
        removed[o.Name]=dict(name=o.Name,part_id=o.BauteilID,group='body',mass_kg=0,cg_m=[0,0,0],inertia_cg_kgm2=[[0]*3 for _ in range(3)],note='Not separately budgeted in P10; zero mass credit, not a physical zero mass')
    else:removed[o.Name]=oldmass[o.Name]
def erase(o):
    mark_old(o);changes.append({'operation':'removed','name':o.Name,'id':o.BauteilID});d.removeObject(o.Name)
def local(s,sign):
    s=s.copy();s.Placement=RT.M.local_world(sign).multiply(s.Placement);return s
def mass(shape,rho=None,mass_g=None):
    # The inertia of each separate solid is re-expressed about the compound CG.
    solids=shape.Solids;volume=sum(s.Volume for s in solids)
    assert volume>0
    m=mass_g/1000 if mass_g is not None else volume*rho*1e-9
    cg=sum((s.CenterOfMass*s.Volume for s in solids),V())/volume;J=[[0.]*3 for _ in range(3)]
    for s in solids:
        I=s.MatrixOfInertia;q=s.CenterOfMass-cg;x=[q.x,q.y,q.z];rows=[[I.A11,I.A12,I.A13],[I.A21,I.A22,I.A23],[I.A31,I.A32,I.A33]]
        for i in range(3):
            for j in range(3):J[i][j]+=rows[i][j]+s.Volume*((q.Length**2 if i==j else 0)-x[i]*x[j])
    return m,[cg.x/1000,cg.y/1000,cg.z/1000],[[v*m/volume*1e-6 for v in row] for row in J]
def put(name,shape,ident,material,note,key='fixed',rho=819,mass_g=None,tag='body',existing=None,color=(.4,.6,.7)):
    assert shape.isValid(),name
    o=existing or d.addObject('Part::Feature',name)
    if existing:mark_old(o)
    frame=neutral.get(key,A.Placement());s=shape.copy();s.Placement=frame.multiply(s.Placement)
    o.Shape=Part.Compound([s]);o.Placement=A.Placement()
    prop(o,'BauteilID',ident);prop(o,'P09_Rahmen',key);prop(o,'P09_Neutralrahmen',frame,'App::PropertyPlacement')
    prop(o,'P11_Werkstoff',material);prop(o,'P11_Hinweis',note);prop(o,'P11_Farbe',list(color),'App::PropertyFloatList');prop(o,'P10_Farbe',list(color),'App::PropertyFloatList')
    prop(o,'P06_Fertigungsbereit',False,'App::PropertyBool');o.Label=name.replace('_',' ')
    m,cg,J=mass(o.Shape,rho,mass_g);rec=dict(name=o.Name,part_id=ident,group=tag,frame=key,mass_kg=m,cg_m=cg,inertia_cg_kgm2=J,material=material,note=note)
    records.append(rec);prop(o,'P11_Masse_g',str(m*1000));group.addObject(o)
    shape.exportStep(str(OUT/'STEP'/(name+'.step')))
    return o

parts=[o for o in d.Objects if hasattr(o,'P09_Rahmen')]
for o in parts:
    ident=o.BauteilID;key=o.P09_Rahmen
    if (ident in {'MOTOR-ECO2-2306','RITZEL-M1-Z20','ISO4035-M5','P10-STUETZPLANET-Z20','MR85ZZ','P10-PLANETENBOLZENTRAEGER','P10-PLANETENBOLZEN-D5','P10-DISTANZSCHEIBE-5'}
        or o.Name.startswith(('P05_Motorschraube','P05_Motorscheibe','P10_Motorbruecke','P10_Kabel_M1','P10_Kabel_M2'))):erase(o)

for l,sign in [(0,1),(1,-1)]:
    lvl='Oben' if sign>0 else 'Unten';world=RT.M.local_world(sign)
    o=d.getObject('Rotor_oben_1' if sign>0 else 'Rotor_unten_1');old=o.Shape.copy();old.Placement=world.inverse().multiply(old.Placement)
    carrier=G.smooth_lid(old).cut(G.ring(64.4,65.4,15.1,7)).fuse(G.rotor_cup()).removeSplitter()
    put('P11_Rotortraeger_'+lvl,carrier,'P11-ROTORTRAEGER-D184','PA-CF, effektiver Fuellgrad 0.70 (Annahme)',
        'Integrierter glatter Ring und 1:1-Motorrotortraeger; kein Zahnrad; D184 erfordert Fremdfertigung oder neues Fertigungskonzept.',f'rotor:{l}',existing=o,tag='upper' if l==0 else 'lower')
    put('P11_Laufbahneinsatz_'+lvl,G.guide_insert(),'P11-LAUFBAHN-STAHL','Stahl, 7850 kg/m3','Austauschbare glatte Innenlaufbahn; Schulter z15.1, Klebe-/Pressverbindung noch auszulegen.',f'rotor:{l}',rho=7850,tag='upper' if l==0 else 'lower',color=(.72,.74,.78))
    put('P11_Motorrotor_Bauraum_'+lvl,G.ring(87,89,15,15),'P11-MOTORROTOR-BAURAUM','Magnet-/Polbauraum, Masse angenommen',
        '80g Budgetannahme, kein ausgewaehlter Motor; starr mit Rotortraeger gekoppelt 1:1.',f'motor:{l}',mass_g=P['motor_rotor_mass_assumption_g'],tag='upper' if l==0 else 'lower',color=(.3,.7,.8))
    put('P11_Stator_Bauraum_'+lvl,local(G.stator(),sign),'P11-STATOR-BAURAUM','Stator-/Wicklungsbauraum, Masse angenommen',
        '200g Budgetannahme; innerer Durchgang fuer Mittelrohr/Gestaenge, kein EMAX-Geometriemodell.',mass_g=P['stator_mass_assumption_g'],color=(.88,.48,.2))
    oldplate=d.getObject(lvl+'_feststehend_10');s=oldplate.Shape.copy();s.Placement=world.inverse().multiply(s.Placement)
    plate=G.plate(s)
    assert len(plate.Solids)==1,'Guide mounting bridge must be connected to the retained plate'
    put('P11_Halteplatte_'+lvl,local(plate,sign),'P11-HALTEPLATTE','PETG, effektiver Fuellgrad 0.5',
        'Alter Motorhalter entfernt; drei Statorarme und Stuetzpfosten; vorhandene Servo-/Rollentraeger-Lochbilder erhalten.',existing=oldplate,rho=635,color=(.5,.54,.6))
    for k,phi in enumerate(P['roller_azimuths_deg']):
        key=f'roller:{l}:{k}';x,y=G.xy(phi)
        put(f'P11_Fuehrungsrolle_{lvl}_{k}',G.ring(4,9.55,15.4,5.5),'P11-FUEHRUNGSROLLE-POM','POM-C, 1410 kg/m3',
            'D19.1, zwei MR85, kein Antriebsmoment; Ringkontakt mit einstellbarer Betriebsluft.',key,rho=1410,color=(.72,.35,.22))
        for b,z in enumerate([15.4,17.9]):
            put(f'P11_MR85_{lvl}_{k}_{b}',local(G.ring(2.5,4,z,2.5,x,y),sign),'MR85ZZ','Kaufteil-Nennmass 5x8x2.5',
                'Massereferenz 0.6g; Wälzkoerper/Innenaufbau nicht animiert. Aussenring-Tragfaehigkeit und 20k/min pruefen.',mass_g=.6,color=(.7,.7,.65))
        put(f'P11_Rollentraeger_{lvl}_{k}',local(G.carrier(phi),sign),'P11-ROLLENTRAEGER','Aluminium EN AW-6082, 2700 kg/m3',
            'Wiederverwendetes M3-Lochbild, exzentrische D5-Aufnahme und radiale M3-Klemmschraube.',rho=2700)
        put(f'P11_Exzenterbolzen_{lvl}_{k}',local(G.eccentric(phi),sign),'P11-EXZENTERBOLZEN-D5','Stahl, 7850 kg/m3',
            'Exzentrizitaet 0.25 mm, Einstellwinkel36.87 Grad; obere Stammachse r54.6, Journal r54.8/t0.15.',rho=7850)
        put(f'P11_Klemmschraube_{lvl}_{k}',local(G.locking_screw(phi),sign),'P11-M3-GEWINDESTIFT','Stahl, nominales Gewindemass',
            'Sichert Exzenter; Gewinde, Anzugsmoment und Sicherung noch nicht freigegeben.',rho=7850)
        put(f'P11_Distanz_{lvl}_{k}',local(G.ring(2.6,3.4,20.4,1.1,x,y),sign),'P11-DISTANZ-D5','Stahl',
            'Auf Journal zentriert, stuetzt die Lagerinnenringe gegen den Traeger.',rho=7850)
    # Third fixed guide replaces the former motor mounting sector.
    for i,(ident,s) in enumerate(G.G.carrier_fasteners(330)):
        put(f'P11_Traegerbefestigung_{lvl}_{i}',local(s,sign),ident,'Stahl','Dritte feste Rollenaufnahme an neuer Halteplattenbruecke.',rho=7850)
    for k,az in enumerate(P['stator_post_azimuths_deg']):
        a=math.radians(az);x,y=82*math.cos(a),82*math.sin(a)
        for part,ident,s in [('Schraube','ISO4762-M3x20',G.G.orient(G.G.iso4762(20),(x,y,46.5),(0,0,1))),('Scheibe','ISO7089-M3',G.G.orient(G.G.iso7089(),(x,y,46),(0,0,1)))]:
            put(f'P11_Stator_{part}_{lvl}_{k}',local(s,sign),ident,'Stahl','Stator an 13-mm-Pfosten; 3.5mm angenommener Gewindeeingriff, Anschluss am zukuenftigen Motor bestaetigen.',rho=7850,color=(.6,.62,.65))

def world(sign,j,p):
    return tuple(RT.M.local_world(sign).multiply(RT.M.placement(rotation=RT.M.rotz(0 if j is None else (60,180,300)[j]))).multVec(V(*p)))
cable_rows=list(csv.DictReader((H.parent/'integration_p10/Ausgabe/Kabelliste_P10.csv').open()))
for c in K.cable_list(world):
    if not c['id'].startswith(('M1','M2')):continue
    sign=1 if c['id'].startswith('M1') else -1;off=(-1.8,0,1.8)[int(c['id'][-1])-1];a=math.radians(330)
    x,y=83*math.cos(a)-off*math.sin(a),83*math.sin(a)+off*math.cos(a)
    c['punkte']=[world(sign,None,(x,y,z)) for z in (30,33,49.5)]+c['punkte'][3:]
    c['von']='P11 Ringstator '+('oben' if sign>0 else 'unten');shape,length,mg=K.build(c)
    put('P11_Kabel_'+c['id'],shape,'P11-KABEL-'+c['typ'],c['typ'],'Drei Phasen zum Ringstator; 20AWG nur Geometriestand, fuer neuen Motor elektrisch neu auszulegen.',mass_g=mg,color=K.COLORS[c['farbe']])
    for row in cable_rows:
        if row['id']==c['id']:row.update(von=c['von'],laenge_mm=round(length,1),masse_g=round(mg,2))

ctl=d.getObject('P09_Animation');ctl.Proxy=RT.Controller(ctl);ctl.Label='P11 Animation 1:1 + Fuehrungsrollen'
status=d.getObject('P02_Fertigungsstatus');status.Gesamt_Fertigungsfreigabe=False;status.Begruendung='P11 Direktantrieb, Motor/KV/Temperatur und Rollentragfaehigkeit noch offen; keine Freigabe'
d.Label='P11 Direktantrieb 1:1 mit kugelgelagerten Fuehrungsrollen (Motorbauraum)'
d.recompute();RT.apply(d,[0]*6,[0,0]);target=OUT/'P11_Gesamtbaugruppe.FCStd';d.saveAs(str(target))
parts=[o for o in d.Objects if hasattr(o,'P09_Rahmen') and not o.BauteilID.startswith('KEEP_')]
assert not any(o.P09_Rahmen.startswith(('planet:','pinion:')) or o.BauteilID in ['RITZEL-M1-Z20','TM-DECKEL-HOHLRAD-130','P10-STUETZPLANET-Z20','MOTOR-ECO2-2306'] for o in parts)
newmass={r['name']:r for r in records}
def izz(rec):return rec['inertia_cg_kgm2'][2][2]+rec['mass_kg']*(rec['cg_m'][0]**2+rec['cg_m'][1]**2)
spin_delta=[]
for tag in ['upper','lower']:spin_delta.append(sum(izz(r) for r in records if r['group']==tag)-sum(izz(r) for r in removed.values() if r['group']==tag))
rollerJ=next(r for r in records if r['part_id']=='P11-FUEHRUNGSROLLE-POM')['inertia_cg_kgm2'][2][2]
payload=dict(revision='P11',source_native_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),base_revision='P10',base_native_sha256=source_hash,
 remove_components=list(removed.values()),add_components=records,rotor_spin_inertia_delta_kgm2=spin_delta,
 guide_rollers=dict(count_per_rotor=len(P['roller_azimuths_deg']),radius_m=.00955,track_radius_m=.0644,spin_ratio=RT.RATIO,spin_inertia_kgm2=rollerJ+2*.0006*.5*(.004**2+.003**2)/2),
 drive=dict(layout='P11_DIRECT',ratio=1,motor_sense=1,mechanical_efficiency_assumption=.98,motor_inertia_embedded_in_rotor=True,motor_selection_pending=True,electrical_reference='EMAX ECO II 2306 KV1900'),
 assumptions=P,unbudgeted_legacy_removals=unbudgeted_legacy_removals,manufacturing_release=False)
(OUT/'Massen_P11.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n')
(SIM/'p11_massen.json').write_text(json.dumps(payload,separators=(',',':'),ensure_ascii=False)+'\n')
(SIM/'p11_massen.js').write_text('globalThis.H01_P11_MASSEN='+json.dumps(payload,separators=(',',':'),ensure_ascii=False)+';\n')
with (OUT/'Kabelliste_P11.csv').open('w',newline='') as f:w=csv.DictWriter(f,lineterminator="\n",fieldnames=list(cable_rows[0]));w.writeheader();w.writerows(cable_rows)
bom={}
for o in parts:
    r=newmass.get(o.Name) or oldmass.get(o.Name);entry=bom.setdefault(o.BauteilID,dict(BauteilID=o.BauteilID,Anzahl=0,Masse_erfasst_g=0,Fehlende_Massenzuordnungen=0,Hinweis=''))
    entry['Anzahl']+=1
    if r:entry['Masse_erfasst_g']+=r['mass_kg']*1000
    else:entry['Fehlende_Massenzuordnungen']+=1
    if hasattr(o,'P11_Hinweis'):entry['Hinweis']=o.P11_Hinweis
with (OUT/'Stueckliste_P11.csv').open('w',newline='') as f:w=csv.DictWriter(f,lineterminator="\n",fieldnames=list(next(iter(bom.values()))));w.writeheader();w.writerows(bom.values())
report=dict(revision='P11',native_sha256=payload['source_native_sha256'],base_sha256=source_hash,parts=len(parts),removed=len(changes),replaced=len(removed)-len(changes),new_or_changed=len(records),changes=changes,invalid_inherited=[o.Name for o in parts if not o.Shape.isValid()],ratio=1,guide_rollers=2*len(P['roller_azimuths_deg']),guide_bearings=4*len(P['roller_azimuths_deg']),motor_selection_pending=True,manufacturing_release=False)
(OUT/'Aufbau_P11.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
A.closeDocument(d.Name)
assert hashlib.sha256(SRC.read_bytes()).hexdigest()==source_hash,'P10 archive was modified'
print(json.dumps({k:v for k,v in report.items() if k!='changes'},indent=2),flush=True)
