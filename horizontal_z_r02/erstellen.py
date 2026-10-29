#!/usr/bin/python3
"""Horizontal Z R02: mechanically explicit assembly, not a flight release.

Threaded mating geometry uses nominal cylinders. Thread designation,
fastener length and seat are separate properties, never tap-drill drawings.
"""
import sys,json,math,csv,hashlib,copy
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent
source=ROOT/'konstruktion/erstellen.py'
ns={'__file__':str(source),'__name__':'r02_helpers'}
exec(compile(source.read_text().split('frame_doc=doc(')[0],str(source),'exec'),ns)
App=ns['App'];Part=ns['Part'];state=ns['state'];perimeter=ns['perimeter']
P=json.loads((OUT/'parameter.json').read_text());P.update({'longeron_bottom_z_mm':295,'crossbeam_bottom_z_mm':245,'deck_top_z_mm':361,'upper_frame_raise_mm':15})
ns['HERE']=OUT;ns['P']=P
doc=ns['doc'];group=ns['group'];box=ns['box'];cyl=ns['cyl'];feature=ns['feature'];plate=ns['plate']
PARTS=ns['DOC_PARTS'];JOINTS=[];OPEN=[];REPORT={};CACHE={};CUTS=[]
FIELDS=['BauteilID','Material_Annahme','Prozess_Referenz','Bemerkung','Freigabe','Referenzkoerper']
VECTOR=lambda v:App.Vector(*v) if not isinstance(v,App.Vector) else v


def prop(o,k,value):
    if k not in o.PropertiesList:o.addProperty('App::PropertyString',k)
    setattr(o,k,str(value))


def cut(o,shapes,label=None):
    d=o.Document;tool=d.addObject('Part::Feature',o.Name+'_Werkzeug')
    tool.Shape=shapes[0].multiFuse(shapes[1:]).removeSplitter() if len(shapes)>1 else shapes[0]
    assert tool.Shape.isValid(),tool.Name
    n=d.addObject('Part::Cut',o.Name+'_Bearbeitet');n.Base=o;n.Tool=tool
    for k in FIELDS:prop(n,k,getattr(o,k))
    for g in o.InList:
        if g.TypeId=='App::DocumentObjectGroup':g.addObject(n)
    if label:n.Label=label
    PARTS[d.Name].remove(o);PARTS[d.Name].append(n)
    for record in JOINTS:
        if record.get('document')==d.Name:
            record['targets']=[n.Name if name==o.Name else name for name in record.get('targets',[])]
    for k in FIELDS:
        if k in o.PropertiesList:o.removeProperty(k)
    o.Visibility=False;tool.Visibility=False
    d.recompute();assert not n.Shape.isNull() and n.Shape.isValid(),n.Name
    CUTS.append(n.Name)
    return n


def remove(o):
    PARTS[o.Document.Name].remove(o);o.Document.removeObject(o.Name)


def cylinder(r,h,point,axis=(0,0,1)):return Part.makeCylinder(r,h,VECTOR(point),VECTOR(axis))


def hole(point,axis,r,length):return cylinder(r,length,point,axis)


def hexshape(af,h,z=0):
    rad=af/math.sqrt(3)
    v=[App.Vector(rad*math.cos(i*math.pi/3),rad*math.sin(i*math.pi/3),z) for i in range(6)]
    return Part.Face(Part.Wire(Part.makePolygon(v+[v[0]]).Edges)).extrude(App.Vector(0,0,h))


# Basic nominal dimensions for assembly representation, supplier/grade TBD.
HD={2:(3.8,2,1.5),3:(5.5,3,2.5),4:(7,4,3),5:(8.5,5,4),6:(10,6,5)}
WS={2:(4.5,2.2,.3),3:(7,3.2,.5),4:(9,4.3,.8),5:(10,5.3,1),6:(12,6.4,1.6)}
NT={2:(4,1.6),3:(5.5,2.4),4:(7,3.2),5:(8,4),6:(10,5)}
PITCH={2:.4,3:.5,4:.7,5:.8,6:1,8:1.25}


def boltshape(diam,length,style):
    key=(diam,length,style)
    if key in CACHE:return CACHE[key]
    if style=='cap':
        hd,h,af=HD[diam]
        s=cylinder(diam/2,length,(0,0,-length)).fuse(cylinder(hd/2,h,(0,0,0)))
        s=s.cut(hexshape(af,h/2+.1,h/2))
    else:
        h=diam/2;hd=2*diam;af=HD[diam][2]*.8
        s=cylinder(diam/2,length-h,(0,0,-length)).fuse(Part.makeCone(diam/2,hd/2,h,App.Vector(0,0,-h)))
        s=s.cut(hexshape(af,h*.65+.1,-h*.65))
    s=s.removeSplitter();assert s.isValid() and len(s.Solids)==1,key
    CACHE[key]=s;return s


def place_shape(shape,point,axis):
    p=App.Placement(VECTOR(point),App.Rotation(App.Vector(0,0,1),VECTOR(axis)))
    s=shape.copy();s.Placement=p.multiply(s.Placement);return s


def bolt(d,g,diam,length,point,axis=(0,0,1),style='cap',joint=''):
    o=feature(d,g,f'Schraube_M{diam}x{length}',place_shape(boltshape(diam,length,style),point,axis),
              f'BF-M{diam}x{length}-{style}','Stahl / Festigkeitsklasse und Beschichtung TBD','Kaufteil-Nennform',
              'Gewinde vereinfacht als Nennzylinder; keine freigegebene Norm-/Lieferantenauswahl.')
    for k,v in {'Gewinde':f'M{diam}x{PITCH[diam]}','Nennlaenge_mm':length,'Kopfform':style,
                'Verbindung':joint,'Sitzpunkt_mm':json.dumps(list(VECTOR(point))),
                'Achse_nach_aussen':json.dumps(list(VECTOR(axis))),
                'Gewindedarstellung':'Vereinfacht, keine Helix; Innengewinde keine Fertigungsbohrung'}.items():prop(o,k,v)
    return o


def washer(d,g,diam,point,axis=(0,0,1)):
    od,id_,t=WS[diam];s=cylinder(od/2,t,(0,0,0)).cut(cylinder(id_/2,t+2,(0,0,-1)))
    return feature(d,g,f'Scheibe_M{diam}',place_shape(s,point,axis),f'BF-SCHEIBE-M{diam}',
                   'Stahl / Korrosionspaarung TBD','Kaufteil-Nennform','Nennmasse; Haerte und Lieferant offen')


def nut(d,g,diam,point,axis=(0,0,1)):
    af,h=NT[diam];s=hexshape(af,h).cut(cylinder(diam/2,h+2,(0,0,-1)))
    o=feature(d,g,f'Mutter_M{diam}',place_shape(s,point,axis),f'BF-MUTTER-M{diam}',
              'Stahl / Festigkeitsklasse TBD','Kaufteil-Nennform','Innengewinde als Nennhuelle; Sicherung/Vorspannung offen')
    prop(o,'Gewinde',f'M{diam}x{PITCH[diam]}');return o


def clamp_stack(d,g,diam,length,point,thickness,joint,targets):
    t=WS[diam][2];h=NT[diam][1];v=VECTOR(point)
    b=bolt(d,g,diam,length,v+App.Vector(0,0,t),joint=joint)
    w1=washer(d,g,diam,v);w2=washer(d,g,diam,v-App.Vector(0,0,thickness+t))
    n=nut(d,g,diam,v-App.Vector(0,0,thickness+t+h))
    protrusion=length-(thickness+2*t+h)
    assert protrusion>=2*PITCH[diam]-.001,(joint,protrusion)
    JOINTS.append({'document':d.Name,'id':joint,'bolt':b.Name,'diameter_mm':diam,'length_mm':length,
                   'stack_mm':thickness,'thread_protrusion_mm':protrusion,
                   'targets':[x.Name for x in targets],'kind':'Durchsteckschraube, zwei Scheiben, Mutter'})
    return b


def threadjoint(d,g,diam,length,point,axis,joint,targets,engagement):
    b=bolt(d,g,diam,length,point,axis,'csk',joint)
    JOINTS.append({'document':d.Name,'id':joint,'bolt':b.Name,'diameter_mm':diam,'length_mm':length,
                   'nominal_engagement_mm':engagement,'targets':[x.Name for x in targets],
                   'kind':'Senkschraube, Innengewinde-Nennhuelle, Festigkeit offen'})
    return b


def csktool(point,axis,diam,length):
    normal=VECTOR(axis);base=VECTOR(point)-normal*(diam/2)
    return [hole(VECTOR(point)-normal*length,normal,diam/2+.2,length+.1),
            Part.makeCone(diam/2,diam,diam/2,base,normal)]


def axis_stack(d,g,diam,length,point,normal,thickness,joint,targets):
    n=VECTOR(normal);p=VECTOR(point);t=WS[diam][2];h=NT[diam][1]
    b=bolt(d,g,diam,length,p+n*t,n,joint=joint)
    washer(d,g,diam,p,n);washer(d,g,diam,p-n*(thickness+t),n);nut(d,g,diam,p-n*(thickness+t+h),n)
    protr=length-(thickness+2*t+h)
    assert protr>=2*PITCH[diam]-.001,(joint,protr)
    JOINTS.append({'document':d.Name,'id':joint,'bolt':b.Name,'targets':[v.Name for v in targets],
                   'diameter_mm':diam,'length_mm':length,'stack_mm':thickness,'thread_protrusion_mm':protr,
                   'kind':'Durchsteckverbindung, zwei Scheiben und Mutter'})
    return b


def outer_frame_connectors(d):
    g=group(d,'11_Aussenpfosten_T_Knoten')
    for x in (-200,0,200):
        for y in (-825,825):
            block=Part.makeBox(60,44,85,App.Vector(x-30,y-22,210))
            void=Part.makeBox(40.6,46,40.6,App.Vector(x-20.3,y-23,244.7))
            shape=block.cut(void).cut(cylinder(15.3,36,(x,y,209)))
            halves=[]
            for sign in (-1,1):
                clip=Part.makeBox(30,46,87,App.Vector(x+.3 if sign==1 else x-30.3,y-23,209))
                part=feature(d,g,'T_Knoten_Halbschale',shape.common(clip),'R02-TKNOTEN30','Aluminium TBD','Fraesreferenz',
                             'Umschliesst Quertraeger und Pfosten mit Isolierlagen; Last/Vorspannung offen')
                part=cut(part,[hole((x-31,yy,z),(1,0,0),2.2,62) for yy in (y-18,y+18) for z in (225,290)])
                halves.append(part)
            for yy in (y-18,y+18):
                for z in (225,290):axis_stack(d,g,4,70,(x-30,yy,z),(-1,0,0),60,'TKNOTEN30',halves)
            ring=cylinder(15.3,34.7,(x,y,210)).cut(cylinder(15,36.7,(x,y,209)))
            feature(d,g,'T_Knoten_Rundisolation',ring,'R02-TISO30','GFK TBD','Isolierhuelse','Keine Klemmdruck-/Korrosionsfreigabe')
            cyl(d,g,'T_Knoten_Endisolation',15,.3,(x,y,244.7),id='R02-TISO-END',mat='GFK TBD')
            outer=Part.makeBox(40.6,44,40.6,App.Vector(x-20.3,y-22,244.7))
            inner=Part.makeBox(40,46,40,App.Vector(x-20,y-23,245))
            feature(d,g,'T_Knoten_Vierkantisolation',outer.cut(inner),'R02-TISO40','GFK TBD','Isolierhuelle','Referenz 0.3 mm, keine Lastfreigabe')


def guide_supports(d):
    g=group(d,'12_Stator_Postenklemmen')
    # The straight tracks are at y = +/-130 and +/-770.
    railparts=[o for o in PARTS[d.Name] if o.BauteilID in ['R02-RAIL-C','R02-RAIL-JOCH']]
    for x in (-200,0,200):
        for level in (-120,120):
            for sign in (-1,1):
                for outer in (False,True):
                    cy=sign*(825 if outer else 85);ro=21 if outer else 13;ri=15.3 if outer else 8.3
                    diameter=4 if outer else 3;af=24 if outer else 21;off=18 if outer else 11
                    base=cylinder(ro,40,(x,cy,level-20)).cut(cylinder(ri,42,(x,cy,level-21)))
                    for yy in (cy-off,cy+off):
                        for zz in (level-12,level+12):
                            base=base.fuse(Part.makeBox(2*af,6,8,App.Vector(x-af,yy-3,zz-4)))
                    # Bridge clear of the four counter-sunk rail attachment seats.
                    end1=sign*(796 if outer else 104);end2=cy-sign*(16 if outer else -9)
                    bridge=Part.makeBox(24,abs(end2-end1),30,App.Vector(x-12,min(end1,end2),level-15))
                    base=base.fuse(bridge)
                    base=base.cut(cylinder(ri,42,(x,cy,level-21)))
                    halves=[]
                    tools=[hole((x-af-1,yy,zz),(1,0,0),diameter/2+.2,2*af+2)
                           for yy in (cy-off,cy+off) for zz in (level-12,level+12)]
                    for sx in (-1,1):
                        clip=Part.makeBox(af+1,100,44,App.Vector(x+.3 if sx==1 else x-af-1.3,cy-50,level-22))
                        obj=feature(d,g,'Stator_Spannhalbschale',base.common(clip),'R02-GUIDE-CLAMP-OUT' if outer else 'R02-GUIDE-CLAMP-IN',
                                    'Aluminium TBD','Fraesreferenz','Klemmlasten, Steifigkeit und Kontaktdruck offen')
                        halves.append(cut(obj,tools))
                    for yy in (cy-off,cy+off):
                        for zz in (level-12,level+12):axis_stack(d,g,diameter,55 if outer else 50,(x-af,yy,zz),(-1,0,0),2*af,'STATOR_CLAMP',halves)
                    feature(d,g,'Stator_Spannhuelsen_Isolation',cylinder(ri,40,(x,cy,level-20)).cut(cylinder(15 if outer else 8,42,(x,cy,level-21))),
                            'R02-GUIDE-CLAMP-ISO','GFK TBD','Isolierlage','Keine Werkstoff- oder elektrische Freigabe')
                    # Back plate, screws outboard of the short central bridge.
                    back=sign*(790 if outer else 110);normal=App.Vector(0,sign if outer else -sign,0)
                    centre=App.Vector(x,back,level)
                    pos=App.Vector(x-24,min(back,back+normal.y*6),level-25)
                    plate_shape=Part.makeBox(48,6,50,pos)
                    seats=[]
                    for xx in (x-18,x+18):
                        for zz in (level-18,level+18):
                            basepoint=App.Vector(xx,back,zz)+normal*6
                            plate_shape=plate_shape.fuse(cylinder(5,1.5,basepoint-normal*.5,normal))
                            seats.append((basepoint+normal,normal))
                    mount=feature(d,g,'Stator_Anbindungsplatte',plate_shape,'R02-GUIDE-MOUNT','Aluminium TBD','Fraesreferenz',
                                  'Planes Montageinterface fuer Klemmschalen; Gewinde nominal dargestellt')
                    mount=cut(mount,[t for pt,n in seats for t in csktool(pt,n,4,17)])
                    # Two accessible-during-preassembly screws positively join
                    # the bridge halves to the rail attachment plate.
                    bridge_seats=[App.Vector(xx,back,level) for xx in (x-6,x+6)]
                    mount=cut(mount,[t for pt in bridge_seats for t in csktool(pt,-normal,4,7)])
                    for k,half in enumerate(halves):
                        halves[k]=cut(half,[hole(pt+normal*6,normal,2,10) for pt in bridge_seats])
                    for pt in bridge_seats:threadjoint(d,g,4,16,pt,-normal,'STATOR_BRIDGE',[mount]+halves,10)
                    # At these positions both straight guides have homogeneous faces.
                    for item in list(railparts):
                        if item not in PARTS[d.Name]:continue
                        ts=[]
                        for pt,n in seats:
                            t=hole(pt-n*16,n,2,17)
                            if item.Shape.BoundBox.intersect(t.BoundBox) and item.Shape.common(t).Volume>1e-6:ts.append(t)
                        if ts:
                            new=cut(item,ts);railparts.remove(item);railparts.append(new)
                    for pt,n in seats:threadjoint(d,g,4,16,pt,n,'STATOR_MOUNT',[mount],5)
    return g


def newframe(d):
    g=group(d,'01_CFK_Rahmen_R02');j=group(d,'02_Rahmenknoten_R02');hw=group(d,'03_Befestigung_Rahmen')
    for y in (-100,100):ns['rect_tube'](d,g,'Laengsrohr',(1200,40,40),(-600,y-20,295),0,'R02-CFK-L01')
    for x in (-200,0,200):
        ns['rect_tube'](d,g,'Quertraeger',(40,1690,40),(x-20,-845,245),1,'R02-CFK-Q01')
        for y in (-825,825):
            ns['round_tube'](d,g,'Aussenstuetze',15,12,414.7,(x,y,-170),'R02-CFK-S01')
            cyl(d,g,'Fusspuffer',22,30,(x,y,-200),id='R02-FUSS',mat='Elastomer TBD',note='Kein Landelastnachweis')
        for y in (-100,100):
            py=85 if y>0 else -85
            ns['round_tube'](d,g,'Innenstuetze',8,5,405,(x,py,-170),'R02-CFK-S02')
            holes=[(x+a,y+b,3.3) for a in (-32,32) for b in (-26,26)]
            plates=[]
            for z in (236,286,336):
                pp=plate(d,j,'Knotenplatte',(90,80,8),(x-45,y-40,z),holes,'R02-KNOTEN-90x80x8',
                         'Zusaetzliche untere Gegenplatte umfasst jetzt beide kreuzenden CFK-Rohre.')
                if z==336:pp=cut(pp,[hole((x,y,338),(0,0,1),4,7)],'Obere Knotenplatte M8-Nenngewinde')
                if z==236:
                    # Socket under lower saddle plate, no drilling through CFK post.
                    socket=cylinder(13,22,(x,py,214)).cut(cylinder(8.3,23,(x,py,213)))
                    socket=socket.fuse(Part.makeBox(8,20,6,App.Vector(x-19,py-10,222)))
                    socket=socket.fuse(Part.makeBox(8,20,6,App.Vector(x+11,py-10,222)))
                    socket=socket.cut(Part.makeBox(40,.6,20,App.Vector(x-20,py-.3,214)))
                    sk=feature(d,j,'Innenpfosten_Spannhuelse',socket,'R02-SOCKET16','Aluminium TBD','Dreh-/Fraesreferenz',
                               'Klemmdruck, Material und Fuge nicht lastvalidiert')
                    for xx in (x-15,x+15):
                        sk=cut(sk,[hole((xx,py-11,225),(0,1,0),1.7,22)])
                        # M3x25 across the split ears, not through carbon.
                        bb=bolt(d,hw,3,25,(xx,py-10.5,225),(0,-1,0),joint='SOCKET16')
                        washer(d,hw,3,(xx,py-10.5,225),(0,1,0));washer(d,hw,3,(xx,py+10,225),(0,1,0));nut(d,hw,3,(xx,py+10.5,225),(0,1,0))
                        JOINTS.append({'document':d.Name,'id':'SOCKET16','bolt':bb.Name,'targets':[sk.Name],
                                       'diameter_mm':3,'length_mm':25,'kind':'Geteilte Klemmhuelse; Vorspannung offen'})
                    feature(d,j,'Pfosten_Isolierhuelse',cylinder(8.3,21,(x,py,214)).cut(cylinder(8,23,(x,py,213))),
                            'R02-ISO-S16','GFK/Isolierlage TBD','Referenz','Keine elektrische/galvanische Freigabe')
                    cyl(d,j,'Pfosten_Endisolation',8,1,(x,py,235),id='R02-ISO-END16',mat='GFK TBD')
                    union=d.addObject('Part::MultiFuse','Sattelplatte_mit_Spannsocket');union.Shapes=[pp,sk]
                    for key in FIELDS:prop(union,key,getattr(pp,key))
                    prop(union,'BauteilID','R02-SATTEL-INTEGRAL')
                    prop(union,'Bemerkung','Integral bearbeitete Sattel-/Socket-Geometrie; keine lose Huelse unter Platte')
                    j.addObject(union)
                    for old in [pp,sk]:
                        PARTS[d.Name].remove(old);old.Visibility=False
                        for key in FIELDS:
                            if key in old.PropertiesList:old.removeProperty(key)
                    PARTS[d.Name].append(union)
                    for entry in JOINTS:
                        entry['targets']=[union.Name if name in [pp.Name,sk.Name] else name for name in entry.get('targets',[])]
                    pp=union;d.recompute();assert pp.Shape.isValid()
                plates.append(pp)
            isolators=[]
            for z in (244,285,294,335):
                iso=plate(d,j,'Isolierplatte',(90,80,1),(x-45,y-40,z),holes,'R02-ISO-KNOTEN')
                iso.Material_Annahme='GFK/FR4 TBD';isolators.append(iso)
            for a in (-32,32):
                for b in (-26,26):clamp_stack(d,hw,6,120,(x+a,y+b,344),108,f'KNOTEN_{x}_{y}_{a}_{b}',plates+isolators)
            stand=cylinder(12,9,(x,y,344)).fuse(cylinder(4,6,(x,y,338)))
            stand=stand.cut(hole((x,y,345),(0,0,1),3,9))
            o=feature(d,j,'Deck_Distanz_M8_M6',stand,'R02-DECK-STAND','Metall/Isolation TBD','Drehteilreferenz',
                      'Aussen M8x1.25, oben M6x1.0; Gewinde vereinfacht. Keine Einschraub-/Traglastfreigabe.')
            # Deck hardpoint in a relieved sandwich core, not a screw into foam.
            sleeve=cylinder(10,8,(x,y,353)).fuse(cylinder(12,1,(x,y,360)))
            sleeve=sleeve.cut(hole((x,y,352),(0,0,1),3.3,10))
            sleeve=sleeve.cut(Part.makeCone(3,6,3,App.Vector(x,y,358)))
            hp=feature(d,j,'Deck_Hardpoint',sleeve,'R02-DECK-HP','Metall + Verguss TBD','Dreh-/Vergussreferenz','Kernverguss und Klebflaeche offen')
            threadjoint(d,hw,6,16,(x,y,361),(0,0,1),f'DECK_{x}_{y}',[hp,o],8)
    deck=box(d,g,'Deck_Sandwich',(1200,300,8),(-600,-150,353),'R02-DECK','CFK Sandwich TBD','Panel mit lokalen Hardpoints',
             'Deck um 15 mm angehoben; Laminat/Kern/Lastnachweis offen')
    tools=[]
    for x in (-200,0,200):
        for y in (-100,100):
            tools += [hole((x,y,352),(0,0,1),10.25,10),hole((x,y,360),(0,0,1),12.25,2)]
            for a in (-32,32):
                for b in (-26,26):tools.append(hole((x+a,y+b,352),(0,0,1),7,10))
    deck=cut(deck,tools,'Deck mit Hardpoint- und Werkzeugoeffnungen')
    return deck,g


def footpads(d,deck):
    g=group(d,'04_Fussauflagen');hw=group(d,'05_Befestigung_Fuss')
    decktools=[]
    for cx,cy in [(160,-70),(-160,70)]:
        positions=[(cx+a,cy+b) for a in (-100,100) for b in (-45,45)]
        pad=plate(d,g,'Fussadapter',(280,130,5),(cx-140,cy-65,361),[(x,y,3.3) for x,y in positions],'R02-FOOT-ADAPTER')
        pad=cut(pad,[s for x,y in positions for s in csktool((x,y,366),(0,0,1),6,6)])
        box(d,g,'Abnehmbare_Antirutschmatte',(260,120,7),(cx-130,cy-60,366),'R02-FOOT-MAT','Elastomer TBD','Zuschnitt',
            'Zur Schrauben-/Werkzeugzugaenglichkeit abnehmen; kein gepruefter Fussrueckhalt')
        for x,y in positions:
            insert=cylinder(8.75,16,(x,y,345)).fuse(cylinder(11,1,(x,y,360)))
            insert=insert.cut(hole((x,y,346),(0,0,1),3,17))
            ins=feature(d,g,'Vergussinsert_M6',insert,'R02-FOOT-INSERT','Metall/Harz TBD','Drehteil und lokaler Verguss',
                        'Innen M6x1, Nennhuelle; Kleb- und Auszugslasten nicht validiert')
            resin=cylinder(9,8,(x,y,353)).cut(cylinder(8.75,10,(x,y,352)))
            feature(d,g,'Vergussfuge',resin,'R02-POTTING','Vergusswerkstoff TBD','Prozess offen','0.25 mm Referenz-Ringspalt')
            decktools += [hole((x,y,352),(0,0,1),9,10),hole((x,y,360),(0,0,1),11,2)]
            threadjoint(d,hw,6,20,(x,y,366),(0,0,1),f'FUSS_{x}_{y}',[pad,ins],12)
    return cut(deck,decktools,'Deck mit lokalen Fuss-Hardpoints')


def collar(d,g,x,y,z,ro,ri,id):
    # Shared split-clamp shape used by tray; leaves post unperforated.
    base=cylinder(ro,16,(x,y,z)).cut(cylinder(ri,18,(x,y,z-1)))
    for xx in (x-15,x+15):base=base.fuse(Part.makeBox(8,20,6,App.Vector(xx-4,y-10,z+9)))
    base=base.cut(Part.makeBox(50,.6,18,App.Vector(x-25,y-.3,z-1)))
    halves=[]
    for sign in (-1,1):
        clip=Part.makeBox(60,30,20,App.Vector(x-30,y+.3 if sign==1 else y-30.3,z-1))
        shape=base.common(clip)
        o=feature(d,g,'Geteilte_Klemmschelle',shape,id,'Aluminium TBD','Dreh-/Fraesreferenz','Keine CFK-Durchgangsbohrung; Vorspannung offen')
        o=cut(o,[hole((xx,y-11,z+12),(0,1,0),1.7,22) for xx in (x-15,x+15)])
        halves.append(o)
    for xx in (x-15,x+15):
        bb=bolt(d,g,3,25,(xx,y-10.5,z+12),(0,-1,0),joint=id)
        washer(d,g,3,(xx,y-10.5,z+12),(0,1,0));washer(d,g,3,(xx,y+10,z+12),(0,1,0));nut(d,g,3,(xx,y+10.5,z+12),(0,1,0))
        JOINTS.append({'document':d.Name,'id':id,'bolt':bb.Name,'targets':[o.Name for o in halves],
                       'diameter_mm':3,'length_mm':25,'kind':'Schelle mit zwei Halbschalen'})
    return halves


def battery(d):
    g=group(d,'06_Batterie_R02');hw=group(d,'07_Befestigung_Batterie')
    guard=box(d,g,'Schutzlage_Batterie',(1100,200,4),(-550,-100,155),'R02-BAT-GUARD','GFK/FR4 TBD','Zuschnitt')
    tray=plate(d,g,'Akkuwanne',(1100,200,3),(-550,-100,159),[],'R02-BAT-TRAY')
    guard=cut(guard,[hole((x,y,154),(0,0,1),13.5,6) for x in (-200,0,200) for y in (-85,85)])
    tray=cut(tray,[hole((x,y,158),(0,0,1),10,5) for x in (-200,0,200) for y in (-85,85)])
    for x in (-200,0,200):
        for y in (-85,85):
            collar(d,g,x,y,143,13,8.3,'R02-TRAY-CLAMP')
            feature(d,g,'Schellen_Isolierung',cylinder(8.3,16,(x,y,143)).cut(cylinder(8,18,(x,y,142))),
                    'R02-TRAY-ISO','GFK TBD','Referenz','Keine elektrische oder Klemmlastfreigabe')
    trayholes=[]
    for cx in (-240,240):
        # External enclosure remains 400x140x60, with real walls and lid.
        base=box(d,g,'Akkukasten_Roh',(400,140,58),(cx-200,-70,165),'R02-BAT-CASE','Aluminium TBD','Eigengehaeuse, keine Zell-/Brandfreigabe')
        base=cut(base,[Part.makeBox(397,137,58,App.Vector(cx-198.5,-68.5,166.5))])
        bosses=[];lidholes=[]
        for x in (cx-195,cx+195):
            for y in (-65,65):bosses.append(cylinder(5,8,(x,y,215)));lidholes.append((x,y))
        # Bosses join the side walls; no floating screw pillars.
        fused=base.Shape.multiFuse(bosses).removeSplitter()
        old=base;remove(old)
        base=feature(d,g,'Akkukasten_mit_Schraubdomen',fused,'R02-BAT-CASE','Aluminium TBD','Fraes-/Fuegereferenz',
                     'Elektrische Isolation, Thermik und Gasfuehrung offen; keine ausgewaehlten Zellen')
        base=cut(base,[hole((x,y,216),(0,0,1),1.5,8) for x,y in lidholes])
        lid=plate(d,g,'Akkudeckel',(400,140,2),(cx-200,-70,223),[(x,y,1.7) for x,y in lidholes],'R02-BAT-LID')
        lid=cut(lid,[s for x,y in lidholes for s in csktool((x,y,225),(0,0,1),3,3)])
        for x,y in lidholes:threadjoint(d,hw,3,8,(x,y,225),(0,0,1),f'BAT_LID_{x}_{y}',[base,lid],6)
        gasket=Part.makeBox(399,139,.5,App.Vector(cx-199.5,-69.5,222.5)).cut(Part.makeBox(395,135,1.5,App.Vector(cx-197.5,-67.5,222)))
        feature(d,g,'Deckeldichtung_Referenz',gasket,'R02-BAT-SEAL','Dichtung TBD','Konturzuschnitt','Geometrische Referenz; keine IP-/Brandschutzfreigabe')
        for bx in (cx-140,cx+140):
            bridge=plate(d,g,'Akku_Haltebruecke',(24,200,5),(bx-12,-100,225.5),[(bx,-84,2.75),(bx,84,2.75)],'R02-BAT-BRIDGE',
                         'Ersetzt schmalen bisherigen Buegel; Last und Sicherung noch offen')
            box(d,g,'Druckauflage',(24,140,.5),(bx-12,-70,225),'R02-BAT-PAD','Elastomer TBD','Zuschnitt')
            for y in (-84,84):
                post=feature(d,g,'Brueckendistanz',cylinder(6,63.5,(bx,y,162)).cut(cylinder(2.75,65.5,(bx,y,161))),
                             'R02-BAT-SPACER','Metall TBD','Drehteilreferenz')
                trayholes.append(hole((bx,y,158),(0,0,1),2.75,5))
                clamp_stack(d,hw,5,80,(bx,y,230.5),71.5,f'BAT_RETAIN_{bx}_{y}',[bridge,post,tray])
    tray=cut(tray,trayholes)
    # Route the previously defined static cable spaces; terminals remain unselected.
    for sign in (-1,1):
        for label,points,r,rad,id in [
          ('HV_Kabelraum',[(0,sign*65,210),(0,sign*240,210),(140,sign*240,210),(140,sign*835,210),(140,sign*835,-120)],6,60,'R02-HV-CABLE-REF'),
          ('LV_Datenraum',[(60,sign*150,200),(60,sign*835,200),(60,sign*835,-100)],3,30,'R02-LV-CABLE-REF')]:
            feature(d,g,label,ns['rounded_cable'](points,rad,r),id,'Kabeltyp TBD','Routingbauraum',
                    'Keine Aderquerschnitts-/Isolationsfreigabe; Anschluesse nicht elektrisch ausgelegt',True)
    OPEN.append('BMS, Zellhalter, Kontaktoren, Ladeanschluss und HV-Steckverbinder sind ohne Produktauswahl nicht intern detailliert.')
    return g


def rail_sector(a,rlo,rhi,z,h,kind,t0,t1):
    # Circle centres at +/-a; clockwise path, angular parameter in radians.
    if kind=='straight_top':return Part.makeBox(t1-t0,rhi-rlo,h,App.Vector(t0,rlo,z))
    if kind=='straight_bottom':return Part.makeBox(t1-t0,rhi-rlo,h,App.Vector(t0,-rhi,z))
    cx=a if kind=='right' else -a
    v=lambda r,t:App.Vector(cx+r*math.cos(t),r*math.sin(t),z)
    e=[Part.Arc(v(rhi,t0),v(rhi,(t0+t1)/2),v(rhi,t1)).toShape(),
       Part.makeLine(v(rhi,t1),v(rlo,t1)),
       Part.Arc(v(rlo,t1),v(rlo,(t0+t1)/2),v(rlo,t0)).toShape(),Part.makeLine(v(rlo,t0),v(rhi,t0))]
    return Part.Face(Part.Wire(e)).extrude(App.Vector(0,0,h))


def rails(d):
    g=group(d,'08_Segmentierte_C_Fuehrungen');hw=group(d,'09_Schienen_Stossverschraubungen')
    count=0
    for level in (-120,120):
        for side in (-1,1):
            r=450+side*320;segments=[];jointstates=[]
            # Two straight and twelve 30-degree curved segments per track.
            specs=[('straight_top',-249.75,249.75),('straight_bottom',-249.75,249.75)]
            for kind,start in [('right',-math.pi/2),('left',math.pi/2)]:
                for i in range(6):
                    t0=start+i*math.pi/6+.25/r;t1=start+(i+1)*math.pi/6-.25/r
                    specs.append((kind,t0,t1))
            for index,(kind,t0,t1) in enumerate(specs):
                low,high=(r-16,r-10) if side==-1 else (r+10,r+16)
                back=rail_sector(250,low,high,level-30,60,kind,t0,t1)
                fl=rail_sector(250,r-16 if side==-1 else r-12,r+12 if side==-1 else r+16,level-30,8,kind,t0,t1)
                fu=rail_sector(250,r-16 if side==-1 else r-12,r+12 if side==-1 else r+16,level+22,8,kind,t0,t1)
                solid=back.fuse(fl).fuse(fu).removeSplitter()
                # A genuine pocket replaces copper occupying solid metal.
                slot=rail_sector(250,r-16 if side==-1 else r+12,r-12 if side==-1 else r+16,level-10,20,kind,t0,t1)
                o=feature(d,g,'C_Segment',solid.cut(slot),'R02-RAIL-C','Aluminium TBD','Segmentprofil mit Wicklungstasche',
                          'Fugen 0.5 mm Referenz; Kurven-/Spalt-/Lastnachweis offen')
                prop(o,'Segment',f'{level}_{side}_{index}');prop(o,'Geometrie',f'{kind}:{t0}:{t1}')
                iron=feature(d,g,'Rueckschluss_Segment',rail_sector(250,r-20 if side==-1 else r+16,r-16 if side==-1 else r+20,level-22,44,kind,t0,t1),
                             'R02-RAIL-JOCH','Elektroblechpaket TBD','Segmentbauraum','Keine EM-Auslegung')
                segments.append((o,iron,kind,t0,t1));count+=1
            # Fourteen joints around the stadium, including straight/curve transitions.
            for kind,cx,start in [('right',250,-math.pi/2),('left',-250,math.pi/2)]:
                for j in range(7):
                    theta=start+j*math.pi/6
                    nr=App.Vector(math.cos(theta),math.sin(theta),0)
                    normal=nr*side;outer_back=r+side*20
                    # Intersect the exact offset stadium strip, including the
                    # straight/curve transition, with a local tangent window.
                    lo=min(outer_back,outer_back+side*6);hi=max(outer_back,outer_back+side*6)
                    full=ns['oval_face'](250,hi,level-25).cut(ns['oval_face'](250,lo,level-25)).extrude(App.Vector(0,0,50))
                    tangent=App.Vector(-math.sin(theta),math.cos(theta),0);inward=App.Vector(-math.cos(theta),-math.sin(theta),0)
                    matrix=App.Matrix()
                    for col,v in enumerate((tangent,inward,App.Vector(0,0,1)),1):
                        for row,value in enumerate(v,1):setattr(matrix,f'A{row}{col}',value)
                    clip=Part.makeBox(48,24,50,App.Vector(-24,-12,-25))
                    centre=App.Vector(cx+(outer_back+side*3)*nr.x,(outer_back+side*3)*nr.y,level)
                    clip.Placement=App.Placement(centre,App.Rotation(matrix))
                    shape=full.common(clip)
                    sb=.5+(math.pi/2-theta)*(outer_back/1000) if kind=='right' else 1+math.pi*(outer_back/1000)+(1.5*math.pi-theta)*(outer_back/1000)
                    seats=[];tools=[]
                    for delta in (-.018,.018):
                        px,py,tx,ty,_=state(sb+delta,.5,outer_back/1000)
                        rad=App.Vector(-ty,tx,0);n=rad*side
                        for dz in (-18,18):
                            backpoint=App.Vector(px*1000,py*1000,level+dz)+n*6
                            boss=cylinder(5,1.5,backpoint-n*.5,n)
                            shape=shape.fuse(boss)
                            seat=backpoint+n
                            seats.append((seat,n));tools+=csktool(seat,n,4,17)
                    splice=feature(d,g,'Schienen_Stosslasche',shape.removeSplitter(),'R02-RAIL-SPLICE','Aluminium TBD',
                                   'Gekruemmte Lasche mit Plansitzen','Uebergangs-Unterseiten und Temperaturfugen nicht freigegeben')
                    splice=cut(splice,tools)
                    # Drill matching profiles, only when actual metal intersects tool.
                    modified=[]
                    for k,(o,iron,sk,t0,t1) in enumerate(segments):
                        hits=[]
                        for seat,n in seats:
                            tool=hole(seat-n*16,n,2,17)
                            if o.Shape.BoundBox.intersect(tool.BoundBox) and o.Shape.common(tool).Volume>1e-6:hits.append(tool)
                        if hits:
                            o=cut(o,hits);iron=cut(iron,hits);segments[k]=(o,iron,sk,t0,t1);modified += [o,iron]
                    for seat,n in seats:threadjoint(d,hw,4,16,seat,n,'RAIL_SPLICE',[splice]+modified,5)
    return count


def save(d,name,step=True):
    d.recompute();parts=PARTS[d.Name]
    for o in parts:assert not o.Shape.isNull() and o.Shape.isValid(),o.Name
    filename=OUT/(name+'.FCStd');d.saveAs(str(filename))
    visible=[o for o in parts if o.BauteilID!='PILOT-REF']
    if step:Part.export(visible,str(OUT/(name+'.step')))
    bb=App.BoundBox()
    for o in visible:bb.add(o.Shape.BoundBox)
    REPORT[name]={'parts':len(parts),'bounds_mm':[bb.XLength,bb.YLength,bb.ZLength],
                  'manufacturing_release':False,'flight_validation':False,'source_revision':'R02'}
    print(name,REPORT[name],flush=True)


def mobile_hardware(d,mg,fast):
    """Close the generic carrier's mechanical interfaces without inventing electronics."""
    for body0 in [o for o in list(PARTS[d.Name]) if o.BauteilID=='SCHL-01']:
        body=body0;cy=320 if body.Shape.BoundBox.Center.y>0 else -320;side=1 if cy>0 else -1
        bc=cy-side*2;inward=App.Vector(0,-side,0);front=cy-side*12;back=cy+side*8
        # Fangrolle: real bore, local pocket and axial screw, not a solid roller on a solid block.
        for roller in [o for o in list(PARTS[d.Name]) if o.BauteilID=='FANG-REF' and abs(o.Shape.BoundBox.Center.y-cy)<3]:
            centre=roller.Shape.BoundBox.Center;x=centre.x;z=centre.z
            roller=cut(roller,[hole((x,cy-3.5,z),(0,1,0),1.6,7)])
            body=cut(body,[hole((x,cy-2.7,z),(0,1,0),6.3,5.4),
                           hole(App.Vector(x,front,z)+inward*.1,-inward,1.7,12),
                           hole((x,cy+side*2.7,z),(0,side,0),1.5,5.3)])
            seat=App.Vector(x,front,z)
            b=bolt(d,fast,3,20,seat+inward*.5,inward,joint='FANGROLLE_AXLE')
            washer(d,fast,3,seat,inward)
            JOINTS.append({'document':d.Name,'id':'FANGROLLE_AXLE','bolt':b.Name,'targets':[body.Name,roller.Name],
                           'diameter_mm':3,'length_mm':20,'nominal_engagement_mm':4.8,
                           'kind':'Achsschraube; konkrete Rollenlagerung und Fanglast offen'})
        # Smaller PM envelopes keep clear of the central 24.4-mm bore.
        for magnet in [o for o in list(PARTS[d.Name]) if o.BauteilID=='LM-MAG-REF' and abs(o.Shape.BoundBox.Center.y-cy)<12]:remove(magnet)
        pockets=[]
        for x in (-15,15):
            y0=min(back,back-side*4)
            box(d,mg,'PM_Nennkoerper',(4,4,12),(x-2,y0,-6),'R02-PM-REF','Magnetguete TBD','Bauraum',
                'Polmittenabstand30; schmaler fuer Bohrungsfreiheit. Kein Kraft-/Flussnachweis.',True)
            pockets.append(Part.makeBox(4.2,4.2,12.2,App.Vector(x-2.1,y0-.1,-6.1)))
        body=cut(body,pockets)
        cap=box(d,mg,'PM_Halteplatte',(64,1,16),(-32,min(back,back+side),-8),'R02-PM-KEEP','GFK/Isolierstoff TBD','Konturteil',
                'Positive Deckelgeometrie, Haltekraft und Material offen')
        for x in (-28,28):
            pt=App.Vector(x,back+side,0);n=App.Vector(0,side,0)
            cap=cut(cap,csktool(pt,n,2,2))
            body=cut(body,[hole(pt-n*6,n,1,7)])
            threadjoint(d,fast,2,6,pt,n,'PM_KEEPER',[cap,body],5)
        # Remove unsupported floating electronics and use a bolted bridge.
        for obj in [o for o in list(PARTS[d.Name]) if o.BauteilID=='CTRL-MOB-REF' and abs(o.Shape.BoundBox.Center.y-cy)<15]:remove(obj)
        casey=bc-side*38;rooty=bc-side*5;brackets=[]
        for x,columnx in [(-15,-18),(15,18)]:
            root=Part.makeBox(12,14,6,App.Vector(x-6,rooty-7,14))
            root=root.fuse(Part.makeBox(12,abs(rooty-casey)+12,2,App.Vector(x-6,min(rooty,casey)-6,18)))
            root=root.fuse(cylinder(3,11,(columnx,casey,20)))
            br=feature(d,mg,'Elektronik_Kraghalter',root.removeSplitter(),'R02-CTRL-BRACKET','Metall TBD','Fraesreferenz',
                       'Fuehrt unter dem festen C-Flansch nach innen; keine Steifigkeitsfreigabe')
            br=cut(br,csktool((x,rooty,20),(0,0,1),3,7)+[hole((columnx,casey,25),(0,0,1),1,7)])
            body=cut(body,[hole((x,rooty,8),(0,0,1),1.5,7)])
            threadjoint(d,fast,3,12,(x,rooty,20),(0,0,1),'CTRL_BRACKET_ROOT',[br,body],6)
            brackets.append(br)
        shape=Part.makeBox(45,22,6.5,App.Vector(-22.5,casey-11,31)).cut(Part.makeBox(42,19,6,App.Vector(-21,casey-9.5,33)))
        for x in (-19,19):
            for y in (casey-7.5,casey+7.5):shape=shape.fuse(cylinder(2.5,4.5,(x,y,33)))
        base=feature(d,mg,'Elektronik_Gehaeuse',shape.removeSplitter(),'R02-CTRL-CASE','Gehaeusewerkstoff TBD','Eigengehaeuse',
                     'Keine konkrete Elektronik oder Dichtheitsklasse ausgewaehlt')
        base=cut(base,[hole((x,y,33),(0,0,1),1,5) for x in (-19,19) for y in (casey-7.5,casey+7.5)])
        for x,br in zip((-18,18),brackets):
            base=cut(base,csktool((x,casey,33),(0,0,1),2,3))
            threadjoint(d,fast,2,8,(x,casey,33),(0,0,1),'CTRL_CASE_BASE',[base,br],6)
        lid=box(d,mg,'Elektronik_Deckel',(45,22,1.5),(-22.5,casey-11,37.5),'R02-CTRL-LID','Gehaeusewerkstoff TBD','Deckel')
        lid=cut(lid,[s for x in (-19,19) for y in (casey-7.5,casey+7.5) for s in csktool((x,y,39),(0,0,1),2,2)])
        for x in (-19,19):
            for y in (casey-7.5,casey+7.5):threadjoint(d,fast,2,6,(x,y,39),(0,0,1),'CTRL_LID',[lid,base],4.5)
        board=Part.makeBox(38,15,1.6,App.Vector(-19,casey-7.5,33.5))
        for x in (-19,19):
            for y in (casey-7.5,casey+7.5):board=board.cut(cylinder(2.7,3,(x,y,33)))
        feature(d,mg,'PCB_Referenz_mit_Keepouts',board,'R02-PCB-REF','PCB unbestimmt','Referenz',
                'Mechanischer Raum mit Domfreistellungen, KEIN fertiges Schalt-/Layoutdesign',True)
        # Retained inductive pickup, supported on a bracket below the C lip.
        for obj in [o for o in list(PARTS[d.Name]) if o.BauteilID=='IPT-SEC-REF' and abs(o.Shape.BoundBox.Center.y-cy)<12]:remove(obj)
        pickup=box(d,mg,'Energieaufnahme_Referenz',(30,12,6),(35,bc-6,12),'R02-IPT-REF','Induktivsystem TBD','Bauraum',
                   'Keine Uebertragungsleistung und keine zugeordnete Primaerwicklung nachgewiesen',True)
        hs=Part.makeBox(3,20,8,App.Vector(35,bc-10,4)).fuse(Part.makeBox(33,22,2,App.Vector(35,bc-11,10)))
        for y in (bc-8.5,bc+8.5):hs=hs.fuse(cylinder(2.5,3,(50,y,7)))
        holder=feature(d,mg,'Energieaufnahme_Halter',hs.removeSplitter(),'R02-IPT-HOLDER','Isolierwerkstoff TBD','Fraesreferenz')
        holder=cut(holder,[hole((50,y,7),(0,0,1),1,6) for y in (bc-8.5,bc+8.5)])
        for y in (bc-6,bc+6):
            holder=cut(holder,csktool((38,y,8),(1,0,0),2,4))
            body=cut(body,[hole((30,y,8),(1,0,0),1,6)])
            threadjoint(d,fast,2,8,(38,y,8),(1,0,0),'IPT_HOLDER',[holder,body],5)
        strap=Part.makeBox(4,21,1,App.Vector(48,bc-10.5,18))
        for y0 in (bc-10.5,bc+6.5):strap=strap.fuse(Part.makeBox(4,4,6,App.Vector(48,y0,12)))
        strap=feature(d,mg,'Energieaufnahme_Buegel',strap.removeSplitter(),'R02-IPT-STRAP','Isolierwerkstoff TBD','Konturteil')
        for y in (bc-8.5,bc+8.5):
            strap=cut(strap,csktool((50,y,19),(0,0,1),2,8))
            threadjoint(d,fast,2,12,(50,y,19),(0,0,1),'IPT_STRAP',[strap,holder],5)
    OPEN.extend(['Pitchmotor-/Encoder-Innenaufbau, Rotor-Wellen-Kraftschluss und produktspezifische Befestigungen ohne Herstellerauswahl offen.',
                 'PCB, Stecker und Leistungsuebertragung bleiben Funktionsreferenzen; keine erfundene Elektronik.',
                 'Fangrollen sind geometrisch gebohrt und verschraubt; konkrete Lager-/Achsschraubenpaarung und Fanglastfreigabe offen.'])


def main():
    d=doc('Horizontal_Z_R02_Montage')
    deck,fg=newframe(d);footpads(d,deck);battery(d);nsegments=rails(d);outer_frame_connectors(d);guide_supports(d)
    # Existing wing mechanism remains explicit in this revision; no invented motor internals.
    md=doc('Schlitten_R02_Detail');mg=group(md,'Mobile_Referenzbaugruppe')
    moving=ns['mobile'](md,mg,True)
    # Attach real screws to pole shims, not loose poles floating above the body.
    fast=group(md,'Befestigungen_Mobil')
    for body in [o for o in moving if o.BauteilID=='SCHL-01']:
        cy=320 if body.Shape.BoundBox.YMin>0 else -320;side=1 if cy>0 else -1
        for zz in (-18,18):
            basez=14 if zz>0 else -16
            shim=box(md,mg,'Pol_Distanzlage',(24,12,2),(-12,cy-6,basez),'R02-POLE-SHIM','Isolierender Traeger TBD','Referenz')
            cut(shim,[hole((x,cy,basez-1),(0,0,1),1.2,4) for x in (-10,10)])
        for pole in [o for o in list(PARTS[md.Name]) if o.BauteilID=='MAG-AKT-REF' and abs(o.Shape.BoundBox.Center.y-cy)<2]:
            sign=1 if pole.Shape.BoundBox.Center.z>0 else -1
            pole=cut(pole,[s for x in (-10,10) for s in csktool((x,cy,sign*20),(0,0,sign),2,5)])
            for x in (-10,10):
                # Matching nominal threaded body bores are added below.
                body=cut(body,[hole((x,cy,sign*10),(0,0,sign),1,5)])
                threadjoint(md,fast,2,10,(x,cy,sign*20),(0,0,sign),'POLE_MOUNT',[pole,body],4)
    mobile_hardware(md,mg,fast)
    md.recompute();moving=list(PARTS[md.Name])
    save(md,'02_Schlitten_R02_Detail')
    ag=group(d,'10_Mobile_Fluegelbaugruppen')
    length=perimeter(.5,.45)
    for layer,z in enumerate((-120,120)):
        direction=1 if layer==0 else -1
        for i in range(8):
            x,y,tx,ty,_=state(i*length/8,.5,.45)
            mapping={}
            for src in moving:
                new=ns['oriented_copy'](d,ag,src,(x*1000,y*1000,z),(direction*tx,direction*ty,0),(-ty,tx,0),f'W{layer}_{i}_{src.Name}')
                mapping[src.Name]=new.Name
                for k in ['Gewinde','Nennlaenge_mm','Kopfform','Gewindedarstellung']:
                    if k in src.PropertiesList:prop(new,k,getattr(src,k))
            for connection in [v for v in list(JOINTS) if v['document']==md.Name]:
                rec=copy.deepcopy(connection);rec['document']=d.Name;rec['id']=f'W{layer}_{i}/'+rec['id']
                rec['bolt']=mapping[rec['bolt']];rec['targets']=[mapping[t] for t in rec.get('targets',[]) if t in mapping]
                JOINTS.append(rec)
    # Previous pilot reference is raised with the standing surface; not a body model.
    pg=ns['pilot'](d,'Stehen')
    for obj in pg.Group:obj.Placement.Base.z+=15
    save(d,'00_Horizontal_Z_R02_Montage')
    OPEN.extend(['Mobile Elektronikhalter, Fangrollenachsen und PM-Rueckhaltung geometrisch verschraubt; Eigenschaften der Funktionskomponenten bleiben offen.',
                 'Aussenpfosten-T-Knoten und Statorhalter geometrisch detailliert; Lasten, Werkstoffe und Toleranzen offen.',
                 'Keine konkrete Magnet-, Pitchmotor-, Lager-, Akku- oder Elektronik-Auswahl; deren interne Schrauben sind nicht bekannt.',
                 'Schienen-Stosslaschen sind geometrisch konturangepasst; Temperaturfugen, Lasten und Toleranzen bleiben offen.',
                 'Innengewinde als Nennhuellen, keine Kernloch-/Gewindefertigungszeichnung.'])
    rows=[]
    for dn in (d.Name,md.Name):
        for o in PARTS[dn]:
            rows.append({'Datei':dn,'Instanz':o.Name,'ID':o.BauteilID,'Material':o.Material_Annahme,'Status':o.Freigabe,
                         'Gewinde':getattr(o,'Gewinde',''),'Nennlaenge_mm':getattr(o,'Nennlaenge_mm',''),
                         'Bemerkung':o.Bemerkung})
    with (OUT/'Stueckliste.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (OUT/'Verbindungen.json').write_text(json.dumps(JOINTS,ensure_ascii=False,indent=2))
    (OUT/'Offene_Schnittstellen.json').write_text(json.dumps(list(dict.fromkeys(OPEN)),ensure_ascii=False,indent=2))
    REPORT['rail_C_segments']=nsegments
    (OUT/'Pruefbericht.json').write_text(json.dumps(REPORT,indent=2))
    for doc_ in [d,md]:App.closeDocument(doc_.Name)
    for name in ['00_Horizontal_Z_R02_Montage','02_Schlitten_R02_Detail']:
        opened=App.openDocument(str(OUT/(name+'.FCStd')));opened.recompute()
        assert all(o.Shape.isValid() for o in opened.Objects if hasattr(o,'BauteilID'))
        App.closeDocument(opened.Name)
    print('R02 gespeichert/geoeffnet; C-Segmente',nsegments,'lokal registrierte Verbindungen',len(JOINTS),flush=True)

if __name__=='__main__':main()
