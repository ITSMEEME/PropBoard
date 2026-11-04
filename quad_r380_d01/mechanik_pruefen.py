"""Actual solid interference, screw phase, engagement and demand-only frame QA."""
import sys,json,math,hashlib,csv
from pathlib import Path
sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
H=Path(__file__).resolve().parent;O=H/'Ausgabe';native=O/'QuadR380_D01_Mechanik.FCStd';doc=A.openDocument(str(native));bom=json.loads((O/'Instanzen.json').read_text());spec=json.loads((O/'Bauteile.json').read_text());P=json.loads((H/'parameter.json').read_text());byname={r['instance']:r for r in bom};rows=[];cache={};phases={};threshold=.05
reuse_records={r['bolt']:r for r in json.loads((O/'Gewinde_Wiederverwendung.json').read_text())} if '--reuse-verified-threads' in sys.argv else {};geometry_hashes={}
def geometry_digest(obj):
    if obj.Name not in geometry_hashes:geometry_hashes[obj.Name]=hashlib.sha256(obj.Shape.exportBrepToString().encode()).hexdigest()
    return geometry_hashes[obj.Name]
def axis(obj):return obj.LinkPlacement.Rotation.multVec(A.Vector(0,0,1))
def volume(a,b):return max(0.,a.common(b).Volume)
def shape_for(obj,rotation):
    s=obj.LinkedObject.Shape.copy();s.Placement=A.Placement(obj.LinkPlacement.Base,rotation).multiply(s.Placement);return s
def tune(bolt,mate,signature,seed=0,reference_base=None):
    normal=axis(bolt);short_base=A.Rotation(A.Vector(0,0,1),normal);base=reference_base or short_base;p=bolt.LinkPlacement.Base;target=mate.LinkedObject.Shape;inverse=mate.LinkPlacement.inverse()
    if bolt.Name in reuse_records:
        ref=reuse_records[bolt.Name];assert ref['mate']==mate.Name
        assert geometry_digest(bolt.LinkedObject)==ref['master_a_sha256'] and geometry_digest(mate.LinkedObject)==ref['master_b_sha256']
        rel=bolt.LinkPlacement.inverse().multiply(mate.LinkPlacement);current=list(rel.Base)+list(rel.Rotation.Q);expected=ref['relative_placement'];assert max(abs(x-y) for x,y in zip(current,expected))<1e-7
        result=dict(ref['result']);result['reused_identical_master_and_relative_placement']=True;result['intersection_mm3']=max(0,result['intersection_mm3'])
        fmt=lambda x:f'{0 if abs(x)<5e-7 else x:.6f}';row=byname[bolt.Name];ck=row['id']+'@'+','.join(fmt(x) for x in p)+'|'+','.join(fmt(x) for x in normal);phases[ck]=result['phase_deg'];return result
    def result_for(phase,v,reused=None):
        desired=A.Rotation(normal,phase).multiply(base);bolt.LinkPlacement=A.Placement(p,desired)
        delta=desired.multiply(short_base.inverted());signed=math.degrees(delta.Angle)*(1 if delta.Axis.dot(normal)>=0 else -1);global_phase=signed%360
        row=byname[bolt.Name];fmt=lambda x:f'{0 if abs(x)<5e-7 else x:.6f}';ck=row['id']+'@'+','.join(fmt(x) for x in p)+'|'+','.join(fmt(x) for x in normal);phases[ck]=global_phase
        r=dict(bolt=bolt.Name,mate=mate.Name,phase_deg=global_phase,reference_phase_deg=phase,intersection_mm3=v,passed=v<=threshold)
        if reused:r['rigid_or_homologous_pattern_reference']=reused
        return r
    reused=signature in cache
    if reused:
        prior=cache[signature];return result_for(prior['phase'],prior['volume'],prior['reference'])
    else:candidates=[seed,(seed+15)%360,(seed-15)%360,(seed+30)%360,(seed-30)%360]+list(range(0,360,30))
    best=(float('inf'),0)
    for phase in candidates:
        r=A.Rotation(normal,phase).multiply(base);s=shape_for(bolt,r);s.Placement=inverse.multiply(s.Placement);v=volume(s,target)
        if v<best[0]:best=(v,phase)
        if v<=threshold:break
    if best[0]>threshold:
        centre=best[1]
        for delta in range(-15,16,3):
            phase=(centre+delta)%360;r=A.Rotation(normal,phase).multiply(base);s=shape_for(bolt,r);s.Placement=inverse.multiply(s.Placement);v=volume(s,target)
            if v<best[0]:best=(v,phase)
            if v<=threshold:break
    phase=best[1];cache[signature]=dict(phase=phase,volume=best[0],reference=bolt.Name)
    result=result_for(phase,best[0]);(O/'Gewindereferenzen_Zwischenstand.json').write_text(json.dumps(dict(references=[dict(key=str(k),**v) for k,v in cache.items()],phases=phases),indent=2));return result
bolts=[r for r in bom if r['id'].startswith('ISO4762')];nuts=[r for r in bom if r['id'].startswith('ISO7719')]
for nr in nuts:
    nut=doc.getObject(nr['instance']);p=nut.LinkPlacement.Base;diam=nr['id'].split('_')[1];choices=[]
    for br in bolts:
        if not br['id'].split('_')[1].startswith(diam+'x'):continue
        bolt=doc.getObject(br['instance']);a=axis(bolt);dp=p-bolt.LinkPlacement.Base;d=-dp.dot(a);offset=(dp+a*d).Length;L=float(br['id'].split('x')[1])
        if offset<.001 and 0<d<L:choices.append((bolt,d,L,br))
    assert len(choices)==1,('Ambiguous bolt/nut',nr['instance'],len(choices))
    bolt,d,L,br=choices[0];pitch=1 if diam=='M6' else .8;signature=(br['id'],nr['id'],round(d,5));seed=(195+360*(d/pitch-65.2))%360
    result=tune(bolt,nut,signature,seed);result.update(nominal_length_mm=L,bearing_distance_mm=d,pitch_mm=pitch,nut_height_mm=5.9 if diam=='M6' else 5.3,nominal_protrusion_mm=L-d-(5.9 if diam=='M6' else 5.3));rows.append(result);print('Thread',br['id'],nr['instance'],result['passed'],round(result['intersection_mm3'],6),flush=True)
for br in bolts:
    if br['label'] not in ['Druckstueck-Sicherung','Kassetten-Deckelschraube']:continue
    bolt=doc.getObject(br['instance']);family='QD_E01' if br['label']=='Druckstueck-Sicherung' else 'QD_K01';mates=[doc.getObject(r['instance']) for r in bom if r['id']==family and doc.getObject(r['instance']).Shape.BoundBox.intersect(bolt.Shape.BoundBox)]
    assert len(mates)==1,('Tapped-hole match',br['instance'],len(mates))
    mate=mates[0];hole=next(f for f in mate.LinkedObject.Group if f.TypeId=='PartDesign::Hole');profile=hole.Profile[0] if isinstance(hole.Profile,tuple) else hole.Profile
    assert hole.ModelThread and len(profile.Geometry)==2 and family in ['QD_E01','QD_K01']
    # These two CAD families use a native equal-hole pattern. End/neighbor faces
    # lie outside the bolt envelope; each local mating surface is identical.
    local=profile.Placement.inverse().multVec(mate.LinkPlacement.inverse().multVec(bolt.LinkPlacement.Base));reference_base=mate.LinkPlacement.Rotation.multiply(profile.Placement.Rotation)
    assert reference_base.multVec(A.Vector(0,0,1)).dot(axis(bolt))>.999999
    delta=bolt.LinkPlacement.Rotation.multiply(reference_base.inverted());existing_phase=math.degrees(delta.Angle)*(1 if delta.Axis.dot(axis(bolt))>=0 else -1)%360
    signature=('NativeEqualHolePattern',br['id'],family,str(hole.ThreadSize),float(hole.ThreadDepth),round(local.z,6));rows.append(tune(bolt,mate,signature,seed=existing_phase,reference_base=reference_base));print('Tapped',br['instance'],rows[-1]['passed'],round(rows[-1]['intersection_mm3'],6),flush=True)
doc.recompute();(O/'Gewindephasen.json').write_text(json.dumps(dict(scope='Geometric helicoidal fit only; no tightening torque or manufacturing tolerance certificate',phases=phases),indent=2))
# Actual assembly-wide check, with repeated rigid pairs cached by relative placement.
shapes={r['instance']:doc.getObject(r['instance']).Shape for r in bom};interferences=[];checked=0;pair_cache={};thread_volumes={frozenset([r['bolt'],r['mate']]):r['intersection_mm3'] for r in rows}
for i,r in enumerate(bom):
    a=shapes[r['instance']];oa=doc.getObject(r['instance'])
    for q in bom[i+1:]:
        b=shapes[q['instance']]
        if not a.BoundBox.intersect(b.BoundBox):continue
        ob=doc.getObject(q['instance']);rel=oa.LinkPlacement.inverse().multiply(ob.LinkPlacement);key=(r['id'],q['id'],tuple(round(v,5) for v in list(rel.Base)+list(rel.Rotation.Q)))
        if key not in pair_cache:pair_cache[key]=thread_volumes.get(frozenset([r['instance'],q['instance']]),None)
        if pair_cache[key] is None:pair_cache[key]=volume(a,b)
        v=pair_cache[key];checked+=1
        if v>.1:interferences.append(dict(a=r['instance'],b=q['instance'],part_a=r['id'],part_b=q['id'],label_a=r['label'],label_b=q['label'],volume_mm3=v))
    if i%50==0:print('Collision',i,'checked',checked,'findings',len(interferences),flush=True)
for r in bom:
    obj=doc.getObject(r['instance']);r['placement_mm']=list(obj.LinkPlacement.Base);r['placement_quaternion']=list(obj.LinkPlacement.Rotation.Q)
for obj in doc.Objects:
    if obj.TypeId=='PartDesign::Body':
        for feature in obj.Group:
            if hasattr(feature,'Visibility'):feature.Visibility=feature==obj.Tip
        obj.Visibility=False
(O/'Instanzen.json').write_text(json.dumps(bom,indent=2))
with (O/'Stueckliste.csv').open('w',newline='') as file:
    writer=csv.DictWriter(file,list(bom[0]));writer.writeheader();writer.writerows(bom)
doc.saveAs(str(native));Import=None
import Import
Import.export([doc.getObject(r['instance']) for r in bom],str(O/'QuadR380_D01_Mechanik.step'))
report=json.loads((O/'Pruefung.json').read_text());report['native_sha256']=hashlib.sha256(native.read_bytes()).hexdigest();report['thread_pairs_checked']=len(rows);report['thread_geometry_pass']=all(r['passed'] for r in rows);report['positive_interference_count_over_0_1mm3']=len(interferences);report['production_ready']=False;report['mass_modeled_kg']=sum(r['mass_kg'] for r in bom)
(O/'Pruefung.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));(O/'Kollisionen.json').write_text(json.dumps(dict(scope='All placed solid pairs, no excluded part/contact families. Values <=0.1mm³ are below reporting tolerance. Thread geometry nominal; no preload/contact FEM.',candidate_pairs=checked,unique_pairs=len(pair_cache),interferences=interferences),indent=2));(O/'Gewindepruefung.json').write_text(json.dumps(rows,indent=2))
print('Checked',len(rows),'thread pairs,',checked,'solid pairs;',len(interferences),'interferences',flush=True)
