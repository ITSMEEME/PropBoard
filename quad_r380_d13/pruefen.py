"""Native axis/radius and connector-free bore checks for the changed internal harness.
No assertion of complete external path,OEM mating/functional pinout or thermal release.
"""
from pathlib import Path
import sys,json,hashlib,math
H=Path(__file__).resolve().parent;R=H.parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod']);sys.path.insert(0,str(R/'quad_r380_d07'))
import FreeCAD as A,Part,PartDesign
from geometrie import intersection_volume
D=A.openDocument(str(O/'Quad_Standardkabelbaum.FCStd'));meta=json.loads((O/'Aufbau.json').read_text());plan=json.loads((O/'Kabelplanung.json').read_text());parts=json.loads((O/'Kabel_Bauteile.json').read_text());instances=json.loads((O/'Kabel_Instanzen.json').read_text());oldrows=json.loads((R/'quad_r380_d10/Ausgabe/Instanzen.json').read_text());cfg=json.loads((R/'quad_r380_d10/Konfigurationen.json').read_text());rows=[];collisions=[];switch=[];corridors=[];control=D.getObject('Variantensteuerung');cache={}
def cyls(s):return [f.Surface for f in s.Faces if isinstance(f.Surface,Part.Cylinder)]
for c in plan['configurations']:
 pi=c['propeller_index'];vi=c['variant'];cs=[p for p in parts if p['propeller_index']==pi and p['variant']==vi and p['part']=='Isolation'];actual=[]
 for r in cs:
  cable=D.getObject(r['master']).Shape;cc=max(cyls(cable),key=lambda s:s.Radius);tubeRow=next(t for t in oldrows if t['propeller_index']==pi and t['variant']==vi and t['part']==f'Tube{r["tube"]}' and t['instance'].endswith('_45'));tube=D.getObject(tubeRow['instance']).LinkedObject.Shape;tc=min(cyls(tube),key=lambda s:s.Radius);liner_shape=D.getObject(f'H13_P{pi}_{vi}_Liner{r["tube"]}').Shape;lc=min(cyls(liner_shape),key=lambda s:s.Radius);lo=max(cyls(liner_shape),key=lambda s:s.Radius);assert tc.Radius-lo.Radius>=.09;off=(cc.Center-lc.Center).cross(lc.Axis).Length;gap=lc.Radius-off-cc.Radius;parallel=abs(abs(cc.Axis.dot(tc.Axis))-1);assert abs(cc.Radius-r['OD_design_max_mm']/2)<1e-7;assert gap>=.5-1e-7 and parallel<1e-8,(pi,vi,r['net'],gap,parallel);actual.append((r,cc));rows.append(dict(propeller_index=pi,variant=vi,net=r['net'],measured_outer_diameter_mm=2*cc.Radius,native_liner_wall_gap_mm=gap,axis_parallel_error=parallel,passed=True))
 for i,(a,ca) in enumerate(actual):
  for b,cb in actual[i+1:]:
   if a['tube']!=b['tube']:continue
   gap=(ca.Center-cb.Center).cross(ca.Axis).Length-ca.Radius-cb.Radius;assert gap>=.5-1e-7,(pi,vi,a['net'],b['net'],gap)
 # Full protected bore cylinder against actual root/motor geometry. Root corridors repeat across sizes.
 for t in sorted({r['tube'] for r in cs}):
  tubeRow=next(z for z in oldrows if z['propeller_index']==pi and z['variant']==vi and z['part']==f'Tube{t}' and z['instance'].endswith('_45'));tube=D.getObject(tubeRow['instance']).LinkedObject.Shape;surface=min(cyls(tube),key=lambda z:z.Radius);axis=surface.Axis;axis.normalize();vv=[v.Point.dot(axis) for v in tube.Vertexes];origin=surface.Center;ts=[(v.Point-origin).dot(axis) for v in tube.Vertexes];a=origin+axis*min(ts);b=origin+axis*max(ts)
  if a.x>b.x:a,b=b,a;axis=-axis
  for role,base,length in [('Root',a-axis*30,90),('Motor',b-axis*60,64)]:
   nodeRow=next(z for z in oldrows if z['propeller_index']==pi and z['variant']==vi and z['part']==role and z['instance'].endswith('_45'));obj=D.getObject(nodeRow['instance']).LinkedObject;corridor=Part.makeCylinder(surface.Radius-.4,length,base,axis);key=(obj.Name,t,tuple(round(x,6) for x in base),round(length,6))
   if key not in cache:cache[key]=intersection_volume(corridor,obj.Shape)
   vol=cache[key];corridors.append(dict(propeller_index=pi,variant=vi,tube=t,part=role,corridor_overlap_mm3=vol))
   if vol>.1:collisions.append(corridors[-1])
 control.Propeller=cfg[pi]['label'];control.Variante=vi;D.recompute();visible=[r for r in instances if D.getObject(r['instance']).Visibility];expected=4*(10+len({r['tube'] for r in cs}));assert len(visible)==expected and all(r['propeller_index']==pi and r['variant']==vi for r in visible);switch.append(dict(propeller_index=pi,variant=vi,new_visible_cable_parts=len(visible),passed=True));print('D13 check',pi,vi,'corridor findings',len(collisions),flush=True)
report=dict(native_sha256=hashlib.sha256((O/'Quad_Standardkabelbaum.FCStd').read_bytes()).hexdigest(),source_structural_native_sha256=meta['source_D12_native_sha256'],axis_radius_checks=rows,full_bore_against_root_motor_checks=corridors,corridor_findings=collisions,minimum_native_wire_liner_gap_mm=min(r['native_liner_wall_gap_mm'] for r in rows),nominal_packing_pass=True,root_motor_bore_clear=not collisions,switch_checks=switch,protected_structural_BREP_unchanged=meta['structural_shapes_unchanged'],scope='Actual cylindrical jacket/liner axes and radii;pair spacing;50 native selector states;90mm root/64mm motor segments of full usable liner bore vs actual root/motor solids.One rigid corner copy per configuration.Purchased connector bodies,other vehicle parts outside these corridors,external bends,OEM ports,pinout,thermal rating and strength release are not covered.',closed_harness=False,production_ready=False)
(O/'Kabel_Pruefung.json').write_text(json.dumps(report,indent=2));assert not collisions,collisions;print('D13 native internal routing verified',len(rows),flush=True)
