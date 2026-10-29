#!/usr/bin/python3
"""Editable TechDraw reference views, with dimensioned reference templates."""
import sys,json
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as App
import Part,TechDraw
HERE=Path(__file__).resolve().parent
specs=[('KNOTEN-P01','01_CFK_Rahmen.FCStd','KNOTEN-P01',(0,0,1),1.5,
        ['90 x 80 x 8 mm','4 x D6.6; Achsenabstand 64 x 52 mm','Lochmitten ab links/unten: (13,14), (77,14), (13,66), (77,66)',
         'Legierung / Zustand / Toleranzen / Vorspannung: OFFEN']),
       ('SCHL-01','02_Fuehrung_Antrieb_Detail.FCStd','SCHL-01',(0,1,0),2,
        ['70 x 20 x 28 mm; Querbohrung D24.4','Bohrungsmitte 35 / 14 mm in Frontansicht','Kleinste nominelle Restwand oben/unten: 1.8 mm',
         'Nicht festigkeitsvalidiert; Passung und Mindestwand neu auslegen']),
       ('ERG-ST-P01','00_PropBoard_Detail_Stehen.FCStd','ERG-ST-P01',(0,0,1),.65,
        ['280 x 130 x 5 mm; 4 x D6.6','Lochmitten: (40,20), (240,20), (40,110), (240,110)',
         'Standposition durch Verschieben/Adapter einstellbar, keine Langlochmechanik modelliert','Deck-Hardpoints und Rueckhaltung: OFFEN']),
       ('BAT-BUEGEL','03_Batterie_Kabel.FCStd','BAT-BUEGEL',(0,0,1),1.25,
        ['12 x 160 x 5 mm; 2 x D6.6','Lochmitten: (6,5), (6,155) ab links/unten',
         'Nur Rueckhaltegeometrie; schmale Randabstaende nicht lastvalidiert','Verriegelung, Stosslast und Schraubverbindung neu auslegen'])]
d=App.newDocument('Referenzzeichnungen')
transient=Path('/tmp/propboard-techdraw');transient.mkdir(exist_ok=True)
d.TransientDir=str(transient)+'/'
reports=[]
for code,filename,partid,direction,scale,notes in specs:
    source=App.openDocument(str(HERE/filename))
    item=next(o for o in source.Objects if hasattr(o,'BauteilID') and o.BauteilID==partid)
    shape=item.Shape.copy();bb=shape.BoundBox;shape.translate(App.Vector(-bb.XMin,-bb.YMin,-bb.ZMin))
    obj=d.addObject('Part::Feature','Quelle_'+code.replace('-','_'));obj.Shape=shape
    obj.addProperty('App::PropertyString','Quellobjekt');obj.Quellobjekt=f'{filename}: {item.Name}'
    obj.Visibility=False
    svg=['<svg xmlns="http://www.w3.org/2000/svg" xmlns:freecad="http://www.freecadweb.org/wiki/index.php?title=Svg_Namespace" width="420mm" height="297mm" viewBox="0 0 420 297">',
         '<rect x="10" y="10" width="400" height="277" fill="none" stroke="black" stroke-width="0.4"/>',
         '<text x="18" y="23" font-size="5" font-family="sans-serif">VORENTWURF - NICHT ZUR FERTIGUNG FREIGEGEBEN</text>',
         f'<text x="250" y="55" font-size="5">{code}</text>']
    for j,note in enumerate(notes):
        # Short wrapped labels, drawing is native projected view at left.
        words=note.split();lines=[];line=''
        for word in words:
            if len(line+' '+word)>45:lines.append(line);line=word
            else:line=(line+' '+word).strip()
        lines.append(line)
        for k,line in enumerate(lines):svg.append(f'<text x="250" y="{70+j*27+k*6}" font-size="3.2">{line.replace("&","&amp;")}</text>')
    svg.extend(['<path d="M10 252 H410 M230 252 V287" stroke="black" fill="none" stroke-width="0.3"/>',
                f'<text x="18" y="265" font-size="5">PropBoard - {code}</text>',
                '<text x="18" y="277" font-size="3.5">Alle Masse mm. Werkstoff-/Toleranz-/Lastfreigabe fehlt.</text>',
                f'<text x="240" y="266" font-size="3.5">Referenzansicht; Massstab {scale}:1</text>',
                '<text x="240" y="278" font-size="3.5">Keine Gewinde oder Passungen freigegeben.</text>','</svg>'])
    template_path=HERE/'zeichnungen'/f'{code}_Vorlage.svg';template_path.write_text('\n'.join(svg))
    page=d.addObject('TechDraw::DrawPage','Blatt_'+code.replace('-','_'))
    template=d.addObject('TechDraw::DrawSVGTemplate','Vorlage_'+code.replace('-','_'));template.Template=str(template_path);page.Template=template
    view=d.addObject('TechDraw::DrawViewPart','Ansicht_'+code.replace('-','_'));view.Source=[obj]
    view.Direction=App.Vector(*direction);view.Scale=scale;view.X=120;view.Y=155
    page.addView(view);d.recompute()
    # Native computed projection export for review independent of FreeCAD GUI.
    centred=shape.copy();b=centred.BoundBox
    centred.translate(App.Vector(-(b.XMin+b.XMax)/2,-(b.YMin+b.YMax)/2,-(b.ZMin+b.ZMax)/2))
    svg_part=TechDraw.projectToSVG(centred,App.Vector(*direction))
    full='\n'.join(svg).replace('</svg>',f'<g transform="translate(120,142) scale({scale})">{svg_part}</g></svg>')
    (HERE/'zeichnungen'/f'{code}_Projektion.svg').write_text(full)
    reports.append({'id':code,'native_page':page.Name,'view':view.Name,'source':obj.Quellobjekt,
                    'projected_svg_bytes':len(svg_part),'manufacturing_release':False})
    App.closeDocument(source.Name)
d.recompute();d.saveAs(str(HERE/'05_Referenzzeichnungen.FCStd'))
App.closeDocument(d.Name)
opened=App.openDocument(str(HERE/'05_Referenzzeichnungen.FCStd'));opened.recompute()
assert len([o for o in opened.Objects if o.TypeId=='TechDraw::DrawPage'])==4
(HERE/'Zeichnungspruefung.json').write_text(json.dumps(reports,indent=2))
print(json.dumps(reports,indent=2))
