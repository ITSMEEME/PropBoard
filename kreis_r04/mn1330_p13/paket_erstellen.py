#!/usr/bin/env python3
"""Package only active geometry and completed reports; no stale export files."""
import csv,hashlib,json,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent
O=H/'Ausgabe'

def main():
    report=json.loads((O/'Pruefung.json').read_text())
    native=hashlib.sha256((O/'P13_Mechanik.FCStd').read_bytes()).hexdigest()
    assert report['checked_native_sha256']==native,'Native Geometrie seit Prüfung geändert'
    step=json.loads((O/'Gesamt_STEP_Pruefung.json').read_text())
    assert step['native_sha256']==native
    assert step['step_sha256']==hashlib.sha256((O/'P13_Mechanik.step').read_bytes()).hexdigest()
    files=set(H.glob('*.py'))|set(H.glob('*.md'))|set(H.glob('*.FCMacro'))|{H/'parameter.json'}
    files|={p for p in (H/'basis_p12').iterdir() if p.suffix in ('.py','.json')}
    files|={p for p in O.iterdir() if p.suffix in ('.json','.csv','.html','.png') and 'Zwischenstand' not in p.name}
    files.add(O/'P13_Mechanik.FCStd')
    if step.get('passed',False):files.add(O/'P13_Mechanik.step')
    types=json.loads((O/'Teile.json').read_text())
    for t in types:
        folder='STEP_Nennkonturen' if t['reference'] else 'STEP_Sonderteile'
        files.add(O/folder/(t['id']+'.step'));files.add(O/'STL'/(t['id']+'.stl'))
        drawing=O/'Zeichnungen_RFQ'/(t['id']+'.svg')
        if drawing.exists():files.add(drawing)
    with (O/'Stueckliste.csv').open(encoding='utf-8-sig') as f:
        files|={O/r['step'] for r in csv.DictReader(f,delimiter=';')}
    assert all(p.is_file() for p in files)
    manifest={str(p.relative_to(H)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files)}
    mf=H/'DATEIEN_SHA256.json';mf.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n');files.add(mf)
    target=H.parents[1]/'lieferung'/'PropBoard_P13_Mechanik_RFQ.zip';target.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(files):z.write(p,'PropBoard_P13/'+str(p.relative_to(H)))
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    result=dict(path=str(target),files=len(files),bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),collision_status=report['collision_status'],manufacturing_release=False)
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
