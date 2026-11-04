from pathlib import Path
import json,csv,math,hashlib,zipfile
H=Path(__file__).resolve().parent;R=H.parent;O=H/'Ausgabe';read=lambda n:json.loads((O/n).read_text());status=read('Status.json');viewer=read('Viewer_Pruefung.json');assert status['native_switches_passed'] and status['nominal_rotor_space_clear'] and status['integration_passed'] and viewer['passed'];assert viewer['native_sha256']==status['native_sha256'];common=read('Gemeinsame_Instanzen.json');variable=read('Instanzen.json')+read('Hardware.json')+read('Groessen_Instanzen.json')+read('Kabel_Instanzen.json');checks=read('Umschalter_Pruefung.json')['checks'];spec=json.loads((R/'motoranschluss_varianten/Varianten.json').read_text())[:4];bom=[];cutlist=[]
for c in checks:
 pidx=c['propeller_index'];v=c['variant'];active=common+[r for r in variable if r['propeller_index']==pidx and r.get('variant',v)==v and r.get('group')!='Rotorhuelle'];groups={}
 for r in active:
  key=r.get('id') or v+'_'+r['part'];g=groups.setdefault(key,dict(propeller=c['propeller'],variant=v,part=key,count=0,mass_kg=0));g['count']+=1;g['mass_kg']+=r['mass_kg']
 assert abs(sum(g['mass_kg'] for g in groups.values())-c['mass_modeled_excluding_propellers_kg'])<1e-7;bom+=list(groups.values())
 vs=next(x for x in spec if x['id']==v);section=math.pi/4*(vs['od']**2-vs['di']**2)
 for r in active:
  if r.get('part','').startswith('Tube'):
   length=r['mass_kg']/(1600e-9*section);assert 70<length<=1000;cutlist.append(dict(propeller=c['propeller'],variant=v,instance=r['instance'],tube=r['part'],outer_diameter_mm=vs['od'],inner_diameter_mm=vs['di'],cut_length_mm=length,stock_length_mm=1000,grip_each_end_mm=35))
for filename,rows in [('Stueckliste_40_Konfigurationen.csv',bom),('CFK_Zuschnitt_40_Konfigurationen.csv',cutlist)]:
 with (O/filename).open('w') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
inputs=['quad_r380_d08/Ausgabe/Quad_Parametrisch_V1_V4.FCStd','quad_r380_d08/Ausgabe/Gemeinsame_Instanzen.json','quad_r380_d08/Ausgabe/Instanzen.json','quad_r380_d08/Ausgabe/Hardware.json','quad_r380_d07/Ausgabe/QuadR380_D07_V3.FCStd','quad_r380_d07/parameter.json','quad_r380_d07/geometrie.py','motoranschluss_varianten/Varianten.json','quad_r380_d06/Ausgabe/mesh_geometrie.json','quad_r380_d08/Quellen/Normteile/LICENSE-FastenersWB','quad_r380_d08/Quellen/Normteile/Quellenmanifest.json','quad_r380_d08/Ausgabe/Antriebsnachweis.json','quad_r380_varianten/DATENNACHTRAG.md']
files=[R/n for n in inputs]+list((R/'quad_r380_varianten/Quellen/Nutzer_Nachtrag').glob('*'))
for p in H.rglob('*'):
 if not p.is_file() or any(x in p.parts for x in ['Cache','__pycache__']):continue
 if p.suffix in ['.FCBak','.zip','.log'] or p.name.startswith(('debug_','Failed_','Debug_')) or p.name=='SHA256SUMS.txt':continue
 files.append(p)
files=sorted(set(files));manifest=H/'SHA256SUMS.txt';manifest.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(R))+'\n' for p in files));archive=H/'Quad_HEPS_10_Groessen_V1_V4.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4) as z:
 for p in files+[manifest]:z.write(p,p.relative_to(R))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print('Delivery verified',archive.stat().st_size,'bytes',len(files)+1,'files',flush=True)
