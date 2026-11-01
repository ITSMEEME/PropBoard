#!/usr/bin/env python3
"""CFD results are accepted by evidence, never by process exit code alone."""
import argparse,gzip,json,math,re,shutil,tempfile
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent;OUT=H/'Ausgabe';OUT.mkdir(exist_ok=True)
def history(case,name,file):
    paths=sorted((case/'postProcessing'/name).glob('*/'+file),key=lambda p:float(p.parent.name))
    if not paths:return np.empty((0,0))
    # Most recent continuation only: do not blend different RPM operating points.
    try:return np.loadtxt(paths[-1],comments='#',ndmin=2)
    except (ValueError,OSError):return np.empty((0,0))
def measure(case):
    meta=json.loads((case/'case.json').read_text());r={'candidate_rank':meta['candidate_rank'],'level':meta['level'],'design':meta['design'],'native_sha256':meta['native_sha256'],'source_search_sha256':meta['source_search_sha256'],'status':'PENDING','accepted':False,'limitations':meta['limitations']}
    net=case/'Netzcheck.json';r['mesh']=json.loads(net.read_text()) if net.exists() else None
    if not (case/'log.simpleFoam').exists():return r
    log=(case/'log.simpleFoam').read_text(errors='replace');up=history(case,'forces_wingUpper','force.dat');lo=history(case,'forces_wingLower','force.dat');mu=history(case,'forces_wingUpper','moment.dat');ml=history(case,'forces_wingLower','moment.dat')
    if min(map(len,[up,lo,mu,ml]))<2:r['status']='SOLVER_STARTING_OR_FAILED';return r
    n=min(len(up),len(lo),len(mu),len(ml));up,lo,mu,ml=[v[-n:] for v in [up,lo,mu,ml]]
    om=meta.get('run_rpm',meta['design']['rpm'])*math.pi/30;T=up[:,3]+lo[:,3];P=-om*mu[:,3]+om*ml[:,3]
    w=min(200,n);tt,pp=T[-w:],P[-w:];thrust=float(tt.mean());power=float(pp.mean());area=math.pi*(meta['design']['diameterMm']/2000)**2
    def variability(a):
        scale=max(abs(float(a.mean())),1e-8);m=len(a)//2
        return {'relative_std':float(a.std()/scale),'relative_drift':float(abs(a[:m].mean()-a[m:].mean())/scale)}
    velocities=[float(v) for v in re.findall(r'Solving for U[xyz], Initial residual = ([\deE+.\-]+)',log)][-60:]
    pressures=[float(v) for v in re.findall(r'Solving for p, Initial residual = ([\deE+.\-]+)',log)][-20:]
    mass=history(case,'farFlux','surfaceFieldValue.dat');mag=history(case,'farAbsFlux','surfaceFieldValue.dat')
    imbalance=float(np.max(np.abs(mass[-w:,1])/np.maximum(mag[-w:,1],1e-12))) if len(mass)>=w and len(mag)>=w else None
    yp=re.findall(r'patch (wing\w+) y\+ : min = ([\deE+.\-]+), max = ([\deE+.\-]+), average = ([\deE+.\-]+)',log)
    yplus={k:{'min':float(a),'max':float(b),'average':float(c)} for k,a,b,c in yp}
    ideal=thrust**1.5/math.sqrt(2*1.225*area) if thrust>0 else None
    r.update(thrustN=thrust,thrustEquivalentKg=thrust/9.81,mechanicalPowerW=power,rpm=om*30/math.pi,forceWindowIterations=w,lastIteration=float(up[-1,0]),forceStability=variability(tt),powerStability=variability(pp),massImbalanceFraction=imbalance,yPlus=yplus,maxVelocityInitialResidual=max(velocities,default=1),maxPressureInitialResidual=max(pressures,default=1),idealInducedPowerW=ideal,figureOfMerit=ideal/power if ideal and power>0 else None,screeningThrustN=meta['screeningThrustN'],screeningPowerW=meta['screeningPowerW'])
    target=meta['massKg']*9.81*1.055;r['targetThrustN']=target;r['requiredRpmSimilarityEstimate']=r['rpm']*math.sqrt(target/thrust) if thrust>0 else None;r['targetPowerSimilarityEstimateW']=power*(target/thrust)**1.5 if thrust>0 else None
    checks={'mesh':bool(r['mesh'] and r['mesh']['status']=='PASS'),'solver_ended_normally':bool(re.search(r'^End\s*$',log,re.M)) and 'FOAM FATAL' not in log,'at_least_200_iterations':n>=200,'positive_thrust_power':thrust>0 and power>0,'force_std_below_3_percent':r['forceStability']['relative_std']<.03,'force_drift_below_2_percent':r['forceStability']['relative_drift']<.02,'power_std_below_3_percent':r['powerStability']['relative_std']<.03,'power_drift_below_2_percent':r['powerStability']['relative_drift']<.02,'mass_imbalance_below_1_percent':imbalance is not None and imbalance<.01,'velocity_residual_below_1e4':r['maxVelocityInitialResidual']<1e-4,'pressure_residual_below_1e4':r['maxPressureInitialResidual']<1e-4,'spalding_wall_function_mean_yplus_below_30':len(yplus)==2 and all(v['average']<30 for v in yplus.values()),'spalding_wall_function_max_yplus_below_500':len(yplus)==2 and all(v['max']<500 for v in yplus.values()),'energy_lower_bound':ideal is not None and power>=ideal}
    r['wall_resolution_class']='mixed_Spalding_wall_function_RANS';r['fully_wall_resolved']=len(yplus)==2 and all(v['max']<3 for v in yplus.values());r['residualWindowIterations']=20;
    images=list(OUT.glob(f'K{meta["candidate_rank"]:02d}_I*_{meta["level"]}_Stroemung.png'));images.sort(key=lambda p:int(re.search(r'_I(\d+)_',p.name)[1]));r['flowImages']=[images[-1].name] if images else [];r['convergenceImage']=f'K{meta["candidate_rank"]:02d}_{meta["level"]}_Konvergenz.png' if (OUT/f'K{meta["candidate_rank"]:02d}_{meta["level"]}_Konvergenz.png').exists() else None;
    r['checks']=checks;r['accepted']=all(checks.values());r['status']='ACCEPTED_CONDITIONAL_RANS' if r['accepted'] else ('RUNNING' if not checks['solver_ended_normally'] and 'FOAM FATAL' not in log else 'NOT_ACCEPTED');return r
def main():
    rows=[measure(p) for p in sorted((H/'cases').glob('K??_coarse')) if (p/'case.json').exists()]
    accepted=[r for r in rows if r['accepted']];ranking=sorted(accepted,key=lambda r:r['targetPowerSimilarityEstimateW'])
    report={'status':'COMPLETE' if len(rows)==10 and len(accepted)==10 else 'INCOMPLETE_OR_UNACCEPTED','protocol':'P11_3D_SCREENING_SST_SPALDING_V1','method':'Conditional engineering screening with blended Spalding wall functions; not fully wall-resolved. Full 360-degree coaxial frozen-MRF 3D RANS. Similarity-scaled target power is an estimate, not a CFD recalculation at target thrust.','accepted_count':len(accepted),'case_count':len(rows),'cases':rows,'conditional_ranking':[r['candidate_rank'] for r in ranking],'unique_optimum_proven':False}
    def finite(v):
        if isinstance(v,float) and not math.isfinite(v):return None
        if isinstance(v,dict):return {k:finite(x) for k,x in v.items()}
        if isinstance(v,list):return [finite(x) for x in v]
        return v
    if (H/'cases/.paused.json').exists():
        report['status']='PAUSED_FOR_LOCAL_CFD'
        for r in rows:
            if r['status']=='RUNNING':r['status']='PAUSED'
    report=finite(report)
    for name,text in [('CFD_Auswertung.json',json.dumps(report,indent=2,allow_nan=False)+'\n'),('CFD_Ergebnisse.js','globalThis.P11_CFD_RESULTS='+json.dumps(report,allow_nan=False)+';\n')]:
        with tempfile.NamedTemporaryFile(mode='w',dir=OUT,prefix='.cfdtmp',delete=False) as stream:stream.write(text);tmp=Path(stream.name)
        tmp.replace(OUT/name)
    print(json.dumps({'status':report['status'],'accepted':len(accepted),'cases':[{k:r[k] for k in ['candidate_rank','status']} for r in rows]},indent=2))
if __name__=='__main__':main()
