"""Detailed bolted metal airframe; no invented OEM envelopes.

Native PartDesign prototypes + placed App::Links. All joints have actual holes,
washers, nuts and screw geometry. This module deliberately excludes unavailable
powertrain/OEM parts rather than filling them with schematic shapes.
"""
import sys,json,math,csv,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';O.mkdir(exist_ok=True)
sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,Sketcher,Import
V=A.Vector;P=json.loads((H/'parameter.json').read_text());D=math.pi/180
doc=A.newDocument('QUAD_R380_D01_Rahmen');lib=doc.addObject('App::DocumentObjectGroup','Bauteilbibliothek');assembly=doc.addObject('App::DocumentObjectGroup','Montage');masters={};specs={};bom=[];connections=[];drills={}
phase_file=O/'Gewindephasen.json';phase_cache=json.loads(phase_file.read_text()).get('phases',{}) if phase_file.exists() else {}
def vec(v):return V(*v)
def rotation(columns):
    m=A.Matrix()
    for i in range(3):
        for j in range(3):setattr(m,f'A{i+1}{j+1}',columns[j][i])
    return A.Rotation(m)
def place(p=(0,0,0),rot=None):return A.Placement(vec(p),rot or A.Rotation())
def finish(body,feature):
    for old in body.Group:
        if old!=feature and hasattr(old,'Visibility'):old.Visibility=False
    body.Tip=feature;feature.Visibility=True;doc.recompute()
    if feature.Shape.isNull() or not feature.Shape.isValid() or len(feature.Shape.Solids)!=1:raise ValueError('Invalid feature '+feature.Name+': '+str(feature.State))
    return feature
def sketch(body,label,z=0,rot=None,p=(0,0,0)):
    s=body.newObject('Sketcher::SketchObject','SK_'+body.Name+'_'+label);s.Placement=place((p[0],p[1],z if p==(0,0,0) else p[2]),rot);return s
def block_geom(s,g):
    i=s.addGeometry(g,False);s.addConstraint(Sketcher.Constraint('Block',i));return i
def rectangle(s,w,h,x=0,y=0,r=0):
    if not r:
        pts=[V(x-w/2,y-h/2,0),V(x+w/2,y-h/2,0),V(x+w/2,y+h/2,0),V(x-w/2,y+h/2,0)]
        for i in range(4):block_geom(s,Part.LineSegment(pts[i],pts[(i+1)%4]))
    else:
        L=x-w/2;R=x+w/2;B=y-h/2;T=y+h/2
        for a,b in [((L+r,B),(R-r,B)),((R,B+r),(R,T-r)),((R-r,T),(L+r,T)),((L,T-r),(L,B+r))]:block_geom(s,Part.LineSegment(V(*a,0),V(*b,0)))
        for cx,cy,a0 in [(R-r,B+r,-90),(R-r,T-r,0),(L+r,T-r,90),(L+r,B+r,180)]:block_geom(s,Part.ArcOfCircle(Part.Circle(V(cx,cy,0),V(0,0,1),r),a0*D,(a0+90)*D))
def circles(s,points,diam):
    for x,y in points:block_geom(s,Part.Circle(V(x,y,0),V(0,0,1),diam/2))
def pad(b,s,length,label='Pad'):
    f=b.newObject('PartDesign::Pad','PD_'+b.Name+'_'+label);f.Profile=s;f.Length=length;s.Visibility=False;finish(b,f);return f
def pocket(b,s,depth,label='Pocket',through=False,reversed=False):
    f=b.newObject('PartDesign::Pocket','PD_'+b.Name+'_'+label);f.Profile=s;f.Length=depth;f.Type=1 if through else 0;f.Reversed=reversed;s.Visibility=False;finish(b,f);return f
def holes(b,points,diam,z,depth,label='Bohrungen',rot=None,p=(0,0,0),thread=None,thread_depth=None):
    s=sketch(b,label,z,rot,p);circles(s,points,diam)
    if not thread:return pocket(b,s,depth,label)
    doc.recompute();f=b.newObject('PartDesign::Hole','PD_'+b.Name+'_'+label);f.Profile=s;doc.recompute()
    f.ThreadType='ISOMetricProfile';doc.recompute();f.Threaded=True;f.ThreadSize=thread;doc.recompute()
    f.ThreadClass='6H';f.Depth=depth;f.ThreadDepthType='Dimension';f.ThreadDepth=thread_depth;f.DrillPoint='Angled';f.DrillPointAngle=118;doc.recompute();f.ModelThread=True;s.Visibility=False;finish(b,f);return f
def body(key,label,process='CNC, EN AW-6082 T6',density=2700):
    b=doc.addObject('PartDesign::Body',key);b.Label=label;lib.addObject(b);b.addProperty('App::PropertyString','Fertigung','D01');b.Fertigung=process;b.addProperty('App::PropertyString','Status','D01');b.Status='DETAILLIERT; BAUGRUPPENFREIGABE OFFEN';b.addProperty('App::PropertyString','Oberflaeche','D01');b.Oberflaeche='Entgraten 0.2–0.5; Ra3.2, Kontaktflaechen Ra1.6; Beschichtung im Mass beruecksichtigen';specs[key]=dict(id=key,label=label,process=process,density_kg_m3=density,material='EN AW-6082 T6' if density==2700 else 'Stahl');drills[key]=[];return b
def register(b):
    b.Visibility=False;masters[b.Name]=b;specs[b.Name]['volume_mm3']=b.Shape.Volume;specs[b.Name]['mass_kg']=b.Shape.Volume*specs[b.Name]['density_kg_m3']*1e-9;print('Bauteil',b.Name,'features',len(b.Group),'mass',round(specs[b.Name]['mass_kg'],3),flush=True)
    if len(masters)%2==0:doc.recompute();doc.saveAs(str(O/'D01_Teile_Zwischenstand.FCStd'))
def rotated_rectangle(s,length,width,centre_r,angle):
    co,si=math.cos(angle*D),math.sin(angle*D);points=[]
    for x,y in [(centre_r-length/2,-width/2),(centre_r+length/2,-width/2),(centre_r+length/2,width/2),(centre_r-length/2,width/2)]:points.append(V(x*co-y*si,x*si+y*co,0))
    for i in range(4):block_geom(s,Part.LineSegment(points[i],points[(i+1)%4]))
def flat(key,label,w,h,t,outline_r=3):
    b=body(key,label);s=sketch(b,'Kontur');rectangle(s,w,h,r=outline_r);pad(b,s,t);return b
def install(key,label,placement,group='Rahmen'):
    master=masters[key];l=doc.addObject('App::Link','I_'+str(len(bom)+1));l.Label=label;l.setLink(master);l.LinkPlacement=placement;l.Visibility=True;assembly.addObject(l);l.addProperty('App::PropertyString','BauteilID','D01');l.BauteilID=key
    bom.append(dict(instance=l.Name,label=label,id=key,group=group,mass_kg=specs[key]['mass_kg'],source='Normtabellen mit Helixgewinde' if key.startswith('ISO') else 'Parametrisches PartDesign-Bauteil',placement_mm=list(placement.Base),placement_quaternion=list(placement.Rotation.Q)))
    return l
def norm(key):
    if key in masters:return
    p=H/'Quellen/Normteile'/(key+'.brep');s=Part.Shape();s.read(str(p));assert s.isValid()
    b=doc.addObject('Part::Feature',key.replace('x','_L'));b.Label=key;b.Shape=s;b.Visibility=False;lib.addObject(b);masters[key]=b;specs[key]=dict(id=key,label=key,process='Kaufteil nach ISO; 10.9 / Mutter10 / Scheibe300HV, Zertifikat erforderlich',density_kg_m3=7850,material='Verguetungsstahl, Zinklamelle',volume_mm3=s.Volume,mass_kg=s.Volume*7850e-9)
def hardware(key,label,p,axis=(0,0,1),phase=0):
    fmt=lambda x:f'{0 if abs(x)<5e-7 else x:.6f}'
    cache_key=key+'@'+','.join(fmt(x) for x in p)+'|'+','.join(fmt(x) for x in axis)
    phase+=phase_cache.get(cache_key,0)
    norm(key);r=A.Rotation(V(0,0,1),vec(axis));r=A.Rotation(vec(axis),phase).multiply(r);return install(key,label,place(p,r),'Normteile')

# 1) Central plates: real holes, pocket, edge radii; no fused beam joints.
root_positions=[]
for ang in [45,135,225,315]:
    co,si=math.cos(ang*D),math.sin(ang*D)
    for r in P['root_bolt_radial_positions_mm']:
        for t in P['root_bolt_tangent_positions_mm']:root_positions.append((r*co-t*si,r*si+t*co))
post_positions=[(x+dx,y+dy) for x,y in P['post_xy_mm'] for dx in [-20,20] for dy in [-9,9]]
for key,label,upper in [('QD_P01','Zentralplatte oben',True),('QD_P02','Zentralplatte unten',False)]:
    b=flat(key,label,380,380,8,8);holes(b,root_positions+(post_positions if upper else []),6.6,8,8,'M6_Durchgang')
    s=sketch(b,'Zentralfenster',8);rectangle(s,140,90,r=10);pocket(b,s,8,'Fenster')
    s=sketch(b,'Formschluessige_Armsitze',0 if upper else 8)
    for ang in [45,135,225,315]:rotated_rectangle(s,180,50.2,225,ang)
    pocket(b,s,2,'Armsitze',reversed=upper)
    register(b)

# 2) Arms: actual square tube with radiused corners and retention bores.
L=math.sqrt(2)*P['motor_centres_half_spacing_mm']-P['arm_root_radius_mm']
b=body('QD_R01','Ausleger 50×50×3 mit Sicherungsbohrungen','EN755 Profil, Ablaengen, CNC-Bohrungen');s=sketch(b,'Rohrprofil');rectangle(s,50,50,r=4.5);rectangle(s,44,44,r=1.5);pad(b,s,L)
side_rot=rotation([(0,0,1),(0,-1,0),(1,0,0)])
holes(b,[(20,0),(70,0)],5.5,0,3.2,'Sicherung_M5',side_rot,(25,0,0));register(b)
b=flat('QD_E01','Eingepasstes Wurzel-Druckstueck 43.97×43.97×135',43.97,43.97,P['arm_insert_mm'][2],2)
holes(b,[(20,0),(70,0)],4.2,0,14,'M5_6H_Blind',side_rot,(21.985,0,0),'M5',12.5);register(b)

# 3) Upper/lower tip clamps; own PCD90 interface, NOT an invented motor flange.
tip_clamp_positions=[(x,y) for x in [-50,-10] for y in [-38,38]]
b=flat('QD_M01','Ausleger-Endtraeger oben, Projekteigenes IF90',120,110,20,5)
st=sketch(b,'Armsitz',0);rectangle(st,70,50.2,-35,0);pocket(b,st,2,'Armsitz',reversed=True)
holes(b,tip_clamp_positions,6.6,20,20,'Klemmbohrungen_M6')
pcd=[(45*math.cos(a*D),45*math.sin(a*D)) for a in range(0,360,45)]
holes(b,[(0,0)],42,20,20,'Servicebohrung')
holes(b,pcd,5,20,15,'IF90_M6_6H',thread='M6',thread_depth=12)
register(b)
b=flat('QD_M02','Ausleger-Endtraeger unten',120,110,12,5);st=sketch(b,'Armsitz',12);rectangle(st,70,50.2,-35,0);pocket(b,st,2,'Armsitz');holes(b,tip_clamp_positions,6.6,12,12,'Klemmbohrungen_M6');register(b)

# 4) One-piece machined deck columns, fully modelled through holes.
b=flat('QD_S01','Deckstuetze, aus Vollmaterial gefertigt',60,44,6,4);s=sketch(b,'Rohrschaft',6);circles(s,[(0,0)],25);pad(b,s,140,'Schaft');s=sketch(b,'Oberflansch',146);rectangle(s,60,44,r=4);pad(b,s,6,'Oberflansch')
tip=b.Tip;edges=[]
for idx,e in enumerate(tip.Shape.Edges,1):
    curve=e.Curve
    if hasattr(curve,'Radius') and abs(curve.Radius-12.5)<1e-6 and hasattr(curve,'Center') and any(abs(curve.Center.z-z)<1e-6 for z in [6,146]):edges.append('Edge'+str(idx))
if edges:
    ft=b.newObject('PartDesign::Fillet','PD_Stuetzenwurzel_R2');ft.Base=(tip,edges);ft.Radius=2;finish(b,ft)
holes(b,[(0,0)],17,152,152,'Leichtbaubohrung');holes(b,[(x,y) for x in [-20,20] for y in [-9,9]],6.6,152,152,'Flanschbohrungen_M6');register(b)

# 5) Deck beams, captive locking-nut cassettes and crush-proof deck collars.
b=body('QD_R02','Decktraeger 40×30×3, Laenge620','EN755 Profil, Ablaengen, Bohrungen');s=sketch(b,'Rechteckrohr');rectangle(s,40,30,r=4);rectangle(s,34,24,r=1);pad(b,s,620)
# This beam prototype is along Z; side X is tangential, side Y is vertical.
beam_side=rotation([(0,0,1),(1,0,0),(0,1,0)])
holes(b,[(x+310,0) for x in P['deck_bolt_x_mm']],8.2,0,3.2,'Deckhuelsen_oben',beam_side,(0,15,0))
beam_bottom=rotation([(0,0,1),(-1,0,0),(0,-1,0)])
holes(b,[(x+310,0) for x in P['deck_bolt_x_mm']],5.5,0,3.2,'Deckbolzen_unten',beam_bottom,(0,-15,0))
holes(b,[(x+310+dx,dy) for x in sorted(set(p[0] for p in P['post_xy_mm'])) for dx in [-20,20] for dy in [-9,9]],6.6,0,3.2,'Stuetze_M6',beam_bottom,(0,-15,0));register(b)
b=flat('QD_K01','Kassette fuer vier ISO7719-M6-Muttern',72,33.6,8,1)
holes(b,[(x,y) for x in [-20,20] for y in [-9,9]],6.6,8,8,'Durchgang_M6')
s=sketch(b,'Sechskantsitze',8)
for x in [-20,20]:
    for y in [-9,9]:
        pts=[V(x+10.2/math.sqrt(3)*math.cos(k*60*D),y+10.2/math.sqrt(3)*math.sin(k*60*D),0) for k in range(6)]
        for k in range(6):block_geom(s,Part.LineSegment(pts[k],pts[(k+1)%6]))
pocket(b,s,7.2,'Muttersitze')
tip=b.Tip;edges=[]
for i,e in enumerate(tip.Shape.Edges,1):
    bb=e.BoundBox
    if abs(bb.ZMin)<1e-6 and abs(bb.ZMax)<1e-6 and abs(abs(e.CenterOfMass.y)-16.8)<1e-6 and e.Length>65:edges.append('Edge'+str(i))
assert len(edges)==2
cf=b.newObject('PartDesign::Chamfer','PD_QD_K01_Freigang_0_8');cf.Base=(tip,edges);cf.Size=.8;finish(b,cf)
holes(b,[(-30,0),(30,0)],2.5,8,7.5,'Deckel_M3',thread='M3',thread_depth=7);register(b)
b=flat('QD_K02','Kassetten-Abdeckblech',72,33.6,1,1);holes(b,[(x,y) for x in [-20,20] for y in [-9,9]],6.6,1,1,'Bolzenoeffnungen_M6');holes(b,[(-30,0),(30,0)],3.4,1,1,'Deckelschrauben_M3');register(b)
b=body('QD_H01','Hut-Druckhuelse fuer Deckverschraubung','Drehteil EN AW-6082 T6');s=sketch(b,'Schaft');circles(s,[(0,0)],8);pad(b,s,27);s=sketch(b,'Bund',27);circles(s,[(0,0)],12);pad(b,s,2,'Bund');holes(b,[(0,0)],5.5,29,29,'Durchgang_M5');register(b)
b=flat('QD_D01','Personendeck 620×360×5',620,360,5,12);holes(b,[(x,y) for x in P['deck_bolt_x_mm'] for y in P['deck_beams_y_mm']],5.5,5,5,'Deckbohrungen_M5');register(b)

# Placement records: custom part prototypes remain hidden in their own library.
install('QD_P01','Zentralplatte oben',place((0,0,-87)));install('QD_P02','Zentralplatte unten',place((0,0,-141)))
for i,ang in enumerate([45,135,225,315]):
    co,si=math.cos(ang*D),math.sin(ang*D);rad=(co,si,0);tan=(-si,co,0);armrot=rotation([tan,(0,0,1),rad]);xyrot=A.Rotation(V(0,0,1),ang);rr=math.sqrt(2)*425
    origin=(140*co,140*si,-110);install('QD_R01',f'Ausleger {i+1}',place(origin,armrot));install('QD_E01',f'Druckstueck {i+1}',place(origin,armrot))
    install('QD_M01',f'Endtraeger oben {i+1}',place((rr*co,rr*si,-87),xyrot));install('QD_M02',f'Endtraeger unten {i+1}',place((rr*co,rr*si,-145),xyrot))
    for j,r in enumerate([155,215]):
        for k,t in enumerate([-35,35]):
            x,y=r*co-t*si,r*si+t*co
            bolt=hardware('ISO4762_M6x80','Wurzelklemmschraube',(x,y,-77.4));hardware('ISO7089_M6','Kopfscheibe',(x,y,-79));hardware('ISO7089_M6','Mutterscheibe',(x,y,-142.6));nut=hardware('ISO7719_M6','Ganzmetall-Sicherungsmutter',(x,y,-142.6),(0,0,-1));connections.append(dict(id=f'ROOT_{i}_{j}_{k}',bolt=bolt.Name,nut=nut.Name,diameter=6,pitch=1,nominal_bolt_length_mm=80,clamped_stack_mm=62,preload_target_N=8000,required_min_thread_turns=5))
    for j,(localx,localy) in enumerate(tip_clamp_positions):
        x=(rr+localx)*co-localy*si;y=(rr+localx)*si+localy*co
        bolt=hardware('ISO4762_M6x90','Endtraeger-Klemmschraube',(x,y,-65.4));hardware('ISO7089_M6','Kopfscheibe',(x,y,-67));hardware('ISO7089_M6','Mutterscheibe',(x,y,-146.6));nut=hardware('ISO7719_M6','Ganzmetall-Sicherungsmutter',(x,y,-146.6),(0,0,-1));connections.append(dict(id=f'TIP_{i}_{j}',bolt=bolt.Name,nut=nut.Name,diameter=6,pitch=1,nominal_bolt_length_mm=90,clamped_stack_mm=78,preload_target_N=6500,required_min_thread_turns=5))
    for j,r in enumerate([160,210]):
        x,y=r*co+26*tan[0],r*si+26*tan[1];hardware('ISO4762_M5x16','Druckstueck-Sicherung',(x,y,-110),tan);hardware('ISO7089_M5','Sicherungsscheibe',(r*co+25*tan[0],r*si+25*tan[1],-110),tan)

beamrot=rotation([(0,1,0),(0,0,1),(1,0,0)])
for y in P['deck_beams_y_mm']:install('QD_R02','Decktraeger',place((-310,y,88),beamrot))
for i,(x,y) in enumerate(P['post_xy_mm']):
    install('QD_S01','Deckstuetze',place((x,y,-79)));install('QD_K01','Sicherungsmutter-Kassette',place((x,y,76)));install('QD_K02','Kassettendeckel',place((x,y,84)))
    for dx in [-20,20]:
        for dy in [-9,9]:
            xx,yy=x+dx,y+dy
            hardware('ISO4762_M6x25','Stuetzenfuss M6',(xx,yy,-88.6),(0,0,-1));hardware('ISO7089_M6','Fussscheibe',(xx,yy,-88.6));hardware('ISO7719_M6','Fusssicherung',(xx,yy,-73))
            hardware('ISO4762_M6x20','Stuetzenkopf M6',(xx,yy,65.4),(0,0,-1));hardware('ISO7089_M6','Kopfscheibe Stuetze',(xx,yy,65.4));hardware('ISO7719_M6','Gefangene Sicherungsmutter',(xx,yy,76.8))
    for dx in [-30,30]:hardware('ISO4762_M3x8','Kassetten-Deckelschraube',(x+dx,y,85))
for y in P['deck_beams_y_mm']:
    for x in P['deck_bolt_x_mm']:
        install('QD_H01','Deck-Druckhuelse',place((x,y,76)));hardware('ISO4762_M5x50','Deckschraube',(x,y,111));hardware('ISO7089_M5','Deck-Kopfscheibe',(x,y,110));hardware('ISO7089_M5','Deck-Mutterscheibe',(x,y,72));hardware('ISO7719_M5','Deck-Sicherungsmutter',(x,y,72),(0,0,-1))
install('QD_D01','Personendeck',place((0,0,105)))
lib.Visibility=False;assembly.Visibility=True;doc.recompute()
native=O/'QuadR380_D01_Mechanik.FCStd';doc.saveAs(str(native))
Import.export([doc.getObject(r['instance']) for r in bom],str(O/'QuadR380_D01_Mechanik.step'))
partsdir=O/'Einzelteile';partsdir.mkdir(exist_ok=True)
for key,obj in masters.items():obj.Shape.exportStep(str(partsdir/(key+'.step')))
with (O/'Stueckliste.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,list(bom[0]));w.writeheader();w.writerows(bom)
bb=Part.Compound([doc.getObject(r['instance']).Shape for r in bom]).BoundBox
report=dict(revision=P['revision'],production_ready=False,scope='Detaillierter mechanischer Tragwerksbaustein; keine vollstaendige flugfaehige Fahrzeugbaugruppe',modeled_instances=len(bom),part_types=len(masters),parametric_custom_bodies=sum(1 for x in masters if not x.startswith('ISO')),mass_modeled_kg=sum(r['mass_kg'] for r in bom),bounds_mm=[bb.XLength,bb.YLength,bb.ZLength],all_instance_shapes_valid=all(doc.getObject(r['instance']).Shape.isValid() for r in bom),native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),omitted_instead_of_schematic=['Motoren','Motoradapter mit bestaetigtem OEM-Lochbild','Rotoren und Blattanschluesse','Regler und Elektronik','Batteriepack/BMS/Kontaktoren/Sicherungen','Herstellerabhaengiger Kabelbaum','Schutzgitter/Rueckhaltegeometrie','Landegestell'],interface_IF90_scope='Projekteigenes Anschlussbild, noch keine behauptete OEM-Kompatibilitaet',release_blockers=['OEM-Unterlagen abrufen und Bauteile technisch auswaehlen','Dynamische Lasten, Steifigkeit und Erregungen nachweisen','Schraubverbindungen mit Toleranzen, Vorspannung, Reibwerten und Ermuedung nachweisen','Vollstaendige Fahrzeugmasse und Energie schliessen'])
(O/'Pruefung.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));(O/'Bauteile.json').write_text(json.dumps(specs,indent=2,ensure_ascii=False));(O/'Verbindungen.json').write_text(json.dumps(connections,indent=2));(O/'Instanzen.json').write_text(json.dumps(bom,indent=2))
print(json.dumps(report,ensure_ascii=False),flush=True)
