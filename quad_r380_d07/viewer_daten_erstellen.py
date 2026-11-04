import json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';data=json.loads((O/'mesh_geometrie.json').read_text());proof=json.loads((O/'Bauraum_Pruefung.json').read_text());sha=hashlib.sha256((O/'QuadR380_D07_V3.FCStd').read_bytes()).hexdigest();assert data['report']['native_sha256']==proof['native_sha256']==sha
data['rotor_checks']=dict(actual_blade_collision_witnesses=[w for w in proof['existing_D06_rotor_witnesses'] if w['still_present']],actual_blade_collision_count=proof['existing_D06_rotor_collisions_still_present']);data['V3_clearance']=proof
(O/'mesh.js').write_text('globalThis.QD_MODEL='+json.dumps(data,separators=(',',':'),ensure_ascii=False)+';\n');print('V3 viewer data joined')
