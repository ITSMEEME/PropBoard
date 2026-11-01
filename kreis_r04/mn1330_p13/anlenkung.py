"""Pitch links, nonrotating swashplate drive and nominal standard fasteners."""
import math
import FreeCAD as A, Part
from mechanik import V,box,cyl,ring,holes,pcd,axial,annulus_x,rotate

def add(config,parts,scene,q,define,put,mate):
    p=config['parameters'];m=config['mechanics'];new_names=[]
    # Standard screw head dimensions; threaded portions use declared core envelopes.
    sizes={3:(5.5,3,2.5,2.4),4:(7,4,3,3.2),5:(8.5,5,4,4.1),6:(10,6,5,4.9),8:(13,8,6,6.7)}
    def screw(d,L,seat,direction,name,angle=0,sign=1,z=0,pitch=0):
        hd,hh,sw,core=sizes[d];id=f'STD-ISO4762-M{d}x{L:g}'
        if id not in parts:
            s=cyl(hd/2,hh).fuse(cyl(core/2,L,z=-L))
            pts=[V(sw/math.sqrt(3)*math.cos(i*math.pi/3),sw/math.sqrt(3)*math.sin(i*math.pi/3),hh/2) for i in range(6)]
            s=s.cut(Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,hh)))
            define(id,f'ZylinderschraubeM{d}×{L:g}',s,'Stahl8.8, Oberfläche und Korrosionspaarung festzulegen','Kaufen',
                   f'M{d}×{L:g}; KopfØ{hd}×{hh}; SW{sw}; Gewinde nurØ{core}-Kernkontur, Masse unterschätzt',
                   'ISO4762 / ISO261 Nennmaßfamilie')
        s=parts[id]['shape'].copy();s.Placement=A.Placement(V(*seat),A.Rotation(V(0,0,1),V(*direction))).multiply(s.Placement)
        if pitch:s.rotate(V(),V(1,0,0),pitch)
        return put(id,name,shape=s,angle=angle,sign=sign,z=z)
    # Genuinely split spherical-end model: ball and outer housing are separate solids.
    ball=Part.makeSphere(6).common(box(8,20,20,-4,-10,-10)).cut(axial(3,10,-5))
    define('STD-GELENKKUGEL6','GelenkkugelØ6-Bolzen',ball,'Kaufteil','Kaufen',
           'Funktionskontur mitØ6-Bolzen; Lieferteil/Schwenkwinkel/Tragzahl verifizieren','ISO12240-4 / DIN648 Gelenkkopf-Familie; Einbaumaße eigene Vorgabe')
    head=axial(9,8,-4).cut(Part.makeSphere(6.1)).cut(axial(4.5,10,-5))
    head=head.fuse(Part.makeCylinder(4,15,V(0,0,-21),V(0,0,1)))
    head=head.cut(Part.makeCylinder(2.5,12,V(0,0,-22),V(0,0,1)))
    define('STD-GELENKKOPF6','GelenkkopfM6/Ø6',head,'Kaufteil','Kaufen',
           'Kundenseitige Hüllmaße; InnengewindeM6,Ø6-Bolzen; mindestens±25° winkelbeweglich erforderlich',
           'ISO12240-4 / DIN648 Familie, konkrete Ausführung noch zu beschaffen')
    # Link endpoints are from actual neutral-pitch geometry.
    a0=V(m['pitch_lever_x'],m['pitch_lever_r']*math.cos(math.radians(p['pitch_neutral'])),q['level_z']+m['pitch_lever_r']*math.sin(math.radians(p['pitch_neutral'])))
    joint_angle=math.atan2(a0.y,a0.x)
    b0=V(m['swash_joint_r']*math.cos(joint_angle),m['swash_joint_r']*math.sin(joint_angle),m['swash_z'])
    rod_length=(a0-b0).Length;q['pitch_link_centres_mm']=rod_length
    # End bodies consume21mm per end; turnbuckle has two opposite threaded ends.
    effective=rod_length-24
    if effective<20:raise ValueError('Gestänge zu kurz für zwei Gelenkköpfe')
    define('P13-PITCHGESTAENGE','Pitchgestänge RH/LH',cyl(2.45,effective), '42CrMo4+QT','Drehen; M6RH/M6LH; Gegenmuttern',
           f'Neutraler Kugelmittenabstand{rod_length:.3f}; zwei Gelenkköpfe; ein Ende links; Gewindeeingriff mindestens9mm')
    # Actuator module is a specified industrial assembly, with exposed mount points.
    # No named supplier's hidden internals or unverified catalog dimensions are asserted.
    actuator=ring(7,18,40,46)
    actuator=actuator.fuse(cyl(27,6,z=40)).cut(cyl(7,54,z=39))
    actuator=actuator.cut(cyl(14.01,16,z=49)).cut(cyl(14.1,24,z=67))
    actuator=actuator.cut(box(22,32,22,-11,0,67)).cut(box(14,34,22,-7,-34,67))
    actuator=actuator.fuse(box(20,20,6,-10,-34,46))
    actuator=holes(actuator,[(x,y) for x in [-16,16] for y in [-16,16]],3.3,39,8)
    define('P13-AKTUATORGEHAEUSE','Spindelaktor-Schnittstellengehäuse',actuator,'EN AW-6082 T6','Fräsen/Drehen; als Modul beschaffen oder Sonderbaugruppe fertigen',
           'Kugelschraubtrieb12×4, geführter Außenwagen,12mm nutzbarer Hub;Ø36;30×30-M4-Flansch;2×7001B-Festlager und Hubfenster; RFQ-Sonderbaugruppe',
           pending='Lieferant muss500N,100mm/s,100W-Klasse und Einbaumaße erfüllen; Spiel, Bremsung, Endlagen und Stromausfallzustand offen')
    define('STD-KGT1204','Kugelschraubtrieb12×4 Referenz',cyl(6,65,z=45),'Kaufteil','Kaufen',
           'd12, Steigung4; Nennhülle; Genauigkeit/Vorspannung/Lagerung nach Lieferant','ISO3408 Baugruppenfamilie; Maßhülle eigene Vorgabe')
    nut=ring(6.1,11,73,24)
    nut=nut.fuse(box(20,20,6,-10,10,73)).cut(cyl(6.1,30,z=72)).cut(cyl(3.3,8,0,22,72))
    nut=nut.fuse(box(12,15,6,-6,-24,73)).fuse(box(12,12,12,-6,-32,73))
    nut=nut.cut(box(8.2,8.2,14,-4.1,-30.1,72))
    define('P13-AKTUATORWAGEN','Geführter Aktuatorwagen',nut,'EN AW-7075 T6 / Kauf-Kugelgewindemutter','Fräsen; Kaufmutter einsetzen',
           'Nennpositionz73..97; seitlicher Gelenkanschlussy22/z100; Linearführung und Mutter-Lieferkontur zu bestätigen')
    motor=cyl(20,60,z=50).fuse(cyl(2.5,8,z=42))
    define('REF-AKTUATORMOTOR','Aktorservo100W Einbauhülle',motor,'Kaufteil','Kaufen',
           'Funktionsanforderung100W-Klasse;Ø40×60-Hülle; BLDC mit Encoder und Halte-/Notfallkonzept; keine bestätigte Produktkontur',
           'Industrieservoantrieb, Lieferantenauswahl offen')
    # Slider guide is a commercial subassembly with a custom bracket.
    define('STD-LINEARFUEHRUNG','Aktor-Linearführung Referenz',box(8,8,60,-4,-30,52),'Kaufteil','Kaufen',
           'Vorgegebener Einbauraum8×8×60; Führung führt Querlast, Schraube nur Axiallast','ISO14728 Baugruppenfamilie; Lieferteilgeometrie offen')
    define('STD-7001B','Aktor-Festlager7001B',ring(6,14,0,8),'Wälzlagerstahl','Kaufen',
           '12×28×8; gepaartDB; Endbearbeitung der Kugelgewindespindel aufØ12-Lagersitze','ISO15 / DIN628 Maßfamilie7001')
    # Mechanical stop rings on the stationary central column.
    define('P13-HUBANSCHLAG','Geteilter Hubanschlag',ring(20.05,34,m['swash_z']-32,5).cut(box(40,.5,7,0,-.25,m['swash_z']-33)),
           'EN AW-7075 T6','Drehen/Fräsen; M5-Klemmung',
           'Zweiteil-/Klemmschlitzreferenz; zentrale Endlagen über Distanzscheiben einstellen; keine Sicherheitsbremse')
    # Scissors keep the stationary and rotating swashplate rings at the proper phase.
    define('P13-SCHERENLASCHEN','Scherenlasche',holes(box(8,40,6,-4,-20,-3),[(0,-15),(0,15)],6.2,-4,8),
           'EN AW-7075 T6','Fräsen/Bohren','Achsabstand30; zweiØ6.2; gepaarte Laschen mit Abstandshülsen')
    define('STD-ISO7089-M6-SPEICHE','Speichensockel-ScheibeM6',ring(3.2,6,-39.6,1.6),'Stahl200HV','Kaufen','Ø6.4/Ø12×1.6','ISO7089 M6')
    for sign,label in [(1,'Oben'),(-1,'Unten')]:
        for i in range(int(p['blade_count'])):
            a=m['blade_phase']+i*360/p['blade_count'];pre=label+f'_Blatt{i+1}';z=q['level_z']
            for yy in [-18.8,18.8]:
                for zz in [-12,12]:
                    screw(4,8,(99,yy,zz),(-1,0,0),pre+f'_Deckel_M4_{yy}_{zz}',a,sign,z)
                    screw(4,16,(144,yy,zz),(1,0,0),pre+f'_Patrone_M4_{yy}_{zz}',a,sign,z)
            for yy in [-15,15]:
                for zz in [-6,6]:screw(4,12,(738,yy,zz),(-1,0,0),pre+f'_Aussenring_M4_{yy}_{zz}',a,sign,z)
            for xx in [125,138]:
                for yy in [-15,15]:
                    put('STD-ISO7089-M6-SPEICHE',pre+f'_SpeicheScheibe{xx}_{yy}',shape=parts['STD-ISO7089-M6-SPEICHE']['shape'].translated(V(xx,yy,0)),angle=a,sign=sign,z=z)
                    screw(6,16,(xx,yy,-39.6),(0,0,-1),pre+f'_Speiche_M6_{xx}_{yy}',a,sign,z)
            # New spoke clamps need their own full set of flange and pinch bolts.
            for origin,direction,tag in [(V(155,0,-48),V(1,0,0),'Innen'),(V(719,0,-48),V(-1,0,0),'Aussen')]:
                r=A.Rotation(V(0,0,1),direction)
                for j,(xx,yy) in enumerate(pcd(4,15,45)):
                    pos=origin+r.multVec(V(xx,yy,1));d=r.multVec(V(0,0,1))
                    screw(4,8,tuple(pos),tuple(d),pre+f'_Klemme{tag}_Flansch{j}',a,sign,z)
                for j,yy in enumerate([-18,18]):
                    pos=origin+r.multVec(V(8,yy,20));d=r.multVec(V(1,0,0))
                    screw(4,16,tuple(pos),tuple(d),pre+f'_Klemme{tag}_Quer{j}',a,sign,z)
            upper=V(a0);lower=V(b0)
            for endpoint,other,tag in [(upper,lower,'Oben'),(lower,upper,'Unten')]:
                direction=endpoint-other
                # Body stem points toward the other joint.
                zz=V(direction);zz.normalize()
                pin_axis=V(1,0,0) if tag=='Oben' else V(-math.sin(joint_angle),math.cos(joint_angle),0)
                xx=pin_axis-zz*pin_axis.dot(zz);xx.normalize();yy=zz.cross(xx)
                r=A.Rotation(xx,yy,zz,'ZXY')
                for id,suffix in [('STD-GELENKKOPF6','Kopf'),('STD-GELENKKUGEL6','Kugel')]:
                    orient=r if suffix=='Kopf' else (A.Rotation(V(0,0,1),math.degrees(joint_angle)+90) if tag=='Unten' else A.Rotation())
                    s=parts[id]['shape'].copy();s.Placement=A.Placement(endpoint,orient).multiply(s.Placement)
                    put(id,pre+'_Gest'+tag+suffix,shape=s,angle=a,sign=sign)
            d=upper-lower;u=d/d.Length
            rod=Part.makeCylinder(2.45,rod_length-24,lower+u*12,u)
            put('P13-PITCHGESTAENGE',pre+'_Pitchgestaenge',shape=rod,angle=a,sign=sign)
            mate(pre+'_Pitchhebel',pre+'_Pitchgestaenge','Zwei M6-Gelenkköpfe,Ø6-Schulterbolzen; RH/LH-Gestänge; Kugelmittenabstand aus CAD')
            mate(pre+'_Pitchgestaenge',label+'_Taumelring','KugelgelenkR90; Winkelfreigang separat in Kinematikprüfung')
        for i,a in enumerate([0,120,240]):
            pre=label+f'_Aktor{i+1}'
            for id,suffix,offset in [('P13-AKTUATORGEHAEUSE','Gehaeuse',V(82,0,0)),('STD-KGT1204','Spindel',V(82,0,0)),('P13-AKTUATORWAGEN','Wagen',V(82,0,0)),('STD-LINEARFUEHRUNG','Fuehrung',V(82,0,0)),('REF-AKTUATORMOTOR','Motor',V(202,0,0))]:
                s=parts[id]['shape'].translated(offset);put(id,pre+'_'+suffix,shape=s,angle=a,sign=sign)
            for j,zz in enumerate([49,57]):
                s=parts['STD-7001B']['shape'].translated(V(82,0,zz));put('STD-7001B',pre+f'_Festlager{j}',shape=s,angle=a,sign=sign)
            for id,tag in [('STD-GELENKKOPF6','Gelenkkopf'),('STD-GELENKKUGEL6','Gelenkkugel')]:
                put(id,pre+'_'+tag,shape=parts[id]['shape'].translated(V(82,22,100)),angle=a,sign=sign)
            screw(6,16,(82,22,73),(0,0,-1),pre+'_Wagen_Gelenk_M6',a,sign)
            mate(label+'_Zentralplatte',pre+'_Gehaeuse','GE20ES-Gelenkfuß;12mm nutzbarer Hub; geführter Außenwagen; Schnittstellengehäuse nach RFQ')
            mate(pre+'_Wagen',label+'_Taumeltraeger','M6-Kugelgelenk, seitlicher Abtrieb; stationäre Scherenführung gegen Mitdrehen')
        put('P13-HUBANSCHLAG',label+'_Hubanschlag',sign=sign)
    # Remaining drive stack: through-bolts at each post and at the hub membrane circle.
    for sign,label in [(1,'Oben'),(-1,'Unten')]:
        for i,(x,y) in enumerate(pcd(p['blade_count'],p['drive_post_radius'])):
            L=q['membrane_z']+p['membrane_t']-q['carrier_bottom']+24
            # A cut-to-length DIN976 tie rod is preferable to inventing a stocked screw length.
            id='STD-DIN976-M6-ROTOR'
            if id not in parts:
                define(id,'Rotor-ZugankerM6',cyl(2.45,L),'Stahl8.8','DIN976-Stange ablängen; entgraten',
                       f'M6×{L:g}; Muttern/Scheiben beidseitig; Gewinde-Kernkontur','DIN976-1 / ISO261 Familie')
            s=parts[id]['shape'].translated(V(x,y,q['carrier_bottom']-15))
            put(id,label+f'_Zuganker{i+1}',shape=s,sign=sign)
            mate(label+'_Membran',label+'_Innenring','DIN976-M6-Zuganker; Distanzsäule; ISO7089-Scheiben/ISO4032-Muttern beidseitig')
    q['actuator_requirement']=dict(stroke_mm=12,force_N=500,speed_mm_s=100,power_class_W=100,
                                   screw_lead_mm=4,rotational_speed_rpm=1500,
                                   status='RFQ_ANFORDERUNG_KEIN_VERIFIZIERTES_KAUFPRODUKT')
    from verbindungen import add as hardware
    hardware(config,parts,scene,q,define,put,mate,screw)
