"""Illustration of model assumptions and actual CFD result arrays."""
import json
import math
import os
from pathlib import Path
import sys
os.environ.setdefault('MPLCONFIGDIR','/tmp/propboard-matplotlib')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/propboard-cache')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'cad'))
from umlauf_kinematik import state,perimeter,naca_thickness
p=json.loads((ROOT/'cad/umlauf_parameter.json').read_text())
length=perimeter(p['straight_m'],p['radius_m'])
fig=plt.figure(figsize=(12,7))
ax=fig.add_subplot(111,projection='3d')
for module,cy in enumerate(p['module_centres_y_m']):
    direction=1 if module==0 else -1
    color=['#007b83','#bc4b14'][module]
    path=np.array([state(q,p['straight_m'],p['radius_m'])[:2]
                   for q in np.linspace(0,length,350)])
    for side in (-1,1):
        ax.plot(path[:,0],np.full(len(path),cy+side*.32),path[:,1],color=color,lw=2)
    for i in range(p['wings_per_module']):
        x,z,tx,tz,b=state(i*length/p['wings_per_module'],p['straight_m'],p['radius_m'],direction,p['pitch_amplitude_deg'])
        xx=np.linspace(0,1,40)
        contour=[(q,naca_thickness(q)) for q in xx]+[(q,-naca_thickness(q)) for q in xx[::-1]]
        front=[];back=[]
        for q,h in contour:
            px=x+(.5-q)*p['chord_m']*math.cos(b)-h*p['chord_m']*math.sin(b)
            pz=z+(.5-q)*p['chord_m']*math.sin(b)+h*p['chord_m']*math.cos(b)
            front.append((px,cy-p['span_m']/2,pz))
            back.append((px,cy+p['span_m']/2,pz))
        faces=[[front[k],back[k],back[(k+1)%len(back)],front[(k+1)%len(front)]] for k in range(len(front))]
        ax.add_collection3d(Poly3DCollection(faces,facecolor=color,alpha=.8,edgecolor='none'))
    ax.quiver(0,cy,.18,.28*direction,0,0,color=color,linewidth=3,arrow_length_ratio=.25)
deck=[(-.6,-.15,.25),(.6,-.15,.25),(.6,.15,.25),(-.6,.15,.25)]
ax.add_collection3d(Poly3DCollection([deck],facecolor='#666666',alpha=.65))
ax.set(xlim=(-1.05,1.05),ylim=(-.85,.85),zlim=(-.3,.35),xlabel='x [m]',ylabel='y [m]',zlabel='z [m]')
ax.set_box_aspect((2.1,1.7,.65))
ax.view_init(elev=25,azim=-55)
ax.set_title('Konzept: zwei gegenläufige Flügelumläufe\n16 NACA-0012-Flügel; Führungen und Deck schematisch')
fig.text(.5,.02,'Neue Geometrieannahmen – kein Magnet-, Struktur- oder Flugnachweis',ha='center')
fig.tight_layout()
fig.savefig(ROOT/'cad/Umlauf_Konzept.png',dpi=180)
plt.close(fig)

available=[]
for name in ['forward_c12','forward_c16','reverse_c16','zero_pitch_c12']:
    path=ROOT/'cfd/results'/f'{name}.npz'
    if path.exists(): available.append((name,np.load(path)))
if available:
    fig,ax=plt.subplots(figsize=(10,5))
    for name,data in available:
        a=data['history']
        # Average ~1/8 orbit to suppress grid-crossing force impulses.
        window=max(1,int((a[-1,0]/a[-1,1])/8))
        smoothed=np.convolve(a[:,3],np.ones(window)/window,mode='valid')
        ax.plot(a[window-1:,1],smoothed,label=name)
    ax.axhline(0,color='gray',lw=.6)
    ax.set(xlabel='Umläufe',ylabel='Cz, gleitender Mittelwert (1/8 Umlauf)',title='Explorative 2D-CFD, Re = 40 – keine reale Traglast')
    ax.legend();ax.grid(alpha=.2);fig.tight_layout()
    fig.savefig(ROOT/'cfd/results/Kraftverlauf.png',dpi=160)
    plt.close(fig)
    for name,data in available:
        ux,uz=data['ux'],data['uz']
        dx=float(data['dx'])
        chord_cells=.12/dx
        vort=(np.gradient(uz,axis=1)-np.gradient(ux,axis=0))/.04*chord_cells
        vort=np.ma.array(vort,mask=data['mask'])
        nz,nx=ux.shape
        fig,ax=plt.subplots(figsize=(12,5))
        im=ax.imshow(vort,origin='lower',extent=(-nx*dx/2,nx*dx/2,-nz*dx/2,nz*dx/2),cmap='RdBu_r',vmin=-3,vmax=3)
        ax.contour(data['mask'],levels=[.5],colors='black',linewidths=.5,origin='lower',extent=(-nx*dx/2,nx*dx/2,-nz*dx/2,nz*dx/2))
        ax.set(xlabel='x [m], Geometrieskalierung',ylabel='z [m]',title=f'{name}: 2D-Wirbelstärke, Re = 40 (künstliche Viskosität)')
        fig.colorbar(im,ax=ax,label='dimensionslose Wirbelstärke ωc/U')
        fig.tight_layout();fig.savefig(ROOT/'cfd/results'/f'{name}_Stroemung.png',dpi=160)
        plt.close(fig)
