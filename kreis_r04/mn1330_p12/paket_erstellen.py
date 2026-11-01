#!/usr/bin/env python3
"""Deliver only active part files; no stale aluminium pieces or FreeCAD backups."""
import csv,hashlib,json,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];O=H/'Ausgabe';DEST=R/'lieferung';DEST.mkdir(exist_ok=True)
files=set()
for p in H.iterdir():
    if p.is_file() and p.suffix in ['.py','.json','.md','.FCMacro','.sh']:files.add(p)
for p in O.iterdir():
    if p.is_file() and p.suffix in ['.FCStd','.step','.csv','.json','.png'] and p.name!='Ansichten_Mesh.json':files.add(p)
parts=json.loads((O/'Teile.json').read_text())
for part in parts:
    for folder,ext in [('STEP','.step'),('STL','.stl'),('Referenz_STEP','.step')]:
        p=O/folder/(part['id']+ext)
        if p.exists():files.add(p)
with (O/'Stueckliste.csv').open(encoding='utf-8-sig',newline='') as f:
    for row in csv.DictReader(f,delimiter=';'):
        if row['manufacturing_step']:
            step=O/row['manufacturing_step'];assert step.exists();files.add(step)
            stl=O/'STL'/(step.stem+'.stl')
            if stl.exists():files.add(stl)
for name in ['P12_MN1330.FCStd','Parameter_Eingefroren.json','Pruefung.json']:
    p=H/'Varianten/Aluminium'/name
    if p.exists():files.add(p)
archive=DEST/'PropBoard_P12_Parametrisch_CFK20.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    checks=[]
    for p in sorted(files):
        label='mn1330_p12/'+p.relative_to(H).as_posix();z.write(p,label);checks.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+label)
    z.writestr('SHA256SUMS','\n'.join(checks)+'\n')
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
archive.with_suffix('.zip.sha256').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
print(json.dumps({'archive':str(archive),'files':len(files),'bytes':archive.stat().st_size}))
