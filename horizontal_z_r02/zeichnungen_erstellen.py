#!/usr/bin/python3
"""Editable TechDraw reference views, with dimensioned reference templates."""
import sys,json
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as App
import Part,TechDraw
HERE=Path(__file__).resolve().parent
specs=[('R02-KNOTEN','00_Horizontal_Z_R02_Montage.FCStd','R02-KNOTEN-90x80x8',(0,0,1),1.5,
 ['90 x 80 x 8 mm; 4 x D6.6','Lochbild 64 x 52; Randabstand 13 / 14 mm','Mittlere Knotenplatte: z = 286 bis 294 mm','CFK-Klemmdruck, Legierung, Passungen und Momente offen']),
 ('R02-BAT-BRIDGE','00_Horizontal_Z_R02_Montage.FCStd','R02-BAT-BRIDGE',(0,0,1),.9,
 ['24 x 200 x 5 mm; 2 x D5.5','Lochmitten ab links/unten: (12,16), (12,184)','M5x80 mit zwei Scheiben und Mutter; Distanzrohre 63.5 mm','Geometrische Rueckhaltung; Stoss-/Brand-/Landelast offen']),
 ('R02-GUIDE-MOUNT','00_Horizontal_Z_R02_Montage.FCStd','R02-GUIDE-MOUNT',(0,1,0),2,
 ['Grundplatte 48 x 50 x 6 mm plus Sitzbossen','4 Schienenschrauben M4x16: Lochbild 36 x 36','2 Brueckenschrauben M4x16: x = +/-6, z = 0','Brueckenschrauben vor Schienenmontage einsetzen']),
 ('R02-CTRL-CASE','02_Schlitten_R02_Detail.FCStd','R02-CTRL-CASE',(0,0,1),3,
 ['45 x 22 x 6.5 mm; Boden 2 mm','Deckel 1.5 mm; 4 Schrauben M2x6','2 M2x8 im Boden verbinden das Gehaeuse mit Halter','Elektronik, Waerme, EMV und Stecker noch nicht ausgelegt'])]
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
d.recompute();d.saveAs(str(HERE/'04_Referenzzeichnungen_R02.FCStd'))
App.closeDocument(d.Name)
opened=App.openDocument(str(HERE/'04_Referenzzeichnungen_R02.FCStd'));opened.recompute()
assert len([o for o in opened.Objects if o.TypeId=='TechDraw::DrawPage'])==4
(HERE/'Zeichnungspruefung.json').write_text(json.dumps(reports,indent=2))
print(json.dumps(reports,indent=2))
