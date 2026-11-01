#!/usr/bin/env python3
"""Scientific plots from actual force histories / sampled OpenFOAM fields only."""
import argparse,gzip,json,math,os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/propboard-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as Polygon
import numpy as np
from scipy.interpolate import griddata
from erstellen import H,profile
from auswerten import history
OUT=H/'Ausgabe';OUT.mkdir(exist_ok=True)
def forces(rank,level='coarse'):
    case=H/'cases'/f'K{rank:02d}_{level}';m=json.loads((case/'case.json').read_text())
    a,b,c,d=[history(case,name,file) for name,file in [('forces_wingUpper','force.dat'),('forces_wingLower','force.dat'),('forces_wingUpper','moment.dat'),('forces_wingLower','moment.dat')]]
    n=min(map(len,[a,b,c,d]))
    if n<2:return
    a,b,c,d=[v[-n:] for v in [a,b,c,d]];omega=m['design']['rpm']*math.pi/30;T=a[:,3]+b[:,3];P=omega*(-c[:,3]+d[:,3]);it=a[:,0]
    fig,ax=plt.subplots(2,1,figsize=(10,6),sharex=True,constrained_layout=True)
    ax[0].plot(it,T/9.81,label='3D-CFD',color='#147eab');
    if m.get('screeningThrustN') is not None:ax[0].axhline(m['screeningThrustN']/9.81,ls='--',color='#9d661c',label='Vereinfachtes Prüfstandsmodell')
    ax[0].axhline(m['massKg'],ls=':',color='#555',label='Modellgewicht');ax[0].set_ylabel('Schubäquivalent [kg]');ax[0].legend(fontsize=8)
    ax[1].plot(it,P,color='#147eab');
    if m.get('screeningPowerW') is not None:ax[1].axhline(m['screeningPowerW'],ls='--',color='#9d661c')
    ax[1].set_ylabel('Mechanische Rotorleistung [W]');ax[1].set_xlabel('SIMPLE-Iteration, keine physikalische Zeit')
    for v in ax:v.grid(alpha=.25)
    fig.suptitle(f'Kandidat {rank:02d}: tatsächliche CFD-Kräfte / Drehmomente · numerische Akzeptanz separat prüfen')
    p=OUT/f'K{rank:02d}_{level}_Konvergenz.png';fig.savefig(p,dpi=150);plt.close(fig);print(p)
def flow(rank,time,level='coarse'):
    case=H/'cases'/f'K{rank:02d}_probe_{time}_{level}';meta=json.loads((case/'case.json').read_text());d=meta['design'];folder=case/f'postProcessing/profiles/{time}'
    p=np.loadtxt(folder/'p_midspan.raw');u=np.loadtxt(folder/'U_midspan.raw');assert np.max(np.abs(p[:,:3]-u[:,:3]))<1e-10
    r=.7*d['diameterMm']/2000;omega=d['rpm']*math.pi/30;f=(r-d['rootRadiusMm']/1000)/(d['diameterMm']/2000-d['rootRadiusMm']/1000);chord=d['chordMm']/1000*(1+(d['taper']-1)*f)
    fig,axes=plt.subplots(1,2,figsize=(13,4.8),constrained_layout=True);fig.suptitle(f'CFD-Pilot K{rank:02d} · Schnitt bei 70 % Radius · Iteration {time}\nMomentaufnahme, numerische Akzeptanz separat prüfen',fontsize=12)
    levels=np.linspace(-1.5,.8,30)
    for l,ax in enumerate(axes):
        sign=1 if l==0 else -1;zc=sign*d['spacingMm']/2000
        sel=(np.abs(p[:,1])<2*chord)&(np.abs(p[:,2]-zc)<1.8*chord);points=p[sel,1:3]-[0,zc]
        yy,zz=np.meshgrid(np.linspace(-1.5*chord,1.5*chord,300),np.linspace(-.8*chord,.8*chord,180))
        cp=griddata(points,p[sel,3]/(.5*(omega*r)**2),(yy,zz),method='linear');uy=griddata(points,u[sel,4]-sign*omega*r,(yy,zz),method='linear');uz=griddata(points,u[sel,5],(yy,zz),method='linear')
        q=(1-np.cos(np.linspace(0,np.pi,100)))/2;coords=np.r_[q,q[-1:0:-1]];th=np.r_[profile(q,d['thickness']),-profile(q[-1:0:-1],d['thickness'])]*chord;theta=math.radians(d['pitchUpperDeg' if l==0 else 'pitchLowerDeg']+d['twistDeg']*f);x=(coords-d.get('pitchAxisFraction',.25))*chord
        foil=np.column_stack([-sign*(x*np.cos(theta)+th*np.sin(theta)),-x*np.sin(theta)+th*np.cos(theta)])
        mask=Polygon(foil).contains_points(np.column_stack([yy.ravel(),zz.ravel()])).reshape(yy.shape)
        for v in [cp,uy,uz]:v[mask]=np.nan
        image=ax.contourf(yy*1000,zz*1000,cp,levels=levels,cmap='coolwarm',extend='both');ax.streamplot(yy[0]*1000,zz[:,0]*1000,np.ma.masked_invalid(uy),np.ma.masked_invalid(uz),density=.8,color='#404040',linewidth=.55,arrowsize=.65)
        ax.fill(foil[:,0]*1000,foil[:,1]*1000,color='#e9e9e9',edgecolor='black',lw=.8,zorder=10);ax.set_aspect('equal');ax.set_xlabel('Tangentialrichtung y [mm]');ax.set_ylabel('z relativ zur Rotorebene [mm]');ax.set_title(('Oben' if l==0 else 'Unten')+' · projizierte Relativströmung')
    fig.colorbar(image,ax=axes,label='Druckbeiwert Cp, Bezug ½ (Ωr)²');dest=OUT/f'K{rank:02d}_I{time}_{level}_Stroemung.png';fig.savefig(dest,dpi=160);plt.close(fig)
    data=np.column_stack([p[:,:3],p[:,3],u[:,3:]])
    with gzip.open(OUT/f'K{rank:02d}_I{time}_{level}_Schnittdaten.csv.gz','wt') as stream:np.savetxt(stream,data,delimiter=';',header='x_m;y_m;z_m;p_kinematic_m2_s2;Ux_m_s;Uy_m_s;Uz_m_s')
    print(dest)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--rank',type=int,required=True);a.add_argument('--level',default='coarse');a.add_argument('--time',type=int);p=a.parse_args();forces(p.rank,p.level)
    if p.time is not None:flow(p.rank,p.time,p.level)
