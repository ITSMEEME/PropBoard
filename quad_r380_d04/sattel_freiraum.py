"""Shorten the saddle to clear the neighboring P12 socket ends; keep all CFRP uncut."""
import sys,json,hashlib,math
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,Sketcher
V=A.Vector;D=A.openDocument(str(O/'QuadR380_D04_CFK.FCStd'));rows=json.loads((O/'Instanzen.json').read_text());spec=json.loads((O/'Bauteile.json').read_text());xf=145/math.sqrt(2)
def block(s,g):i=s.addGeometry(g,False);s.addConstraint(Sketcher.Constraint('Block',i))
def outline(s,x):
 L=x-25;R=x+25;B=-40;T=40;r=3
 for a,b in [((L+r,B),(R-r,B)),((R,B+r),(R,T-r)),((R-r,T),(L+r,T)),((L,T-r),(L,B+r))]:block(s,Part.LineSegment(V(*a,0),V(*b,0)))
 for cx,cy,a in [(R-r,B+r,-90),(R-r,T-r,0),(L+r,T-r,90),(L+r,B+r,180)]:block(s,Part.ArcOfCircle(Part.Circle(V(cx,cy,0),V(0,0,1),r),math.radians(a),math.radians(a+90)))
for sx in [-1,1]:
 for stem in ['D04_SADDLE_TOP_','D04_SADDLE_BOTTOM_']:
  key=stem+str(sx).replace('-','M');b=D.getObject(key);pad=next(f for f in b.Group if f.TypeId=='PartDesign::Pad');s=pad.Profile[0] if isinstance(pad.Profile,tuple) else pad.Profile
  for i in reversed(range(s.GeometryCount)):s.delGeometry(i)
  outline(s,sx*xf);D.recompute()
  if 'TOP' in stem:
   seat=next(f for f in b.Group if f.TypeId=='PartDesign::Pocket' and f.Name.endswith('CFK_Sitz'));previous=seat.Shape.copy();features=[f for f in b.Group if f.TypeId=='PartDesign::Feature']
   assert len(features)==2
   for sy,f in zip([-1,1],features):
    low=V(sx*xf,sy*25,126.25);u=V(sx*385,sy*75,170)-low;u.normalize();f.Shape=previous.fuse(Part.makeCone(14,21,35,low,u)).removeSplitter();previous=f.Shape.copy()
  pocket=next(f for f in b.Group if f.TypeId=='PartDesign::Pocket' and f.Name.endswith('M6_Klemmung'));s=pocket.Profile[0] if isinstance(pocket.Profile,tuple) else pocket.Profile
  for i in reversed(range(s.GeometryCount)):s.delGeometry(i)
  for x,y in [(sx*xf-sx*18,-32),(sx*xf-sx*18,32),(sx*xf+sx*18,0)]:block(s,Part.Circle(V(x,y,0),V(0,0,1),3.3))
for r in rows:
 if r['label'] in ['Zentraler Sattel M6','Sattel Scheibe oben','Sattel Scheibe unten','Sattel Sicherungsmutter'] and abs(r['placement_mm'][1])>1:
  obj=D.getObject(r['instance']);p=obj.LinkPlacement;p.Base.y=32 if p.Base.y>0 else -32;obj.LinkPlacement=p
 if r['id']=='D04_SADDLE_FILM':
  obj=D.getObject(r['instance']);p=obj.LinkPlacement;p.Base.y=-40;obj.LinkPlacement=p
film=D.getObject('D04_SADDLE_FILM');film.Tip.Shape=Part.makeCylinder(10.3,80).cut(Part.makeCylinder(10,82,V(0,0,-1))).cut(Part.makeBox(12,.5,82,V(0,-.25,-1)));D.recompute()
for k in spec:
 if k.startswith('D04_SADDLE_'):
  b=D.getObject(k);assert b.Shape.isValid() and len(b.Shape.Solids)==1,k;spec[k]['volume_mm3']=b.Shape.Volume;spec[k]['mass_kg']=b.Shape.Volume*spec[k]['density_kg_m3']*1e-9;b.Shape.exportStep(str(O/(k+'.step')))
for r in rows:
 obj=D.getObject(r['instance']);r['placement_mm']=list(obj.LinkPlacement.Base);r['placement_quaternion']=list(obj.LinkPlacement.Rotation.Q);r['mass_kg']=spec[r['id']]['mass_kg']
# Actual solid head/shaft-to-upper-saddle checks, independent of nut thread fit.
for r in rows:
 if r['label']=='Zentraler Sattel M6':
  obj=D.getObject(r['instance']);sx=1 if obj.LinkPlacement.Base.x>0 else -1;target=D.getObject('D04_SADDLE_TOP_'+str(sx).replace('-','M'));volume=obj.Shape.common(target.Shape).Volume;print('Saddle bolt clearance',r['instance'],volume,flush=True);assert volume<.1
D.save();(O/'Instanzen.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False));(O/'Bauteile.json').write_text(json.dumps(spec,indent=2,ensure_ascii=False));before=json.loads((H.parent/'quad_r380_d03/Ausgabe/Instanzen.json').read_text());old={r['instance']:r for r in before};new={r['instance']:r for r in rows};oldmass=sum(r['mass_kg'] for r in before);mass=sum(r['mass_kg'] for r in rows);ledger=dict(d03_mass_kg=oldmass,d04_mass_kg=mass,saved_kg=oldmass-mass,saved_percent=100*(oldmass-mass)/oldmass,removed=[r for r in before if r['instance'] not in new],added=[r for r in rows if r['instance'] not in old],changed=[dict(instance=k,old_id=old[k]['id'],new_id=new[k]['id'],old_mass_kg=old[k]['mass_kg'],new_mass_kg=new[k]['mass_kg']) for k in old.keys()&new.keys() if abs(old[k]['mass_kg']-new[k]['mass_kg'])>1e-8]);(O/'Massenvergleich.json').write_text(json.dumps(ledger,indent=2,ensure_ascii=False));r=json.loads((O/'Status.json').read_text());r.update(mass_modeled_kg=mass,native_sha256=hashlib.sha256((O/'QuadR380_D04_CFK.FCStd').read_bytes()).hexdigest(),saddle_contact_length_mm=80);(O/'Status.json').write_text(json.dumps(r,indent=2,ensure_ascii=False));print('80mm saddle',mass,'saved',oldmass-mass,flush=True)
