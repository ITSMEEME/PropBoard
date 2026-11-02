"""Export selected actual native CAD surfaces, not illustrative substitutes."""
import sys,json
from pathlib import Path
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as App
H=Path(__file__).resolve().parent
selected=['P14_R750','P14_R800','QUAD_R380','HEXA_R265_B4']
data=[]
for cid in selected:
    out=H/'Ausgabe'/cid;r=json.loads((out/'Pruefung.json').read_text());rows=json.loads((out/'Massendaten.json').read_text());doc=App.openDocument(str(out/(cid+'.FCStd')));meshes=[]
    for p in rows:
        key,label=p['id'],p['label']
        if key.startswith('GRID'):continue
        if p['group']=='P14_existing' and not any(s in label for s in ['CFK01','MN1330','SERVO','Zentralblock',' A01',' A03','A09','A10','A11','A16A']):continue
        if key.startswith('ATTACH_M8'):continue
        s=doc.getObject(key).Shape;v,f=s.tessellate(1.6)
        category='guard' if key.startswith(('RING','GUARD')) else 'deck' if key=='DECK' else 'battery' if key.startswith('BATTERY') else 'drive' if p['group'] in ['motor','rotor','P14_existing'] else 'frame'
        colour= '#137f9a' if ('BLADE' in key or 'CFK01' in label) else '#b44c4b' if ('MOTOR' in key or 'MN1330' in label) else '#c29b51' if category=='guard' else '#4c8b64' if category=='battery' else '#253e50' if category=='deck' else '#9aabb7'
        meshes.append(dict(id=key,label=label,category=category,colour=colour,vertices=[[round(x,3) for x in pt] for pt in v],faces=f))
    data.append(dict(id=cid,report=r,meshes=meshes));App.closeDocument(doc.Name)
    print(cid,len(meshes),'meshes',flush=True)
(H/'modelle.js').write_text('globalThis.AB_MODELS='+json.dumps(data,separators=(',',':'),ensure_ascii=False)+';\n')
(H/'Renderdaten.json').write_text(json.dumps(data,separators=(',',':'),ensure_ascii=False))
