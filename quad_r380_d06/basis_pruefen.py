"""Check unchanged D05 inventory/poses and native geometry metrics; chain prior proofs."""
import sys,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';B=H.parent/'quad_r380_d05/Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
old=A.openDocument(str(B/'QuadR380_D05_MN1330.FCStd'));new=A.openDocument(str(O/'QuadR380_D06_Propeller.FCStd'));before=json.loads((B/'Instanzen.json').read_text());after=json.loads((O/'Instanzen.json').read_text());byname={r['instance']:r for r in after};oldspec=json.loads((B/'Bauteile.json').read_text());newspec=json.loads((O/'Bauteile.json').read_text());checks=[]
for r in before:
    n=byname[r['instance']]
    assert r==n,r['instance']
    a=old.getObject(r['instance']).LinkPlacement;b=new.getObject(r['instance']).LinkPlacement
    assert (a.Base-b.Base).Length<1e-8 and abs(abs(sum(x*y for x,y in zip(a.Rotation.Q,b.Rotation.Q)))-1)<1e-10
for k in oldspec:
    assert oldspec[k]==newspec[k]
    r=next(r for r in before if r['id']==k);a=old.getObject(r['instance']).LinkedObject.Shape;b=new.getObject(r['instance']).LinkedObject.Shape
    assert len(a.Faces)==len(b.Faces) and len(a.Edges)==len(b.Edges)
    metrics=lambda s:[s.Volume,s.Area,*s.Solids[0].CenterOfMass,s.BoundBox.XMin,s.BoundBox.XMax,s.BoundBox.YMin,s.BoundBox.YMax,s.BoundBox.ZMin,s.BoundBox.ZMax]
    delta=max(abs(x-y) for x,y in zip(metrics(a),metrics(b)));assert delta<1e-5,(k,delta)
    checks.append(dict(part=k,maximum_geometry_metric_delta=delta,topology_counts_equal=True))
base_hash=hashlib.sha256((B/'QuadR380_D05_MN1330.FCStd').read_bytes()).hexdigest();inherited=[]
for name in ['Gewindepruefung.json','Bauraum_Pruefung.json','Motor_Montage_Pruefung.json']:
    d=json.loads((B/name).read_text());assert d['native_sha256']==base_hash
    inherited.append(dict(file='quad_r380_d05/Ausgabe/'+name,sha256=hashlib.sha256((B/name).read_bytes()).hexdigest(),native_sha256=base_hash,rerun_for_D06=False))
report=dict(passed=True,native_sha256=hashlib.sha256((O/'QuadR380_D06_Propeller.FCStd').read_bytes()).hexdigest(),base_native_sha256=base_hash,unchanged_inventory_and_link_placement_count=len(before),unchanged_prototype_metric_count=len(checks),actual_native_motor_reference_datum_corrected_count=4,prototype_metric_checks=checks,inherited_proofs=inherited,scope='D05 row data, link placement properties, masses and local master geometry metrics unchanged. Four actual native motor-reference positions are corrected by baking the formerly ignored -14mm master transform; previous D05 motor-clearance/motor-tool checks are superseded by D06. All corrected motors are checked versus fixed neighbors; motor/foot systems are separated in Z. Metrics are not a new full Boolean shape equivalence proof. Previous202 structural thread results retain original D05 hashes, with motor internal threads excluded. D06 checks new propeller interactions and72 tool corridors.')
motors=[r for r in after if r['id']=='D05_MN1330_LEGACY_REF'];feet=[r for r in after if r.get('foot_side')]
assert min(new.getObject(r['instance']).Shape.BoundBox.ZMin for r in feet)>max(new.getObject(r['instance']).Shape.BoundBox.ZMax for r in motors)
(O/'D05_Basis_Pruefung.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print('D05 basis unchanged',len(before),len(checks))
