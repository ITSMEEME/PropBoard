"""Verify review artifacts and package native CAD, exports and helper sources."""
import json,csv,hashlib,zipfile
from pathlib import Path
from pypdf import PdfReader
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
check=json.loads((HERE/'Montagepruefung.json').read_text())
assert not check['reference_integrity']
assert not check['intersections_sample'],check['intersections_sample']
for r in check['shapes'].values():assert not r['invalid'] and not r['multi_solid_results']
for r in check['bolt_coverage'].values():assert r['modeled_bolts']==r['registered_bolts'] and not r['unregistered']
display=json.loads((HERE/'Darstellungspruefung.json').read_text())
assert display['models']==5 and display['rotation_changes_image'] and display['hardware_toggle_changes_image'] and not display['page_errors']
native=list(HERE.glob('*.FCStd'));assert len(native)==6
for f in native:
    with zipfile.ZipFile(f) as z:assert z.testzip() is None and 'Document.xml' in z.namelist()
for model in json.loads((HERE/'Modelldaten.json').read_text()):
    assert hashlib.sha256((ROOT/model['file']).read_bytes()).hexdigest()==model['sha256']
assert len(PdfReader(HERE/'Referenzblaetter.pdf').pages)==4
pages=len(PdfReader(HERE/'Montagebericht.pdf').pages)
assert pages>=5
rows=list(csv.DictReader((HERE/'Stueckliste.csv').open(encoding='utf-8-sig')))
assert len([r for r in rows if r['Datei']=='Horizontal_Z_R02_Montage'])==3185
files=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts
       and p.suffix not in ['.zip','.FCBak','.FCStd1'] and p.name!='Paketmanifest.json']
files += [ROOT/'cad/umlauf_kinematik.py',ROOT/'konstruktion/erstellen.py',ROOT/'konstruktion/parameter.json',ROOT/'bericht/viewer_erstellen.py']
manifest={'revision':'R02','native_FCStd':len(native),'main_result_bodies':3185,'main_bolts':1270,
          'report_pages':pages,'drawing_pages':4,'sample_connection_count':check['sample_connections'],
          'manufacturing_release':False,'flight_validation':False,
          'sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
mp=HERE/'Paketmanifest.json';mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2));files.append(mp)
archive=HERE/'PropBoard_Horizontal_Z_R02_FreeCAD.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('START.txt','PropBoard Horizontal Z – R02\nZuerst entpacken.\nHauptmodell: horizontal_z_r02/00_Horizontal_Z_R02_Montage.FCStd\nBericht: horizontal_z_r02/Montagebericht.pdf\n3D: horizontal_z_r02/Modelle_3D.html\nOffene Schnittstellen im Bericht beachten. Keine Fertigungs- oder Personenflugfreigabe.\n')
    for p in files:z.write(p,str(p.relative_to(ROOT)))
    assert z.testzip() is None
    for f,sha in manifest['sha256'].items():assert hashlib.sha256(z.read(f)).hexdigest()==sha,f
for f in HERE.glob('*.FCBak'):f.unlink()
print(json.dumps({'files':len(files)+1,'native_files':len(native),'report_pages':pages,
      'archive_MiB':round(archive.stat().st_size/1024**2,2),'integrity_and_hashes_verified':True},indent=2))
