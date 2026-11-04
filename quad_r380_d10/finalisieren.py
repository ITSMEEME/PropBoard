from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
native=O/'Quad_HEPS_Innenverkabelung.FCStd';D=A.openDocument(str(native));read=lambda n:json.loads((O/n).read_text());cables=read('Kabel_Instanzen.json');rows=read('Instanzen.json');proof=read('Umschalter_Pruefung.json');groups={};remove=[]
for r in cables:
 if r['variant']=='V5' and r['part']=='Innenliner':groups.setdefault((r['propeller_index'],tuple(r['placement_quaternion'])),[]).append(r)
for group in groups.values():
 if len(group)==4:remove.append(group[-1])
for r in remove:
 o=D.getObject(r['instance']);master=o.LinkedObject;D.removeObject(o.Name);D.removeObject(master.Name)
for c in proof['checks']:
 removed=[r for r in remove if r['propeller_index']==c['propeller_index'] and r['variant']==c['variant']];c['mass_modeled_excluding_propellers_kg']-=sum(r['mass_kg'] for r in removed);c['visible_config_instances']-=len(removed)
cables=[r for r in cables if r not in remove];control=D.getObject('Variantensteuerung')
if not hasattr(control,'CarbonAuslegerAnzeigen'):control.addProperty('App::PropertyBool','CarbonAuslegerAnzeigen','Ansicht')
control.CarbonAuslegerAnzeigen=True
for r in rows+cables:
 if r['part'].startswith('Tube') or r['part']=='Innenliner':
  o=D.getObject(r['instance']);expr=next(exp for prop,exp in o.ExpressionEngine if prop=='Visibility')
  if not expr.startswith('Variantensteuerung.CarbonAuslegerAnzeigen'):o.setExpression('Visibility','Variantensteuerung.CarbonAuslegerAnzeigen == 1 ? ('+expr+') : 0')
D.Label='Quad D10 – Innenverkabelung und Aufnahmen für1–4 Rohre';D.recompute();D.saveAs(str(native));sha=hashlib.sha256(native.read_bytes()).hexdigest();proof['native_sha256']=sha
(O/'Umschalter_Pruefung.json').write_text(json.dumps(proof,indent=2));(O/'Kabel_Instanzen.json').write_text(json.dumps(cables,indent=2))
for name in ['Kabelbaum.json','Geometrie_Pruefung.json']:
 data=read(name);data['native_sha256']=sha;(O/name).write_text(json.dumps(data,indent=2))
(O/'Ready.json').write_text(json.dumps(dict(native_sha256=sha,unused_fourth_tube_liners_removed=len(remove))));print('Finalized',sha,flush=True)
