import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/propboard-mpl')
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
H=Path(__file__).resolve().parent;O=H/'Ausgabe';a=json.loads((O/'Propeller_Studie.json').read_text());s=json.loads((O/'Struktur_Klemmnachweis.json').read_text());cfg=a['configurations'];fig,ax=plt.subplots(1,3,figsize=(15,4.8))
for fm in [.55,.65,.75]:
 rows=[next(c for c in a['cases'] if c['propeller']==p['id'] and c['flight_minutes']==5 and c['figure_of_merit_assumed']==fm) for p in cfg];ax[0].plot([p['diameter_in'] for p in cfg],[r['total_shaft_power_kW']/4 if r['converged'] else float('nan') for r in rows],marker='o',label=f'Gütegrad {fm:.2f}')
ax[0].axhline(8.916,color='black',linestyle='--',label='NS52-Prüfpunkt, keine Dauergrenze');ax[0].set(xlabel='Durchmesser [Zoll]',ylabel='Wellenleistung je Motor [kW]',title='100 kg Nutzlast, 5 min, Akku-Rückkopplung',ylim=(0,55));ax[0].legend(fontsize=7);ax[0].grid(alpha=.2)
ax[1].plot([p['diameter_in'] for p in cfg],[p['unprotected_width_mm']/1000 for p in cfg],marker='o');ax[1].axhline(1.7,linestyle=':',color='red');ax[1].set(xlabel='Durchmesser [Zoll]',ylabel='Breite ohne Schutz [m]',title='Automatischer Rahmenabstand');ax[1].grid(alpha=.2)
for v in ['V1','V2','V3','V4']:
 rows=[next(c for c in s['cases'] if c['propeller_index']==i and c['variant']==v and c['E_GPa']==70 and c['total_mass_kg']==175 and c['thrust_factor']==1) for i in range(10)];ax[2].plot([p['diameter_in'] for p in cfg],[r['hub_translation_mm'][2] for r in rows],label=v,marker='o')
ax[2].set(xlabel='Durchmesser [Zoll]',ylabel='Vertikale Motorauslenkung [mm]',title='175 kg, E70/G5 GPa, starre Knoten');ax[2].legend();ax[2].grid(alpha=.2);fig.suptitle('Entwurfssensitivitäten – keine HEP-S-Messkennfelder oder Materialfreigaben');fig.tight_layout();fig.savefig(O/'Propeller_Struktur_Vergleich.png',dpi=170);fig.savefig(O/'Propeller_Struktur_Vergleich.pdf')
