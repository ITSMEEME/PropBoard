from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
H=Path(__file__).resolve().parent;O=H/'Ausgabe';a=json.loads((O/'Antriebsnachweis.json').read_text());s=json.loads((O/'Struktur_Klemmnachweis.json').read_text());fig,ax=plt.subplots(1,2,figsize=(12,4.5))
for name,label in [('low_lift','Niedrige Auftriebsannahme'),('central','Mittlere Annahme'),('high_lift','Hohe Auftriebsannahme')]:
 rows=[r for r in a['curves'] if r['polar']==name];ax[0].plot([r['rpm'] for r in rows],[r['thrust_N'] for r in rows],label=label)
ax[0].axvline(4032,color='black',linestyle='--',label='24S voll: idealer Leerlauf');ax[0].axhline(175*9.81/4,color='red',linestyle=':',label='175 kg: Schub je Motor');ax[0].set(xlabel='Drehzahl [1/min]',ylabel='Schub je Rotor [N]',title='R380: BEM mit angenommenen Profilpolaren',xlim=(2400,6000));ax[0].legend(fontsize=7);ax[0].grid(alpha=.2)
rows=[r for r in s['cases'] if r['E_GPa']==70 and r['total_mass_kg']==175 and r['thrust_factor']==1];ax[1].bar([r['variant'] for r in rows],[r['hub_translation_mm'][2] for r in rows],color=['#507a90','#507a90','#d77c38','#507a90']);ax[1].set(ylabel='Vertikale Motorauslenkung [mm]',title='175 kg, E=70 GPa, G=5 GPa, ideale Knoten');ax[1].grid(axis='y',alpha=.2)
fig.suptitle('Entwurfsrechnungen – keine gemessenen Kennfelder oder Freigaben');fig.tight_layout();fig.savefig(O/'Antrieb_Struktur.png',dpi=170);fig.savefig(O/'Antrieb_Struktur.pdf')
