import os,json,math
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/propboard-matplotlib')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/propboard-cache')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'Ergebnisse.json').read_text());rho=1.225;g=9.80665
S=r['radial_quasisteady_model']['wing_area_m2'];k=r['radial_quasisteady_model']['k2_time_span_average']
fig,axes=plt.subplots(1,2,figsize=(12,5))
CL=np.linspace(.4,1.4,100)
for m in [100,200,260]:axes[0].plot(CL,np.sqrt(2*m*g/(rho*S*CL*k)),label=f'{m} kg Gesamtmasse (Szenario)')
axes[0].set(xlabel='Angenommener CL – keine verifizierte Profilpolare',ylabel='Erforderliche Bahnmittelgeschwindigkeit [m/s]',title='Geometrische Auftriebsanforderung')
axes[0].legend(fontsize=8);axes[0].grid(alpha=.2)
u=np.linspace(0,80,150);axes[1].plot(u,u*u/.45,label='Umlenkung am mittleren Radius 0,45 m')
axes[1].set(xlabel='Bahnmittelgeschwindigkeit [m/s]',ylabel='Radialkraft je kg bewegter Masse [N/kg]',title='Mechanische Last skaliert mit U²')
axes[1].grid(alpha=.2)
fig.suptitle('Analytische Szenarien – keine nachgewiesene Tragfähigkeit')
fig.tight_layout();fig.savefig(HERE/'Auftrieb_und_Umlenkung.png',dpi=170);plt.close(fig)

M0=100+10+r['partial_mass_scenario_kg'];volume=r['battery_volume_L'];density=np.linspace(100,4000,300)
fig,ax=plt.subplots(figsize=(10,5))
for eta,egrav in [(.6,.3),(.8,.3),(.8,.4)]:
    E=volume*density/1000;mb=E/egrav;m=M0+mb
    P=(m*g)**1.5/np.sqrt(2*rho*3.57)/1000/eta
    t=60*.8*E/P
    ax.plot(density,t,label=f'η = {eta:.1f}, spezifisch {egrav*1000:.0f} Wh/kg (angenommen)')
ax.axhline(15,color='black',ls='--',label='15-Minuten-Ziel')
ax.set(xlabel='Hypothetische Pack-Nennenergiedichte [Wh/L] – keine Produktdaten',ylabel='Referenzdauer [min]',
       title='6,72 L Akkuraum mit Akku-Massenrückkopplung\nAktuatorscheiben-Vergleich, 10 kg Ausrüstung, unvollständige Fahrzeugmasse')
ax.grid(alpha=.2);ax.legend(fontsize=9)
fig.tight_layout();fig.savefig(HERE/'Akku_Massenrueckkopplung.png',dpi=170);plt.close(fig)

fig,ax=plt.subplots(figsize=(10,4.5));data=r['partial_CAD_mass_scenario']
names=['Aluminiumgruppen','CFK-Rohre + Flügelhüllen','Rückschluss als Stahl','Pitchwellen als Stahl']
ax.barh(names,[v['mass_scenario_kg'] for v in data],color=['#8090a0','#246b76','#4b5669','#939da9'])
ax.set(xlabel='Masse aus CAD-Volumen × angenommener Dichte [kg]',title='Nur ausgewählte Materialgruppen – kein fertiges Fahrzeuggewicht')
ax.invert_yaxis();ax.grid(axis='x',alpha=.2)
fig.text(.5,.015,'Akku, Antriebsinnenteile, Wicklungen, Elektronik, Deck und weitere Ausstattung fehlen.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.05,1,1));fig.savefig(HERE/'CAD_Massenszenario.png',dpi=170);plt.close(fig)
print('Drei Szenariografiken erstellt')
