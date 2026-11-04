"""Assembly-stage access checks, continuous cassette insertion and joint registry."""
import sys,json,math,csv,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
V=A.Vector;native=O/'QuadR380_D01_Mechanik.FCStd';doc=A.openDocument(str(native));bom=json.loads((O/'Instanzen.json').read_text());byname={r['instance']:r for r in bom};threads=json.loads((O/'Gewindepruefung.json').read_text());candidates=[];access=[];insertion=[];registry=[];cache={}
def common(a,b):return max(0.,a.common(b).Volume)
stages={'Wurzelklemmschraube':'Rahmen vor Antrieb/Schutz','Endtraeger-Klemmschraube':'Endtraeger vor OEM-Adapter','Stuetzenfuss M6':'Rahmenmontage','Stuetzenkopf M6':'Rahmenmontage','Deckschraube':'Deckmontage','Druckstueck-Sicherung':'Arm+Druckstueck vor Wurzelklemmung','Kassetten-Deckelschraube':'Kassette ausserhalb Deckrohr vormontieren'}
preload={'Wurzelklemmschraube':8000,'Endtraeger-Klemmschraube':6500,'Stuetzenfuss M6':3000,'Stuetzenkopf M6':3000,'Deckschraube':1500,'Druckstueck-Sicherung':2000,'Kassetten-Deckelschraube':500}
for row in threads:
    br=byname[row['bolt']];bolt=doc.getObject(row['bolt']);mate=doc.getObject(row['mate']);typ=br['id'].split('_')[1];diam=float(typ.split('x')[0][1:]);head_height=diam;af={3:2.5,5:4,6:5}[diam];axis=bolt.LinkPlacement.Rotation.multVec(V(0,0,1));origin=bolt.LinkPlacement.Base+axis*(head_height+.1);tool=Part.makeCylinder(af/math.sqrt(3)+.6,35,origin,axis)
    stage=stages[br['label']];scope=bom
    if br['label']=='Druckstueck-Sicherung':
        # Other full-assembly fasteners are deliberately absent in this documented stage.
        scope=[r for r in bom if r['id'] in ['QD_R01','QD_E01'] and doc.getObject(r['instance']).Shape.BoundBox.intersect(mate.Shape.BoundBox)]
    if br['label']=='Kassetten-Deckelschraube':scope=[r for r in bom if r['id'] in ['QD_K01','QD_K02'] and doc.getObject(r['instance']).Shape.BoundBox.intersect(mate.Shape.BoundBox)]
    hits=[]
    for other in scope:
        if other['instance']==row['bolt']:continue
        s=doc.getObject(other['instance']).Shape
        if tool.BoundBox.intersect(s.BoundBox):
            vol=common(tool,s)
            if vol>.1:hits.append(dict(instance=other['instance'],part=other['id'],volume_mm3=vol))
    access.append(dict(bolt=bolt.Name,stage=stage,hex_AF_mm=af,analytical_tool_radius_mm=af/math.sqrt(3)+.6,approach_length_mm=35,positive_intersections=hits,passed=not hits))
    f=preload[br['label']];joint=dict(bolt=bolt.Name,mate=mate.Name,bolt_id=br['id'],mate_id=byname[mate.Name]['id'],function=br['label'],assembly_stage=stage,preload_target_N=f,torque_K018_024_reference_Nm=[.18*f*diam/1000,.24*f*diam/1000],torque_released=False,reason='Reibung, Sicherungsmoment und VDI2230-Verhalten nicht qualifiziert',geometric_thread_fit=row['passed'])
    registry.append(joint)
    if 'Verbundpartner' not in bolt.PropertiesList:bolt.addProperty('App::PropertyLink','Verbundpartner','D01 Verbindung')
    bolt.Verbundpartner=mate
    if 'Vorspannung_Ziel' not in bolt.PropertiesList:bolt.addProperty('App::PropertyForce','Vorspannung_Ziel','D01 Verbindung')
    bolt.Vorspannung_Ziel=str(f)+' N'
    if 'Montagestufe' not in bolt.PropertiesList:bolt.addProperty('App::PropertyString','Montagestufe','D01 Verbindung')
    bolt.Montagestufe=stage
    print('Tool',bolt.Name,stage,not hits,flush=True)

# Cassette may slide inside an unperforated, uniform tube; holes can only remove
# additional material. Deck collars and support bolts must be installed afterwards.
for carrier_row in [r for r in bom if r['id']=='QD_K01']:
    carrier=doc.getObject(carrier_row['instance']);x,y,z=carrier.LinkPlacement.Base
    beam_row=next(r for r in bom if r['id']=='QD_R02' and abs(r['placement_mm'][1]-y)<.01);beam=doc.getObject(beam_row['instance']);master=beam.LinkedObject;blank=next(f for f in master.Group if f.TypeId=='PartDesign::Pad').Shape.copy();blank.Placement=beam.LinkPlacement.multiply(blank.Placement)
    members=[]
    for r in bom:
        p=doc.getObject(r['instance']).LinkPlacement.Base
        selected=(r['id'] in ['QD_K01','QD_K02'] and abs(p.x-x)<.01 and abs(p.y-y)<.01) or (r['label']=='Gefangene Sicherungsmutter' and abs(p.x-x)<=20.01 and abs(p.y-y)<=9.01) or (r['label']=='Kassetten-Deckelschraube' and abs(p.x-x)<=30.01 and abs(p.y-y)<.01)
        if selected:members.append(r)
    assert len(members)==8
    hits=[]
    for r in members:
        obj=doc.getObject(r['instance']);s=obj.Shape;rel=beam.LinkPlacement.inverse().multiply(obj.LinkPlacement);key=(r['id'],round(rel.Base.x,6),round(rel.Base.y,6),tuple(round(v,6) for v in rel.Rotation.Q))
        if key not in cache:cache[key]=common(blank,s)
        if cache[key]>.1:hits.append(dict(instance=r['instance'],volume_mm3=cache[key]))
    insertion.append(dict(carrier=carrier.Name,members=[r['instance'] for r in members],direction_from_open_end='right' if x>0 else 'left',target_x_mm=x,passed=not hits,intersections=hits,method='8 true solids against uniform unperforated tube at fully internal position; axial translation preserves cross-section. From corresponding open end, before deck collars/support bolts. Other cassette remains on opposite half.'))
report=dict(geometric_access=access,cassette_insertion=insertion,tool_checks_passed=all(x['passed'] for x in access),cassette_checks_passed=all(x['passed'] for x in insertion),scope='Analytical straight tool clearance cylinders, not OEM tool CAD. Nominal rigid geometry, stage-specific; socket fit from ISO AF dimensions, not manual dexterity, torque or production validation.')
(O/'Montage_Pruefung.json').write_text(json.dumps(report,indent=2));(O/'Schraubstellen.json').write_text(json.dumps(registry,indent=2))
with (O/'Schraubstellen.csv').open('w',newline='') as f:w=csv.DictWriter(f,list(registry[0]));w.writeheader();w.writerows(registry)
doc.recompute();doc.saveAs(str(native));r=json.loads((O/'Pruefung.json').read_text());r['native_sha256']=hashlib.sha256(native.read_bytes()).hexdigest();r['tool_approach_screen_pass']=report['tool_checks_passed'];r['cassette_insertion_screen_pass']=report['cassette_checks_passed'];(O/'Pruefung.json').write_text(json.dumps(r,indent=2,ensure_ascii=False));print('Montage',report['tool_checks_passed'],report['cassette_checks_passed'],flush=True)
