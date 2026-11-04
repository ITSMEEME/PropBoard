"""Compare independently rebuilt D06 with all poses including root thread phase."""
import json,hashlib,collections
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';F=Path('/tmp/quad-d06-fresh-check');load=lambda p:json.loads(p.read_text());a=load(O/'Instanzen.json');b=load(F/'Instanzen.json');sa=load(O/'Bauteile.json');sb=load(F/'Bauteile.json')
def token(r):
    # q and -q are the same orientation. Rebuild is deterministic; canonicalize.
    q=r['placement_quaternion'];q=[x*(1 if q[3]>=0 else -1) for x in q]
    return r['instance'],r['id'],tuple(round(x,7) for x in r['placement_mm']),tuple(round(x,7) for x in q),r.get('rotor_id'),r.get('foot_side')
assert collections.Counter(map(token,a))==collections.Counter(map(token,b));assert set(sa)==set(sb)
deltas={k:abs(sa[k]['mass_kg']-sb[k]['mass_kg']) for k in sa};assert max(deltas.values())<1e-7
ma=sum(r['mass_kg'] for r in a);mb=sum(r['mass_kg'] for r in b);assert abs(ma-mb)<1e-7
native=O/'QuadR380_D06_Propeller.FCStd';status=load(O/'Status.json')
assert status['source_script_sha256']==hashlib.sha256((H/'propeller_einbauen.py').read_bytes()).hexdigest()
assert status['geometry_script_sha256']==hashlib.sha256((H/'geometrie.py').read_bytes()).hexdigest()
report=dict(passed=True,native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),instances=len(a),part_types=len(sa),all_positions_and_quaternions_match=True,root_screw_phases_included=True,mass_delivered_kg=ma,mass_rebuilt_kg=mb,total_mass_delta_kg=abs(ma-mb),maximum_prototype_mass_delta_kg=max(deltas.values()),source_script_sha256=status['source_script_sha256'],geometry_script_sha256=status['geometry_script_sha256'])
(O/'Neuaufbau_Pruefung.json').write_text(json.dumps(report,indent=2));print('D06 independent rebuild verified',len(a),ma)
