#!/usr/bin/env python3
"""Build editable P12 native CAD and synchronized exports from one parameter source."""
import argparse,csv,hashlib,json,sys
from pathlib import Path
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as A,Part,Mesh
from parameter_schema import load,validate,SCHEMA
import parametrik
H=Path(__file__).resolve().parent

def collisions(items):
    rows=[]
    for i,a in enumerate(items):
        for b in items[i+1:]:
            if not a.Shape.BoundBox.intersect(b.Shape.BoundBox):continue
            v=a.Shape.common(b.Shape).Volume
            if v>.01:rows.append(dict(a=a.P12Key,b=b.P12Key,volume_mm3=v))
    return rows

def export(doc,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    for f in ['STEP','STL']:(out/f).mkdir(exist_ok=True)
    doc.recompute();driver=doc.getObject('P12_Modell');p=json.loads(driver.LastValidParameters);validate(p);q=json.loads(driver.DerivedJSON)
    if driver.Error:raise ValueError(driver.Error)
    if 'Invalid' in driver.State or 'Invalid' in doc.getObject('Parameter').State:raise ValueError('FreeCAD meldet einen ungültigen Tabellen-/Ausdruckszustand.')
    for k,value in p.items():
        try:shown=float(doc.getObject('Parameter').get(k))
        except (ValueError,TypeError):raise ValueError('Kein gültiger numerischer Tabellenwert: '+k)
        if abs(shown-value)>1e-9:raise ValueError('Tabellenstand und Geometrie passen nicht zusammen: '+k)
    # Restored documents may not have the transient export shape cache.
    if not hasattr(driver.Proxy,'parts'):
        from geometrie import build
        driver.Proxy.parts,driver.Proxy.scene,_=build(p,json.loads(driver.MaterialsJSON))
    parts=driver.Proxy.parts;items=[o for o in doc.Objects if 'P12Key' in o.PropertiesList]
    for id,part in parts.items():
        if not part['reference']:part['shape'].exportStep(str(out/'STEP'/f'{id}.step'))
        mesh=Mesh.Mesh(part['shape'].tessellate(.8));mesh.write(str(out/'STL'/f'{id}.stl'))
    variants={}
    for row in driver.Proxy.scene:
        id=row['id'];variant=row['variant']
        if parts[id]['reference'] or variant=='NOMINAL':continue
        key=id+'_'+variant
        if key in variants:continue
        variants[key]=row['manufacturing_shape']
    for key,shape in variants.items():
        shape.exportStep(str(out/'STEP'/f'{key}.step'));Mesh.Mesh(shape.tessellate(.8)).write(str(out/'STL'/f'{key}.stl'))
    doc.recompute();native=out/'P12_MN1330.FCStd';doc.saveAs(str(native));Part.export(items,str(out/'P12_MN1330.step'))
    bom=[dict(instance=o.P12Key,id=o.BauteilID,material=o.Werkstoff,process=o.Fertigung,manufacturing_variant=o.Fertigungsvariante,manufacturing_step='' if o.Status!='FERTIGUNGSENTWURF' else ('STEP/'+o.BauteilID+('' if o.Fertigungsvariante=='NOMINAL' else '_'+o.Fertigungsvariante)+'.step'),reference=o.Status!='FERTIGUNGSENTWURF',volume_mm3=o.Shape.Volume,open_items=o.Offene_Punkte) for o in items]
    with (out/'Stueckliste.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(bom[0]),delimiter=';');w.writeheader();w.writerows(bom)
    types=[{k:v for k,v in part.items() if k!='shape'}|dict(count=sum(r['id']==id for r in bom),volume_mm3=part['shape'].Volume,valid=part['shape'].isValid(),solids=len(part['shape'].Solids)) for id,part in parts.items()]
    for name,data in [('Teile.json',types),('Parameter_Eingefroren.json',{'parameters':p,'derived':q,'hash':driver.LastValidHash,'materials_assumed':json.loads(driver.MaterialsJSON)})]:(out/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    with (out/'Parameterliste.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f,delimiter=';');w.writerow(['Parameter','Wert','Einheit','Gruppe','Minimum','Maximum'])
        for k,s in SCHEMA.items():w.writerow([k,p[k],s['unit'],s['group'],s['minimum'],s['maximum']])
    if p['frame_mode']==1:
        from zuschnitt import export_cut_plan
        export_cut_plan(out,p,q)
    overlap=collisions(items);bounds=Part.Compound([o.Shape for o in items]).BoundBox
    report=dict(revision='P12_PARAMETRISCH',manufacturing_release=False,parts=len(items),types=len(parts),all_single_solids_valid=all(o.Shape.isValid() and len(o.Shape.Solids)==1 for o in items),overlaps=overlap,battery_excluded=True,parameter_hash=driver.LastValidHash,native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),bounding_box_mm=dict(x=bounds.XLength,y=bounds.YLength,z=bounds.ZLength),parameter_count=len(SCHEMA),native_spreadsheet_expressions=True,limitations=['Pitchmechanik und Rotor-Pitchlageranschluss bleiben offen','Nur neutrale Geometrie, kein vollständiger Bewegungs-/Festigkeitsnachweis','Kaufteilabmessungen sind Referenzen, keine frei skalierbaren realen Produkte'])
    (out/'Pruefung.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');return report

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,default=H/'parameter.json');ap.add_argument('--set',action='append',default=[]);ap.add_argument('--output',type=Path,default=H/'Ausgabe');args=ap.parse_args();overrides={}
    for item in args.set:
        k,v=item.split('=',1);overrides[k]=float(v)
    raw=json.loads(args.config.read_text());p=load(args.config,overrides);d=A.newDocument('P12_MN1330');model=parametrik.create(d,p,raw['materials_assumed']);d.recompute()
    if model.Error:raise ValueError(model.Error)
    report=export(d,args.output);print(json.dumps({k:report[k] for k in ['parts','types','overlaps','parameter_count','bounding_box_mm']}))
    if report['overlaps']:raise SystemExit('Kollisionen gefunden: Pruefung.json lesen; keine Freigabe.')
if __name__=='__main__':main()
