#!/usr/bin/python3
"""Native, manufacturing-oriented PRELIMINARY assemblies. Millimetres."""
import json,math,csv,sys,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.extend(['/usr/lib/freecad/lib',str(ROOT/'cad')])
import FreeCAD as App
import Part
from umlauf_kinematik import state,perimeter,naca_thickness
P=json.loads((HERE/'parameter.json').read_text())
BOM=[];REPORT={};DOC_PARTS={}


def doc(name):
    d=App.newDocument(name);DOC_PARTS[d.Name]=[]
    info=d.addObject('App::FeaturePython','Konstruktionsstatus')
    for k,v in {'Status':P['status'],'Hinweis':P['note'],'Hauptvariante':'Stehen',
                'Parameterquelle':'parameter.json; Tabelle ist Dokumentation, Regeneration per Skript',
                'KeinNachweis':'CFD nicht auf diese Detailgeometrie uebertragen; keine Fertigungs- oder Personenflugfreigabe'}.items():
        info.addProperty('App::PropertyString',k);setattr(info,k,v)
    s=d.addObject('Spreadsheet::Sheet','Parameter')
    for i,(k,v) in enumerate(P.items(),1):s.set(f'A{i}',k);s.set(f'B{i}',str(v))
    return d


def group(d,name):return d.addObject('App::DocumentObjectGroup',name)


def mark(o,g,id,material,process,note='',reference=False):
    if g:g.addObject(o)
    for k,v in {'BauteilID':id,'Material_Annahme':material,'Prozess_Referenz':process,
                'Bemerkung':note,'Freigabe':'VOR_ENTWURF','Referenzkoerper':'JA' if reference else 'NEIN'}.items():
        o.addProperty('App::PropertyString',k);setattr(o,k,v)
    DOC_PARTS[o.Document.Name].append(o)
    return o


def box(d,g,name,dim,pos,id='REF',mat='TBD',process='Bauraum',note='',ref=False):
    o=d.addObject('Part::Box',name);o.Length,o.Width,o.Height=dim;o.Placement.Base=App.Vector(*pos)
    return mark(o,g,id,mat,process,note,ref)


def cyl(d,g,name,r,h,pos,axis=(0,0,1),id='REF',mat='TBD',note='',ref=False):
    o=d.addObject('Part::Cylinder',name);o.Radius=r;o.Height=h
    o.Placement=App.Placement(App.Vector(*pos),App.Rotation(App.Vector(0,0,1),App.Vector(*axis)))
    return mark(o,g,id,mat,'Drehteil / Bauraum',note,ref)


def feature(d,g,name,shape,id,mat,process,note='',ref=False):
    o=d.addObject('Part::Feature',name);o.Shape=shape
    return mark(o,g,id,mat,process,note,ref)


def bored_block(d,g,name,dim,pos,radius,axis_start,axis_length,id):
    a=d.addObject('Part::Box',name+'_Roh');a.Length,a.Width,a.Height=dim;a.Placement.Base=App.Vector(*pos)
    b=d.addObject('Part::Cylinder',name+'_Bore');b.Radius=radius;b.Height=axis_length
    b.Placement=App.Placement(App.Vector(*axis_start),App.Rotation(App.Vector(0,0,1),App.Vector(0,1,0)))
    o=d.addObject('Part::Cut',name);o.Base=a;o.Tool=b;a.Visibility=False;b.Visibility=False
    return mark(o,g,id,'Aluminium / Zustand TBD','Fraesen, Querbohren',
                'Lagersitz und integrierter Motorbauraum ohne Passungs-, Last- oder Waermenachweis')


def ring_axis(d,g,name,ro,ri,length,start,axis,id,mat,note='',ref=False):
    a=d.addObject('Part::Cylinder',name+'_Aussen');a.Radius=ro;a.Height=length
    a.Placement=App.Placement(App.Vector(*start),App.Rotation(App.Vector(0,0,1),App.Vector(*axis)))
    b=d.addObject('Part::Cylinder',name+'_Innen');b.Radius=ri;b.Height=length+2
    unit=App.Vector(*axis);unit.normalize()
    b.Placement=App.Placement(App.Vector(*start)-unit,App.Rotation(App.Vector(0,0,1),unit))
    o=d.addObject('Part::Cut',name);o.Base=a;o.Tool=b;a.Visibility=False;b.Visibility=False
    return mark(o,g,id,mat,'Dreh-/Katalogbauraum',note,ref)


def rect_tube(d,g,name,dim,pos,axis,id):
    outer=d.addObject('Part::Box',name+'_Aussen');outer.Length,outer.Width,outer.Height=dim;outer.Placement.Base=App.Vector(*pos)
    inner=d.addObject('Part::Box',name+'_Innen');s=list(dim);q=list(pos)
    for k in range(3):
        s[k]=dim[k]+2 if k==axis else dim[k]-6
        q[k]=pos[k]-1 if k==axis else pos[k]+3
    inner.Length,inner.Width,inner.Height=s;inner.Placement.Base=App.Vector(*q)
    o=d.addObject('Part::Cut',name);o.Base=outer;o.Tool=inner
    outer.Visibility=False;inner.Visibility=False
    return mark(o,g,id,'CFK Rohr / Laminat TBD','Zuschnitt; Enden/Lastanschluesse gesondert auslegen',
                'Wand 3 mm nur Geometrieannahme. Keine Faserfolge, Festigkeit oder Klebfuge nachgewiesen.')


def round_tube(d,g,name,ro,ri,h,pos,id,mat='CFK Rohr / Laminat TBD'):
    a=d.addObject('Part::Cylinder',name+'_Aussen');a.Radius=ro;a.Height=h;a.Placement.Base=App.Vector(*pos)
    b=d.addObject('Part::Cylinder',name+'_Innen');b.Radius=ri;b.Height=h+2;b.Placement.Base=App.Vector(pos[0],pos[1],pos[2]-1)
    o=d.addObject('Part::Cut',name);o.Base=a;o.Tool=b;a.Visibility=False;b.Visibility=False
    return mark(o,g,id,mat,'Zuschnitt; Klemm-/Knotenanschluss TBD','Keine Bohrung direkt in tragende CFK-Rohre vorgesehen')


def plate(d,g,name,dim,pos,holes,id,note=''):
    a=d.addObject('Part::Box',name+'_Rohteil');a.Length,a.Width,a.Height=dim;a.Placement.Base=App.Vector(*pos)
    current=a
    for n,(x,y,r) in enumerate(holes):
        tool=d.addObject('Part::Cylinder',name+f'_Bohrung{n}');tool.Radius=r;tool.Height=dim[2]+2
        tool.Placement.Base=App.Vector(x,y,pos[2]-1)
        cut=d.addObject('Part::Cut',name+f'_Schnitt{n}');cut.Base=current;cut.Tool=tool
        current.Visibility=False;tool.Visibility=False;current=cut
    return mark(current,g,id,'Aluminium / Legierung und Zustand TBD','Fraesen, Bohren, Entgraten',note)


def frame(d):
    g=group(d,'CFK_Rahmen');cl=group(d,'Klemmknoten_Isolation')
    for y in (-100,100):rect_tube(d,g,f'Laengsrohr_{y+100}',(1200,40,40),(-600,y-20,280),0,'CFK-L01')
    for x in (-200,0,200):
        rect_tube(d,g,f'Quertraeger_{x+200}',(40,1660,40),(x-20,-830,230),1,'CFK-Q01')
        for y in (-810,810):
            round_tube(d,g,f'Aussenstuetze_{x+200}_{y+810}',15,12,400,(x,y,-170),'CFK-S01')
            cyl(d,g,'Fuss_Puffer',22,30,(x,y,-200),id='FUSS-01',mat='Elastomer TBD',note='Kein Aufprall-/Landefahrwerksnachweis')
        for y in (-100,100):
            round_tube(d,g,'Innenstuetze',8,5,400,(x,y,-170),'CFK-S02')
            for z in (271,321):
                holes=[(x+a,y+b,3.3) for a in (-32,32) for b in (-26,26)]
                plate(d,cl,'Klemmplatte',(90,80,8),(x-45,y-40,z),holes,'KNOTEN-P01',
                      'Bohrbild 64 x 52, D6.6 als Referenz. Schraubenvorspannung/Klemmdruck nicht ausgelegt.')
            for iz in (270,279,320):
                iso=plate(d,cl,'Isolierlage_Knoten',(90,80,1),(x-45,y-40,iz),holes,'ISO-01',
                          'Galvanische Trennung konzeptionell; Feuchte, Durchschlag, Kriechen nicht validiert')
                iso.Material_Annahme='GFK/FR4 TBD'
            for a in (-32,32):
                for b in (-26,26):
                    cyl(d,cl,'Schraubenschaft_REF',3,62,(x+a,y+b,267),id='BOLT-REF',mat='Schraubenauswahl TBD',note='Gewinde/Kopf/Vorspannung nicht ausgelegt',ref=True)
                    cyl(d,cl,'Schraubenkopf_REF',5,4,(x+a,y+b,329),id='HEAD-REF',mat='Schraubenauswahl TBD',ref=True)
            cyl(d,cl,'Deck_Distanz',12,9,(x,y,329),id='DECK-SP01',mat='Isolierender Hartpunkt TBD',note='Druck-/Kernlast nicht nachgewiesen')
    deck=box(d,g,'Deckplatte',(1200,300,8),(-600,-150,338),'DECK-01','CFK Sandwich / Kern und Laminat TBD','Panelzuschnitt; Hardpoints TBD',
             'Keine Lasteinleitung in Kern ohne ausgelegte Inserts. Nicht als ungepruefte Stehplatte verwenden.')
    for x in (-200,0,200):
        for y in (-100,100):
            box(d,cl,'Knotenwinkel_Bauraum',(50,50,35),(x-25,y-25,225),'KNOTEN-REF','Metall + Isolierlagen TBD','Referenzhülle',
                'Ueberlagerung mit Rohren ist Anschlussbauraum, kein fertiger Formschluss',True)
    return g


def oval_face(a,r,z):
    v=lambda x,y:App.Vector(x,y,z)
    return Part.Face(Part.Wire([Part.makeLine(v(-a,r),v(a,r)),Part.Arc(v(a,r),v(a+r,0),v(a,-r)).toShape(),
                               Part.makeLine(v(a,-r),v(-a,-r)),Part.Arc(v(-a,-r),v(-a-r,0),v(-a,r)).toShape()]))


def band(d,g,name,radial_low,radial_high,z0,height,id,mat,note):
    shape=oval_face(250,radial_high,z0).cut(oval_face(250,radial_low,z0)).extrude(App.Vector(0,0,height))
    return feature(d,g,name,shape,id,mat,'Segmentierte Schiene erforderlich; hier Gesamt-Huelle',note)


def rails(d):
    g=group(d,'Fuehrungen_Stationaer')
    for level in (-120,120):
        for side in (-1,1):
            r=450+side*320
            low,high=(r-16,r-10) if side==-1 else (r+10,r+16)
            band(d,g,'C_Rueckwand',low,high,level-30,60,'FUEHR-C','Aluminium / Zustand TBD',
                 'C-Profil; Oeffnung zur Fluegelspannweite. Keine Magnet- oder Kontaktkraftauslegung.')
            for zz in (level-30,level+22):
                band(d,g,'C_Flansch',r-16 if side==-1 else r-12,r+12 if side==-1 else r+16,zz,8,'FUEHR-F','Aluminium / Zustand TBD',
                     'Freiraum/Fangfunktion nur geometrischer Entwurf; Segmente und Stossfugen offen')
            band(d,g,'Rueckschluss_Eisen',r-20 if side==-1 else r+16,r-16 if side==-1 else r+20,level-22,44,
                 'MAG-JOCH','Elektroblech / Paket TBD','Keine Saettigungs-, Wirbelstrom- oder Waermenachweise')
            band(d,g,'Stator_Wicklungsraum',r-16 if side==-1 else r+12,r-12 if side==-1 else r+16,level-15,30,
                 'LM-STATOR-REF','Wicklungsbauraum, KEIN Vollkupferteil','Polteilung, Windungen, Isolation und Strom noch offen')
            band(d,g,'Kontaktlose_Energie_Primaer',r-16 if side==-1 else r+12,r-12 if side==-1 else r+16,level+16,6,
                 'IPT-PRI-REF','Induktivsystem TBD','Frequenz, Leistung, EMV und Beruehrschutz nicht ausgelegt')
    # Static brackets at straight sections, back of channel (not through wing space).
    for x in (-200,0,200):
        for z in (-120,120):
            for sign in (-1,1):
                plate(d,g,'Aussen_Statorlasche',(36,34,6),(x-18,sign*798-17,z-3),
                      [(x-10,sign*798,3.3),(x+10,sign*798,3.3)],'FUEHR-L01',
                      'Backside-Anbindung; isolierter Anschluss an CFK-Stuetze konstruktiv abzustimmen')
                plate(d,g,'Innen_Statorlasche',(30,24,6),(x-15,sign*108-12,z-3),[],
                      'FUEHR-L02','Montagezone innen; Anbindung und Verbindung nicht festigkeitsvalidiert')
    return g


def foil_shape(span=600):
    xx=[(1-math.cos(math.pi*i/50))/2 for i in range(51)]
    def face(inner=False):
        points=[]
        for sign,seq in ((1,xx),(-1,xx[-2:0:-1])):
            for q in seq:
                chord_q=.04+.92*q if inner else q
                thick=naca_thickness(q)*(.70 if inner else 1)
                points.append(App.Vector((.5-chord_q)*120,0,sign*thick*120))
        points.append(points[0]);return Part.Face(Part.Wire(Part.makePolygon(points).Edges))
    return face().cut(face(True)).extrude(App.Vector(0,span,0)).translated(App.Vector(0,-span/2,0))


def mobile(d,g,detail=False):
    parts=[]
    shell=feature(d,g,'Fluegel_Huelle',foil_shape(),'FL-CFK-REF','CFK Laminat TBD','Formwerkzeug/Laminieren; Profilinnenkontur nur Referenz',
                  'Innenkontur skaliert, NICHT konstante Wandstaerke. Kein Laminat-, Flatter- oder Ermuedungsnachweis.')
    parts.append(shell)
    shaft=cyl(d,g,'Pitchwelle',4,640,(0,-320,0),(0,1,0),'PITCH-W01','Wellenwerkstoff TBD',
              'Achse bei 50 Prozent Sehne wie Referenzmodell; Torsion und Eigenfrequenz offen');parts.append(shaft)
    for side in (-1,1):
        cy=side*320
        body=bored_block(d,g,'Schlitten_Traeger',(70,20,28),(-35,cy-10-side*2,-14),12.2,(0,cy-15,0),30,'SCHL-01');parts.append(body)
        housing=ring_axis(d,g,'Pitchlager_Sitz',15,11.1,8,(0,side*300,0),(0,side,0),'LAGER-G01','Aluminium TBD','Sitz D22.2 nur Referenz, keine Passungsfreigabe');parts.append(housing)
        bearing=ring_axis(d,g,'Lager_Bauraum',11,4,7,(0,side*301,0),(0,side,0),'LAGER-REF','Katalogauswahl offen','Nur Geometrie 8/22/7; kein ausgewaehltes oder lastbewertetes Lager',True);parts.append(bearing)
        fork=bored_block(d,g,'Wurzelgabel',(24,6,12),(-12,side*298-3,-6),4.2,(0,side*298-4,0),8,'PITCH-G01');parts.append(fork)
        if detail:
            for j in range(2):
                magnet=box(d,g,f'Magnet_{side+1}_{j}',(8,4,12),(-19+j*30,cy+side*6-2,-6),
                           'LM-MAG-REF','Permanentmagnet / Guete TBD','Katalogbauraum',
                           f'Polsymbol {"N" if j%2==0 else "S"}; Polteilung und Fluss nicht ausgelegt',True);parts.append(magnet)
            for zz in (-18,18):
                pole=box(d,g,'Fuehrpol_Bauraum',(24,12,4),(-12,cy-6,zz-2),'MAG-AKT-REF','Aktives Magnetlager TBD','Referenzvolumen',
                         'Nomineller CAD-Abstand 2 mm zum Flansch; kein funktionsfaehiger Luftspaltnachweis',True);parts.append(pole)
                for xx in (-25,25):
                    roller=cyl(d,g,'Fangrolle',6,5,(xx,cy-2.5,zz-3 if zz>0 else zz+3),(0,1,0),
                               'FANG-REF','PEEK / Lager TBD','1 mm nominelle Restfreiheit; keine Fanglastfreigabe',True);parts.append(roller)
            pickup=box(d,g,'Induktiv_Sekundaer',(30,12,6),(35,cy-6,12),'IPT-SEC-REF','Sekundaerwicklung TBD','Bauraum',
                       'Versorgt Pitch/Encoder nur konzeptionell; Leistungsuebertragung nicht nachgewiesen',True);parts.append(pickup)
            pcb=box(d,g,'Schlitten_Elektronik',(45,22,8),(-22.5,cy-11,31),'CTRL-MOB-REF','Elektronik TBD','Bauraum',
                    'Positionssensor, Pitchregler und Puffer; keine fertige Elektronik',True);parts.append(pcb)
        if side==1:
            servo=ring_axis(d,g,'Pitch_Torquemotor_Huelle',12,4.2,12,(0,315,0),(0,1,0),'PITCH-MOT-REF','Direktantrieb TBD',
                            'Integrierter koaxialer Motorbauraum; kein Drehmoment-, Winkelraten- oder Waermenachweis',True);parts.append(servo)
            encoder=ring_axis(d,g,'Absolutencoder_Bauraum',8,4.2,4,(0,308,0),(0,1,0),'ENC-REF','Encoder TBD','Referenzhuelle',True);parts.append(encoder)
    return parts


def oriented_copy(d,g,source,centre,tangent,radial,name):
    # Local x = direction of travel, local y = radial or opposite;
    # choose right-handed basis and constant positive nose-up pitch.
    t=App.Vector(*tangent);r=App.Vector(*radial);alpha=math.radians(12) if source.BauteilID in ['FL-CFK-REF','PITCH-G01'] else 0
    x=t*math.cos(alpha)+App.Vector(0,0,math.sin(alpha))
    z=t*(-math.sin(alpha))+App.Vector(0,0,math.cos(alpha))
    y=z.cross(x)
    m=App.Matrix()
    for col,v in enumerate((x,y,z),1):
        for row,val in enumerate((v.x,v.y,v.z),1):setattr(m,f'A{row}{col}',val)
    transform=App.Placement(App.Vector(*centre),App.Rotation(m))
    obj=d.addObject('Part::Feature',name);obj.Shape=source.Shape.copy();obj.Placement=transform.multiply(source.Placement)
    return mark(obj,g,source.BauteilID,source.Material_Annahme,source.Prozess_Referenz,
                source.Bemerkung+' | Kopie aus Mechanismus-Datei; lokale Quellen editierbar.',source.Referenzkoerper=='JA')


def rounded_cable(points,radius,tube_radius):
    pts=[App.Vector(*p) for p in points];edges=[];last=pts[0]
    for k in range(1,len(pts)-1):
        a,b,c=pts[k-1:k+2];incoming=b-a;outgoing=c-b
        incoming.normalize();outgoing.normalize();theta=math.acos(max(-1,min(1,incoming.dot(outgoing))))
        distance=radius*math.tan(theta/2)
        assert distance<(b-a).Length and distance<(c-b).Length
        start=b-incoming*distance;end=b+outgoing*distance
        edges.append(Part.makeLine(last,start))
        bisector=(-incoming+outgoing);bisector.normalize()
        centre=b+bisector*(radius/math.cos(theta/2))
        va=start-centre;vb=end-centre;middle=va+vb;middle.normalize();middle=centre+middle*radius
        edges.append(Part.Arc(start,middle,end).toShape());last=end
    edges.append(Part.makeLine(last,pts[-1]));wire=Part.Wire(edges)
    direction=pts[1]-pts[0];direction.normalize()
    profile=Part.Wire([Part.makeCircle(tube_radius,pts[0],direction)])
    return wire.makePipeShell([profile],True,True)


def batteries(d):
    g=group(d,'Batterie_Kabel_Stationaer');modules=[];cables=[]
    box(d,g,'Trennschutz_Unterseite',(1100,160,4),(-550,-80,155),'BAT-GUARD','GFK/FR4/Brandkonzept TBD','Zuschnitt',
        'Nur Trenngeometrie. Keine Brand-, Splitter- oder Durchschlagpruefung.')
    tray=plate(d,g,'Schubkasten_Boden',(1100,160,3),(-550,-80,159),[], 'BAT-TRAY','Entnahme laengs x; Befestigung und Rueckhaltung offen')
    for x in (-240,240):
        mod=box(d,g,'Akku_Modulhuelle',(400,140,60),(x-200,-70,165),'BAT-MOD-REF','Akkusystem unbestimmt','Bauraum',
                'KEINE Tattu-Auswahl. Energie, Spannung, Strom, Masse und thermischer Aufbau offen.',True);modules.append(mod)
        for yy in (-76,73):box(d,g,'Gleit_Isolation',(430,3,60),(x-215,yy,163),'BAT-GLEIT','GFK/PEEK TBD','Zuschnitt','Keine Kriech-/Brandfreigabe')
        for xx in (x-190,x+190):
            plate(d,g,'Modul_Rueckhaltebuegel',(12,160,5),(xx-6,-80,225),[(xx,-75,3.3),(xx,75,3.3)],'BAT-BUEGEL',
                  'Positiver Rueckhalt nur Konzept; Belastung, Verriegelung und Sicherung offen')
    box(d,g,'Servicebox_HV',(60,120,70),(-30,-60,165),'HV-BOX-REF','Isolierendes Gehaeuse TBD','Bauraum',
        'BMS, Sicherung, Schuetze, Vorladung, Trennstelle nur Funktionsanforderungen; kein Schaltplan',True)
    for side in (-1,1):
        shape=rounded_cable([(0,side*65,210),(0,side*835,210),(0,side*835,-120)],60,6)
        cable=feature(d,g,'HV_Kabelraum',shape,'HV-CABLE-REF','Kabeltyp/Aderquerschnitt TBD','Routingbauraum',
                      'D12 und R60 nur CAD-Referenz; keine Strombelastbarkeit, Isolations- oder Mindestbiegeradiusfreigabe',True);cables.append(cable)
        shape=rounded_cable([(60,side*150,200),(60,side*835,200),(60,side*835,-100)],30,3)
        cables.append(feature(d,g,'LV_Datenraum',shape,'LV-CABLE-REF','Daten-/Versorgungstyp TBD','Routingbauraum',
                        'Getrennte Trasse; kein EMV- oder Sicherheitsabstandsnachweis',True))
        box(d,g,'Stator_Verteilbox',(50,28,45),(-25,side*835-14,-140),'STATOR-JB-REF','Elektronik/Isolation TBD','Bauraum',
            'Fester Anschluss an untere/obere Statorzonen noch elektrisch auszuarbeiten',True)
        for z in (-100,0,100):
            box(d,g,'Kabelschelle_Isoliert',(24,18,14),(-12,side*835-9,z-7),'KABEL-CLIP','Isolierwerkstoff TBD','Klemmhalter',
                'Schellen-Ueberlagerung mit Kabel ist beabsichtigter Halteraum; keine Klemmkraftfreigabe')
    d.recompute()
    for a in modules:
        for cable in cables:assert a.Shape.distToShape(cable.Shape)[0]>0,(a.Name,cable.Name)
    return g


def body_segment(d,g,name,a,b,r):
    va=App.Vector(*a);vb=App.Vector(*b);axis=vb-va
    return cyl(d,g,name,r,axis.Length,a,(axis.x,axis.y,axis.z),'PILOT-REF','Menschliche Referenzhuelle','Keine anthropometrische oder biomechanische Validierung',True)


def pilot(d,posture):
    g=group(d,'Pilot_Referenz_KEIN_Bauteil')
    if posture=='Stehen':
        floor=358
        hips=[(0,-100,1308),(0,100,1308)];knees=[(100,-90,858),(-100,90,858)];feet=[(160,-70,418),(-160,70,418)]
        shoulders=[(0,-180,1758),(0,180,1758)];head=(0,0,2008)
    elif posture=='Sitzen':
        hips=[(-80,-100,440),(-80,100,440)];knees=[(300,-100,395),(300,100,395)];feet=[(650,-100,350),(650,100,350)]
        shoulders=[(-270,-180,830),(-270,180,830)];head=(-330,0,1050)
    else:
        hips=[(50,-100,440),(50,100,440)];knees=[(440,-90,420),(440,90,420)];feet=[(820,-80,390),(820,80,390)]
        shoulders=[(-450,-180,440),(-450,180,440)];head=(-680,0,450)
    for i in range(2):
        body_segment(d,g,'Oberschenkel',hips[i],knees[i],60);body_segment(d,g,'Unterschenkel',knees[i],feet[i],45)
        body_segment(d,g,'Torso_Seite',hips[i],shoulders[i],90)
        hand=(shoulders[i][0]+180,shoulders[i][1]*1.2,shoulders[i][2]-220) if posture!='Liegen' else (-650,shoulders[i][1]*1.4,390)
        body_segment(d,g,'Arm_Referenz',shoulders[i],hand,35)
    s=d.addObject('Part::Sphere','Kopf_Referenz');s.Radius=100;s.Placement.Base=App.Vector(*head)
    mark(s,g,'PILOT-REF','Menschliche Referenzhuelle','Referenz','Keine Schutz-/Helmhuelle und kein CG-Modell',True)
    return g


def ergonomics(d,posture):
    g=group(d,'Ergonomie_'+posture)
    if posture=='Stehen':
        for x,y in [(160,-70),(-160,70)]:
            plate(d,g,'Fussauflage_Adapter',(280,130,5),(x-140,y-65,346),
                  [(x+a,y+b,3.3) for a in (-100,100) for b in (-45,45)],'ERG-ST-P01',
                  'Raster fuer verstellbare Klemmadapter. Deck-Hardpoints und Befestigung noch auszulegen.')
            box(d,g,'Antirutsch_Auflage',(260,120,7),(x-130,y-60,351),'ERG-ST-G01','Elastomer TBD','Zuschnitt',
                'Keine feste Fussbindung. Reibung, Naesse und kontrollierbares Loesen unbewertet.')
    elif posture=='Sitzen':
        box(d,g,'Langsitz_Adapter',(500,420,20),(-320,-210,346),'ERG-SI-P01','Sandwich / Laminat TBD','Formteil/Hardpoints TBD',
            'Niedriger Langsitz statt herkoemmlicher Stuhl. Kein Sitz- oder Rueckhaltesystemnachweis.')
        box(d,g,'Langsitz_Polster',(450,400,27),(-300,-200,366),'ERG-SI-G01','Polster TBD','Formteil')
        box(d,g,'Beckenanschlag',(40,400,49),(-340,-200,346),'ERG-SI-B01','Tragstruktur/Polster TBD','Beckenstuetze',
            'KEINE hohe Rueckenlehne. Becken-/Wirbelsaeulenbelastung und 15-min-Komfort offen.')
        for y in (-100,100):
            box(d,g,'Fussausleger',(200,40,20),(550,y-20,318),'ERG-SI-A01','CFK/Metall TBD','Auslegerreferenz','Kragarm nicht nachgewiesen')
            box(d,g,'Fussauflage',(140,130,10),(610,y-65,338),'ERG-SI-F01','Auflage TBD','Referenz')
    else:
        box(d,g,'Liege_Sandwich',(1800,500,12),(-900,-250,346),'ERG-LI-P01','CFK Sandwich TBD','Panel/Hardpoints TBD',
            'Neue grosse Abschattung oberhalb der Fluegel; vorherige CFD nicht uebertragbar.')
        box(d,g,'Liege_Polster',(1750,480,20),(-875,-240,358),'ERG-LI-G01','Polster TBD','Formteil','Bauchlage nur Konzept, Nacken-/Atem-/Druckstellen offen')
        for y in (-250,250):box(d,g,'Unterarmauflage',(220,100,40),(-760,y-50,358),'ERG-LI-A01','Polster/Traeger TBD','Referenz',
                                  'Sichtfeld, Ausstieg und Bedienung nicht erprobt')
    pg=pilot(d,posture)
    return g,pg


def save(d,filename,export=True):
    d.recompute();parts=DOC_PARTS[d.Name]
    assert all(not o.Shape.isNull() and o.Shape.isValid() for o in parts)
    vehicle=[o for o in parts if o.BauteilID!='PILOT-REF']
    bb=App.BoundBox()
    for o in vehicle:bb.add(o.Shape.BoundBox)
    dims=[bb.XLength,bb.YLength,bb.ZLength]
    for o in parts:
        BOM.append({'Datei':filename+'.FCStd','Instanz':o.Name,'ID':o.BauteilID,'Material_Annahme':o.Material_Annahme,
                    'Prozess':o.Prozess_Referenz,'Referenz':o.Referenzkoerper,'Volumen_mm3':round(o.Shape.Volume,3),
                    'Bemerkung':o.Bemerkung,'Freigabe':'VOR_ENTWURF'})
    d.saveAs(str(HERE/(filename+'.FCStd')))
    if export:Part.export(vehicle,str(HERE/(filename+'.step')))
    REPORT[filename]={'valid_result_shapes':len(parts),'vehicle_bounds_mm':dims,
                       'within_2100_1700_600':all(a<=b+1e-6 for a,b in zip(dims,[2100,1700,600])),
                       'pilot_excluded_from_vehicle_bounds':True,'manufacturing_release':False}
    print(filename,REPORT[filename],flush=True)
    return parts


frame_doc=doc('CFK_Rahmen');frame(frame_doc);save(frame_doc,'01_CFK_Rahmen')
mech_doc=doc('Fluegel_Mechanismus');mg=group(mech_doc,'Bewegte_Baugruppe');mobile_parts=mobile(mech_doc,mg,True)
# Straight stator coupon, local rails at y +/-320. No claim of endless-band closure.
sg=group(mech_doc,'Stator_Probeabschnitt')
for side in (-1,1):
    cy=side*320;back=cy+side*13
    box(mech_doc,sg,'C_Probe_Rueckwand',(240,6,60),(-120,back-3,-30),'FUEHR-C-PROBE','Aluminium TBD','Fraes-/Profilreferenz')
    for zz in (-30,22):box(mech_doc,sg,'C_Probe_Flansch',(240,28,8),(-120,cy-16 if side==-1 else cy-12,zz),'FUEHR-F-PROBE','Aluminium TBD','Profilreferenz')
    for j in range(12):box(mech_doc,sg,'ABC_Statorzelle',(16,4,30),(-118+j*20,cy+side*14-2,-15),
                       'LM-SPULE-REF','Wicklungsraum TBD','Referenz',f'Phasenkennzeichen {"ABC"[j%3]}; KEINE Wicklungsauslegung',True)
mech_doc.recompute();save(mech_doc,'02_Fuehrung_Antrieb_Detail')
bat_doc=doc('Batterie_Kabel');batteries(bat_doc);save(bat_doc,'03_Batterie_Kabel')

assembly=doc('PropBoard_Detail_Stehen');frame(assembly);rails(assembly);batteries(assembly)
ag=group(assembly,'Fluegel_Bauraum_16')
length=perimeter(.5,.45)
# Detailed mobile mechanism remains independently editable in file 02.
for level,z in enumerate((-120,120)):
    direction=1 if level==0 else -1
    for i in range(8):
        x,y,tx,ty,_=state(i*length/8,.5,.45)
        for source in mobile_parts:
            # Small electromagnetic components remain in detail file only.
            oriented_copy(assembly,ag,source,(x*1000,y*1000,z),(direction*tx,direction*ty,0),(-ty,tx,0),f'Fluegel_{level}_{i}_{source.Name}')
ergonomics(assembly,'Stehen');save(assembly,'00_PropBoard_Detail_Stehen')
for posture in ('Sitzen','Liegen'):
    d=doc('Ergonomie_'+posture);frame(d)
    rg=group(d,'Bahnreferenz_KEIN_NEUER_CFD_NACHWEIS')
    # Static rail shells only for visual context; no duplicate frame references.
    for source in DOC_PARTS[assembly.Name]:
        if source.BauteilID in ['FUEHR-C','FUEHR-F','FL-CFK-REF']:
            o=d.addObject('Part::Feature',source.Name);o.Shape=source.Shape.copy()
            mark(o,rg,source.BauteilID,source.Material_Annahme,source.Prozess_Referenz,'Kontextkopie aus Hauptbaugruppe')
    ergonomics(d,posture);save(d,'04_Ergonomie_'+posture)

with (HERE/'Stueckliste_Instanzen.csv').open('w',newline='',encoding='utf-8-sig') as f:
    writer=csv.DictWriter(f,fieldnames=list(BOM[0]));writer.writeheader();writer.writerows(BOM)
for d in list(App.listDocuments().values()):App.closeDocument(d.Name)
for path in sorted(HERE.glob('*.FCStd')):
    opened=App.openDocument(str(path));opened.recompute()
    assert all(o.Shape.isValid() for o in opened.Objects if hasattr(o,'Shape') and not o.Shape.isNull())
    REPORT[path.stem]['saved_reopened']=True;App.closeDocument(opened.Name)
(HERE/'Pruefbericht.json').write_text(json.dumps(REPORT,indent=2))
print(json.dumps(REPORT,indent=2),flush=True)
