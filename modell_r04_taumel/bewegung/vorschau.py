#!/usr/bin/env python3
import gzip,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
H=Path(__file__).resolve().parent
with gzip.open(H/'Ausgabe/Meshvorschau.json.gz','rt') as f:parts=json.load(f)
fig=plt.figure(figsize=(13,7),facecolor='#eef3f6')
for pane in range(2):
    ax=fig.add_subplot(1,2,pane+1,projection='3d');ax.set_facecolor('#eef3f6')
    for p in parts:
        v=np.array(p['vertices']);f=np.array(p['faces'],dtype=int);tri=v[f]
        if pane:
            mask=np.all(np.linalg.norm(tri[:,:,:2],axis=2)<110,axis=1)&np.all(tri[:,:,2]>12,axis=1)&np.all(tri[:,:,2]<125,axis=1);tri=tri[mask]
        if not len(tri):continue
        color=np.array([.18,.65,.75]) if p['rotor']==0 and p['role']!='fixed' else np.array([.88,.53,.25]) if p['role']!='fixed' else np.array([.52,.59,.66])
        if p['role'].startswith('bearing'):color=np.array([.63,.7,.74])
        if p['role'].startswith('servo'):color=np.array([.52,.27,.58])
        n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-10);brightness=.65+.35*np.abs(n@np.array([.4,-.3,.866]));colors=color[None,:]*brightness[:,None]
        ax.add_collection3d(Poly3DCollection(tri,facecolors=colors,edgecolors='none',rasterized=True))
    R=205 if not pane else 110;ax.set_xlim(-R,R);ax.set_ylim(-R,R);ax.set_zlim(-180 if not pane else 10,140 if not pane else 125);ax.set_box_aspect((2*R,2*R,320 if not pane else 115));ax.view_init(23,-55);ax.set_xlabel('x [mm]');ax.set_ylabel('y [mm]');ax.set_zlabel('z [mm]');ax.set_title('M01 · vollständige Baugruppe' if not pane else 'Oberer Mechanismus · Detailauswahl')
fig.suptitle('Echte FreeCAD-Geometrie in bewegter Stellung · Savöx-Hüllen aus Nutzerzeichnung\nLager-/Motorinneres schematisch; Servohalter noch offen',fontsize=13);fig.subplots_adjust(left=.01,right=.96,top=.86,bottom=.06,wspace=.04);fig.savefig(H/'Ausgabe/Vorschau_M01.png',dpi=150);plt.close(fig)
