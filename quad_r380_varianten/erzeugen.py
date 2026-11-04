import sys,json,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent; O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,Import
V=A.Vector; variants=json.loads((H.parent/'motoranschluss_varianten/Varianten.json').read_text())[:4]
def rod(a,b,r):
 d=b-a;return Part.makeCylinder(r,d.Length,a,d)
def capsule(a,b,r):return rod(a,b,r).fuse(Part.makeSphere(r,a)).fuse(Part.makeSphere(r,b))
def inter(a,b):
 c=a.common(b);return 0 if c.isNull() else max(0,c.Volume)
for v in variants:
 doc=A.newDocument('Variante_'+v['id']); starts=[V(*p) for p in v['start']];ends=[V(*p) for p in v['end']];outer=v['od']/2;inner=v['di']/2;bore=outer+.3; ringouter=bore+4
 base=Part.makeCylinder(14,6,V(420,0,-6));
 for x,y in [(25,0),(-25,0),(0,25),(0,-25)]:
  c=V(420+x,y,-6);base=base.fuse(Part.makeCylinder(9,6,c));base=base.fuse(rod(V(420,0,-3),V(420+x,y,-3),6))
 base=base.common(Part.makeBox(200,200,150,V(320,-100,-150)))
 root=Part.makeSphere(13,V(-20,0,-40));tubes=[];caps=[]
 for a,b in zip(starts,ends):
  d=b-a;d.normalize();t=rod(a,b,outer).cut(rod(a-d,b+d,inner));tubes.append(t)
  root=root.fuse(rod(a,a+d*35,ringouter)).fuse(capsule(V(-20,0,-40),a+d*3,7))
  base=base.fuse(rod(b-d*35,b,ringouter)).fuse(capsule(V(420,0,-9),b-d*3,7))
 for a,b in zip(starts,ends):
  d=b-a;d.normalize();root=root.cut(rod(a-d*5,b,bore));base=base.cut(rod(a,b+d*5,bore))
 for x,y in [(25,0),(-25,0),(0,25),(0,-25)]:base=base.cut(Part.makeCylinder(3.3,40,V(420+x,y,-20)))
 base=base.cut(Part.makeCylinder(7,30,V(420,0,-15))).common(Part.makeBox(200,200,150,V(320,-100,-150)))
 parts=[('Rahmenknoten',root),('Motorknoten',base)]+[(f'Rohr_{i+1}',s) for i,s in enumerate(tubes)]
 valid=all(s.isValid() and len(s.Solids)==1 for _,s in parts); print(v['id'],'valid',valid,flush=True)
 if not valid: print('Ungültige Körper',[(n,s.isValid(),len(s.Solids)) for n,s in parts],flush=True);A.closeDocument(doc.Name);continue
 for name,s in parts:
  o=doc.addObject('Part::Feature',name);o.Label=name;o.Shape=s
 doc.addObject('App::FeaturePython','Auswahl').addProperty('App::PropertyString','Variante');doc.Auswahl.Variante=v['id'];doc.recompute();path=O/(v['id']+'.FCStd');doc.saveAs(str(path));Import.export([doc.getObject(n) for n,_ in parts],str(O/(v['id']+'.step')))
 hits=[]
 for i,(n,s) in enumerate(parts):
  for m,t in parts[i+1:]:
   if s.BoundBox.intersect(t.BoundBox):
    volume=inter(s,t)
    if volume>.1:hits.append(dict(a=n,b=m,volume_mm3=volume))
 mass=(root.Volume+base.Volume)*2810e-9+sum(t.Volume for t in tubes)*1600e-9
 result=dict(variant=v['id'],tube_count=len(tubes),diameters_mm=[v['od'],v['di']],node_mass_kg=(root.Volume+base.Volume)*2810e-9,tube_mass_kg=sum(t.Volume for t in tubes)*1600e-9,model_mass_kg=mass,intersections=hits,symmetric_about_y_zero=True,scope='Isolierter Vorentwurf ohne Klemmschlitze, Schrauben, Isolierungen, Propeller oder Gesamtfahrzeug. Keine geprüfte Verbindungspassung, Zugänglichkeit, Festigkeit oder Flugfreigabe.',native_sha256=hashlib.sha256(path.read_bytes()).hexdigest());(O/(v['id']+'.json')).write_text(json.dumps(result,indent=2,ensure_ascii=False));print(v['id'],'collision',len(hits),'mass',mass,flush=True);A.closeDocument(doc.Name)
