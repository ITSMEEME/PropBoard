#!/usr/bin/env python3
"""Offline-Paket P10: native Baugruppe, Animation, STEP, Listen, Prüfberichte und Laufzeitabhängigkeiten."""
import hashlib
import json
import py_compile
import zipfile
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parents[1]
OUT = H / 'Ausgabe'
aufbau = json.loads((OUT / 'Aufbau_P10.json').read_text())
pruef = json.loads((OUT / 'Pruefbericht_P10.json').read_text())
export = json.loads((OUT / 'Browserexport_P10.json').read_text())
native = OUT / 'P10_Gesamtbaugruppe.FCStd'
sha = hashlib.sha256(native.read_bytes()).hexdigest()
assert aufbau['native_sha256'] == pruef['source_native_sha256'] == export['source_native_sha256'] == sha, 'Berichte gehören nicht zur nativen Datei'
assert pruef['status'] == 'PASS' and not aufbau['manufacturing_release']
for p in H.glob('*.py'):
    py_compile.compile(str(p), doraise=True)
compile((H / 'P10_oeffnen.FCMacro').read_text(), 'P10_oeffnen.FCMacro', 'exec')
files = [p for p in H.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc', '.FCBak')]
deps = ['bewegung_p09/voll_runtime.py', 'bewegung/bewegung_runtime.py', 'fertigung_p08/runtime.py', 'fertigung_p08/geometrie.py',
        'simulation/kinematik.json', 'cad/erstellen.py', 'cad/parameter.json', 'fertigung_p05/geometrie.py', 'bewegung_p09/README.md']
files += [H.parent / d for d in deps]
entries = {'PropBoard_P10/' + str(p.relative_to(ROOT)): p.read_bytes() for p in files}
entries['PropBoard_P10/README.md'] = ('''# P10 – Servohalter, Planetenstufe, Kabelbaum, Landegestell

FreeCAD 1.0.2: modell_r04_taumel/integration_p10/P10_oeffnen.FCMacro ausführen (Animation inkl. Planeten).
Die native Baugruppe Ausgabe/P10_Gesamtbaugruppe.FCStd lässt sich auch statisch öffnen.
Beschreibung, Annahmen und offene Punkte: modell_r04_taumel/integration_p10/README.md.
Interaktive 3D-Flugsimulation: im Repository ITSMEEME/PropBoard modell_r04_taumel/simulation/H01_Flugsimulator.html.

Konstruktionsentwurf; keine Fertigungs-, Festigkeits-, Elektro- oder Flugfreigabe. Servo-STEP weiterhin ungültig.
''').encode()
entries['PropBoard_P10/SHA256SUMS'] = ''.join(hashlib.sha256(d).hexdigest() + '  ' + n + '\n' for n, d in sorted(entries.items())).encode()
Z = H.parent / 'Cohexial_P10_Integration.zip'
with zipfile.ZipFile(Z, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for n, d in sorted(entries.items()):
        z.writestr(n, d)
with zipfile.ZipFile(Z) as z:
    assert z.testzip() is None
print(Z.name, len(entries), 'Dateien', round(Z.stat().st_size / 2 ** 20, 2), 'MiB')
