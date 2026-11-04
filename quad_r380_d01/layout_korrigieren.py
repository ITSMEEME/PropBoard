"""Move complete deck-column joints and their native hole patterns together.

The verified thread solids remain identical. Retuning is avoided only when both
master BReps and the complete relative placement of a verified pair are unchanged.
"""
import sys,json,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,Sketcher
V=A.Vector;P=json.loads((H/'parameter.json').read_text());native=O/'QuadR380_D01_Mechanik.FCStd';doc=A.openDocument(str(native));bom=json.loads((O/'Instanzen.json').read_text());threads=json.loads((O/'Gewindepruefung.json').read_text());spec=json.loads((O/'Bauteile.json').read_text());hashes={}
def digest(obj):
    if obj.Name not in hashes:hashes[obj.Name]=hashlib.sha256(obj.Shape.exportBrepToString().encode()).hexdigest()
    return hashes[obj.Name]
references=[]
for row in threads:
    a,b=doc.getObject(row['bolt']),doc.getObject(row['mate']);rel=a.LinkPlacement.inverse().multiply(b.LinkPlacement)
    references.append(dict(bolt=row['bolt'],mate=row['mate'],master_a_sha256=digest(a.LinkedObject),master_b_sha256=digest(b.LinkedObject),relative_placement=list(rel.Base)+list(rel.Rotation.Q),result=row))
def remake(sk,points,diam):
    for i in range(sk.ConstraintCount-1,-1,-1):sk.delConstraint(i)
    for i in range(sk.GeometryCount-1,-1,-1):sk.delGeometry(i)
    for x,y in points:
        idx=sk.addGeometry(Part.Circle(V(x,y,0),V(0,0,1),diam/2),False);sk.addConstraint(Sketcher.Constraint('Block',idx))
root=[]
for ang in [45,135,225,315]:
    co,si=math.cos(math.radians(ang)),math.sin(math.radians(ang))
    for r in P['root_bolt_radial_positions_mm']:
        for t in P['root_bolt_tangent_positions_mm']:root.append((r*co-t*si,r*si+t*co))
feet=[(x+dx,y+dy) for x,y in P['post_xy_mm'] for dx in [-20,20] for dy in [-9,9]]
remake(doc.getObject('SK_QD_P01_M6_Durchgang'),root+feet,6.6)
for key in ['QD_P01','QD_P02']:
    sk=doc.getObject('SK_'+key+'_Formschluessige_Armsitze')
    for i in range(sk.ConstraintCount-1,-1,-1):sk.delConstraint(i)
    for i in range(sk.GeometryCount-1,-1,-1):sk.delGeometry(i)
    for a in [45,135,225,315]:
        co,si=math.cos(math.radians(a)),math.sin(math.radians(a));pts=[]
        for x,y in [(135,-25.1),(315,-25.1),(315,25.1),(135,25.1)]:pts.append(V(x*co-y*si,x*si+y*co,0))
        for j in range(4):idx=sk.addGeometry(Part.LineSegment(pts[j],pts[(j+1)%4]),False);sk.addConstraint(Sketcher.Constraint('Block',idx))
doc.getObject('PD_QD_E01_Pad').Length=P['arm_insert_mm'][2];doc.getObject('QD_E01').Label='Eingepasstes Wurzel-Druckstueck 43.97×43.97×135'
carrier=doc.getObject('QD_K01')
if doc.getObject('PD_QD_K01_Freigang_0_8') is None:
    tip=carrier.Tip;edges=[]
    for i,e in enumerate(tip.Shape.Edges,1):
        bb=e.BoundBox
        if abs(bb.ZMin)<1e-6 and abs(bb.ZMax)<1e-6 and abs(abs(e.CenterOfMass.y)-16.8)<1e-6 and e.Length>65:edges.append('Edge'+str(i))
    assert len(edges)==2
    cf=carrier.newObject('PartDesign::Chamfer','PD_QD_K01_Freigang_0_8');cf.Base=(tip,edges);cf.Size=.8;carrier.Tip=cf
beam=[(x+310+dx,dy) for x in sorted(set(v[0] for v in P['post_xy_mm'])) for dx in [-20,20] for dy in [-9,9]];remake(doc.getObject('SK_QD_R02_Stuetze_M6'),beam,6.6)
labels={'Deckstuetze','Sicherungsmutter-Kassette','Kassettendeckel','Stuetzenfuss M6','Fussscheibe','Fusssicherung','Stuetzenkopf M6','Kopfscheibe Stuetze','Gefangene Sicherungsmutter','Kassetten-Deckelschraube'}
old_x=abs(next(r['placement_mm'][0] for r in bom if r['label']=='Deckstuetze'));new_x=abs(P['post_xy_mm'][0][0]);delta_x=new_x-old_x
for row in bom:
    if row['label'] not in labels:continue
    obj=doc.getObject(row['instance']);p=obj.LinkPlacement.Base;obj.LinkPlacement=A.Placement(V(p.x+math.copysign(1,p.x)*delta_x,p.y,p.z),obj.LinkPlacement.Rotation)
doc.recompute();verified=[]
for r in references:
    a,b=doc.getObject(r['bolt']),doc.getObject(r['mate']);rel=a.LinkPlacement.inverse().multiply(b.LinkPlacement);new=list(rel.Base)+list(rel.Rotation.Q)
    assert max(abs(x-y) for x,y in zip(new,r['relative_placement']))<1e-7
    if b.LinkedObject.Name in ['QD_E01','QD_K01']:continue # Changed support/carrier: directly recheck 16 bolt/hole pairs.
    assert digest(a.LinkedObject)==r['master_a_sha256'] and digest(b.LinkedObject)==r['master_b_sha256']
    verified.append(r)
for row in bom:
    obj=doc.getObject(row['instance']);row['placement_mm']=list(obj.LinkPlacement.Base);row['placement_quaternion']=list(obj.LinkPlacement.Rotation.Q)
for key in ['QD_P01','QD_P02','QD_R02','QD_E01','QD_K01']:
    obj=doc.getObject(key);assert obj.Shape.isValid() and len(obj.Shape.Solids)==1;spec[key]['label']=obj.Label;spec[key]['volume_mm3']=obj.Shape.Volume;spec[key]['mass_kg']=obj.Shape.Volume*2700e-9;obj.Shape.exportStep(str(O/'Einzelteile'/(key+'.step')))
for r in bom:r['mass_kg']=spec[r['id']]['mass_kg']
phases={}
for r in threads:
    obj=doc.getObject(r['bolt']);row=next(v for v in bom if v['instance']==obj.Name);normal=obj.LinkPlacement.Rotation.multVec(V(0,0,1));fmt=lambda x:f'{0 if abs(x)<5e-7 else x:.6f}';key=row['id']+'@'+','.join(fmt(x) for x in obj.LinkPlacement.Base)+'|'+','.join(fmt(x) for x in normal);phases[key]=r['phase_deg']
(O/'Gewindephasen.json').write_text(json.dumps(dict(scope='Verified nominal helicoidal fit',phases=phases),indent=2));(O/'Gewinde_Wiederverwendung.json').write_text(json.dumps(verified,indent=2));(O/'Instanzen.json').write_text(json.dumps(bom,indent=2));(O/'Bauteile.json').write_text(json.dumps(spec,indent=2));doc.saveAs(str(native));report=json.loads((O/'Pruefung.json').read_text());report['mass_modeled_kg']=sum(r['mass_kg'] for r in bom);report['native_sha256']=hashlib.sha256(native.read_bytes()).hexdigest();(O/'Pruefung.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print('Moved deck joints; retained',len(verified),'thread proofs with exact master geometry and rigid relative placement',flush=True)
