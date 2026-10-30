#!/usr/bin/env python3
"""Build a self-contained offline simulator + native CAD review package."""
import hashlib,json,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1];Z=H/'H01_Flugsimulation.zip'
report=json.loads((H/'Ergebnisse/Testbericht.json').read_text());checks=json.loads((H/'Ergebnisse/Physikpruefung.json').read_text());robust=json.loads((H/'Ergebnisse/Robustheit.json').read_text())
assert len(report['results'])==19 and len(robust['results'])==12
assert len(checks['results'])==10 and all(x['status']=='PASS' for x in checks['results'])
assert report['status']=='UNVALIDATED_MODEL_TESTS_NOT_FLIGHT_CLEARANCE'
assert json.loads((H/'Ergebnisse/Browserpruefung.json').read_text())['status']=='PASS'
model=json.loads((H/'modell_h01.json').read_text());native=H.parent/'halterungen/Ausgabe/R04_Taumelmodell_Halterungen_H01.FCStd'
assert hashlib.sha256(native.read_bytes()).hexdigest()==model['source_sha256']
files=[p for p in H.rglob('*') if p.is_file() and p.suffix not in ('.zip','.pyc') and '__pycache__' not in p.parts]
files += [H.parent/'bewegung/Ausgabe/Cohexial_R04_M01_Bewegung.FCStd',H.parent/'bewegung/bewegung_runtime.py',H.parent/'bewegung/servo_geometrie.py',H.parent/'bewegung/Bewegung_oeffnen.FCMacro',H.parent/'bewegung/README.md',H.parent/'messdaten/Servodaten_Nutzer.json',H.parent/'aerodynamik/polar_lookup.js',H.parent/'aerodynamik/Ausgabe/Polaren.json',H.parent/'aerodynamik/Ausgabe/Polaren.js',ROOT/'kreis_r04/simulation/r04_physik.js',ROOT/'modell_r04/auslegung/antrieb.js',native,H.parent/'halterungen/halterungen_features.py',H.parent/'halterungen/parameter.json',H.parent/'cad/parameter.json',H.parent/'mechanik/pruefen.py',H.parent/'mechanik/Fluegel_Traegheit.json',H.parent/'mechanik/README.md']
prefix='PropBoard_H01_Flug/'
entries={prefix+str(p.relative_to(ROOT)):p.read_bytes() for p in files}
entries[prefix+'README.md']=('''# Cohexial Study H01 – Offline-Flugsimulation

Öffne `modell_r04_taumel/simulation/H01_Flugsimulator.html` im Browser.
Der `Flugbericht.pdf` und die README stehen daneben.

Das tatsächliche native FreeCAD-Modell liegt unter
`modell_r04_taumel/halterungen/Ausgabe/R04_Taumelmodell_Halterungen_H01.FCStd`.
Das zusätzliche bewegliche M01-Modell liegt unter `modell_r04_taumel/bewegung/`;
zum Bewegen `Bewegung_oeffnen.FCMacro` in FreeCAD starten. Savöx-Hüllen/-Daten stammen aus Nutzerangaben.
Masse, Schwerpunkt, Tensor und Sichtgeometrie des Grundmodells wurden aus H01 importiert;
das SHA256 der nativen Quelle steht in `simulation/modell_h01.json`.

Node ohne weitere Pakete:
- `node modell_r04_taumel/simulation/testflug.js`
- `node modell_r04_taumel/simulation/pruefen.js`
- `node modell_r04_taumel/simulation/robustheit.js`

Browser mit gesperrtem file://: im entpackten Ordner
`python -m http.server 8000 --bind 127.0.0.1`, danach die HTML-Seite über localhost öffnen.
Die Zeichnungen und vollständigen CAD-Generatoren sind im separaten H01-Fertigungspaket
oder im Repository ITSMEEME/PropBoard. Weiterführende Repository-Links können hier fehlen.

Unvalidierte Modellversuche, keine Flugfreigabe. Servo-/Reibungsdaten sind Annahmen.
PID-Werte nicht ungeprüft auf reale Hardware übertragen.
''').encode()
manifest=''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n' for name,data in sorted(entries.items()))
entries[prefix+'SHA256SUMS']=manifest.encode()
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for name,data in sorted(entries.items()):z.writestr(name,data)
with zipfile.ZipFile(Z) as z:
    assert z.testzip() is None
    for name,data in entries.items():assert hashlib.sha256(z.read(name)).digest()==hashlib.sha256(data).digest()
print(Z.name,len(entries),'files',round(Z.stat().st_size/2**20,2),'MiB',hashlib.sha256(Z.read_bytes()).hexdigest())
