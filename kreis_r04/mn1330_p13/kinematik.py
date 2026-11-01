#!/usr/bin/env python3
"""Independent link closure and articulated-actuator checks, not a flight simulation."""
import json,math
from pathlib import Path
H=Path(__file__).resolve().parent
def tilt(v,x,y):
    cx,sx=math.cos(x),math.sin(x);cy,sy=math.cos(y),math.sin(y)
    a,b,c=v;a,c=cy*a+sy*c,-sy*a+cy*c
    return a,cx*b-sx*c,sx*b+cx*c
def rz(v,a):
    x,y,z=v;c,s=math.cos(a),math.sin(a);return c*x-s*y,s*x+c*y,z
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def norm(v):return math.sqrt(sum(x*x for x in v))
def calc(config):
    p=config['parameters'];m=config['mechanics'];level=p['level_spacing']/2;sw=m['swash_z'];theta0=math.radians(p['pitch_neutral'])
    upper=(m['pitch_lever_x'],m['pitch_lever_r']*math.cos(theta0),level+m['pitch_lever_r']*math.sin(theta0))
    delta=math.atan2(upper[1],upper[0]);lower=(m['swash_joint_r']*math.cos(delta),m['swash_joint_r']*math.sin(delta),sw)
    length=norm(sub(upper,lower));results=[];failures=[];max_gimbal=0;max_pin_x=0;strokes=[];max_closure=0
    scissor_spans={'stationary':[],'rotating':[]}
    for collective in [m['collective_min'],-2,0,m['collective_max']]:
        for amount in [0,m['cyclic_tilt_deg']/2,m['cyclic_tilt_deg']]:
            for direction in range(0,360,45):
                tx=math.radians(amount)*math.cos(math.radians(direction));ty=math.radians(amount)*math.sin(math.radians(direction))
                for phase in range(0,360,5):
                    a=math.radians(phase)
                    sa=a+math.radians(70)
                    moved=tilt(rz((83,0,-25),sa),tx,ty)
                    moved=(moved[0],moved[1],moved[2]+sw+collective)
                    fixed=rz((110,0,120),sa)
                    scissor_spans['rotating'].append(norm(sub(fixed,moved)))
                    b=tilt((m['swash_joint_r']*math.cos(a+delta),m['swash_joint_r']*math.sin(a+delta),0),tx,ty)
                    b=(b[0],b[1],b[2]+sw+collective)
                    def error(t):
                        u=rz((m['pitch_lever_x'],m['pitch_lever_r']*math.cos(t),0),a)
                        u=(u[0],u[1],level+m['pitch_lever_r']*math.sin(t))
                        return norm(sub(u,b))-length
                    lo,hi=map(math.radians,[p['pitch_min'],p['pitch_max']])
                    if error(lo)*error(hi)>0:
                        failures.append(dict(collective=collective,tilt=amount,direction=direction,phase=phase));continue
                    for _ in range(45):
                        mid=(lo+hi)/2
                        if error(lo)*error(mid)<=0:hi=mid
                        else:lo=mid
                    results.append(math.degrees((lo+hi)/2))
                for phase in [0,120,240]:
                    a=math.radians(phase)
                    b=tilt(rz((82,22,-32),a),tx,ty);b=(b[0],b[1],b[2]+sw+collective)
                    base=rz((82,0,30),a);d=rz(sub(b,base),-a)
                    vz=math.sqrt(sum(x*x for x in d)-22**2);stroke=vz-70
                    beta=math.asin(d[0]/vz);t=math.sqrt(vz*vz-d[0]*d[0]);alpha=math.atan2(d[2],d[1])-math.atan2(t,22)
                    # R_x(alpha)R_y(beta) reconstructs the joint position from the actuator.
                    reconstructed=tilt((0,22,vz),alpha,beta)
                    closure=norm(sub(reconstructed,d));max_closure=max(max_closure,closure)
                    strokes.append(stroke);max_gimbal=max(max_gimbal,math.degrees(math.hypot(alpha,beta)))
                    max_pin_x=max(max_pin_x,abs(13*math.sin(beta)))
                moved=tilt(rz((66,0,-40),math.radians(70)),tx,ty)
                moved=(moved[0],moved[1],moved[2]+sw+collective)
                scissor_spans['stationary'].append(norm(sub(rz((40,0,65),math.radians(70)),moved)))
    # Neutral12-degree link must close independently of the numerical root finder.
    assert abs(norm(sub(upper,lower))-length)<1e-12
    assert max_closure<1e-8
    assert not failures,failures[:5]
    assert min(strokes)>=-m['actuator_stroke']/2 and max(strokes)<=m['actuator_stroke']/2
    assert max_pin_x<.2 # Ø4 pin within the4.4mm anti-yaw slot
    assert all(5<min(v)<=max(v)<55 for v in scissor_spans.values()),'Scheren außerhalb geometrischer Reichweite der2×30mm-Laschen'
    return dict(passed=True,link_states=len(results),pitch_min_deg=min(results),pitch_max_deg=max(results),
        pitch_link_centres_mm=length,actuator_stroke_range_mm=[min(strokes),max(strokes)],actuator_available_stroke_mm=m['actuator_stroke'],
        maximum_actuator_gimbal_deg=max_gimbal,maximum_antirotation_pin_x_mm=max_pin_x,slot_radial_clearance_mm=.2,
        scissor_endpoint_distance_range_mm={k:[min(v),max(v)] for k,v in scissor_spans.items()},scissor_scope='Dreiecksreichweite2×30mm; keine Freigabe der Gelenklager-Kippwinkel oder Bewegungskollision',
        maximum_joint_closure_error_mm=max_closure,scope='Starrkörper-Gelenkschluss im vorgegebenen Stellraum; keine vollständige BRep-Bewegungskollision, Elastik, Dynamik oder Flugfreigabe')
if __name__=='__main__':
    out=H/'Ausgabe';out.mkdir(exist_ok=True);r=calc(json.loads((H/'parameter.json').read_text()))
    (out/'Kinematik_Pruefung.json').write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n');print(json.dumps(r,ensure_ascii=False))
