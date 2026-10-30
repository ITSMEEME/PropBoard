#!/usr/bin/env python3
"""Independent closed-chain kinematics and explicitly conditional servo load model.

Run with the project tools venv. Uses numpy; no CAD regeneration and no changes
in the F01 manufacturing snapshot. CAD inertia is extracted separately.
"""
import csv
import json
import math
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
P=json.loads((HERE.parent/'cad/parameter.json').read_text())
I=json.loads((HERE/'Fluegel_Traegheit.json').read_text())
N=P['blade']['count']; SW=P['swash']; HO=P['horn']; DEG=math.pi/180
L=SW['c_hover_link_len']; arm=HO['arm']; zhorn=HO['ball_z']; radius=HO['r_center']
SERVO_HORN=8.0 # proposal, not a measured product horn
SERVO_PIVOT_Z=P['plate']['rod_top_z']
RSTAT=SW['stat_arm_r']+SW['stud_len']+SW['ball_d']/2


def rz(deg):
    a=deg*DEG;c,s=math.cos(a),math.sin(a)
    return np.array([[c,-s,0],[s,c,0],[0,0,1.]])


def tilt(tx,ty):
    x,y=tx*DEG,ty*DEG;cx,sx=math.cos(x),math.sin(x);cy,sy=math.cos(y),math.sin(y)
    return np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])


def hb(theta,a,k,sign):
    # theta is commanded physical pitch, radians, for either handed rotor.
    return rz(a+360*k/N)@np.array([radius,sign*(arm*math.cos(theta)-zhorn*math.sin(theta)),arm*math.sin(theta)+zhorn*math.cos(theta)])


def dh(theta,a,k,sign):
    return rz(a+360*k/N)@np.array([0,sign*(-arm*math.sin(theta)-zhorn*math.cos(theta)),arm*math.cos(theta)-zhorn*math.sin(theta)])


def rb(pose,a,k,sign):
    return np.array([0,0,pose[0]])+tilt(*pose[1:])@rz(a+360*k/N)@np.array([radius,sign*arm,SW['rot_ball_z']])


def fit_pose(collective,cyclic,phase,sign):
    desired=np.array([(collective+cyclic*math.sin((360*k/N+phase)*DEG))*DEG for k in range(N)])
    balls=[hb(t,0,k,sign) for k,t in enumerate(desired)]
    def residual(x):return np.array([np.linalg.norm(rb(x,0,k,sign)-balls[k])-L for k in range(N)])
    x=np.array([balls[0][2]-SW['rot_ball_z']+L,0.,0.])
    for _ in range(25):
        r=residual(x);J=np.column_stack([(residual(x+np.eye(3)[j]*1e-4)-r)/1e-4 for j in range(3)])
        dx=np.linalg.lstsq(J,-r,rcond=None)[0];x+=dx
        if np.max(np.abs(dx))<1e-8:break
    return x,float(np.max(np.abs(residual(x))))


def forward(pose,a,sign,guess):
    result=[];errors=[]
    for k,t in enumerate(guess):
        point=rb(pose,a,k,sign)
        for _ in range(20):
            delta=point-hb(t,a,k,sign)
            dt=(delta@delta-L*L)/(2*delta@dh(t,a,k,sign))
            t+=dt
            if abs(dt)<1e-12:break
        errors.append(abs(np.linalg.norm(point-hb(t,a,k,sign))-L))
        result.append(t)
    return np.array(result),max(errors)


def stat_ball(pose,ang):
    p=rz(ang)@np.array([RSTAT,0,SW['arm_z0']+SW['arm_t']/2])
    return np.array([0,0,pose[0]])+tilt(*pose[1:])@p


def servo_end(angle,azimuth):
    # Tangential servo shaft. Neutral horn points radially inward.
    return rz(azimuth)@np.array([RSTAT+SERVO_HORN-SERVO_HORN*math.cos(angle),0,
                              SERVO_PIVOT_Z+SERVO_HORN*math.sin(angle)])


def servo_angles(pose,neutral):
    angles=[]
    for ang in SW['servo_angles_deg']:
        length=np.linalg.norm(servo_end(0,ang)-stat_ball(neutral,ang))
        p=stat_ball(pose,ang);a=0.
        for _ in range(20):
            e=servo_end(a,ang);d=e-p
            de=rz(ang)@np.array([SERVO_HORN*math.sin(a),0,SERVO_HORN*math.cos(a)])
            da=(d@d-length*length)/(2*d@de);a-=da
            if abs(da)<1e-12:break
        assert abs(a)<math.pi/3,'servo travel exceeds proposed +/-60 degree model'
        assert abs(np.linalg.norm(servo_end(a,ang)-p)-length)<1e-7
        angles.append(a)
    return np.array(angles)


def actuation_matrix(pose,angles,neutral,sign,a=0):
    # Virtual work: M_servo = (d theta / d alpha)^T M_blade.
    guess=np.full(N,P['pitch_hover_deg'][0 if sign>0 else 1]*DEG)
    theta,_=forward(pose,a,sign,guess)
    Jtheta=np.column_stack([(forward(pose+np.eye(3)[j]*1e-4,a,sign,theta)[0]-
                             forward(pose-np.eye(3)[j]*1e-4,a,sign,theta)[0])/2e-4 for j in range(3)])
    Jalpha=np.column_stack([(servo_angles(pose+np.eye(3)[j]*1e-4,neutral)-
                             servo_angles(pose-np.eye(3)[j]*1e-4,neutral))/2e-4 for j in range(3)])
    assert np.linalg.cond(Jalpha)<100,'ill-conditioned servo geometry'
    return theta,Jtheta@np.linalg.inv(Jalpha)


def main():
    rows=[];worst_error=0.;worst_closure=0.;fit_error=0.;travel=[]
    neutral={s:fit_pose(P['pitch_hover_deg'][0 if s>0 else 1],0,0,s)[0] for s in (1,-1)}
    samples=[]
    for sign in (1,-1):
        for collective in (-2,0,5,10,14,16.7,21):
            for cyclic,phase in [(0,0)]+[(4,p) for p in range(0,360,30)]:
                pose,error=fit_pose(collective,cyclic,phase,sign);fit_error=max(fit_error,error)
                angles=servo_angles(pose,neutral[sign]);travel.append(angles)
                for azimuth in range(0,360,10):
                    requested=np.array([(collective+cyclic*math.sin((azimuth+360*k/N+phase)*DEG))*DEG for k in range(N)])
                    actual,closure=forward(pose,azimuth,sign,requested)
                    error_deg=float(np.max(np.abs(actual-requested))/DEG)
                    worst_error=max(worst_error,error_deg);worst_closure=max(worst_closure,closure)
                    rows.append([sign,collective,cyclic,phase,azimuth,*pose,error_deg,closure])
                samples.append((sign,collective,cyclic,phase,pose,angles))
    assert len(rows)==6552,len(rows)
    assert worst_closure<1e-7
    # Zero cyclic gives a constant physical pitch with fixed plate pose.
    for sign in (1,-1):
        t,_=forward(neutral[sign],37,sign,np.full(N,P['pitch_hover_deg'][0 if sign>0 else 1]*DEG))
        assert np.max(np.abs(t/DEG-P['pitch_hover_deg'][0 if sign>0 else 1]))<1e-6
    # Consistency of independent inverse/forward Jacobian, not a rotor strength test.
    jacobian_error=0.
    pose=neutral[1];angles=servo_angles(pose,neutral[1]);theta,J=actuation_matrix(pose,angles,neutral[1],1)
    delta=np.array([.0001,-.00005,.00002]);trial=pose+delta
    th2,_=forward(trial,0,1,theta)
    pred=J@(servo_angles(trial,neutral[1])-angles)
    jacobian_error=float(np.max(np.abs((th2-theta)-pred)))
    assert jacobian_error<1e-7
    rp=P['pin']['z_offset']/1000
    mass=I['mass_kg'];rcg=I['cg_mm'][0]/1000
    inertia_difference=I['delta_I_about_radial_pitch_axis_kgm2']
    pitch_inertia=I['Ixx_about_pitch_axis_kgm2']
    # Precompute independent mechanical Jacobians once; load assumptions can
    # then be varied without repeating geometry solves.
    mechanical=[]
    for sign,collective,cyclic,phase,pose,angles in samples:
        for azimuth in (0,11.25,22.5,33.75):
            theta,J=actuation_matrix(pose,angles,neutral[sign],sign,azimuth)
            eps=1e-3
            tp=forward(pose,azimuth+eps/DEG,sign,theta)[0]
            tm=forward(pose,azimuth-eps/DEG,sign,theta)[0]
            curvature=(tp-2*theta+tm)/eps**2
            mechanical.append((sign,collective,cyclic,phase,azimuth,theta,J,curvature))
    source_points=json.loads((HERE/'Betriebspunkte_H01.json').read_text())['scenarios']
    cases=[]
    for scenario in source_points:
        for point_name,label in [('hover','hover_model'),('tw2','tw2_model'),('tw2','overspeed_screening_not_operating_point')]:
            point=scenario[point_name]
            scale=1.2 if label.startswith('overspeed') else 1.
            rpm=point['rpm']*scale
            omega=rpm*2*math.pi/60;centrifugal=mass*omega**2*rcg
            for mu in (0.,.03,.1,.2):
                maximum=0.;source=None
                for sign,collective,cyclic,phase,azimuth,theta,J,curvature in mechanical:
                    mean_thrust=point['upper_thrust_N'] if sign>0 else point['lower_thrust_N']
                    aerodynamic=mean_thrust*scale**2/N*(P['blade']['chord']/1000)*.25
                    cf=np.abs(inertia_difference*omega**2*np.sin(theta)*np.cos(theta))
                    oscillation=pitch_inertia*omega**2*np.abs(curvature)
                    friction=mu*centrifugal*rp
                    # Bound independent signs under these assumptions. No
                    # favorable cancellation or false one-blade / three split.
                    blade_bound=cf+aerodynamic+oscillation+friction
                    torque=np.abs(J).T@blade_bound
                    if max(torque)>maximum:
                        maximum=float(max(torque));source={'side':sign,'collective_deg':collective,
                            'cyclic_deg':cyclic,'phase_deg':phase,'azimuth_deg':azimuth}
                cases.append({'scenario':scenario['name'],'vehicle_mass_kg':scenario['mass_kg'],
                    'assumed_servo_mass_g':scenario['assumed_servo_mass_g'],'label':label,'rpm':rpm,
                    'mu_assumed':mu,'centrifugal_per_blade_N':centrifugal,
                    'blade_friction_moment_Nmm':mu*centrifugal*rp*1000,'max_servo_torque_Nm':maximum,
                    'max_servo_torque_kgcm':maximum/.0980665,'with_factor_2_kgcm':2*maximum/.0980665,
                    'critical_command':source})
    positions=np.array(travel)/DEG
    report={'status':'INDEPENDENT_MECHANISM_AUDIT_CONDITIONAL_LOADS_NOT_RELEASE',
            'kinematics':{'samples':len(rows),'blade_closure_checks':len(rows)*N,
              'max_closed_link_error_mm':worst_closure,'max_requested_pitch_error_deg':worst_error,
              'max_prescribed_inverse_fit_error_mm':fit_error,
              'servo_min_deg':positions.min(axis=0).tolist(),'servo_max_deg':positions.max(axis=0).tolist(),
              'servo_horn_proposal_mm':SERVO_HORN,'servo_pivot_radius_proposal_mm':RSTAT+SERVO_HORN,
              'servo_pivot_height_proposal_mm':SERVO_PIVOT_Z,'jacobian_linearization_error_rad':jacobian_error},
            'load_sensitivity':cases,
            'assumptions':{'blade_mass_distribution':'CAD homogeneous effective density; actual infill not measured',
              'friction':'Coulomb mu * centrifugal blade force * 4.8 mm sliding-retention radius; sensitivity only',
              'aerodynamic':'BEMT mean rotor thrust / 8 blades, quarter-chord arm; cyclic airload variation and true section moment not resolved',
              'cyclic_inertia':'Ixx * omega^2 * numerical second derivative of the closed-link physical blade pitch versus rotor azimuth',
              'servo':'new tangential shaft orientation and 8 mm horn; F01 has no real servo horn or mounting',
              'excluded':'bearing drag, preload, stiction peak, impacts, structural flexibility, fatigue, control stability'},
            'findings':['F01 does not model a fixed-length servo linkage with actual horn motion.',
                        'Servo shaft must be tangent to produce radial-vertical horn motion; placeholder does not establish this.',
                        'Pitch-root centrifugal sliding friction prevents unconditional microservo selection.',
                        'Eight fixed blade links and a rigid swashplate cannot reproduce the prescribed sinusoid exactly at finite pitch.',
                        'Servo does not have to sweep once per rotor revolution for steady cyclic; rotating links do.']}
    (HERE/'Mechanikpruefung.json').write_text(json.dumps(report,indent=2))
    with (HERE/'Kinematik_Sweep.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['rotor_sign','collective_deg','cyclic_deg','phase_deg','azimuth_deg','c_mm','tx_deg','ty_deg','max_pitch_deviation_deg','closure_error_mm']);w.writerows(rows)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
