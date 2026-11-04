"""Add detailed own-design R380 propellers; retain and expose D05 integration conflicts."""
import sys,json,math,hashlib,os,csv
from pathlib import Path
H=Path(__file__).resolve().parent;O=Path(os.environ.get('D06_OUTPUT_DIR',str(H/'Ausgabe')));O.mkdir(parents=True,exist_ok=True)
sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
from geometrie import blade,hub,cap,mirrored,intersection_volume
V=A.Vector;P=json.loads((H/'parameter.json').read_text());BASE=H.parent/'quad_r380_d05';native=O/'QuadR380_D06_Propeller.FCStd'
doc=A.openDocument(str(BASE/'Ausgabe/QuadR380_D05_MN1330.FCStd'));doc.Label='Quad R380 D06 – Propellerentwurf mit offenen Einbaukonflikten'
lib=doc.getObject('Bauteilbibliothek');assembly=doc.getObject('Montage');specs=json.loads((BASE/'Ausgabe/Bauteile.json').read_text());bom=json.loads((BASE/'Ausgabe/Instanzen.json').read_text());base_count=len(bom);masters={r['id']:doc.getObject(r['instance']).LinkedObject for r in bom}

# App::Link with LinkTransform=False ignores the linked object's placement.
# D05's normalization was stored only in the motor master's -14mm placement,
# making its actual native links z102..168 while the mesh used z88..154.
# Embed that same normalized solid inside an identity-placement compound.
# No dimensions, material or motor-reference mass are changed.
motor=masters['D05_MN1330_LEGACY_REF'];normalized=motor.Shape.copy();motor.Placement=A.Placement();motor.Shape=Part.Compound([normalized]);doc.recompute()
for row in [r for r in bom if r['id']=='D05_MN1330_LEGACY_REF']:
    bb=doc.getObject(row['instance']).Shape.BoundBox
    assert abs(bb.ZMin-88)<1e-7 and abs(bb.ZMax-154)<1e-7

def master(key,label,shape,density,material,process):
    assert shape.isValid() and len(shape.Solids)==1,key
    b=doc.addObject('PartDesign::Body',key);b.Label=label;lib.addObject(b)
    f=b.newObject('PartDesign::Feature','Geometrie_'+key);f.Label='Parametrisch erzeugter Volumenkörper';f.Shape=shape;b.Tip=f
    b.addProperty('App::PropertyString','Quelle','D06');b.Quelle='Eigener Entwurf; reproduzierbare Geometrie.py + parameter.json, kein OEM-Modell'
    b.addProperty('App::PropertyBool','Fertigungsfreigabe','D06');b.Fertigungsfreigabe=False
    b.addProperty('App::PropertyString','Materialannahme','D06');b.Materialannahme=material
    b.addProperty('App::PropertyString','Konstruktionsparameter_JSON','D06');b.Konstruktionsparameter_JSON=json.dumps(P,ensure_ascii=False)
    b.Visibility=False;masters[key]=b
    specs[key]=dict(id=key,label=label,process=process,density_kg_m3=density,material=material,volume_mm3=shape.Volume,mass_kg=shape.Volume*density*1e-9,geometry_quality='DETAILED_OWN_DESIGN_NOT_OEM_OR_RELEASED',production_ready=False)
    shape.exportStep(str(O/(key+'.step')));print('Master',key,round(specs[key]['mass_kg'],5),flush=True)
    return b

def norm(key):
    if key in masters:return
    paths=[H/'Quellen/Normteile'/(key+'.brep'),H.parent/'quad_r380_d01/Quellen/Normteile'/(key+'.brep')];p=next(p for p in paths if p.exists());s=Part.Shape();s.read(str(p));assert s.isValid()
    obj=doc.addObject('Part::Feature',key.replace('x','_L'));obj.Label=key;obj.Shape=s;obj.Visibility=False;lib.addObject(obj);masters[key]=obj
    specs[key]=dict(id=key,label=key,process='Kaufteil nach ISO; nominales Helixgewinde; Beschaffung und Vorspannung offen',density_kg_m3=7850,material='Vergütungsstahl; Klasse/Beschichtung zu bemessen',volume_mm3=s.Volume,mass_kg=s.Volume*7850e-9)

def install(key,label,ridx,local,angle=0,extra_rotation=None):
    rotor=rotors[ridx];rot=A.Rotation(V(0,0,1),angle);rot=rot.multiply(extra_rotation or A.Rotation());p=V(*local)+V(*rotor['centre_mm']);l=doc.addObject('App::Link','D06_I_'+str(len(bom)+1));l.Label=label;l.setLink(masters[key]);l.LinkPlacement=A.Placement(p,rot);l.Visibility=True;assembly.addObject(l);l.addProperty('App::PropertyString','BauteilID','D06');l.BauteilID=key
    l.addProperty('App::PropertyString','Rotor_ID','D06');l.Rotor_ID=rotor['id']
    row=dict(instance=l.Name,label=label,id=key,group='Propeller',mass_kg=specs[key]['mass_kg'],source='Eigener detaillierter Propellerentwurf' if not key.startswith('ISO') else 'ISO-Normgeometrie',placement_mm=list(p),placement_quaternion=list(rot.Q),rotor_id=rotor['id'],rotor_hand=rotor['hand'],rotor_axis_mm=rotor['centre_mm'],rotor_part_angle_deg=angle)
    bom.append(row);return l

full,skin,cores=blade(P)
master('D06_HUB','Dreiblatt-Nabe mit 12×M5/PCD40',hub(P),2700,'EN AW-6082 T6 (Entwurfsannahme)','CNC aus Vollmaterial; Oberflächen, Toleranzen und Lastnachweis offen')
master('D06_ROOT_CAP','Blattwurzel-Klemmplatte 46×40×6',cap(P),2700,'EN AW-6082 T6 (Entwurfsannahme)','CNC; zwei Ø5,5-Durchgänge; Klemmkräfte offen')
for hand,flip in [('CCW',False),('CW',True)]:
    master('D06_BLADE_'+hand,'R380 '+hand+' CFK-Blatt mit Wurzel, Haut und Stegen',mirrored(skin) if flip else skin,P['cfk_density_assumed_kg_m3'],'CFK, effektive Dichte angenommen; Laminat noch nicht definiert','Negativform/CFK-Sandwich mit massivem Wurzelbereich; keine Laminat-/Betriebsfreigabe')
    for i,core in enumerate(cores):master('D06_CORE_'+str(i+1)+'_'+hand,'R380 '+hand+' Schaumkern '+str(i+1),mirrored(core) if flip else core,P['foam_density_assumed_kg_m3'],'Strukturschaum, 80 kg/m³ angenommen','Geformter Kern; Harzsystem und Verklebung offen')
master('D06_ROOT_BUSH','Blattwurzel-Druckhülse Ø8/5,5×8',Part.makeCylinder(4,8).cut(Part.makeCylinder(2.75,8)),P['bush_density_assumed_kg_m3'],'Ti-6Al-4V (Entwurfsannahme)','Drehteil; Länge und Flächenpressung noch zu tolerieren')
master('D06_ROOT_BOND','Wurzelhülsen-Klebschicht radial 0,1 mm',Part.makeCylinder(4.1,8).cut(Part.makeCylinder(4,8)),P['adhesive_density_assumed_kg_m3'],'Epoxidklebstoff, Dichte angenommen; Produkt offen','Realer Klebespalt als Geometrie; Klebeprozess und Festigkeit offen')
for k in ['ISO4762_M5x35','ISO7089_M5','ISO7719_M5']:norm(k)

rotors=[dict(id='R1',centre_mm=[425,425,154],hand='CCW',sign=1),dict(id='R2',centre_mm=[-425,425,154],hand='CW',sign=-1),dict(id='R3',centre_mm=[-425,-425,154],hand='CCW',sign=1),dict(id='R4',centre_mm=[425,-425,154],hand='CW',sign=-1)]
# All blade-root joints share one relative bolt/nut stack. Fit its nominal helical
# phase once, then transfer by exact rigid rotation; no tolerance/preload claim.
bs=masters['ISO4762_M5x35'].Shape.copy();bs.translate(V(98,0,24))
ns=masters['ISO7719_M5'].Shape.copy();best=None
for phase in [37,38,39,41,42,40,30,45]+list(range(0,360,30)):
    r=A.Rotation(V(0,0,1),phase).multiply(A.Rotation(V(0,1,0),180));n=ns.copy();n.Placement=A.Placement(V(98,0,-1),r)
    try:v=intersection_volume(bs,n)
    except (ValueError,Part.OCCError) as error:
        print('Thread phase rejected: Boolean failure',phase,type(error).__name__,flush=True);continue
    if best is None or v<best[0]:best=(v,phase)
    print('Thread phase candidate',phase,v,flush=True)
    if v<=.1:break
if best[0]>.1:
    for phase in [best[1]+i*3 for i in range(-10,11)]:
        r=A.Rotation(V(0,0,1),phase).multiply(A.Rotation(V(0,1,0),180));n=ns.copy();n.Placement=A.Placement(V(98,0,-1),r)
        try:v=intersection_volume(bs,n)
        except (ValueError,Part.OCCError):continue
        if v<best[0]:best=(v,phase)
        if v<=.1:break
print('Root nominal thread phase',best,flush=True);assert best[0]<.1
new_pairs=[]
for idx,rotor in enumerate(rotors):
    install('D06_HUB','Propellernabe '+rotor['id'],idx,(0,0,0))
    for a in [0,120,240]:
        rr=A.Rotation(V(0,0,1),a)
        install('D06_BLADE_'+rotor['hand'],'Blatt '+rotor['hand']+' '+str(a),idx,(0,0,13),a)
        for i in [1,2]:install('D06_CORE_'+str(i)+'_'+rotor['hand'],'Schaumkern '+str(i),idx,(0,0,13),a)
        install('D06_ROOT_CAP','Wurzel-Klemmplatte',idx,(0,0,17),a)
        for radius in P['root_bolt_radii_mm']:
            x,y,_=rr.multVec(V(radius,0,0));install('D06_ROOT_BUSH','Druckhülse Blattwurzel',idx,(x,y,9),a);install('D06_ROOT_BOND','Klebefuge Druckhülse',idx,(x,y,9),a)
            for z in [-1,23]:install('ISO7089_M5','Scheibe Blattwurzel',idx,(x,y,z),a)
            bolt=install('ISO4762_M5x35','Blattwurzel M5x35',idx,(x,y,24),a)
            nr=A.Rotation(V(0,0,1),best[1]).multiply(A.Rotation(V(0,1,0),180));nut=install('ISO7719_M5','Sicherungsmutter Blattwurzel',idx,(x,y,-1),a,nr)
            new_pairs.append(dict(bolt=bolt.Name,mate=nut.Name,family='D06 Blattwurzel M5',fitted_nominal_phase_deg=best[1]))
for obj in masters.values():obj.Visibility=False
doc.recompute()
pose_checks=[]
for row in bom:
    obj=doc.getObject(row['instance']);expected=obj.LinkedObject.Shape.copy();expected.Placement=obj.LinkPlacement.multiply(expected.Placement);actual=obj.Shape
    aa=actual.BoundBox;bb=expected.BoundBox;delta=max(abs(getattr(aa,k)-getattr(bb,k)) for k in ['XMin','XMax','YMin','YMax','ZMin','ZMax']);assert delta<1e-5,(row['instance'],delta)
    pose_checks.append(dict(instance=row['instance'],maximum_world_bbox_delta_mm=delta))
interface_checks=[]
def pattern(obj,centre,radius):
    points=[]
    for f in obj.Shape.Faces:
        if not isinstance(f.Surface,Part.Cylinder):continue
        surface=f.Surface;p=surface.Center
        if abs(surface.Radius-radius)<1e-6 and abs(math.hypot(p.x-centre[0],p.y-centre[1])-20)<1e-6:
            if not any(math.hypot(x-p.x,y-p.y)<1e-5 for x,y in points):points.append((p.x,p.y))
    return points
for rotor in rotors:
    centre=rotor['centre_mm'];mrow=next(r for r in bom if r['id']=='D05_MN1330_LEGACY_REF' and math.dist(r['placement_mm'][:2],centre[:2])<.001);hrow=next(r for r in bom if r['id']=='D06_HUB' and r['rotor_id']==rotor['id'])
    mp=pattern(doc.getObject(mrow['instance']),centre,2.65);hp=pattern(doc.getObject(hrow['instance']),centre,2.75);assert len(mp)==len(hp)==12
    error=max(min(math.dist(a,b) for b in mp) for a in hp);assert error<1e-5
    interface_checks.append(dict(rotor_id=rotor['id'],hole_count=12,pcd_mm=40,maximum_axis_misalignment_mm=error,nominal_reference_only=True,motor_thread_depth_verified=False,motor_bolts_installed=False))
doc.recompute();doc.saveAs(str(native))
for n,data in [('Instanzen.json',bom),('Bauteile.json',specs),('Neue_Gewindepaare.json',new_pairs),('Rotoren.json',rotors)]: (O/n).write_text(json.dumps(data,indent=2,ensure_ascii=False))
with (O/'Blattstationen.csv').open('w',newline='') as f:
    w=csv.writer(f,delimiter=';');w.writerow(['Radius_mm','Sehne_mm','Geometrischer_Pitch_grad','Dickenverhaeltnis','Sehnenbezug']);w.writerows(P['sections_r_chord_pitch_tc_axis'])
report=dict(revision=P['revision'],production_ready=False,modeled_instances=len(bom),part_types=len(specs),mass_modeled_kg=sum(r['mass_kg'] for r in bom),previous_D05_mass_kg=sum(r['mass_kg'] for r in bom[:base_count]),propeller_added_mass_kg=sum(r['mass_kg'] for r in bom[base_count:]),rotor_count=4,blades_per_rotor=3,blade_count=12,rotation_pairs='2 CW + 2 CCW viewed from +Z toward aircraft',rotor_radius_mm=380,cfk_article='CBU20171005TG',motor_model='MN1330 KV40',motor_cad_fidelity='Legacy P14 nominal reference, not detailed OEM',propeller_geometry='Detailed own design, not measured/qualified OEM propeller',motor_to_hub_bolts_installed=False,rotor_height_changed=False,integration_clearance_closed=False,airfoil_map_verified=False,laminate_defined=False,excluded=['Akku','Regler','Versorgungskabelbaum','Rotorschutz','Landegestell','Motor-Naben-Schrauben: Gewindetiefe und Länge offen'],native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),base_native_sha256=hashlib.sha256((BASE/'Ausgabe/QuadR380_D05_MN1330.FCStd').read_bytes()).hexdigest(),source_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),geometry_script_sha256=hashlib.sha256((H/'geometrie.py').read_bytes()).hexdigest(),parameter_sha256=hashlib.sha256((H/'parameter.json').read_bytes()).hexdigest())
report['motor_reference_native_14mm_datum_error_fixed']=True
(O/'Native_Platzierung_Pruefung.json').write_text(json.dumps(dict(native_sha256=report['native_sha256'],passed=True,checks=pose_checks,scope='All native instance bounding boxes match the transformed master geometry used for mesh rendering. The four legacy motor references now actually occupy z88..154; only their former ignored -14mm master-placement normalization was baked into a compound.'),indent=2))
(O/'Naben_Schnittstellen_Pruefung.json').write_text(json.dumps(dict(native_sha256=report['native_sha256'],nominal_hole_axes_match=True,checks=interface_checks,scope='All48 motor/hub hole axes coincide in actual native CAD at default phase, including the15deg hub-hole phase required by the installed legacy motor orientations. Only legacy nominal geometry, not a confirmed OEM pattern, thread engagement, centering or load release.'),indent=2))
(O/'Status.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print('D06 built',report['modeled_instances'],report['mass_modeled_kg'],'added',report['propeller_added_mass_kg'],flush=True)
