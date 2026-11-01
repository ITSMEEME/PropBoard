"""Static motor brackets, standing deck, and bolted skid landing gear."""
import math
import FreeCAD as A,Part
from spiegeln import reflected, X, Y, Z
from mechanik import V,box,cyl,ring,holes,pcd,axial,rotate
from verbindungen import replace

def add(config,parts,scene,q,define,put,mate,screw):
    p=config['parameters'];m=config['mechanics']
    # Motor bracket arms are part of the central plate, not floating motor bodies.
    for sign,label,R in [(1,'Oben',277),(-1,'Unten',322)]:
        foot=parts['P13-ZENTRALPLATTE']['shape'].copy()
        for a in [0,120,240]:
            arm=box(R-100,40,8,100,-20,32).fuse(cyl(25,8,R,0,32))
            arm=arm.cut(cyl(3,12,R,0,30))
            for x,y in pcd(4,15,45):arm=arm.cut(cyl(1.7,12,R+x,y,30))
            foot=foot.fuse(rotate(arm,a))
            # Four actual actuator flange holes, replacing the earlier single pilot.
            for xx in [-15,15]:
                for yy in [-15,15]:foot=foot.cut(rotate(cyl(1.65,10,82+xx,yy,30),a))
        id='P13-ZENTRALPLATTE-'+label.upper()
        define(id,'Zentralplatte mit Servoträgern '+label,foot,'EN AW-6082 T6','5-Achs-Fräsen/Bohren/Gewinde',
               f'Ø228 fertige Grundplatte; drei Servoträger bisR{R};GE20ES-Aktorfüße;4×M3/PCD30 Motor-RFQ-Schnittstelle')
        for row in scene:
            if row['name']!=label+'_Zentralplatte':continue
            local=reflected(foot,Z) if sign<0 else foot.copy()
            row.update(id=id,shape=local.copy(),manufacturing_shape=local,variant='MZ' if sign<0 else 'NOMINAL')
        for i,a in enumerate([0,120,240]):
            for xx in [-15,15]:
                for yy in [-15,15]:screw(4,12,(82+xx,yy,46),(0,0,1),label+f'_Aktor{i+1}_FlanschM4{xx}_{yy}',a,sign)
            # Move the servo to the central layer: it clears all rotating truss members.
            row=next(r for r in scene if r['name']==label+f'_Aktor{i+1}_Motor')
            motor=cyl(20,60,z=-30).fuse(cyl(2.5,19,z=30))
            for x,y in pcd(4,15,45):motor=motor.cut(cyl(1.25,7,x,y,24))
            idm='REF-AKTUATORMOTOR-'+label.upper()
            if idm not in parts:define(idm,'Aktorservo100W '+label,motor,'Kaufteil','Kaufen',
                'Ø40×60 Hülle; RFQ-Flansch4×M3/PCD30, WelleØ5; kein identifiziertes Lieferprodukt',
                'Industrieservo-Funktionsanforderung; eigene vorgegebene Einbaumaße')
            s=motor.translated(V(R,0,0));s=rotate(s,a)
            if sign<0:s=reflected(s,Z)
            row.update(id=idm,shape=s,manufacturing_shape=motor.copy())
            for j,(x,y) in enumerate(pcd(4,15,45)):
                tid='P13-SERVO-DISTANZ2'
                if tid not in parts:define(tid,'Servo-Distanz2mm',ring(1.7,3,30,2),'EN AW-6082 T6','Drehen','Ø6/Ø3.4×2')
                put(tid,label+f'_Aktor{i+1}_ServoDistanz{j}',shape=parts[tid]['shape'].translated(V(R+x,y,0)),angle=a,sign=sign)
                screw(3,12,(R+x,y,38.8),(0,0,1),label+f'_Aktor{i+1}_ServoM3{j}',a,sign)
            for r,bore,tag in [(82,6.1,'Spindel'),(R,2.6,'Motor')]:
                tid='STD-HTD3M20-'+tag
                if tid not in parts:define(tid,'Zahnriemenscheibe20HTD3M '+tag,ring(bore,9.5,42,6),'Aluminium','Kaufen / Bohrung anpassen',
                    f'20Z/3mm; TeilkreisØ{60/math.pi:.3f}; Zahnung nur Rundhülle; Klemmnabe nach Lieferant',
                    'HTD3M20 Systemfamilie, genaue Lieferkontur offen')
                put(tid,label+f'_Aktor{i+1}_Riemenscheibe{tag}',shape=parts[tid]['shape'].translated(V(r,0,0)),angle=a,sign=sign)
            length=60+2*(R-82)
            tid=f'STD-HTD3M-L{length}'
            outer=cyl(11,6,82,0,42).fuse(cyl(11,6,R,0,42)).fuse(box(R-82,22,6,82,-11,42))
            inner=cyl(9.55,8,82,0,41).fuse(cyl(9.55,8,R,0,41)).fuse(box(R-82,19.1,8,82,-9.55,41))
            if tid not in parts:define(tid,f'ZahnriemenHTD3M{length}',outer.cut(inner),'Kaufteil','Kaufen',
                f'L{length},Breite6,Achsabstand{R-82};20/20Z; glatte Riemenhülle, kein Zahneingriffmodell',
                'HTD3M Systemfamilie, konkrete Riemenlänge/Spannreserve mit Lieferant bestätigen')
            put(tid,label+f'_Aktor{i+1}_Zahnriemen',angle=a,sign=sign)
            mate(label+'_Zentralplatte',label+f'_Aktor{i+1}_Motor','Auskragender Servoträger;4×M3/PCD30 nach RFQ;2mm Distanz;15mm Langloch-Spannreserve noch nicht modelliert')
    # Lower spindle-pulley clearance in the specified actuator cartridge.
    case=parts['P13-AKTUATORGEHAEUSE']['shape'].cut(cyl(11.1,10,z=39)).cut(box(24,24,8,0,-12,42))
    replace(parts,scene,'P13-AKTUATORGEHAEUSE',case)
    # Four upper motor-support nodes have free upper hemispheres for the deck supports.
    tops=[r for r in scene if 'Oben_Motorstütze_' in r['name'] and r['id'].startswith('CFK-KNOTEN')]
    node_positions={n['name']:V(*n['position_mm']) for n in q['cfk_nodes']}
    deck_base=q['beam_z']+2*p['cfk_node_core_r']+16  # flange top of the modified node
    deck_beam_z=deck_base+30
    deck_z=deck_beam_z+40
    deck=box(1100,320,8,-550,-160,deck_z)
    beam=box(1000,60,40,-500,-30,deck_beam_z).cut(box(1002,54,34,-501,-27,deck_beam_z+3))
    standoff=ring(10,30,deck_base,30)
    bolt_points=[]
    for row in tops:
        node_id=row['id'];nodepos=node_positions[row['name']]
        shape=parts[node_id]['shape'].copy().fuse(cyl(30,25,z=10)).fuse(cyl(35,6,z=35))
        for dx,dy in pcd(4,22,45):shape=shape.cut(cyl(2.5,22,dx,dy,19))
        replace(parts,scene,node_id,shape)
        parts[node_id]['features']+='; P13 integrierter DecksockelØ70/4×M6PCD44, Gewindekern22tief'
        x,y=nodepos.x,nodepos.y
        spacer=standoff.copy()
        for dx,dy in pcd(4,22,45):
            point=(x+dx,y+dy);bolt_points.append(point)
            spacer=spacer.cut(cyl(3.3,32,dx,dy,deck_base-1))
            deck=deck.cut(cyl(3.3,10,*point,deck_z-1))
        tid='P13-DECKSTUETZE'
        if tid not in parts:define(tid,'Deckstütze',spacer,'EN AW-6082 T6','Drehen/Bohren','Ø60/Ø20×30;4×Ø6.6/PCD44')
        put(tid,'Deckstuetze_'+row['name'],shape=spacer.translated(V(x,y,0)))
        mate(row['name'],'Deckstuetze_'+row['name'],'CNC-Decksockel;4×ISO4762-M6×100; durchgehende Druckhülsen im Deckträger')
    for x,y in bolt_points:
        for yy in [-100,100]:
            if abs(y-yy)<30:beam=beam.cut(cyl(3.3,42,x,y-yy,deck_beam_z-1))
    define('P13-DECKTRAEGER','DeckträgerRHS60×40×3',beam,'EN AW-6082 T6','Standard-RHS-Zuschnitt/Bohren','L1000; zugehörige M6-Druckhülsen verhindern Rohrwandquetschung')
    for y in [-100,100]:put('P13-DECKTRAEGER',f'Decktraeger{y}',shape=beam.translated(V(0,y,0)))
    define('P13-DECK','Standdeck',deck,'EN AW-6082 T6','Plattenzuschnitt/CNC; rutschfeste Auflage',
           '1100×320×8; Lochbild über16M6-Schrauben; Kantenschutz und rutschfeste Deckauflage erforderlich')
    put('P13-DECK','Standdeck')
    define('P13-DECK-DRUCKHUELSE','Deckträger-Druckhülse',ring(3.3,5,deck_beam_z+3,34),'EN AW-6082 T6','Drehen','Ø10/Ø6.6×34; Einsetzen vor Endmontage')
    define('STD-SCHEIBE-DECKM6','DeckscheibeM6',ring(3.2,6,deck_z+8,1.6),'Stahl200HV','Kaufen','Ø6.4/12×1.6','ISO7089 M6')
    for i,(x,y) in enumerate(bolt_points):
        put('P13-DECK-DRUCKHUELSE',f'Deckdruckhuelse{i}',shape=parts['P13-DECK-DRUCKHUELSE']['shape'].translated(V(x,y,0)))
        put('STD-SCHEIBE-DECKM6',f'Deckscheibe{i}',shape=parts['STD-SCHEIBE-DECKM6']['shape'].translated(V(x,y,0)))
        screw(6,100,(x,y,deck_z+9.6),(0,0,1),f'Deck_M6_{i}')
    # Skid struts attach to four lower ring nodes, clear of the swept blade radius.
    nodes=[r for r in scene if r['name'].startswith('Ring0_') and r['id'].startswith('CFK-KNOTEN')]
    chosen=[]
    for xs in [-1,1]:
        for ys in [-1,1]:
            target=V(xs*q['post_x'],ys*p['frame_beam_y'],-q['cfk_rim_z'])
            chosen.append(min(nodes,key=lambda r:(r['shape'].Placement.Base-target).Length))
    leg_bottom=-q['beam_z']-2*p['cfk_node_core_r']-31
    skid_z=leg_bottom-22
    for row in chosen:
        nodepos=node_positions[row['name']];x,y=nodepos.x,nodepos.y
        shape=parts[row['id']]['shape'].copy().fuse(cyl(30,25,z=-35)).fuse(cyl(35,6,z=-41))
        for dx,dy in pcd(4,22,45):shape=shape.cut(cyl(2.5,22,dx,dy,-41))
        replace(parts,scene,row['id'],shape)
        top=nodepos.z-41
        leg=ring(13,16,leg_bottom,top-leg_bottom)
        leg=leg.fuse(ring(10,35,top-6,6))
        for dx,dy in pcd(4,22,45):leg=leg.cut(cyl(3.3,8,dx,dy,top-7))
        tid='P13-LANDEBEIN'
        if tid not in parts:define(tid,'Landebein32×26',leg,'EN AW-6082 T6','Rohr32×26; CNC-Flansch; qualifizierte Fügung',
               f'Obere Anlagez{top:g}; Unterkante{leg_bottom:g}; quasistatisches Kufenfahrwerk, kein Crashdämpfer')
        put(tid,'Landebein_'+row['name'],shape=leg.translated(V(x,y,0)))
        for j,(dx,dy) in enumerate(pcd(4,22,45)):
            screw(6,16,(x+dx,y+dy,top-6),(0,0,-1),'Landebein_M6_'+row['name']+str(j))
        # Machined upper/lower skid clamps with a visible split and twoM6 bores.
        full=box(70,40,44,-35,-20,skid_z-22)
        bore=Part.makeCylinder(16.1,42,V(0,-21,skid_z),V(0,1,0));full=full.cut(bore)
        for xx in [-26,26]:full=full.cut(cyl(3.3,46,xx,0,skid_z-23))
        for side in [1]:
            s=box(70,40,21.75,-35,-20,skid_z+.25).cut(bore).removeSplitter()
            tid='P13-KUFENKLEMME-'+str(side)
            if tid not in parts:define(tid,'Kufen-Schweißsattel',s,'EN AW-6082 T6','Fräsen; qualifizierte Aluminium-Schweißbaugruppe',
                 'SattelsitzØ32.2; Spalt0.1 für Fügung; a3-Symbole nach ISO2553; Verfahren nach ENISO15614-2; Schweißnahtprüfung nach ISO10042; keine Klemmhälfte')
            put(tid,'Kufenklemme_'+row['name']+str(side),shape=parts[tid]['shape'].translated(V(x,y,0)))
        mate(row['name'],'Landebein_'+row['name'],'Integrierter CNC-Knotenflansch;4×M6;30mm-Gewinde-/Fügungsnachweis offen')
    skid=Part.makeCylinder(16,600,V(0,-300,skid_z),V(0,1,0)).cut(Part.makeCylinder(13,602,V(0,-301,skid_z),V(0,1,0)))
    define('P13-LANDEKUFE','Landekufe32×26',skid,'EN AW-6082 T6','Rohrzuschnitt; Endkappen; abriebfeste Auflage','L600; zwei getrennte Sattelklemmungen je Kufe')
    for xs in [-1,1]:put('P13-LANDEKUFE',f'Landekufe{xs}',shape=skid.translated(V(xs*q['post_x'],0,0)))
    q['deck_height_mm']=deck_z+8;q['skid_axis_z_mm']=skid_z
    q['mechanical_architecture_status']='GEOMETRISCHER_ENTWURF_MIT_OFFENEN_LIEFERTEIL_UND_NACHWEISDETAILS'
    from abschluss import add as finish
    finish(config,parts,scene,q,define,put,mate,screw)
