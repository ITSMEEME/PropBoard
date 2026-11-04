import json,csv
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';routing=json.loads((O/'Kabelbaum.json').read_text());rho20=.017241;temperature=80;rho=rho20*(1+.00393*(temperature-20));rows=[]
for current in [112.91,177.03]:
 for n in routing['nets']:
  if n['circuit'] not in ['DC branch','main DC']:continue
  I=current*(4 if n['circuit']=='main DC' else 1);length=n['length_mm']/1000;resistance=rho*length/n['conductor_mm2'];rows.append(dict(net=n['net'],branch_reference_A=current,current_A=I,length_m=length,section_mm2=n['conductor_mm2'],conductor_temperature_assumed_C=temperature,resistance_ohm=resistance,drop_V=I*resistance,heat_W=I*I*resistance))
(O/'Elektrische_Auslegung.json').write_text(json.dumps(dict(reference='24S up to100.8V,4 MN1330 branches.112.91A comes from NS52 80% test point;177.03A maximum test point has no holding duration. These are wiring comparison loads,not R380 validated currents.',cases=rows,main_reference_currents_A=[451.64,708.12],assumed_branch_mm2=35,assumed_phase_mm2=25,assumed_main_mm2=95,dc_copper_only=True,ampacity_pass=None,phase_current_verified=False,protection_selected=False,flight_release=False,scope='Ohmic losses only for routed lengths; excludesOEM150mm leads,lugs,contacts,switches,fuses.80C is evaluation temperature,not predicted equilibrium. No thermal ampacity,short-circuit,I2t,insulation or creepage release.'),indent=2))
with (O/'Kabel_Von_Nach.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['net','circuit','from_port','to_port','conductor_mm2','assumed_outer_diameter_mm','length_mm','minimum_sampled_bend_radius_mm','terminations_verified']);w.writeheader();w.writerows({k:n[k] for k in w.fieldnames} for n in routing['nets'])
