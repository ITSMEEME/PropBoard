"""Create per-configuration BOMs and a reproducible CAD review package."""
from pathlib import Path
import json,csv,hashlib,zipfile
H=Path(__file__).resolve().parent;R=H.parent;O=H/'Ausgabe'
read=lambda n:json.loads((O/n).read_text())
proof=read('Varianten_Pruefung.json');qa=read('Freiraum_Pruefung.json')
sha=hashlib.sha256((O/'Quad_Parametrisch_V1_V4.FCStd').read_bytes()).hexdigest()
assert sha==proof['native_sha256']==qa['native_sha256']
assert all(v['all_four_arms_passed'] and v['all_new_parts_clear_of_rotor_and_foot_in_Z'] for v in qa['variants'])
common=read('Gemeinsame_Instanzen.json');variable=read('Instanzen.json')+read('Hardware.json')
for check in proof['switch_checks']:
 v=check['variant'];groups={}
 for r in common+[r for r in variable if r['variant']==v]:
  key=r.get('id') or v+'_'+r['part'];g=groups.setdefault(key,dict(part=key,count=0,mass_kg=0));g['count']+=1;g['mass_kg']+=r['mass_kg']
 assert abs(sum(g['mass_kg'] for g in groups.values())-check['mass_modeled_kg'])<1e-7
 with (O/('Stueckliste_'+v+'.csv')).open('w') as f:
  w=csv.DictWriter(f,fieldnames=['part','count','mass_kg']);w.writeheader();w.writerows(groups.values())
inputs=['quad_r380_d06/Ausgabe/QuadR380_D06_Propeller.FCStd','quad_r380_d06/Ausgabe/Instanzen.json','quad_r380_d06/Ausgabe/mesh_geometrie.json','quad_r380_d06/Ausgabe/Rotor_Pruefung.json','quad_r380_d07/Ausgabe/QuadR380_D07_V3.FCStd','quad_r380_d07/parameter.json','quad_r380_d07/geometrie.py','motoranschluss_varianten/Varianten.json','quad_r380_d01/Quellen/Normteile/ISO7089_M4.brep','quad_r380_d05/normteile_erstellen.py']
files=[R/n for n in inputs]
for p in H.rglob('*'):
 if not p.is_file() or any(x in p.parts for x in ['__pycache__','.git']):continue
 if p.suffix in ['.zip','.FCBak','.log'] or p.name in ['erzeugen.py','SHA256SUMS.txt']:continue
 files.append(p)
files=sorted(set(files))
manifest=H/'SHA256SUMS.txt';manifest.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(R))+'\n' for p in files))
archive=H/'Quad_Parametrisch_V1_V4_Paket.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 for p in files+[manifest]:z.write(p,p.relative_to(R))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print('Package verified:',archive,archive.stat().st_size,'bytes',len(files)+1,'files',flush=True)
