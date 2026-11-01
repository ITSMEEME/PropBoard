"""Swashplate phase links, bearing retainers, and the actuator belt drive."""
import math
import FreeCAD as A,Part
from mechanik import V,box,cyl,ring,holes,pcd,axial,rotate
from verbindungen import replace
from gelenke import pin

def add(config,parts,scene,q,define,put,mate,screw):
    p=config['parameters'];m=config['mechanics'];sw=m['swash_z'];z=q['level_z']
    # Axial bearing restraints are separate serviceable parts.
    inner=parts['P13-TAUMEL-INNEN']['shape']
    inner=inner.fuse(ring(45.01,50,sw-22,44))
    inner=inner.fuse(ring(45.01,54.5,sw-9.5,3))
    define('P13-TAUMEL-M100','Dünnring-LagermutterM100',ring(50.05,55,sw+6.5,5),'42CrMo4+QT','Drehen/Gewinde; Stirnlochschlüssel',
           'M100×2 symbolisch; klemmt61820-Innenring gegen integrierte Schulter; Sicherungsschraube und Paarabstimmung vorsehen')
    for side,tag in [(-1,'UNTEN'),(1,'OBEN')]:
        zz=sw-25 if side<0 else sw+22
        cap=holes(ring(35.1,50,zz,3),pcd(6,47,30),3.4,zz-1,5)
        if side<0:
            for aa in [0,120,240]:cap=cap.cut(rotate(box(5,10.2,5,45.5,-5.1,zz-1),aa))
        define('P13-GE-DECKEL-'+tag,'GE60 Außensitzdeckel '+tag,cap,'EN AW-7075 T6','Drehen/Bohren',
               'Äußere axiale Nennkontur; GE60C36/Schultern endgültig anhand Lieferzeichnung abgleichen')
    for a in range(30,360,60):
        x=47*math.cos(math.radians(a));y=47*math.sin(math.radians(a))
        for start in [sw-22,sw+16]:inner=inner.cut(cyl(1.25,6,x,y,start))
    # Stationary scissors attach outside the GE retaining caps.
    anchor=box(4.5,28,43.5,50.5,-14,sw-50)
    anchor=anchor.fuse(box(22,4,20,55,-14,sw-50)).fuse(box(22,4,20,55,10,sw-50))
    anchor=anchor.cut(Part.makeCylinder(3.1,32,V(66,-16,sw-40),V(0,1,0)))
    inner=inner.fuse(rotate(anchor,70))
    replace(parts,scene,'P13-TAUMEL-INNEN',inner)
    # Rotating scissors occupy an azimuth midway between pitch-link joints.
    a_sc=70
    anchor=box(4,28,29,68,-14,sw-35)
    anchor=anchor.fuse(box(22,4,20,72,-14,sw-35)).fuse(box(22,4,20,72,10,sw-35))
    anchor=anchor.cut(Part.makeCylinder(3.1,32,V(83,-16,sw-25),V(0,1,0)))
    rotating=parts['P13-TAUMEL-AUSSEN']['shape'].fuse(rotate(anchor,a_sc))
    rotating=rotating.fuse(ring(60,77.5,sw-9.5,3))
    rotating=rotating.cut(rotate(box(24,20,31,72,-10,sw-36),a_sc))
    rotating=rotating.cut(rotate(Part.makeCylinder(3.3,44,V(83,-22,sw-25),V(0,1,0)),a_sc))
    rotating=rotating.cut(ring(62.51,73,sw+6.5,4))
    for x,y in pcd(8,70):rotating=rotating.cut(cyl(1.25,6,x,y,sw+1.5))
    replace(parts,scene,'P13-TAUMEL-AUSSEN',rotating)
    cap=holes(ring(60,73,sw+6.5,3),pcd(8,70),3.4,sw+5.5,5)
    define('P13-TAUMEL-AUSSENDECKEL','Taumel-Außenringdeckel',cap,'EN AW-7075 T6','Drehen/Bohren',
           '61820 Außenring geklemmt;8×M3; außenR73 hält Abstand zu den Pitchgelenkgabeln')
    replace(parts,scene,'P13-GLEITHUELSE',ring(20.1,30,sw-27,54))
    for start,tag in [(sw-27,'UNTEN'),(sw+22,'OBEN')]:
        define('P13-GE-M60-'+tag,'GleithülsenmutterM60 '+tag,ring(30.05,35,start,5),'42CrMo4+QT','Drehen/Gewinde; Stirnlochschlüssel',
               'M60×1.5 symbolisch; GE60-Innenring axial gehalten; Rundlauf, Freistich und Sicherung festlegen')
    # Move the fixed stops clear of the allowed collective travel.
    replace(parts,scene,'P13-HUBANSCHLAG',ring(20.05,34,sw-38,5).cut(box(40,.5,7,0,-.25,sw-39)))
    define('P13-HUBANSCHLAG-OBEN','Oberer geteilter Hubanschlag',ring(20.05,34,sw+33,5).cut(box(40,.5,7,0,-.25,sw+32)),
           'EN AW-7075 T6','Drehen/Fräsen; geteilte M5-Klemmung','Verstellbarer oberer Anschlag; keine Stellbremse')
    # Link blank, with clevis pin holes along Y.
    s=box(30,8,20,0,-4,-10)
    for x in [0,30]:s=s.fuse(Part.makeCylinder(10,8,V(x,-4,0),V(0,1,0)))
    for x in [0,30]:
        s=s.cut(Part.makeCylinder(5.5,10,V(x,-5,0),V(0,1,0)))
        s=s.cut(Part.makeCylinder(7.01,6.1,V(x,-2,0),V(0,1,0)))
        s=s.cut(Part.makeCylinder(7.5,1.1,V(x,2,0),V(0,1,0)))
    define('P13-SCHERENLASCHEN','Sphärisch gelagerte Scherenlasche30',s,'EN AW-7075 T6','Fräsen/Bohren, kantenrunden',
           'Achsabstand30; Dicke8;2×GE6E6×14×6/C4; integrierte Schulter und DIN472-14-Nut; Schwenkfähigkeit statt verspannter Parallelbolzen')
    ball6=Part.makeSphere(5).common(box(12,6,12,-6,-3,-6)).cut(Part.makeCylinder(3,8,V(0,-4,0),V(0,1,0)))
    race6=Part.makeCylinder(7,4,V(0,-2,0),V(0,1,0)).cut(Part.makeSphere(5.1))
    define('STD-GE6-INNEN','Scheren-GelenklagerGE6 Innenring',ball6,'Kaufteil','Kaufen','d6/D14/B6/C4; angenäherte innere Kugelfläche','ISO12240-1 GE6E Nennmaßfamilie')
    define('STD-GE6-AUSSEN','Scheren-GelenklagerGE6 Außenring',race6,'Kaufteil','Kaufen','D14/C4; Lieferteil-Kippwinkel mindestens2° erforderlich','ISO12240-1 GE6E Nennmaßfamilie')
    clip=Part.makeCylinder(7.4,1,V(0,2,0),V(0,1,0)).cut(Part.makeCylinder(5.5,3,V(0,1,0),V(0,1,0))).cut(box(9,4,1,0,0,-.5))
    define('STD-DIN472-14','Scheren-Innensicherungsring14',clip,'Federstahl','Kaufen','Nennhülle;14mm-Sitz, NutØ15×1.1; konkrete DIN472-Liefermaße abgleichen','DIN472 Maßfamilie14')
    for length in [2,4,6,12]:
        spacer=Part.makeCylinder(4,length,V(),V(0,1,0)).cut(Part.makeCylinder(3.1,length+2,V(0,-1,0),V(0,1,0)))
        define(f'P13-SCHERENDISTANZ-{length}','Scheren-Distanzbuchse'+str(length),spacer,'C45','Drehen/Schleifen',f'Ø8/Ø6.2×{length}; Kontakt nur am Gelenklager-Innenring')
    collar=ring(20.1,28,59,12)
    fork=box(3,28,20,26,-14,55).fuse(box(22,4,20,29,-14,55)).fuse(box(22,4,20,29,10,55))
    collar=collar.fuse(fork).cut(Part.makeCylinder(3.1,32,V(40,-16,65),V(0,1,0)))
    define('P13-SCHERENFESTPUNKT','Scheren-Festpunktschelle',collar,'EN AW-7075 T6','Drehen/Fräsen; geteilte Klemmung',
           'Ø40.2-Sitz; zwei Schellenhälften und M5-Klemmung vor Lieferfreigabe ausarbeiten; fester Drehmomentpfad zur Säule')
    # The rotor scissors attach to an integrated ear on pylon2, below the bearing plane.
    foot=box(6,28,20,121,-14,-70).fuse(box(22,4,20,100,-14,-70)).fuse(box(22,4,20,100,10,-70))
    foot=foot.fuse(box(18,28,4,109,-14,-70))
    foot=foot.cut(Part.makeCylinder(3.1,32,V(110,-16,-60),V(0,1,0)))
    integrated=parts['P13-FACHWERK-PYLON']['shape'].fuse(rotate(foot,25)).fuse(box(10,40,4,105,10,-70))
    integrated=integrated.cut(rotate(Part.makeCylinder(10.2,20,V(110,-10,-60),V(0,1,0)),25))
    define('P13-FACHWERK-PYLON-MITNEHMER','Rotorpylon mit integrierter Scherengabel',integrated,'EN AW-7075 T6','5-Achs-Fräsen/Bohren',
           'Fachwerkpylon2, zusätzliche sphärische Scherenabstützung bei R110/Z120/Phase70; keine überlappenden Unterflansche')
    for sign,label in [(1,'Oben'),(-1,'Unten')]:
        name=label+'_Fachwerk2_Pylon';scene[:]=[r for r in scene if r['name']!=name]
        put('P13-FACHWERK-PYLON-MITNEHMER',name,angle=45,sign=sign,z=z)
    for sign,label in [(1,'Oben'),(-1,'Unten')]:
        for tid in ['P13-TAUMEL-M100','P13-GE-DECKEL-UNTEN','P13-GE-DECKEL-OBEN','P13-TAUMEL-AUSSENDECKEL','P13-GE-M60-UNTEN','P13-GE-M60-OBEN','P13-HUBANSCHLAG-OBEN','P13-SCHERENFESTPUNKT']:
            put(tid,label+'_'+tid,sign=sign)
        for j,(x,y) in enumerate(pcd(8,70)):
            screw(3,8,(x,y,sw+9.5),(0,0,1),label+f'_Taumeldeckel_M3{j}',sign=sign)
        for j,(x,y) in enumerate(pcd(6,47,30)):
            screw(3,8,(x,y,sw+25),(0,0,1),label+f'_GEdeckelO_M3{j}',sign=sign)
            screw(3,8,(x,y,sw-25),(0,0,-1),label+f'_GEdeckelU_M3{j}',sign=sign)
        for name,start,end in [('Stationaer',V(40,0,65),V(66,0,92)),('Rotor',V(83,0,sw-25),V(110,0,120))]:
            d=end-start;L=d.Length
            mid=(start+end)*.5;normal=V(-d.z,0,d.x)/L
            offset=math.sqrt(30**2-(L/2)**2)
            elbow=mid-normal*offset
            for j,(a,b,ys) in enumerate([(start,elbow,[-5]),(elbow,end,[5])]):
                rotation=A.Rotation(V(1,0,0),b-a)
                for yy in ys:
                    s=parts['P13-SCHERENLASCHEN']['shape'].copy();s.Placement=A.Placement(a+V(0,yy,0),rotation).multiply(s.Placement)
                    put('P13-SCHERENLASCHEN',label+f'_{name}Schere{j}_{yy}',shape=s,angle=a_sc,sign=sign)
                    for k,point in enumerate([a,b]):
                        for tid,tag in [('STD-GE6-INNEN','Innenring'),('STD-GE6-AUSSEN','Aussenring'),('STD-DIN472-14','Sicherungsring')]:
                            ss=parts[tid]['shape'].copy();ss.Placement=A.Placement(point+V(0,yy,0),rotation).multiply(ss.Placement)
                            put(tid,label+f'_{name}Schere{j}_{k}_{tag}',shape=ss,angle=a_sc,sign=sign)
            for j,pt in enumerate([start,elbow,end]):
                reverse=name=='Rotor' and j==2;direction=(0,1,0) if reverse else (0,-1,0)
                pin(6,35,tuple(pt+V(0,-15.6 if reverse else 15.6,0)),direction,label+f'_{name}Scherenpin{j}',a_sc,sign,define,put,parts)
                intervals=[(-10,2),(-2,12)] if j==0 else ([(-10,12),(8,2)] if j==2 else [(-14,6),(-2,4),(8,6)])
                for k,(begin,length) in enumerate(intervals):
                    tid=f'P13-SCHERENDISTANZ-{length}';put(tid,label+f'_{name}Scherenpin{j}_Distanz{k}',shape=parts[tid]['shape'].translated(pt+V(0,begin,0)),angle=a_sc,sign=sign)
            mate(label+'_Taumeltraeger' if name=='Stationaer' else label+'_Taumelring',label+'_Mittelstuetze_Rohr' if name=='Stationaer' else label+'_Innenring',
                 'Sphärisch gelagerte30mm-Scherenlaschen;GE6E; DIN1444B6×35; ISO1234-Splinte und Innenringdistanzen; Phasenhaltung bei Hub/Kippung')
    # Brace clevises use positive retained pins, not friction-only clamping.
    for sign,label in [(1,'Oben'),(-1,'Unten')]:
        for i in range(int(p['blade_count'])):
            for side in [-1,1]:
                pin(8,30,(125,side*14,-126.6),(0,0,1),label+f'_Fachwerk{i+1}_Innenpin{side}',360*i/p['blade_count'],sign,define,put,parts,z)
                pin(8,30,(719,side*14,-78.4),(0,0,-1),label+f'_Blatt{i+1}_Aussenpin{side}',m['blade_phase']+360*i/p['blade_count'],sign,define,put,parts,z)
    from fahrwerk import add as vehicle
    vehicle(config,parts,scene,q,define,put,mate,screw)
