#!/usr/bin/env python3
"""Plot actual parameterized CFD inputs; these pictures are not flow predictions."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from erstellen import SOURCE,H,profile
r=json.loads(SOURCE.read_text());out=H/'Ausgabe';out.mkdir(exist_ok=True)
fig,axes=plt.subplots(2,5,figsize=(19,8),constrained_layout=True)
for i,(ax,row) in enumerate(zip(axes.flat,r['top10Aerodynamic'])):
    d=row['design'];radius=np.linspace(d['rootRadiusMm'],d['diameterMm']/2,50);f=np.linspace(0,1,50);chord=d['chordMm']*(1+(d['taper']-1)*f)
    ax.fill_between(radius,-.75*chord,.25*chord,color='#159cb8',alpha=.7);ax.plot(radius,np.zeros_like(radius),color='#233648',lw=.7)
    ax.set_aspect('equal',adjustable='box');ax.set_xlim(25,255);ax.set_ylim(-45,20);ax.grid(alpha=.2);ax.set_xlabel('Radius [mm]');ax.set_ylabel('Sehnenrichtung [mm]')
    ax.set_title(f"K{i+1:02d}: {d['blades']} Blätter, D {d['diameterMm']:.1f} mm\nt/c {d['thickness']:.3f}, Zuspitzung {d['taper']:.2f}, Verwindung {d['twistDeg']:+.1f}°",fontsize=10)
fig.suptitle('CFD-Eingaben: Sehnenplanformen der Top 10, unprojiziert · keine Strömungsresultate',fontsize=15)
fig.savefig(out/'Top10_Planformen.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,4),constrained_layout=True);q=np.linspace(0,1,300)
for i,row in enumerate(r['top10Aerodynamic']):
    tc=row['design']['thickness'];t=profile(q,tc);ax.plot(q,t,label=f'K{i+1:02d}, t/c={tc:.3f}');ax.plot(q,-t,color=ax.lines[-1].get_color())
ax.set_aspect('equal');ax.set_xlabel('x/c');ax.set_ylabel('y/c');ax.grid(alpha=.2);ax.legend(ncols=2,fontsize=8,loc='upper left',bbox_to_anchor=(1,1));ax.set_title('CFD-Profilfamilie: symmetrische NACA-Kontur mit endlicher Hinterkante')
fig.savefig(out/'Top10_Profile.png',dpi=150);plt.close(fig)
print(out)
