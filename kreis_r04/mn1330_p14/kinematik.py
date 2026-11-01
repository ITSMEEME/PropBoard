"""P14 closed linkage geometry, independent of CAD and motor power assumptions."""
import math,json
from pathlib import Path
H=Path(__file__).resolve().parent
D=math.pi/180
def rz(v,a):
    c,s=math.cos(a),math.sin(a);x,y,z=v;return [c*x-s*y,s*x+c*y,z]
def tilt(v,x,y):
    a,b,c=v;u=math.cos(y)*a+math.sin(y)*c;w=-math.sin(y)*a+math.cos(y)*c
    return [u,math.cos(x)*b-math.sin(x)*w,math.sin(x)*b+math.cos(x)*w]
def dist(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def derive(c):
    g=c['geometry'];n=g['blades_per_rotor'];h=math.pi/n
    assert isinstance(n,int) and 4<=n<=12 and n%2==0,'Gerade Blattzahl4..12'
    assert 1<=g['lift_units']<=4 and int(g['lift_units'])==g['lift_units']
    root=max(g['root_min_radius_mm'],(g['root_housing_radius_mm']+g['root_clearance_mm'])/math.sin(h),4+(g['root_housing_radius_mm']+g['root_phase_arm_half_width_mm']+g['root_clearance_mm'])/math.tan(h))
    blade=root+g['blade_root_offset_mm'];assert g['rotor_radius_mm']-blade>=350
    assert 115<=g['chord_mm']<=145 and .10<=g['airfoil_tc']<=.16
    assert 650<=g['rotor_radius_mm']<=800 and 360<=g['rotor_spacing_mm']<=440
    level=g['rotor_spacing_mm']/2;upper=[root-20,g['pitch_lever_mm']*math.cos(g['neutral_pitch_deg']*D),level+g['pitch_lever_mm']*math.sin(g['neutral_pitch_deg']*D)]
    delta=math.atan2(upper[1],upper[0]);lower=[g['swash_joint_r_mm']*math.cos(delta),g['swash_joint_r_mm']*math.sin(delta),g['swash_z_mm']]
    sl=[g['servo_swash_x_mm'],g['servo_joint_y_mm'],g['swash_z_mm']-20]
    se=[g['servo_r_mm']-g['servo_horn_mm']*math.cos(g['servo_neutral_deg']*D),g['servo_joint_y_mm'],g['servo_z_mm']+g['servo_horn_mm']*math.sin(g['servo_neutral_deg']*D)]
    count=g['lift_units'];centres=[[0.,0.,0.]]
    if count>1:
        r=(2*g['rotor_radius_mm']+g['unit_disk_clearance_mm'])/(2*math.sin(math.pi/count))
        centres=[rz([r,0,0],2*math.pi*i/count) for i in range(count)]
    vv=[lower[i]-upper[i] for i in range(3)];bb=[-vv[2],0,vv[0]];ll=dist(bb,[0,0,0]);bb=[t/ll for t in bb]
    pin=tilt(bb,-g['neutral_pitch_deg']*D,0)
    ur=math.hypot(upper[0],upper[1]);lb=[upper[2]-lower[2],0,g['swash_joint_r_mm']-ur];ll=dist(lb,[0,0,0]);lb=[v/ll for v in lb]
    return dict(root_r_mm=root,blade_root_mm=blade,blade_span_mm=g['rotor_radius_mm']-blade,level_mm=level,pitch_link_length_mm=dist(upper,lower),pitch_joint_delta_deg=delta/D,servo_link_length_mm=dist(sl,se),unit_centres_mm=centres,root_cassette_tip_clearance_mm=2*root*math.sin(h)-2*g['root_housing_radius_mm'],phase_pin_r_mm=max(185,root+86),pitch_pin_axis_local=pin,pitch_lower_pin_axis=lb,production_ready=False)
def bisect_roots(f,lo,hi,guess):
    roots=[];x0=lo;y0=f(x0)
    for i in range(1,81):
        x1=lo+(hi-lo)*i/80;y1=f(x1)
        if y0*y1<=0:
            a,b=x0,x1
            for _ in range(35):
                m=(a+b)/2
                if f(a)*f(m)<=0:b=m
                else:a=m
            roots.append((a+b)/2)
        x0,y0=x1,y1
    if not roots:raise ValueError('Anlenkung ausserhalb Stellbereich')
    return min(roots,key=lambda r:abs(r-guess))
def solve(c,collective=0,tx=0,ty=0,rotor_angle=0):
    g=c['geometry'];q=derive(c);x,y=tx*D,ty*D;sw=g['swash_z_mm']+collective
    # One lower revolute clevis constrains the stationary ring phase. Other legs
    # have spherical ends. The phase change is solved, never assumed zero.
    gamma=0.
    for _ in range(10):
        def fy(a):return tilt(rz([g['servo_swash_x_mm'],g['servo_joint_y_mm'],-20],a),x,y)[1]-g['servo_joint_y_mm']
        err=fy(gamma);df=(fy(gamma+1e-6)-err)/1e-6;gamma-=err/df
    servo=[];servo_points=[]
    for az in [0,120,240]:
        a=az*D;upper=tilt(rz([g['servo_swash_x_mm'],g['servo_joint_y_mm'],-20],a+gamma),x,y);upper[2]+=sw
        def endpoint(alpha):return rz([g['servo_r_mm']-g['servo_horn_mm']*math.cos(alpha),g['servo_joint_y_mm'],g['servo_z_mm']+g['servo_horn_mm']*math.sin(alpha)],a)
        error=lambda alpha:dist(endpoint(alpha),upper)-q['servo_link_length_mm']
        alpha=bisect_roots(error,g['servo_min_deg']*D,g['servo_max_deg']*D,g['servo_neutral_deg']*D)
        servo.append(alpha/D);servo_points.append([endpoint(alpha),upper])
    pitches=[];points=[]
    for i in range(g['blades_per_rotor']):
        a=(i*360/g['blades_per_rotor']+rotor_angle)*D
        lower=tilt(rz([g['swash_joint_r_mm'],0,0],a+q['pitch_joint_delta_deg']*D),x,y);lower[2]+=sw
        def end(t):
            v=rz([q['root_r_mm']-20,g['pitch_lever_mm']*math.cos(t),g['pitch_lever_mm']*math.sin(t)],a);v[2]+=q['level_mm'];return v
        error=lambda t:dist(end(t),lower)-q['pitch_link_length_mm']
        t=bisect_roots(error,-10*D,35*D,g['neutral_pitch_deg']*D)
        pitches.append(t/D);points.append([lower,end(t)])
    return dict(pitches_deg=pitches,servo_deg=servo,servo_points_mm=servo_points,pitch_points_mm=points,stationary_phase_deg=gamma/D,swash_z_mm=sw,tilt_deg=[tx,ty])
if __name__=='__main__':
    c=json.loads((H/'parameter.json').read_text());print(json.dumps(dict(derived=derive(c),neutral=solve(c)),indent=2))
