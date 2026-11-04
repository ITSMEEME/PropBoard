"""Realize chosen V3 in all four corners of the D06 native assembly.

Replace bulky root/end bulkheads and plates by integrated socket nodes. All
production/laminate/OEM limits remain explicit; no illustrative PNG is CAD input.
"""
import sys,json,math,hashlib,os
from pathlib import Path
H=Path(__file__).resolve().parent;O=Path(os.environ.get('D07_OUTPUT_DIR',str(H/'Ausgabe')));O.mkdir(parents=True,exist_ok=True)
sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,Sketcher
from geometrie import root_node,motor_node,core_envelope,socket_shape,liner,frame,placed,trim_core
V=A.Vector;P=json.loads((H/'parameter.json').read_text());B=H.parent/'quad_r380_d06';native=O/'QuadR380_D07_V3.FCStd';D=A.openDocument(str(B/'Ausgabe/QuadR380_D06_Propeller.FCStd'));D.Label='Quad R380 D07 – V3 horizontale V-Gabel';lib=D.getObject('Bauteilbibliothek');assembly=D.getObject('Montage');rows=json.loads((B/'Ausgabe/Instanzen.json').read_text());specs=json.loads((B/'Ausgabe/Bauteile.json').read_text());before=json.loads(json.dumps(rows));masters={r['id']:D.getObject(r['instance']).LinkedObject for r in rows};oldtop=masters['D04_CORE_TOP'].Shape.copy();oldbottom=masters['D04_CORE_BOTTOM'].Shape.copy()

def eliminate(r):
    return r['id'] in ['D02_ROOT','D02_ARM_TUBE','D05_MOTOR_PLATE'] or r['label'].startswith(('Wurzel ','Ende ','Armrohr ')) or r['label'] in ['CFK-Kappe M6','CFK-Kappe Scheibe','Motorträger Schott M6','Motorträger Schott Scheibe']
removed=[r for r in rows if eliminate(r)]
for r in removed:D.removeObject(r['instance'])
rows=[r for r in rows if not eliminate(r)];newpairs=[];new_instances=[];thread_features={}
phasefile=H/'Ausgabe/Gewindephasen.json';phases=json.loads(phasefile.read_text()).get('phases',{}) if phasefile.exists() else {}
for row in rows:
    if row['instance'] in phases:
        obj=D.getObject(row['instance']);pose=obj.LinkPlacement;axis=pose.Rotation.multVec(V(0,0,1));pose.Rotation=A.Rotation(axis,phases[row['instance']]).multiply(pose.Rotation);obj.LinkPlacement=pose

def raw(key,label,shape,density,material,process):
    assert shape.isValid() and len(shape.Solids)==1,key
    b=D.addObject('PartDesign::Body',key);b.Label=label;lib.addObject(b);f=b.newObject('PartDesign::Feature','CNC_'+key);f.Label='Grundkörper mit realen Taschen, Sitzen und Radien';f.Shape=Part.Compound([shape]);b.Tip=f
    b.addProperty('App::PropertyString','Fertigung','D07');b.Fertigung=process;b.addProperty('App::PropertyBool','Produktionsfreigabe','D07');b.Produktionsfreigabe=False;b.addProperty('App::PropertyString','Parameter_JSON','D07');b.Parameter_JSON=json.dumps(P,ensure_ascii=False)
    specs[key]=dict(id=key,label=label,density_kg_m3=density,material=material,process=process,production_ready=False,geometry_quality='DETAILED_PARAMETRIC_V3_OWN_DESIGN');masters[key]=b;D.recompute();b.Visibility=False;return b

def register(b):
    D.recompute();s=b.Shape;assert s.isValid() and len(s.Solids)==1,b.Name;v=s.Volume;specs[b.Name].update(volume_mm3=v,mass_kg=v*specs[b.Name]['density_kg_m3']*1e-9)
    for child in b.Group:
        if hasattr(child,'Visibility'):child.Visibility=child==b.Tip
    b.Visibility=False;print('V3 master',b.Name,round(specs[b.Name]['mass_kg'],5),flush=True)

def native_socket_threads(b,ports):
    for i,port in enumerate(ports):
        r=A.Rotation(*port['quaternion']);p=V(*port['origin'])+r.multVec(V(0,-P['split_gap_mm']/2,0));hr=r.multiply(A.Rotation(V(1,0,0),-90));sk=b.newObject('Sketcher::SketchObject','SK_'+b.Name+'_M4_'+str(i));sk.Placement=A.Placement(p,hr)
        for x in [-P['ear_x_mm'],P['ear_x_mm']]:
            idx=sk.addGeometry(Part.Circle(V(x,-P['grip_length_mm']/2,0),V(0,0,1),1.65),False);sk.addConstraint(Sketcher.Constraint('Block',idx))
        D.recompute();f=b.newObject('PartDesign::Hole','D07_M4_'+b.Name+'_'+str(i));f.Profile=sk;D.recompute();f.ThreadType='ISOMetricProfile';D.recompute();f.Threaded=True;f.ThreadSize='M4';D.recompute();f.ThreadClass='6H';f.Depth=P['ear_top_mm']-P['split_gap_mm']/2;f.ThreadDepthType='Dimension';f.ThreadDepth=f.Depth;f.DrillPoint='Flat';D.recompute();f.ModelThread=True;sk.Visibility=False;b.Tip=f;D.recompute()
        if hasattr(f,'Refine'):f.Refine=False;D.recompute()
        assert f.Shape.isValid() and len(f.Shape.Solids)==1,(f.Name,str(f.State));thread_features[b.Name,i]=f.Name
        for child in b.Group:
            if hasattr(child,'Visibility'):child.Visibility=child==f

def native_core_threads(b,sign):
    _,dirs=core_envelope(sign)
    for i,axis in enumerate(dirs):
        sk=b.newObject('Sketcher::SketchObject','SK_'+b.Name+'_Kernport_'+str(i));sk.Placement=A.Placement(axis*25,A.Rotation(V(0,0,1),axis))
        for k in range(4):
            angle=k*math.pi/2;idx=sk.addGeometry(Part.Circle(V(15*math.cos(angle),15*math.sin(angle),0),V(0,0,1),1.65),False);sk.addConstraint(Sketcher.Constraint('Block',idx))
        D.recompute();f=b.newObject('PartDesign::Hole','D07_Kernport_'+b.Name+'_'+str(i));f.Profile=sk
        if hasattr(f,'Refine'):f.Refine=False
        D.recompute();f.ThreadType='ISOMetricProfile';D.recompute();f.Threaded=True;f.ThreadSize='M4';D.recompute();f.ThreadClass='6H';f.Depth=11;f.ThreadDepthType='Dimension';f.ThreadDepth=10;f.DrillPoint='Angled';f.DrillPointAngle=118;D.recompute();f.ModelThread=True;sk.Visibility=False;b.Tip=f;D.recompute()
        assert f.Shape.isValid() and len(f.Shape.Solids)==1,(f.Name,str(f.State))
        for child in b.Group:
            if hasattr(child,'Visibility'):child.Visibility=child==f

al=P['al_density_kg_m3'];mat=P['al_material_assumed'];shape,rootports=root_node(P,oldtop);b=raw('D07_ROOT_TOP','Rahmenknoten mit zwei integrierten V3-Rohrsitzen',shape,al,mat,'CNC;3 Kernports nach bisherigem Lochbild neu parametrisiert,2 neue direkte Rohrklemmen');native_core_threads(b,1);native_socket_threads(b,rootports);register(b)
shape,_=core_envelope(-1);b=raw('D07_CORE_BOTTOM','Kompakter unterer Rahmenknoten ohne Schottauflage',shape,al,mat,'CNC; bestehende Kernportpositionen,neue native Gewindefeatures');native_core_threads(b,-1);register(b)
shape,motorports=motor_node(P);b=raw('D07_MOTOR_NODE','V3 Direkt-Motorknoten mit integriertem4xM6/PCD50-Fuß',shape,al,mat,'CNC;2 Rohrsitze,schmale integrierte Motoraugen,offene Kopfzugänge');native_socket_threads(b,motorports);register(b)
b=raw('D07_CLAMP_CAP','V3 obere Rohrklemmhälfte35mm mit2 M4-Durchgängen',socket_shape(P,upper=True),al,mat,'CNC;Ø20.6-Sitz,0.5mm Spalt,2×Ø4.5');register(b)
b=raw('D07_LINER','Geschlitzte Isolierhülse Ø20.6/20×35',liner(P),P['liner_density_assumed_kg_m3'],'GFK-/Isolierfilm,Produkt/Kriechen offen','An gemessenen Rohr-OD anpassen');register(b)
b=raw('D07_END_PAD','Isolier-Endscheibe Ø20×0.3',Part.makeCylinder(10,P['end_pad_thickness_mm']),P['liner_density_assumed_kg_m3'],'GFK-/Isolierfilm,Produkt/Kriechen offen','Zuschnitt und Verklebung noch zu spezifizieren');register(b)
length=math.sqrt((P['tip_tube_r_mm']-P['root_tube_r_mm'])**2+(P['root_tube_half_width_mm']-P['tip_tube_half_width_mm'])**2+(P['tip_tube_z_mm']-P['root_tube_z_mm'])**2)
b=raw('D07_ARM_TUBE','CBU20171005TG V3-Zuschnitt '+str(round(length,3)),Part.makeCylinder(10,length).cut(Part.makeCylinder(8.5,length)),P['tube_density_assumed_kg_m3'],'CFK CBU20171005TG; Dichte angenommen','Sägen/Enden versiegeln,keine Querbohrungen');register(b)
for old,new in [('D04_CORE_TOP','D07_ROOT_TOP'),('D04_CORE_BOTTOM','D07_CORE_BOTTOM')]:
    for r in rows:
        if r['id']==old:
            obj=D.getObject(r['instance']);obj.setLink(masters[new]);obj.BauteilID=new;r.update(id=new,label='V3 Rahmenknoten oben' if old.endswith('TOP') else 'V3 Rahmenknoten unten')

def norm(key):
    if key in masters:return
    f=H/'Quellen/Normteile'/(key+'.brep');s=Part.Shape();s.read(str(f));assert s.isValid();obj=D.addObject('Part::Feature',key.replace('x','_L'));obj.Label=key;obj.Shape=s;obj.Visibility=False;lib.addObject(obj);masters[key]=obj;specs[key]=dict(id=key,label=key,density_kg_m3=7850,material='Vergütungsstahl; Klasse/Vorspannung zu bemessen',process='ISO Normteil mit echtem nominalem Helixgewinde',volume_mm3=s.Volume,mass_kg=s.Volume*7850e-9)
norm('ISO4762_M4x20')
counter=0
def install(key,label,p,r,group='V3 Anschluss',**extra):
    global counter
    counter+=1;obj=D.addObject('App::Link','D07_I_'+str(counter));obj.Label=label;obj.setLink(masters[key]);obj.LinkPlacement=A.Placement(p,r);obj.Visibility=True;assembly.addObject(obj);obj.addProperty('App::PropertyString','BauteilID','D07');obj.BauteilID=key
    if obj.Name in phases:
        r=A.Rotation(r.multVec(V(0,0,1)),phases[obj.Name]).multiply(r);obj.LinkPlacement=A.Placement(p,r)
    row=dict(instance=obj.Name,id=key,label=label,group=group,mass_kg=specs[key]['mass_kg'],placement_mm=list(p),placement_quaternion=list(r.Q),source='D07 V3 mechanischer CAD-Entwurf',**extra);rows.append(row);new_instances.append(obj.Name);return obj

interfaces=[];arms=[]
for angle in [45,135,225,315]:
    a=math.radians(angle);u=V(math.cos(a),math.sin(a),0);v=V(-u.y,u.x,0);r=A.Rotation(v,-u,V(0,0,1),'ZXY');rootorigin=u*P['core_radius_mm']+V(0,0,P['core_z_mm']);motororigin=u*(P['motor_xy_half_spacing_mm']*math.sqrt(2))+V(0,0,P['motor_base_z_mm']);rootrow=next(row for row in rows if row['id']=='D07_ROOT_TOP' and (V(*row['placement_mm'])-rootorigin).Length<.001);motor=install('D07_MOTOR_NODE','V3 Motorknoten '+str(angle),motororigin,r,arm_angle_deg=angle)
    for i,sign in enumerate([-1,1]):
        start=u*P['root_tube_r_mm']+v*(sign*P['root_tube_half_width_mm'])+V(0,0,P['root_tube_z_mm']);end=u*P['tip_tube_r_mm']+v*(sign*P['tip_tube_half_width_mm'])+V(0,0,P['tip_tube_z_mm']);direction=end-start;assert abs(direction.Length-length)<1e-6;direction.normalize();sr=frame(direction)
        tube=install('D07_ARM_TUBE','V3 Carbonrohr '+str(angle)+'/'+str(sign),start,sr,'V3 Carbonrohre',arm_angle_deg=angle,tube_side=sign)
        arms.append(dict(angle_deg=angle,side=sign,instance=tube.Name,cut_start_mm=list(start),cut_end_mm=list(end),length_mm=length,grip_each_end_mm=35,free_length_between_grips_mm=length-70))
        for side,origin,mate,ports in [('Wurzel',start,rootrow['instance'],rootports),('Motor',end-direction*35,motor.Name,motorports)]:
            local=ports[i];expected=(rootorigin if side=='Wurzel' else motororigin)+r.multVec(V(*local['origin']));assert (expected-origin).Length<1e-6
            install('D07_CLAMP_CAP','V3 Klemmkappe '+side,origin,sr,arm_angle_deg=angle)
            install('D07_LINER','V3 Rohr-Isolierung '+side,origin,sr,'Isolierung',arm_angle_deg=angle)
            padpos=start-direction*.3 if side=='Wurzel' else end
            install('D07_END_PAD','V3 Endisolation '+side,padpos,sr,'Isolierung',arm_angle_deg=angle)
            for x in [-16,16]:
                hp=origin+sr.multVec(V(x,P['ear_top_mm'],17.5));hr=sr.multiply(A.Rotation(V(1,0,0),-90));bolt=install('ISO4762_M4x20','V3 Rohrklemmung M4x20',hp,hr,'Normteile',arm_angle_deg=angle)
                newpairs.append(dict(bolt=bolt.Name,mate=mate,hole_feature=thread_features['D07_ROOT_TOP' if side=='Wurzel' else 'D07_MOTOR_NODE',i],family='V3 socket M4',socket_index=i,side=side))
    motorref=next(row for row in rows if row['id']=='D05_MN1330_LEGACY_REF' and math.dist(row['placement_mm'][:2],list(motororigin)[:2])<1e-5)
    interfaces.append(dict(angle_deg=angle,node=motor.Name,motor=motorref['instance'],pcd_mm=50,holes=4,clearance_mm=6.6,integral_foot_thickness_mm=6,stator_bolts_retained='ISO4762 M6x12;6mm nominal engagement from old project,OEM depth unverified',separate_motor_plate_present=False))

used={r['id'] for r in rows};usedobjects={masters[k].Name for k in used}
for obj in list(lib.Group):
    if obj.Name not in usedobjects:
        if obj.TypeId=='PartDesign::Body':
            for child in reversed(list(obj.Group)):D.removeObject(child.Name)
        D.removeObject(obj.Name)
specs={k:v for k,v in specs.items() if k in used};masters={k:v for k,v in masters.items() if k in used}
for row in rows:
    obj=D.getObject(row['instance']);row['mass_kg']=specs[row['id']]['mass_kg'];row['placement_mm']=list(obj.LinkPlacement.Base);row['placement_quaternion']=list(obj.LinkPlacement.Rotation.Q)
for obj in masters.values():obj.Visibility=False
D.recompute();pose=[]
for row in rows:
    obj=D.getObject(row['instance']);expected=obj.LinkedObject.Shape.copy();expected.Placement=obj.LinkPlacement.multiply(expected.Placement);actual=obj.Shape
    delta=max(abs(getattr(actual.BoundBox,k)-getattr(expected.BoundBox,k)) for k in ['XMin','XMax','YMin','YMax','ZMin','ZMax']);assert delta<1e-5,(row['instance'],delta);pose.append(dict(instance=row['instance'],max_bbox_delta_mm=delta))
D.saveAs(str(native));digest=hashlib.sha256(native.read_bytes()).hexdigest();mass=sum(row['mass_kg'] for row in rows);oldmass=sum(row['mass_kg'] for row in before)
for name,data in [('Instanzen.json',rows),('Bauteile.json',specs),('Neue_Gewindepaare.json',newpairs),('V3_Rohre.json',arms),('Motor_Schnittstellen.json',interfaces),('Entfernte_Instanzen.json',removed)]: (O/name).write_text(json.dumps(data,indent=2,ensure_ascii=False))
for key in specs:
    if key.startswith('D07_'):masters[key].Shape.exportStep(str(O/(key+'.step')))
after={r['instance']:r for r in rows};prior={r['instance']:r for r in before};changed=[dict(instance=name,old_id=prior[name]['id'],new_id=row['id'],old_mass_kg=prior[name]['mass_kg'],new_mass_kg=row['mass_kg']) for name,row in after.items() if name in prior and row['id']!=prior[name]['id']]
ledger=dict(previous_D06_mass_kg=oldmass,mass_modeled_kg=mass,saved_kg=oldmass-mass,saved_percent=100*(oldmass-mass)/oldmass,removed=removed,added=[r for r in rows if r['instance'] not in prior],changed=changed)
(O/'Massenvergleich.json').write_text(json.dumps(ledger,indent=2,ensure_ascii=False))
report=dict(revision=P['revision'],selected_variant='V3',production_ready=False,modeled_instances=len(rows),part_types=len(specs),mass_modeled_kg=mass,previous_D06_mass_kg=oldmass,saved_kg=oldmass-mass,native_sha256=digest,source_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),geometry_script_sha256=hashlib.sha256((H/'geometrie.py').read_bytes()).hexdigest(),parameter_sha256=hashlib.sha256((H/'parameter.json').read_bytes()).hexdigest(),base_native_sha256=hashlib.sha256((B/'Ausgabe/QuadR380_D06_Propeller.FCStd').read_bytes()).hexdigest(),cfk_article=P['tube_article'],arm_tubes_per_motor=2,total_arm_tubes=8,tube_length_mm=length,grip_length_mm=35,separate_motor_plate_present=False,large_arm_bulkheads_present=False,motor_count=4,motor_model='MN1330 KV40',motor_cad_fidelity='Legacy nominal reference,not OEM CAD',propeller_count=4,blades_per_rotor=3,foot_system_geometry_changed=False,old_foot_rail_rotor_conflicts_resolved=False,rotor_clearance_verified=False,nominal_new_socket_thread_pairs=len(newpairs),excluded=['Akku','Regler','Versorgungskabelbaum','Rotorschutz','Landegestell','Motor-Naben-Schrauben mit unbekannter Gewindetiefe'],open_items=['CFK Laminat,Kontaktpressung,Rutschlast und Ermüdung','Balkenmodell nur mit angenommenen Materialdaten,keine Traglastfreigabe','Bestehende D06 Konflikte Fußschienen-Streben versus Rotorumlauf','MN1330 OEM-Geometrie,Statorgewindetiefen,Motor-Nabenschrauben und Motorbetriebspunkt','Globale Rahmensteifigkeit nach geänderter Einleitung an oberen Knoten'])
(O/'Status.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));(O/'Native_Platzierung_Pruefung.json').write_text(json.dumps(dict(native_sha256=digest,passed=True,checks=pose),indent=2));print('D07 V3 built',len(rows),'mass',mass,'saved',oldmass-mass,flush=True)
