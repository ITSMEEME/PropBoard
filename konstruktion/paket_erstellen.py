import json,csv,hashlib,zipfile
from pathlib import Path
from collections import Counter
from pypdf import PdfReader
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
report=json.loads((HERE/'Pruefbericht.json').read_text())
assert all(r['saved_reopened'] for r in report.values())
assert report['00_PropBoard_Detail_Stehen']['within_2100_1700_600']
check=json.loads((HERE/'Abstandspruefung.json').read_text())
assert all(r['strictly_positive_clearance'] for r in check['checks'].values())
views=json.loads((HERE/'Darstellungspruefung.json').read_text())
assert views['models']==7 and views['rotation_changes_image'] and not views['page_errors']
for model in json.loads((HERE/'Modelldaten.json').read_text()):
    assert hashlib.sha256((ROOT/model['file']).read_bytes()).hexdigest()==model['sha256']
rows=list(csv.DictReader((HERE/'Stueckliste_Instanzen.csv').open(encoding='utf-8-sig')))
main=[r for r in rows if r['Datei']=='00_PropBoard_Detail_Stehen.FCStd'];qty=Counter(r['ID'] for r in main)
for key,n in {'FL-CFK-REF':16,'PITCH-W01':16,'SCHL-01':32,'PITCH-MOT-REF':16,'ENC-REF':16,'BAT-MOD-REF':2,'CFK-L01':2,'CFK-Q01':3}.items():assert qty[key]==n,(key,qty[key])
native=list(HERE.glob('*.FCStd'));assert len(native)==8
for file in native:
    with zipfile.ZipFile(file) as z:assert z.testzip() is None and 'Document.xml' in z.namelist()
draw=PdfReader(HERE/'Referenzblaetter.pdf');assert len(draw.pages)==4
pdf=PdfReader(HERE/'Konstruktionsbericht.pdf');assert len(pdf.pages)>=12
text='\n'.join(p.extract_text() for p in pdf.pages)
for term in ['Stehen als Hauptvariante','1,8','1698','Fertigungsfreigabe']:assert term in text,term
files=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts
       and p.suffix not in ['.zip','.FCBak','.FCStd1'] and p.name!='Paketmanifest.json']
files += [ROOT/'cad/umlauf_kinematik.py',ROOT/'bericht/viewer_erstellen.py']
manifest={'native_files':len(native),'pdf_pages':len(pdf.pages),'reference_drawing_pages':4,
          'main_instances':len(main),'manufacturing_release':False,
          'files_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
mp=HERE/'Paketmanifest.json';mp.write_text(json.dumps(manifest,indent=2));files.append(mp)
archive=HERE/'PropBoard_Konstruktionsvorentwurf_FreeCAD.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('START.txt','Hauptmodell: konstruktion/00_PropBoard_Detail_Stehen.FCStd\nBericht: konstruktion/Konstruktionsbericht.pdf\nReferenzblaetter: konstruktion/Referenzblaetter.pdf\n3D-Viewer: konstruktion/Modelle_3D.html\nZuerst entpacken. VORENTWURF OHNE FERTIGUNGS- ODER FLUGFREIGABE.\n')
    for p in files:z.write(p,str(p.relative_to(ROOT)))
    assert z.testzip() is None
    for filename,sha in manifest['files_sha256'].items():assert hashlib.sha256(z.read(filename)).hexdigest()==sha,filename
for p in HERE.glob('*.FCBak'):p.unlink()
print(json.dumps({'files':len(files)+1,'native_FCStd':len(native),'main_instances':len(main),
                  'report_pages':len(pdf.pages),'archive_MiB':round(archive.stat().st_size/1024/1024,2),
                  'zip_and_hashes_verified':True},indent=2))
