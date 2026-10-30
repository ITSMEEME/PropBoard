#!/usr/bin/env python3
"""Self-contained P08 viewing/motion package; generators need full checkout."""
from pathlib import Path
import json,hashlib,zipfile
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
b=json.loads((H/'Ausgabe/Aufbaupruefung_P08.json').read_text());v=json.loads((H/'Ausgabe/Bewegungspruefung_P08.json').read_text())
assert b['native_reopen_pass'] and b['new_linkage_objects']==90 and b['new_parts_valid']
assert not b['full_manufacturing_release'] and not v['manufacturing_release']
assert v['neutral_return_pass'] and v['max_closure_error_mm']<1e-6 and not v['collisions']
for name,key in [('P08_Baugruppe_Servoverbindung_ENTWURF.FCStd','full_native_sha256'),('P08_Isolierte_Anschlussbewegung.FCStd','isolated_native_sha256')]:
 assert hashlib.sha256((H/'Ausgabe'/name).read_bytes()).hexdigest()==b[key]
files=[p for p in H.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.FCBak','.pyc')]
files += [H.parent/'bewegung/bewegung_runtime.py',H.parent/'simulation/kinematik.json',H.parent/'fertigung_p07/Quellen/SB-2270SGP.STEP',H.parent/'fertigung_p07/Ausgabe/Importpruefung_P07.json']
entries={str(p.relative_to(H.parent)):p.read_bytes() for p in files}
entries['README.md']=('P08 mechanische Servoverbindung – detaillierter Entwurf, keine Fertigungsfreigabe.\n\nNative Baugruppen und STEP unter fertigung_p08/Ausgabe.\nFuer die isolierte Bewegung fertigung_p08/P08_Bewegung_oeffnen.FCMacro mit FreeCAD1.0.2 ausfuehren.\nOrdnerstruktur erhalten: bewegung und simulation enthalten die Kinematik-Abhaengigkeiten.\n\nDie kompletten CAD-Generatoren und vorherigen Baugruppen zur Regeneration befinden sich im Repository ITSMEEME/PropBoard.\nServo-Originalimport geometrisch ungueltig; lokale Abtriebsableitung separat gueltig. Alle offenen Punkte stehen in fertigung_p08/README.md und Anschlussdaten.json.\n').encode()
entries['SHA256SUMS']=''.join(hashlib.sha256(value).hexdigest()+'  '+name+'\n' for name,value in sorted(entries.items())).encode()
z=H.parent/'Cohexial_P08_Mechanische_Servoverbindung.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as out:
 for name,value in sorted(entries.items()):out.writestr(name,value)
with zipfile.ZipFile(z) as out:
 assert out.testzip() is None
 for name,value in entries.items():assert hashlib.sha256(out.read(name)).digest()==hashlib.sha256(value).digest()
print(z.name,len(entries),'files',round(z.stat().st_size/2**20,2),'MiB; hashes PASS')
