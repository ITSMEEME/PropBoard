"""D03 Carbonrahmen mit Aluminiumverbindern und indexierten Fußplatten.

Native PartDesign prototypes + placed App::Links; previous P12 core-only
thread interfaces remain explicitly open. This module excludes unavailable
powertrain/OEM parts rather than filling them with schematic shapes.
"""
import sys,json,math,csv,hashlib,os
from pathlib import Path
H=Path(__file__).resolve().parent;O=Path(os.environ.get('D05_OUTPUT_DIR',str(H/'Ausgabe')));O.mkdir(exist_ok=True)
sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,Sketcher,Import
V=A.Vector;P=json.loads((H/'parameter.json').read_text());D=math.pi/180
BASE=H.parent/'quad_r380_d04';doc=A.openDocument(str(BASE/'Ausgabe/QuadR380_D04_CFK.FCStd'));doc.saveAs(str(O/'QuadR380_D05_MN1330.FCStd'));doc.Label='Quad R380 D05 – MN1330-Motorintegration'
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
    if len(masters)%2==0:doc.recompute();doc.saveAs(str(O/'D05_Teile_Zwischenstand.FCStd'))
def rotated_rectangle(s,length,width,centre_r,angle):
    co,si=math.cos(angle*D),math.sin(angle*D);points=[]
    for x,y in [(centre_r-length/2,-width/2),(centre_r+length/2,-width/2),(centre_r+length/2,width/2),(centre_r-length/2,width/2)]:points.append(V(x*co-y*si,x*si+y*co,0))
    for i in range(4):block_geom(s,Part.LineSegment(points[i],points[(i+1)%4]))
def flat(key,label,w,h,t,outline_r=3):
    b=body(key,label);s=sketch(b,'Kontur');rectangle(s,w,h,r=outline_r);pad(b,s,t);return b
def install(key,label,placement,group='Rahmen'):
    master=masters[key];l=doc.addObject('App::Link','D05_I_'+str(len(bom)+1));l.Label=label;l.setLink(master);l.LinkPlacement=placement;l.Visibility=True;assembly.addObject(l);l.addProperty('App::PropertyString','BauteilID','D01');l.BauteilID=key
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

BEFORE=json.loads(json.dumps(bom));prior=[];hashes={}
for q in json.loads((BASE/'Ausgabe/Gewindepruefung.json').read_text())['pairs']:
 a=doc.getObject(q['bolt']);b=doc.getObject(q['mate'])
 for obj in [a.LinkedObject,b.LinkedObject]:
  if obj.Name not in hashes:hashes[obj.Name]=hashlib.sha256(obj.Shape.exportBrepToString().encode()).hexdigest()
 rel=a.LinkPlacement.inverse().multiply(b.LinkPlacement);prior.append(dict(result=q,master_a_sha256=hashes[a.LinkedObject.Name],master_b_sha256=hashes[b.LinkedObject.Name],relative_placement=list(rel.Base)+list(rel.Rotation.Q)))
# Replace the unused IF90 pattern by the selected legacy motor mounting pattern.
# Move the two carrier fasteners outward beyond the150mm motor envelope.
for r in bom:
 if r['id']=='D02_TIP':
  obj=doc.getObject(r['instance']);obj.setLink(masters['D02_ROOT']);obj.BauteilID='D02_ROOT';r['id']='D02_ROOT';r['label']='Endschott mit M6-Anschluss ±65'
caprad=425*math.sqrt(2);mount_y=caprad-544
b=flat('D05_MOTOR_PLATE','MN1330 Motorträger 160 x 150 x 8',160,150,8,5)
holes(b,[(-65,mount_y),(65,mount_y)],6.6,8,8,'Schott_M6_ausserhalb_Motor')
holes(b,[(0,0)],24,8,8,'Servicefenster')
stator=[(25*math.cos(i*math.pi/2),25*math.sin(i*math.pi/2)) for i in range(4)]
holes(b,stator,6.6,8,8,'MN1330_4xM6_PCD50')
s=sketch(b,'M6_Kopfsenkungen_unten',0);circles(s,stator,11);pocket(b,s,2,'M6_Kopfsenkungen_unten',reversed=True);register(b)
for r in bom:
 if r['id']=='D02_MOTOR_PLATE':
  obj=doc.getObject(r['instance']);obj.setLink(b);obj.BauteilID=b.Name;r['id']=b.Name;r['label']='Motorträger MN1330'
# Preserve original P14 motor geometry and its provenance; normalize its z14..80 datum only.
source=H/'Quellen/MN1330/MN1330.step';raw=Part.read(str(source));assert raw.isValid() and len(raw.Solids)==1;source_z=raw.BoundBox.ZMin;motor=raw.copy();motor.translate(V(0,0,-source_z));assert abs(motor.BoundBox.ZLength-66)<1e-6
m=doc.addObject('Part::Feature','D05_MN1330_LEGACY_REF');m.Label='MN1330 KV40 – Altmodell-Zeichnungsreferenz';m.Shape=motor;m.Visibility=False;lib.addObject(m);m.addProperty('App::PropertyString','CAD_Qualitaet','Quelle');m.CAD_Qualitaet='Vereinfachte P14-Zeichnungsreferenz, kein detailliertes Original-OEM-CAD';m.addProperty('App::PropertyFloat','Dokumentierte_Masse_kg','Quelle');m.Dokumentierte_Masse_kg=2.75;m.addProperty('App::PropertyBool','OEM_STEP_verifiziert','Quelle');m.OEM_STEP_verifiziert=False
masters[m.Name]=m;specs[m.Name]=dict(id=m.Name,label=m.Label,process='MN1330 KV40 durch Nutzer festgelegt; Geometrie aus P14, nominale Referenz',density_kg_m3=None,material='Kaufteil, realer Werkstoffmix nicht aufgelöst',volume_mm3=motor.Volume,mass_kg=2.75,mass_source='User original XLS including leads; no volume-derived motor mass',geometry_quality='LEGACY_NOMINAL_REFERENCE_NOT_DETAILED_OEM',inertia_from_reference_not_valid=True)
newpairs=[];interfaces=[]
for a in [45,135,225,315]:
 u=V(math.cos(a*D),math.sin(a*D),0);v=V(-u.y,u.x,0);rot=rotation([tuple(v),tuple(-u),(0,0,1)]);centre=u*caprad;carrier=next(r for r in bom if r['id']=='D05_MOTOR_PLATE' and (vec(r['placement_mm'])-centre-V(0,0,80)).Length<.001)
 motorlink=install(m.Name,'MN1330 KV40 '+str(a)+' – Zeichnungsreferenz',place(tuple(centre+V(0,0,88)),rot),'Motorreferenzen');bom[-1].update(source='P14 STEP-Zeichnungsreferenz, keine OEM-Detaillierung',geometry_quality='LEGACY_NOMINAL_REFERENCE_NOT_DETAILED_OEM',motor_selected_by_user=True,mass_override_source='XLS2750g including leads')
 for x,y in stator:
  p=centre+rot.multVec(V(x,y,82));bolt=hardware('ISO4762_M6x12','MN1330 Statorschraube M6x12',tuple(p),(0,0,-1));interfaces.append(dict(motor=motorlink.Name,bolt=bolt.Name,carrier=carrier['instance'],pcd_mm=50,clearance_mm=6.6,counterbore_mm=11,counterbore_depth_mm=2,nominal_engagement_assumed_mm=6,actual_motor_thread_verified=False,assembly_access_axis=[0,0,-1]))
# Match and relocate the existing carrier/end-bulkhead screws.
for r in bom:
 if r['label'] not in ['Endplatte M6','Endplatte Scheibe']:continue
 obj=doc.getObject(r['instance']);p=obj.LinkPlacement;old=p.Base;angle=min([45,135,225,315],key=lambda a:abs((math.degrees(math.atan2(old.y,old.x))-a+180)%360-180));u=V(math.cos(angle*D),math.sin(angle*D),0);v=V(-u.y,u.x,0);side=1 if old.dot(v)>0 else -1;p.Base=u*544+v*(side*65)+V(0,0,old.z);obj.LinkPlacement=p;r['label']='Motorträger Schott M6' if r['label']=='Endplatte M6' else 'Motorträger Schott Scheibe'
 if r['label']=='Motorträger Schott M6':
  choices=[q for q in bom if q['label']=='Endschott mit M6-Anschluss ±65' and (vec(q['placement_mm'])-p.Base).Length<130];assert len(choices)==1;newpairs.append(dict(bolt=obj.Name,mate=choices[0]['instance'],hole_suffix='M6_Stirn_1',family='D05 Carrier M6'))
used={r['id'] for r in bom};usedobjects={masters[k].Name for k in used}
for obj in list(lib.Group):
 if obj.Name not in usedobjects:
  if obj.TypeId=='PartDesign::Body':
   for child in reversed(list(obj.Group)):doc.removeObject(child.Name)
  doc.removeObject(obj.Name)
specs={k:v for k,v in specs.items() if k in used};masters={k:v for k,v in masters.items() if k in used}
for row in bom:
 obj=doc.getObject(row['instance']);row['mass_kg']=specs[row['id']]['mass_kg'];row['placement_mm']=list(obj.LinkPlacement.Base);row['placement_quaternion']=list(obj.LinkPlacement.Rotation.Q)
for obj in masters.values():
 if obj.TypeId=='PartDesign::Body':
  for feature in obj.Group:
   if hasattr(feature,'Visibility'):feature.Visibility=feature==obj.Tip
 obj.Visibility=False
native=O/'QuadR380_D05_MN1330.FCStd';doc.recompute();doc.saveAs(str(native));b.Shape.exportStep(str(O/'D05_MOTOR_PLATE.step'));m.Shape.exportStep(str(O/'MN1330_LEGACY_REF_normalisiert.step'))
for name,data in [('Instanzen.json',bom),('Bauteile.json',specs),('D04_Gewindereferenzen.json',prior),('Neue_Gewindepaare.json',newpairs),('Motor_Schnittstellen.json',interfaces)]: (O/name).write_text(json.dumps(data,indent=2,ensure_ascii=False))
mass=sum(r['mass_kg'] for r in bom);oldmass=sum(r['mass_kg'] for r in BEFORE);report=dict(revision=P['revision'],production_ready=False,modeled_instances=len(bom),part_types=len(masters),mass_modeled_kg=mass,previous_D04_mass_kg=oldmass,motor_model='MN1330 KV40',motor_selected_by_user=True,motor_count=4,motor_mass_each_kg=2.75,motor_total_kg=11,motor_cad_fidelity='Legacy P14 nominal drawing reference; NOT detailed original OEM CAD',motor_mounts_detailed=True,motor_thread_depth_verified=False,motor_reference_length_mm=66,xls_length_mm=65,cfk_article=P['tube_article'],oem_powertrain_integrated=False,native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),open_items=['Original MN1330-CAD/Montagebezug65/66mm und Gewindetiefen','Passender R380-Rotor und bestätigter Motor-Dauerbetriebspunkt','Regler/Batterie/Kabelbaum/Kühlung/Schutz/Landegestell','Tragfähigkeit mit zusätzlichen11kg Motoren und realen Schub-/Dynamiklasten','Nicht gesondert geprüfte Altverbindungen'])
(O/'Status.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));(O/'Motor_Quellenbezug.json').write_text(json.dumps(dict(source_file_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),legacy_geometry_z_offset_removed_mm=source_z,geometry_scale_changed=False,diameter_mm=motor.BoundBox.XLength,reference_length_mm=motor.BoundBox.ZLength,source_status='Legacy project drawing reference, explicitly not OEM STEP',mass_source_sha256=hashlib.sha256((H/'Quellen/MN1330/basicParameter_MN1330 KV40.xls').read_bytes()).hexdigest()),indent=2));print('D05 motor integration',len(bom),mass,'motor mass11kg',flush=True)
