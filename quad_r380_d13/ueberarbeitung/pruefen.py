"""Native changed-node pass: all50 configurations, local fits/corridors/assembly.
Four corners are rigid copies; collision checks use the45degree corner and all
active native assembly peers. Human is a reference, not a load-bearing part.
"""
from pathlib import Path
import sys,json,hashlib,math
H=Path(__file__).resolve().parents[1];R=H.parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod']);sys.path.insert(0,str(R/'quad_r380_d07'));sys.path.insert(0,str(H))
import FreeCAD as A,Part,PartDesign
from geometrie import intersection_volume,frame
from planung import axis_geometry
meta=json.loads((O/'Flachrippen_Aufbau.json').read_text());native=O/'Quad_Flachrippen_Mensch.FCStd';D=globals().get('BUILD_DOC') or A.openDocument(str(native));ctl=D.getObject('Variantensteuerung');asm=D.getObject('Montage');cs=json.loads((R/'quad_r380_d10/Konfigurationen.json').read_text());vs=json.loads((R/'quad_r380_d10/Varianten.json').read_text());old=json.loads((R/'quad_r380_d10/Ausgabe/Instanzen.json').read_text());oldshapes=globals().get('BUILD_OLD_SHAPES');source=None if oldshapes else A.openDocument(str(O/'Quad_Standardkabelbaum.FCStd'));checks=[];hits=[];baseline=[];corr=[];cache={};paircache={};V=A.Vector
for pi,c in enumerate(cs):
 for v in vs:
  vi=v['id'];ctl.Propeller=c['label'];ctl.Variante=vi;D.recompute();a,b=axis_geometry(v,c);nodes=[r for r in meta['changes'] if r['propeller_index']==pi and r['variant']==vi];selected=[o for o in asm.Group if o.TypeId=='App::Link' and o.Visibility and not o.Name.startswith('MENSCH_')];modified={r['master'] for r in nodes}
  for r in nodes:
   master=D.getObject(r['master']);shape=master.Shape
   if ('valid',master.Name) not in cache:cache[('valid',master.Name)]=shape.isValid() and len(shape.Solids)==1
   assert cache[('valid',master.Name)]
   if r['part']=='Motor':
    cy=shape.Solids[0].CenterOfMass.y;assert abs(cy)<.001,(pi,vi,cy)
    reflected=shape.mirror(V(),V(0,1,0));delta=abs(shape.Volume-intersection_volume(shape,reflected));assert delta<.1,(pi,vi,delta)
    x=c['motor_half_spacing_mm']*math.sqrt(2)-210
    for dx,y in [(25,0),(-25,0),(0,25),(0,-25)]:assert intersection_volume(shape,Part.makeCylinder(3.29,8,V(x+dx,y,-7)))<.1
   for j,(aa,bb) in enumerate(zip(a,b)):
    aa=V(*aa);bb=V(*bb);d=bb-aa;d.normalize();start=aa-d*30 if r['part']=='Root' else bb-d*60;length=90 if r['part']=='Root' else 64
    tool=Part.makeCylinder(v['di']/2-.4,length,start,d);key=(master.Name,j,r['part'],tuple(round(t,6) for t in start),tuple(round(t,6) for t in d))
    if key not in cache:cache[key]=intersection_volume(shape,tool)
    vol=cache[key];corr.append(dict(propeller_index=pi,variant=vi,part=r['part'],tube=j,volume_mm3=vol));assert vol<.1,(pi,vi,r['part'],j,vol)
   instance=D.getObject(next(x for x in r['instances'] if x.endswith('_45')));s=instance.Shape
   for other in selected:
    if other==instance or other.LinkedObject.Name in modified:continue
    t=other.Shape
    # Early axis-aligned rejection before expensive native common().
    if not s.BoundBox.intersect(t.BoundBox):continue
    key=(master.Name,other.LinkedObject.Name,tuple(round(x,5) for x in other.LinkPlacement.Base),tuple(round(x,5) for x in instance.LinkPlacement.Base))
    if key in paircache:vol,oldvol=paircache[key]
    else:
     vol=intersection_volume(s,t);oldvol=0
     if vol>.1:
      if oldshapes:
       previous=oldshapes[master.Name].copy();previous.Placement=instance.LinkPlacement.multiply(previous.Placement);oldvol=intersection_volume(previous,t)
      elif source.getObject(other.Name):oldvol=intersection_volume(source.getObject(instance.Name).Shape,source.getObject(other.Name).Shape)
     paircache[key]=(vol,oldvol)
    if vol>.1:
     finding=dict(propeller_index=pi,variant=vi,part=r['part'],other=other.Name,other_master=other.LinkedObject.Name,volume_mm3=vol,previous_volume_mm3=oldvol)
     # Existing untouched frame mating surfaces are reported, never silently waived.
     if vol<=oldvol+.1:baseline.append(finding)
     else:hits.append(finding)
  all_nodes=[o for o in selected if o.LinkedObject.Name in modified];assert len(all_nodes)==8
  checks.append(dict(propeller_index=pi,variant=vi,single_solid_nodes=True,motor_symmetric=True,native_selector_eight_yokes=True,new_interferences=sum(1 for h in hits if h['propeller_index']==pi and h['variant']==vi)));print('Yoke check',pi,vi,'new intersections',len(hits),flush=True)
people=[D.getObject(r['id']).Shape for r in meta['human']];height=max(s.BoundBox.ZMax for s in people)-min(s.BoundBox.ZMin for s in people);assert abs(height-1750)<.01,height
report=dict(native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),checks=checks,internal_corridor_checks=corr,new_interferences=hits,unchanged_or_reduced_baseline_contacts=baseline,human_height_measured_mm=height,human_lowest_z_mm=min(s.BoundBox.ZMin for s in people),geometry_passed=not hits,scope='Saved build document (or reopened native when run standalone),file SHA recorded;changed root/motor solids versus active native assembly peers at one rigid45degree corner;all50 configurations,motor mirror Boolean,bolt bores,full cable corridors.Human excluded as size reference.Existing unchanged mating contacts reported separately.No clamp-force,load,thermal or manufacturing-tolerance release.',strength_revalidation_required=True,production_ready=False)
(O/'Flachrippen_Pruefung.json').write_text(json.dumps(report,indent=2));assert not hits,hits;print('All50 new yokes passed native geometry',flush=True)
