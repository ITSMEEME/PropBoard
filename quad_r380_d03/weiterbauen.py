"""D03 Carbonrahmen mit Aluminiumverbindern und indexierten Fußplatten.

Native PartDesign prototypes + placed App::Links; previous P12 core-only
thread interfaces remain explicitly open. This module excludes unavailable
powertrain/OEM parts rather than filling them with schematic shapes.
"""
import sys,json,math,csv,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';O.mkdir(exist_ok=True)
sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,Sketcher,Import
V=A.Vector;P=json.loads((H/'parameter.json').read_text());D=math.pi/180
BASE=H.parent/'quad_r380_d02';doc=A.openDocument(str(BASE/'Ausgabe/QuadR380_D02_CFK.FCStd'));doc.saveAs(str(O/'QuadR380_D03_CFK.FCStd'))
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
    if len(masters)%2==0:doc.recompute();doc.saveAs(str(O/'D03_Teile_Zwischenstand.FCStd'))
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
    p=H/'Quellen/Normteile'/(key+'.brep');p=p if p.exists() else BASE/'Quellen/Normteile'/(key+'.brep');p=p if p.exists() else H.parent/'quad_r380_d01/Quellen/Normteile'/(key+'.brep');s=Part.Shape();s.read(str(p));assert s.isValid()
    b=doc.addObject('Part::Feature',key.replace('x','_L'));b.Label=key;b.Shape=s;b.Visibility=False;lib.addObject(b);masters[key]=b;specs[key]=dict(id=key,label=key,process='Kaufteil nach ISO; 10.9 / Mutter10 / Scheibe300HV, Zertifikat erforderlich',density_kg_m3=7850,material='Verguetungsstahl, Zinklamelle',volume_mm3=s.Volume,mass_kg=s.Volume*7850e-9)
def hardware(key,label,p,axis=(0,0,1),phase=0):
    fmt=lambda x:f'{0 if abs(x)<5e-7 else x:.6f}'
    cache_key=key+'@'+','.join(fmt(x) for x in p)+'|'+','.join(fmt(x) for x in axis)
    phase+=phase_cache.get(cache_key,0)
    norm(key);r=A.Rotation(V(0,0,1),vec(axis));r=A.Rotation(vec(axis),phase).multiply(r);return install(key,label,place(p,r),'Normteile')

# D03 extends the D02 foot saddle outward around the new rack, without touching CFRP.
b=masters['D02_SLIDER_BOTTOM'];b.Label='D03 Unterbacke mit Indexierbügel'
s=sketch(b,'Buegelsteg',-18);rectangle(s,50,23,y=37.5,r=1);pad(b,s,4,'Buegelsteg')
s=sketch(b,'Aussenwange',-18);rectangle(s,50,8,y=45,r=1);pad(b,s,30,'Aussenwange')
holes(b,[(0,0)],5,0,8,'Index_M6',rot=A.Rotation(V(0,0,1),V(0,1,0)),p=(0,49,0),thread='M6',thread_depth=8)
register(b)
for row in bom:
 if row['id']=='D02_SLIDER_BOTTOM':
  obj=doc.getObject(row['instance'])
  if row['placement_mm'][1]<0:obj.LinkPlacement=A.Placement(obj.LinkPlacement.Base,A.Rotation(V(0,0,1),180))
# Widen end plates, preserving the inclined socket bosses and actual P12 clamps.
flangeholes=[(15*math.cos((45+90*i)*D),15*math.sin((45+90*i)*D)) for i in range(4)]
for sign in [-1,1]:
 for sy in [-1,1]:
  key='D02_HIGH_'+('P' if sign>0 else 'M')+'_'+('P' if sy>0 else 'M');b=masters[key];y=sy*75
  s=sketch(b,'Endplatte_breit',145);rectangle(s,8,90,x=sign*389,y=y);pad(b,s,116,'Endplatte_breit')
  # Original rail socket pattern becomes an actual M4-6H native thread group.
  holes(b,flangeholes,3.3,0,8,'Schienenflansch_M4',rot=A.Rotation(V(0,0,1),V(-sign,0,0)),p=(sign*385,y,220),thread='M4',thread_depth=8)
  # Separate clearance holes connect the rack through the metal end plate.
  holes(b,[(-6,0),(6,0)],4.5,0,8,'Rasterleiste_M4_Durchgang',rot=A.Rotation(V(0,0,1),V(sign,0,0)),p=(sign*393,sy*110,220))
  register(b)
# One native rack prototype, installed twice by a rigid 180-degree rotation.
b=flat('D03_INDEX_RACK','Indexierleiste 770 x 24 x 10',770,10,24,0)
# flat() starts at z0; shift the entire body to its internal manufacturing height.
# Keep local geometry at z0..24, and place rack at world z208.
hole_x=[sign*x for sign in [-1,1] for x in range(130,251,10)]
holes(b,[(x,0) for x in hole_x],6.4,0,10,'Indexraster',rot=A.Rotation(V(0,0,1),V(0,1,0)),p=(0,5,12))
for sign in [-1,1]:holes(b,[(-6,0),(6,0)],3.3,0,12,'Endgewinde_M4_'+str(sign),rot=A.Rotation(V(0,0,1),V(sign,0,0)),p=(sign*385,0,12),thread='M4',thread_depth=10)
register(b)
for sy in [-1,1]:install('D03_INDEX_RACK','Indexierleiste '+str(sy),place((0,sy*110,208),A.Rotation(V(0,0,1),180 if sy<0 else 0)),'Positionssicherung')
# Explicit new threaded pairs and their matching native holes, used by QA.
newpairs=[]
for sign in [-1,1]:
 for sy in [-1,1]:
  rack=next(r for r in bom if r['id']=='D03_INDEX_RACK' and r['placement_mm'][1]*sy>0)
  for z in [214,226]:
   bolt=hardware('ISO4762_M4x16','Rasterleiste Endschraube',(sign*393.8,sy*110,z),(sign,0,0));hardware('ISO7089_M4','Rasterleiste Scheibe',(sign*393,sy*110,z),(sign,0,0))
   # Local rack X flips when the negative-Y rack is rotated.
   endsign=sign*sy;newpairs.append(dict(bolt=bolt.Name,mate=rack['instance'],hole_suffix='Endgewinde_M4_'+str(endsign),family='Rack M4'))
for cx in [-200,200]:
 for sy in [-1,1]:
  mate=next(r for r in bom if r['id']=='D02_SLIDER_BOTTOM' and abs(r['placement_mm'][0]-cx)<.01 and abs(r['placement_mm'][1]-sy*75)<.01)
  bolt=hardware('ISO4762_M6x20','Indexierschraube',(cx,sy*125.6,220),(0,sy,0));hardware('ISO7089_M6','Indexierschraube Scheibe',(cx,sy*124,220),(0,sy,0))
  newpairs.append(dict(bolt=bolt.Name,mate=mate['instance'],hole_suffix='Index_M6',family='Index M6'))
  for r in bom[-2:]:r.update(foot_side='Links' if cx<0 else 'Rechts',foot_base_x_mm=cx)
# Previously core-only end-bracket threads now get explicit mating records.
for sy in [-1,1]:
 for sign in [-1,1]:
  mate=next(r for r in bom if r['id']=='D02_HIGH_'+('P' if sign>0 else 'M')+'_'+('P' if sy>0 else 'M'))
  for r in bom:
   if r['id']=='ISO4762_M4x16' and r['label']=='Schienenende Flansch M4' and abs(r['placement_mm'][0]-sign*384)<.01 and abs(r['placement_mm'][1]-sy*75)<16:
    newpairs.append(dict(bolt=r['instance'],mate=mate['instance'],hole_suffix='Schienenflansch_M4',family='Rail flange M4'))
assert len(newpairs)==28,len(newpairs)
control=doc.getObject('Fussverstellung');control.Links=(-200,-250,-130,10);control.Rechts=(200,130,250,10)
control.addProperty('App::PropertyFloatConstraint','Entriegelung','Positionssicherung');control.Entriegelung=(0,0,10,10)
control.addProperty('App::PropertyString','Bedienhinweis','Positionssicherung');control.Bedienhinweis='Darstellung Endlagen 0/10mm; Schrauben real um 10 Umdrehungen lösen. Verriegeln nur im 10mm-Raster. Danach Rohrklemmung gemäß noch zu qualifizierendem Verfahren anziehen.'
for r in bom:
 obj=doc.getObject(r['instance'])
 if r.get('foot_side'):
  x=r['placement_mm'][0];obj.setExpression('LinkPlacement.Base.x','Fussverstellung.'+r['foot_side']+f' + ({x-r["foot_base_x_mm"]:.8f})')
 if r['label']=='Indexierschraube':
  y=r['placement_mm'][1];sgn=1 if y>0 else -1;obj.setExpression('LinkPlacement.Base.y',f'{y} + ({sgn})*Fussverstellung.Entriegelung')
for r in bom:
 obj=doc.getObject(r['instance']);r['mass_kg']=specs[r['id']]['mass_kg'];r['placement_mm']=list(obj.LinkPlacement.Base);r['placement_quaternion']=list(obj.LinkPlacement.Rotation.Q)
for master in masters.values():
 if master.TypeId=='PartDesign::Body':
  for f in master.Group:
   if hasattr(f,'Visibility'):f.Visibility=f==master.Tip
 master.Visibility=False
native=O/'QuadR380_D03_CFK.FCStd';doc.recompute();doc.saveAs(str(native))
for name,data in [('Instanzen.json',bom),('Bauteile.json',specs),('Neue_Gewindepaare.json',newpairs)]: (O/name).write_text(json.dumps(data,indent=2,ensure_ascii=False))
for key in ['D02_SLIDER_BOTTOM','D03_INDEX_RACK']+[k for k in masters if k.startswith('D02_HIGH')]:masters[key].Shape.exportStep(str(O/(key+'.step')))
report=dict(production_ready=False,revision=P['revision'],modeled_instances=len(bom),part_types=len(masters),mass_modeled_kg=sum(r['mass_kg'] for r in bom),native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),cfk_article=P['tube_article'],legacy_P12_clamps_preserved=True,index_pitch_mm=10,index_screw_retraction_mm=10,new_thread_pairs=len(newpairs),oem_powertrain_integrated=False,open_items=['OEM Kennfelder und verbindliche Anschlussdaten','Gesamtfahrzeugmasse/Energie/Kühlung','CFK Klemmpressung, Reibung, Festigkeit und Ermüdung','Gesamte alte P12 Gewindeschnittstellen und Gesamtverbindungen','Indexierleisten/Schraubenlasten und Anzugverfahren','Schutz und Landegestell'])
(O/'Status.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print('D03 built',len(bom),len(newpairs),report['mass_modeled_kg'],flush=True)
