"""Reports numerical diagnostics without silently treating them as validation."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.cfd-tools'))
import numpy as np

out=ROOT/'cfd/results'
names=['forward_c12','forward_c16','reverse_c16','zero_pitch_c12','rest_control']
data={name:json.loads((out/(name+'.json')).read_text()) for name in names}
def last(name,key='Cz'):
    return data[name]['cycle_means'][-1][key]
f=last('forward_c16'); r=last('reverse_c16'); coarse=last('forward_c12')
first=data['forward_c16']['cycle_means'][0]['Cz']
rest=np.load(out/'rest_control.npz')['history']
zero=last('zero_pitch_c12')
result={
    'all_runs_completed':True,
    'method_validated_for_design':False,
    'flight_scale_simulation_completed':False,
    'last_cycle_Cz':{name:last(name) for name in names if name!='rest_control'},
    'relative_grid_difference_Cz':abs(coarse-f)/abs(f),
    'relative_cycle1_to_cycle2_change_forward_Cz':abs(f-first)/abs(first),
    'relative_direction_difference_Cz':abs(f-r)/abs(f),
    'moments_opposite_sign':bool(last('forward_c16','Cmoment')*last('reverse_c16','Cmoment')<0),
    'sum_of_independent_module_Cmoment':last('forward_c16','Cmoment')+last('reverse_c16','Cmoment'),
    'rest_max_abs_force_coefficient':float(np.max(np.abs(rest[:,2:4]))),
    'zero_pitch_abs_Cz_relative_to_active_coarse':abs(zero/coarse),
    'conclusion':'Exploratory low-Re 2D results only. No thrust, mass, power or flight-time clearance.'
}
(out/'Auswertung.json').write_text(json.dumps(result,indent=2))
lines=['# CFD-Voruntersuchung: Ergebnisse','',
       '**Keine realmaßstäbliche Board-Simulation und kein Tragfähigkeitsnachweis.**','',
       '| Lauf | Schritte | Mittlerer Cz, Umlauf 1 | Mittlerer Cz, Umlauf 2 | Cmoment, Umlauf 2 |',
       '| --- | ---: | ---: | ---: | ---: |']
for name in names[:-1]:
    a,b=data[name]['cycle_means']
    lines.append(f"| {name} | {data[name]['steps_completed']} | {a['Cz']:.5f} | {b['Cz']:.5f} | {b['Cmoment']:.5f} |")
lines+=['',f"Gitterunterschied (12 gegen 16 Zellen/Sehne): **{100*result['relative_grid_difference_Cz']:.1f} %** bezogen auf Cz des feineren Gitters, jeweils zweiter Umlauf.",
        '',f"Änderung Cz vom ersten zum zweiten Umlauf im feineren Vorwärtslauf: **{100*result['relative_cycle1_to_cycle2_change_forward_Cz']:.1f} %**. Periodisches Einschwingen ist damit nicht nachgewiesen.",
        '',f"Differenz der getrennten Umlaufrichtungen im zweiten Umlauf: **{100*result['relative_direction_difference_Cz']:.1f} %**. Momente mit entgegengesetztem Vorzeichen: **{result['moments_opposite_sign']}**. Dies belegt keinen vollständigen Momentenausgleich des gekoppelten Boards.",
        '',f"Ruhekontrolle: {data['rest_control']['steps_completed']} Schritte; maximaler absoluter Kraftbeiwert {result['rest_max_abs_force_coefficient']:.3g}.",
        '',f"Null-Pitch-Kontrolle: |Cz| beträgt {100*result['zero_pitch_abs_Cz_relative_to_active_coarse']:.2f} % des aktiven groben Vergleichslaufs.",
        '', 'Alle Werte stammen aus einem eigenen 2D-LBM-Prototyp bei Re = 40. Die Kontrollen ersetzen keine quantitative Referenzvalidierung des Solvers. Die Rechnung zeigt das Verhalten dieses numerischen Modells; daraus folgen keine reale Traglast, Flugzeit oder elektrische Leistung.',
        '', 'Eine belastbare 3D-CFD bei realistischer Reynolds-Zahl wurde nicht ausgeführt. Grenzen und Reproduktionsbefehle stehen in [README.md](../README.md).']
(out/'Ergebnisbericht.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(result,indent=2))
