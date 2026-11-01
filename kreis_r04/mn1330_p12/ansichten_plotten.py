#!/usr/bin/env python3
import json,math,os,argparse
os.environ.setdefault('MPLCONFIGDIR','/tmp/propboard-mpl')
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
H=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=H/'Ausgabe');args=ap.parse_args();O=args.output
frozen=json.loads((O/'Parameter_Eingefroren.json').read_text());p=frozen['parameters'];q=frozen['derived'];R=q['guide_ring_outer']/1000;HH=q['height']/2000;L=q['level_z']/1000
rows=json.loads((O/'Ansichten_Mesh.json').read_text())
C={'frame':'#8c9ba7','motor':'#e9b15b','drive':'#6ec6ce','guide':'#d5dce2','upper':'#2a94ce','lower':'#dd8950','column':'#9acc88','cfk':'#252c33'}
def category(r):
 i=r['id']
 if i.startswith('CFK-ROHR'):return 'cfk'
 if i=='REF-FLUEGEL':return 'upper' if r['name'].startswith('Oben') else 'lower'
 if i=='REF-MN1330':return 'motor'
 if i in ['P12-002','P12-003','P12-004','P12-005']:return 'drive'
 if i in ['P12-010','P12-011']:return 'column'
 if i in ['P12-014','P12-015','P12-016','P12-017','P12-018','P12-019','P12-020','P12-022','REF-7202B']:return 'guide'
 return 'frame'
for r in rows:r['v']=np.array(r['vertices'])/1000;r['f']=np.array(r['triangles']);r['cat']=category(r)
def draw3(ax,elev,azim):
 for r in rows:
  tris=r['v'][r['f']];norm=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]);norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-15)
  base=np.array(matplotlib.colors.to_rgb(C[r['cat']]));light=.55+.45*np.abs(norm@np.array([.25,-.4,.88]));colors=np.c_[light[:,None]*base,np.ones(len(tris))]
  p=Poly3DCollection(tris,facecolors=colors,linewidths=0,rasterized=True);ax.add_collection3d(p)
 ax.set_xlim(-R*1.06,R*1.06);ax.set_ylim(-R*1.06,R*1.06);ax.set_zlim(-HH*1.1,HH*1.1);ax.set_box_aspect((R*2.12,R*2.12,HH*2.2),zoom=1.35);ax.view_init(elev=elev,azim=azim);ax.set_proj_type('ortho');ax.set_facecolor('#f5f7f9');ax.set_axis_off()
fig=plt.figure(figsize=(16,10),facecolor='#f5f7f9');ax=fig.add_axes([0,.11,1,.82],projection='3d');draw3(ax,24,-53)
fig.text(.035,.95,'P12 · MN1330 · CAD-Zwischenstand',fontsize=23,weight='bold',color='#193247')
fig.text(.035,.912,f"Rotoren Ø {2*p['rotor_radius']:g} mm · Rahmen {q.get('frame_envelope_x',2*q['guide_ring_outer']):.0f} × {q.get('frame_envelope_y',2*q['guide_ring_outer']):.0f} mm · Höhe {q['height']:g} mm",fontsize=13,color='#354f60')
fig.legend(handles=[Patch(color=C[k],label=v) for k,v in [('upper','Obere Flügel: Profilreferenz'),('lower','Untere Flügel: Profilreferenz'),('motor','MN1330: Kaufteilhülle'),('drive','Mitnehmer / Innenring'),('frame','Metallische Knoten / Führungen'),('cfk','CFK-Rohre 20 × 17 mm')]],loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,.025),fontsize=11)
fig.text(.035,.018,'Formfaktor-Entwurf · Pitchanlenkung, Lageranschlüsse und Fertigungsfreigabe noch offen',fontsize=10,color='#885624')
fig.savefig(O/'Zwischenstand_P12_Perspektive.png',dpi=145);plt.close(fig)
# Orthographic projected meshes, sorted by depth. No imagined parts.
fig,axes=plt.subplots(1,2,figsize=(16,9),facecolor='#f5f7f9');fig.suptitle('P12 · Draufsicht und Vorderansicht aus dem CAD-Modell',fontsize=21,weight='bold',color='#193247',y=.97)
from matplotlib.collections import PolyCollection
for ax,mode in zip(axes,['top','front']):
 records=[]
 for r in rows:
  tris=r['v'][r['f']];dims=[0,1] if mode=='top' else [0,2];depth=2 if mode=='top' else 1
  for tri in tris:
   uv=tri[:,dims]
   if abs((uv[1,0]-uv[0,0])*(uv[2,1]-uv[0,1])-(uv[1,1]-uv[0,1])*(uv[2,0]-uv[0,0]))<1e-10:continue
   records.append((tri[:,depth].mean(),uv,C[r['cat']]))
 records.sort(key=lambda x:x[0]);ax.add_collection(PolyCollection([r[1] for r in records],facecolors=[r[2] for r in records],edgecolors='none',linewidths=0,rasterized=True))
 ax.set_aspect('equal');ax.set_xlim(-R*1.13,R*1.13);ax.set_ylim((-R*1.16,R*1.16) if mode=='top' else (-max(HH*1.4,R*.6),max(HH*1.4,R*.6)));ax.set_facecolor('#f5f7f9');ax.axis('off')
 if mode=='top':
  ax.set_title(f"Draufsicht · Breite {q.get('frame_envelope_x',2*q['guide_ring_outer']):.0f} mm",fontsize=14,pad=16)
  ax.annotate('',(-R,-R*1.07),(R,-R*1.07),arrowprops={'arrowstyle':'|-|','color':'#304959'});ax.text(0,-R*1.12,f"{2*q['guide_ring_outer']:g} mm",ha='center',fontsize=11)
  ax.add_patch(plt.Circle((0,0),p['rotor_radius']/1000,fill=False,color='#2a94ce',ls='--',lw=.8))
 else:
  ax.set_title(f"Vorderansicht · Ebenenabstand {p['level_spacing']:g} mm",fontsize=14,pad=16)
  ax.annotate('',(R*1.04,-HH),(R*1.04,HH),arrowprops={'arrowstyle':'|-|','color':'#304959'});ax.text(R*1.07,0,f"{q['height']:g} mm",rotation=90,va='center',fontsize=11)
  ax.annotate('',(-R*.87,-L),(-R*.87,L),arrowprops={'arrowstyle':'|-|','color':'#304959'});ax.text(-R*.90,0,f"{p['level_spacing']:g} mm",rotation=90,va='center',ha='right',fontsize=10)
fig.text(.04,.07,'Außenrahmen, Motoren und Mitnehmer sind konstruiert. Flügel sind aerodynamische Vollkörper als Bauraumreferenz.',fontsize=11,color='#354f60')
fig.text(.04,.04,'Noch kein vollständiges Fertigungsmodell: Pitchlager, Taumelscheibenmechanik und finale Verbindungen sind offen.',fontsize=11,color='#885624')
fig.subplots_adjust(top=.87,bottom=.12,wspace=.06);fig.savefig(O/'Zwischenstand_P12_Orthogonal.png',dpi=145);plt.close(fig)
print('2 CAD preview PNGs written')
