"""Standalone technical figures from the exact exported CAD meshes."""
import os,json,re
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/p14-mpl');os.environ.setdefault('XDG_CACHE_HOME','/tmp/p14-cache')
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
H=Path(__file__).resolve().parent;O=H/'Ausgabe';F=H/'Ansichten';F.mkdir(exist_ok=True)
model=json.loads((O/'Modell.json').read_text());meshes=json.loads((O/'Meshes.json').read_text())
def colour(id):
    t=model['types'][id]
    if id=='CFK01':return '#253b48'
    if id=='MN1330':return '#a92c36'
    if id=='SERVO':return '#e77930'
    if t['material']=='PTFE':return '#99c7d4'
    if id.startswith('ROD_') or id in ['A18','A27']:return '#2188ae'
    if t['kind']=='Normlager':return '#83919d'
    return '#b9c7d0'
def make(name,title,predicate,bounds,view):
    fig=plt.figure(figsize=(12,8),facecolor='#f7fafb');ax=fig.add_subplot(111,projection='3d');ax.set_facecolor('#f7fafb');polys=[];colours=[]
    for r in model['scene']:
        id=r['part']
        if not predicate(r) or re.match(r'^(F[0-9]|N[0-9]|TIE)',id):continue
        m=meshes[id];v=np.asarray(m['vertices_mm']);M=np.asarray(r['neutral_transform']).reshape(4,4);v=v@M[:3,:3].T+M[:3,3]
        if r['sign']<0:v*=np.array([-1,1,-1])
        v+=np.asarray(model['derived']['unit_centres_mm'][r['unit']]);tri=v[np.asarray(m['triangles'])]
        keep=np.ones(len(tri),dtype=bool)
        for axis,(lo,hi) in enumerate(bounds):keep&=(tri[:,:,axis].max(1)>=lo)&(tri[:,:,axis].min(1)<=hi)
        tri=tri[keep];polys.append(tri);colours.extend([colour(id)]*len(tri))
    collection=Poly3DCollection(np.concatenate(polys),facecolors=colours,edgecolors='none',linewidths=0,rasterized=True);ax.add_collection3d(collection)
    ax.set(xlim=bounds[0],ylim=bounds[1],zlim=bounds[2],xlabel='x [mm]',ylabel='y [mm]',zlabel='z [mm]');ax.set_box_aspect([hi-lo for lo,hi in bounds]);ax.view_init(*view);ax.tick_params(labelsize=8)
    fig.suptitle(title,ha='left',x=.06,y=.94,fontsize=17,fontweight='bold',color='#183e52')
    fig.text(.06,.895,'P14 | CAD-Entwicklung | Aluminiumstruktur + freitragende CFK-Blätter',fontsize=10,color='#577384')
    fig.text(.06,.045,'Geometrie aus FCStd-Export · Bauteil-/Materialannahmen · keine Fertigungs- oder Flugfreigabe',fontsize=9,color='#577384')
    fig.text(.06,.025,'Native SHA256 '+model['source_native_sha256'][:24]+'…',fontsize=8,color='#6e8794')
    fig.subplots_adjust(left=.03,right=.97,bottom=.1,top=.86);fig.savefig(F/(name+'.png'),dpi=170);plt.close(fig)
make('P14_Gesamt','Zentrale Lagerung ohne Außenrahmen',lambda r:True,[[-800,800],[-800,800],[-280,280]],(24,-64))
make('P14_Servo','PH54-Servo mit extern gelagerter28-mm-Umlenkung',lambda r:r['sign']>0 and (r['servo_index']==0 or r['part'] in ['A20','A20C']),[[95,280],[-85,140],[38,125]],(27,-65))
make('P14_Wurzel','Innenbefestigung: Integralflansch und CFK-Klemmung',lambda r:r['sign']>0 and (r['blade_index']==0 or r['part'] in ['A09','A04','A21','A24','B7212']),[[35,320],[-65,110],[105,235]],(24,-65))
# Canonical CAD prototypes, separated along their common pin axis. The explode
# offsets are illustration only, not an assertion about installation order.
fig=plt.figure(figsize=(13,7),facecolor='#f7fafb');ax=fig.add_subplot(111,projection='3d');ax.set_facecolor('#f7fafb')
items=[('J_PIN8',-48,'Kopfbolzen'),('J_SP_L',-18,'Distanz'),('J_EYE_P',0,'Alu-Auge / M6'),('J_GE8_O',15,'GE8 außen'),('J_GE8_I',29,'GE8 innen'),('J_SHIM16',39,'Passscheibe'),('J_CLIP16',49,'DIN472'),('J_SP_R',57,'Distanz'),('J_W8',64,'Scheibe'),('J_COTTER',71,'Splint')]
legend=[];alltri=[];allcolours=[]
for i,(id,offset,label) in enumerate(items,1):
    m=meshes[id];v=np.asarray(m['vertices_mm'])+np.array([0,offset,0]);tri=v[np.asarray(m['triangles'])]
    alltri.append(tri);shade='#2188ae' if id=='J_EYE_P' else '#455d6b' if id in ['J_CLIP16','J_COTTER'] else colour(id);allcolours.extend([shade]*len(tri))
    centre=np.asarray(m['vertices_mm'])[:,1].mean()+offset
    ax.text(0,centre,18,str(i),fontsize=10,color='#183e52');legend.append(f'{i} {label}')
ax.add_collection3d(Poly3DCollection(np.concatenate(alltri),facecolors=allcolours,edgecolors='none',linewidths=0,rasterized=True))
ax.set(xlim=(-12,36),ylim=(-69,93),zlim=(-14,18),xlabel='x [mm]',ylabel='Bolzenachse y [mm]',zlabel='z [mm]');ax.set_box_aspect([48,162,32]);ax.view_init(30,-30);ax.tick_params(labelsize=7)
fig.suptitle('Trennbares Gelenk · GE8E / Alu-Gabelbolzen',x=.05,y=.95,ha='left',fontsize=17,fontweight='bold',color='#183e52')
fig.text(.05,.89,'Exakte CAD-Teilnetze, zur Ansicht axial auseinandergezogen · Gabel ausgeblendet',fontsize=10,color='#577384')
fig.text(.05,.10,' · '.join(legend[:5]),fontsize=9,color='#183e52');fig.text(.05,.075,' · '.join(legend[5:]),fontsize=9,color='#183e52')
fig.text(.05,.035,'Nenngeometrie, Lieferprofil und Tragzahlen offen · Native SHA256 '+model['source_native_sha256'][:20]+'…',fontsize=8,color='#577384')
fig.subplots_adjust(left=.01,right=.99,bottom=.15,top=.87);fig.savefig(F/'P14_Gelenk_Explodiert.png',dpi=170);plt.close(fig)
print('4 CAD figures generated')
