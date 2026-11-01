#!/usr/bin/env python3
"""Rebuild the P13 design and its supplier inquiry files from explicit inputs."""
import argparse,csv,hashlib,json,sys,re
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as A,Part,MeshPart
from spiegeln import reflected, X, Y, Z
from mechanik import build

def write_json(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=H/'Ausgabe');ap.add_argument('--config',type=Path,default=H/'parameter.json');ap.add_argument('--no-step',action='store_true');a=ap.parse_args()
    out=a.output;out.mkdir(parents=True,exist_ok=True)
    for name in ['STEP_Sonderteile','STEP_Nennkonturen','STL','Zeichnungen_RFQ']:(out/name).mkdir(exist_ok=True)
    sources=list(H.glob('*.py'))+list((H/'basis_p12').glob('*.py'))+[a.config]
    source_hashes={str(p.relative_to(H)) if p.is_relative_to(H) else str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    config=json.loads(a.config.read_text());print('Konstruktion starten',flush=True)
    parts,scene,q=build(config);active={r['id'] for r in scene};parts={k:v for k,v in parts.items() if k in active}
    print(f'{len(scene)} Körper, {len(parts)} aktive Geometrietypen',flush=True)
    doc=A.newDocument('P13_Mechanik');meta=doc.addObject('App::FeaturePython','Konstruktionsstand')
    for k,v in dict(Revision='P13',Status='GEOMETRISCHER_ENTWURF_PRUEFUNG_ERFORDERLICH',EingabenJSON=json.dumps(config,ensure_ascii=False),Fertigungsfreigabe='NEIN',Herstellerzeichnung='Motorzeichnung vom Nutzer,01.11.2026').items():
        meta.addProperty('App::PropertyString',k,'P13');setattr(meta,k,v)
    sheet=doc.addObject('Spreadsheet::Sheet','Nennmasse');sheet.Label='Nennmaße — Dokumentation, nicht automatisch gekoppelt'
    sheet.set('A1','Parameter');sheet.set('B1','Wert');sheet.set('C1','Gruppe')
    for i,(k,v,g) in enumerate([(k,v,g) for g in ['parameters','mechanics'] for k,v in config[g].items()],2):
        sheet.set('A'+str(i),k);sheet.set('B'+str(i),str(v));sheet.set('C'+str(i),g)
    sheet.setColumnWidth('A',250);sheet.setColumnWidth('B',100)
    groups={g:doc.addObject('App::DocumentObjectGroup',g) for g in ['Sonderteile','Normteil_Nennkonturen','Kaufteil_Huellraeume']}
    bom=[]
    for i,row in enumerate(scene):
        part=parts[row['id']];o=doc.addObject('Part::Feature','Teil_'+str(i));o.Shape=row['shape'];o.Label=row['name']
        fields=dict(P13Key=row['name'],P12Key=row['name'],BauteilID=row['id'],Werkstoff=part['material'],Fertigung=part['process'],Nennmerkmale=part['features'],Normfamilie=part.get('standard',''),Quelle=part.get('source','P12-Basis, QUELLSTAND.json'),Offene_Punkte=part['open'],Freigabe='RFQ_ENTWURF_NICHT_BESTELLFREIGEGEBEN')
        for k,v in fields.items():o.addProperty('App::PropertyString',k,'P13');setattr(o,k,v)
        group='Kaufteil_Huellraeume' if row['id'].startswith('REF-AKTUATOR') else ('Normteil_Nennkonturen' if part['reference'] else 'Sonderteile')
        groups[group].addObject(o)
        if o.ViewObject:
            o.ViewObject.ShapeColor=(.15,.18,.2) if 'CFK' in row['id'] else ((.8,.64,.3) if 'Motor' in row['name'] else (.6,.65,.7))
        folder='STEP_Nennkonturen' if part['reference'] else 'STEP_Sonderteile'
        bom.append(dict(instance=row['name'],id=row['id'],variant=row['variant'],material=part['material'],process=part['process'],standard=part.get('standard',''),source=part.get('source','P12-Basis'),step=f'{folder}/{row["id"]}'+('_MZ' if row['variant']=='MZ' and not part['reference'] else '')+'.step',volume_mm3=o.Shape.Volume,valid=o.Shape.isValid() and len(o.Shape.Solids)==1 and o.Shape.Volume>0,release=o.Freigabe,open=part['open']))
    doc.recompute();native=out/'P13_Mechanik.FCStd';doc.saveAs(str(native));print('Native Baugruppe gespeichert',flush=True)
    if not a.no_step:
        objects=[o for o in doc.Objects if 'P13Key' in o.PropertiesList]
        Part.export(objects,str(out/'P13_Mechanik.step'));print('Gesamt-STEP gespeichert',flush=True)
    types=[]
    for id,part in parts.items():
        folder='STEP_Nennkonturen' if part['reference'] else 'STEP_Sonderteile'
        part['shape'].exportStep(str(out/folder/(id+'.step')))
        if not part['reference'] and any(r['id']==id and r['variant']=='MZ' for r in scene):
            reflected(part['shape'],Z).exportStep(str(out/folder/(id+'_MZ.step')))
        mesh=MeshPart.meshFromShape(Shape=part['shape'],LinearDeflection=.8,AngularDeflection=.6,Relative=False)
        mesh.write(str(out/'STL'/(id+'.stl')))
        types.append({k:v for k,v in part.items() if k!='shape'}|dict(count=sum(r['id']==id for r in scene),volume_mm3=part['shape'].Volume,bounding_box_mm=[part['shape'].BoundBox.XLength,part['shape'].BoundBox.YLength,part['shape'].BoundBox.ZLength]))
    for name,data in [('Teile.json',types),('Eingaben.json',config),('Abgeleitet.json',q),('Schnittstellen.json',q['interfaces'])]:write_json(out/name,data)
    with (out/'Stueckliste.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(bom[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(bom)
    with (out/'RFQ_Sonderteile.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['id','name','count','material','process','features','open'];w=csv.DictWriter(f,fieldnames=fields,delimiter=';',extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(p for p in types if not p['reference'])
    bb=A.BoundBox()
    for row in scene:bb.add(row['shape'].BoundBox)
    report=dict(revision='P13',parts=len(scene),types=len(types),all_valid=all(r['valid'] for r in bom),manufacturing_release=False,geometry_complete=False,collision_status='NICHT_GEPRUEFT',bounding_box_mm=dict(x=bb.XLength,y=bb.YLength,z=bb.ZLength),native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),limitations=['Normteilkonturen sind Nennmaße, keine Hersteller-CADs','Gewinde überwiegend Kern-/Nennkonturen ohne Flanken','Aktuator/Getriebe/Führung als spezifizierte Baugruppe, konkrete Lieferteile offen','CFK-Laminat und Kleb-/Füge-/Lastnachweise offen','Keine Fertigungs- oder Flugfreigabe'])
    write_json(out/'Pruefung.json',report)
    write_json(out/'Konstruktionsquellen.json',dict(native_sha256=report['native_sha256'],source_sha256=source_hashes))
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
