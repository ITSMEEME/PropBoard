"""P13 mechanical design. Nominal standard envelopes and individually manufactured parts.

The build does not confer a supplier, strength, fatigue, or flight release.
All dimensions in mm. Local blade axes: X radial, Y chord, Z rotor normal.
"""
import json, math, sys
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path[:0]=[str(H/'basis_p12'),'/usr/lib/freecad-python3/lib']
import FreeCAD as A, Part
from spiegeln import reflected, X, Y, Z
from geometrie import build as base_build, box, cyl, ring, holes, pcd
V=A.Vector

def axial(r,length,x=0,y=0,z=0):
    return Part.makeCylinder(r,length,V(x,y,z),V(1,0,0))

def annulus_x(ri,ro,x,length):
    return axial(ro,length,x).cut(axial(ri,length+2,x-1))

def rotate(s,angle):
    s=s.copy();s.rotate(V(),V(0,0,1),angle);return s

def profile(p,m,x,inner=False):
    f=(x-p['blade_root'])/(p['rotor_radius']-p['blade_root'])
    t=p['blade_thickness']
    if x<m['root_transition_end']:
        t+=(m['root_thickness_ratio']-t)*min(1,(m['root_transition_end']-x)/40)
    if x>m['tip_transition_start']:
        t+=(m['tip_thickness_ratio']-t)*(x-m['tip_transition_start'])/(p['rotor_radius']-m['tip_transition_start'])
    chord=p['blade_chord']*(1+(p['blade_taper']-1)*f)
    pts=[];samples=[(1-math.cos(math.pi*i/40))/2 for i in range(41)]
    for sign,seq in [(1,samples),(-1,list(reversed(samples[1:])) )]:
        for a in seq:
            z=5*t*(.2969*math.sqrt(a)-.126*a-.3516*a*a+.2843*a**3-.1036*a**4)*chord+p['blade_te']/2*a**10
            y=(p['pitch_axis']-a)*chord
            if inner:
                # Explicit inner mould line, not an assertion of a constant-normal offset.
                y*=.94;z=max(.1,z-m['shell_t']) if a>.04 else z*.4
            pts.append(V(x,y,sign*z))
    return Part.makePolygon(pts+[pts[0]])

def blade_shapes(p,m):
    start,end=p['blade_root'],p['rotor_radius']
    stations=sorted(set([start,start+2,start+50,start+60,m['root_transition_end'],m['tip_transition_start'],end-2,end]))
    stations=[x for x in stations if start<=x<=end]
    outer=Part.makeLoft([profile(p,m,x) for x in stations],True,True)
    inside=Part.makeLoft([profile(p,m,x,True) for x in stations],True,True)
    if outer.Volume<0:outer.reverse()
    if inside.Volume<0:inside.reverse()
    shell=outer.cut(inside)
    # Two moulded halves, bonded along leading/trailing seams and bulkheads.
    top=shell.common(box(end+20,400,100,0,-200,0))
    bottom=shell.common(box(end+20,400,100,0,-200,-100))
    root=inside.common(box(52,200,100,start,-100,-50)).cut(axial(9.2,54,start-1))
    root=root.cut(axial(10.2,4,200))
    tip=inside.common(box(40,200,100,end-40,-100,-50)).cut(axial(6.2,42,end-41))
    web=inside.common(box(end-start-92,1.5,80,start+52,14,-40))
    web2=inside.common(box(end-start-92,1.5,80,start+52,-15.5,-40))
    return outer,dict(SCHALE_OBEN=top,SCHALE_UNTEN=bottom,WURZELBLOCK=root,SPITZENBLOCK=tip,HOLM_VORN=web,HOLM_HINTEN=web2)


def build(config):
    p=config['parameters'];m=config['mechanics']
    parts,scene,q=base_build(p,config.get('materials_assumed'))
    node_positions={n['name']:n['position_mm'] for n in q.get('cfk_nodes',[])}
    for row in scene:
        if row['id']=='REF-MN1330':
            row['pose']=dict(angle=0,sign=-1 if row['name'].startswith('Unten') else 1,z=q['motor_face'],local=A.Placement())
        elif row['id'].startswith('CFK-KNOTEN') and row['name'] in node_positions:
            row['pose']=dict(angle=0,sign=1,z=0,local=A.Placement(V(*node_positions[row['name']]),A.Rotation()))
        elif row['id']=='CFK-BRUECKE-END':
            neg=row['variant']=='MX'
            row['pose']=dict(angle=0,sign=1,z=0,local=A.Placement(V((-1 if neg else 1)*p['cfk_bridge_length']/2,0,0),A.Rotation()),mirror_x=neg)
        elif row['id'].startswith('REF-ACHS-MUTTER'):
            idx=int(row['name'].split('_Rolle_')[1].split('_')[0])-1
            row['pose']=dict(angle=q['guide_angles'][idx],sign=-1 if row['name'].startswith('Unten') else 1,z=q['level_z'],local=A.Placement(V(q['roller_center'],0,q['axle_half_length']),A.Rotation()))
    mates=[];new=[]
    def define(id,name,shape,material,process,features,standard='',pending='Festigkeits-/Ermüdungs- und Lieferantenfreigabe offen'):
        s=shape.removeSplitter()
        if s.Volume<0:s.reverse()
        if not s.isValid() or len(s.Solids)!=1 or s.Volume<=0:
            raise ValueError(f'{id}: {len(s.Solids)} solids, valid={s.isValid()}')
        parts[id]=dict(id=id,name=name,shape=s,material=material,process=process,
                       features=features,open=pending,reference=bool(standard),standard=standard,
                       source='Nennmaßfamilie, kein verifiziertes Lieferanten-CAD' if standard else 'P13 Eigenkonstruktion',
                       tolerance='ISO2768-1m nur unbemaßte Längen; GPS nach ISO22081 vereinbaren; Funktionspassungen separat')
    def put(id,name,shape=None,angle=0,sign=1,z=0):
        local=(shape if shape is not None else parts[id]['shape']).copy()
        local_transform=local.Placement.multiply(parts[id]['shape'].Placement.inverse())
        s=local.copy();s.rotate(V(),V(0,0,1),angle);s.translate(V(0,0,z))
        if sign<0:s=reflected(s,Z)
        variant='MZ' if sign<0 else 'NOMINAL'
        manufactured=reflected(local,Z) if sign<0 else local.copy()
        scene.append(dict(id=id,name=name,shape=s,context=False,variant=variant,manufacturing_shape=manufactured,
                          pose=dict(angle=angle,sign=sign,z=z,local=local_transform)))
        new.append(name)
        return name
    def mate(a,b,interface,check='DIMENSIONIERTE_SCHNITTSTELLE',pending='Last-/Montagenachweis offen'):
        mates.append(dict(a=a,b=b,interface=interface,geometric_status=check,release_pending=pending))
    def remove(ids):
        scene[:]=[r for r in scene if r['id'] not in ids]
        for id in ids:parts.pop(id,None)
    remove({'REF-FLUEGEL','P12-005','P12-014','P12-010'})
    # Original P12 bolt shapes remain reference envelopes; P13 assigns families explicitly.
    for id,part in parts.items():
        if id.startswith('REF-SCHRAUBE'):
            part.update(standard='ISO 4762 / ISO 261 Gewindefamilie; konkrete Länge siehe Stückliste',
                        source='Nennmaßreferenz aus P12, keine zertifizierte Normteilgeometrie')
        if id=='REF-7202B':part.update(standard='ISO 15 Maßreihe 7202; Schrägkugellagerpaar DB',source='Nennmaße 15×35×11; Tragzahlen/Vorspannung vom Lieferanten')
    # Machined root carrier: 64 mm deep, with radial cartridges between the drive posts.
    carrier=ring(p['carrier_inner_r'],p['carrier_outer_r'],-p['carrier_height']/2,p['carrier_height'])
    carrier=holes(carrier,pcd(p['blade_count'],p['drive_post_radius']),p['drive_hole_d'],-p['carrier_height'],2*p['carrier_height'])
    for i in range(int(p['blade_count'])):
        a=m['blade_phase']+i*360/p['blade_count']
        cut=axial(m['root_housing_r']+.1,42,98)
        cut=cut.fuse(axial(m['root_flange_r']+.1,9,98))
        cut=cut.fuse(box(20,56,56,138,-28,-28))
        carrier=carrier.cut(rotate(cut,a))
        for yy in [-18.8,18.8]:
            for zz in [-12,12]:
                carrier=carrier.cut(rotate(axial(1.65,12,126,yy,zz),a))
                carrier=carrier.cut(rotate(axial(2.2,3,107,yy,zz),a))
        for y in [-15,15]:
            for x in [125,138]:
                h=cyl(2.5,12,x,y,-p['carrier_height']/2-1)
                carrier=carrier.cut(rotate(h,a))
    define('P13-INNENRING','Innenring mit Patronenaufnahmen',carrier,'EN AW-7075 T6','5-Achs-Fräsen, Bohren, Gewinde',
           '64mm axial; radialeØ40.2; rückseitigeØ52.2; Plananlage x138; blinde M6-Kernlöcher für Speichensockel')
    track=parts['P12-015']['shape'] # only used to keep imported roller type alive
    from geometrie import revolve
    track=revolve([(744,-12),(758,-12),(770,0),(758,12),(744,12)])
    for i in range(int(p['blade_count'])):
        a=m['blade_phase']+i*360/p['blade_count']
        for y in [-15,15]:
            for zz in [-6,6]:track=track.cut(rotate(axial(1.65,7,743,y,zz),a))
    define('P13-AUSSENRING','V-Laufbahn mit integralem Tragsteg',track,'42CrMo4+QT','Rohdrehen, Bohren, Härten/Laufbahnschleifen',
           'Tragsteg R744..758; V-Profil bisR770 durchgehend; 4×M4 je Außenlagerträger, 6mm symbolische Gewindetiefe')
    # Housing with defined end stops. Bearings remain nominal solid envelopes.
    housing=axial(20,35,103).fuse(axial(26,4,103)).fuse(axial(26,6,138))
    housing=housing.cut(axial(16.01,34,103)).cut(axial(10.5,9,137)).cut(axial(14,5,102))
    for yy in [-18.8,18.8]:
        for zz in [-12,12]:
            housing=housing.cut(axial(1.65,12,103,yy,zz))
            housing=housing.cut(axial(2.2,8,137,yy,zz))
    define('P13-WURZELGEHAEUSE','Pitchlagerpatrone',housing,'EN AW-7075 T6','Drehen/Fräsen; Lagersitze nach ISO286',
           '2×7201B12×32×10 DB; SitzeØ32 H7; Außenringdistanz10; Frontschulter x137; GehäuseØ40; FlanscheØ52')
    cover=annulus_x(14,26,99,4).fuse(annulus_x(14,16,103,4))
    for yy in [-18.8,18.8]:
        for zz in [-12,12]:cover=cover.cut(axial(2.2,10,98,yy,zz))
    define('P13-WURZELDECKEL','Patronendeckel',cover,'EN AW-7075 T6','Drehen/Fräsen/Bohren','Außenringanschlag x107; zentrale MutterfreistellungØ24; 4×Ø4.4')
    define('STD-7201B','Schrägkugellager7201B',annulus_x(6,16,0,10),'Wälzlagerstahl','Kaufen',
           '12×32×10; gepaart DB; Dreh-/Schwinglast und Vorspannklasse separat bestellen','ISO15 / DIN628 Maßfamilie7201')
    define('P13-DISTANZ-INNEN','Pitch-Innenringdistanz',annulus_x(6.05,9,117,10),'42CrMo4+QT','Drehen/Stirnschleifen',
           'Ø12.1/18×10; axiale Paarabstimmung mit Außenringdistanz')
    define('P13-DISTANZ-AUSSEN','Pitch-Außenringdistanz',annulus_x(13.5,16,117,10),'42CrMo4+QT','Drehen/Stirnschleifen','Ø27/32×10; Parallelität und Paarabstimmung auf Zeichnung')
    shaft=axial(6,132,68).fuse(axial(8,8,137))
    shaft=shaft.cut(box(8,8,5,68,-4,5))
    shaft=shaft.cut(axial(1.65,14,67)).cut(axial(2.1,14,187))
    # A real keyway is provided on the removable blade connection.
    shaft=shaft.cut(box(26,4,4,152,-2,4.2))
    define('P13-PITCHWELLE','Pitchwelle Festlager',shaft,'42CrMo4+QT','Drehen, Schleifen, Fräsen',
           'Ø12 k6 Lagersitze; M12×1 x96..107 symbolisch; Schulter x137; Passfedernut4×4 an x152..178; ISO13715 Kanten')
    define('STD-KM1','Nutmutter KM1',annulus_x(6.05,11,102,4),'Stahl','Kaufen',
           'M12×1, Nennhülle; mit passender Sicherungsscheibe bestellen','ISO2982-2 / KM1 Maßfamilie')
    define('STD-MB1','Sicherungsscheibe MB1',annulus_x(6.05,12.5,106,1),'Stahl','Kaufen',
           'Nennhülle; Innen-/Außenlaschen und Wellensicherungsnut vor Lieferfreigabe spezifizieren','ISO2982-2 / MB1 Maßfamilie')
    key=box(24,4,4,153,-2,4.2)
    define('STD-PASSFEDER4','Passfeder4×4×24',key,'C45','Kaufen', '4×4×24; hier gerade Endkontur, Nut nach Lieferform anpassen','DIN6885-1 Maßfamilie')
    insert=annulus_x(6.05,9,150,50).cut(box(26,4.1,4,152,-2.05,4.2))
    define('P13-WURZELEINSATZ','Flügel-Wurzeleinsatz',insert,'Titan Grade5 oder freigegebenes isoliertes Aluminium','Drehen/Fräsen, Klebflächen vorbereiten',
           'Ø18; BohrungØ12.1; Passfedernut4;50mm Einbettlänge;0.2mm Klebfuge zur CFK-Wurzel')
    outer_pin=axial(4,64,670)
    for xx in [719.2,727]:outer_pin=outer_pin.cut(annulus_x(3.75,4.1,xx,.8))
    define('P13-AUSSENZAPFEN','Flügel-Außenzapfen',outer_pin,'42CrMo4+QT','Drehen/Schleifen; Sicherungsnuten',
           'Ø8 k6 Lagersitz720..727; KlebesitzØ8; DIN471-Nuten/Endanschläge funktional separat festlegen')
    define('P13-SPITZENEINSATZ','Flügel-Spitzeneinsatz',annulus_x(4.05,6,670,38),'Titan Grade5 oder isoliertes Aluminium','Drehen, Klebvorbereitung','Ø12/Ø8.1×38; CFK-Klebfuge0.2')
    define('STD-608','Loslager608',annulus_x(4,11,0,7),'Wälzlagerstahl','Kaufen',
           '8×22×7; Außenring axial verschieblich ±1mm; Dichtung/Spiel nach Betrieb festlegen','ISO15 Maßfamilie608')
    # Standard CFK clamp and liner geometry reused for each radial spoke.
    root_mount=box(34,44,6,120,-22,-38)
    root_mount=root_mount.fuse(box(8,16,24,147,-8,-62)).fuse(axial(21,5,150,0,-48))
    for xx in [125,138]:
        for yy in [-15,15]:root_mount=root_mount.cut(cyl(3.3,8,xx,yy,-39))
    for yy,zz in pcd(4,15,45):root_mount=root_mount.cut(axial(1.65,9,147,yy,zz-48))
    define('P13-SPEICHENWURZEL','Speichensockel',root_mount,'EN AW-7075 T6','5-Achs-Fräsen/Bohren/Gewinde',
           '4×M6 zum Innenring; P12-Standardflansch Ø42 für geteilte20mm-CFK-Klemme; Speichenachse48mm unter Pitchachse')
    out=axial(14,18,716).fuse(box(5,16,48,719,-8,-48)).fuse(axial(21,5,719,0,-48))
    out=out.fuse(box(10,44,28,734,-22,-14))
    out=out.cut(axial(11.01,9,719)).cut(axial(6,21,715))
    for yy in [-15,15]:
        for zz in [-6,6]:out=out.cut(axial(2.2,14,733,yy,zz)).cut(axial(3.75,4,734,yy,zz))
    for yy,zz in pcd(4,15,45):out=out.cut(axial(1.65,9,719,yy,zz-48))
    define('P13-AUSSENLAGERTRAEGER','Außenlagerträger mit Speichenflansch',out,'EN AW-7075 T6','5-Achs-Fräsen, Bohren',
           '608-SitzØ22 H7; Kammer719..728; ±1mm axiales Loslager; radialer CFK-Flansch;4×M4 an Tragsteg')
    define('P13-SPEICHE-CFK','Rotor-Speiche CFK20×17',annulus_x(8.5,10,160,554).translated(V(0,0,-48)),
           'CFK20×17 aus CBU20171005TG','Rohrzuschnitt; Enden versiegeln','L554; zwei30mm Klemmlängen; keine Querbohrungen')
    # CFK blade is a separately quotable assembly, not a homogeneous aerodynamic solid.
    outer,wing_parts=blade_shapes(p,m)
    for key,shape in wing_parts.items():
        define('P13-CFK-'+key,'CFK-Flügel '+key,shape,'CFK/Epoxid; Laminat vom Dienstleister auszulegen',
               'Geteilte Negativformen, Prepreg/Infusion nach qualifiziertem Prozess; Klebemontage',
               'Geometrische Innen-/Außenform;1.2mm Z-Abstand im Hauptbereich; keine festgelegte Lagenfreigabe')
    # Root pitch lever: removable, keyed shaft clamp and transverse spherical joint pin.
    d_bore=axial(6.05,8,68).cut(box(10,8,6,67,-4,5.05))
    lever=axial(10,6,69).cut(d_bore).fuse(box(6,25,8,69,0,-4)).fuse(axial(7,6,69,25,0))
    lever=lever.cut(d_bore).cut(axial(3.1,8,68,25,0))
    define('P13-PITCHHEBEL','Pitchhebel',lever,'EN AW-7075 T6','Fräsen/Bohren; geteilte Klemmstelle',
           'Hebel25; WellenaufnahmeØ12.1; GelenkbolzenØ6; Klemmsicherung/Torsionsschluss separat bemessen')
    # Base support for the three screw-drive cartridges at each level.
    foot=ring(12.5,110,30,10)
    foot=holes(foot,[(x,y) for x in [-45,45] for y in [-32,32]],6.6,29,12)
    foot=holes(foot,pcd(3,82),6.6,29,12)
    define('P13-ZENTRALPLATTE','Zentralstütz-/Aktuatorplatte',foot,'EN AW-6082 T6','Fräsen/Bohren',
           'Ø220×10; ZentralbohrungØ25; vorhandenes90×64-M6-Lochbild;3 AktuatorplätzeR82')
    # Sleeve, spherical articulation and rotating bearing form a genuine swashplate chain.
    define('P13-GLEITHUELSE','Taumelscheiben-Gleithülse',ring(20.1,30,m['swash_z']-25,50),'42CrMo4+QT','Drehen/Schleifen',
           'InnenØ40.2 als vorläufige Gleitpassung; GE60-InnensitzØ60; L50; Endanschläge/Klemmringe erforderlich')
    # GE is represented as a dimensional ring; tilt envelope is checked separately.
    define('STD-GE60ES','Gelenklager GE60ES',ring(30,45,m['swash_z']-22,44),'Kaufteil','Kaufen',
           'd60/D90/B44/C36; Nennhülle, keine innere Kugelfläche; Schmierung/Kippwinkel lieferantenspezifisch','ISO12240-1 Maßfamilie GE60ES')
    tilting=ring(45.01,50,m['swash_z']-18,36)
    # Arms sit below the rotating bearing, avoiding a fixed member through that bearing.
    for a in [0,120,240]:
        arm=box(27,10,6,46,-5,m['swash_z']-35)
        arm=arm.fuse(box(4,10,18,46,-5,m['swash_z']-29))
        arm=arm.fuse(box(6,22,6,70,0,m['swash_z']-35))
        fork=box(4,20,20,72,12,m['swash_z']-42).fuse(box(4,20,20,87,12,m['swash_z']-42))
        fork=fork.fuse(box(19,20,3,72,12,m['swash_z']-45))
        fork=fork.cut(axial(3.1,22,71,22,m['swash_z']-32))
        arm=arm.fuse(fork)
        arm=arm.cut(axial(3.3,34,62,22,m['swash_z']-32))
        arm=arm.cut(axial(6.2,8,64,22,m['swash_z']-32))
        arm=arm.cut(cyl(4.2,10,82,22,m['swash_z']-47))
        tilting=tilting.fuse(rotate(arm,a))
    define('P13-TAUMEL-INNEN','Nichtrotierender Taumelträger',tilting,'EN AW-7075 T6','Drehen/Fräsen',
           'GE60 AußensitzØ90;61820 InnensitzØ100;3 abgesenkte Arme; Scherenführung verhindert Mitdrehen')
    define('STD-61820','Taumelscheibenlager61820',ring(50,62.5,m['swash_z']-6.5,13),'Wälzlagerstahl','Kaufen',
           '100×125×13; dünnwandiges Rillenkugellager; Betrieb unter Kippung nur mit gemeinsamem Träger','ISO15 Maßfamilie61820')
    rotating=ring(62.51,77.5,m['swash_z']-9,18)
    for i in range(int(p['blade_count'])):
        a=m['blade_phase']+i*360/p['blade_count']+math.degrees(math.atan2(m['pitch_lever_r']*math.cos(math.radians(p['pitch_neutral'])),m['pitch_lever_x']))
        tab=box(28,4,27,73,-11,m['swash_z']-15).fuse(box(28,4,27,73,7,m['swash_z']-15))
        tab=tab.fuse(box(28,22,3,73,-11,m['swash_z']-15))
        tab=tab.cut(Part.makeCylinder(3.1,26,V(90,-13,m['swash_z']),V(0,1,0)))
        rotating=rotating.fuse(rotate(tab,a))
    define('P13-TAUMEL-AUSSEN','Rotierender Taumelring',rotating,'EN AW-7075 T6','Drehen/Fräsen',
           '61820 AußensitzØ125 H7;8 GelenkplätzeR90; Scherenmitnehmer zur Rotorphase erforderlich')
    q.update(mechanics=m,interfaces=mates,new_instances=new,full_mechanical_release=False)
    # Installed roots, spokes, blades, and the two common swashplates.
    for sign,label in [(1,'Oben'),(-1,'Unten')]:
        z=q['level_z']
        inner=put('P13-INNENRING',label+'_Innenring',sign=sign,z=z)
        tr=put('P13-AUSSENRING',label+'_Aussenring',sign=sign,z=z)
        for id,name in [('P13-ZENTRALPLATTE','Zentralplatte'),('P13-GLEITHUELSE','Gleithuelse'),('STD-GE60ES','Gelenklager'),('P13-TAUMEL-INNEN','Taumeltraeger'),('STD-61820','Taumellager'),('P13-TAUMEL-AUSSEN','Taumelring')]:
            put(id,label+'_'+name,sign=sign)
        for i in range(int(p['blade_count'])):
            a=m['blade_phase']+i*360/p['blade_count'];prefix=label+f'_Blatt{i+1}'
            for id,name in [('P13-WURZELGEHAEUSE','Patrone'),('P13-WURZELDECKEL','Deckel'),('P13-DISTANZ-INNEN','DistanzInnen'),('P13-DISTANZ-AUSSEN','DistanzAussen'),('STD-KM1','Nutmutter'),('STD-MB1','Sicherungsscheibe'),('P13-AUSSENLAGERTRAEGER','Aussenlagertraeger'),('P13-SPEICHENWURZEL','Speichensockel'),('P13-SPEICHE-CFK','Speiche')]:
                put(id,prefix+'_'+name,angle=a,sign=sign,z=z)
            for bx,tag in [(107,'A'),(127,'B')]:
                s=parts['STD-7201B']['shape'].translated(V(bx,0,0));put('STD-7201B',prefix+'_7201'+tag,shape=s,angle=a,sign=sign,z=z)
            put('STD-608',prefix+'_608',shape=parts['STD-608']['shape'].translated(V(720,0,0)),angle=a,sign=sign,z=z)
            # Pitch parts rotate together around the local radial axis.
            for id,name in [('P13-PITCHWELLE','Pitchwelle'),('STD-PASSFEDER4','Passfeder'),('P13-WURZELEINSATZ','Wurzeleinsatz'),('P13-SPITZENEINSATZ','Spitzeneinsatz'),('P13-AUSSENZAPFEN','Aussenzapfen'),('P13-PITCHHEBEL','Pitchhebel')]+[('P13-CFK-'+k,k) for k in wing_parts]:
                s=parts[id]['shape'].copy();s.rotate(V(),V(1,0,0),p['pitch_neutral'])
                put(id,prefix+'_'+name,shape=s,angle=a,sign=sign,z=z)
            # Two standard split clamps and insulating liners for the CFK spoke.
            for point,direction,tag in [(V(155,0,-48),V(1,0,0),'Innen'),(V(719,0,-48),V(-1,0,0),'Aussen')]:
                for half in ['A','B']:
                    s=parts['CFK-KLEMM-'+half]['shape'].copy();s.Placement=A.Placement(point,A.Rotation(V(0,0,1),direction)).multiply(s.Placement)
                    put('CFK-KLEMM-'+half,prefix+'_Speichenklemme'+tag+half,shape=s,angle=a,sign=sign,z=z)
                s=parts['CFK-ZWISCHENLAGE']['shape'].copy();s.Placement=A.Placement(point+direction*5,A.Rotation(V(0,0,1),direction)).multiply(s.Placement)
                put('CFK-ZWISCHENLAGE',prefix+'_Isolierung'+tag,shape=s,angle=a,sign=sign,z=z)
            mate(inner,prefix+'_Patrone','Ø40.2 Gehäuseaufnahme; Flanschanschlag x138; Deckel von innen montierbar')
            mate(prefix+'_Patrone',prefix+'_Pitchwelle','7201B-DB-Paar; KM1/MB1; axialer Festlagerpfad')
            mate(prefix+'_Pitchwelle',prefix+'_Wurzeleinsatz','Ø12/4×4 Passfeder; zusätzliche axiale Sicherung vor Freigabe')
            mate(prefix+'_Wurzeleinsatz',prefix+'_WURZELBLOCK','50mm Klebeeinbettung;0.2mm Fuge; galvanische Isolation')
            mate(prefix+'_SPITZENBLOCK',prefix+'_Spitzeneinsatz','38mm Einbettung;0.2mm Klebfuge')
            mate(prefix+'_Aussenzapfen',prefix+'_608','Ø8 k6; Außenring imØ22-H7-Sitz axial±1mm')
            mate(prefix+'_Aussenlagertraeger',tr,'Vier M4;6mm Eingriff im separaten Tragsteg; V-Kontur bleibt durchgehend')
            mate(inner,prefix+'_Speichensockel','Vier M6;4×Blindkernloch12tief; keine CFK-Querbohrung')
            mate(prefix+'_Speichensockel',prefix+'_Speiche','Geteilte Standardklemme und Isolierlage')
            mate(prefix+'_Speiche',prefix+'_Aussenlagertraeger','Geteilte Standardklemme und Isolierlage')
    from anlenkung import add
    add(config,parts,scene,q,define,put,mate)
    bad=[]
    for row in scene:
        if row['shape'].Volume<0:row['shape'].reverse()
        if not row['shape'].isValid() or len(row['shape'].Solids)!=1 or row['shape'].Volume<=0:
            bad.append((row['name'],row['id'],len(row['shape'].Solids),row['shape'].Volume))
    if bad:raise ValueError('Ungültige installierte Körper: '+str(bad[:20]))
    return parts,scene,q
