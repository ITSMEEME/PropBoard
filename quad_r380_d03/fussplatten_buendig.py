"""Replace protruding foot bolts by ISO10642 and real 90-degree countersinks."""
import sys,json,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,Sketcher
V=A.Vector;d=A.openDocument(str(O/'QuadR380_D03_CFK.FCStd'));bom=json.loads((O/'Instanzen.json').read_text());spec=json.loads((O/'Bauteile.json').read_text())
# Recover already computed screw orientations after the expression-path assertion.
proof_file=O/'Gewindepruefung.json'
if proof_file.exists():
 prior=json.loads(proof_file.read_text());(O/'Gewindepruefung_vor_Senkkopf.json').write_text(json.dumps(prior,indent=2))
 for r in prior['pairs']:
  obj=d.getObject(r['bolt']);axis=obj.LinkPlacement.Rotation.multVec(V(0,0,1));obj.LinkPlacement=A.Placement(obj.LinkPlacement.Base,A.Rotation(axis,r['phase_deg']).multiply(A.Rotation(V(0,0,1),axis)))
body=d.getObject(next(r['instance'] for r in bom if r['id']=='D02_FOOT')).LinkedObject
pad=next(f for f in body.Group if f.TypeId=='PartDesign::Pad');pad.Length=6
pocket=next(f for f in body.Group if f.TypeId=='PartDesign::Pocket');sk=pocket.Profile[0] if isinstance(pocket.Profile,tuple) else pocket.Profile;pl=sk.Placement;pl.Base.z=6;sk.Placement=pl;pocket.Length=6;d.recompute()
s=body.newObject('Sketcher::SketchObject','SK_Fuss_Senkungen');s.Placement=A.Placement(V(0,0,6),A.Rotation())
for x in [-18,18]:
 for y in [-75,75]:
  for dy in [-20,20]:i=s.addGeometry(Part.Circle(V(x,y+dy,0),V(0,0,1),2.75),False);s.addConstraint(Sketcher.Constraint('Block',i))
f=body.newObject('PartDesign::Hole','Fuss_ISO10642_Senkungen');f.Profile=s;d.recompute();f.Diameter=5.5;f.Depth=6;f.DrillPoint='Flat';f.HoleCutType='Countersink';f.HoleCutDiameter=11.6;f.HoleCutCountersinkAngle=90;d.recompute();assert f.Shape.isValid() and len(f.Shape.Solids)==1;body.Tip=f
for feature in body.Group:
 if hasattr(feature,'Visibility'):feature.Visibility=feature==f
body.Visibility=False;spec['D02_FOOT'].update(volume_mm3=body.Shape.Volume,mass_kg=body.Shape.Volume*2700e-9,label='Fußplatte 300 x 140 x 6, Senkungen Ø11.6/90°')
shape=Part.read(str(H/'Quellen/Normteile/ISO10642_M5x50.brep'));assert shape.isValid();master=d.addObject('Part::Feature','ISO10642_M5_L50');master.Shape=shape;master.Label='ISO10642 M5x50';master.Visibility=False;d.getObject('Bauteilbibliothek').addObject(master);spec['ISO10642_M5x50']=dict(id='ISO10642_M5x50',label='ISO10642 M5x50 Senkschraube',process='Kaufteil ISO10642 Klasse10.9; konkrete Lieferung und Zinklamelle qualifizieren',density_kg_m3=7850,material='Vergütungsstahl',volume_mm3=shape.Volume,mass_kg=shape.Volume*7850e-9)
remove=[]
for r in bom:
 obj=d.getObject(r['instance'])
 if r['label']=='Scheibe Fuß oben':remove.append(r['instance']);d.removeObject(r['instance']);continue
 if r['label']=='Fußschlitten M5':
  obj.setLink(master);obj.BauteilID='ISO10642_M5x50';p=obj.LinkPlacement;p.Base.z=243.8;obj.LinkPlacement=p;r['id']='ISO10642_M5x50';r['source']='ISO10642 Nenngeometrie mit Helixgewinde'
 if r['id']=='D02_FOOT':r['label']='Fußplatte 300 x 140 x 6'
 r['mass_kg']=spec[r['id']]['mass_kg'];r['placement_mm']=list(obj.LinkPlacement.Base);r['placement_quaternion']=list(obj.LinkPlacement.Rotation.Q)
bom=[r for r in bom if r['instance'] not in remove];used={r['id'] for r in bom};spec={k:v for k,v in spec.items() if k in used};d.recompute();d.save();(O/'Instanzen.json').write_text(json.dumps(bom,indent=2,ensure_ascii=False));(O/'Bauteile.json').write_text(json.dumps(spec,indent=2,ensure_ascii=False));body.Shape.exportStep(str(O/'D02_FOOT.step'))
if proof_file.exists():proof_file.unlink() # Foot thread pairs require the new ISO10642 geometry; no old pass is carried forward.
report=json.loads((O/'Status.json').read_text());report.update(modeled_instances=len(bom),part_types=len(used),mass_modeled_kg=sum(r['mass_kg'] for r in bom),native_sha256=hashlib.sha256((O/'QuadR380_D03_CFK.FCStd').read_bytes()).hexdigest(),foot_plate_thickness_mm=6,foot_counterbore_diameter_mm=11.6,foot_head_top_clearance_mm=.2,foot_screw_type='ISO10642 M5x50');(O/'Status.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print('Flush foot plates',len(bom),report['mass_modeled_kg'],flush=True)
