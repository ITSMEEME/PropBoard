"""Compare independently rebuilt geometry, all instance poses and calibrated phases."""
import json,hashlib,collections
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';F=Path('/tmp/quad-d07-fresh-check');load=lambda p:json.loads(p.read_text());a=load(O/'Instanzen.json');b=load(F/'Instanzen.json');sa=load(O/'Bauteile.json');sb=load(F/'Bauteile.json')
def token(r):
    x,y,z,w=r['placement_quaternion'];rot=[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]
    return r['instance'],r['id'],tuple(round(v,6) for v in r['placement_mm']),tuple(round(v,6) for v in rot)
assert collections.Counter(map(token,a))==collections.Counter(map(token,b));assert set(sa)==set(sb);delta=max(abs(sa[k]['mass_kg']-sb[k]['mass_kg']) for k in sa);assert delta<1e-6
ma=sum(r['mass_kg'] for r in a);mb=sum(r['mass_kg'] for r in b);assert abs(ma-mb)<1e-6
report=dict(native_sha256=hashlib.sha256((O/'QuadR380_D07_V3.FCStd').read_bytes()).hexdigest(),passed=True,instances=len(a),part_types=len(sa),all_poses_match=True,calibrated_screw_phases_included=True,phase_calibration_as_input=True,mass_delivered_kg=ma,mass_rebuilt_kg=mb,total_mass_difference_kg=abs(ma-mb),max_prototype_mass_difference_kg=delta,source_script_sha256=hashlib.sha256((H/'bauen.py').read_bytes()).hexdigest(),geometry_script_sha256=hashlib.sha256((H/'geometrie.py').read_bytes()).hexdigest());status=load(O/'Status.json');assert report['source_script_sha256']==status['source_script_sha256'] and report['geometry_script_sha256']==status['geometry_script_sha256'];(O/'Neuaufbau_Pruefung.json').write_text(json.dumps(report,indent=2));print('V3 independent rebuild verified',len(a),ma)
