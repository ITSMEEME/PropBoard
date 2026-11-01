"""Retained standard-family clevis pins, washers, and split pins."""
import FreeCAD as A,Part
from mechanik import V,box,cyl,ring

def pin(d,L,point,direction,name,angle,sign,define,put,parts,z=0,span_override=None):
    id=f'STD-DIN1444B-{d}x{L}'
    cotter=1.6 if d==6 else 2
    hole=L-(3 if d==8 else 1.5)
    if id not in parts:
        shape=cyl(d/2,L).fuse(cyl((d+4)/2,3,z=-3))
        shape=shape.cut(Part.makeCylinder(cotter/2,2*d,V(-d,0,hole),V(1,0,0)))
        define(id,f'Gabelbolzen{d}×{L}',shape,'Stahl','Kaufen',
               f'FormB,Ø{d}×{L}; QuerlochØ{cotter}; Nennkontur mit Kopf; reale Lieferform abgleichen','DIN1444 FormB Maßfamilie')
    r=A.Rotation(V(0,0,1),V(*direction));point=V(*point)
    def place(tid,suffix,shape):
        s=shape.copy()
        if d==6:s.rotate(V(),V(0,0,1),90)
        s.Placement=A.Placement(point,r).multiply(s.Placement)
        put(tid,name+suffix,shape=s,angle=angle,sign=sign,z=z)
    place(id,'_Bolzen',parts[id]['shape'])
    # Stacked washers and positive cotter retention do not clamp the moving links.
    wid=f'STD-ISO7089-M{d}-GELENK'
    if wid not in parts:define(wid,'Gelenkscheibe',ring(d/2+.2,d,0,1.6),'Stahl200HV','Kaufen',
        f'Ø{d+.4}/Ø{2*d}×1.6; Nennkontur','ISO7089 Maßfamilie')
    place(wid,'_ScheibeKopf',parts[wid]['shape'])
    span=span_override if span_override is not None else (28 if d==6 else 20)
    place(wid,'_ScheibeSplint',parts[wid]['shape'].translated(V(0,0,span+1.6)))
    if d==8:
        for j,start in enumerate([span+3.2,span+4.8]):place(wid,f'_Distanzscheibe{j}',parts[wid]['shape'].translated(V(0,0,start)))
    else:place(wid,'_Distanzscheibe',parts[wid]['shape'].translated(V(0,0,span+3.2)))
    if d==6 and span==22:
        sid='STD-DIN988-6-L1'
        if sid not in parts:define(sid,'PassscheibeM6×1',ring(3.1,6,0,1),'Stahl','Kaufen','Ø6.2/12×1; exakte Liefermaße abgleichen','DIN988 Maßfamilie')
        place(sid,'_Passscheibe',parts[sid]['shape'].translated(V(0,0,span+4.8)))
    cid=f'STD-DIN94-{cotter}'
    if cid not in parts:
        wire=cotter/5;rad=cotter*.27
        s=Part.makeCylinder(wire,12,V(-6,rad,0),V(1,0,0)).fuse(Part.makeCylinder(wire,12,V(-6,-rad,0),V(1,0,0)))
        end=Part.makeTorus(rad,wire,V(6,0,0),V(0,0,1)).common(box(3,4,4,6,-2,-2))
        s=s.fuse(end)
        define(cid,'Splint',s,'Weicher Stahl','Kaufen; nach Montage Schenkel spreizen',
               'Haarnadelartige Einbaukontur; genormte Lieferform und Längen vor Bestellung abgleichen','DIN94 / ISO1234 Familie')
    place(cid,'_Splint',parts[cid]['shape'].translated(V(0,0,hole)))

