"""Hash all review artifacts and archive reproducible project dependencies."""
from pathlib import Path
import json,hashlib,zipfile
H=Path(__file__).resolve().parent;R=H.parent
deps=['kreis_r04/mn1330_p14/geometrie.py','kreis_r04/mn1330_p14/gelenke.py','kreis_r04/mn1330_p14/kinematik.py','kreis_r04/mn1330_p14/parameter.json','kreis_r04/mn1330_p14/p14_physik.js','kreis_r04/mn1330_p14/Motor_Daten.json','kreis_r04/mn1330_p14/MOTOR_DATEN.md','kreis_r04/mn1330_p14/Ausgabe/Massenvarianten.json','kreis_r04/simulation/r04_physik.js','studie_antrieb/simulieren.cjs']
files=[p for p in H.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.FCStd1','.FCBak'] and p.name not in ['Manifest_SHA256.json','Entwicklung_AB.zip']]+[R/d for d in deps]
manifest={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(H/'Manifest_SHA256.json').write_text(json.dumps(manifest,indent=2))
with zipfile.ZipFile(H/'Entwicklung_AB.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in files+[H/'Manifest_SHA256.json']:z.write(p,str(p.relative_to(R)))
print(len(files),'files; ZIP',round((H/'Entwicklung_AB.zip').stat().st_size/1024**2,1),'MiB')
