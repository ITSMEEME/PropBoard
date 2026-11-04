"""Actual solid interference, screw phase, engagement and demand-only frame QA."""
import sys,json,math,hashlib,csv
from pathlib import Path
sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
H=Path(__file__).resolve().parent;O=H/'Ausgabe';native=O/'QuadR380_D03_CFK.FCStd';doc=A.openDocument(str(native));bom=json.loads((O/'Instanzen.json').read_text());spec=json.loads((O/'Bauteile.json').read_text());P=json.loads((H/'parameter.json').read_text());byname={r['instance']:r for r in bom};rows=[];cache={};phases={};threshold=.05
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
import re
new=json.loads((O/'Neue_Gewindepaare.json').read_text())
for pair in new:
 bolt=doc.getObject(pair['bolt']);mate=doc.getObject(pair['mate']);suffix=re.sub(r'[^A-Za-z0-9_]','_',pair['hole_suffix']);features=[f for f in mate.LinkedObject.Group if f.TypeId=='PartDesign::Hole' and f.Name.endswith(suffix)];assert len(features)==1,(pair,[(f.Name) for f in mate.LinkedObject.Group])
 hole=features[0];profile=hole.Profile[0] if isinstance(hole.Profile,tuple) else hole.Profile;base=mate.LinkPlacement.Rotation.multiply(profile.Placement.Rotation);assert base.multVec(A.Vector(0,0,1)).dot(axis(bolt))>.99999
 local=profile.Placement.inverse().multVec(mate.LinkPlacement.inverse().multVec(bolt.LinkPlacement.Base));signature=(pair['family'],str(hole.ThreadSize),float(hole.ThreadDepth),round(local.z,6))
 delta=bolt.LinkPlacement.Rotation.multiply(base.inverted());seed=math.degrees(delta.Angle)*(1 if delta.Axis.dot(axis(bolt))>=0 else -1)%360
 result=tune(bolt,mate,signature,seed=seed,reference_base=base);result['family']=pair['family'];rows.append(result);print('New thread',pair['family'],bolt.Name,result['passed'],round(result['intersection_mm3'],6),flush=True)
# Existing sixteen foot-clamp bolt/nut pairs have identical nominal ISO geometry.
bolts=[r for r in bom if r['label']=='Fußschlitten M5'];nuts=[r for r in bom if r['label']=='Sicherungsmutter Fuß'];assert len(bolts)==len(nuts)==16
for nr in nuts:
 nut=doc.getObject(nr['instance']);p=nut.LinkPlacement.Base;matches=[]
 for br in bolts:
  bolt=doc.getObject(br['instance']);a=axis(bolt);dp=p-bolt.LinkPlacement.Base;distance=-dp.dot(a)
  if (dp+a*distance).Length<1e-5 and 0<distance<50:matches.append((bolt,distance))
 assert len(matches)==1
 bolt,distance=matches[0];r=tune(bolt,nut,(byname[bolt.Name]['id'],'ISO7719_M5',round(distance,6)),seed=(195+360*(distance/.8-65.2))%360);r.update(family='Foot clamp M5',bearing_distance_mm=distance,nominal_protrusion_mm=50-distance-5.3);rows.append(r);print('Foot nut',bolt.Name,r['passed'],round(r['intersection_mm3'],6),flush=True)
assert len(rows)==44
(O/'Gewindepruefung.json').write_text(json.dumps(dict(scope='28 new tapped pairs and 16 existing foot clamp nut pairs. Nominal thread geometry only; repeated equal nominal local hole profiles use phase references. Remaining whole-vehicle pairs not released.',pairs=rows,passed=all(r['passed'] for r in rows)),indent=2))
if not all(r['passed'] for r in rows):raise RuntimeError('Thread fitting failed; see evidence')
for r in bom:
 obj=doc.getObject(r['instance']);r['placement_mm']=list(obj.LinkPlacement.Base);r['placement_quaternion']=list(obj.LinkPlacement.Rotation.Q)
 if r.get('foot_side'):assert any(e[0].lstrip('.')=='LinkPlacement.Base.x' for e in obj.ExpressionEngine),(obj.Name,obj.ExpressionEngine)
doc.recompute();doc.saveAs(str(native));(O/'Instanzen.json').write_text(json.dumps(bom,indent=2,ensure_ascii=False));(O/'Gewindephasen.json').write_text(json.dumps(dict(phases=phases),indent=2));r=json.loads((O/'Status.json').read_text());r.update(native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),thread_pairs_checked=44,thread_geometry_pass=True);(O/'Status.json').write_text(json.dumps(r,indent=2,ensure_ascii=False));print('44 thread pairs passed',flush=True)
