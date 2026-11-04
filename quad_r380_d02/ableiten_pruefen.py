"""Check D02 nominal bodies, adjustable foot travel and export native display surfaces."""
import sys,json,hashlib,math
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,MeshPart
V=A.Vector;d=A.openDocument(str(O/'QuadR380_D02_CFK.FCStd'));bom=json.loads((O/'Instanzen.json').read_text());spec=json.loads((O/'Bauteile.json').read_text())
if not d.getObject('Fussverstellung'):
 c=d.addObject('App::FeaturePython','Fussverstellung');c.addProperty('App::PropertyFloatConstraint','Links','Verstellung');c.Links=(-200,-250,-130,1);c.addProperty('App::PropertyFloatConstraint','Rechts','Verstellung');c.Rechts=(200,130,250,1)
 for r in bom:
  if any(w in r['label'] for w in ['Fuß','Schlitten','Verstellbacke']):
   x=r['placement_mm'][0];side='Links' if x<0 else 'Rechts';base=-200 if x<0 else 200;r['foot_side']=side;r['foot_base_x_mm']=base;d.getObject(r['instance']).setExpression('LinkPlacement.Base.x','Fussverstellung.'+side+f' + ({x-base:.8f})')
 d.recompute()
control=d.getObject('Fussverstellung');travel=[]
for left in [-250,-200,-130]:
 for right in [130,200,250]:
  control.Links=left;control.Rechts=right;d.recompute()
  for r in bom:
   if 'foot_side' in r:
    value=left if r['foot_side']=='Links' else right;expected=value+r['placement_mm'][0]-r['foot_base_x_mm'];assert abs(d.getObject(r['instance']).LinkPlacement.Base.x-expected)<1e-6
  # Analytical full travel: foot outline and 60mm clamp envelope remain inside tube ends; plates separate.
  assert left+70<right-70;assert left-70>-380 and right+70<380
  assert left-30>-380 and right+30<380
  travel.append(dict(left_x_mm=left,right_x_mm=right,stance_mm=right-left,native_expressions_match=True,rail_and_plate_envelope_pass=True))
control.Links=-200;control.Rechts=200;d.recompute();d.save()
(O/'Instanzen.json').write_text(json.dumps(bom,indent=2,ensure_ascii=False));(O/'Fussverstellung_Pruefung.json').write_text(json.dumps(dict(cases=travel,scope='Native LinkPlacement expressions and analytical longitudinal plate/clamp envelopes; not whole-vehicle swept-volume or clamp-load proof'),indent=2))
meshes={};shapevalid=True
for k in dict.fromkeys(r['id'] for r in bom):
 r=next(r for r in bom if r['id']==k);master=d.getObject(r['instance']).LinkedObject;s=master.Shape;assert s.isValid() and len(s.Solids)==1,k
 mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.15,AngularDeflection=.6 if k.startswith('ISO') else .35,Relative=False);v,f=mesh.Topology;meshes[k]=dict(vertices_mm=[[round(y,5) for y in p] for p in v],faces=f,material=spec[k]['material'],label=master.Label);print('Mesh',k,len(f),flush=True)
r=json.loads((O/'Status.json').read_text());r.update(native_sha256=hashlib.sha256((O/'QuadR380_D02_CFK.FCStd').read_bytes()).hexdigest(),all_master_solids_valid=True,foot_travel_cases_checked=len(travel));(O/'Status.json').write_text(json.dumps(r,indent=2,ensure_ascii=False))
j=dict(scope='D02 actual CAD surfaces, no schematic OEM solids',report=r,meshes=meshes,instances=bom);(O/'mesh.js').write_text('globalThis.QD_MODEL='+json.dumps(j,separators=(',',':'),ensure_ascii=False)+';\n')
print('D02 exports and travel checked',flush=True)
