"""Native BREP/placement verification directly from saved FCStd ZIP.
No GUI-mesh geometry and no25000-link restoration; explicit selector bindings.
"""
from pathlib import Path
import sys,json,hashlib,math
H=Path(__file__).resolve().parents[1];R=H.parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib']);sys.path.insert(0,str(R/'quad_r380_d07'));sys.path.insert(0,str(H))
import FreeCAD as A,Part
from zipcad import Native
from geometrie import intersection_volume
from planung import axis_geometry
meta=json.loads((O/'Flachrippen_Aufbau.json').read_text());native=O/'Quad_Flachrippen_Mensch.FCStd';n=Native(native);original=Native(O/'Quad_Standardkabelbaum.FCStd');data=json.loads((O/'projekt.js').read_text()[len('globalThis.QD_MODEL='):].strip().rstrip(';'));rows=data['instances'];del data
cs=json.loads((R/'quad_r380_d10/Konfigurationen.json').read_text());vs=json.loads((R/'quad_r380_d10/Varianten.json').read_text());hits=[];baseline=[];checks=[];corr=[];cache={};paircache={};shapes={};V=A.Vector
resume_file=H/'Cache/Pruef_Wiederaufnahme.json';resume=json.loads(resume_file.read_text()) if resume_file.exists() else {}
if resume and resume.get('native_sha256')==meta['native_sha256'] and resume.get('source_reader_sha256')==hashlib.sha256((Path(__file__).parent/'zipcad.py').read_bytes()).hexdigest():
 checks=resume['checks'];hits=resume['new_interferences'];baseline=resume['baseline_contacts'];print('Resume',len(checks),'completed native cases',flush=True)
else:resume={}
completed={(r['propeller_index'],r['variant']) for r in checks}
world_boxes={}
for pi,c in enumerate(cs):
 for vidx,v in enumerate(vs):
  vi=v['id']
  if (pi,vi) in completed:continue
  nodes=[r for r in meta['changes'] if r['propeller_index']==pi and r['variant']==vi];active=[r for r in rows if ('propeller_index' not in r or r['propeller_index']==pi) and ('variant' not in r or r['variant']==vi) and r.get('group') not in ['Rotorhuelle','Mensch','Bildpropeller']];changed={r['master'] for r in nodes};a,b=axis_geometry(v,c)
  for r in nodes:
   name=r['master'];s=n.shape(name)
   if ('valid',name) not in cache:cache[('valid',name)]=s.isValid() and len(s.Solids)==1
   assert cache[('valid',name)]
   for inst in r['instances']:
    ex=' '.join(x.get('expression','') for x in n.expressions(inst));assert f'Variantensteuerung.Variante == {vidx}' in ex and f'Variantensteuerung.Propeller == {pi}' in ex
    assert n.linked(inst)==name
   if r['part']=='Motor':
    assert abs(s.Solids[0].CenterOfMass.y)<.001
    assert abs(s.Volume-intersection_volume(s,s.mirror(V(),V(0,1,0))))<.1
   for j,(aa,bb) in enumerate(zip(a,b)):
    aa=V(*aa);bb=V(*bb);d=bb-aa;d.normalize();start=aa-d*30 if r['part']=='Root' else bb-d*60;length=90 if r['part']=='Root' else 64;key=('bore',name,j,tuple(round(x,6) for x in start),tuple(round(x,6) for x in d))
    if key not in cache:cache[key]=intersection_volume(s,Part.makeCylinder(v['di']/2-.4,length,start,d))
    vol=cache[key];corr.append(dict(propeller_index=pi,variant=vi,part=r['part'],tube=j,volume_mm3=vol));assert vol<.1,(pi,vi,r['part'],j,vol)
   inst=next(i for i in r['instances'] if i.endswith('_45'));world=n.instance(inst);world_box=world.BoundBox
   for p in active:
    if p['id'] in changed:continue
    key=('world',p['instance'])
    if key not in shapes:shapes[key]=n.row(p)
    t=shapes[key]
    if key not in world_boxes:world_boxes[key]=t.BoundBox
    if not world_box.intersect(world_boxes[key]):continue
    pair=(name,p['id'],tuple(round(x,5) for x in p['placement_mm']),tuple(round(x,5) for x in p['placement_quaternion']))
    if pair not in paircache:
     vol=intersection_volume(world,t);oldvol=0
     if vol>.1:
      print('Contact',pi,vi,r['part'],p['instance'],vol,flush=True);oldvol=intersection_volume(original.instance(inst),original.row(p))
     paircache[pair]=(vol,oldvol)
    vol,oldvol=paircache[pair]
    if vol>.1:
     finding=dict(propeller_index=pi,variant=vi,part=r['part'],other=p['instance'],other_master=p['id'],volume_mm3=vol,previous_volume_mm3=oldvol)
     (baseline if vol<=oldvol+.1 else hits).append(finding)
  checks.append(dict(propeller_index=pi,variant=vi,single_solid_nodes=True,motor_symmetric=True,eight_native_link_bindings_checked=True,new_interferences=sum(1 for x in hits if x['propeller_index']==pi and x['variant']==vi)));(O/'Flachrippen_Zwischenpruefung.json').write_text(json.dumps(dict(checks=checks,new_interferences=hits,baseline_contacts=baseline),indent=2));print('Native ZIP check',pi,vi,'new',len(hits),flush=True)
people=[n.shape(r['id']) for r in meta['human']];height=max(s.BoundBox.ZMax for s in people)-min(s.BoundBox.ZMin for s in people);assert abs(height-1750)<.01
report=dict(native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),checks=checks,internal_corridor_checks=corr,new_interferences=hits,unchanged_or_reduced_baseline_contacts=baseline,human_height_measured_mm=height,human_lowest_z_mm=min(s.BoundBox.ZMin for s in people),geometry_passed=not hits,scope='Saved native BREP and native LinkPlacements from FCStd ZIP;one rigid45degree corner vs active assembly peers;all50 configurations;mirror Boolean and full cable bores.Native selector expressions/links verified,not50 GUI recomputations.Human excluded as reference;no structural/thermal/tolerance approval.',strength_revalidation_required=True,production_ready=False,resumed_completed_cases=resume.get('checks',[]),resumed_source_checkpoint_sha256=hashlib.sha256(resume_file.read_bytes()).hexdigest() if resume else None,resumed_completed_case_bores_verified=bool(resume.get('successful_cases_include_all_asserted_bore_checks')),source_completed_algorithm_sha256=resume.get('completed_algorithm_sha256'))
(O/'Flachrippen_Pruefung.json').write_text(json.dumps(report,indent=2));assert not hits,hits;print('All50 native saved geometries pass',flush=True)
