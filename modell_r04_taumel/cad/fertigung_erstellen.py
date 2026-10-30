#!/usr/bin/env python3
"""Build the editable manufacturing DRAFT; use official FreeCAD 1.0.2 Python.

Run erstellen.py first for assembly and sampled kinematic/collision checks.
No manufacturing release is implied by successful geometry export.
"""
import csv
import hashlib
import json
import math
import os
import re
from pathlib import Path
import sys
import tempfile
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, os.environ.get('FREECAD_LIB', '/usr/lib/freecad/lib'))
import FreeCAD as App
import Part
import MeshPart
import TechDraw
from fertigung_features import ManufacturingPart, EnvelopeReferences

OUT = HERE / 'Fertigung'
for sub in ('Einzelteile', 'STEP', 'STL', 'Zeichnungen', 'Vorlagen'):
    (OUT / sub).mkdir(parents=True, exist_ok=True)
PARAMS = json.loads((HERE / 'parameter.json').read_text())

# These are nominal design specifications, not approved production tolerances.
PARTS = [
 ('TM-01', 'Fluegel', 'Fluegel', 16, 'PA-CF', [
  'NACA 0012; Sehne 30; Profil radial 48 bis 187.5', 'Profilspanne 139.5; Hinterkante 0.6',
  'Zapfen D10; Beginn r30; Vierkant 7 x 7, Laenge 4',
  'Nutmitte r40; Breite 2.2; radiale Tiefe 1.2',
  'Flaechenkontur gemaess STEP; Profilkoordinaten als CSV'],
  'Nut-/Zapfenfestigkeit und Druckorientierung pruefen; keine Belastungsfreigabe.'),
 ('TM-02', 'Nabe', 'Nabe', 2, 'PA-CF', [
  'Aussen D88; Wand innen D72; Hoehe 20; Boden 3',
  '2 Lagersitze D42 x 7, axial -10..-3 / 3..10',
  'Schulterbohrung D38 x 6; Innenring aussen D48',
  '8 radiale Zapfenbohrungen D10.4 bei 0,45,...315 Grad',
  '16 Stiftkanaele D2 x 18; Mitten r40, z +/-4.8',
  '8 Deckelbohrungen D2.5 auf LK80, Start 22.5 Grad'],
  'D2.5 sind Modellbohrungen, keine modellierten Gewinde. Lager-/Zapfenpassung offen.'),
 ('TM-03O', 'Deckel_oben', 'Deckel_Zahnkranz_oben', 1, 'PA-CF', [
  'Modul 1; 130 Zaehne; Eingriffswinkel 20 Grad',
  'Teilkreis D130; Kopfkreis D132; Fusskreis D127.5',
  'Zahnbreite 6; Boden 3; Innen D44; Rand innen D118',
  '8 Langloecher 7 x 9 bei r32, y=+2.5..+11.5',
  '8 D3 auf LK80, Start 22.5 Grad; 8 D12 auf LK100',
  'Achsabstand zu Z20-Ritzel 75.1; Flankenspielansatz 0.15',
  'Mitnehmerbohrung D3.1 auf r31.5, Winkel -12 Grad'],
  'OBEN: eigene Datei. D3.1-Stiftaufnahme bei r31.5 / -12 Grad; Sicherung offen.'),
 ('TM-03U', 'Deckel_unten', 'Deckel_Zahnkranz_unten', 1, 'PA-CF', [
  'Modul 1; 130 Zaehne; Eingriffswinkel 20 Grad',
  'Teilkreis D130; Kopfkreis D132; Fusskreis D127.5',
  'Zahnbreite 6; Boden 3; Innen D44; Rand innen D118',
  '8 Langloecher 7 x 9 bei r32, y=-11.5..-2.5',
  '8 D3 auf LK80, Start 22.5 Grad; 8 D12 auf LK100',
  'Achsabstand zu Z20-Ritzel 75.1; Flankenspielansatz 0.15',
  'Mitnehmerbohrung D3.1 auf r31.5, Winkel +12 Grad'],
  'UNTEN: eigene Datei. D3.1-Stiftaufnahme bei r31.5 / +12 Grad; Sicherung offen.'),
 ('TM-04', 'Pitchhebel', 'Pitchhebel', 16, 'PA-CF', [
  'Vierkantaufnahme 7.2 x 7.2 durchgehend',
  'Radial r29.5..33.8; Hebel bis y11; Dicke 8',
  'Soll-Kugelmitte r32, y+/-9, z5.5 im Rotorrahmen'],
  'Kugelbolzenaufnahme und Sicherung auf Vierkant fehlen. NICHT fertigungsreif.'),
 ('TM-05', 'Taumel_Gleitkugel', 'Taumel_Gleitkugel', 2, 'PA-CF', [
  'Gleitbohrung D30.3; Huelse D34 x 18',
  'Kugelsegment D38, beschnitten auf z +/-5',
  'Gegenkugel im Innenring D38.1'],
  'Montagefolge der geschlossenen Kugelpaarung sowie Reibung und Verschleiss offen.'),
 ('TM-06', 'Taumel_Innenring', 'Taumel_Innenring', 2, 'PA-CF', [
  'Lageransatz D44.9 x 7; Kugelausschnitt D38.1',
  'Flansch innen D36 / aussen D50, Dicke 3',
  '4 Arme bei 60,180,300 und 240 Grad',
  'Armende r44; Breite 7; Arm z8..11',
  'Servo-Kugelmitten r50.3, z9.5; Fuehrung bei 240 Grad'],
  'Radiale M2-Kugelbolzenbohrungen / D3-Fuehrungsstiftaufnahme fehlen.'),
 ('TM-07', 'Taumel_Drehring', 'Taumel_Drehring', 2, 'PA-CF', [
  'Aussen D72; Lagerbohrung D58.1 x 7',
  'Schulter innen D55, Dicke 1',
  '2 Mitnehmerschlitze 3.4 bei +/-12 Grad',
  '16 D2 axial an (x32,y+/-9), 8-fach um 45 Grad'],
  'Lagersicherung und Kugelbolzen-Verschraubung mit Kaufteilen abstimmen.'),
 ('TM-08', 'Halteplatte', 'Halteplatte', 2, 'PETG', [
  'Platte 4; Mittelbohrung D30.3; Klemmkragen Hoehe 14',
  'Motorachse x75.1; Motorzentrierung D7.6',
  '4 D3.4 auf Motor-LK16, Start 45 Grad',
  '3 Stangendurchfuehrungen D10 bei r50.3',
  'Servos bei 60,180,300 Grad; Fuehrung bei 240 Grad',
  'Klemmschlitz 1.2; Fuehrungsnut 4.0, nach unten offen'],
  'Servolochbilder und Klemmschraube fehlen; tatsaechliches Servomodell erforderlich.'),
 ('TM-09', 'Kappe', 'Kappe_Stack_Pruefstand', 2, 'PETG', [
  'Platte 46 x 46 x 4; Einsteckhuelse innen D24 / aussen D27.8 x 8',
  '4 D3.4 auf Quadrat 30.5 x 30.5',
  '2 D5.2, Mittenabstand 20, mittig auf einer Achse'],
  'Kappe sitzt am Rohrende mit Einsteckhuelse; axiale Sicherung und Lastpfad offen.'),
 ('TM-10', 'Huelse_Mitte', 'Huelse_Mitte', 1, 'PETG', [
  'Innen D30.3; Aussen D33.5; Laenge 40'],
  'Axiale Lagerklemmung und Laengentoleranz mit realen Lagern festlegen.'),
 ('TM-11', 'Klemmring', 'Klemmring', 2, 'PETG', [
  'Innen D30.3; Aussen D33.5; Laenge 3.8'],
  'Bisher einfacher Distanzring: keine Klemmung oder axiale Sicherung modelliert.'),
 ('TM-12', 'Mittelrohr', 'Mittelrohr_Zuschnitt', 1, 'Aluminium, Legierung offen', [
  'Rohr D30 x 1; Zuschnittlaenge 192', 'Enden rechtwinklig entgraten; Legierung und Toleranzen offen'],
  'Halte-/Lagersitz, Befestigung und Festigkeit sind noch auszulegen.'),
]


def leaves(d, prefix=''):
    for key, value in d.items():
        path = prefix + key
        if isinstance(value, dict): yield from leaves(value, path + '.')
        else: yield path, value


def param_sheet(doc):
    sheet = doc.addObject('Spreadsheet::Sheet', 'Parameter')
    sheet.set('A1', 'Parameterpfad'); sheet.set('B1', 'Wert als JSON; mm / Grad / g')
    rows = list(leaves(PARAMS))
    for row, (key, value) in enumerate(rows, 2):
        sheet.set('A'+str(row), key); sheet.set('B'+str(row), json.dumps(value, ensure_ascii=False))
    sheet.setColumnWidth('A', 250); sheet.setColumnWidth('B', 380)
    return sheet, len(rows)


def template(path, ident, title, material, count):
    txt = lambda x,y,s,size=3: f'<text x="{x}" y="{y}" font-family="sans-serif" font-size="{size}">{escape(str(s))}</text>'
    svg = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:freecad="http://www.freecadweb.org/wiki/index.php?title=Svg_Namespace" width="297mm" height="210mm" viewBox="0 0 297 210">'
    svg += '<rect x="8" y="8" width="281" height="194" fill="white" stroke="black" stroke-width="0.35"/>'
    svg += '<path d="M8 173 H289 M8 190 H289 M195 173 V202" fill="none" stroke="black" stroke-width="0.25"/>'
    svg += txt(12,179,'COHEXIAL STUDY | R04-Taumelmodell 1:4 | ENTWURF F01',3.5)
    svg += txt(12,185,f'{ident}  {title}',4)
    svg += txt(12,195,f'Werkstoff: {material} | Anzahl je Baugruppe: {count}')
    svg += txt(12,200,'Alle Masse in mm. Keine Allgemeintoleranz freigegeben. Nicht aus der Zeichnung abmessen.',2.6)
    svg += txt(199,179,'Status: NICHT FREIGEGEBEN',3)
    svg += txt(199,185,'Datum: 2026-10-30 | Blatt 1/1',3)
    svg += txt(199,195,'3D-Datensatz + Nennmasstabelle',2.8)
    svg += txt(199,200,'FreeCAD 1.0.2 | Revision F01',2.8) + '</svg>'
    path.write_text(svg)


def oriented(shape, direction):
    result=shape.copy()
    if direction == (0,-1,0): result.rotate(App.Vector(),App.Vector(1,0,0),-90)
    elif direction == (1,0,0): result.rotate(App.Vector(),App.Vector(1,1,1),-120)
    return result


def svg_projection(shape, direction, cx, cy, width, height, label):
    # Use the same exact OpenCASCADE HLR projection as FreeCAD TechDraw.
    shape=oriented(shape,direction)
    projected = TechDraw.project(shape, App.Vector(0,0,1))[0]
    bb = projected.BoundBox
    scale = min(width/max(bb.XLength, 1), height/max(bb.YLength, 1), 4)
    content = TechDraw.projectToSVG(shape, App.Vector(0,0,1))
    content = re.sub(r'stroke-width="[^"]+"', f'stroke-width="{0.08/scale}"', content)
    center_x, center_y = (bb.XMin+bb.XMax)/2, (bb.YMin+bb.YMax)/2
    # projectToSVG includes y inversion, so translation must account for it.
    result = f'<g transform="translate({cx},{cy}) scale({scale}) translate({-center_x},{center_y})">{content}</g>'
    result += f'<text x="{cx}" y="{cy+height/2+9}" text-anchor="middle" font-family="sans-serif" font-size="3">{escape(label)} | {scale:.3f}:1</text>'
    return result


def extent_dimensions(shape, cx, cy, width, height):
    b=shape.BoundBox; scale=min(width/max(b.XLength,1),height/max(b.YLength,1),4)
    x0,x1=cx-b.XLength*scale/2,cx+b.XLength*scale/2
    y0,y1=cy-b.YLength*scale/2,cy+b.YLength*scale/2
    line=lambda x,y,u,v: f'<path d="M{x},{y} L{u},{v}" stroke="black" stroke-width="0.18" fill="none"/>'
    s=line(x0,y1,x0,y1+8)+line(x1,y1,x1,y1+8)+line(x0,y1+6,x1,y1+6)
    for x in (x0,x1): s+=line(x-1,y1+7,x+1,y1+5)
    s+=f'<text x="{cx}" y="{y1+5}" font-family="sans-serif" font-size="3" text-anchor="middle">{b.XLength:.3f}</text>'
    s+=line(x0,y0,x0-8,y0)+line(x0,y1,x0-8,y1)+line(x0-6,y0,x0-6,y1)
    for y in (y0,y1): s+=line(x0-7,y+1,x0-5,y-1)
    s+=f'<text x="{x0-7}" y="{cy}" transform="rotate(-90 {x0-7} {cy})" font-family="sans-serif" font-size="3" text-anchor="middle">{b.YLength:.3f}</text>'
    return s


def add_drawing(doc, obj, spec):
    ident,recipe,title,count,material,nominal,issue=spec
    tp=OUT/'Vorlagen'/f'{ident}.svg'; template(tp,ident,title,material,count)
    page=doc.addObject('TechDraw::DrawPage','Zeichnung')
    t=doc.addObject('TechDraw::DrawSVGTemplate','Blattvorlage');t.Template=str(tp);page.Template=t
    shape=obj.Shape
    drawing_obj=obj
    datum=doc.getObject('Bemassungsbezug') or doc.addObject('Part::FeaturePython','Bemassungsbezug')
    if 'Source' not in datum.PropertiesList:datum.addProperty('App::PropertyLink','Source')
    datum.Source=obj;EnvelopeReferences(datum);datum.Proxy.execute(datum)
    if recipe in ('Deckel_oben','Deckel_unten'):
        # Standard simplified gear representation: tooth-tip envelope, while
        # the master feature and STEP/STL retain every involute tooth.
        import erstellen as model
        from fertigung_features import configure
        configure(json.loads(obj.ParameterJSON))
        shape=model.lid_shape(1 if recipe=='Deckel_oben' else -1,teeth=False)[0]
        shape.translate(App.Vector(-shape.BoundBox.XMin,-shape.BoundBox.YMin,-shape.BoundBox.ZMin))
        drawing_obj=doc.getObject('Zeichnungsgeometrie') or doc.addObject('Part::Feature','Zeichnungsgeometrie')
        drawing_obj.Shape=shape;drawing_obj.Placement=shape.Placement
        nominal=[*nominal,'Verzahnung vereinfacht als Kopfkreis; Zahnform im STEP']
    for name,direction,cx,cy,w,h in [
        ('Draufsicht',(0,0,1),66,62,87,65),
        ('Vorderansicht',(0,-1,0),66,132,87,39),
        ('Seitenansicht',(1,0,0),155,132,48,39)]:
        projected=TechDraw.project(oriented(shape,direction), App.Vector(0,0,1))[0].BoundBox
        v=doc.addObject('TechDraw::DrawViewPart',name);page.addView(v)
        v.Source=[drawing_obj,datum];v.Direction=App.Vector(*direction)
        v.XDirection=App.Vector(0,1,0) if direction==(1,0,0) else App.Vector(1,0,0)
        # TechDraw Y is measured from the bottom of the page.
        v.X=cx;v.Y=210-cy;v.ScaleType='Custom'
        v.Scale=min(w/max(projected.XLength,1),h/max(projected.YLength,1),4)
        v.Caption=name
    section=None
    if recipe in ('Nabe','Taumel_Gleitkugel','Taumel_Innenring','Taumel_Drehring'):
        b=shape.BoundBox;ym=(b.YMin+b.YMax)/2
        pts=[App.Vector(x,ym,z) for x,z in [(b.XMin-1,b.ZMin-1),(b.XMax+1,b.ZMin-1),
              (b.XMax+1,b.ZMax+1),(b.XMin-1,b.ZMax+1),(b.XMin-1,b.ZMin-1)]]
        section=shape.section(Part.Face(Part.makePolygon(pts)))
        section_obj=doc.getObject('Schnittgeometrie') or doc.addObject('Part::Feature','Schnittgeometrie')
        section_obj.Shape=section
        sv=doc.addObject('TechDraw::DrawViewPart','Schnitt_A_A');page.addView(sv)
        sv.Source=[section_obj];sv.Direction=App.Vector(0,-1,0);sv.XDirection=App.Vector(1,0,0)
        sv.X=155;sv.Y=112;sv.ScaleType='Custom'
        sv.Scale=min(48/max(b.XLength,1),24/max(b.ZLength,1),4)
        sv.Caption='Schnitt A-A; mittige x-z-Ebene'
    bb=shape.BoundBox
    notes=doc.addObject('TechDraw::DrawViewAnnotation','Nennmasse');page.addView(notes)
    notes.Text=['NENNMASSE / MODELLBEZUG', *nominal,
                f'Huellmasse XYZ: {bb.XLength:.3f} / {bb.YLength:.3f} / {bb.ZLength:.3f}',
                'PASSUNGEN / BEFESTIGUNGEN: siehe Fertigungshinweise.md']
    notes.X=194;notes.Y=175;notes.TextSize=2.6;notes.MaxWidth=89
    # Native, associative overall dimensions using 3D vertex references.
    for axis,kind,x,y in [('x','DistanceX',66,102),('y','DistanceY',13,148),('z','DistanceZ',121,78)]:
        dim=doc.addObject('TechDraw::DrawViewDimension','Gesamtmass_'+axis.upper());page.addView(dim)
        dim.Type=kind;dim.References2D=[(doc.getObject('Draufsicht' if axis!='z' else 'Vorderansicht'), [])]
        dim.References3D=[(datum,['Vertex1']),(datum,['Vertex2'])]
        dim.X=x;dim.Y=y;dim.FormatSpec='%.3f'
    doc.recompute()
    # Portable drawing exports, with explicit sizes and complete nominal table.
    svg=tp.read_text().removesuffix('</svg>')
    svg+=svg_projection(shape,(0,0,1),66,58,87,65,'Draufsicht')
    svg+=extent_dimensions(shape,66,58,87,65)
    svg+=svg_projection(shape,(0,-1,0),66,136,87,36,'Vorderansicht')
    svg+=svg_projection(shape,(1,0,0),153,136,48,36,'Seitenansicht')
    if section is not None:
        svg+=svg_projection(section,(0,-1,0),155,98,48,24,'Schnitt A-A; mittige x-z-Ebene')
    for row,text in enumerate(['NENNMASSE / MODELLBEZUG',*nominal,
                              f'Huellmasse XYZ: {bb.XLength:.3f} / {bb.YLength:.3f} / {bb.ZLength:.3f}',
                              'Passungen und offene Schnittstellen:', 'siehe Fertigungshinweise.md']):
        svg+=f'<text x="119" y="{20+row*5}" font-family="sans-serif" font-size="2.6">{escape(text)}</text>'
    svg+='</svg>'
    (OUT/'Zeichnungen'/f'{ident}_{title}.svg').write_text(svg)


def main():
    selected=next((a.split('=',1)[1] for a in sys.argv if a.startswith('--part=')),None)
    if selected and selected not in [p[0] for p in PARTS]: raise ValueError(selected)
    results=json.loads((OUT/'Geometriepruefung.json').read_text())['parts'] if selected else []
    if selected: results=[r for r in results if r['id']!=selected]
    for spec in PARTS:
        ident,recipe,title,count,material,nominal,issue=spec
        if selected and ident!=selected:continue
        print('Generating',ident,title,flush=True)
        doc=App.newDocument(ident.replace('-','_'))
        doc.TransientDir=tempfile.mkdtemp(prefix='propboard-td-')+'/'
        sheet,n=param_sheet(doc)
        obj=doc.addObject('Part::FeaturePython','Bauteil')
        for key,value in [('BauteilID',ident),('Rezept',recipe),('Werkstoff',material),
                          ('Status','FERTIGUNGSENTWURF_KEINE_FREIGABE'),
                          ('ParameterJSON',json.dumps(PARAMS,ensure_ascii=False)),('OffenePunkte',issue)]:
            obj.addProperty('App::PropertyString',key,'Fertigung');setattr(obj,key,value)
        obj.addProperty('App::PropertyInteger','Anzahl','Fertigung');obj.Anzahl=count
        obj.addProperty('App::PropertyLink','ParameterTabelle','Parameter');obj.ParameterTabelle=sheet
        obj.addProperty('App::PropertyInteger','ParameterZeilen','Parameter');obj.ParameterZeilen=n
        ManufacturingPart(obj);doc.recompute()
        # Surface Python feature errors in headless runs, where Console output
        # otherwise has no terminal observer.
        if obj.Shape.isNull(): obj.Proxy.execute(obj)
        s=obj.Shape
        assert not s.isNull() and s.isValid() and len(s.Solids)==1,(ident, len(s.Solids))
        add_drawing(doc,obj,spec)
        doc.recompute()
        if obj.State and 'Invalid' in obj.State: raise ValueError((ident,obj.State))
        doc.saveAs(str(OUT/'Einzelteile'/f'{ident}_{title}.FCStd'))
        Part.export([obj],str(OUT/'STEP'/f'{ident}_{title}.step'))
        if recipe!='Mittelrohr':
            mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=0.02,AngularDeflection=0.25,Relative=False)
            mesh.write(str(OUT/'STL'/f'{ident}_{title}.stl'))
            assert mesh.isSolid(),ident
        # Verify STEP exchange independently of the original in-memory shape.
        exchanged=Part.Shape();exchanged.read(str(OUT/'STEP'/f'{ident}_{title}.step'))
        assert exchanged.isValid() and len(exchanged.Solids)==1,ident
        # OCCT integrates trimmed curved faces differently after STEP healing.
        # Record the error; require <0.01% volume and <0.01 mm in all bounds.
        # Nabe was independently cross-checked by 0.005 mm tessellations.
        volume_error=abs(exchanged.Volume-s.Volume)/s.Volume
        assert volume_error<1e-4,(ident,volume_error)
        bound_error=max(abs(getattr(exchanged.BoundBox,k)-getattr(s.BoundBox,k))
                        for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax'))
        assert bound_error<0.01,(ident,bound_error)
        bb=s.BoundBox
        dims=[bb.XLength,bb.YLength,bb.ZLength]
        fits=all(a<=b for a,b in zip(sorted(dims),sorted(PARAMS['print']['bed']))) if recipe!='Mittelrohr' else None
        results.append(dict(id=ident,name=title,recipe=recipe,count=count,material=material,
                            volume_mm3=s.Volume,dimensions_mm=dims,valid=True,solids=1,
                            step_roundtrip=True,step_volume_relative_error=volume_error,
                            step_bounds_max_error_mm=bound_error,
                            print_bed_envelope_fits=fits,open_issue=issue))
        App.closeDocument(doc.Name)
    results.sort(key=lambda r:r['id'])
    # Actual tabulated profile coordinates; STEP is the controlling surface.
    import erstellen as model
    with (OUT/'Profil_NACA0012.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['q_Sehnenanteil','y_lokal_mm','z_oben_mm','z_unten_mm'])
        for i in range(121):
            q=(1-math.cos(math.pi*i/120))/2
            w.writerow([q,(0.5-q)*PARAMS['blade']['chord'],model.naca_half(q),-model.naca_half(q)])
    with (OUT/'Fertigungsstueckliste.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f,delimiter=';');w.writerow(['ID','Benennung','Anzahl','Werkstoff','Verfahren','Status','Offene_Punkte'])
        for r in results:w.writerow([r['id'],r['name'],r['count'],r['material'],'Zuschnitt' if r['recipe']=='Mittelrohr' else '3D-Druck; Parameter mit Slicer festlegen','NICHT FREIGEGEBEN',r['open_issue']])
    (OUT/'Geometriepruefung.json').write_text(json.dumps({'freecad':App.Version(), 'parts':results},ensure_ascii=False,indent=2))
    (OUT/'Parameterstand.json').write_text(json.dumps(PARAMS,ensure_ascii=False,indent=2))
    print('Completed',len(results),'unique manufacturing parts',flush=True)


def redraw():
    for spec in PARTS:
        ident,_,title,*_=spec
        path=OUT/'Einzelteile'/f'{ident}_{title}.FCStd'
        doc=App.openDocument(str(path))
        doc.TransientDir=tempfile.mkdtemp(prefix='propboard-td-')+'/'
        for obj in reversed(doc.Objects):
            if obj.TypeId.startswith('TechDraw::'): doc.removeObject(obj.Name)
        doc.getObject('Bauteil').OffenePunkte=spec[-1]
        add_drawing(doc,doc.getObject('Bauteil'),spec)
        doc.recompute();doc.save();App.closeDocument(doc.Name)
        print('Redrawn',ident,flush=True)


if __name__=='__main__':
    redraw() if '--drawings-only' in sys.argv else main()
