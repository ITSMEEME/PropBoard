"""Combine the four nonoverlapping D12_GROUP geometry runs; reject incomplete evidence."""
from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent/'Ausgabe'
parts=[json.loads((O/f'Reglerhalter_Pruefung_{i}.json').read_text()) for i in range(4)]
sha=hashlib.sha256((O/'Quad_Reglerhalter_Landefuesse.FCStd').read_bytes()).hexdigest()
assert all(p['native_sha256']==sha for p in parts)
checks=sum([p['switch_checks'] for p in parts],[])
assert len(checks)==50 and len({(c['propeller_index'],c['variant']) for c in checks})==50
assert all(c['passed'] for c in checks)
result=parts[0].copy()
result['switch_checks']=sorted(checks,key=lambda c:(c['propeller_index'],c['variant']))
result['findings']=sum([p['findings'] for p in parts],[])
result['nominal_clear']=not result['findings']
result['candidates']=sum(p['candidates'] for p in parts)
result['new_parts_rotor_Z_gap_mm']=min(p['new_parts_rotor_Z_gap_mm'] for p in parts)
(O/'Reglerhalter_Pruefung.json').write_text(json.dumps(result,indent=2))
assert result['nominal_clear'],result['findings']
print('All50 geometry states verified',result['new_parts_rotor_Z_gap_mm'])
