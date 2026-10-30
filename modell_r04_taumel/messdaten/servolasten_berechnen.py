#!/usr/bin/env python3
"""Updated 69 g Savox requirement sweep, using full eight-blade virtual work.

Reuses independent mechanism equations, leaves historical H01 reports intact.
"""
import sys,json,math
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'mechanik'));import pruefen as K
points=json.loads((H.parent/'aerodynamik/Ausgabe/Betriebspunkte_Savox.json').read_text())['scenarios']
rows=[];mechanical=[]
for sign in (1,-1):
    neutral=K.fit_pose(14 if sign==1 else 16.7,0,0,sign)[0]
    for collective in (-2,0,5,10,14,16.7,21):
        for cyclic,phase in [(0,0)]+[(4,p) for p in range(0,360,30)]:
            pose,_=K.fit_pose(collective,cyclic,phase,sign);angles=K.servo_angles(pose,neutral)
            for az in (0,11.25,22.5,33.75):
                theta,J=K.actuation_matrix(pose,angles,neutral,sign,az);eps=1e-3;tp=K.forward(pose,az+eps/K.DEG,sign,theta)[0];tm=K.forward(pose,az-eps/K.DEG,sign,theta)[0]
                mechanical.append((sign,collective,cyclic,phase,az,theta,np.abs(J),(tp-2*theta+tm)/eps**2))
for scenario in points:
    for stage in ('hover','tw2'):
        p=scenario[stage];omega=p['rpm']*2*math.pi/60;F=K.I['mass_kg']*K.I['cg_mm'][0]/1000*omega**2
        for mu in (0,.03,.1,.2):
            maximum=0;critical=None
            for sign,col,cyc,phase,az,theta,J,curv in mechanical:
                thrust=p['upper_thrust_N'] if sign==1 else p['lower_thrust_N'];aero=thrust/8*.03*.25
                bound=np.abs(K.I['delta_I_about_radial_pitch_axis_kgm2']*omega**2*np.sin(theta)*np.cos(theta))+K.I['Ixx_about_pitch_axis_kgm2']*omega**2*np.abs(curv)+mu*F*.0048+aero
                torque=J.T@bound;v=float(max(torque))
                if v>maximum:maximum=v;critical=dict(rotor=sign,collective=col,cyclic=cyc,phase=phase,azimuth=az)
            required=2*maximum;rows.append(dict(aero_model=scenario['name'],stage=stage,rpm=p['rpm'],mu_assumed=mu,centrifugal_load_per_blade_N=F,required_each_servo_Nm_with_factor2=required,required_kgcm_with_factor2=required/.0980665,advertised_7_4V_ratio=1.96133/required,advertised_6V_ratio=1.4709975/required,critical=critical,aero_final_fallback_fraction=p['final_section_fallback_fraction']))
out=dict(status='CALCULATED_REQUIREMENTS_NOT_A_SERVO_CONTINUOUS_LOAD_APPROVAL',mass_kg=points[0]['mass_kg'],mechanical_states=len(mechanical),results=rows,source='Independent closed-link 8-blade/3-servo Jacobian, CAD homogeneous blade inertia, supplied 69 g Savox specs',limitations=['Friction mu is unknown; sweep values are assumptions, not measured PA-CF coefficients','Advertised dynamic torque is not verified stall torque or continuous rating; ratios are screening numbers only','Quarter-chord mean-thrust aerodynamic arm; XFOIL Cm and cyclic airloads not included in this load bound','New servo brackets, BEC, bearing friction, preload, stiction and thermal limits not included','XFOIL TW2 cases can include explicitly reported fallback sections'])
(H/'Servolasten_Savox.json').write_text(json.dumps(out,indent=2));print('Full Jacobian states',len(mechanical))
for r in rows:
    if r['aero_model']=='SIMPLIFIED_HISTORICAL' and r['stage']=='tw2':print('mu',r['mu_assumed'],'required kgcm',round(r['required_kgcm_with_factor2'],2),'ratio at 7.4V',round(r['advertised_7_4V_ratio'],2))
