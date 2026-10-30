#!/usr/bin/env python3
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from reportlab.graphics import renderPDF
from reportlab.lib.units import mm
from svglib.svglib import svg2rlg
from svglib.fonts import register_font
import re
HERE=Path(__file__).resolve().parent;OUT=HERE/'Ausgabe'
register_font('sans-serif','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
files=sorted((OUT/'Zeichnungen').glob('*.svg'));assert len(files)==7
c=Canvas(str(OUT/'Halterungen_H01_Zeichnungen.pdf'),pagesize=(297*mm,210*mm));c.setTitle('R04 – FC/ESC und Akkuhalter H01 – Entwurf')
for p in files:
    svg=p.read_text()
    for label,y in [('Draufsicht',99.5),('Vorderansicht',163),('Seitenansicht',163)]:
        pattern=r'(<text x="[^"]+" y=")[^"]+(" text-anchor="middle"[^>]*>'+re.escape(label)+')'
        svg=re.sub(pattern,lambda m:m.group(1)+str(y)+m.group(2),svg)
    p.write_text(svg);d=svg2rlg(str(p));assert d;renderPDF.draw(d,c,0,0);c.showPage()
c.save();print('7 A4 drawing sheets exported')
