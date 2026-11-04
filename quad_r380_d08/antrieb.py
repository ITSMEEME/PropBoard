"""Stationary annular BEM screen using the actual D06 blade stations, assumed polars."""
from pathlib import Path
import math,json,csv
import numpy as np
H=Path(__file__).resolve().parent;R=H.parent;O=H/'Ausgabe';P=json.loads((R/'quad_r380_d06/parameter.json').read_text());stations=np.array(P['sections_r_chord_pitch_tc_axis']);B=3;radius=.38

def rotor(rpm,rho=1.225,clmax=1.2,cd0=.015,slope=5.7,N=120):
 dr=(radius-.134)/N;r=np.linspace(.134+dr/2,radius-dr/2,N);c=np.interp(r*1000,stations[:,0],stations[:,1])/1000;pitch=np.deg2rad(np.interp(r*1000,stations[:,0],stations[:,2]));omega=rpm*math.pi/30
 def evaluate(vi):
  phi=np.arctan2(vi,omega*r);alpha=pitch-phi+math.radians(2);cl=np.clip(slope*alpha,-clmax,clmax);cd=cd0+.02*cl*cl;dynamic=.5*rho*((omega*r)**2+vi**2);L=dynamic*c*cl;drag=dynamic*c*cd;dt=B*(L*np.cos(phi)-drag*np.sin(phi));dq=B*(L*np.sin(phi)+drag*np.cos(phi))*r;f=B/2*(radius-r)/(r*np.maximum(np.sin(phi),1e-5));loss=np.maximum(2/math.pi*np.arccos(np.clip(np.exp(-f),0,1)),.05);res=dt-4*math.pi*rho*r*loss*vi*vi;return res,dt,dq,alpha
 lo=np.zeros(N);hi=np.full(N,omega*radius)
 for _ in range(70):
  mid=(lo+hi)/2;res,*_=evaluate(mid);lo=np.where(res>0,mid,lo);hi=np.where(res>0,hi,mid)
 res,dt,dq,alpha=evaluate((lo+hi)/2);thrust=float(sum(dt)*dr);torque=float(sum(dq)*dr)
 return dict(rpm=rpm,thrust_N=thrust,torque_Nm=torque,shaft_power_W=torque*omega,tip_speed_m_s=omega*radius,max_annulus_residual_N_per_m=float(max(abs(res))),max_abs_alpha_deg=float(max(abs(alpha))*180/math.pi))
polars=[dict(name='low_lift',clmax=.8,cd0=.025,slope=5.0),dict(name='central',clmax=1.2,cd0=.015,slope=5.7),dict(name='high_lift',clmax=1.4,cd0=.012,slope=6.28)]
curves=[];hover=[]
for polar in polars:
 args={k:v for k,v in polar.items() if k!='name'}
 for rpm in [2434,2744,2880,3456,4032,4500,5000,6000,7000]:curves.append(dict(polar=polar['name'],**rotor(rpm,**args)))
 base=rotor(3000,**args)
 for mass in [130,150,175,200]:
  rpm=3000*math.sqrt(mass*9.81/4/base['thrust_N']);p=rotor(rpm,**args);hover.append(dict(mass_kg=mass,polar=polar['name'],**p,ideal_min_supply_V=rpm/40,within_24S_ideal_no_load=rpm<=4032))
a=rotor(4032,N=60);b=rotor(4032,N=120);c=rotor(4032,N=240);assert abs(b['thrust_N']/c['thrust_N']-1)<.01
assert rotor(3000)['shaft_power_W']>rotor(3000)['thrust_N']**1.5/math.sqrt(2*1.225*math.pi*radius**2)
report=dict(method='Stationary annular blade-element/momentum hover with Prandtl tip loss; no swirl or root loss; 134–380 mm lifting span from CAD stations.',polars_measured=False,model_validated=False,assumptions='Cl slope/clipping and Cd polar assumed; +2 degree zero-lift correction for cambered profile; no Reynolds/Mach-dependent polar, interference, ground effect or motor thermal model. Samples above4032rpm are demands,not permitted operation.',curves=curves,hover=hover,mesh_convergence=[a,b,c],motor_24S_no_load_limits_rpm={'empty_3V_cell':2880,'nominal_3_6V_cell':3456,'full_4_2V_cell':4032},ideal_total_hover_power_kW=[dict(mass_kg=m,power_kW=(m*9.81)**1.5/math.sqrt(2*1.225*4*math.pi*.38**2)/1000) for m in [130,150,175,200]],positive_drive_verification=False,scope='This provides a reproducible conditional feasibility check, not a measured R380 map or release. NS52 thrust is not transferred.')
(O/'Antriebsnachweis.json').write_text(json.dumps(report,indent=2))
with (O/'R380_Kennfeld_Annahmen.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=curves[0]);w.writeheader();w.writerows(curves)
for p in hover:
 if p['polar']=='central':print('Hover',p,flush=True)
print('Thrust full ideal',rotor(4032),flush=True)
