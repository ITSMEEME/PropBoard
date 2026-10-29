"""Archive report, native models, inputs and existing CFD evidence."""
from pathlib import Path
import json,hashlib,zipfile
from pypdf import PdfReader
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
models=json.loads((HERE/'Modelldaten.json').read_text())
for m in models:
    assert hashlib.sha256((ROOT/m['file']).read_bytes()).hexdigest()==m['sha256']
display=json.loads((HERE/'Darstellungspruefung.json').read_text())
assert display['rotation_changes_image'] and not display['page_errors']
assert display['report_images_loaded']==6
pdf=PdfReader(HERE/'Vergleichsbericht.pdf')
assert len(pdf.pages)==16
pdf_text='\n'.join(p.extract_text() for p in pdf.pages)
for term in ['13,9','19,4','5,92','80 000','Keine der beiden']:assert term in pdf_text,term
files=[]
for folder in ['bericht','cfd','vergleich_horizontal']:
    files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file())
for pattern in ['umlauf*','Umlauf*','Gegenlaeufiger_Fluegelumlauf*']:
    files.extend(p for p in (ROOT/'cad').glob(pattern) if p.is_file())
files=sorted(set(p for p in files if '__pycache__' not in p.parts
       and p.suffix not in ['.zip','.FCBak','.FCStd1'] and p.name!='Paketmanifest.json'))
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
manifest_path=HERE/'Paketmanifest.json'
manifest_path.write_text(json.dumps({'pdf_pages':len(pdf.pages),'files_sha256':manifest},indent=2))
files.append(manifest_path)
archive=HERE/'PropBoard_Vergleichsbericht_Gesamtpaket.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('START.txt','Bericht: bericht/Vergleichsbericht.pdf\nOffline-Bericht: bericht/Vergleichsbericht.html\nInteraktive CAD-Ansicht: bericht/Modelle_3D.html\nDateien zuerst entpacken.\nKeine realmassstaebliche 3D-CFD oder Flugvalidierung.\n')
    for p in files:z.write(p,str(p.relative_to(ROOT)))
    assert z.testzip() is None
    for filename,expected in manifest.items():
        assert hashlib.sha256(z.read(filename)).hexdigest()==expected,filename
print(json.dumps({'archive':str(archive),'files':len(files)+1,
                  'size_MiB':round(archive.stat().st_size/1024/1024,2),
                  'pdf_pages':len(pdf.pages),'integrity_verified':True},indent=2))
