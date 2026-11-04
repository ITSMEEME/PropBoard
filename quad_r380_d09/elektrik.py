from pathlib import Path
import json,csv
H=Path(__file__).resolve().parent;O=H/'Ausgabe';source=json.loads((O/'Kabelbaum.json').read_text());rows=[];rho=.017241*(1+.00393*60)
for n in source['nets']:
 for branch_current in [112.91,177.03]:
  if n['circuit'] not in ['DC branch','main DC']:continue
  current=branch_current*(4 if n['circuit']=='main DC' else 1);resistance=rho*n['length_mm']/1000/n['conductor_mm2'];rows.append(dict(propeller_index=n['propeller_index'],net=n['net'],branch_reference_A=branch_current,current_A=current,resistance_ohm=resistance,voltage_drop_V=current*resistance,heat_W=current**2*resistance))
(O/'Elektrische_Auslegung.json').write_text(json.dumps(dict(native_sha256=source['native_sha256'],cases=rows,ampacity_verified=False,scope='DC copper at assumed80C,NS52 comparison currents112.91/177.03A per motor,not HEP-S measured currents. Phase ampacity and motor lead transitions unknown. No contacts,clips,lugs,fuses,ESC/battery or closed circuit integrated.'),indent=2))
with (O/'Kabel_Von_Nach.csv').open('w') as f:
 fields=['propeller_index','net','circuit','from_port','to_port','conductor_mm2','assumed_outer_diameter_mm','length_mm','minimum_sampled_bend_radius_mm','terminations_verified'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:n[k] for k in fields} for n in source['nets'])
