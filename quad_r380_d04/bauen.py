"""D03 Carbonrahmen mit Aluminiumverbindern und indexierten Fußplatten.

Native PartDesign prototypes + placed App::Links; previous P12 core-only
thread interfaces remain explicitly open. This module excludes unavailable
powertrain/OEM parts rather than filling them with schematic shapes.
"""
import sys,json,math,csv,hashlib,os
from pathlib import Path
H=Path(__file__).resolve().parent;O=Path(os.environ.get('D04_OUTPUT_DIR',str(H/'Ausgabe')));O.mkdir(exist_ok=True)
sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,Sketcher,Import
V=A.Vector;P=json.loads((H/'parameter.json').read_text());D=math.pi/180
BASE=H.parent/'quad_r380_d03';doc=A.openDocument(str(BASE/'Ausgabe/QuadR380_D03_CFK.FCStd'));doc.saveAs(str(O/'QuadR380_D04_CFK.FCStd'));doc.Label='Quad R380 D04 – CFK-Zentralrahmen'
lib=doc.getObject('Bauteilbibliothek');assembly=doc.getObject('Montage');specs=json.loads((BASE/'Ausgabe/Bauteile.json').read_text());bom=json.loads((BASE/'Ausgabe/Instanzen.json').read_text());masters={r['id']:doc.getObject(r['instance']).LinkedObject for r in bom};connections=[];drills={}

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
    if len(masters)%2==0:doc.recompute();doc.saveAs(str(O/'D04_Teile_Zwischenstand.FCStd'))
def rotated_rectangle(s,length,width,centre_r,angle):
    co,si=math.cos(angle*D),math.sin(angle*D);points=[]
    for x,y in [(centre_r-length/2,-width/2),(centre_r+length/2,-width/2),(centre_r+length/2,width/2),(centre_r-length/2,width/2)]:points.append(V(x*co-y*si,x*si+y*co,0))
    for i in range(4):block_geom(s,Part.LineSegment(points[i],points[(i+1)%4]))
def flat(key,label,w,h,t,outline_r=3):
    b=body(key,label);s=sketch(b,'Kontur');rectangle(s,w,h,r=outline_r);pad(b,s,t);return b
def install(key,label,placement,group='Rahmen'):
    master=masters[key];l=doc.addObject('App::Link','D04_I_'+str(len(bom)+1));l.Label=label;l.setLink(master);l.LinkPlacement=placement;l.Visibility=True;assembly.addObject(l);l.addProperty('App::PropertyString','BauteilID','D01');l.BauteilID=key
    bom.append(dict(instance=l.Name,label=label,id=key,group=group,mass_kg=specs[key]['mass_kg'],source='Normtabellen mit Helixgewinde' if key.startswith('ISO') else 'Parametrisches PartDesign-Bauteil',placement_mm=list(placement.Base),placement_quaternion=list(placement.Rotation.Q)))
    return l
def norm(key):
    if key in masters:return
    p=H/'Quellen/Normteile'/(key+'.brep');p=p if p.exists() else BASE/'Quellen/Normteile'/(key+'.brep');p=p if p.exists() else H.parent/'quad_r380_d02/Quellen/Normteile'/(key+'.brep');p=p if p.exists() else H.parent/'quad_r380_d01/Quellen/Normteile'/(key+'.brep');s=Part.Shape();s.read(str(p));assert s.isValid()
    b=doc.addObject('Part::Feature',key.replace('x','_L'));b.Label=key;b.Shape=s;b.Visibility=False;lib.addObject(b);masters[key]=b;specs[key]=dict(id=key,label=key,process='Kaufteil nach ISO; 10.9 / Mutter10 / Scheibe300HV, Zertifikat erforderlich',density_kg_m3=7850,material='Verguetungsstahl, Zinklamelle',volume_mm3=s.Volume,mass_kg=s.Volume*7850e-9)
def hardware(key,label,p,axis=(0,0,1),phase=0):
    fmt=lambda x:f'{0 if abs(x)<5e-7 else x:.6f}'
    cache_key=key+'@'+','.join(fmt(x) for x in p)+'|'+','.join(fmt(x) for x in axis)
    phase+=phase_cache.get(cache_key,0)
    norm(key);r=A.Rotation(V(0,0,1),vec(axis));r=A.Rotation(vec(axis),phase).multiply(r);return install(key,label,place(p,r),'Normteile')

BEFORE=json.loads(json.dumps(bom));oldpairs=json.loads((BASE/'Ausgabe/Gewindepruefung.json').read_text())['pairs'];digest=lambda obj:hashlib.sha256(obj.Shape.exportBrepToString().encode()).hexdigest()
prior=[]
for q in oldpairs:
 a=doc.getObject(q['bolt']);b=doc.getObject(q['mate']);rel=a.LinkPlacement.inverse().multiply(b.LinkPlacement)
 prior.append(dict(result=q,master_a_sha256=digest(a.LinkedObject),master_b_sha256=digest(b.LinkedObject),relative_placement=list(rel.Base)+list(rel.Rotation.Q)))
# Remove both broad plates and every obsolete attachment to them.
remove=[]
for r in bom:
 if r['id'] in ['D02_CENTRAL_TOP','D02_CENTRAL_BOTTOM','D02_STAY_TUBE'] or r['id'].startswith('D02_LOW_') or r['label'].startswith('Stützenport D02_') or r['label'].startswith('Stützenfuß '):remove.append(r['instance'])
for name in remove:doc.removeObject(name)
bom[:]=[r for r in bom if r['instance'] not in remove]
newpairs=[];cutlist=[];prototype_pairs={}
def setmaterial(b,material):specs[b.Name]['material']=material

def raw_part(key,label,shape):
 b=body(key,label,'CNC, EN AW-7075 T6',2810);f=b.newObject('PartDesign::Feature','CNC_Grundkoerper');f.Shape=shape;finish(b,f);setmaterial(b,'EN AW-7075 T6');return b

def tube(key,length):
 b=body(key,'CBU20171005TG Zuschnitt '+str(round(length,3)),'Sägen, Enden versiegeln; keine Querbohrung',1600);s=sketch(b,'Rohrprofil');circles(s,[(0,0)],20);circles(s,[(0,0)],17);pad(b,s,length);setmaterial(b,'CFK CBU20171005TG; Dichte1600 angenommen');register(b)

def puttube(key,start,end,label):
 delta=vec(end)-vec(start);return install(key,label,place(start,A.Rotation(V(0,0,1),delta)),'Carbonrohre')

def socket(point,rot,label,mate,feature):
 for half in ['A','B']:install('CFK_KLEMM_'+half,label+' '+half,place(point,rot),'P12 Aluverbinder')
 install('CFK_FILM',label+' Isolierung',place(tuple(vec(point)+rot.multVec(V(0,0,5))),rot),'Isolierung')
 for i in range(4):
  a=math.radians(45+90*i);p=vec(point)+rot.multVec(V(15*math.cos(a),15*math.sin(a),1));l=hardware('ISO4762_M4x10',label+' Flansch M4',tuple(p),tuple(rot.multVec(V(0,0,1))))
  newpairs.append(dict(bolt=l.Name,mate=mate,hole_suffix=feature,family='D04 M4 Flansch'))
 for y in [-18,18]:
  p=vec(point)+rot.multVec(V(8,y,20));hardware('ISO4762_M4x16',label+' Queranzug M4',tuple(p),tuple(rot.multVec(V(1,0,0))))

# Eight compact metal nodes replace the large plates: three perpendicular socket ports.
core_pitch=[(15*math.cos(i*math.pi/2),15*math.sin(i*math.pi/2)) for i in range(4)]
h=math.sqrt(.5);xy=[V(h,h,0),V(-h,h,0)];pitch=[(15*math.cos((45+90*i)*D),15*math.sin((45+90*i)*D)) for i in range(4)]
for sign in [-1,1]:
 key='D04_CORE_'+('TOP' if sign>0 else 'BOTTOM');dirs=xy+[V(0,0,-sign)]
 shape=Part.makeSphere(14)
 for axis in dirs:
  shape=shape.fuse(Part.makeCone(8,21,15,V(),axis)).fuse(Part.makeCylinder(21,10,axis*15,axis))
 # Narrow ribbed caps connect to the existing two M6 edge threads in each root bulkhead.
 bar=Part.makeBox(160,16,6,V(-80,-47,-30));bridge_pts=[V(-8,-39,-28),V(-8,-39,-20),V(-8,0,0),V(-8,0,-12)];bridge=Part.Face(Part.makePolygon(bridge_pts+[bridge_pts[0]])).extrude(V(16,0,0))
 ribpts=[V(-45,-41,-25),V(45,-41,-25),V(0,-41,-8)];rib=Part.Face(Part.makePolygon(ribpts+[ribpts[0]])).extrude(V(0,4,0));support=bar.fuse(bridge).fuse(rib)
 if sign<0:support=support.mirror(V(),V(0,0,1))
 shape=shape.fuse(support).removeSplitter();b=raw_part(key,'CFK-Rahmenknoten '+str(sign),shape)
 holes(b,[(-65,-39),(65,-39)],6.6,-24 if sign>0 else 30,6,'M6_Kappenanschluss')
 for i,axis in enumerate(dirs):holes(b,core_pitch,3.3,0,11,'Port_M4_'+str(i),rot=A.Rotation(V(0,0,1),axis),p=tuple(axis*25),thread='M4',thread_depth=10)
 register(b)

nodes={};R=145;zlevel=110
for a in [45,135,225,315]:
 u=V(math.cos(a*D),math.sin(a*D),0);v=V(-u.y,u.x,0);rot=rotation([tuple(v),tuple(-u),(0,0,1)])
 for sign in [-1,1]:
  pos=u*R+V(0,0,sign*zlevel);key='D04_CORE_'+('TOP' if sign>0 else 'BOTTOM');l=install(key,'Zentralrahmen Knoten '+str(a)+'/'+str(sign),place(tuple(pos),rot),'CFK-Zentralrahmen');nodes[a,sign]=dict(pos=pos,rot=rot,instance=l.Name)
 # Retain and relocate existing M6 root/cap hardware to the narrow six-mm caps.
for r in bom:
 if r['label'] in ['Zentralplatte M6','Scheibe Zentralplatte']:
  obj=doc.getObject(r['instance']);p=obj.LinkPlacement;sgn=1 if p.Base.z>0 else -1;p.Base.z=sgn*87.6 if r['label']=='Zentralplatte M6' else (86 if sgn>0 else -87.6);obj.LinkPlacement=p;r['label']='CFK-Kappe M6' if r['label']=='Zentralplatte M6' else 'CFK-Kappe Scheibe'
  if r['label']=='CFK-Kappe M6':
   choices=[q for q in bom if q['id']=='D02_ROOT' and (vec(q['placement_mm'])-obj.LinkPlacement.Base).Length<130];assert len(choices)==1
   newpairs.append(dict(bolt=obj.Name,mate=choices[0]['instance'],hole_suffix='M6_Stirn_'+str(sgn),family='D04 Root M6'))
# Four edges per layer and four verticals, with 30-mm engagement at every P12 socket.
core_edges=[]
angles=[45,135,225,315]
for sign in [-1,1]:
 for i,a in enumerate(angles):core_edges.append(((a,sign),(angles[(i+1)%4],sign)))
for a in angles:core_edges.append(((a,-1),(a,1)))
for index,(aa,bb) in enumerate(core_edges):
 na,nb=nodes[aa],nodes[bb];direction=nb['pos']-na['pos'];length=direction.Length;direction.normalize();key='D04_TUBE_RING' if aa[1]==bb[1] else 'D04_TUBE_VERTICAL'
 if key not in masters:tube(key,length-60)
 for node,axis in [(na,direction),(nb,-direction)]:
  local=node['rot'].inverted().multVec(axis);options=xy+[V(0,0,-aa[1] if node is na else -bb[1])];port=max(range(3),key=lambda k:options[k].dot(local));assert options[port].dot(local)>.999999
  localrot=A.Rotation(V(0,0,1),options[port]);rot=node['rot'].multiply(localrot).multiply(A.Rotation(V(0,0,1),45));socket(tuple(node['pos']+axis*25),rot,'Kernport '+str(index)+'/'+node['instance'],node['instance'],'Port_M4_'+str(port))
 puttube(key,tuple(na['pos']+direction*30),tuple(nb['pos']-direction*30),'Carbon Zentralrahmen '+str(index))

# Two split saddles support four inclined stays directly on the upper CFK tubes.
xframe=R/math.sqrt(2)
def finish_cfk_seat(b,sx):
 previous=b.Shape.copy();result=previous.cut(Part.makeCylinder(10.3,90,V(sx*xframe,-45,110),V(0,1,0))).removeSplitter();f=b.newObject('PartDesign::Feature','CNC_Rohrsitz_20_6');f.Shape=result;f.addProperty('App::PropertyLength','Bohrdurchmesser','Fertigung');f.Bohrdurchmesser=20.6;f.addProperty('App::PropertyLength','Bearbeitungslaenge','Fertigung');f.Bearbeitungslaenge=90;finish(b,f)
def saddle_holes(sx):return [(sx*xframe-sx*18,-32),(sx*xframe-sx*18,32),(sx*xframe+sx*18,0)]
low_points={};stay_axes={}
for sx in [-1,1]:
 for sy in [-1,1]:
  low=V(sx*xframe,sy*25,126.25);high=V(sx*385,sy*75,170);u=high-low;u.normalize();low_points[sx,sy]=low;stay_axes[sx,sy]=u
for sx in [-1,1]:
 key='D04_SADDLE_TOP_'+str(sx).replace('-','M');b=body(key,'Gemeinsamer Carbon-Strebensattel oben '+str(sx),'CNC EN AW-7075 T6',2810)
 s=sketch(b,'Sattelkontur',110.25);rectangle(s,50,80,x=sx*xframe,r=3);pad(b,s,16)
 # Cylinder cut normal toY; its upper half forms a true measured-OD clamp seat.
 for sy in [-1,1]:
  low=low_points[sx,sy];u=stay_axes[sx,sy];previous=b.Shape.copy();f=b.newObject('PartDesign::Feature','Portkegel_'+str(sy).replace('-','M'));f.Shape=previous.fuse(Part.makeCone(14,21,35,low,u)).removeSplitter();finish(b,f)
 finish_cfk_seat(b,sx)
 holes(b,saddle_holes(sx),6.6,126.25,16,'M6_Klemmung')
 for sy in [-1,1]:
  low=low_points[sx,sy];u=stay_axes[sx,sy];holes(b,pitch,3.3,0,12,'Strebenport_'+str(sy),rot=A.Rotation(V(0,0,1),u),p=tuple(low+u*35),thread='M4',thread_depth=10)
 setmaterial(b,'EN AW-7075 T6');register(b);top=install(key,'CFK-Strebensattel oben '+str(sx),place(),'CFK-Zentralrahmen')
 key='D04_SADDLE_BOTTOM_'+str(sx).replace('-','M');b=body(key,'Gemeinsamer Carbon-Strebensattel unten '+str(sx),'CNC EN AW-7075 T6',2810);s=sketch(b,'Sattelkontur',94);rectangle(s,50,80,x=sx*xframe,r=3);pad(b,s,15.75);finish_cfk_seat(b,sx);holes(b,saddle_holes(sx),6.6,109.75,15.75,'M6_Klemmung');setmaterial(b,'EN AW-7075 T6');register(b);install(key,'CFK-Strebensattel unten '+str(sx),place(),'CFK-Zentralrahmen')
 # Slit sleeve covers the80mm saddle length; no metal-to-CFK contact assumed.
 sleeve=Part.makeCylinder(10.3,80).cut(Part.makeCylinder(10,82,V(0,0,-1))).cut(Part.makeBox(12,.5,82,V(0,-.25,-1)))
 key='D04_SADDLE_FILM'
 if key not in masters:
  b=body(key,'Isolierlage Strebensattel','Anpassen an gemessenen Rohr-OD',1900);f=b.newObject('PartDesign::Feature','Geschlitzte_Huelse');f.Shape=sleeve;finish(b,f);setmaterial(b,'GFK-/Isolierfilm; Auswahl und Kriechen offen');register(b)
 install(key,'Isolierlage zentraler Strebensattel',place((sx*xframe,-40,110),A.Rotation(V(0,0,1),V(0,1,0))),'Isolierung')
 for px,py in saddle_holes(sx):
  p=(px,py,127.85);bolt=hardware('ISO4762_M6x45','Zentraler Sattel M6',p);hardware('ISO7089_M6','Sattel Scheibe oben',(p[0],p[1],126.25));hardware('ISO7089_M6','Sattel Scheibe unten',(p[0],p[1],92.4));nut=hardware('ISO7719_M6','Sattel Sicherungsmutter',(p[0],p[1],92.4),(0,0,-1));newpairs.append(dict(bolt=bolt.Name,mate=nut.Name,family='D04 Saddle nut M6'))
 for sy in [-1,1]:socket(tuple(low_points[sx,sy]+stay_axes[sx,sy]*35),A.Rotation(V(0,0,1),stay_axes[sx,sy]),'Unterer Strebenport '+str(sx)+'/'+str(sy),top.Name,'Strebenport_'+str(sy))
# Rebuild the four upper metal brackets around the new inclined stay axes.
for sx in [-1,1]:
 for sy in [-1,1]:
  high=V(sx*385,sy*75,170);u=-stay_axes[sx,sy];key='D04_HIGH_'+('P' if sx>0 else 'M')+'_'+('P' if sy>0 else 'M');b=body(key,'Schienen-Endknoten '+str(sx)+'/'+str(sy),'CNC EN AW-7075 T6',2810)
  s=sketch(b,'Endplatte',145);rectangle(s,8,90,x=sx*389,y=sy*75);pad(b,s,116);previous=b.Shape.copy();f=b.newObject('PartDesign::Feature','Portkegel');f.Shape=previous.fuse(Part.makeCone(14,21,35,high,u)).removeSplitter();finish(b,f)
  holes(b,pitch,3.3,0,8,'Schienenflansch_M4',rot=A.Rotation(V(0,0,1),V(-sx,0,0)),p=(sx*385,sy*75,220),thread='M4',thread_depth=8)
  holes(b,[(-6,0),(6,0)],4.5,0,8,'Rasterleiste_M4_Durchgang',rot=A.Rotation(V(0,0,1),V(sx,0,0)),p=(sx*393,sy*110,220))
  holes(b,pitch,3.3,0,12,'Strebenport_M4',rot=A.Rotation(V(0,0,1),u),p=tuple(high+u*35),thread='M4',thread_depth=10);setmaterial(b,'EN AW-7075 T6');register(b)
  old='D02_HIGH_'+('P' if sx>0 else 'M')+'_'+('P' if sy>0 else 'M');row=next(r for r in bom if r['id']==old);obj=doc.getObject(row['instance']);obj.setLink(b);obj.BauteilID=key;row['id']=key;row['label']='Schienen-Endknoten D04';socket(tuple(high+u*35),A.Rotation(V(0,0,1),u),'Oberer Strebenport '+str(sx)+'/'+str(sy),obj.Name,'Strebenport_M4')
  length=(high-low_points[sx,sy]).Length-80;key='D04_TUBE_STAY'
  if key not in masters:tube(key,length)
  puttube(key,tuple(low_points[sx,sy]+stay_axes[sx,sy]*40),tuple(high+u*40),'Carbon Schienenstrebe D04')
# Keep original foot-system/rail flange proof records; changed masters will be retested.
for prior_record in prior:
 q=prior_record['result']
 if q['family']=='Rail flange M4':newpairs.append(dict(bolt=q['bolt'],mate=q['mate'],hole_suffix='Schienenflansch_M4',family='D04 Rail flange M4'))

# Remove unused solid prototypes, including the two old large plates themselves.
used={r['id'] for r in bom};usedobjects={masters[k].Name for k in used}
for obj in list(lib.Group):
 if obj.Name not in usedobjects:
  if obj.TypeId=='PartDesign::Body':
   for child in reversed(list(obj.Group)):doc.removeObject(child.Name)
  doc.removeObject(obj.Name)
specs={k:v for k,v in specs.items() if k in used};masters={k:v for k,v in masters.items() if k in used}
for row in bom:
 obj=doc.getObject(row['instance']);row['mass_kg']=specs[row['id']]['mass_kg'];row['placement_mm']=list(obj.LinkPlacement.Base);row['placement_quaternion']=list(obj.LinkPlacement.Rotation.Q)
 if row['group']=='Carbonrohre':cutlist.append(dict(instance=row['instance'],id=row['id'],length_mm=obj.LinkedObject.Shape.BoundBox.ZLength,article=P['tube_article'],stock_mm=1000))
for obj in masters.values():
 if obj.TypeId=='PartDesign::Body':
  for f in obj.Group:
   if hasattr(f,'Visibility'):f.Visibility=f==obj.Tip
 obj.Visibility=False
native=O/'QuadR380_D04_CFK.FCStd';doc.recompute();doc.saveAs(str(native))
for key in [k for k in masters if k.startswith('D04_')]:masters[key].Shape.exportStep(str(O/(key+'.step')))
for name,data in [('Instanzen.json',bom),('Bauteile.json',specs),('Neue_Gewindepaare.json',newpairs),('D03_Gewindereferenzen.json',prior),('CFK_Zuschnitt.json',cutlist)]: (O/name).write_text(json.dumps(data,indent=2,ensure_ascii=False))
oldmass=sum(r['mass_kg'] for r in BEFORE);mass=sum(r['mass_kg'] for r in bom);before={r['instance']:r for r in BEFORE};after={r['instance']:r for r in bom}
ledger=dict(d03_mass_kg=oldmass,d04_mass_kg=mass,saved_kg=oldmass-mass,saved_percent=100*(oldmass-mass)/oldmass,removed=[r for r in BEFORE if r['instance'] not in after],added=[r for r in bom if r['instance'] not in before],changed=[dict(instance=k,old_id=before[k]['id'],new_id=after[k]['id'],old_mass_kg=before[k]['mass_kg'],new_mass_kg=after[k]['mass_kg']) for k in before.keys()&after.keys() if abs(before[k]['mass_kg']-after[k]['mass_kg'])>1e-8])
assert mass<oldmass,(mass,oldmass)
(O/'Massenvergleich.json').write_text(json.dumps(ledger,indent=2,ensure_ascii=False))
report=dict(revision=P['revision'],production_ready=False,modeled_instances=len(bom),part_types=len(masters),mass_modeled_kg=mass,native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),cfk_article=P['tube_article'],large_central_plates_present=False,central_cfk_tubes=12,total_cfk_tubes=len(cutlist),new_thread_pairs=len(newpairs),oem_powertrain_integrated=False,open_items=['CFK Laminat/Klemmpressung und globale Festigkeit/Ermüdung','Alle nicht gesondert geprüften alten P12-Gewinde/Klemmungen','OEM Antrieb, Batterie, Verkabelung, Kühlung, Schutz und Fahrwerk'])
(O/'Status.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print('D04 built',len(bom),'mass',mass,'saved',oldmass-mass,'pairs',len(newpairs),flush=True)
