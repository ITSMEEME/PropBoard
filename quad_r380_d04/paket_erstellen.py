from pathlib import Path
import json,hashlib,zipfile,math
H=Path(__file__).resolve().parent;O=H/'Ausgabe';cuts=json.loads((O/'CFK_Zuschnitt.json').read_text());bins=[]
for c in sorted(cuts,key=lambda x:x['length_mm'],reverse=True):
 planned=math.ceil(c['length_mm']*10)/10;need=planned+2;target=next((b for b in bins if b['used_mm']+need<=990),None)
 if target is None:target=dict(used_mm=0,cuts=[]);bins.append(target)
 target['used_mm']+=need;target['cuts'].append(dict(instance=c['instance'],planned_mm=planned))
(O/'CFK_Beschaffung.json').write_text(json.dumps(dict(article='CBU20171005TG',stock_length_mm=1000,end_trim_each_mm=5,kerf_per_cut_mm=2,stock_count=len(bins),cut_count=len(cuts),algorithm='First fit decreasing, no optimality claim',bins=bins),indent=2))
files={}
for p in H.rglob('*'):
 if not p.is_file() or '__pycache__' in p.parts or p.suffix in ['.FCBak','.FCStd1','.zip'] or p.name in ['D04_Teile_Zwischenstand.FCStd','Gewindereferenzen_Zwischenstand.json','SHA256SUMS.txt']:continue
 files[str(p.relative_to(H.parent))]=p
for folder in ['quad_r380_d01/Quellen/Normteile','quad_r380_d02/Quellen/Normteile','quad_r380_d03/Quellen/Normteile']:
 for p in (H.parent/folder).iterdir():
  if p.is_file():files[str(p.relative_to(H.parent))]=p
for rel in ['quad_r380_d03/Ausgabe/QuadR380_D03_CFK.FCStd','quad_r380_d03/Ausgabe/Bauteile.json','quad_r380_d03/Ausgabe/Instanzen.json','quad_r380_d03/Ausgabe/Gewindepruefung.json','quad_r380_d02/KENNDATEN_BEWERTUNG.md','quad_r380_d02/HERSTELLERDATEN.md','quad_r380_d02/Quellen/Beschaffungsagent/kenndaten.md','quad_r380_d02/Quellen/Beschaffungsagent/Provenienz.json']:
 files[rel]=H.parent/rel
for n in ['CFK-KLEMM-A.step','CFK-KLEMM-B.step','CFK-ZWISCHENLAGE.step']:
 p=H.parent/'kreis_r04/mn1330_p12/Ausgabe/STEP'/n;files[str(p.relative_to(H.parent))]=p
manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+n+'\n' for n,p in sorted(files.items()));(H/'SHA256SUMS.txt').write_text(manifest)
with zipfile.ZipFile(H/'QuadR380_D04_Detailpaket.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name,p in sorted(files.items()):z.write(p,name)
 z.writestr('SHA256SUMS.txt',manifest)
with zipfile.ZipFile(H/'QuadR380_D04_Detailpaket.zip') as z:assert z.testzip() is None
print('D04 package verified',len(files),'files;',len(cuts),'cuts;',len(bins),'stocks')
