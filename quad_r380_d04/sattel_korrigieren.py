"""Documented iterative correction: three noncollinear clamp screws clear the stay bosses."""
import sys,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,Sketcher
V=A.Vector;D=A.openDocument(str(O/'QuadR380_D04_CFK.FCStd'));rows=json.loads((O/'Instanzen.json').read_text());spec=json.loads((O/'Bauteile.json').read_text());pairs=json.loads((O/'Neue_Gewindepaare.json').read_text());xframe=145/(2**.5);remove=set()
proof=json.loads((O/'Gewindepruefung.json').read_text());assert proof['passed'];refs=[];hashes={}
for r in proof['pairs']:
 a=D.getObject(r['bolt']);b=D.getObject(r['mate'])
 for obj in [a.LinkedObject,b.LinkedObject]:
  if obj.Name not in hashes:hashes[obj.Name]=hashlib.sha256(obj.Shape.exportBrepToString().encode()).hexdigest()
 rel=a.LinkPlacement.inverse().multiply(b.LinkPlacement);refs.append(dict(result=r,master_a_sha256=hashes[a.LinkedObject.Name],master_b_sha256=hashes[b.LinkedObject.Name],relative_placement=list(rel.Base)+list(rel.Rotation.Q)))
(O/'D04_Gewindereferenzen_vor_Korrektur.json').write_text(json.dumps(refs,indent=2))
for sx in [-1,1]:
 pts=[(sx*xframe-sx*18,-35),(sx*xframe-sx*18,35),(sx*xframe+sx*18,0)]
 for stem in ['D04_SADDLE_TOP_','D04_SADDLE_BOTTOM_']:
  key=stem+str(sx).replace('-','M');b=D.getObject(key);pocket=next(f for f in b.Group if f.TypeId=='PartDesign::Pocket' and f.Name.endswith('M6_Klemmung'));sk=pocket.Profile[0] if isinstance(pocket.Profile,tuple) else pocket.Profile
  for i in reversed(range(sk.GeometryCount)):sk.delGeometry(i)
  for x,y in pts:i=sk.addGeometry(Part.Circle(V(x,y,0),V(0,0,1),3.3),False);sk.addConstraint(Sketcher.Constraint('Block',i))
 # Drop the outboard negative-Y joint; move the outboard positive-Y joint toY0.
 for r in rows:
  if r['label'] not in ['Zentraler Sattel M6','Sattel Scheibe oben','Sattel Scheibe unten','Sattel Sicherungsmutter']:continue
  if abs(r['placement_mm'][0]-(sx*xframe+sx*18))>.01:continue
  if r['placement_mm'][1]<0:remove.add(r['instance'])
  else:obj=D.getObject(r['instance']);p=obj.LinkPlacement;p.Base.y=0;obj.LinkPlacement=p
for n in remove:D.removeObject(n)
rows=[r for r in rows if r['instance'] not in remove];pairs=[p for p in pairs if p['bolt'] not in remove]
D.recompute()
for k in list(spec):
 if k.startswith('D04_SADDLE_TOP_') or k.startswith('D04_SADDLE_BOTTOM_'):
  b=D.getObject(k);assert b.Shape.isValid() and len(b.Shape.Solids)==1;spec[k]['volume_mm3']=b.Shape.Volume;spec[k]['mass_kg']=b.Shape.Volume*2810e-9;b.Shape.exportStep(str(O/(k+'.step')))
for r in rows:
 obj=D.getObject(r['instance']);r['placement_mm']=list(obj.LinkPlacement.Base);r['placement_quaternion']=list(obj.LinkPlacement.Rotation.Q);r['mass_kg']=spec[r['id']]['mass_kg']
D.save();(O/'Instanzen.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False));(O/'Bauteile.json').write_text(json.dumps(spec,indent=2,ensure_ascii=False));(O/'Neue_Gewindepaare.json').write_text(json.dumps(pairs,indent=2,ensure_ascii=False))
before=json.loads((H.parent/'quad_r380_d03/Ausgabe/Instanzen.json').read_text());old={r['instance']:r for r in before};new={r['instance']:r for r in rows};oldmass=sum(r['mass_kg'] for r in before);mass=sum(r['mass_kg'] for r in rows)
ledger=dict(d03_mass_kg=oldmass,d04_mass_kg=mass,saved_kg=oldmass-mass,saved_percent=100*(oldmass-mass)/oldmass,removed=[r for r in before if r['instance'] not in new],added=[r for r in rows if r['instance'] not in old],changed=[dict(instance=k,old_id=old[k]['id'],new_id=new[k]['id'],old_mass_kg=old[k]['mass_kg'],new_mass_kg=new[k]['mass_kg']) for k in old.keys()&new.keys() if abs(old[k]['mass_kg']-new[k]['mass_kg'])>1e-8]);(O/'Massenvergleich.json').write_text(json.dumps(ledger,indent=2,ensure_ascii=False))
r=json.loads((O/'Status.json').read_text());r.update(modeled_instances=len(rows),mass_modeled_kg=mass,new_thread_pairs=len(pairs),native_sha256=hashlib.sha256((O/'QuadR380_D04_CFK.FCStd').read_bytes()).hexdigest(),saddle_clamp_screws_each=3,thread_geometry_pass=False);(O/'Status.json').write_text(json.dumps(r,indent=2,ensure_ascii=False));print('Corrected clamp layout',len(rows),mass,'saved',oldmass-mass,'pairs',len(pairs),flush=True)
