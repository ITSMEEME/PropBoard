"""2D straight-strip comparison. NOT complete horizontal-loop CFD."""
import json,math,sys,time,argparse,os
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.extend([str(HERE.parent/'cfd')])
os.environ.setdefault('NUMBA_NUM_THREADS','1')
from umlauf_lbm import np,njit,collide,stream,CX,CZ,W

@njit(cache=True)
def mask_rows(mask,wx,wz,step,chord,speed,levels,directions,pitch):
    mask[:]=False;wx[:]=0;wz[:]=0
    nz,nx=mask.shape
    for row in range(len(levels)):
        direction=directions[row]
        xc=(nx/2+direction*speed*step)%nx
        zc=nz/2+levels[row]
        beta=pitch if direction==1 else math.pi-pitch
        co,si=math.cos(beta),math.sin(beta)
        for j in range(max(0,int(zc-chord)),min(nz,int(zc+chord)+1)):
            for i in range(nx):
                dx=(i-xc+nx/2)%nx-nx/2
                dz=j-zc
                q=.5-(dx*co+dz*si)/chord
                h=(-dx*si+dz*co)/chord
                if q>0 and q<1:
                    thick=.6*(.2969*math.sqrt(q)-.126*q-.3516*q*q+.2843*q**3-.1036*q**4)
                    if abs(h)<=thick:mask[j,i]=True;wx[j,i]=speed*direction

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--cells',type=int,default=16)
    ap.add_argument('--gap',type=float,default=.24)
    ap.add_argument('--single',action='store_true')
    ap.add_argument('--passages',type=int,default=20)
    ap.add_argument('--name',required=True)
    args=ap.parse_args()
    p=json.loads((HERE/'parameter.json').read_text())
    c=args.cells;dx=p['chord_m']/c;u=.04;re=40
    length=2*p['straight_m']+2*math.pi*p['radius_m']
    spacing=length/p['wings_per_level']
    nx=round(spacing/dx);nz=round(1.8/dx)
    levels=np.array([0.] if args.single else [-args.gap/2/dx,args.gap/2/dx])
    directions=np.array([1] if args.single else [1,-1])
    f=np.empty((nz,nx,9));f[:]=W;post=f.copy()
    old=np.zeros((nz,nx),dtype=np.bool_);mask=old.copy();wx=np.zeros((nz,nx));wz=wx.copy()
    corr=np.zeros((nz,4));force=corr.copy()
    j=np.indices((nz,nx))[0];distance=np.minimum(j,nz-1-j)
    sponge=.03*np.maximum(0,1-distance/(3*c))**2
    period=nx/u;steps=round(args.passages*period);scale=.5*u*u*c
    mask_rows(old,wx,wz,0,c,u,levels,directions,math.radians(p['pitch_deg']))
    rows=[];start=time.time();rho_range=[1.,1.];umax=0.
    for step in range(steps):
        mask_rows(mask,wx,wz,step+1,c,u,levels,directions,math.radians(p['pitch_deg']))
        collide(f,post,old,mask,wx,wz,1/(.5+3*u*c/re),sponge,corr)
        stream(post,f,mask,wx,wz,force)
        total=force.sum(axis=0)+corr.sum(axis=0)
        rows.append([(step+1)/period,total[0]/scale,total[1]/scale])
        old,mask=mask,old
        if step%1000==0 or step==steps-1:
            rho=f.sum(axis=2);ux=(f*CX).sum(axis=2)/rho;uz=(f*CZ).sum(axis=2)/rho
            fluid=~old;lo=float(rho[fluid].min());hi=float(rho[fluid].max())
            um=float(np.sqrt(ux[fluid]**2+uz[fluid]**2).max())
            rho_range=[min(rho_range[0],lo),max(rho_range[1],hi)];umax=max(umax,um)
            if not np.isfinite(f).all() or lo<.75 or hi>1.25 or um>.3:raise RuntimeError((step,lo,hi,um))
            if step%5000==0:print(f'{args.name}: {step}/{steps}, {time.time()-start:.1f}s',flush=True)
    a=np.array(rows);out=HERE/'results';out.mkdir(exist_ok=True)
    averages=[]
    for k in range(args.passages//5):
        part=a[(a[:,0]>k*5)&(a[:,0]<=(k+1)*5)]
        averages.append({'passages':[k*5,(k+1)*5],'Cz_total':float(part[:,2].mean())})
    result={'case':args.name,'kind':'2D periodic straight section, artificial Re=40; NOT 3D loop',
            'levels':len(levels),'gap_m':None if args.single else args.gap,'chord_cells':c,
            'grid':[nx,nz],'steps_completed':steps,'passages':args.passages,'Re':re,
            'spacing_m_actual':nx*dx,'spacing_m_requested':spacing,
            'rho_range':rho_range,'max_lattice_speed':umax,'block_means':averages,
            'force_reference':'0.5*rho*U^2*chord per unit span; SUM across all levels',
            'elapsed_s':time.time()-start,'flight_scale':False,'full_loop_simulated':False}
    (out/(args.name+'.json')).write_text(json.dumps(result,indent=2))
    np.savetxt(out/(args.name+'.csv'),a[::10],delimiter=',',header='passages,Cx_total,Cz_total')
    np.savez_compressed(out/(args.name+'.npz'),history=a,rho=rho,ux=ux,uz=uz,mask=old,dx=dx)
    print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
