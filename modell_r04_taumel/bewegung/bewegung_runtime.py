"""FreeCAD M01 motion runtime. Pure Python closed links; no numpy or GUI dependency.

Kinematic animation/replay, not a force solver. Bearing/motor internals are schematic.
"""
import json,math
import FreeCAD as App
V=App.Vector;DEG=math.pi/180

def add(a,b):return [x+y for x,y in zip(a,b)]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(a):return math.sqrt(dot(a,a))
def rz(v,a):
    c,s=math.cos(a),math.sin(a)
    return [c*v[0]-s*v[1],s*v[0]+c*v[1],v[2]]
def tilt(v,x,y):
    x*=DEG;y*=DEG;c,s=math.cos(y),math.sin(y);u=[c*v[0]+s*v[2],v[1],-s*v[0]+c*v[2]];c,s=math.cos(x),math.sin(x)
    return [u[0],c*u[1]-s*u[2],s*u[1]+c*u[2]]
def solve(a,b):
    a=[list(row)+[v] for row,v in zip(a,b)];n=len(b)
    for i in range(n):
        k=max(range(i,n),key=lambda j:abs(a[j][i]));a[i],a[k]=a[k],a[i]
        if abs(a[i][i])<1e-12:raise ValueError('Singular closed-link mechanism')
        v=a[i][i]
        for j in range(i,n+1):a[i][j]/=v
        for k in range(n):
            if k==i:continue
            v=a[k][i]
            for j in range(i,n+1):a[k][j]-=v*a[i][j]
    return [r[n] for r in a]
AZ=[a*DEG for a in (60,180,300)]
def stat(p,a):return add([0,0,p[0]],tilt(rz([50.3,0,9.5],a),p[1],p[2]))
def servo_end(alpha,a):return rz([58.3-8*math.cos(alpha),0,60+8*math.sin(alpha)],a)
def residual(p,alpha,k):return [norm(sub(stat(p,a),servo_end(alpha[i],a)))-k['link_lengths_mm'][i] for i,a in enumerate(AZ)]
def pose_from_servos(alpha,k):
    p=list(k['neutral'])
    for _ in range(12):
        r=residual(p,alpha,k)
        if max(map(abs,r))<1e-9:break
        cols=[]
        for j in range(3):
            q=p[:];q[j]+=1e-4;cols.append([(x-y)*1e4 for x,y in zip(residual(q,alpha,k),r)])
        dx=solve([[cols[j][i] for j in range(3)] for i in range(3)],r);p=sub(p,dx)
    if max(map(abs,residual(p,alpha,k)))>1e-6:raise ValueError('Servo link cannot close')
    return p

def horn_ball(theta,a,sign):return rz([32,sign*(9*math.cos(theta)-5.5*math.sin(theta)),9*math.sin(theta)+5.5*math.cos(theta)],a)
def ring_ball(p,a,sign):return add([0,0,p[0]],tilt(rz([32,sign*9,-5.5],a),p[1],p[2]))
def blade_pitch(p,a,sign,guess):
    r=ring_ball(p,a,sign);t=guess
    for _ in range(20):
        d=sub(r,horn_ball(t,a,sign));dh=rz([0,sign*(-9*math.sin(t)-5.5*math.cos(t)),9*math.cos(t)-5.5*math.sin(t)],a)
        den=2*dot(d,dh)
        if abs(den)<1e-9:raise ValueError('Blade toggle/singular configuration')
        dt=(dot(d,d)-225)/den;t+=dt
        if abs(dt)<1e-12:break
    err=abs(norm(sub(r,horn_ball(t,a,sign)))-15)
    if err>1e-6:raise ValueError('Blade link cannot close')
    return t,err

def placement(pos=(0,0,0),rotation=None):return App.Placement(V(*pos),rotation or App.Rotation())
def rotz(a):return App.Rotation(V(0,0,1),a)
def local_world(sign):return placement((0,0,30*sign),App.Rotation() if sign>0 else App.Rotation(V(0,0,1),180).multiply(App.Rotation(V(1,0,0),180)))
def swash(p):return placement((0,0,p[0]),App.Rotation(V(1,0,0),p[1]).multiply(App.Rotation(V(0,1,0),p[2])))
def link_place(a,b,trim):
    d=V(*sub(b,a));u=d/d.Length
    return App.Placement(V(*a)+u*trim,App.Rotation(V(0,0,1),u))

def motion_state(servo_deg,angles,kine):
    poses=[];pitches=[];error=0
    for l,k in enumerate(kine):
        alpha=[v*DEG for v in servo_deg[l*3:l*3+3]];p=pose_from_servos(alpha,k);poses.append(p);ths=[]
        for j in range(8):
            a=(angles[l]+j*45)*DEG;t,e=blade_pitch(p,a,k['sign'],(14 if l==0 else 16.7)*DEG);ths.append(t);error=max(error,e)
        pitches.append(ths);error=max(error,max(map(abs,residual(p,alpha,k))))
    return poses,pitches,error

def apply(doc,controller,servo_deg,angles,body_pos=(0,0,0),body_euler=(0,0,0),cg=(0,0,0),flight=False):
    kine=json.loads(controller.KinematikJSON);poses,pitches,error=motion_state(servo_deg,angles,kine)
    body_rot=rotz(body_euler[2]).multiply(App.Rotation(V(0,1,0),body_euler[1])).multiply(App.Rotation(V(1,0,0),body_euler[0]))
    body=placement([1000*x for x in body_pos],body_rot).multiply(placement([-1000*x for x in cg])) if flight else App.Placement()
    for o in doc.Objects:
        if not hasattr(o,'MotionRole'):continue
        role=o.MotionRole
        if role=='fixed':o.Placement=body.multiply(o.RestPlacement);continue
        l=int(o.Rotor);s=1 if l==0 else -1;a=angles[l];p=poses[l];S=swash(p);base=local_world(s);idx=int(o.MotionIndex)
        pl=App.Placement()
        if role=='rotor':pl=placement(rotation=rotz(a))
        elif role in ('blade','pitch_horn'):pl=placement(rotation=rotz(a+idx*45).multiply(App.Rotation(V(1,0,0),s*pitches[l][idx]/DEG)))
        elif role=='hub_pin':pl=placement(rotation=rotz(a+idx*45))
        elif role=='blade_ball':pl=placement(horn_ball(pitches[l][idx],(a+idx*45)*DEG,s))
        elif role=='ring_ball':pl=placement(ring_ball(p,(a+idx*45)*DEG,s))
        elif role=='blade_link':pl=link_place(horn_ball(pitches[l][idx],(a+idx*45)*DEG,s),ring_ball(p,(a+idx*45)*DEG,s),2.7)
        elif role=='swash_rotating':pl=S.multiply(placement(rotation=rotz(a)))
        elif role=='swash_stationary':pl=S
        elif role=='sleeve':pl=placement((0,0,p[0]))
        elif role=='servo_link':pl=link_place(stat(p,AZ[idx]),servo_end(servo_deg[l*3+idx]*DEG,AZ[idx]),2.7)
        elif role in ('servo_horn','servo_shaft'):
            pl=placement(rotation=rotz(AZ[idx]/DEG)).multiply(placement((58.3,0,60),App.Rotation(V(0,1,0),servo_deg[l*3+idx])))
            # Positive alpha raises an inward-pointing horn in the x/z plane.
        elif role=='servo_tip':pl=placement(servo_end(servo_deg[l*3+idx]*DEG,AZ[idx]))
        elif role=='servo_housing':pl=placement(rotation=rotz(AZ[idx]/DEG))
        elif role in ('pinion','motor_bell','motor_shaft'):pl=placement((75.1,0,0),rotz(-6.5*a))
        elif role=='motor_stator':pl=placement((75.1,0,0))
        elif role.startswith('bearing_'):
            # Nominal race split; rolling geometry is illustrative, not manufacturer data.
            which=idx//100;j=idx%100
            z=(-6.5,6.5)[which] if which<2 else 0
            ref=placement((0,0,z)) if which<2 else S
            if role=='bearing_inner':pl=ref
            elif role=='bearing_outer':pl=ref.multiply(placement(rotation=rotz(a)))
            elif role=='bearing_cage':
                rp=18 if which<2 else 25.75;rb=1.2 if which<2 else 1.3
                pl=ref.multiply(placement(rotation=rotz(.5*(1+rb/rp)*a)))
            elif role=='bearing_ball':
                rp=18 if which<2 else 25.75;count=18 if which<2 else 24
                rb=1.2 if which<2 else 1.3;orbit=(j*360/count+.5*(1+rb/rp)*a)*DEG
                pl=ref.multiply(placement((rp*math.cos(orbit),rp*math.sin(orbit),0),rotz(.5*(rp/rb+1)*a)))
        else:raise ValueError('Unknown motion role '+role)
        o.Placement=body.multiply(base).multiply(pl)
    return dict(poses=poses,pitches_deg=[[v/DEG for v in t] for t in pitches],max_link_error_mm=error)

class MotionController:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        if not obj.KinematikJSON:return
        if hasattr(obj,'ServoTyp') and getattr(self,'_servo_type',None)!=obj.ServoTyp:
            from servo_geometrie import housing,shaft
            import Part
            data=json.loads(obj.ServodatenJSON)
            for part in obj.Document.Objects:
                if hasattr(part,'MotionRole') and part.MotionRole in ('servo_housing','servo_shaft'):
                    shape=housing(obj.ServoTyp,data) if part.MotionRole=='servo_housing' else shaft(obj.ServoTyp,data)
                    part.Shape=Part.makeCompound([shape])
                    if part.MotionRole=='servo_housing' and hasattr(part,'Masse_g'):part.Masse_g='69' if obj.ServoTyp=='Savox_SB2271SG' else 'unbekannt'
            self._servo_type=obj.ServoTyp
        if getattr(obj,'ServoTyp','Savox_SB2271SG')=='KST_X15_755X_760us' and obj.Modus not in ('Manuell','Kinematik_Demo'):
            raise ValueError('KST: flight replay unavailable; mass, torque and signal configuration unverified')
        if obj.Modus=='Manuell':
            info=apply(obj.Document,obj,list(obj.Servo_deg),list(obj.Rotorwinkel_deg));obj.MaxGestangefehler_mm=info['max_link_error_mm'];return
        data=json.loads(obj.WiedergabeJSON);frames=data[obj.Modus]['frames'];cg=data[obj.Modus].get('cg_m',[0,0,0]);t=max(frames[0]['t'],min(obj.Zeit_s,frames[-1]['t']))
        import bisect
        i=max(0,min(len(frames)-2,bisect.bisect_right([f['t'] for f in frames],t)-1));a,b=frames[i:i+2];q=(t-a['t'])/max(1e-9,b['t']-a['t'])
        mix=lambda key:[x+(y-x)*q for x,y in zip(a[key],b[key])]
        servo=mix('servoDeg');angles=mix('angles');flight=obj.Modus!='Kinematik_Demo'
        info=apply(obj.Document,obj,servo,angles,mix('p'),mix('euler'),cg,flight);obj.MaxGestangefehler_mm=info['max_link_error_mm']
    def onChanged(self,obj,prop):pass
    def dumps(self):return None
    def loads(self,state):pass
