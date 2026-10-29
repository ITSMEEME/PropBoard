"""Repeat the 240-mm c24 strip case with time-resolved encounter output."""
import sys,os,json,math,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vergleich_horizontal'))
os.environ.setdefault('NUMBA_NUM_THREADS','2')
from strip_cfd import np,mask_rows,collide,stream,CX,CZ,W

out=ROOT/'begegnung/results';out.mkdir(exist_ok=True)
c=24;dx=.12/c;u=.04;re=40;gap=.24
nx,nz=96,360;period=nx/u;steps=int(20*period)
levels=np.array([-gap/2/dx,gap/2/dx]);directions=np.array([1,-1])
f=np.empty((nz,nx,9));f[:]=W;post=f.copy()
old=np.zeros((nz,nx),dtype=np.bool_);mask=old.copy();wx=np.zeros((nz,nx));wz=wx.copy()
force=np.zeros((nz,4));corr=force.copy()
j=np.indices((nz,nx))[0];distance=np.minimum(j,nz-1-j)
sponge=.03*np.maximum(0,1-distance/(3*c))**2
mask_rows(old,wx,wz,0,c,u,levels,directions,math.radians(12))
scale=.5*u*u*c
rows=[];frames=[];times=[];rho_range=[1.,1.];maxu=0.;start=time.time()
crop=slice(nz//2-72,nz//2+73)
for step in range(1,steps+1):
    mask_rows(mask,wx,wz,step,c,u,levels,directions,math.radians(12))
    collide(f,post,old,mask,wx,wz,1/(.5+3*u*c/re),sponge,corr)
    stream(post,f,mask,wx,wz,force)
    total=force+corr
    lower=total[:nz//2].sum(axis=0)/scale
    upper=total[nz//2:].sum(axis=0)/scale
    rows.append([step,step/period,(2*step/period)%1,lower[0],lower[1],upper[0],upper[1]])
    old,mask=mask,old
    capture=step>=18*period and step%40==0
    if step%1000==0 or capture or step==steps:
        rho=f.sum(axis=2);ux=(f*CX).sum(axis=2)/rho;uz=(f*CZ).sum(axis=2)/rho
        fluid=~old
        lo=float(rho[fluid].min());hi=float(rho[fluid].max())
        umax=float(np.sqrt(ux[fluid]**2+uz[fluid]**2).max())
        rho_range=[min(rho_range[0],lo),max(rho_range[1],hi)];maxu=max(maxu,umax)
        if not np.isfinite(f).all() or lo<.75 or hi>1.25 or umax>.3:raise RuntimeError((step,lo,hi,umax))
        if capture:
            frames.append(np.stack([rho[crop],ux[crop],uz[crop],old[crop]]).astype(np.float32))
            times.append(step/period)
    if step%6000==0:print(f'Encounter: {step}/{steps}; {time.time()-start:.1f}s',flush=True)
a=np.asarray(rows)
np.savez_compressed(out/'Zeitfelder.npz',fields=np.array(frames),times=times,dx=dx,u=u,
                    history=a,z_start=-72*dx,period=period)
np.savez_compressed(out/'Checkpoint.npz',f=f,step=steps,dx=dx,period=period)
np.savetxt(out/'Kraefte.csv',a[::10],delimiter=',',header='step,passages,encounter_phase,Cx_lower,Cz_lower,Cx_upper,Cz_upper')
last=a[(a[:,1]>15)&(a[:,1]<=20)]
baseline=json.loads((ROOT/'vergleich_horizontal/results/stack_240_c24.json').read_text())['block_means'][-1]['Cz_total']
cz=float((last[:,4]+last[:,6]).mean())
assert abs(cz-baseline)<1e-8,(cz,baseline)
report={'scope':'2D local straight periodic opposed rows, Re=40, NOT real-scale 3D',
        'steps':steps,'chord_cells':c,'gap_m':gap,'gap_over_chord':2.,'grid':[nx,nz],
        'frames':len(frames),'snapshot_passages':[18,20],
        'pitch_deg':12,'rho_range':rho_range,'max_lattice_speed':maxu,
        'per_row_force_assignment':'By z half-plane; only valid here because separate rows stay at z=+/-0.12 m',
        'Cz_total_last5':cz,'previous_run_Cz_total_last5':baseline,
        'absolute_reproduction_difference':abs(cz-baseline),'elapsed_s':time.time()-start,
        'not_periodically_converged':True}
(out/'Laufbericht.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
