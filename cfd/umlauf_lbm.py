"""Exploratory 2D D2Q9-BGK CFD of ONE prescribed moving wing loop.

Low-Reynolds numerical experiment, NOT flight-scale air CFD. Unit span,
moving halfway bounce-back, momentum exchange + covered/uncovered-cell
momentum correction, damped periodic far field. No rail/deck/person geometry.
"""
import argparse
import json
import math
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.cfd-tools'))
sys.path.insert(0,str(ROOT/'cad'))
os.environ.setdefault('NUMBA_NUM_THREADS','4')
import numpy as np
from numba import njit, prange
from umlauf_kinematik import state, perimeter

CX=np.array([0,1,0,-1,0,1,-1,-1,1],dtype=np.int64)
CZ=np.array([0,0,1,0,-1,1,1,-1,-1],dtype=np.int64)
OP=np.array([0,3,4,1,2,7,8,5,6],dtype=np.int64)
W=np.array([4/9]+[1/9]*4+[1/36]*4)
state_jit=njit(state)
# Compile the global dependency used by state.
state_jit.__wrapped__.__globals__['perimeter']=njit(perimeter)


@njit(cache=True)
def make_mask(mask,wx,wz,step,chord,straight,radius,nw,speed,direction,pitch):
    mask[:]=False
    wx[:]=0
    wz[:]=0
    nz,nx=mask.shape
    length=2*straight+2*math.pi*radius
    for k in range(nw):
        s=k*length/nw+direction*speed*step
        x,z,tx,tz,beta=state_jit(s,straight,radius,direction,pitch)
        x+=nx/2
        z+=nz/2
        eps=0.001
        b1=state_jit(s+direction*eps,straight,radius,direction,pitch)[4]
        b0=state_jit(s-direction*eps,straight,radius,direction,pitch)[4]
        db=math.atan2(math.sin(b1-b0),math.cos(b1-b0))/(2*eps)*speed
        co,si=math.cos(beta),math.sin(beta)
        reach=chord*.6
        for j in range(max(0,int(z-reach)-1),min(nz,int(z+reach)+2)):
            for i in range(max(0,int(x-reach)-1),min(nx,int(x+reach)+2)):
                dx,dz=i-x,j-z
                q=.5-(dx*co+dz*si)/chord
                h=(-dx*si+dz*co)/chord
                if q>0 and q<1:
                    thick=.6*(.2969*math.sqrt(q)-.126*q-.3516*q*q+.2843*q**3-.1036*q**4)
                    if abs(h)<=thick:
                        mask[j,i]=True
                        wx[j,i]=speed*tx-db*dz
                        wz[j,i]=speed*tz+db*dx


@njit(cache=True,parallel=True)
def collide(f,post,oldmask,mask,wx,wz,omega,sponge,correction):
    nz,nx=mask.shape
    correction[:]=0
    for j in prange(nz):
        for i in range(nx):
            rho=0.
            mx=0.
            mz=0.
            for q in range(9):
                rho+=f[j,i,q]
                mx+=f[j,i,q]*CX[q]
                mz+=f[j,i,q]*CZ[q]
            if mask[j,i]:
                if not oldmask[j,i]:
                    correction[j,0]+=mx
                    correction[j,1]+=mz
                    correction[j,2]+=(i-nx/2)*mz-(j-nz/2)*mx
                    correction[j,3]-=mx*wx[j,i]+mz*wz[j,i]
                ux,uz=wx[j,i],wz[j,i]
                for q in range(9):
                    cu=CX[q]*ux+CZ[q]*uz
                    post[j,i,q]=W[q]*(1+3*cu+4.5*cu*cu-1.5*(ux*ux+uz*uz))
                continue
            if oldmask[j,i]:
                # Refill uncovered cells from neighbouring fluid macrostates.
                rsum=0.; usum=0.; vsum=0.; count=0
                for q in range(1,9):
                    jj=(j+CZ[q])%nz; ii=(i+CX[q])%nx
                    if not oldmask[jj,ii] and not mask[jj,ii]:
                        rr=0.; mmx=0.; mmz=0.
                        for a in range(9):
                            rr+=f[jj,ii,a]
                            mmx+=f[jj,ii,a]*CX[a]
                            mmz+=f[jj,ii,a]*CZ[a]
                        rsum+=rr; usum+=mmx; vsum+=mmz; count+=1
                if count:
                    rho=rsum/count; ux=usum/rsum; uz=vsum/rsum
                else:
                    rho=1.; ux=0.; uz=0.
                mx=rho*ux; mz=rho*uz
                correction[j,0]-=mx
                correction[j,1]-=mz
                correction[j,2]-=(i-nx/2)*mz-(j-nz/2)*mx
                # Newly uncovered cells have no wall velocity; use neighbour
                # velocity only for momentum correction, no power inference.
                for q in range(9):
                    cu=CX[q]*ux+CZ[q]*uz
                    post[j,i,q]=rho*W[q]*(1+3*cu+4.5*cu*cu-1.5*(ux*ux+uz*uz))
            else:
                ux,uz=mx/rho,mz/rho
                for q in range(9):
                    cu=CX[q]*ux+CZ[q]*uz
                    eq=rho*W[q]*(1+3*cu+4.5*cu*cu-1.5*(ux*ux+uz*uz))
                    post[j,i,q]=(1-sponge[j,i])*(f[j,i,q]+omega*(eq-f[j,i,q]))+sponge[j,i]*W[q]


@njit(cache=True,parallel=True)
def stream(post,f,mask,wx,wz,forces):
    nz,nx=mask.shape
    forces[:]=0
    for j in prange(nz):
        for i in range(nx):
            if mask[j,i]:
                for q in range(9): f[j,i,q]=post[j,i,q]
                continue
            rho=0.
            for q in range(9): rho+=post[j,i,q]
            for q in range(9):
                jj=(j-CZ[q])%nz; ii=(i-CX[q])%nx
                if mask[jj,ii]:
                    wall_dot=CX[q]*wx[jj,ii]+CZ[q]*wz[jj,ii]
                    reflected=post[j,i,OP[q]]+6*W[q]*rho*wall_dot
                    f[j,i,q]=reflected
                    fx=-(reflected+post[j,i,OP[q]])*CX[q]
                    fz=-(reflected+post[j,i,OP[q]])*CZ[q]
                    forces[j,0]+=fx; forces[j,1]+=fz
                    forces[j,2]+=(i-.5*CX[q]-nx/2)*fz-(j-.5*CZ[q]-nz/2)*fx
                    forces[j,3]-=fx*wx[jj,ii]+fz*wz[jj,ii]
                else:
                    f[j,i,q]=post[jj,ii,q]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--chord-cells',type=int,default=16)
    ap.add_argument('--cycles',type=float,default=2)
    ap.add_argument('--direction',type=int,choices=(-1,1),default=1)
    ap.add_argument('--pitch',type=float,default=12)
    ap.add_argument('--re',type=float,default=40)
    ap.add_argument('--speed',type=float,default=.04)
    ap.add_argument('--name',default='forward')
    ap.add_argument('--stationary',action='store_true')
    args=ap.parse_args()
    p=json.loads((ROOT/'cad/umlauf_parameter.json').read_text())
    c=args.chord_cells
    dx=p['chord_m']/c
    straight=p['straight_m']/dx
    radius=p['radius_m']/dx
    nx=int(math.ceil(2.9/dx/8)*8)
    nz=int(math.ceil(1.5/dx/8)*8)
    speed=0 if args.stationary else args.speed
    period=(2*straight+2*math.pi*radius)/args.speed
    steps=int(args.cycles*period)
    nu=args.speed*c/args.re
    tau=.5+3*nu
    assert tau>.505 and args.speed<.08
    f=np.zeros((nz,nx,9)); f[:]=W
    post=f.copy()
    old=np.zeros((nz,nx),dtype=np.bool_); mask=old.copy()
    wx=np.zeros((nz,nx)); wz=wx.copy()
    force=np.zeros((nz,4)); corr=force.copy()
    y,x=np.indices((nz,nx))
    distance=np.minimum(np.minimum(x,nx-1-x),np.minimum(y,nz-1-y))
    sponge=.03*np.maximum(0,1-distance/(3*c))**2
    out=ROOT/'cfd/results'
    out.mkdir(exist_ok=True)
    rows=[]
    force_scale=.5*args.speed**2*p['wings_per_module']*c
    start=time.time()
    make_mask(old,wx,wz,0,c,straight,radius,p['wings_per_module'],speed,args.direction,args.pitch)
    rho_min=1.;rho_max=1.;umax=0.
    with (out/(args.name+'.csv')).open('w') as log:
        log.write('step,cycles,Cx,Cz,Cmoment,wall_power_proxy\n')
        for step in range(steps):
            make_mask(mask,wx,wz,step+1,c,straight,radius,p['wings_per_module'],speed,args.direction,args.pitch)
            collide(f,post,old,mask,wx,wz,1/tau,sponge,corr)
            stream(post,f,mask,wx,wz,force)
            total=force.sum(axis=0)+corr.sum(axis=0)
            row=[step+1,(step+1)/period,total[0]/force_scale,total[1]/force_scale,
                 total[2]/(force_scale*c),total[3]/(force_scale*args.speed)]
            rows.append(row)
            if step%10==0: log.write(','.join(map(str,row))+'\n')
            old,mask=mask,old
            if step%500==0 or step==steps-1:
                rho=f.sum(axis=2)
                ux=(f*CX).sum(axis=2)/rho
                uz=(f*CZ).sum(axis=2)/rho
                fluid=~old
                lo=float(rho[fluid].min()); hi=float(rho[fluid].max())
                um=float(np.sqrt(ux[fluid]**2+uz[fluid]**2).max())
                rho_min=min(rho_min,lo);rho_max=max(rho_max,hi);umax=max(umax,um)
                if not np.isfinite(f).all() or lo<.75 or hi>1.25 or um>.3:
                    raise RuntimeError(f'Unstable at {step}: rho={lo,hi}, u={um}')
                if step%2500==0:
                    print(f'{args.name}: {step}/{steps}, rho={lo:.4f}..{hi:.4f}, u={um:.4f}, elapsed={time.time()-start:.1f}s',flush=True)
    a=np.asarray(rows)
    np.savez_compressed(out/(args.name+'.npz'),rho=rho,ux=ux,uz=uz,mask=old,history=a,dx=dx)
    means=[]
    for cycle in range(int(args.cycles)):
        selected=a[(a[:,1]>cycle)&(a[:,1]<=cycle+1)]
        means.append({'cycle':cycle+1,'Cx':float(selected[:,2].mean()),
                      'Cz':float(selected[:,3].mean()),'Cmoment':float(selected[:,4].mean())})
    result={
        'name':args.name,'method':'2D D2Q9 BGK moving bounce-back, one module, artificial low-Re viscosity',
        'not_flight_scale':True,'Re_chord':args.re,'chord_cells':c,
        'domain_cells':[nx,nz],'steps_completed':steps,'cycles':args.cycles,
        'direction':args.direction,'pitch_amplitude_deg':args.pitch,
        'tau':tau,'lattice_speed':args.speed,'rho_range':[rho_min,rho_max],
        'max_lattice_speed':umax,'elapsed_s':time.time()-start,'cycle_means':means,
        'coefficient_reference':'0.5*rho*U^2*8*chord per unit span; moment also divided by chord',
        'power_warning':'wall_power_proxy omits uncovered-cell work; not shaft/electrical power',
        'limitations':['2D infinite span','Re=40 differs strongly from real air',
                       'coarse moving boundary','no magnets, rails, deck, rider or module interaction',
                       'damped periodic outer boundaries','prescribed motion, no structural dynamics']}
    (out/(args.name+'.json')).write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__': main()
