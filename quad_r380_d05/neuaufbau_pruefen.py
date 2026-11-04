"""Compare an independently rebuilt geometry with the delivered model; screw phase is verified separately."""
from pathlib import Path
import json,hashlib,collections
H=Path(__file__).resolve().parent;O=H/'Ausgabe';F=Path('/tmp/quad-d05-fresh-check')
load=lambda p:json.loads(p.read_text());a=load(O/'Instanzen.json');b=load(F/'Instanzen.json');sa=load(O/'Bauteile.json');sb=load(F/'Bauteile.json')
def rotation(q):
 x,y,z,w=q
 return [1-2*(y*y+z*z),2*(x*y+z*w),2*(x*z-y*w),2*(x*y-z*w),1-2*(x*x+z*z),2*(y*z+x*w),2*(x*z+y*w),2*(y*z-x*w),1-2*(x*x+y*y)]
def token(r):
 rot=rotation(r['placement_quaternion']);orientation=[rot[6],rot[7],rot[8]] if r['id'].startswith('ISO') else rot
 return (r['id'],r['label'],tuple(round(x,6) for x in r['placement_mm']),tuple(round(x,6) for x in orientation),r.get('foot_side'))
assert len(a)==len(b)==856;assert collections.Counter(token(r) for r in a)==collections.Counter(token(r) for r in b)
assert set(sa)==set(sb);deltas={k:abs(sa[k]['mass_kg']-sb[k]['mass_kg']) for k in sa};assert max(deltas.values())<1e-6
ma=sum(r['mass_kg'] for r in a);mb=sum(r['mass_kg'] for r in b);assert abs(ma-mb)<1e-6
r=dict(passed=True,instances=len(a),part_types=len(sa),mass_delivered_kg=ma,mass_rebuilt_kg=mb,total_mass_delta_kg=abs(ma-mb),maximum_prototype_mass_delta_kg=max(deltas.values()),part_and_pose_multiset_match=True,scope='Independent source rebuild: part counts, prototype masses, all positions and non-ISO orientations. ISO axial orientations match; their screw phases are independently fitted in the thread proof.',source_script_sha256=hashlib.sha256((H/'motoren_einbauen.py').read_bytes()).hexdigest(),native_sha256=hashlib.sha256((O/'QuadR380_D05_MN1330.FCStd').read_bytes()).hexdigest());(O/'Neuaufbau_Pruefung.json').write_text(json.dumps(r,indent=2));print(r)
