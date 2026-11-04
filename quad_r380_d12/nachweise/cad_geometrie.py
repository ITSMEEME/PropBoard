"""Extract actual cylindrical CFK axes/endpoints from the unchanged D12 BREP."""
from pathlib import Path
import sys,json,hashlib,math
H=Path(__file__).resolve().parents[1];R=H.parent;O=H/'Ausgabe/Festigkeit';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
P=json.loads((H/'parameter.json').read_text());M=json.loads((H/'Ausgabe/Regler_Montage.json').read_text());native=H/'Ausgabe/Quad_Reglerhalter_Landefuesse.FCStd';sha=hashlib.sha256(native.read_bytes()).hexdigest();assert sha==M['native_sha256'];D=A.openDocument(str(native));modules=json.loads((H/'Ausgabe/Reglerhalter_Instanzen.json').read_text());variants={v['id']:v for v in json.loads((R/'quad_r380_d10/Varianten.json').read_text())};cfgs=json.loads((R/'quad_r380_d10/Konfigurationen.json').read_text());maxL=cfgs[-1]['motor_half_spacing_mm']*math.sqrt(2)-246

def cylinder(obj):
 s=obj.Shape;fs=[f for f in s.Faces if isinstance(f.Surface,Part.Cylinder)];assert len(fs)==2,(obj.Name,len(fs));outer=max(fs,key=lambda f:f.Surface.Radius);inner=min(fs,key=lambda f:f.Surface.Radius);axis=outer.Surface.Axis;axis.normalize();origin=outer.Surface.Center;t=[(v.Point-origin).dot(axis) for v in s.Vertexes];a=origin+axis*min(t);b=origin+axis*max(t)
 if a.x>b.x+1e-6 or abs(a.x-b.x)<1e-6 and a.z>b.z:a,b=b,a
 return dict(a=list(a),b=list(b),od_mm=2*outer.Surface.Radius,id_mm=2*inner.Surface.Radius,length_mm=(b-a).Length,master=obj.Name)
rows=[];maximum_error=0.
for c in M['configurations']:
 i=c['propeller_index'];v=variants[c['variant']];tubes=[];legs=[];spec=cfgs[i];mx=spec['motor_half_spacing_mm']*math.sqrt(2)-210
 for j in range(v['count']):
  obj=D.getObject(f'P{i}_{v["id"]}_Tube{j}');assert obj is not None;t=cylinder(obj);a=A.Vector(*v['start'][j]);b=a+(A.Vector(maxL,v['end'][j][1],min(v['end'][j][2],-(v['od']+8)/2-8))-a)*((mx-36)/maxL);error=max((A.Vector(*t['a'])-a).Length,(A.Vector(*t['b'])-b).Length);maximum_error=max(maximum_error,error);assert error<1e-4,(i,v['id'],j,error);tubes.append(t)
 module=next(m for m in modules if m['propeller_index']==i and m['variant']==v['id'])
 for part in module['parts']:
  if part['role']=='landing_CFK':legs.append(cylinder(D.getObject(part['master'])))
 assert len(legs)==2;legs.sort(key=lambda t:t['a'][0]);assert all(abs(t['length_mm']-s['length_mm'])<1e-4 for t,s in zip(legs,c['legs']))
 rows.append(dict(propeller_index=i,variant=v['id'],tubes=tubes,legs=legs,clamps=c['legs'],support_tube_index=c['support_tube_index'],foot_centre=[c['cx'],c['cy'],-260.],hub=[mx,0.,0.],module_origin_world_radial_mm=210,module_origin_world_z_mm=88,ground_z_world_mm=-180,arm_grip_mm=35,landing_grip_mm=32))
(O/'CAD_Geometrie.json').write_text(json.dumps(dict(native_sha256=sha,axis_source='Exact cylindrical BREP faces and vertex axial extrema;local arm coordinates in mm;no remodelling or native modification.',all50_verified=True,max_generator_endpoint_error_mm=maximum_error,configurations=rows),indent=2));print('CAD verified',len(rows),'maximum error',maximum_error,flush=True)
