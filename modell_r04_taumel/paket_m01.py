#!/usr/bin/env python3
"""Self-contained M01 review package, with motion model, offline flight UI and provenance."""
import hashlib,json,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent;Z=H/'Cohexial_M01_Bewegung_und_Daten.zip'
load=lambda p:json.loads((H/p).read_text())
v=load('bewegung/Ausgabe/Validierung_M01.json');native=H/'bewegung/Ausgabe/Cohexial_R04_M01_Bewegung.FCStd';sha=hashlib.sha256(native.read_bytes()).hexdigest();assert v['native_sha256']==sha and v['native_reopen_pass'] and not v['collisions']
assert load('bewegung/Ausgabe/GUI_Pruefung.json')['status']=='PASS'
assert load('simulation/servo_profiles.json')['Savox_SB2271SG_USER']['m01_geometry_sha256']==sha
assert len(load('simulation/Ergebnisse/Testbericht.json')['results'])==19
assert len(load('simulation/Ergebnisse/Physikpruefung.json')['results'])==10
assert load('simulation/Ergebnisse/Browserpruefung.json')['status']=='PASS'
assert load('messdaten/Identifikation_Pruefung.json')['status']=='SYNTHETIC_TESTS_ONLY_NO_REAL_MEASUREMENTS'
assert load('aerodynamik/Ausgabe/Polaren.json')['status']=='COMPUTED_XFOIL_POLARS_NOT_MEASURED_OR_FULL_ROTOR_CFD'
files=[]
for folder in ('bewegung','messdaten','aerodynamik','simulation'):
    for p in (H/folder).rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix.lower() not in ('.pyc','.zip','.fcbak','.gz'):files.append(p)
files += [H/'Datenbericht_M01.pdf',H/'m01_bericht.py',H/'paket_m01.py',H/'README.md',H/'cad/erstellen.py',H/'cad/parameter.json',H/'halterungen/halterungen_features.py',H/'halterungen/parameter.json',H/'halterungen/Ausgabe/R04_Taumelmodell_Halterungen_H01.FCStd',H/'halterungen/Ausgabe/Geometriepruefung_H01.json',H/'mechanik/pruefen.py',H/'mechanik/Fluegel_Traegheit.json',H/'mechanik/README.md',ROOT/'kreis_r04/simulation/r04_physik.js',ROOT/'kreis_r04/simulation/pruefen.js',ROOT/'kreis_r04/simulation/lbm.js',ROOT/'modell_r04/auslegung/antrieb.js']
prefix='PropBoard_M01_Review/'
entries={prefix+str(p.relative_to(ROOT)):p.read_bytes() for p in files}
entries[prefix+'README.md']='''# Cohexial Study M01 – Bewegung und Daten

1. `modell_r04_taumel/bewegung/Bewegung_oeffnen.FCMacro` in FreeCAD starten.
   Die native bewegliche FCStd-Datei liegt daneben im Unterordner `Ausgabe`.
   Das Makro lädt Solver/Zeitleiste und die zwei nominalen Servo-Geometrien.
2. `modell_r04_taumel/Datenbericht_M01.pdf` lesen: Nutzerangaben, berechnete
   Aerodynamik/Servolasten und fehlende Messungen werden ausdrücklich getrennt.
3. `modell_r04_taumel/simulation/H01_Flugsimulator.html` im Browser öffnen.
   Browser mit gesperrtem file://: im entpackten Ordner
   `python -m http.server 8000 --bind 127.0.0.1`, dann Seite über localhost öffnen.

Savöx SB-2271SG(+): Angaben 69 g, 6,0–7,4 V, 15/20 kg·cm, 0,08/0,06 s/60°.
KST X15-755X: 760 µs, nur Geometrie-Demo; weitere Last-/Signalwerte fehlen.
Realer Reibwert und experimentell validierte Aerodynamik liegen NICHT vor.
XFOIL-Kennwerte sind Berechnungen, die Identifikations-Testdaten synthetisch.
Servohalter, Spline-/Kugelaufnahmen, Dauerlast, BEC und Mechanikfreigaben sind offen.

Native M01-Innenteile von Lager/Motor sind Funktionsschemata, keine Hersteller-
fertigungszeichnungen. Die interne Getriebestufe des Kaufservos ist unbekannt.
Flugwiedergabe in FreeCAD löst Kinematik, keine neue Kraft-/Kontaktdynamik.

Node-Flugversuche ohne weitere Pakete:
`node modell_r04_taumel/simulation/testflug.js`
`node modell_r04_taumel/simulation/pruefen.js`

Python-Auswertungen: numpy; Plots: matplotlib; PDF: reportlab.
Optionaler Browser-Test benötigt Playwright/Chromium. CAD-Erzeugung benötigt
FreeCAD Python/Part/MeshPart; die genutzten Tools selbst sind nicht enthalten.

Die vollständigen älteren Fertigungszeichnungen bleiben im separaten H01-Paket
und Repository ITSMEEME/PropBoard. Einige weiterführende Alt-Links fehlen hier.
'''.encode()
manifest=''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n' for name,data in sorted(entries.items()))
entries[prefix+'SHA256SUMS']=manifest.encode()
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for name,data in sorted(entries.items()):z.writestr(name,data)
with zipfile.ZipFile(Z) as z:
    assert z.testzip() is None
    for name,data in entries.items():assert hashlib.sha256(z.read(name)).digest()==hashlib.sha256(data).digest()
print(Z.name,len(entries),'files',round(Z.stat().st_size/2**20,2),'MiB',hashlib.sha256(Z.read_bytes()).hexdigest())
