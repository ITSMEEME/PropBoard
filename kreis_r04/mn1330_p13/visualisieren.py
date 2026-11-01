#!/usr/bin/env python3
"""Render actual saved BRep tessellations, with an explicitly simplified detail selection."""
import argparse,os,sys,json
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/p13-mpl');os.environ.setdefault('XDG_CACHE_HOME','/tmp/p13-cache')
Path(os.environ['XDG_CACHE_HOME']).mkdir(exist_ok=True)
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as A,MeshPart
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
H=Path(__file__).resolve().parent;O=H/'Ausgabe'

def color(o):
    if 'SCHALE' in o.BauteilID:return '#286d98' if o.P13Key.startswith('Oben') else '#b66a3b'
    if 'CFK' in o.Werkstoff:return '#252e36'
    if 'Motor' in o.P13Key:return '#c79d42'
    if 'Taumel' in o.P13Key or 'Aktor' in o.P13Key:return '#4c9f9b'
    return '#8999a6'

def render(items,path,title,subtitle):
    grouped={};lo=np.full(3,np.inf);hi=-lo
    for o in items:
        mesh=MeshPart.meshFromShape(Shape=o.Shape,LinearDeflection=2.5,AngularDeflection=.8,Relative=False)
        vertices,faces=mesh.Topology
        v=np.array([[p.x,p.y,p.z] for p in vertices])/1000
        if len(v)==0:continue
        f=np.array(faces,dtype=int);tri=v[f];grouped.setdefault(color(o),[]).append(tri)
        lo=np.minimum(lo,v.min(axis=0));hi=np.maximum(hi,v.max(axis=0))
    fig=plt.figure(figsize=(15,10),facecolor='#f4f6f7');ax=fig.add_axes([.02,.07,.96,.80],projection='3d')
    for c,pieces in grouped.items():
        tri=np.concatenate(pieces);normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-14)
        base=np.array(matplotlib.colors.to_rgb(c));shade=.55+.45*np.abs(normal@np.array([.3,-.4,.86]));colors=np.c_[shade[:,None]*base,np.ones(len(tri))]
        ax.add_collection3d(Poly3DCollection(tri,facecolors=colors,linewidths=0,rasterized=True))
    span=np.maximum(hi-lo,.02);mid=(hi+lo)/2
    for axis,i in [('x',0),('y',1),('z',2)]:getattr(ax,'set_'+axis+'lim')(mid[i]-span[i]*.55,mid[i]+span[i]*.55)
    ax.set_box_aspect(span);ax.view_init(24,-52);ax.set_proj_type('ortho');ax.axis('off');ax.set_facecolor('#f4f6f7')
    fig.text(.04,.95,title,fontsize=23,weight='bold',color='#183548');fig.text(.04,.91,subtitle,fontsize=11,color='#365469')
    fig.text(.04,.028,'BRep-Geometrie · RFQ-/Konstruktionsentwurf · Freigabestatus und Prüfgrenzen im Bericht',fontsize=10,color='#8a542f')
    fig.savefig(path,dpi=135);plt.close(fig)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=O);O=ap.parse_args().output
    doc=A.openDocument(str(O/'P13_Mechanik.FCStd'));items=[o for o in doc.Objects if 'P13Key' in o.PropertiesList]
    r=json.loads((O/'Pruefung.json').read_text());bb=r['bounding_box_mm']
    render(items,O/'P13_Gesamtansicht.png','P13 · mechanischer Gesamtentwurf',f"{len(items)} Körper · Außenmaße {bb['x']:.0f} × {bb['y']:.0f} × {bb['z']:.0f} mm · keine Fertigungsfreigabe")
    detail=[o for o in items if o.P13Key.startswith('Oben_Aktor1_') or o.P13Key in ['Oben_Zentralplatte','Oben_Taumeltraeger','Oben_Taumelring','Oben_Taumellager','Oben_Gelenklager','Oben_GelenklagerInnen','Oben_Gleithuelse'] or (o.P13Key.startswith('Oben_Blatt1_') and any(t in o.P13Key for t in ['Patrone','Deckel','Pitchwelle','Pitchhebel','Pitchgestaenge','GestOben','GestUnten','Wurzeleinsatz','Nutmutter','Sicherungsscheibe']))]
    render(detail,O/'P13_Zentralmechanik.png','P13 · Taumelscheibe und Pitchantrieb','Detailauswahl aus CAD: Rahmen, Außenlaufbahn und Flügelschalen ausgeblendet')
    print('Gesamt- und Detailansicht aus gespeicherten BRep-Körpern erstellt')
