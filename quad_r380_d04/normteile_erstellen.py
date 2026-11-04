"""Generate true helical fastener models from pinned FreeCAD Fasteners tables.

Generated geometries are nominal ISO surfaces, not manufacturer inspection data.
External workbench is read only. Models and input table rows are retained locally.
"""
import sys,os,json,types,hashlib,subprocess,shutil,csv
from pathlib import Path
H=Path(__file__).resolve().parent;W=Path(os.environ.get('QUAD_FASTENERS_PATH','/tmp/quad-d03-fasteners'))
PIN='fddd07af422b7d3a69098b32333711c5eeae184c'
assert subprocess.check_output(['git','-C',str(W),'rev-parse','HEAD'],text=True).strip()==PIN
sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod/Draft','/usr/share/freecad/Mod/BIM',str(W)])
import PySide2
sys.modules['PySide']=PySide2
import FreeCAD,Part,ScrewMaker
O=H/'Quellen/Normteile';O.mkdir(parents=True,exist_ok=True)
specs=[('ISO4762','M4',10),('ISO4762','M6',45)]
old={r['id']:r for r in json.loads((O/'Quellenmanifest.json').read_text())['rows']} if (O/'Quellenmanifest.json').exists() else {}
rows=[]
for typ,diam,length in specs:
    key=typ+'_'+diam+(f'x{length}' if length else '')
    print('Normteil',key,flush=True)
    fa=types.SimpleNamespace(baseType=typ,Type=typ,Diameter=diam,calc_diam=diam,calc_len=str(length) if length else None,LeftHanded=False,Thread=typ!='ISO7089')
    if key in old and (O/(key+'.brep')).exists():
        assert hashlib.sha256((O/(key+'.brep')).read_bytes()).hexdigest()==old[key]['brep_sha256']
        shape=Part.Shape();shape.read(str(O/(key+'.brep')))
    else:shape=ScrewMaker.Instance.createFastener(fa)
    assert shape and shape.isValid() and len(shape.Solids)==1,key
    shape.exportBrep(str(O/(key+'.brep')));shape.exportStep(str(O/(key+'.step')))
    table=W/'FsData'/(typ.lower()+'def.csv')
    inp=list(csv.reader(table.open()));values=next(r for r in inp[2:] if r[0]==diam)
    rows.append(dict(id=key,standard=typ,diameter=diam,length_mm=length,real_helical_thread=fa.Thread,table=dict(zip(inp[1],values)),brep_sha256=hashlib.sha256((O/(key+'.brep')).read_bytes()).hexdigest(),volume_mm3=shape.Volume,geometry_scope='Nominal ISO profile from open Fasteners implementation; 6g/6H tolerances and property class remain drawing/procurement requirements'))
    shutil.copyfile(table,O/table.name)
shutil.copyfile(W/'LICENSE',O/'LICENSE-FastenersWB')
(O/'Quellenmanifest.json').write_text(json.dumps(dict(repository='https://github.com/shaise/FreeCAD_FastenersWB',commit=PIN,rows=rows),indent=2))
print('Normteilmodelle gueltig',len(rows),flush=True)
