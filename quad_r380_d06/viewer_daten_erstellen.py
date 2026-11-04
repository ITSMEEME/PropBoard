"""Join independently derived CAD surfaces with the hash-matched rotor report."""
import json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';data=json.loads((O/'mesh_geometrie.json').read_text());proof=json.loads((O/'Rotor_Pruefung.json').read_text());sha=hashlib.sha256((O/'QuadR380_D06_Propeller.FCStd').read_bytes()).hexdigest()
assert data['report']['native_sha256']==proof['native_sha256']==sha
data['rotor_checks']=proof;(O/'mesh.js').write_text('globalThis.QD_MODEL='+json.dumps(data,separators=(',',':'),ensure_ascii=False)+';\n');print('D06 viewer payload joined')
