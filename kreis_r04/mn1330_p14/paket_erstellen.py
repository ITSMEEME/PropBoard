"""Portable review ZIP, complete local dependencies, CRC and SHA256 manifest."""
import hashlib,json,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parent.parent;O=H/'Ausgabe';L=R/'lieferung'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def included(p):return p.is_file() and '__pycache__' not in p.parts and p.suffix.lower() not in ['.pyc','.fcbak','.fcstd1'] and p.name!='DATEIEN_SHA256.json'
def main():
    gate=json.loads((O/'Freigabe.json').read_text());assert gate['all_report_sources_match'] and not gate['production_ready']
    assert sha(O/'P14_MN1330_Leichtbau.FCStd')==gate['native_sha256']
    sources={
      'ph54-200-s500-r.md':'https://raw.githubusercontent.com/ROBOTIS-GIT/emanual/master/docs/en/dxl/p/ph54-200-s500-r.md',
      'dxl_p_info.yml':'https://raw.githubusercontent.com/ROBOTIS-GIT/emanual/master/_data/dxl_p_info.yml',
      'specifications_p.md':'https://raw.githubusercontent.com/ROBOTIS-GIT/emanual/master/_includes/en/dxl/p/specifications_p.md',
      'h54p_drawing.png':'https://raw.githubusercontent.com/ROBOTIS-GIT/emanual/master/assets/images/dxl/p/h54p_drawing.png',
      'ph54_performance.jpg':'https://raw.githubusercontent.com/ROBOTIS-GIT/emanual/master/assets/images/dxl/pro/h54-200-s500-r_performance_graph_2.jpg',
      'basicParameter_MN1330 KV40.xls':'User upload, original bytes; XLS contains product HTML',
      'MN1330_NS52x20_Nutzertabelle.csv':'User pasted19-row NS52x20 test line; temperature note117C/ambient25C; dwell unknown',
      'P13_Lastscreen_4dc7252.json':'Project baseline commit4dc7252fe58bc008df2559b8ebddab5328d36f94',
      'Legacy_BEMT_4dc7252.json':'Exact outputs from committed R04 code before P14; source SHA inside file',
      'xh540-w150.md':'Rejected candidate; ROBOTIS-GIT/emanual docs/en/dxl/x/xh540-w150.md',
      'dxl_x_info.yml':'Rejected XH540 candidate; ROBOTIS-GIT/emanual _data/dxl_x_info.yml',
      'specifications_x.md':'Rejected XH540 candidate; ROBOTIS-GIT/emanual _includes/en/dxl/specifications_x.md',
      'xh540_w150_performance.jpg':'Rejected XH540 candidate; ROBOTIS-GIT/emanual assets/images/dxl/x/xh540_w150_performance_graph.jpg',
      'x540_drawing.md':'Rejected XH540 candidate; OEM download links, no original STEP retrieved',
      'ph54-100-s500-r.md':'Alternative, not selected; ROBOTIS-GIT/emanual docs/en/dxl/p/ph54-100-s500-r.md',
    }
    sourceindex=[dict(file=p.name,sha256=sha(p),origin=sources.get(p.name,'Local source artifact')) for p in sorted((H/'Quellen').iterdir()) if p.is_file()]
    (H/'QUELLEN_SHA256.json').write_text(json.dumps(dict(sources=sourceindex,blocked_oem_step='https://www.robotis.com/service/download.php?no=1258 returned403; only nominal servo geometry supplied',user_clarification='180s qualifier is essential; no continuous motor rating inferred'),indent=2,ensure_ascii=False)+'\n')
    files=sorted(p for p in H.rglob('*') if included(p));manifest={p.relative_to(H).as_posix():sha(p) for p in files}
    mp=H/'DATEIEN_SHA256.json';mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n');files.append(mp)
    shared=[R/'kreis_r04/simulation'/f for f in ['r04_physik.js','lbm.js','pruefen.js']]
    start='''# P14 – lokales Entwicklungspaket

Flugsimulator: `kreis_r04/mn1330_p14/P14_Flugsimulator.html`.
Technischer Prüfstand: `kreis_r04/mn1330_p14/P14_Entwicklungspruefstand.html`.
CAD: `kreis_r04/mn1330_p14/Ausgabe/P14_MN1330_Leichtbau.FCStd`.
Ergebnis: `kreis_r04/mn1330_p14/ERGEBNIS.md`.

WASD bewegen, QE drehen, RF Höhe, T Start, L Landung, Leertaste Pause.
Für einen steuerbaren Flug ausdrücklich „Trainingsflug“ wählen.150Nm/40kW je Motor
sind dort freie Annahmen. Der voreingestellte MN1330-Fall bleibt bei100kg am Boden.
Gamepad und Mehrfinger-Touch sind verfügbar. Bedienung: `kreis_r04/mn1330_p14/FLUGSTEUERUNG.md`.

Dieses Paket ist ein Entwicklungsstand ohne Produktions-, Bestell- oder Flugfreigabe.
3,4kW/180s ist keine Dauerleistung. Höhere Motorprüfpunkte haben keine angegebene Haltedauer.
Die28 früheren Gelenk-Anschlussüberschneidungen sind geschlossen. Montagefolge und
geometrischer Prüfumfang: `kreis_r04/mn1330_p14/MONTAGE.md`. OEM-Servo-Anschluss,
Lieferprofile/Toleranzen und Last-/Ermüdungsnachweise bleiben offen.

Falls der Browser lokale Skripte sperrt, hier `python3 -m http.server8050 --bind127.0.0.1`
mit Leerzeichen zwischen `server`, `8050`, `--bind` und `127.0.0.1` starten und anschließend
`http://127.0.0.1:8050/kreis_r04/mn1330_p14/P14_Flugsimulator.html` aufrufen.

Die JSON-SHA256-Liste im P14-Verzeichnis prüft die unveränderten Paketdateien; sich selbst schließt sie aus.
Node-Prüfung aus diesem Verzeichnis: `node kreis_r04/mn1330_p14/pruefen_simulation.js`.
Flugregler-Prüfung: `node kreis_r04/mn1330_p14/pruefen_flugsteuerung.cjs`.
FreeCAD-Animation: zuerst FCStd öffnen, dann das benachbarte P14_Animation.FCMacro ausführen.
'''
    # Keep the actual copy/paste command unambiguous.
    start=start.replace('python3 -m http.server8050 --bind127.0.0.1','python3 -m http.server 8050 --bind 127.0.0.1').replace('\nmit Leerzeichen zwischen `server`, `8050`, `--bind` und `127.0.0.1` starten und anschließend',' starten und anschließend')
    L.mkdir(exist_ok=True);zpath=L/'PropBoard_P14_Leichtbau_Entwicklung.zip'
    with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files+shared:z.write(p,p.relative_to(R).as_posix())
        z.writestr('START_HIER_P14.md',start)
    with zipfile.ZipFile(zpath) as z:
        assert z.testzip() is None
        for rel,digest in manifest.items():assert hashlib.sha256(z.read('kreis_r04/mn1330_p14/'+rel)).hexdigest()==digest
        for p in shared:assert hashlib.sha256(z.read(p.relative_to(R).as_posix())).hexdigest()==sha(p)
        n=len(z.infolist())
    check=dict(zip=zpath.name,bytes=zpath.stat().st_size,sha256=sha(zpath),files=n,crc_and_file_hashes_pass=True,native_sha256=gate['native_sha256'],production_ready=False)
    (L/'PropBoard_P14_Paketpruefung.json').write_text(json.dumps(check,indent=2)+'\n');print(json.dumps(check,indent=2))
if __name__=='__main__':main()
