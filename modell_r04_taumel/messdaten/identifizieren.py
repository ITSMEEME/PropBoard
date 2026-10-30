#!/usr/bin/env python3
"""Fit effective friction / servo response / aerodynamic correction from real CSVs.

No measurements are generated. Synthetic fixtures are explicitly separate tests.
"""
import argparse,csv,json,math,itertools
from pathlib import Path
import numpy as np

def read(path):
    with Path(path).open(newline='') as f:rows=list(csv.DictReader(f))
    if not rows:raise ValueError('CSV contains no measurements; no identification possible')
    return [{k:float(v) for k,v in r.items()} for r in rows]

def positive_fit(X,y):
    best=None
    for flags in itertools.product([False,True],repeat=X.shape[1]):
        ids=[i for i,b in enumerate(flags) if b]
        beta=np.zeros(X.shape[1])
        if ids:
            v=np.linalg.lstsq(X[:,ids],y,rcond=None)[0]
            if min(v)<0:continue
            beta[ids]=v
        error=float(np.sum((X@beta-y)**2))
        if best is None or error<best[0]:best=(error,beta)
    return best[1]

def friction(rows):
    radius=.0048 # effective groove contact moment arm, from existing CAD pin z offset
    use=[r for r in rows if abs(r['pitch_speed_rad_s'])>.02 and not r['breakaway']]
    if len(use)<9:raise ValueError('Need >=9 sliding samples at distinct normal loads AND pitch rates')
    X=np.array([[r['normal_load_N']*radius,1,abs(r['pitch_speed_rad_s'])] for r in use])
    if np.linalg.matrix_rank(X)<3:raise ValueError('Cannot distinguish load friction, preload and viscosity with these samples')
    y=np.array([(r['drive_torque_Nm']-r['inertial_torque_Nm']-r['aero_torque_Nm'])*np.sign(r['pitch_speed_rad_s']) for r in use])
    if min(y)<-.002:raise ValueError('Opposing friction sign inconsistent: check sensor polarity and subtractions')
    beta=positive_fit(X,y);residual=y-X@beta
    return dict(status='FIT_FROM_SUPPLIED_MEASUREMENTS_NOT_MATERIAL_CONSTANT',samples=len(use),effective_mu=float(beta[0]),preload_friction_Nm=float(beta[1]),viscous_Nms=float(beta[2]),rms_torque_error_Nm=float(np.sqrt(np.mean(residual**2))),effective_radius_m=radius,breakaway_peak_Nm=max([abs(r['drive_torque_Nm']-r['inertial_torque_Nm']-r['aero_torque_Nm']) for r in rows if r['breakaway']]+[0]),limitations='Effective loaded joint parameter, not a universal PA-CF friction coefficient; temperature/contact geometry/loading must match prototype')

def servo(rows):
    t=np.array([r['t_s'] for r in rows]);cmd=np.array([r['command_deg'] for r in rows]);angle=np.array([r['measured_deg'] for r in rows]);dt=np.diff(t)
    if len(t)<20 or min(dt)<=0:raise ValueError('Need >=20 strictly increasing time samples')
    if np.ptp(cmd)<1:raise ValueError('Insufficient command excitation')
    best=(math.inf,None,None)
    for delay in np.linspace(0,.06,61):
        target=cmd[np.clip(np.searchsorted(t,t-delay,side='right')-1,0,len(t)-1)]
        for tau in np.geomspace(.003,.3,100):
            pred=np.empty_like(angle);pred[0]=angle[0]
            for i in range(1,len(t)):pred[i]=target[i]+(pred[i-1]-target[i])*math.exp(-dt[i-1]/tau)
            err=float(np.mean((pred-angle)**2))
            if err<best[0]:best=(err,float(delay),float(tau))
    return dict(status='EFFECTIVE_CLOSED_LOOP_FIRST_ORDER_FIT_NOT_INTERNAL_PID_IDENTIFICATION',delay_s=best[1],tau_s=best[2],rms_angle_error_deg=math.sqrt(best[0]),median_sample_interval_s=float(np.median(dt)),delay_resolution_note='Delay resolution limited by sample interval and command timing; fitted delay is not an internal PID specification',observed_speed_95percentile_deg_s=float(np.quantile(np.abs(np.diff(angle)/dt),.95)),current_peak_A=max(r['current_A'] for r in rows),voltage_range_V=[min(r['voltage_V'] for r in rows),max(r['voltage_V'] for r in rows)],load_range_Nm=[min(r['load_Nm'] for r in rows),max(r['load_Nm'] for r in rows)],limitations='Small nonsaturated steps only; speed under tested load, no stall-current inference or continuous-torque qualification')

def aero(rows):
    if len(rows)<6:raise ValueError('Need >=6 independent paired stand measurements')
    measured=np.array([r['thrust_N'] for r in rows]);pred=np.array([r['model_thrust_N'] for r in rows]);Q=np.array([r['torque_Nm'] for r in rows]);Qp=np.array([r['model_torque_Nm'] for r in rows]);weights=np.array([r['uncertainty_N'] for r in rows]);
    if min(weights)<=0 or min(pred)<=0 or min(Qp)<=0:raise ValueError('Positive uncertainty and model thrust/torque required')
    wt=1/weights**2;kT=float(np.sum(wt*pred*measured)/np.sum(wt*pred**2));kQ=float(Qp@Q/(Qp@Qp));res=measured-kT*pred
    return dict(status='LOCAL_EMPIRICAL_CORRECTION_NOT_UNIVERSAL_POLAR',thrust_scale=kT,torque_scale=kQ,rms_thrust_error_N=float(np.sqrt(np.mean(res**2))),samples=len(rows),rpm_range=[min(r['rpm'] for r in rows),max(r['rpm'] for r in rows)],limitations='Only interpolate within measured rpm/pitch/Re/spacing conditions; torque scale unweighted because no torque uncertainties supplied; not a full polar or cyclic-airload identification')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['friction','servo','aero']);p.add_argument('csv');p.add_argument('--out',required=True);a=p.parse_args()
    result=globals()[a.kind](read(a.csv));result['measurement_source']=str(Path(a.csv).resolve());Path(a.out).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
