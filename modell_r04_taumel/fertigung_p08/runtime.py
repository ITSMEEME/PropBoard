"""P08 isolated servo-linkage motion, exact fixed centre distances, mm/degrees.
Only the dedicated P08 linkage document is driven. Not a flight/contact solver.
"""
import json,math,sys
from pathlib import Path
import FreeCAD as A
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'bewegung'))
import bewegung_runtime as M
V=A.Vector
K=json.loads((Path(__file__).resolve().parent.parent/'simulation/kinematik.json').read_text())

def basis(origin,z,x):
    z=V(*z);z.normalize();x=V(*x);x=x-z*x.dot(z);x.normalize();y=z.cross(x)
    m=A.Matrix();m.A11=x.x;m.A21=x.y;m.A31=x.z;m.A12=y.x;m.A22=y.y;m.A32=y.z;m.A13=z.x;m.A23=z.y;m.A33=z.z
    return A.Placement(V(*origin),A.Rotation(m))
def frame(pos=(0,0,0),rot=None):return A.Placement(V(*pos),rot or A.Rotation())
def transforms(degrees):
    poses=[M.pose_from_servos([v*M.DEG for v in degrees[l*3:l*3+3]],k) for l,k in enumerate(K)]
    err=max(abs(e) for l,k in enumerate(K) for e in M.residual(poses[l],[v*M.DEG for v in degrees[l*3:l*3+3]],k))
    out={};angles=[]
    for l,p in enumerate(poses):
        world=M.local_world(1 if l==0 else -1);sw=M.swash(p)
        out[(l,-1,'swash')]=world.multiply(sw)
        for i,a in enumerate(M.AZ):
            alpha=degrees[l*3+i]*M.DEG;lower=M.stat(p,a);upper=M.servo_end(alpha,a);vec=M.sub(upper,lower);L=M.norm(vec)
            assert abs(L-K[l]['link_lengths_mm'][i])<1e-6
            rad=[math.cos(a),math.sin(a),0];tangent=[-math.sin(a),math.cos(a),0]
            lo=basis(lower,vec,rad);hi=basis(upper,[-x for x in vec],tangent)
            lowstud=frame(lower,sw.Rotation.multiply(M.rotz(a/M.DEG)))
            highrot=M.rotz(a/M.DEG).multiply(A.Rotation(V(0,1,0),degrees[l*3+i]))
            highstud=frame(upper,highrot.multiply(M.rotz(90)))
            horn=frame(M.rz([58.3,0,60],a),highrot)
            entries={'horn':horn,'ball_low':lowstud,'ball_high':highstud,'body_low':lo,'body_high':hi,'cap_low':lo,'cap_high':hi,'rod':lo,'jam_low':lo.multiply(frame((0,0,7))),'jam_high':hi.multiply(frame((0,0,7))),'horn_nut':highstud.multiply(frame((-9.9,0,0),A.Rotation(V(0,1,0),90))),'clamp_bolt':horn.multiply(frame((5.5,-7.5,4.3))),'clamp_nut':horn.multiply(frame((5.5,-7.5,-5.9))),'washer_high':horn.multiply(frame((5.5,-7.5,4))),'washer_low':horn.multiply(frame((5.5,-7.5,-4.3)))}
            for role,pl in entries.items():out[(l,i,role)]=world.multiply(pl)
            for cup,stud in ((lo,lowstud),(hi,highstud)):
                x=cup.Rotation.multVec(V(1,0,0));sx=stud.Rotation.multVec(V(1,0,0));angles.append(math.degrees(math.acos(max(-1,min(1,x.dot(sx))))))
    return out,err,angles

def update(doc,degrees):
    if len(degrees)!=6:raise ValueError('Six servo angles required')
    transforms_now,error,angles=transforms(degrees)
    for o in doc.Objects:
        if not hasattr(o,'P08_Rolle'):continue
        key=(o.P08_Rotor,o.P08_Index,o.P08_Rolle)
        o.Placement=transforms_now[key].multiply(o.P08_Neutralrahmen.inverse())
    doc.recompute()
    return dict(link_error_mm=error,max_joint_angle_deg=max(angles))
