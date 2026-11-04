from pathlib import Path
import hashlib,zipfile
H=Path(__file__).resolve().parent;files={}
for p in H.rglob('*'):
 if not p.is_file() or '__pycache__' in p.parts or p.suffix in ['.FCBak','.FCStd1','.zip'] or p.name in ['D03_Teile_Zwischenstand.FCStd','Gewindepruefung_vor_Senkkopf.json','Gewindereferenzen_Zwischenstand.json','SHA256SUMS.txt']:continue
 files[str(p.relative_to(H.parent))]=p
for folder in ['quad_r380_d01/Quellen/Normteile','quad_r380_d02/Quellen/Normteile']:
 for p in (H.parent/folder).iterdir():
  if p.is_file():files[str(p.relative_to(H.parent))]=p
for rel in ['quad_r380_d02/Ausgabe/QuadR380_D02_CFK.FCStd','quad_r380_d02/Ausgabe/Bauteile.json','quad_r380_d02/Ausgabe/Instanzen.json','quad_r380_d02/Ausgabe/CFK_Zuschnitt.json','quad_r380_d02/Ausgabe/Quellteile.json','quad_r380_d02/KENNDATEN_BEWERTUNG.md','quad_r380_d02/HERSTELLERDATEN.md','quad_r380_d02/Quellen/Beschaffungsagent/kenndaten.md','quad_r380_d02/Quellen/Beschaffungsagent/Provenienz.json']:
 p=H.parent/rel;files[rel]=p
for n in ['CFK-KLEMM-A.step','CFK-KLEMM-B.step','CFK-ZWISCHENLAGE.step']:
 p=H.parent/'kreis_r04/mn1330_p12/Ausgabe/STEP'/n;files[str(p.relative_to(H.parent))]=p
manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+n+'\n' for n,p in sorted(files.items()));(H/'SHA256SUMS.txt').write_text(manifest)
with zipfile.ZipFile(H/'QuadR380_D03_Detailpaket.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for n,p in sorted(files.items()):z.write(p,n)
 z.writestr('SHA256SUMS.txt',manifest)
with zipfile.ZipFile(H/'QuadR380_D03_Detailpaket.zip') as z:assert z.testzip() is None
print('D03 package verified',len(files),'files')
