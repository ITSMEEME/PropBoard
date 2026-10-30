#!/usr/bin/env python3
import json,hashlib,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent;M=H.parent;ROOT=M.parent;Z=H/'Cohexial_P04_Motoranschluss_und_Kaufteile.zip'
r=json.loads((H/'Ausgabe/Pruefbericht_P04.json').read_text());native=H/'Ausgabe/P04_Baugruppe_PCD16_GESPERRT.FCStd'
assert not r['full_production_release'] and r['native_assembly_reopen_pass'] and r['drawing_PCD_mm']==16
assert hashlib.sha256(native.read_bytes()).hexdigest()==r['native_sha256']
files=[p for p in H.rglob('*') if p.is_file() and p.suffix.lower() not in ('.zip','.pyc','.fcbak') and '__pycache__' not in p.parts]
files += [p for p in (M/'fertigung_p02/Quellen').iterdir() if p.is_file()]
files += [M/'fertigung_p02/README.md',M/'fertigung_p02/anforderungen.json',M/'fertigung_p02/Ausgabe/Normteilpruefung.json',M/'fertigung_p02/Ausgabe/Integrationspruefung.json',M/'fertigung_p02/Ausgabe/Fertigungsstatus_P02.json',M/'fertigung_p02/Ausgabe/Fertigungsstatus_P02.csv',M/'fertigung_p02/Ausgabe/P02_Normteilkatalog.FCStd',M/'fertigung_p02/Ausgabe/P02_Kaufteile_Integration_GESPERRT.FCStd',M/'cad/erstellen.py',M/'cad/parameter.json',M/'fertigung_p03/Eingang/Nutzerrecherche_2026-10-30.txt',M/'fertigung_p03/Datenabgleich_P03.json',M/'fertigung_p03/VERWORFEN.md']
prefix='PropBoard_P04_Review/';entries={prefix+str(p.relative_to(ROOT)):p.read_bytes() for p in files}
entries[prefix+'README.md']='''# Cohexial Study P04 – aktueller Motoranschluss

`modell_r04_taumel/fertigung_p04/P04_oeffnen.FCMacro` in FreeCAD starten.
Alternativ die gespeicherte native P04-Baugruppe unter `Ausgabe` öffnen.

Die bereitgestellte EMAX-Zeichnung bestätigt 4×M3 auf einem Lochkreis Ø16 mm.
Die vorherige Textangabe 16×16 war falsch. Entsprechende P03-CADs sind verworfen
und NICHT enthalten. Motorhöhe 31,6 mm und 13-mm-Abtriebsüberstand sind übernommen.

Das Motor-CAD ist ein Anschluss-/Grenzhüllenmodell eines vollständigen Kaufteils
nach der Zeichnung, keine Original-STEP oder Innenfertigungszeichnung. Nicht bemaßte
Lüftung/Fußkontur, M3-Blindtiefen und M5-Gewindelänge werden nicht erfunden.
Die Gesamtbaugruppe ist weiterhin GESPERRT; die verbleibenden Daten stehen in
`fertigung_p04/Noch_benoetigte_Daten_P04.md`.

P02-Dateien dienen als historische Basis und Quellen-/Normteilnachweis. Aktuell ist
P04. Die zusätzlichen Servo-/Lagerangaben der Textrecherche sind unverifizierte
Recherchebehauptungen, keine automatisch übernommenen Herstellerfreigaben.

Für Regeneration FreeCAD-Python/Part/MeshPart verwenden. Zum Öffnen der statisch
gepeicherten P04-Dokumente sind keine Community-Erzeuger nötig. Die bisherige
Flugsimulation/M01 und andere Fertigungsentwürfe sind im vollständigen Repository.
'''.encode()
entries[prefix+'SHA256SUMS']=''.join(hashlib.sha256(v).hexdigest()+'  '+k+'\n' for k,v in sorted(entries.items())).encode()
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for k,v in sorted(entries.items()):z.writestr(k,v)
with zipfile.ZipFile(Z) as z:
 assert z.testzip() is None
 for k,v in entries.items():assert hashlib.sha256(z.read(k)).digest()==hashlib.sha256(v).digest()
print(Z.name,len(entries),'files',round(Z.stat().st_size/2**20,2),'MiB',hashlib.sha256(Z.read_bytes()).hexdigest())
