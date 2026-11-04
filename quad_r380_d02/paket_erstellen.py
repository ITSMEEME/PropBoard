from pathlib import Path
import zipfile,hashlib,json,math
H=Path(__file__).resolve().parent
cuts=json.loads((H/'Ausgabe/CFK_Zuschnitt.json').read_text());bins=[]
for c in sorted(cuts,key=lambda r:r['length_mm'],reverse=True):
 planned=math.ceil(c['length_mm']*10)/10;need=planned+2
 target=next((b for b in bins if b['used_mm']+need<=990),None)
 if target is None:target=dict(used_mm=0,cuts=[]);bins.append(target)
 target['used_mm']+=need;target['cuts'].append(dict(id=c['id'],planned_mm=planned))
(H/'Ausgabe/CFK_Beschaffung.json').write_text(json.dumps(dict(stock_article='CBU20171005TG',stock_mm=1000,end_trim_each_mm=5,kerf_per_cut_mm=2,algorithm='first fit decreasing, no global minimum claim',stock_count=len(bins),cut_count=len(cuts),bins=bins),indent=2))
files={}
for p in H.rglob('*'):
 if not p.is_file() or '__pycache__' in p.parts or p.suffix in ['.FCBak','.FCStd1','.zip'] or p.name in ['D02_Teile_Zwischenstand.FCStd','SHA256SUMS.txt']:continue
 files['quad_r380_d02/'+str(p.relative_to(H))]=p
for p in (H.parent/'quad_r380_d01/Quellen/Normteile').iterdir():
 if p.is_file():files[str(p.relative_to(H.parent))]=p
for n in ['CFK-KLEMM-A.step','CFK-KLEMM-B.step','CFK-ZWISCHENLAGE.step']:
 p=H.parent/'kreis_r04/mn1330_p12/Ausgabe/STEP'/n;files[str(p.relative_to(H.parent))]=p
manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+n+'\n' for n,p in sorted(files.items()));(H/'SHA256SUMS.txt').write_text(manifest)
with zipfile.ZipFile(H/'QuadR380_D02_Detailpaket.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for n,p in sorted(files.items()):z.write(p,n)
 z.writestr('SHA256SUMS.txt',manifest)
with zipfile.ZipFile(H/'QuadR380_D02_Detailpaket.zip') as z:assert z.testzip() is None
print(len(files),'files verified; CFK stock count',len(bins))
