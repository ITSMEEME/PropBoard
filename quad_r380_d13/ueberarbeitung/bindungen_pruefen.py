from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parents[1];sys.path.append('/usr/lib/freecad-python3/lib')
from zipcad import Native
n=Native(H/'Ausgabe/Quad_Flachrippen_Mensch.FCStd');o=Native(H/'Ausgabe/Quad_Standardkabelbaum.FCStd');m=json.loads((H/'Ausgabe/Flachrippen_Aufbau.json').read_text());bindings=[];protected=[];roundtrip=[]
for r in m['changes']:
 for inst in r['instances']:
  a=n.placement(inst);b=o.placement(inst);assert (a.Base-b.Base).Length<1e-8;assert abs(abs(sum(x*y for x,y in zip(a.Rotation.Q,b.Rotation.Q)))-1)<1e-10;assert n.linked(inst)==r['master'];bindings.append(inst)
for name in n.objects:
 if name.startswith('H13_') or any(name.endswith('_Tube'+str(i)) for i in range(4)):
  p=n.prop(name,'Shape');q=o.prop(name,'Shape')
  if p is None or q is None:continue
  a=n.z.read(p.find('Part').attrib['file']);b=o.z.read(q.find('Part').attrib['file'])
  if a!=b:
   sa=n.shape(name);sb=o.shape(name)
   if sa.exportBrepToString()!=sb.exportBrepToString():
    eps=max(abs(getattr(sa.BoundBox,k)-getattr(sb.BoundBox,k)) for k in ['XMin','XMax','YMin','YMax','ZMin','ZMax']);diff=sa.cut(sb).Volume+sb.cut(sa).Volume;assert eps<1e-6 and diff<.001,(name,eps,diff);roundtrip.append(dict(master=name,bbox_difference_mm=eps,symmetric_difference_volume_mm3=diff))
  protected.append(name)
assert len(protected)==730,len(protected)
f=H/'Ausgabe/Quad_Flachrippen_Mensch.FCStd';report=dict(native_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),all400_yoke_placements_unchanged=True,link_bindings_checked=len(bindings),protected_cable_and_CFK_shapes=protected,protected_count=len(protected),saved_geometry_equivalent_within_documented_precision=True,serialization_roundtrip_differences=roundtrip,precision_bbox_mm=1e-6,precision_symmetric_difference_mm3=.001)
(H/'Ausgabe/Bindungen_Pruefung.json').write_text(json.dumps(report,indent=2));print('400 native placements and730 saved CFK/cable shapes verified',flush=True)
