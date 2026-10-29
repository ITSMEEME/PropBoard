#!/usr/bin/python3
"""Review exports and geometric connection checks, without changing the R02 source."""
import sys,json,csv,collections,hashlib,re
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as App
import Part
HERE=Path(__file__).resolve().parent
FIELDS=['BauteilID','Material_Annahme','Prozess_Referenz','Bemerkung','Freigabe','Referenzkoerper','Gewinde','Nennlaenge_mm','Kopfform','Gewindedarstellung']

def tagged(d):return [o for o in d.Objects if 'BauteilID' in o.PropertiesList]
def clone(d,o,shape=None):
    n=d.addObject('Part::Feature',o.Name);n.Label=o.Label
    n.Shape=o.Shape.copy() if shape is None else shape
    for k in FIELDS:
        if k in o.PropertiesList:n.addProperty('App::PropertyString',k);setattr(n,k,str(getattr(o,k)))
    n.addProperty('App::PropertyString','Quellinstanz');n.Quellinstanz=o.Document.Name+':'+o.Name
    return n

main=App.openDocument(str(HERE/'00_Horizontal_Z_R02_Montage.FCStd'))
mobile=App.openDocument(str(HERE/'02_Schlitten_R02_Detail.FCStd'))
MAIN='Horizontal_Z_R02_Montage';MOBILE='Schlitten_R02_Detail'
docs={MAIN:main,MOBILE:mobile}
joints=json.loads((HERE/'Verbindungen.json').read_text())
checks={'reference_integrity':[],'bolt_coverage':{},'shapes':{},'intersections_sample':[],
        'limits':['Geometriepruefung; kein Spannungs-, Ermuedungs-, Klemmkraft- oder Schraubenfestigkeitsnachweis.',
                  'Keine vollstaendige Kollisions- oder Bewegungspruefung; Stichprobe umfasst jede Verbindungsfamilie nach ID-Praefix, Durchmesser und Laenge; keine vollstaendige Kollisionspruefung.',
                  'Nenngewinde, keine wirklichen Gewindeflanken; Beruehrung ist kein Festigkeitsnachweis.']}
for canonical,d in docs.items():
    parts=tagged(d);bolts=[o for o in parts if o.BauteilID.startswith('BF-') and '-cap' in o.BauteilID or o in parts and o.BauteilID.startswith('BF-') and '-csk' in o.BauteilID]
    registered={j['bolt'] for j in joints if j['document']==canonical}
    missing=[o.Name for o in bolts if o.Name not in registered]
    checks['bolt_coverage'][canonical]={'modeled_bolts':len(bolts),'registered_bolts':len(registered),'unregistered':missing}
    print('Schraubenliste',canonical,len(bolts),flush=True)
    assert not missing
    representatives=list({o.BauteilID:o for o in parts}.values())
    checks['shapes'][canonical]={'result_bodies':len(parts),'checked_representative_families':len(representatives),'invalid':[],
        'multi_solid_results':[{'name':o.Name,'id':o.BauteilID,'solids':len(o.Shape.Solids)} for o in representatives if len(o.Shape.Solids)!=1]}
    for o in representatives:
        if o.Shape.isNull() or not o.Shape.isValid():checks['shapes'][canonical]['invalid'].append(o.Name)
    assert not checks['shapes'][canonical]['invalid']
for i,j in enumerate(joints):
    d=docs[j['document']];names=[j['bolt']]+j.get('targets',[])
    bad=[n for n in names if not d.getObject(n) or 'BauteilID' not in d.getObject(n).PropertiesList]
    if bad:checks['reference_integrity'].append({'index':i,'missing':bad})
assert not checks['reference_integrity'],checks['reference_integrity'][:3]
# All fixed connections plus a single native mobile set; repeated moving instances share geometry.
sample=[];seen=set()
for j in joints:
    if j['document']==MAIN and j['id'].startswith('W'):continue
    key=(j['document'],re.sub(r'_-?\d.*$', '', j['id']),j['diameter_mm'],j['length_mm'])
    if key not in seen:sample.append(j);seen.add(key)
print('Stichprobe',len(sample),flush=True)
for j in sample:
    if j['document']==MAIN and j['id'].startswith('W'):continue
    print('Pruefe',j['document'],j['id'],flush=True)
    d=docs[j['document']];b=d.getObject(j['bolt'])
    for target in j.get('targets',[]):
        o=d.getObject(target)
        volume=b.Shape.common(o.Shape).Volume
        if volume>0.02:checks['intersections_sample'].append({'document':d.Name,'connection':j['id'],
                'bolt':b.Name,'target':target,'intersection_mm3':round(volume,4)})
checks['sample_connections']=len(sample)
print('Verbindungspruefung',len(sample),'Verbindungen; Ueberschneidungen',len(checks['intersections_sample']),flush=True)

# Native detail and exploded detail, with explicit cut boundaries.
region=Part.makeBox(180,180,190,App.Vector(-290,-190,210))
node=[]
for o in tagged(main):
    if o.BauteilID=='PILOT-REF':continue
    if not o.Shape.BoundBox.intersect(region.BoundBox):continue
    clipped=o.Shape.common(region)
    if clipped.Volume>.001:node.append((o,clipped))
for exploded in [False,True]:
    d=App.newDocument('Rahmenknoten_Explodiert' if exploded else 'Rahmenknoten_Detail')
    for o,shape in node:
        s=shape.copy()
        if exploded:
            z=s.BoundBox.Center.z
            dz=-65 if z<245 else -30 if z<286 else 0 if z<335 else 45 if z<350 else 95
            s.translate(App.Vector(0,0,dz))
        n=clone(d,o,s);n.addProperty('App::PropertyString','Ausschnitt');n.Ausschnitt='Ansichtsausschnitt 180 x 180 mm; angeschnittene Rohre/Deck sind keine Einzelteilzuschnitte.'
    name='01b_Rahmenknoten_Explodiert' if exploded else '01a_Rahmenknoten_Detail'
    d.recompute();d.saveAs(str(HERE/(name+'.FCStd')));Part.export(tagged(d),str(HERE/(name+'.step')))
    App.closeDocument(d.Name)

d=App.newDocument('Batterie_R02_Detail')
for o in tagged(main):
    if o.BauteilID.startswith(('R02-BAT-','R02-TRAY-','R02-HV-','R02-LV-')):clone(d,o)
    elif o.BauteilID in ['BF-M5x80-cap','BF-SCHEIBE-M5','BF-MUTTER-M5','BF-M3x8-csk']:clone(d,o)
d.recompute();d.saveAs(str(HERE/'03_Batterie_R02_Detail.FCStd'));Part.export(tagged(d),str(HERE/'03_Batterie_R02_Detail.step'));App.closeDocument(d.Name)

counts=collections.Counter(o.BauteilID for o in tagged(main))
with (HERE/'Schraubenliste.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['Nennform_ID','Anzahl_Hauptbaugruppe','Auswahlstatus'])
    for k,v in sorted(counts.items()):
        if k.startswith('BF-'):w.writerow([k,v,'Festigkeitsklasse / Beschichtung / Lieferant / Anzugsmoment offen'])
(HERE/'Montagepruefung.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
for d in [main,mobile]:App.closeDocument(d.Name)

models=[]
specs=[('Gesamtmontage R02 – Stehen','00_Horizontal_Z_R02_Montage.FCStd'),
       ('Rahmenknoten – Detailausschnitt','01a_Rahmenknoten_Detail.FCStd'),
       ('Rahmenknoten – Explosionsansicht','01b_Rahmenknoten_Explodiert.FCStd'),
       ('Mobile Fluegelbaugruppe – Detail','02_Schlitten_R02_Detail.FCStd'),
       ('Akkubauraum und Kabeltrassen','03_Batterie_R02_Detail.FCStd')]
for title,name in specs:
    path=HERE/name;d=App.openDocument(str(path));parts=[]
    for o in tagged(d):
        code=o.BauteilID;kind='pilot' if code=='PILOT-REF' else 'wing' if code=='FL-CFK-REF' else 'fastener' if code.startswith('BF-') else 'structure'
        if code.startswith(('R02-RAIL','R02-GUIDE')):kind='stator'
        color='#303945' if 'CFK' in o.Material_Annahme else '#9daab9'
        if kind=='wing':color='#007f89'
        if kind=='pilot':color='#dba376'
        if kind=='fastener':color='#d0ac51'
        if code=='R02-HV-CABLE-REF':color='#ec771e'
        if code=='R02-LV-CABLE-REF':color='#1b9764'
        if code.startswith('R02-BAT-CASE'):color='#5376b0'
        vertices,faces=o.Shape.tessellate(2)
        parts.append({'name':o.Name,'id':code,'kind':kind,'color':color,
            'vertices':[[round(v.x,3),round(v.y,3),round(v.z,3)] for v in vertices],'faces':faces})
    models.append({'title':title,'file':'horizontal_z_r02/'+name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'parts':parts})
    App.closeDocument(d.Name)
    print('Export',name,len(parts),flush=True)
(HERE/'Modelldaten.json').write_text(json.dumps(models,separators=(',',':')))
print('Nachbearbeitung abgeschlossen',flush=True)
