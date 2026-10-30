"""Parametric FreeCAD parts for FC/ESC and the user-specified 78x37x52 battery."""
import json
import FreeCAD as App
import Part
V=App.Vector


def box(l,w,h,z=0,x=0,y=0):return Part.makeBox(l,w,h,V(x-l/2,y-w/2,z))
def cylinder(d,h,z=0,x=0,y=0):return Part.makeCylinder(d/2,h,V(x,y,z))
def ring(od,id,h,z=0):return cylinder(od,h,z).cut(cylinder(id,h+2,z-1))


def corners(p):
    t=p['tray'];return [(sx*t['support_x'],sy*t['support_y']) for sx in (-1,1) for sy in (-1,1)]


def grid(p):
    h=p['board_pitch_mm']/2;return [(x,y) for x in (-h,h) for y in (-h,h)]


def recipe(name,p):
    a=p['adapter'];t=p['tray'];s=p['spacer']
    if name=='H01':
        shape=box(a['length'],a['width'],a['thickness']).fuse(ring(a['spigot_od'],a['spigot_id'],a['spigot_length'],-a['spigot_length'])).removeSplitter()
        tools=[cylinder(p['m3_clearance_mm'],a['thickness']+2,-1,x,y) for x,y in grid(p)]
        tools.append(Part.makeCylinder(a['cross_bore']/2,40,V(-20,0,-a['cross_offset_from_end']),V(1,0,0)))
        return shape.cut(Part.makeCompound(tools))
    if name=='H02':return ring(s['od'],s['bore'],s['esc_length'])
    if name=='H03':return ring(s['od'],s['bore'],s['fc_length'])
    if name=='H04':
        shape=box(t['length'],t['width'],t['connection_thickness'])
        holes=[cylinder(p['m3_clearance_mm'],t['connection_thickness']+2,-1,x,y) for x,y in grid(p)+corners(p)]
        holes.append(cylinder(20,t['connection_thickness']+2,-1))
        return shape.cut(Part.makeCompound(holes))
    if name=='H05':
        floor=box(t['length'],t['width'],t['floor'])
        wall=box(t['inside_length']+2*t['lip_thickness'],t['inside_width']+2*t['lip_thickness'],t['lip_height'],t['floor'])
        wall=wall.cut(box(t['inside_length'],t['inside_width'],t['lip_height']+2,t['floor']-1))
        # Cable exits at both short ends. No hard clamp onto a LiPo cell.
        for sign in (-1,1):wall=wall.cut(box(8,16,t['lip_height']+2,t['floor']-1,sign*(t['inside_length']/2+1),0))
        shape=floor.fuse(wall).removeSplitter()
        tools=[cylinder(p['m3_clearance_mm'],t['floor']+2,-1,x,y) for x,y in corners(p)]
        for x in (-t['strap_x'],t['strap_x']):
            for y in (-t['strap_y'],t['strap_y']):tools.append(box(t['strap_slot_length'],t['strap_slot_width'],t['floor']+2,-1,x,y))
        return shape.cut(Part.makeCompound(tools))
    if name=='H06':return ring(t['standoff_od'],t['standoff_id'],t['standoff_length'])
    if name=='H07':
        q=p['tube'];shape=ring(q['od'],q['od']-2*q['wall'],q['length'])
        for z in (a['cross_offset_from_end'],q['length']-a['cross_offset_from_end']):
            shape=shape.cut(Part.makeCylinder(a['cross_bore']/2,40,V(-20,0,z),V(1,0,0)))
        return shape
    raise ValueError(name)


class MountPart:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):
        s=recipe(obj.Rezept,json.loads(obj.ParameterJSON))
        if s.isNull() or not s.isValid() or len(s.Solids)!=1:raise ValueError(obj.Rezept)
        obj.Shape=s;obj.Placement=s.Placement
    def onDocumentRestored(self,obj):pass
    def dumps(self):return None
    def loads(self,state):pass
    def __getstate__(self):return None
    def __setstate__(self,state):pass


class EnvelopeReferences(MountPart):
    def execute(self,obj):
        b=obj.Source.Shape.BoundBox
        obj.Shape=Part.makeCompound([Part.Vertex(V(b.XMin,b.YMin,b.ZMin)),Part.Vertex(V(b.XMax,b.YMax,b.ZMax))])
