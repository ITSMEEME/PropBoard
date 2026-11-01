"""Manufacturable split clamps, link spacers, and final locking interfaces."""
import math
import FreeCAD as A,Part
from spiegeln import reflected, X, Y, Z
from mechanik import V,box,cyl,ring,axial,annulus_x,pcd,rotate
from verbindungen import replace

def add(config,parts,scene,q,define,put,mate,screw):
    p=config['parameters'];m=config['mechanics'];sw=m['swash_z'];z=q['level_z']
    # The column clamps are actually split into two separately machinable bodies.
    for id,centre,xbolts,angle in [('P13-SCHERENFESTPUNKT',65,24,70),('P13-HUBANSCHLAG',sw-38.5,28,0),('P13-HUBANSCHLAG-OBEN',sw+35.5,28,0)]:
        body=parts[id]['shape'].copy()
        if id=='P13-HUBANSCHLAG':body=ring(20.05,34,sw-41,5)
        locations=[(-24,59),(-24,71)] if id=='P13-SCHERENFESTPUNKT' else [(-xbolts,centre),(xbolts,centre)]
        for xx,zz in locations:body=body.fuse(box(12,36,12,xx-6,-18,zz-6))
        body=body.cut(cyl(20.1,90,z=centre-45))
        a=body.common(box(160,80,90,-80,-80.25,centre-45))
        b=body.common(box(160,80,90,-80,.25,centre-45))
        for xx,zz in locations:
            a=a.cut(Part.makeCylinder(2.1,40,V(xx,-20,zz),V(0,1,0)))
            b=b.cut(Part.makeCylinder(2.75,40,V(xx,-20,zz),V(0,1,0)))
            b=b.cut(Part.makeCylinder(4.5,8,V(xx,18,zz),V(0,1,0)))
        # Replace old instances before adding their positive-Y counterparts.
        replace(parts,scene,id,a)
        parts[id]['features']+='; getrennte SchellenhälfteA;2×M5-Kernloch; keine ungeteilte Ringschelle'
        define(id+'-B',parts[id]['name']+' HälfteB',b,'EN AW-7075 T6','Fräsen/Bohren','Trennfuge0.5;2×Ø5.5; M5×30-Queranzug')
        for sign,label in [(1,'Oben'),(-1,'Unten')]:
            # Existing fixed-point instances were initially placed before the scissor azimuth was chosen.
            if id=='P13-SCHERENFESTPUNKT':
                row=next(r for r in scene if r['name']==label+'_'+id)
                s=rotate(a,angle)
                if sign<0:s=reflected(s,Z)
                row.update(shape=s,manufacturing_shape=a.copy())
            put(id+'-B',label+'_'+id+'_B',angle=angle,sign=sign)
            for j,(xx,zz) in enumerate(locations):screw(5,30,(xx,18,zz),(0,1,0),label+'_'+id+f'_M5{j}',angle,sign)
    # These spacers load only the joint balls, leaving the outer head free to swivel.
    define('P13-GELENKDISTANZ8-L3','Fachwerk-GelenkdistanzØ12/8.2×3',ring(4.1,6,0,3),
           '42CrMo4+QT','Drehen/Schleifen','3mm Innenringdistanz zwischen8mm-Gelenkkugel und14mm-Gabelspalt; Kontakt nur an Kugelplanfläche')
    for sign,label in [(1,'Oben'),(-1,'Unten')]:
        for i in range(int(p['blade_count'])):
            for side in [-1,1]:
                for zz in [-122,-111]:
                    put('P13-GELENKDISTANZ8-L3',label+f'_Fachwerk{i+1}_InnenDistanz{side}_{zz}',shape=parts['P13-GELENKDISTANZ8-L3']['shape'].translated(V(125,side*14,zz)),angle=360*i/p['blade_count'],sign=sign,z=z)
                for zz in [-97,-86]:
                    put('P13-GELENKDISTANZ8-L3',label+f'_Blatt{i+1}_AussenDistanz{side}_{zz}',shape=parts['P13-GELENKDISTANZ8-L3']['shape'].translated(V(719,side*14,zz)),angle=m['blade_phase']+360*i/p['blade_count'],sign=sign,z=z)
    for L in [1,2,3]:
        define(f'P13-GELENKDISTANZ6-L{L}',f'GelenkdistanzØ8/6.2×{L}',annulus_x(3.1,4,0,L),
               '42CrMo4+QT','Drehen/Schleifen','Ballkontaktfläche; Gehäuse bleibt winkelbeweglich; reale Gelenkkugelbreite vor Bestellung prüfen')
    for sign,label in [(1,'Oben'),(-1,'Unten')]:
        for j,a in enumerate([0,120,240]):
            pre=label+f'_Aktor{j+1}'
            for xx,L,tag in [(76,2,'Innen'),(86,1,'Aussen')]:
                s=parts[f'P13-GELENKDISTANZ6-L{L}']['shape'].translated(V(xx,22,100))
                put(f'P13-GELENKDISTANZ6-L{L}',pre+'_GelenkDistanz'+tag,shape=s,angle=a,sign=sign)
            for xx,axis,tag in [(91,V(1,0,0),'Aussen'),(72,V(-1,0,0),'Innen')]:
                s=parts['STD-SCHEIBE-M6']['shape'].copy();s.Placement=A.Placement(V(xx,22,100),A.Rotation(V(0,0,1),axis)).multiply(s.Placement)
                put('STD-SCHEIBE-M6',pre+'_Gelenkscheibe'+tag,shape=s,angle=a,sign=sign)
            s=parts['STD-MUTTER-M6']['shape'].copy();s.Placement=A.Placement(V(70.4,22,100),A.Rotation(V(0,0,1),V(-1,0,0))).multiply(s.Placement)
            put('STD-MUTTER-M6',pre+'_Gelenkmutter',shape=s,angle=a,sign=sign)
            screw(6,30,(92.6,22,100),(1,0,0),pre+'_Gelenkbolzen_M6',a,sign)
        for i in range(int(p['blade_count'])):
            a=m['blade_phase']+i*360/p['blade_count'];pre=label+f'_Blatt{i+1}'
            phi=p['pitch_neutral'];delta=math.degrees(math.atan2(25*math.cos(math.radians(phi)),m['pitch_lever_x']))
            s=parts['P13-GELENKDISTANZ6-L3']['shape'].translated(V(75,25,0));s.rotate(V(),V(1,0,0),phi)
            put('P13-GELENKDISTANZ6-L3',pre+'_PitchpinDistanz',shape=s,angle=a,sign=sign,z=z)
            s=parts['P13-GELENKDISTANZ6-L3']['shape'].translated(V(86,25,0));s.rotate(V(),V(1,0,0),phi)
            put('P13-GELENKDISTANZ6-L3',pre+'_PitchpinDistanzAussen',shape=s,angle=a,sign=sign,z=z)
            for pos,tag in [(-7,'Innen'),(4,'Aussen')]:
                s=parts['P13-GELENKDISTANZ6-L3']['shape'].copy();s.rotate(V(),V(0,0,1),90);s.translate(V(90,pos,sw))
                put('P13-GELENKDISTANZ6-L3',pre+'_TaumelpinDistanz'+tag,shape=s,angle=a+delta,sign=sign)
            from gelenke import pin
            pin(6,30,(90,12.6,sw),(0,-1,0),pre+'_Taumelpin',a+delta,sign,define,put,parts,span_override=22)
    # Replace the earlier arbitrary M14 nut envelope with a fine-thread norm family
    # and a positive two-tab locking plate hooked around the fork's rear edge.
    old_id='REF-ACHS-MUTTER-M14'
    if old_id in parts:
        pts=[V(22/math.sqrt(3)*math.cos(math.radians(30+60*i)),22/math.sqrt(3)*math.sin(math.radians(30+60*i)),0) for i in range(6)]
        nut=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,12)).cut(cyl(7.05,14,z=-1))
        replace(parts,scene,old_id,nut)
        parts[old_id].update(name='SechskantmutterM14×1.5',standard='ISO8673 M14×1.5 Nennmaßfamilie',material='StahlKlasse8',features='M14×1.5/SW22/H12; Zunge am+X-Sechskantflach angelegt')
        lock=ring(7.6,14,0,1).fuse(box(9,6,1,-21,-3,0))
        lock=lock.fuse(box(1,6,2,-21,-3,-2)).fuse(box(1,6,12,11,-3,1))
        define('P13-ACHS-SICHERUNGSBLECH','Rollenachsen-Sicherungsblech',lock,'DC01,1mm','Laserschneiden/Biegen',
               'Eigenkonstruktion nach Prinzip Sicherungsblech: eine Zunge um Gabelrückkante-20, eine am Mutterflach; keine erneute Verwendung nach Aufbiegen')
        for sign,label in [(1,'Oben'),(-1,'Unten')]:
            for i,a in enumerate(q['guide_angles']):
                row=next(r for r in scene if r['name']==label+f'_Rolle_{i+1}_Achse_Achsmutter')
                row['shape'].translate(V(0,0,sign))
                put('P13-ACHS-SICHERUNGSBLECH',label+f'_Rolle{i+1}_Sicherungsblech',shape=parts['P13-ACHS-SICHERUNGSBLECH']['shape'].translated(V(q['roller_center'],0,q['axle_half_length'])),angle=a,sign=sign,z=q['level_z'])
        parts['P12-018']['features']+='; M14×1.5; Sicherungsblech und ISO8673-Mutter'
    # All datum dimensions of the supplied motor drawing are retained independently
    # of the deliberately assumed thread engagements.
    q['motor_connection_status']='LOCHBILDER_AUS_NUTZERZEICHNUNG_UMGESETZT_GEWINDEEINGRIFF_MONTAGEANNAHME'
    q['industrial_standard_policy']='Normmaßfamilie in Stückliste; keine erfundene Lieferantenzertifizierung; Sonderteile als RFQ gekennzeichnet'
    from gimbal import add as articulated_actuators
    articulated_actuators(config,parts,scene,q,define,put,mate,screw)
