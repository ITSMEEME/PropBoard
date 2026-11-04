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
doc=A.newDocument('QUAD_R380_D02_CFK');lib=doc.addObject('App::DocumentObjectGroup','Bauteilbibliothek');assembly=doc.addObject('App::DocumentObjectGroup','Montage');masters={};specs={};bom=[];connections=[];drills={}
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
    if len(masters)%2==0:doc.recompute();doc.saveAs(str(O/'D02_Teile_Zwischenstand.FCStd'))
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
    p=H/'Quellen/Normteile'/(key+'.brep');p=p if p.exists() else H.parent/'quad_r380_d01/Quellen/Normteile'/(key+'.brep');s=Part.Shape();s.read(str(p));assert s.isValid()
    b=doc.addObject('Part::Feature',key.replace('x','_L'));b.Label=key;b.Shape=s;b.Visibility=False;lib.addObject(b);masters[key]=b;specs[key]=dict(id=key,label=key,process='Kaufteil nach ISO; 10.9 / Mutter10 / Scheibe300HV, Zertifikat erforderlich',density_kg_m3=7850,material='Verguetungsstahl, Zinklamelle',volume_mm3=s.Volume,mass_kg=s.Volume*7850e-9)
def hardware(key,label,p,axis=(0,0,1),phase=0):
    fmt=lambda x:f'{0 if abs(x)<5e-7 else x:.6f}'
    cache_key=key+'@'+','.join(fmt(x) for x in p)+'|'+','.join(fmt(x) for x in axis)
    phase+=phase_cache.get(cache_key,0)
    norm(key);r=A.Rotation(V(0,0,1),vec(axis));r=A.Rotation(vec(axis),phase).multiply(r);return install(key,label,place(p,r),'Normteile')

# Reuse exact mechanical clamp geometry from coaxial P12, not a placeholder.
source=H.parent/'kreis_r04/mn1330_p12/Ausgabe/STEP'
source_manifest=[]
def imported(key,label,filename,density=2810,material='EN AW-7075 T6',shape=None):
    if shape is None:shape=Part.read(str(source/filename));source_manifest.append(dict(id=key,file=str((source/filename).relative_to(H.parent)),sha256=hashlib.sha256((source/filename).read_bytes()).hexdigest()))
    b=body(key,label,density=density);f=b.newObject('PartDesign::Feature','Bearbeitete_Quellgeometrie');f.Shape=shape;finish(b,f);specs[key]['material']=material;register(b);return b
for suffix in ['A','B']:imported('CFK_KLEMM_'+suffix,'P12 Rohrklemmhälfte '+suffix,'CFK-KLEMM-'+suffix+'.step')
imported('CFK_FILM','P12 Isolierzwischenlage','CFK-ZWISCHENLAGE.step',1900,'GFK-/Isolierfilm; Reibung/Kriechen offen')
# Imported geometry remains explicitly a source feature; no invented native feature history.
for k in ['CFK_KLEMM_A','CFK_KLEMM_B']:
 masters[k].addProperty('App::PropertyString','Quellstatus');masters[k].Quellstatus='Exakte P12-Geometrie; M4-Kernkonturen, Vorspannung und Toleranzen unqualifiziert'
cutlist=[]
def tube(key,length):
 b=body(key,'CBU20171005TG Rohrzuschnitt '+str(round(length,2)),process='CBU20171005TG zuschneiden, Kanten versiegeln; keine Querbohrung',density=P['cfk_density_assumption_kg_m3']);s=sketch(b,'Rohrprofil');circles(s,[(0,0)],20);circles(s,[(0,0)],17);pad(b,s,length);specs[key]['material']='CFK CBU20171005TG; Dichte angenommen';register(b)
def puttube(key,start,end,label):
 delta=vec(end)-vec(start);install(key,label,place(start,A.Rotation(V(0,0,1),delta)),'Carbonrohre');cutlist.append(dict(id=key,length_mm=delta.Length,stock_article=P['tube_article'],stock_length_mm=1000))
def socket(point,rot,label):
 for half in ['A','B']:install('CFK_KLEMM_'+half,label+' '+half,place(point,rot),'P12 Aluverbinder')
 install('CFK_FILM',label+' Isolierung',place(tuple(vec(point)+rot.multVec(V(0,0,5))),rot),'Isolierung')
 # Actual ISO screws, with legacy core-hole status recorded rather than declared proven thread fit.
 for i in range(4):
  a=math.radians(45+90*i);p=vec(point)+rot.multVec(V(15*math.cos(a),15*math.sin(a),1));hardware('ISO4762_M4x16',label+' Flansch M4',tuple(p),tuple(rot.multVec(V(0,0,1))))
 for y in [-18,18]:
  p=vec(point)+rot.multVec(V(8,y,20));hardware('ISO4762_M4x16',label+' Queranzug M4',tuple(p),tuple(rot.multVec(V(1,0,0))))
root_holes=[]
for a in [45,135,225,315]:
 co,si=math.cos(a*D),math.sin(a*D)
 for t in [-65,65]:root_holes.append((184*co-t*si,184*si+t*co))
for k in ['D02_CENTRAL_TOP','D02_CENTRAL_BOTTOM']:
 b=flat(k,'Zentralplatte '+k,380,380,8,8);holes(b,root_holes,6.6,8,8,'Wurzelbefestigung');register(b)
install('D02_CENTRAL_TOP','Zentralplatte oben',place((0,0,80)))
install('D02_CENTRAL_BOTTOM','Zentralplatte unten',place((0,0,-88)))
# Four-tube space cages retain the selected legacy 20/17 stock and split sockets.
flangepts=[]
for t in [-45,45]:
 for z in [-50,50]:
  for i in range(4):
   a=math.radians(45+90*i);flangepts.append((t+15*math.cos(a),z+15*math.sin(a)))
for key,bolt_t in [('D02_ROOT',65),('D02_TIP',45)]:
 b=flat(key,'Ausleger Schott '+key,160,160,8,3);holes(b,flangepts,3.3,8,8,'M4_Kernloecher_Liefergewinde_offen')
 # Native nominal M6 threads in vertical edges, exactly aligned with upper/lower plates.
 for sign in [-1,1]:holes(b,[(-bolt_t,0),(bolt_t,0)],5,0,15,'M6_Stirn_'+str(sign),rot=A.Rotation(V(0,0,1),V(0,sign,0)),p=(0,sign*80,4),thread='M6',thread_depth=13)
 register(b)
tube('D02_ARM_TUBE',342)
# Future OEM plate has a real but project-specific mounting pattern; no motor compatibility claim.
b=flat('D02_MOTOR_PLATE','Endplatte mit IF90, OEM Adapter offen',160,150,8,5);holes(b,[(-45,57),(45,57)],6.6,8,8,'Schottanschluss');holes(b,[(0,0)],42,8,8,'Service');holes(b,[(45*math.cos(i*math.pi/4),45*math.sin(i*math.pi/4)) for i in range(8)],5,8,7,'IF90',thread='M6',thread_depth=6);register(b)
for a in [45,135,225,315]:
 u=V(math.cos(a*D),math.sin(a*D),0);v=V(-u.y,u.x,0);rot=rotation([tuple(v),(0,0,1),tuple(u)])
 install('D02_ROOT','Wurzelschott '+str(a),place(tuple(u*180),rot));install('D02_TIP','Endschott '+str(a),place(tuple(u*540),rot))
 for t in [-45,45]:
  for z in [-50,50]:
   offset=v*t+V(0,0,z);socket(tuple(u*188+offset),rot,f'Wurzel {a}/{t}/{z}');back=rot.multiply(A.Rotation(V(0,1,0),180));socket(tuple(u*540+offset),back,f'Ende {a}/{t}/{z}');puttube('D02_ARM_TUBE',tuple(u*193+offset),tuple(u*535+offset),f'Armrohr {a}/{t}/{z}')
 for t in [-65,65]:
  xy=u*184+v*t
  for sign in [-1,1]:hardware('ISO4762_M6x20','Zentralplatte M6',tuple(xy+V(0,0,sign*89.6)),(0,0,sign));hardware('ISO7089_M6','Scheibe Zentralplatte',tuple(xy+V(0,0,88 if sign>0 else -89.6)),(0,0,1))
 # Motor plate local X=tangent, Y=-radial; bottom contact at z80.
 caprot=rotation([tuple(v),tuple(-u),(0,0,1)]);install('D02_MOTOR_PLATE','Motorplatte '+str(a),place(tuple(u*(425*math.sqrt(2))+V(0,0,80)),caprot))
 for t in [-45,45]:hardware('ISO4762_M6x20','Endplatte M6',tuple(u*544+v*t+V(0,0,89.6)));hardware('ISO7089_M6','Endplatte Scheibe',tuple(u*544+v*t+V(0,0,88)))
# Continuous upper adjustment rails and two independent foot carriages.
tube('D02_RAIL',760)
for y in [-75,75]:puttube('D02_RAIL',(-380,y,220),(380,y,220),'Verstellschiene '+str(y))
# Halves use the coaxial split-clamp principle, resized as through-bolt sliding saddles.
for sign,key in [(1,'D02_SLIDER_TOP'),(-1,'D02_SLIDER_BOTTOM')]:
 b=body(key,'Fußschlitten '+('oben' if sign>0 else 'unten'));s=sketch(b,'Backenumriss',.25 if sign>0 else -18);rectangle(s,60,54,r=3);pad(b,s,17.75)
 s=sketch(b,'Rohrsitz',0,rot=A.Rotation(V(0,0,1),V(1,0,0)),p=(30,0,0));circles(s,[(0,0)],20.6);pocket(b,s,60,'Rohrsitz')
 holes(b,[(x,y) for x in [-18,18] for y in [-20,20]],5.5,18 if sign>0 else -.25,17.75,'M5_Durchgang');register(b)
# Insulating sleeve, slit, fully distinct from CFRP; exact radial gap nominal 0.3.
s=Part.makeCylinder(10.3,60).cut(Part.makeCylinder(10,62,V(0,0,-1))).cut(Part.makeBox(12,.5,62,V(0,-.25,-1)))
imported('D02_SLIDER_FILM','Anpassbare Isolierhülse Fußschlitten','',1900,'GFK-/Isolierfilm; Auswahl offen',s)
b=flat('D02_FOOT','Fußplatte 300 x 140',140,300,5,12);holes(b,[(x,y+d) for y in [-75,75] for x in [-18,18] for d in [-20,20]],5.5,5,5,'M5_Schlitten');register(b)
for cx in P['foot_centres_x_mm']:
 install('D02_FOOT','Fußplatte '+str(cx),place((cx,0,238)),'Fußsystem')
 for y in [-75,75]:
  for key in ['D02_SLIDER_TOP','D02_SLIDER_BOTTOM']:install(key,'Verstellbacke '+str(cx)+'/'+str(y),place((cx,y,220)),'Fußsystem')
  install('D02_SLIDER_FILM','Isolierung Schlitten',place((cx-30,y,220),A.Rotation(V(0,0,1),V(1,0,0))),'Isolierung')
  for dx in [-18,18]:
   for dy in [-20,20]:
    x=dx+cx;yy=y+dy;hardware('ISO4762_M5x50','Fußschlitten M5',(x,yy,244));hardware('ISO7089_M5','Scheibe Fuß oben',(x,yy,243));hardware('ISO7089_M5','Scheibe Fuß unten',(x,yy,201));hardware('ISO7719_M5','Sicherungsmutter Fuß',(x,yy,201),(0,0,-1))
# Fixed rail supports: actual legacy sockets on machined end brackets, inclined CFK stays.
stays=[]
for sign in [-1,1]:
 for y in [-75,75]:
  low=V(sign*150,y,104);high=V(sign*385,y,170);u=high-low;u.normalize();length=(high-low).Length-80
  key='D02_STAY_TUBE'
  if key not in masters:tube(key,length)
  # Each support is a detailed solid with separate bosses and actual hole pattern.
  for which,point,direction in [('LOW',low,u),('HIGH',high,-u)]:
   k='D02_'+which+'_'+('P' if sign>0 else 'M')+'_'+('P' if y>0 else 'M')
   if which=='LOW':base=Part.makeBox(54,54,16,V(sign*150-27,y-27,88))
   else:base=Part.makeBox(8,74,116,V(385 if sign>0 else -393,y-37,145))
   boss=Part.makeCone(14,21,35,point,direction);shape=base.fuse(boss).removeSplitter();rot=A.Rotation(V(0,0,1),direction);face=point+direction*35
   for i in range(4):
    a=(45+90*i)*D;p=face+rot.multVec(V(15*math.cos(a),15*math.sin(a),0));shape=shape.cut(Part.makeCylinder(1.65,12,p,-direction))
   if which=='LOW':
    for xx in [-18,18]:
     for yy in [-18,18]:shape=shape.cut(Part.makeCylinder(3.3,18,V(sign*150+xx,y+yy,87)))
   else:
    for i in range(4):
     a=(45+90*i)*D;p=V(sign*385,y,220)+A.Rotation(V(0,0,1),V(-sign,0,0)).multVec(V(15*math.cos(a),15*math.sin(a),0));shape=shape.cut(Part.makeCylinder(1.65,10,p,V(sign,0,0)))
   imported(k,'Gefräster CFK-Stützenknoten '+which,'',2810,'EN AW-7075 T6',shape);install(k,'Schienenstütze '+which,place());socket(tuple(face),rot,'Stützenport '+k)
  socket((sign*385,y,220),A.Rotation(V(0,0,1),V(-sign,0,0)),'Schienenende')
  puttube(key,tuple(low+u*40),tuple(high-u*40),'Schienenstrebe')
  stays.append(dict(low=tuple(low),high=tuple(high),tube_length_mm=length))
# Add real mounting clearances and screws for the lower stay nodes in the central top plate.
b=masters['D02_CENTRAL_TOP'];holes(b,[(sign*150+dx,y+dy) for sign in [-1,1] for y in [-75,75] for dx in [-18,18] for dy in [-18,18]],6.6,8,8,'Strebenfuesse');specs[b.Name]['volume_mm3']=b.Shape.Volume;specs[b.Name]['mass_kg']=b.Shape.Volume*2700e-9
for row in bom:
 if row['id']==b.Name:row['mass_kg']=specs[b.Name]['mass_kg']
for sign in [-1,1]:
 for y in [-75,75]:
  for dx in [-18,18]:
   for dy in [-18,18]:
    x=sign*150+dx;yy=y+dy;hardware('ISO4762_M6x40','Stützenfuß M6',(x,yy,105.6));hardware('ISO7089_M6','Stützenfuß Scheibe oben',(x,yy,104));hardware('ISO7089_M6','Stützenfuß Scheibe unten',(x,yy,78.4));hardware('ISO7719_M6','Stützenfuß Mutter',(x,yy,78.4),(0,0,-1))
control=doc.addObject('App::FeaturePython','Fussverstellung')
control.addProperty('App::PropertyFloatConstraint','Links','Verstellung');control.Links=(-200,-250,-130,1)
control.addProperty('App::PropertyFloatConstraint','Rechts','Verstellung');control.Rechts=(200,130,250,1)
for row in bom:
 if any(word in row['label'] for word in ['Fuß','Schlitten','Verstellbacke']):
  x=row['placement_mm'][0];side='Links' if x<0 else 'Rechts';base=-200 if x<0 else 200
  row['foot_side']=side;row['foot_base_x_mm']=base
  doc.getObject(row['instance']).setExpression('LinkPlacement.Base.x','Fussverstellung.'+side+f' + ({x-base:.8f})')
doc.recompute();native=O/'QuadR380_D02_CFK.FCStd';doc.saveAs(str(native));Import.export([doc.getObject(r['instance']) for r in bom],str(O/'QuadR380_D02_CFK.step'))
for key,master in masters.items():
 assert master.Shape.isValid() and len(master.Shape.Solids)==1,key
 master.Shape.exportStep(str(O/(key+'.step')))
for name,data in [('Instanzen.json',bom),('Bauteile.json',specs),('CFK_Zuschnitt.json',cutlist),('Quellteile.json',source_manifest),('Schienenstreben.json',stays)]: (O/name).write_text(json.dumps(data,indent=2,ensure_ascii=False))
with (O/'Stueckliste.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=bom[0].keys(),delimiter=';');w.writeheader();w.writerows(bom)
report=dict(production_ready=False,scope='D02 CFK/Fußplatten mechanischer Entwicklungsstand',modeled_instances=len(bom),part_types=len(masters),mass_modeled_kg=sum(r['mass_kg'] for r in bom),native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),legacy_clamps_exact=True,cfk_article=P['tube_article'],oem_powertrain_integrated=False,not_inherited_from_D01=['Kollisionsfreigabe','Gewindepaarungen','Traglastscreen','Montageprüfung'],open_items=['CFK Kennwerte/Klemmpressung und Gesamttragfähigkeit','vollständige D02 Kollisions-/Gewinde-/Montageprüfung','Gewindeausführungen der übernommenen P12-Klemmen und Knoten schließen','OEM Antrieb, Rotoren, Akku und vollständiger Kabelbaum','Schutz, Landegestell und Rotorfreiraum'])
(O/'Status.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print(json.dumps(report),flush=True)
