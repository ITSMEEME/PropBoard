"""Unilateral vertical-contact landing simulation with rigid heave/pitch/roll body.
Beam-derived arm/leg compliance in series with an assumed Kelvin-Voigt sole.
All stiffness/damping/inertia inputs are hypotheses, not TPU or airframe test data.
Geometry, buckling and small-angle events terminate invalid extrapolation.
"""
from pathlib import Path
import json,math,csv
import numpy as np
from scipy.integrate import solve_ivp
H=Path(__file__).resolve().parents[1];O=H/'Ausgabe/Festigkeit'
cad=json.loads((O/'CAD_Geometrie.json').read_text());spr=json.loads((O/'Federdaten.json').read_text())['cases']

def simulate(c,s,speed=.5,kpad=500.,cpad=0.,pattern='level',mass=160.,gyr=.5,cgxy=(0.,0.),maxstep=.0004,trace=False):
 angles=np.deg2rad([45,135,225,315]);x=(c['foot_centre'][0]+210)/1000;y=c['foot_centre'][1]/1000;xy=np.array([[math.cos(a)*x-math.sin(a)*y,math.sin(a)*x+math.cos(a)*y] for a in angles])-cgxy;B=np.column_stack([np.ones(4),xy]);gaps=np.array({'level':[0,0,0,0],'two_first':[0,0,.010,.010],'one_first':[0,.005,.010,.005]}[pattern]);ks=s['k_vertical_N_mm']*1000;kp=kpad*1000;keq=ks*kp/(ks+kp);Mm=np.array([mass,mass*gyr*gyr,mass*gyr*gyr]);Frame=np.array([[1,xx-cgxy[0],yy-cgxy[1]] for xx,yy in [(-.22,-.22),(-.22,.22),(.22,-.22),(.22,.22)]])
 def contact(z):
  delta=B@z[:3]-gaps
  if cpad==0:F=keq*np.maximum(delta,0);xp=F/kp;xdot=np.zeros(4)
  else:
   xp=np.maximum(z[6:10],0);F=ks*np.maximum(delta-xp,0);xdot=(F-kp*xp)/cpad
  return F,xp,xdot,delta
 def ode(t,z):
  F,xp,xdot,d=contact(z);acc=(np.array([mass*9.81,0,0])-B.T@F)/Mm;return np.r_[z[3:6],acc,xdot,(cpad*float(xdot@xdot) if cpad else 0.)]
 def metal(t,z):return .003-float(np.max(contact(z)[1]))
 def frame(t,z):return .046-float(np.max(Frame@z[:3]))
 def angle(t,z):return math.radians(5)-float(np.max(np.abs(z[1:3])))
 def buckle(t,z):return (s['buckling_force_N'] or 1e30)-float(np.max(contact(z)[0]))
 def release(t,z):return float(np.sum(contact(z)[0]))-1e-4
 events=[metal,frame,angle,buckle,release]
 for f in events:f.terminal=True;f.direction=-1
 z=np.zeros(11);z[3]=speed;sol=solve_ivp(ode,[0,.4],z,method='RK45',rtol=2e-8,atol=2e-10,max_step=maxstep,events=events);assert sol.success,sol.message
 observed=np.array([contact(z)[0] for z in sol.y.T]);xp=np.array([contact(z)[1] for z in sol.y.T]);delta=np.array([contact(z)[3] for z in sol.y.T]);vel=sol.y[3:6].T;q=sol.y[:3].T;Uarm=.5*ks*np.sum(np.maximum(delta-xp,0)**2,axis=1);Upad=.5*kp*np.sum(xp**2,axis=1);kin=.5*np.sum(Mm*vel**2,axis=1);balance=kin+Uarm+Upad-mass*9.81*q[:,0]+sol.y[10]-.5*mass*speed**2;norm=max(1,.5*mass*speed**2,float(np.max(mass*9.81*q[:,0])));err=float(np.max(np.abs(balance))/norm);assert err<2e-3,(err,c['variant'],speed,kpad,cpad,pattern)
 termination='time_limit'
 for i,t in enumerate(sol.t_events):
  if len(t):termination=['sole_metal_clearance','central_frame_contact','small_angle_limit','linearized_buckling','first_rebound'][i];break
 full=termination in ['time_limit','first_rebound'];Fmax=float(np.max(observed));peakn=float(np.max(np.sum(observed,axis=1))/(mass*9.81));force_sum=observed.sum(axis=1);minframe=float(np.min(.046-np.max(q@Frame.T,axis=1)));peakstress=Fmax*s['force_unit_response_stress_MPa_N'];out=dict(propeller_index=c['propeller_index'],variant=c['variant'],contact_mode=s['mode'],sink_speed_m_s=speed,pad_k_assumed_N_mm=kpad,pad_c_assumed_Ns_m=cpad,terrain_pattern=pattern,mass_kg=mass,gyration_radius_assumed_m=gyr,cg_xy_m=list(cgxy),arm_k_N_mm=s['k_vertical_N_mm'],end_time_s=float(sol.t[-1]),termination=termination,full_peak_computed=full,max_observed_foot_force_N=Fmax,max_observed_total_load_factor=peakn,max_pad_compression_mm=float(np.max(xp)*1000),minimum_frame_clearance_mm=minframe*1000,max_roll_pitch_deg=float(np.max(np.abs(q[:,1:]))*180/math.pi),equivalent_arm_stress_demand_MPa=peakstress,required_longitudinal_allowable_factor1p5_MPa=1.5*peakstress,linear_arm_strain_flag=peakstress/50000>.005,energy_balance_relative_error=err,remaining_kinetic_energy_J=float(kin[-1]),required_static_ground_mu=s['required_ground_mu'],material_verified=False,qualified=False)
 if trace:out['trace']=dict(time_s=sol.t.tolist(),force_each_foot_N=observed.tolist(),pad_compression_mm=(xp*1000).tolist(),body_q=q.tolist(),energy_balance_J=balance.tolist(),kinetic_energy_J=kin.tolist(),elastic_arm_energy_J=Uarm.tolist(),elastic_pad_energy_J=Upad.tolist(),dissipated_energy_J=sol.y[10].tolist())
 return out

if __name__=='__main__':
 rows=[];traces=[]
 for c in cad['configurations']:
  for mode in ['point','stick']:
   s=next(x for x in spr if x['propeller_index']==c['propeller_index'] and x['variant']==c['variant'] and x['mode']==mode);r=simulate(c,s);rows.append(r)
  print('Impact',c['propeller_index'],c['variant'],flush=True)
 c=next(c for c in cad['configurations'] if c['propeller_index']==9 and c['variant']=='V4')
 for mode in ['point','stick']:
  s=next(x for x in spr if x['propeller_index']==9 and x['variant']=='V4' and x['mode']==mode)
  for pattern in ['level','two_first','one_first']:
   for speed in [.2,.3,.5,.75,1.]:
    for kp in [100.,500.,2000.]:
     for cp in [0.,500.]:
      keep=mode=='stick' and speed==.5 and kp==500.;r=simulate(c,s,speed,kp,cp,pattern,trace=keep)
      if keep:traces.append(r)
      rows.append({k:v for k,v in r.items() if k!='trace'})
  if mode=='stick':
   for mass in [120.,160.,200.]:
    for gyr in [.35,.5,.65]:
     for cg in [(0.,0.),(.1,0.)]:rows.append(simulate(c,s,pattern='one_first',mass=mass,gyr=gyr,cgxy=cg))
 # Stiff-solid sole sensitivities,without assigning Shore hardness a measured modulus.
 for cc in cad['configurations']:
  for mode in ['point','stick']:
   ss=next(x for x in spr if x['propeller_index']==cc['propeller_index'] and x['variant']==cc['variant'] and x['mode']==mode);rows.append(simulate(cc,ss,kpad=10000.))
 for mode in ['point','stick']:
  ss=next(x for x in spr if x['propeller_index']==9 and x['variant']=='V4' and x['mode']==mode)
  for pattern in ['level','two_first','one_first']:
   for v in [.2,.3,.5,.75,1.]:
    rr=simulate(c,ss,v,30000.,0.,pattern,trace=(mode=='stick' and pattern=='level' and v==.5))
    if 'trace' in rr:traces.append(rr)
    rows.append({k:v for k,v in rr.items() if k!='trace'})
 # Independent analytical peak for a level,undamped,uninterrupted first impact.
 s=next(x for x in spr if x['propeller_index']==9 and x['variant']=='V4' and x['mode']=='stick');v=.2;kp=2000.;r=simulate(c,s,v,kp);meff=160/4;k=1000/(1/s['k_vertical_N_mm']+1/kp);expected=meff*9.81+math.sqrt((meff*9.81)**2+meff*k*v*v);assert r['full_peak_computed'];err=abs(r['max_observed_foot_force_N']/expected-1);assert err<1e-3
 # Step-size check of a clean impact and a viscous/asymmetric contact case.
 checks=[dict(name='undamped_level_peak',numerical_N=r['max_observed_foot_force_N'],analytical_N=expected,relative_error=err,passed=True)]
 for pattern,cp in [('level',0.),('one_first',500.)]:
  a=simulate(c,s,.5,500,cp,pattern,maxstep=.0004);b=simulate(c,s,.5,500,cp,pattern,maxstep=.0001);error=abs(a['max_observed_foot_force_N']/b['max_observed_foot_force_N']-1);assert error<.005;assert a['termination']==b['termination'];checks.append(dict(name='time_step_'+pattern,maxstep_s=[.0004,.0001],relative_peak_difference=error,passed=True,energy_error_fine=b['energy_balance_relative_error']))
 keys=['propeller_index','variant','contact_mode','sink_speed_m_s','pad_k_assumed_N_mm','pad_c_assumed_Ns_m','terrain_pattern','mass_kg','gyration_radius_assumed_m','cg_xy_m']
 rows=list({tuple(json.dumps(r[k],sort_keys=True) for k in keys):r for r in rows}.values())
 result=dict(native_sha256=cad['native_sha256'],qualified=False,scope='3DOF rigid body heave/pitch/roll on four unilateral contacts with CAD-beam-derived arm+leg stiffness and assumed Kelvin-Voigt sole in series.No lateral rigid body motion,Coulomb friction dynamics,foot pressure distribution,local heel impact,beam inertia,rotor thrust,composite damage/plasticity or validated force-stroke data.Central frame treated rigid with conservative220mm square low-point extent;46mm initial clearance.Contact mode springs are separate ground-constraint bounds,not validated soil models.Events terminate before geometry/stability invalidity;observed forces at aborted cases are not complete peaks.',cases=rows,implementation_checks=checks,trace_cases=traces)
 (O/'Landestoss_Simulation.json').write_text(json.dumps(result,indent=2));
 with (O/'Landestoss_Uebersicht.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print('Impact study completed',len(rows),'cases;verification',checks,flush=True)
