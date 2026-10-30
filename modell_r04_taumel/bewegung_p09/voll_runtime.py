"""One closed kinematic chain from six real servo outputs to sixteen blades.
P09 dimensions, mm/degrees. Transform validation happens before any mutation.
"""
import json,math,sys,importlib.util
from pathlib import Path
import FreeCAD as A
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'bewegung'))
import bewegung_runtime as M
spec=importlib.util.spec_from_file_location('_p09_servolinks',H.parent/'fertigung_p08/runtime.py');S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
V=A.Vector;RADIUS=33.;K=S.K

def horn_ball(t,a,sign):return M.rz([RADIUS,sign*(9*math.cos(t)-5.5*math.sin(t)),9*math.sin(t)+5.5*math.cos(t)],a)
def ring_ball(p,a,sign):return M.add([0,0,p[0]],M.tilt(M.rz([RADIUS,sign*9,-5.5],a),p[1],p[2]))
def pitch(p,a,sign,guess):
    r=ring_ball(p,a,sign);t=guess
    for _ in range(30):
        delta=M.sub(r,horn_ball(t,a,sign));dh=M.rz([0,sign*(-9*math.sin(t)-5.5*math.cos(t)),9*math.cos(t)-5.5*math.sin(t)],a)
        den=2*M.dot(delta,dh)
        if abs(den)<1e-10:raise ValueError('Blattgestaenge in Strecklage')
        step=(M.dot(delta,delta)-225)/den;t+=step
        if abs(step)<1e-12:break
    err=abs(M.norm(M.sub(r,horn_ball(t,a,sign)))-15)
    if err>1e-6 or not(-10*M.DEG<t<40*M.DEG):raise ValueError('Blattgestaenge ausserhalb loesbarem Stellbereich')
    return t,err

def state(servos,angles):
    if len(servos)!=6 or len(angles)!=2:raise ValueError('Sechs Servo- und zwei Rotorwinkel erforderlich')
    if not all(math.isfinite(v) for v in list(servos)+list(angles)):raise ValueError('Winkel muessen endlich sein')
    servoframes,err,joint_angles=S.transforms(servos)
    poses=[M.pose_from_servos([v*M.DEG for v in servos[l*3:l*3+3]],k) for l,k in enumerate(K)]
    out={};pitches=[];endpoint_pairs=[]
    for (l,i,role),pl in servoframes.items():out[f'p08:{l}:{i}:{role}']=pl
    for l,p in enumerate(poses):
        sign=1 if l==0 else -1;world=M.local_world(sign);sw=M.swash(p);a=angles[l]
        out[f'rotor:{l}']=world.multiply(M.placement(rotation=M.rotz(a)))
        out[f'swash:{l}']=world.multiply(sw)
        out[f'swashrot:{l}']=world.multiply(sw).multiply(M.placement(rotation=M.rotz(a)))
        out[f'sleeve:{l}']=world.multiply(M.placement((0,0,p[0])))
        out[f'pinion:{l}']=world.multiply(M.placement((75.1,0,0),M.rotz(-6.5*a)))
        ps=[]
        for i in range(3):
            rot=M.rotz((60,180,300)[i]).multiply(A.Rotation(V(0,1,0),servos[l*3+i]))
            out[f'output:{l}:{i}']=world.multiply(M.placement(M.rz([58.3,0,60],M.AZ[i]),rot))
        for j in range(8):
            az=(a+j*45)*M.DEG;t,e=pitch(p,az,sign,(14 if l==0 else 16.7)*M.DEG);ps.append(t/M.DEG);err=max(err,e)
            blade_rot=M.rotz(az/M.DEG).multiply(A.Rotation(V(1,0,0),sign*t/M.DEG))
            out[f'blade:{l}:{j}']=world.multiply(M.placement(rotation=blade_rot))
            out[f'pin:{l}:{j}']=world.multiply(M.placement(rotation=M.rotz(az/M.DEG)))
            low=horn_ball(t,az,sign);high=ring_ball(p,az,sign);vec=M.sub(high,low);rad=[math.cos(az),math.sin(az),0]
            lo=S.basis(low,vec,rad);hi=S.basis(high,[-v for v in vec],rad)
            lowerstud=M.placement(low,blade_rot);upperstud=M.placement(high,sw.Rotation.multiply(M.rotz(az/M.DEG)))
            for role,pl in [('stud_low',lowerstud),('stud_high',upperstud),('body_low',lo),('body_high',hi),('cap_low',lo),('cap_high',hi),('rod',lo)]:out[f'link:{l}:{j}:{role}']=world.multiply(pl)
            endpoint_pairs.append(dict(rotor=l,blade=j,low=world.multVec(V(*low)),high=world.multVec(V(*high))))
        pitches.append(ps)
    return dict(frames=out,poses=poses,pitches=pitches,max_error=err,servo_joint_angles=joint_angles,endpoints=endpoint_pairs)

def apply(doc,servos,angles,recompute=True):
    current=state(servos,angles) # Atomic: reject unsolvable input before changing geometry.
    if recompute:
        ctl=doc.getObject('P09_Animation')
        if ctl is not None:
            ctl.Modus='Manuell';ctl.Servo_deg=list(servos);ctl.Rotor_deg=list(angles)
    for o in doc.Objects:
        if not hasattr(o,'P09_Rahmen') or o.P09_Rahmen=='fixed':continue
        o.Placement=current['frames'][o.P09_Rahmen].multiply(o.P09_Neutralrahmen.inverse())
    if recompute:doc.recompute()
    return current

def demo(t):
    # Periodic, verified mechanical demonstration; not a flight replay for SB2270.
    duration=8.;t=max(0,float(t))%duration;phase=2*math.pi*t/duration
    amplitude=4*math.sin(math.pi*t/duration)**2
    servos=[amplitude*math.sin(phase+(i%3)*2*math.pi/3) for i in range(6)]
    return servos,[45*t,45*t]

class Controller:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        if obj.Modus=='Demo':servos,angles=demo(obj.Zeit_s)
        else:servos,angles=list(obj.Servo_deg),list(obj.Rotor_deg)
        try:
            r=apply(obj.Document,servos,angles,False)
            obj.Gelenkfehler_mm=r['max_error'];obj.Blattpitch_deg=[x for v in r['pitches'] for x in v]
            obj.Status='Kinematik geschlossen; keine Fertigungs-/Flugfreigabe'
        except ValueError as e:obj.Status='Stellung verworfen: '+str(e)
    def onChanged(self,obj,prop):pass
    def dumps(self):return None
    def loads(self,state):pass
