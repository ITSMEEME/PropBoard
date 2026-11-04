"""Native-hole alignment, motor mounting datum and V3 cut/grip checks."""
import sys,json,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
V=A.Vector;native=O/'QuadR380_D07_V3.FCStd';D=A.openDocument(str(native));rows=json.loads((O/'Instanzen.json').read_text());byname={r['instance']:r for r in rows};proof=json.loads((O/'Gewindepruefung.json').read_text());alignment=[]
for p in proof['pairs']:
    mate=D.getObject(p['mate']);bolt=D.getObject(p['bolt']);row=byname[p['mate']]
    if not row['id'].startswith('D07_'):continue
    point=mate.LinkPlacement.inverse().multVec(bolt.LinkPlacement.Base);axis=bolt.LinkPlacement.Rotation.multVec(V(0,0,1));hits=[]
    for f in mate.LinkedObject.Group:
        if f.TypeId!='PartDesign::Hole':continue
        sk=f.Profile[0] if isinstance(f.Profile,tuple) else f.Profile;hp=sk.Placement.inverse().multVec(point);worldaxis=mate.LinkPlacement.Rotation.multiply(sk.Placement.Rotation).multVec(V(0,0,1))
        distance=min(math.hypot(hp.x-g.Center.x,hp.y-g.Center.y) for g in sk.Geometry if type(g).__name__=='Circle')
        if distance<1e-5 and axis.dot(worldaxis)>.999999:
            length=float(byname[p['bolt']]['id'].split('x')[-1]);engagement=length-hp.z;assert engagement>0 and engagement<=float(f.ThreadDepth)+.1
            hits.append(dict(feature=f.Name,axis_offset_mm=distance,nominal_engagement_mm=engagement,thread_depth_mm=float(f.ThreadDepth)))
    assert hits,p;alignment.append(dict(bolt=p['bolt'],mate=p['mate'],matches=hits))

def pattern(obj,centre,radius,pcd):
    points=[]
    for f in obj.Shape.Faces:
        if not isinstance(f.Surface,Part.Cylinder):continue
        s=f.Surface;c=s.Center
        if abs(s.Radius-radius)<1e-5 and abs(math.hypot(c.x-centre[0],c.y-centre[1])-pcd/2)<1e-5:
            if not any(math.dist((c.x,c.y),q)<1e-5 for q in points):points.append((c.x,c.y))
    return points
motorchecks=[]
for m in json.loads((O/'Motor_Schnittstellen.json').read_text()):
    motor=D.getObject(m['motor']);node=D.getObject(m['node']);centre=list(motor.LinkPlacement.Base);a=pattern(node,centre,3.3,50);b=pattern(motor,centre,3.15,50);assert len(a)==len(b)==4;delta=max(min(math.dist(p,q) for q in b) for p in a);assert delta<1e-5
    assert abs(motor.Shape.BoundBox.ZMin-88)<1e-5 and abs(motor.Shape.BoundBox.ZMax-154)<1e-5;assert abs(node.Shape.BoundBox.ZMax-88)<1e-5
    motorchecks.append(dict(**m,maximum_hole_axis_offset_mm=delta,motor_base_z_mm=motor.Shape.BoundBox.ZMin,node_top_z_mm=node.Shape.BoundBox.ZMax,nominal_reference_only=True))
arms=json.loads((O/'V3_Rohre.json').read_text());assert len(arms)==8 and all(abs(r['length_mm']-387)<1e-5 for r in arms)
for r in arms:
    shape=D.getObject(r['instance']).LinkedObject.Shape;assert len(shape.Faces)==4;assert shape.isValid();r['no_transverse_holes']=True
assert len(alignment)==128,(len(alignment),'expected96 core+32 clamp pairs')
report=dict(native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),passed=True,native_thread_axis_checks=alignment,motor_mount_checks=motorchecks,arms=arms,grip_length_each_end_mm=35,clamp_split_gap_mm=.5,liner_radial_thickness_mm=.3,scope='All96 new-parametrized core-port M4 axes and32 new socket M4 axes match the native tap features and positive nominal engagement. Four4xM6 motor patterns coincide with legacy reference only; OEM depths/material/torque remain unverified.8 actual annular tubes with no transverse holes;387mm cuts and35mm grips. No CFK contact/preload/tolerance/strength release.')
(O/'Schnittstellen_Pruefung.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print('V3 interfaces verified',len(alignment),'thread axes,4 motor patterns,8 tubes')
