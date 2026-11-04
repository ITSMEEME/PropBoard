"""Self-contained review archive, including immutable D05 input and provenance."""
from pathlib import Path
import hashlib,zipfile,json
H=Path(__file__).resolve().parent;ROOT=H.parent;files={}
for p in H.rglob('*'):
    if not p.is_file() or '__pycache__' in p.parts or p.suffix in ['.FCBak','.FCStd1','.zip'] or p.name=='SHA256SUMS.txt':continue
    files[str(p.relative_to(ROOT))]=p
for folder in ['quad_r380_d01/Quellen/Normteile','quad_r380_d02/Quellen/Normteile','quad_r380_d03/Quellen/Normteile','quad_r380_d04/Quellen/Normteile','quad_r380_d05/Quellen']:
    for p in (ROOT/folder).rglob('*'):
        if p.is_file():files[str(p.relative_to(ROOT))]=p
for name in ['QuadR380_D05_MN1330.FCStd','Instanzen.json','Bauteile.json','Status.json','Gewindepruefung.json','Bauraum_Pruefung.json','Motor_Montage_Pruefung.json','Motor_Schnittstellen.json','Motor_Quellenbezug.json','MN1330_Betriebsgrenzen.json']:
    p=ROOT/'quad_r380_d05/Ausgabe'/name;files[str(p.relative_to(ROOT))]=p
for name in ['README.md','normteile_erstellen.py','Elektrische_Integration.json']:
    p=ROOT/'quad_r380_d05'/name;files[str(p.relative_to(ROOT))]=p
manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+n+'\n' for n,p in sorted(files.items()));(H/'SHA256SUMS.txt').write_text(manifest)
target=H/'QuadR380_D06_Detailpaket.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name,p in sorted(files.items()):z.write(p,name)
    z.writestr('SHA256SUMS.txt',manifest)
with zipfile.ZipFile(target) as z:assert z.testzip() is None
print('D06 package verified',len(files),'files',round(target.stat().st_size/1024**2,1),'MiB')
