#!/usr/bin/env python3
"""Package only the completed, validated F01 deliverables, keeping macro paths."""
from pathlib import Path
import hashlib
import json
import zipfile

HERE=Path(__file__).resolve().parent
OUT=HERE/'Fertigung'
validation=json.loads((OUT/'Validierung.json').read_text())
assert len(validation['individual_parts'])==13
assembly=validation['assembly']
assert assembly['sampled_checks_passed'] and assembly['guide_pin_checks_passed']
assert not any(assembly[k] for k in ('additional_cap_plate_collisions','additional_cap_tube_collisions','interlevel_collisions'))
assert (OUT/'Fertigungszeichnungen_F01.pdf').is_file()
archive=OUT/'Cohexial_Study_R04_Taumel_F01.zip'
outfiles=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS'
                and p.suffix not in ('.FCBak','.FCStd1','.zip'))
(OUT/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(OUT))+'\n' for p in outfiles))
paths=sorted(p for p in HERE.rglob('*') if p.is_file()
             and p.suffix not in ('.FCBak','.FCStd1','.pyc','.zip')
             and '__pycache__' not in p.parts)
manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(HERE))+'\n' for p in paths)
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in paths:z.write(p,'Cohexial_Study_R04_Taumel_F01/'+str(p.relative_to(HERE)))
    z.writestr('Cohexial_Study_R04_Taumel_F01/SHA256SUMS_Gesamt',manifest)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
print(archive)
print('Files:',len(paths)+1,'bytes:',archive.stat().st_size)
print('SHA256:',hashlib.sha256(archive.read_bytes()).hexdigest())
