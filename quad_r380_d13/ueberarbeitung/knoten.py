"""Integrated split-clamp yokes: one planar rib per tube, symmetric motor cross.
Nominal CAD only; no material allowables or structural release inferred.
"""
import sys,math
from pathlib import Path
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'quad_r380_d07'))
import FreeCAD as A,Part
from geometrie import frame,placed,socket_shape,clean
V=A.Vector

def web(a,b,thickness=4,depth=18):
    # Flat vertical trapezoid; the upper edge penetrates each intended anchor.
    n=(b-a).cross(V(0,0,1));n.normalize();n*=thickness/2
    pts=[a-V(0,0,depth)-n,b-V(0,0,depth)-n,b+V(0,0,2)-n,a+V(0,0,2)-n]
    return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(n*2)

def motor_cross(x):
    s=Part.makeCylinder(14,6,V(x,0,-6))
    for dx,y in [(25,0),(-25,0),(0,25),(0,-25)]:
        a=V(x,0,-6);b=V(x+dx,y,-6);d=b-a;n=V(-d.y,d.x,0);n.normalize();n*=6
        q=[a+n,b+n,b-n,a-n];s=s.fuse(Part.Face(Part.makePolygon(q+[q[0]])).extrude(V(0,0,6))).fuse(Part.makeCylinder(9,6,b))
    return s

def make_nodes(v,c,starts,ends,core,p0,cached_root=None):
    p=dict(p0);p.update(tube_od_mm=v['od'],tube_id_mm=v['di'],socket_bore_mm=v['od']+.6,socket_od_mm=v['od']+8,ear_x_mm=v['od']/2+6)
    x=c['motor_half_spacing_mm']*math.sqrt(2)-210
    root=core.copy() if cached_root is None else cached_root.copy();motor=motor_cross(x);ports=[]
    if cached_root is None:
        low=min((V(*a)+frame(V(*b)-V(*a)).multVec(V(0,-p['socket_od_mm']/2+2,17.5))).z-20 for a,b in zip(starts,ends))
        root=root.fuse(web(V(-58,0,20),V(-20,0,20),12,6))
        root=root.fuse(Part.makeBox(4,56,8,V(-22,-28,14)))
        for y in [-28,22]:root=root.fuse(Part.makeBox(4,6,22-low,V(-22,y,low)))
    for j,(aa,bb) in enumerate(zip(starts,ends)):
        a=V(*aa);b=V(*bb);d=b-a;d.normalize();rot=frame(d);ro=p['socket_od_mm']/2
        for side,origin in ([('Root',a)] if cached_root is None else [])+[('Motor',b-d*35)]:
            shell=placed(socket_shape(p,stop='root' if side=='Root' else 'tip'),tuple(origin),rot)
            q=origin+rot.multVec(V(0,-ro+2,17.5))
            if side=='Root':
                anchor=V(-20,0,q.z-20);rib=web(anchor,q,4,18);root=root.fuse(Part.makeBox(4,56,6,V(-22,-28,q.z-20)))
            else:
                anchor=V(x-(8 if abs(q.y)>1e-6 else 12),8 if q.y>1e-6 else -8 if q.y<-1e-6 else 0,-5);elbow=V(b.x+13,q.y,q.z-2)
                rib=web(anchor,elbow,4,18).fuse(web(elbow,q,4,18))
            if side=='Root':root=root.fuse(shell).fuse(rib)
            else:motor=motor.fuse(shell).fuse(rib)
            ports.append((side,j,origin,d,rot))
    for side,j,origin,d,rot in ports:
        s=root if side=='Root' else motor
        # Retain caps and their seats, with real split gap and through-bolt holes.
        s=s.cut(placed(socket_shape(p,upper=True),tuple(origin),rot))
        a=V(*starts[j]);b=V(*ends[j])
        start=a-d*.3 if side=='Root' else b-d*100
        length=150 if side=='Root' else 100+p['end_pad_thickness_mm']+.125
        s=s.cut(Part.makeCylinder(p['socket_bore_mm']/2,length,start,d))
        s=s.cut(Part.makeCylinder(v['di']/2+.1,(b-a).Length+(90 if side=='Root' else 46),a-d*40,d))
        for sign in [-1,1]:
            pos=origin+rot.multVec(V(sign*p['ear_x_mm'],22,17.5));s=s.cut(Part.makeCylinder(2.25,50,pos,rot.multVec(V(0,-1,0))))
        if side=='Root':root=s
        else:motor=s
    for dx,y in [(25,0),(-25,0),(0,25),(0,-25)]:
        motor=motor.cut(Part.makeCylinder(3.3,30,V(x+dx,y,-20))).cut(Part.makeCylinder(5.5,9,V(x+dx,y,-15)))
    motor=motor.cut(Part.makeCylinder(7,30,V(x,0,-20)))
    root=clean(root);motor=clean(motor)
    
    assert root.isValid() and len(root.Solids)==1,('Root',v['id'],len(root.Solids))
    assert motor.isValid() and len(motor.Solids)==1,('Motor',v['id'],len(motor.Solids))
    assert motor.BoundBox.ZMax<1e-5,(v['id'],motor.BoundBox.ZMax)
    return root,motor
