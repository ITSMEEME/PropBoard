"""Actual solid interference, screw phase, engagement and demand-only frame QA."""
import sys,json,math,hashlib,csv
from pathlib import Path
sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
H=Path(__file__).resolve().parent;O=H/'Ausgabe';native=O/'QuadR380_D04_CFK.FCStd';doc=A.openDocument(str(native));bom=json.loads((O/'Instanzen.json').read_text());spec=json.loads((O/'Bauteile.json').read_text());P=json.loads((H/'parameter.json').read_text());byname={r['instance']:r for r in bom};rows=[];cache={};phases={};threshold=.05
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
prior=json.loads((O/'D03_Gewindereferenzen.json').read_text());reused=0
for q in prior:
 r=q['result'];bolt=doc.getObject(r['bolt']);mate=doc.getObject(r['mate'])
 if geometry_digest(bolt.LinkedObject)!=q['master_a_sha256'] or geometry_digest(mate.LinkedObject)!=q['master_b_sha256']:continue
 rel=bolt.LinkPlacement.inverse().multiply(mate.LinkPlacement);current=list(rel.Base)+list(rel.Rotation.Q)
 assert max(abs(x-y) for x,y in zip(current,q['relative_placement']))<1e-7
 r=dict(r);r['reused_D03_exact_master_geometry_and_relative_pose']=True;rows.append(r);reused+=1
assert reused==28,reused
previous_path=O/'D04_Gewindereferenzen_vor_Korrektur.json';previous={x['result']['bolt']:x for x in json.loads(previous_path.read_text())} if previous_path.exists() else {}
for pair in json.loads((O/'Neue_Gewindepaare.json').read_text()):
 bolt=doc.getObject(pair['bolt']);mate=doc.getObject(pair['mate'])
 if pair['bolt'] in previous:
  ref=previous[pair['bolt']];rel=bolt.LinkPlacement.inverse().multiply(mate.LinkPlacement);values=list(rel.Base)+list(rel.Rotation.Q)
  if ref['result']['mate']==pair['mate'] and geometry_digest(bolt.LinkedObject)==ref['master_a_sha256'] and geometry_digest(mate.LinkedObject)==ref['master_b_sha256'] and max(abs(x-y) for x,y in zip(values,ref['relative_placement']))<1e-7:
   result=dict(ref['result']);result['reused_exact_D04_geometry_and_relative_pose']=True;rows.append(result)
   fmt=lambda x:f'{0 if abs(x)<5e-7 else x:.6f}';ck=byname[bolt.Name]['id']+'@'+','.join(fmt(x) for x in bolt.LinkPlacement.Base)+'|'+','.join(fmt(x) for x in axis(bolt));phases[ck]=result['phase_deg'];print('Reused D04',bolt.Name,flush=True);continue
 if pair['family']=='D04 Saddle nut M6':
  dp=mate.LinkPlacement.Base-bolt.LinkPlacement.Base;distance=-dp.dot(axis(bolt));assert (dp+axis(bolt)*distance).Length<1e-5
  result=tune(bolt,mate,('nut',byname[bolt.Name]['id'],round(distance,6)),seed=(195+360*(distance-65.2))%360);result['nominal_protrusion_mm']=45-distance-5.9
 else:
  suffix=re.sub(r'[^A-Za-z0-9_]','_',pair['hole_suffix']);features=[f for f in mate.LinkedObject.Group if f.TypeId=='PartDesign::Hole' and f.Name.endswith(suffix)];assert len(features)==1,(pair,[x.Name for x in mate.LinkedObject.Group]);hole=features[0];profile=hole.Profile[0] if isinstance(hole.Profile,tuple) else hole.Profile;base=mate.LinkPlacement.Rotation.multiply(profile.Placement.Rotation);assert base.multVec(A.Vector(0,0,1)).dot(axis(bolt))>.99999
  local=profile.Placement.inverse().multVec(mate.LinkPlacement.inverse().multVec(bolt.LinkPlacement.Base));signature=(pair['family'],byname[mate.Name]['id'],suffix,str(hole.ThreadSize),float(hole.ThreadDepth),round(local.z,6));delta=bolt.LinkPlacement.Rotation.multiply(base.inverted());seed=math.degrees(delta.Angle)*(1 if delta.Axis.dot(axis(bolt))>=0 else -1)%360;result=tune(bolt,mate,signature,seed=seed,reference_base=base)
 result['family']=pair['family'];rows.append(result);print('Thread',len(rows),pair['family'],bolt.Name,result['passed'],round(result['intersection_mm3'],6),flush=True)
passed=all(r['passed'] for r in rows);evidence=dict(scope='New D04 native threaded pairs plus28 D03 pairs reused only with exact BRep hashes and relative pose. Other P12 core-only pinch/arm joints remain unverified.',pairs=rows,reused_D03=reused,new_pairs=len(rows)-reused,passed=passed);(O/'Gewindepruefung.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False))
if not passed:raise RuntimeError('Thread evidence contains failures')
for r in bom:
 obj=doc.getObject(r['instance']);r['placement_mm']=list(obj.LinkPlacement.Base);r['placement_quaternion']=list(obj.LinkPlacement.Rotation.Q)
 if r.get('foot_side'):assert any(e[0].lstrip('.')=='LinkPlacement.Base.x' for e in obj.ExpressionEngine)
doc.recompute();doc.saveAs(str(native));(O/'Instanzen.json').write_text(json.dumps(bom,indent=2,ensure_ascii=False));(O/'Gewindephasen.json').write_text(json.dumps(dict(phases=phases),indent=2));evidence['native_sha256']=hashlib.sha256(native.read_bytes()).hexdigest();(O/'Gewindepruefung.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False));r=json.loads((O/'Status.json').read_text());r.update(native_sha256=evidence['native_sha256'],thread_pairs_checked=len(rows),thread_geometry_pass=True);(O/'Status.json').write_text(json.dumps(r,indent=2,ensure_ascii=False));print('D04 threads passed',len(rows),flush=True)
