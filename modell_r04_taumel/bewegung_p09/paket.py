#!/usr/bin/env python3
"""Package independently viewable P09 native + browser animation with dependencies."""
from pathlib import Path
import json,hashlib,zipfile,py_compile
H=Path(__file__).resolve().parent;ROOT=H.parents[1];OUT=H/'Ausgabe'
a=json.loads((OUT/'Aufbaupruefung_P09.json').read_text());v=json.loads((OUT/'Bewegungspruefung_P09.json').read_text());b=json.loads((OUT/'Browserpruefung_P09.json').read_text());e=json.loads((OUT/'Browserexport_P09.json').read_text())
assert a['native_reopen_pass'] and not a['manufacturing_release']
assert not v['collisions'] and v['max_closure_error_mm']<1e-6 and v['max_actual_sphere_centre_error_mm']<1e-6
assert v['invalid_input_atomic_rejection'] and v['neutral_return_pass']
assert b['status']=='PASS'
native=OUT/'P09_Servo_bis_Rotorblatt_Bewegung.FCStd';html=OUT/'P09_Durchgaengige_Animation.html'
assert a['native_sha256']==v['native_sha256']==e['source_native_sha256']==hashlib.sha256(native.read_bytes()).hexdigest()
assert b['source_html_sha256']==e['html_sha256']==hashlib.sha256(html.read_bytes()).hexdigest()
for p in H.glob('*.py'):py_compile.compile(str(p),doraise=True)
compile((H/'P09_Bewegung_oeffnen.FCMacro').read_text(),str(H/'P09_Bewegung_oeffnen.FCMacro'),'exec')
files=[p for p in H.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.FCBak','.pyc')]
files += [H.parent/'fertigung_p08/runtime.py',H.parent/'fertigung_p08/geometrie.py',H.parent/'fertigung_p08/Anschlussdaten.json',H.parent/'bewegung/bewegung_runtime.py',H.parent/'bewegung/Bewegungsdaten.json',H.parent/'simulation/kinematik.json',H.parent/'fertigung_p07/Quellen/SB-2270SGP.STEP',H.parent/'fertigung_p07/Servowahl.json',H.parent/'fertigung_p07/Ausgabe/Importpruefung_P07.json']
entries={'PropBoard_P09/'+str(p.relative_to(ROOT)):p.read_bytes() for p in files}
entries['PropBoard_P09/README.md']=('''# P09 – gemeinsame Animation Servo bis Rotorblatt

Browser: modell_r04_taumel/bewegung_p09/Ausgabe/P09_Durchgaengige_Animation.html öffnen und Animation starten.
FreeCAD 1.0.2: modell_r04_taumel/bewegung_p09/P09_Bewegung_oeffnen.FCMacro ausführen.
Ordnerstruktur erhalten: runtime.py, bewegung_runtime.py und kinematik.json sind enthaltene Animationsabhängigkeiten.

Die native Baugruppe ist auch statisch direkt zu öffnen. Die README unter bewegung_p09 dokumentiert Konstruktion, Tests und offene Punkte.
Dies ist ein Bewegungs-/Konstruktionsentwurf, keine Fertigungs-/Flugfreigabe. Der vollständige Servo-STEP-Import ist weiterhin ungültig.
Für alle Fertigungsgeneratoren und Vorstufen ist der komplette Repository-Checkout ITSMEEME/PropBoard nötig.
''').encode()
entries['PropBoard_P09/SHA256SUMS']=''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n' for name,data in sorted(entries.items())).encode()
z=H.parent/'Cohexial_P09_Servo_bis_Rotorblatt_Animation.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as out:
 for name,data in sorted(entries.items()):out.writestr(name,data)
with zipfile.ZipFile(z) as out:
 assert out.testzip() is None
 for name,data in entries.items():assert hashlib.sha256(out.read(name)).digest()==hashlib.sha256(data).digest()
print(z.name,len(entries),'files',round(z.stat().st_size/2**20,2),'MiB; native/HTML/dependency hashes PASS')
