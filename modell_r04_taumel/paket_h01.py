#!/usr/bin/env python3
"""Package the validated holder geometry and explicitly conditional mechanism review."""
from pathlib import Path
import hashlib,json,zipfile
HERE=Path(__file__).resolve().parent
h=HERE/'halterungen';m=HERE/'mechanik'
v=json.loads((h/'Ausgabe/Validierung_H01.json').read_text())
assert len(v['parts'])==7 and v['recorded_static_collisions']==0 and v['parameter_adapter_70_72_70_passed']
a=json.loads((m/'Mechanikpruefung.json').read_text())
assert a['kinematics']['samples']==6552 and a['kinematics']['max_closed_link_error_mm']<1e-7
servo=json.loads((m/'Servoauswahl_OFFEN.json').read_text())
assert servo['status'].startswith('BLOCKED_') # do not silently publish a false product approval
for p in list(h.rglob('*'))+list(m.rglob('*')):
    if p.is_file() and p.suffix in ('.FCBak','.FCStd1'):p.unlink()
paths=sorted(p for folder in (h,m) for p in folder.rglob('*') if p.is_file()
             and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.npz','.zip','.FCBak','.FCStd1'))
archive=HERE/'H01_Mechanik_und_Halterungen.zip'
root='PropBoard_H01_Review/'
manifest=[]
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in paths:
    name='modell_r04_taumel/'+str(p.relative_to(HERE))
    z.write(p,root+name);manifest.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+name)
 readme='''R04 – Mechanikreview und Halterungen H01

FreeCAD 1.0.2: modell_r04_taumel/halterungen/Halterungen_oeffnen.FCMacro ausfuehren.
Die neue Gesamtbaugruppe ist vollstaendig enthalten. Fuer native Einzelteile muss
halterungen_features.py neben dem Makro erhalten bleiben.

Zeichnungen: halterungen/Ausgabe/Halterungen_H01_Zeichnungen.pdf
Mechanikbericht: mechanik/Mechanikbericht.pdf und mechanik/README.md

Halterungen sind als Geometrie-/Montageentwurf geprueft. Keine Festigkeits- oder
Betriebsfreigabe. F01-Rotoranschluesse und Pitchwurzelreibung bleiben offen.
Servoauswahl_OFFEN.json nennt unbestaetigte Kandidaten: Herstellerabgleich wurde
von der Netz-Allowlist mit HTTP 403 blockiert. Keine Kauf- oder Einbaufreigabe.

Zur vollstaendigen Neuerzeugung dieses Pakets diese beiden Verzeichnisse in den
PropBoard-Checkout einordnen: Die vorhandenen cad/-Quellen und die F01-Baugruppe
werden als Basis verwendet. Das Oeffnen der mitgelieferten Gesamtbaugruppe und
Einzelteile benoetigt keinen vollstaendigen Repository-Checkout.

SHA256SUMS prueft die eingebetteten Daten. Vorschau-Quelldaten NPZ sind nicht
enthalten und koennen aus dem FreeCAD-Modell neu erzeugt werden.
'''
 z.writestr(root+'README.txt',readme)
 manifest.append(hashlib.sha256(readme.encode()).hexdigest()+'  README.txt')
 z.writestr(root+'SHA256SUMS','\n'.join(manifest)+'\n')
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for line in z.read(root+'SHA256SUMS').decode().splitlines():
    digest,name=line.split('  ',1)
    assert hashlib.sha256(z.read(root+name)).hexdigest()==digest,name
print(archive)
print('Files verified:',len(manifest),'MiB:',round(archive.stat().st_size/1024**2,2))
print('SHA256:',hashlib.sha256(archive.read_bytes()).hexdigest())
