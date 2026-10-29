import json,math,sys,os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/propboard-matplotlib')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/propboard-cache')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'cad'))
from umlauf_kinematik import state,perimeter
p=json.loads((HERE/'parameter.json').read_text());L=perimeter(p['straight_m'],p['radius_m'])
fig=plt.figure(figsize=(12,7));ax=fig.add_subplot(111,projection='3d')
for k,z in enumerate(p['levels_z_m']):
    color=['#00838a','#bc4b14'][k];direction=1 if k==0 else -1
    for side in (-1,1):
        rr=p['radius_m']+side*p['rail_radial_offset_m']
        ll=perimeter(p['straight_m'],rr)
        pts=np.array([state(s,p['straight_m'],rr)[:2] for s in np.linspace(0,ll,300)])
        ax.plot(pts[:,0],pts[:,1],np.full(len(pts),z),color=color,lw=1.8)
    for i in range(p['wings_per_level']):
        x,y,tx,ty,_=state(i*L/p['wings_per_level'],p['straight_m'],p['radius_m'])
        tangent=np.array([direction*tx,direction*ty,0]);radial=np.array([-ty,tx,0])
        nose=tangent*math.cos(math.radians(p['pitch_deg']))+np.array([0,0,math.sin(math.radians(p['pitch_deg']))])
        centre=np.array([x,y,z]);vertices=[centre+a*nose*p['chord_m']/2+b*radial*p['span_m']/2 for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]
        ax.add_collection3d(Poly3DCollection([vertices],facecolor=color,edgecolor='black',linewidth=.3,alpha=.8))
    ax.quiver(0,.45,z,.22*direction,0,0,color=color,lw=3)
ax.add_collection3d(Poly3DCollection([[(-.6,-.15,.25),(.6,-.15,.25),(.6,.15,.25),(-.6,.15,.25)]],facecolor='gray',alpha=.7))
ax.set(xlim=(-1.08,1.08),ylim=(-.85,.85),zlim=(-.25,.35),xlabel='x [m]',ylabel='y [m]',zlabel='z [m]',title='Horizontale Gegenläufe – 240 mm Abstand in z\nGeometrieannahme, keine konstruktive Auslegung')
ax.set_box_aspect((2.16,1.7,.6));ax.view_init(elev=26,azim=-55)
fig.tight_layout();fig.savefig(HERE/'Horizontal_Konzept.png',dpi=170);plt.close(fig)

names=['single_c16','stack_240_c16','stack_360_c16','stack_240_c24']
if not all((HERE/'results'/f'{n}.json').exists() for n in names):
    print('CAD preview generated; CFD results still incomplete.');sys.exit(0)
data={n:json.loads((HERE/'results'/f'{n}.json').read_text()) for n in names}
last=lambda n:data[n]['block_means'][-1]['Cz_total']
single=last('single_c16')
result={'scope':'2D straight sections only; no complete 3D horizontal loop comparison',
        'last_five_passages_Cz':{n:last(n) for n in names},
        'stack_240_vs_two_independent_rows_ratio':last('stack_240_c16')/(2*single),
        'stack_360_vs_two_independent_rows_ratio':last('stack_360_c16')/(2*single),
        'relative_grid_difference_stack_240':abs(last('stack_240_c24')-last('stack_240_c16'))/abs(last('stack_240_c24')),
        'relative_last_blocks_change':{n:abs(last(n)-data[n]['block_means'][-2]['Cz_total'])/abs(last(n)) for n in names},
        'design_validated':False,'real_air_3d_cfd':False}
(HERE/'results/Vergleich.json').write_text(json.dumps(result,indent=2))
lines=['# Vergleichsversuch: horizontale Bänder in zwei z-Ebenen','',
       '**Nur lokale 2D-Strömung gerader Abschnitte bei Re = 40; keine 3D-Simulation der gesamten Umläufe.**','',
       '| Versuch | Gitter | Schritte | Mittlerer Cz gesamt, letzte fünf Durchgänge |',
       '| --- | --- | ---: | ---: |']
for n in names:lines.append(f"| {n} | {data[n]['grid']} | {data[n]['steps_completed']} | {last(n):.5f} |")
lines+=['',f"240-mm-Stapel / zwei unabhängige Einzelreihen: **{result['stack_240_vs_two_independent_rows_ratio']:.3f}**.",
        '',f"360-mm-Stapel / zwei unabhängige Einzelreihen: **{result['stack_360_vs_two_independent_rows_ratio']:.3f}**.",
        '',f"Gitterunterschied des 240-mm-Stapels (16/24 Zellen pro Sehne): **{100*result['relative_grid_difference_stack_240']:.1f} %**.",
        '', 'Änderung des mittleren Cz der letzten zwei Fünferblöcke:', '']
for n,v in result['relative_last_blocks_change'].items():lines.append(f'- {n}: {100*v:.1f} %.')
lines+=['','Die Kennwerte gelten nur für dieses vereinfachte Rechenmodell. Die Kraftreferenz ist eine Profilsehne pro Einheitsspannweite, beim Stapel wird über beide Reihen summiert. Der Vergleichsfaktor verwendet deshalb zweimal den Einzelreihenwert. Keine Umrechnung auf reale Traglast oder elektrische Leistung.',
        '', 'Der frühere vertikale Umlauf hatte eine andere Geometrie und eine andere Kraftnormierung. Ein direkter Leistungsvergleich zwischen beiden vollständigen Fahrzeugvarianten ist mit diesen 2D-Rechnungen nicht zulässig.',
        '', 'Grenzen: künstliche Viskosität, grobe Profilauflösung, treppenförmige bewegte Wände, periodische gerade Flügelreihen, gedämpfte äußere Ränder, keine Kurvenfahrt, keine endliche Spannweite, keine Führung/Schlitten, kein Deck und kein Mensch. Der eigene Solver ist nicht quantitativ gegen einen externen Referenzfall validiert. Zwei Gitter und die beobachteten Zeitverläufe sind kein vollständiger Konvergenznachweis.']
(HERE/'results/Vergleichsbericht.md').write_text('\n'.join(lines)+'\n')
fig,ax=plt.subplots(figsize=(10,5))
for n in names:
    a=np.load(HERE/'results'/f'{n}.npz')['history'];window=round(len(a)/data[n]['passages'])
    curve=np.convolve(a[:,2],np.ones(window)/window,mode='valid')
    if n=='single_c16':curve*=2
    ax.plot(a[window-1:,0],curve,label='2 × Einzelreihe (Referenz)' if n=='single_c16' else n)
ax.set(xlabel='Flügeldurchgänge',ylabel='Cz gesamt (Mittel über einen Durchgang)',title='Lokaler 2D-Vergleich, Re = 40 – kein vollständiger 3D-Umlauf')
ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(HERE/'results/Kraftvergleich.png',dpi=160);plt.close(fig)
print(json.dumps(result,indent=2))
