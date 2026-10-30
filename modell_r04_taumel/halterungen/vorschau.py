#!/usr/bin/env python3
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
HERE=Path(__file__).resolve().parent;OUT=HERE/'Ausgabe';data=np.load(OUT/'Vorschau_Daten.npz');tris=data['triangles'];groups=data['groups']
colors=[(0.15,.4,.75),(.3,.6,.85),(.12,.65,.4),(1,.5,.12),(.25,.55,.7),(.48,.5,.52)]

def draw(ax,mask,limits,title):
 for g,c in enumerate(colors):
  t=tris[mask & (groups==g)]
  if not len(t):continue
  normals=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);normals/=np.linalg.norm(normals,axis=1)[:,None]+1e-12
  light=np.array([.3,-.4,.8]);light/=np.linalg.norm(light)
  shade=.5+.5*np.abs(normals@light)
  face=np.column_stack([np.clip(np.array(c)*shade[:,None],0,1),np.full(len(t),.42 if g==3 else 1.)])
  ax.add_collection3d(Poly3DCollection(t,facecolors=face,edgecolor='none',linewidths=0))
 ax.set_xlim(*limits[0]);ax.set_ylim(*limits[1]);ax.set_zlim(*limits[2]);ax.set_box_aspect([b-a for a,b in limits]);ax.view_init(elev=23,azim=-56)
 ax.set_axis_off();ax.set_title(title,fontsize=10)
fig=plt.figure(figsize=(14,10));gs=fig.add_gridspec(2,2,width_ratios=[1.2,1])
centers=tris.mean(axis=1)
draw(fig.add_subplot(gs[:,0],projection='3d'),np.ones(len(tris),dtype=bool),[(-195,195),(-195,195),(-180,145)],'Gesamtaufbau: F01-Rotor + Halterungen H01')
draw(fig.add_subplot(gs[0,1],projection='3d'),((centers[:,2]>90) & np.isin(groups,[2,3,4])),[(-42,42),(-45,40),(90,140)],'Oben: FC / ESC, offene Abstandshalter')
draw(fig.add_subplot(gs[1,1],projection='3d'),((centers[:,2]<-95) & np.isin(groups,[2,3,4])),[(-58,58),(-38,38),(-176,-94)],'Unten: Akku 78 x 37 x 52, Wanne und Zugstangen')
fig.suptitle('H01 – Montageentwurf, keine Freigabe | gruen: Halter, orange: Akku-Bauraum, blau: Rotor/Elektronik\nPCB-Komponenten sind Referenzhuellen; Gurte als Kaufteile vorgesehen, hier nicht dargestellt.',fontsize=11)
fig.tight_layout(rect=[0,0,1,.94]);fig.savefig(OUT/'Vorschau_H01.png',dpi=140);plt.close(fig)
