#!/usr/bin/env python3
"""Synthetic recovery checks only. These fixtures are NOT physical measurements."""
import json,math
from pathlib import Path
import numpy as np
from identifizieren import friction,servo,aero,read
H=Path(__file__).resolve().parent;results=[]
rows=[]
for N in (20,60,100):
    for speed in (.2,.7,1.5):
        for direction in (-1,1):
            t=direction*(.08*N*.0048+.003+.002*speed)
            rows.append(dict(normal_load_N=N,pitch_speed_rad_s=speed*direction,drive_torque_Nm=t,inertial_torque_Nm=0,aero_torque_Nm=0,breakaway=0))
f=friction(rows);assert abs(f['effective_mu']-.08)<1e-10 and abs(f['preload_friction_Nm']-.003)<1e-10
results.append(dict(name='Synthetic friction recovery',status='PASS',effective_mu=f['effective_mu']))
rows=[];theta=0;dt=.005;tau=.05;delay=.015
cmd=lambda t:0 if t<.15 else 5 if t<.6 else -3
for i in range(200):
    t=i*dt
    if i:theta=cmd(t-delay)+(theta-cmd(t-delay))*math.exp(-dt/tau)
    rows.append(dict(t_s=t,command_deg=cmd(t),measured_deg=theta,load_Nm=.03,voltage_V=7.4,current_A=.2))
s=servo(rows);assert abs(s['tau_s']-.05)<.005 and abs(s['delay_s']-delay)<.008,(s['tau_s'],s['delay_s'])
results.append(dict(name='Synthetic effective servo lag recovery',status='PASS',tau_s=s['tau_s'],delay_s=s['delay_s']))
a=aero([dict(thrust_N=.9*p,model_thrust_N=p,torque_Nm=1.15*q,model_torque_Nm=q,uncertainty_N=.05,rpm=2200+i*100) for i,(p,q) in enumerate(zip(range(8,16),np.linspace(.1,.4,8)))])
assert abs(a['thrust_scale']-.9)<1e-10 and abs(a['torque_scale']-1.15)<1e-10
results.append(dict(name='Synthetic aero correction recovery',status='PASS',kT=a['thrust_scale'],kQ=a['torque_scale']))
for p in ('Reibung_Vorlage.csv','Servo_Vorlage.csv','Aero_Vorlage.csv'):
    try:read(H/p)
    except ValueError:pass
    else:raise AssertionError('Empty measurement template must not manufacture data')
results.append(dict(name='Empty physical measurement templates rejected',status='PASS'))
(H/'Identifikation_Pruefung.json').write_text(json.dumps(dict(status='SYNTHETIC_TESTS_ONLY_NO_REAL_MEASUREMENTS',results=results),indent=2));print(results)
