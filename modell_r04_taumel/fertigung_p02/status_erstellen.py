#!/usr/bin/env python3
"""Publish explicit production blockers, never promote drawings by file extension."""
import json,csv
from pathlib import Path
H=Path(__file__).resolve().parent;R=H/'Ausgabe';p=json.loads((H/'anforderungen.json').read_text());v=json.loads((R/'Integrationspruefung.json').read_text());n=json.loads((R/'Normteilpruefung.json').read_text())
assert not p['overall_production_release'] and not v['production_release']
rows=[]
for x in p['required_purchased_modules']:rows.append(dict(id=x['id'],quantity=x['quantity'],item=x['item'],status='GESPERRT_ANSCHLUSSDATEN_FEHLEN',required='; '.join(x['required'])))
for x in p['critical_in_house_interfaces']:rows.append(dict(id=x['id'],quantity='',item=x['part'],status='GESPERRT_KONSTRUKTION_OFFEN',required=x['blocking']))
for x in n['assets']:rows.append(dict(id=x['id'],quantity='siehe Integration',item=x['id'],status='NENNMASSE_GEPRUEFT_KEINE_GESAMTFREIGABE',required='Klemmlänge, Schraubensicherung, Gegenflächen und Montagekontext prüfen'))
with (R/'Fertigungsstatus_P02.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['id','quantity','item','status','required'],delimiter=';');w.writeheader();w.writerows(rows)
report=dict(overall_production_release=False,purchased_module_types_awaiting_data=len(p['required_purchased_modules']),in_house_interface_blockers=len(p['critical_in_house_interfaces']),dimension_checked_imported_standard_types=len(n['assets']),native_assembly_imported_fastener_instances=v['imported_bolts']+v['imported_cap_nuts'],rules=['Purchased internals do not need in-house production drawings','Community library geometry is not automatically original manufacturer CAD','Unmatched bearing sizes are not scaled replacements','A STEP/STL/FCStd file is not by itself a production release'])
(R/'Fertigungsstatus_P02.json').write_text(json.dumps(report,indent=2));print(report)
