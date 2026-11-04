"""Exact V3 socket/node construction; all dimensions in mm, no strength release."""
import math
import FreeCAD as A
import Part
V=A.Vector

def clean(shape):
    candidate=shape.copy().removeSplitter()
    return candidate if candidate.isValid() and len(candidate.Solids)==len(shape.Solids) else shape

def trim_core(shape):
    # Delete the old broad cap/bar behind Y=-22. This cutting plane stays outside
    # all three retained socket-port envelopes and their native thread surfaces.
    out=shape.cut(Part.makeBox(300,150,300,V(-150,-172,-150)))
    assert out.isValid() and len(out.Solids)==1
    return out

def pipe_direction(p,sign):
    d=V(sign*(p['tip_tube_half_width_mm']-p['root_tube_half_width_mm']),-(p['tip_tube_r_mm']-p['root_tube_r_mm']),p['tip_tube_z_mm']-p['root_tube_z_mm']);d.normalize();return d

def frame(axis):
    z=V(*axis) if not isinstance(axis,V) else V(axis);z.normalize();x=V(0,0,1).cross(z);x.normalize();y=z.cross(x)
    return A.Rotation(x,y,z,'ZXY')

def placed(shape,origin,rotation):
    s=shape.copy();s.Placement=A.Placement(V(*origin),rotation).multiply(s.Placement);return s

def capsule(a,b,r):
    a=V(*a);b=V(*b);d=b-a
    return Part.makeCylinder(r,d.Length,a,d).fuse(Part.makeSphere(r,a)).fuse(Part.makeSphere(r,b))

def socket_shape(p,upper=False,stop=None):
    length=p['grip_length_mm'];gap=p['split_gap_mm']/2;outer=p['socket_od_mm']/2;inner=p['socket_bore_mm']/2
    ring=Part.makeCylinder(outer,length).cut(Part.makeCylinder(inner,length+2,V(0,0,-1)))
    half=Part.makeBox(100,50,length+2,V(-50,gap if upper else -50-gap,-1));s=ring.common(half)
    # One ear per side, shortened axially to reduce mass;2 screws per cap.
    ez=(length-p['ear_axial_length_mm'])/2
    for sign in [-1,1]:
        x=sign*p['ear_x_mm']-5;y=gap if upper else -p['ear_top_mm'];h=p['ear_top_mm']-gap
        s=s.fuse(Part.makeBox(10,h,p['ear_axial_length_mm'],V(x,y,ez)))
    if stop:
        z=-3.3 if stop=='root' else length
        end=Part.makeCylinder(outer,3.3,V(0,0,z))
        pocket_z=-p['end_pad_thickness_mm'] if stop=='root' else length
        end=end.cut(Part.makeCylinder(inner,p['end_pad_thickness_mm'],V(0,0,pocket_z)))
        s=s.fuse(end)
    s=s.removeSplitter()
    if upper:
        for sign in [-1,1]:s=s.cut(Part.makeCylinder(2.25,20,V(sign*p['ear_x_mm'],20,length/2),V(0,-1,0)))
    assert s.isValid() and len(s.Solids)==1
    return s

def pipe_local_points(p):
    radial=p['motor_xy_half_spacing_mm']*math.sqrt(2)
    root=[];tip=[]
    # Node-local axes: X=tangent, Y=inward, Z=up.
    for sign in [-1,1]:
        root.append(V(sign*p['root_tube_half_width_mm'],-(p['root_tube_r_mm']-p['core_radius_mm']),p['root_tube_z_mm']-p['core_z_mm']))
        tip.append(V(sign*p['tip_tube_half_width_mm'],radial-p['tip_tube_r_mm'],p['tip_tube_z_mm']-p['motor_base_z_mm']))
    return root,tip

def core_envelope(sign):
    h=math.sqrt(.5);dirs=[V(h,h,0),V(-h,h,0),V(0,0,-sign)];s=Part.makeSphere(14)
    for d in dirs:s=s.fuse(Part.makeCone(8,21,15,V(),d)).fuse(Part.makeCylinder(21,10,d*15,d))
    return s.removeSplitter(),dirs

def root_node(p,old_threaded_core):
    # Parameterize the existing three-port envelope anew. Internal threads are
    # added as native Hole features only after all load-path unions are complete.
    s,_=core_envelope(1);roots,tips=pipe_local_points(p);ports=[]
    for i,start in enumerate(roots):
        sign=-1 if i==0 else 1;d=pipe_direction(p,sign);rot=frame(d);body=placed(socket_shape(p,stop='root'),tuple(start),rot);s=s.fuse(body)
        # Bypass the retained downward core port and join directly to the backstop.
        s=s.fuse(capsule((sign*13,-9,-1),tuple(start-d*2+rot.multVec(V(0,-4,0))),7))
        ports.append(dict(origin=list(start),direction=list(d),quaternion=list(rot.Q)))
    for port in ports:s=s.cut(Part.makeCylinder(p['socket_bore_mm']/2,500,V(*port['origin']),V(*port['direction'])))
    assert s.isValid() and len(s.Solids)==1
    return s,ports

def motor_node(p):
    h=p['integrated_motor_foot_thickness_mm'];s=Part.makeCylinder(14,h,V(0,0,-h))
    for x,y in [(25,0),(-25,0),(0,25),(0,-25)]:
        a=V(0,0,-h);b=V(x,y,-h);d=b-a
        # Rounded constant-thickness integral arms, not a separate mounting plate.
        n=V(-d.y,d.x,0);n.normalize();pts=[a+n*6,b+n*6,b-n*6,a-n*6]
        web=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,h));s=s.fuse(web).fuse(Part.makeCylinder(9,h,V(x,y,-h)))
    roots,tips=pipe_local_points(p);ports=[]
    for i,end in enumerate(tips):
        sign=-1 if i==0 else 1;d=pipe_direction(p,sign);rot=frame(d);start=end-d*p['grip_length_mm'];s=s.fuse(placed(socket_shape(p,stop='tip'),tuple(start),rot))
        # Connect at the forward tube stop; support webs remain below the motor.
        q=end+d*2+rot.multVec(V(0,-4,0))
        s=s.fuse(capsule((sign*25,10,-7),tuple(q),6))
        ports.append(dict(origin=list(start),direction=list(d),quaternion=list(rot.Q)))
    for port in ports:
        d=V(*port['direction']);end=V(*port['origin'])+d*p['grip_length_mm'];s=s.cut(Part.makeCylinder(p['socket_bore_mm']/2,500,end-d*500,d))
    for x,y in [(25,0),(-25,0),(0,25),(0,-25)]:
        s=s.cut(Part.makeCylinder(3.3,10,V(x,y,-8)))
        # Explicit head/tool access below each integral boss.
        s=s.cut(Part.makeCylinder(6,40,V(x,y,-46)))
    s=s.cut(Part.makeCylinder(7,20,V(0,0,-10)))
    s=s.removeSplitter();assert s.isValid() and len(s.Solids)==1
    assert s.BoundBox.ZMax<1e-6
    return s,ports

def liner(p):
    L=p['grip_length_mm'];s=Part.makeCylinder(p['socket_bore_mm']/2,L).cut(Part.makeCylinder(p['tube_od_mm']/2,L+2,V(0,0,-1)))
    return s.cut(Part.makeBox(15,.5,L+2,V(0,-.25,-1)))

def intersection_volume(a,b):
    aa=a.BoundBox;bb=b.BoundBox
    if any(min(getattr(aa,d+'Max'),getattr(bb,d+'Max'))-max(getattr(aa,d+'Min'),getattr(bb,d+'Min'))<=1e-7 for d in ['X','Y','Z']):return 0.0
    try:
        c=a.common(b);return 0.0 if c.isNull() else max(0,c.Volume)
    except ValueError as error:
        if 'NullShapeException' not in str(error):raise
        s=a.cut(b);assert not s.isNull() and s.isValid();v=a.Volume-s.Volume;assert v>=-1e-5;return max(0,v)
