"""Package only current delivery files, with a SHA256 manifest."""
from pathlib import Path
import hashlib,zipfile
H=Path(__file__).resolve().parent
skip={'D01_Teile_Zwischenstand.FCStd','Gewinde_Wiederverwendung.json'}
files=sorted(p for p in H.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in skip and p.suffix not in ['.FCBak','.FCStd1','.zip'] and p.name!='SHA256SUMS.txt')
manifest=H/'SHA256SUMS.txt';manifest.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(H))+'\n' for p in files))
with zipfile.ZipFile(H/'QuadR380_D01_Detailpaket.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in [*files,manifest]:z.write(p,'quad_r380_d01/'+str(p.relative_to(H)))
with zipfile.ZipFile(H/'QuadR380_D01_Detailpaket.zip') as z:assert z.testzip() is None
print('Verified package:',len(files)+1,'files')
