#!/usr/bin/env python3
"""Render the actual FreeCAD-HLR drawing SVG files to a combined PDF.

Use .cfd-tools/venv/bin/python (svglib 1.5.1, reportlab 4.4.9).
"""
from pathlib import Path
import re
from reportlab.pdfgen.canvas import Canvas
from reportlab.graphics import renderPDF
from reportlab.lib.units import mm
from svglib.svglib import svg2rlg
from svglib.fonts import register_font

HERE=Path(__file__).resolve().parent
OUT=HERE/'Fertigung'
register_font('sans-serif','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
files=sorted((OUT/'Zeichnungen').glob('*.svg'))
assert len(files)==13, len(files)
pdf=Canvas(str(OUT/'Fertigungszeichnungen_F01.pdf'),pagesize=(297*mm,210*mm))
pdf.setTitle('Cohexial Study – R04 Taumelmodell – Fertigungsentwurf F01')
for path in files:
    # Keep captions clear of overall dimension lines. Idempotent so already
    # generated sheets from the CAD run and fresh exports use identical layout.
    svg=path.read_text()
    for label,y in [('Draufsicht',99.5),('Vorderansicht',163),('Seitenansicht',163),('Schnitt A-A',119)]:
        pattern=r'(<text x="[^"]+" y=")[^"]+(" text-anchor="middle"[^>]*>'+re.escape(label)+')'
        svg=re.sub(pattern,lambda m:m.group(1)+str(y)+m.group(2),svg)
    path.write_text(svg)
    drawing=svg2rlg(str(path))
    assert drawing and drawing.width>0,path
    renderPDF.draw(drawing,pdf,0,0)
    pdf.showPage()
pdf.save()
print('PDF:',len(files),'drawing sheets')
