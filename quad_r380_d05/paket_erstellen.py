from pathlib import Path
import hashlib,zipfile
H=Path(__file__).resolve().parent;files={}
for p in H.rglob('*'):
 if not p.is_file() or '__pycache__' in p.parts or p.suffix in ['.FCBak','.FCStd1','.zip'] or p.name in ['D05_Teile_Zwischenstand.FCStd','Gewindereferenzen_Zwischenstand.json','SHA256SUMS.txt']:continue
 files[str(p.relative_to(H.parent))]=p
for folder in ['quad_r380_d01/Quellen/Normteile','quad_r380_d02/Quellen/Normteile','quad_r380_d03/Quellen/Normteile','quad_r380_d04/Quellen/Normteile']:
 for p in (H.parent/folder).iterdir():
  if p.is_file():files[str(p.relative_to(H.parent))]=p
for rel in ['quad_r380_d04/Ausgabe/QuadR380_D04_CFK.FCStd','quad_r380_d04/Ausgabe/Bauteile.json','quad_r380_d04/Ausgabe/Instanzen.json','quad_r380_d04/Ausgabe/Gewindepruefung.json','quad_r380_d04/Ausgabe/Neue_Gewindepaare.json','quad_r380_d03/Ausgabe/Neue_Gewindepaare.json','quad_r380_d01/Ausgabe/Antriebsanforderungen.json']:
 files[rel]=H.parent/rel
manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+n+'\n' for n,p in sorted(files.items()));(H/'SHA256SUMS.txt').write_text(manifest)
with zipfile.ZipFile(H/'QuadR380_D05_Detailpaket.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name,p in sorted(files.items()):z.write(p,name)
 z.writestr('SHA256SUMS.txt',manifest)
with zipfile.ZipFile(H/'QuadR380_D05_Detailpaket.zip') as z:assert z.testzip() is None
print('D05 package verified',len(files),'files')
