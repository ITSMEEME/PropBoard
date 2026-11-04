"""Actual solid interference, screw phase, engagement and demand-only frame QA."""
import sys,json,math,hashlib,csv
from pathlib import Path
sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
H=Path(__file__).resolve().parent;O=H/'Ausgabe';native=O/'QuadR380_D05_MN1330.FCStd';doc=A.openDocument(str(native));bom=json.loads((O/'Instanzen.json').read_text());spec=json.loads((O/'Bauteile.json').read_text());P=json.loads((H/'parameter.json').read_text());byname={r['instance']:r for r in bom};rows=[];cache={};phases={};threshold=.05
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
prior=json.loads((O/'D04_Gewindereferenzen.json').read_text());maps={}
for folder in ['quad_r380_d03','quad_r380_d04']:
 for q in json.loads((H.parent/folder/'Ausgabe/Neue_Gewindepaare.json').read_text()):maps[q['bolt']]=q
restored_cache={}
for ref in prior:
 r=dict(ref['result']);bolt=doc.getObject(r['bolt']);mate=doc.getObject(r['mate']);rel=bolt.LinkPlacement.inverse().multiply(mate.LinkPlacement);v=list(rel.Base)+list(rel.Rotation.Q);assert max(abs(x-y) for x,y in zip(v,ref['relative_placement']))<1e-7
 if geometry_digest(bolt.LinkedObject)==ref['master_a_sha256'] and geometry_digest(mate.LinkedObject)==ref['master_b_sha256']:
  r['reused_exact_D04_geometry_and_relative_pose']=True;rows.append(r);continue
 # Strict hash mismatches are checked geometrically; no release inferred from a similar label.
 signature=None
 if byname[mate.Name]['id'].startswith('ISO'):
  signature=('rigid',geometry_digest(bolt.LinkedObject),geometry_digest(mate.LinkedObject),tuple(round(z,7) for z in v))
 elif bolt.Name in maps:
  specmap=maps[bolt.Name];suffix=re.sub(r'[^A-Za-z0-9_]','_',specmap['hole_suffix']);feature=next(f for f in mate.LinkedObject.Group if f.TypeId=='PartDesign::Hole' and f.Name.endswith(suffix));profile=feature.Profile[0] if isinstance(feature.Profile,tuple) else feature.Profile
  assert feature.ModelThread and all(type(g).__name__=='Circle' for g in profile.Geometry)
  position=profile.Placement.inverse().multVec(mate.LinkPlacement.inverse().multVec(bolt.LinkPlacement.Base));assert min(math.hypot(position.x-g.Center.x,position.y-g.Center.y) for g in profile.Geometry)<1e-5
  basis=mate.LinkPlacement.Rotation.multiply(profile.Placement.Rotation);rr=basis.inverted().multiply(bolt.LinkPlacement.Rotation).toMatrix();orientation=tuple(round(getattr(rr,'A'+str(i)+str(j)),7) for i in range(1,4) for j in range(1,4))
  signature=('equal_circle_native_hole',geometry_digest(bolt.LinkedObject),geometry_digest(mate.LinkedObject),feature.Name,str(feature.ThreadSize),str(feature.ThreadClass),float(feature.ThreadDepth),round(position.z,6),orientation)
 if signature is not None and signature in restored_cache:
  intersection,reference=restored_cache[signature];r['rechecked_equal_nominal_pattern_reference']=reference
 else:
  local=bolt.LinkedObject.Shape.copy();local.Placement=mate.LinkPlacement.inverse().multiply(bolt.LinkPlacement);intersection=volume(local,mate.LinkedObject.Shape)
  if signature is not None:restored_cache[signature]=(intersection,bolt.Name)
 if intersection>threshold:raise RuntimeError(('D04 mating changed',r['bolt'],intersection))
 r.update(intersection_mm3=intersection,rechecked_after_restore=True);rows.append(r);print('Restored pair rechecked',r['bolt'],intersection,flush=True)
assert len(rows)==194
for pair in json.loads((O/'Neue_Gewindepaare.json').read_text()):
 bolt=doc.getObject(pair['bolt']);mate=doc.getObject(pair['mate']);suffix=re.sub(r'[^A-Za-z0-9_]','_',pair['hole_suffix']);hole=next(f for f in mate.LinkedObject.Group if f.TypeId=='PartDesign::Hole' and f.Name.endswith(suffix));profile=hole.Profile[0] if isinstance(hole.Profile,tuple) else hole.Profile;base=mate.LinkPlacement.Rotation.multiply(profile.Placement.Rotation);assert base.multVec(A.Vector(0,0,1)).dot(axis(bolt))>.99999
 local=profile.Placement.inverse().multVec(mate.LinkPlacement.inverse().multVec(bolt.LinkPlacement.Base));delta=bolt.LinkPlacement.Rotation.multiply(base.inverted());seed=math.degrees(delta.Angle)*(1 if delta.Axis.dot(axis(bolt))>=0 else -1)%360;r=tune(bolt,mate,('CarrierM6',float(hole.ThreadDepth),round(local.z,6)),seed=seed,reference_base=base);r['family']='D05 carrier-to-bulkhead M6';rows.append(r);print('Carrier thread',bolt.Name,r['passed'],r['intersection_mm3'],flush=True)
assert len(rows)==202 and all(r['passed'] for r in rows)
for r in bom:
 obj=doc.getObject(r['instance']);r['placement_mm']=list(obj.LinkPlacement.Base);r['placement_quaternion']=list(obj.LinkPlacement.Rotation.Q)
doc.recompute();doc.saveAs(str(native));digest=hashlib.sha256(native.read_bytes()).hexdigest();(O/'Instanzen.json').write_text(json.dumps(bom,indent=2,ensure_ascii=False));(O/'Gewindepruefung.json').write_text(json.dumps(dict(native_sha256=digest,passed=True,pairs=rows,scope='194 inherited nominal pairs (exact master/pose hashes or actual check with equal-circle native-hole references),8 new carrier-to-bulkhead pairs. Motor internal threads/depths are NOT verified; legacy motor reference is not OEM thread geometry.'),indent=2));r=json.loads((O/'Status.json').read_text());r.update(native_sha256=digest,thread_pairs_checked=202,thread_geometry_pass=True);(O/'Status.json').write_text(json.dumps(r,indent=2,ensure_ascii=False));print('D05 carrier/structure thread checks passed202',flush=True)
