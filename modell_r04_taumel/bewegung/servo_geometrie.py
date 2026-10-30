"""Nominal servo envelopes from user drawings. Ear thickness/bores are flagged assumptions.
Axis is tangential +y, horn plane y=0; output-axis radius 58.3, local z=60.
"""
import FreeCAD as App,Part
from pathlib import Path
import json

def dimensions(typ,data):return data['Savox_SB2271SG' if typ=='Savox_SB2271SG' else 'KST_X15_755X_760us']
def housing(typ,data):
    p=dimensions(typ,data);L,W,H=p['body_mm'];total=p['overall_height_with_shaft_mm'];off=p['axis_offset_from_body_end_mm'];x0=58.3-off
    # Envelopes faithfully use known extents, without inventing internal case details.
    s=Part.makeBox(L,H,W,App.Vector(x0,-total,60-W/2))
    mid=x0+L/2;mount=p['overall_mounting_length_mm'];yf=-total+p['ear_underside_from_bottom_mm'];th=2.0 # unknown ear thickness, display assumption
    ears=Part.makeBox(mount,th,W,App.Vector(mid-mount/2,yf,60-W/2));s=s.fuse(ears)
    dx,dz=p['mounting_pitch_mm'];hole=3.2 if typ=='Savox_SB2271SG' else 3.5 # Savox bore missing; KST nominal reading of supplied drawing
    for x in (mid-dx/2,mid+dx/2):
        for z in (60-dz/2,60+dz/2):s=s.cut(Part.makeCylinder(hole/2,th+2,App.Vector(x,yf-1,z),App.Vector(0,1,0)))
    return s.removeSplitter()

def shaft(typ,data):
    p=dimensions(typ,data);gap=p['overall_height_with_shaft_mm']-p['body_mm'][2]
    return Part.makeCylinder(1.5,gap+1,App.Vector(0,-gap,0),App.Vector(0,1,0)) # 25T diameter unavailable: display only
