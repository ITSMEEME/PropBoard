"""Articulated actuator bases; no rigid vertical-actuator/swashplate overconstraint."""
import math
import FreeCAD as A,Part
from spiegeln import reflected, X, Y, Z
from mechanik import V,box,cyl,ring,holes,pcd,rotate
from verbindungen import replace

def add(config,parts,scene,q,define,put,mate,screw):
    m=config['mechanics']
    # Machined access windows for the articulated feet through the central RHS.
    beam=parts['P12-012']['shape'].copy()
    for a in [0,120,240]:
        for zz in [-31,22]:beam=beam.cut(rotate(cyl(26.5,9,82,0,zz),a))
    replace(parts,scene,'P12-012',beam)
    parts['P12-012']['features']+='; CNC-Freistellungen Ø53 für GE20-Füße; lokale Festigkeit nachzuweisen'
    ep=parts['CFK-BRUECKE-END']['shape'].copy()
    for zz in [-41,31]:ep=ep.cut(box(10,44,10,-1,-22,zz))
    replace(parts,scene,'CFK-BRUECKE-END',ep)
    parts['CFK-BRUECKE-END']['features']+='; obere/untere Freistellung für schwenkbaren Servoträger'
    scene[:]=[r for r in scene if '_FlanschM4' not in r['name']]
    # GE20ES nominal internal surfaces are approximate, outside dimensions follow the family.
    ball=Part.makeSphere(15,V(0,0,30)).common(box(40,40,16,-20,-20,22)).cut(cyl(10,20,z=20))
    outer=cyl(17.5,12,z=24).cut(Part.makeSphere(15.1,V(0,0,30)))
    define('STD-GE20-INNEN','Aktor-Gelenklager GE20 Innenring',ball,'Kaufteil','Kaufen',
           'GE20ES20×35×16,C12; angenäherte innere Kugelfläche; Innen-/Außenkörper getrennt für Freigangprüfung',
           'ISO12240-1 MaßfamilieGE20ES; innere Kontur nicht Hersteller-CAD')
    define('STD-GE20-AUSSEN','Aktor-Gelenklager GE20 Außenring',outer,'Kaufteil','Kaufen',
           'GE20ES,D35,C12; schwenkbarer Fußpunkt(82,0,30)','ISO12240-1 MaßfamilieGE20ES; innere Kontur Nennmodell')
    case=parts['P13-AKTUATORGEHAEUSE']['shape'].copy()
    case=case.fuse(ring(7,10,19,21)).fuse(ring(10,14,38,2))
    case=case.cut(Part.makeCylinder(2.01,22,V(0,13,43),V(0,1,0)))
    case=case.cut(box(35,24,8,0,-12,42))
    replace(parts,scene,'P13-AKTUATORGEHAEUSE',case)
    parts['P13-AKTUATORGEHAEUSE']['features']+='; GE20-KardanfußØ20/M20×1; VerdrehsicherungsstiftØ4×25; Motorträger schwenkt mit'
    define('P13-AKTOR-M20','Aktorfuß-NutmutterM20×1',ring(10.05,14,19,3),'42CrMo4+QT','Drehen/Gewinde, Sicherungslasche',
           'SondermutterØ28×3 mit M20×1, keine KM4-Normmutter; GE20-Innenring axial geklemmt; Sicherungslasche zu montieren')
    # A dowel in a vertical guide slot holds yaw, while allowing the two small swing angles.
    pin=Part.makeCylinder(2,25,V(0,14,43),V(0,1,0))
    groove=Part.makeCylinder(2.1,.5,V(0,37.5,43),V(0,1,0)).cut(Part.makeCylinder(1.6,.7,V(0,37.4,43),V(0,1,0)))
    pin=pin.cut(groove)
    define('STD-DIN6325-4x25','Verdrehsicherungsstift4×25',pin,'Gehärteter Stahl','Kaufen; Ringnut als Sonderbearbeitung',
           'Ø4m6×25, Gehäusebohrung nach H7; CAD-Montagespiel0.02; äußere Ringnut separat bemaßt','DIN6325 Maßfamilie, Ringnut Sonderbearbeitung')
    for side,tag in [(1,'OBEN'),(-1,'UNTEN')]:
        zz=36 if side>0 else 22
        cap=holes(ring(14.5,25,zz,2),pcd(4,19.5,45),3.4,zz-1,4)
        for x,y in pcd(4,19.5,45):
            cut=Part.makeCone(1.7,3.1,1.8,V(x,y,36.2)) if side>0 else Part.makeCone(3.1,1.7,1.8,V(x,y,22))
            cap=cap.cut(cut)
        define('P13-GE20-DECKEL-'+tag,'Aktorfuß-Lagerdeckel '+tag,cap,'EN AW-7075 T6','Drehen, Bohren,90°-Senken',
               'GE20-Außenring zwischen zwei2mm-Deckeln;4×M3PCD39; ISO10642-M3×6 bündig')
    # Reconstruct stationary plates without the formerly integral motor arms.
    for sign,label,R in [(1,'Oben',277),(-1,'Unten',322)]:
        foot=parts['P13-ZENTRALPLATTE']['shape'].copy()
        foot=foot.fuse(ring(110,114,30,10))
        for a in [0,120,240]:
            holder=ring(17.51,25,24,12).translated(V(82,0,0))
            foot=foot.fuse(rotate(holder,a))
            foot=foot.cut(rotate(cyl(17.51,20,82,0,21),a)).cut(rotate(cyl(28.5,5,82,0,36),a))
            guide=box(12,4,10,76,29,38).cut(box(4.4,6,12,79.8,28,37))
            foot=foot.fuse(rotate(guide,a))
            for x,y in pcd(4,19.5,45):foot=foot.cut(rotate(cyl(1.25,12,82+x,y,24),a))
        id='P13-ZENTRALPLATTE-'+label.upper()
        replace(parts,scene,id,foot)
        parts[id]['features']='Ø228×10; drei GE20ES-Kardansitze,Ø35H7; bündige Lagerdeckel; vertikale4.4mm-Stiftführungen; mittleres90×64-M6-Lochbild'
        # A bolted moving motor bracket clears the static bearing caps and foot plate.
        rel=R-82
        arm=box(rel-34,40,8,34,-20,32).fuse(cyl(25,8,rel,0,32)).cut(cyl(3,12,rel,0,30))
        for yy in [-20,12]:
            contour=[(34,32),(40,32),(40,40),(28,52),(22,52),(34,40)]
            points=[V(x,yy,zz) for x,zz in contour]
            knee=Part.Face(Part.makePolygon(points+[points[0]])).extrude(V(0,8,0))
            arm=arm.fuse(box(22,8,6,4,yy,46)).fuse(knee)
        arm=arm.cut(cyl(18.2,30,z=30))
        arm=arm.cut(box(22,22,8,-11,-35,45))
        for yy in [-16,16]:arm=arm.cut(cyl(2.2,8,16,yy,45))
        for x,y in pcd(4,15,45):
            arm=arm.cut(cyl(1.7,12,rel+x,y,30)).cut(cyl(2.9,3,rel+x,y,38.8))
        aid='P13-AKTOR-MOTORTRAEGER-'+label.upper()
        define(aid,'Schwenkbarer Aktor-Motorträger '+label,arm,'EN AW-6082 T6','5-Achs-Fräsen',
               f'Achsabstand{rel}mm; starre gemeinsame Riemenebene;2×M4 zur Aktorflanschplatte;4×M3PCD30 am Servo')
        for i,a in enumerate([0,120,240]):
            pre=label+f'_Aktor{i+1}'
            for tid,tag in [('STD-GE20-INNEN','KardanInnen'),('STD-GE20-AUSSEN','KardanAussen'),('P13-AKTOR-M20','KardanMutter'),('STD-DIN6325-4x25','Verdrehstift'),('P13-GE20-DECKEL-OBEN','KardandeckelO'),('P13-GE20-DECKEL-UNTEN','KardandeckelU'),(aid,'Motortraeger')]:
                put(tid,pre+'_'+tag,shape=parts[tid]['shape'].translated(V(82,0,0)),angle=a,sign=sign)
            for yy in [-16,16]:screw(4,12,(98,yy,52),(0,0,1),pre+f'_MotortraegerM4{yy}',a,sign)
            for j,(x,y) in enumerate(pcd(4,19.5,45)):
                for side,seat in [(1,38),(-1,22)]:
                    tid='STD-ISO10642-M3x6'
                    if tid not in parts:
                        sh=Part.makeCone(3,1.5,1.7).fuse(cyl(1.2,4.3,z=1.7))
                        define(tid,'SenkschraubeM3×6',sh,'Stahl8.8','Kaufen','M3×6, KopfØ6×1.7; GewindekernØ2.4; Antrieb nicht ausmodelliert','ISO10642 Nennmaßfamilie')
                    s=parts[tid]['shape'].copy();s.Placement=A.Placement(V(82+x,y,seat),A.Rotation(V(0,0,1),V(0,0,-side))).multiply(s.Placement)
                    put(tid,pre+f'_KardandeckelM3_{side}_{j}',shape=s,angle=a,sign=sign)
            mate(label+'_Zentralplatte',pre+'_Gehaeuse','GE20ES-Gelenkfuß;Ø4-Verdrehsicherungsstift im4.4mm-Schwenkschlitz; gesamter Riemenantrieb schwenkt mit')
    q['actuator_mounting']='GE20ES Kardanfuss, Aktor+Servo+Riemen schwenken gemeinsam; keine starre vertikale Überbestimmung'
    # A split geometric GE60 envelope makes its correct inner/outer kinematics explicit.
    ball60=Part.makeSphere(40,V(0,0,m['swash_z'])).common(box(100,100,44,-50,-50,m['swash_z']-22)).cut(cyl(30,48,z=m['swash_z']-24))
    outer60=cyl(45,36,z=m['swash_z']-18).cut(Part.makeSphere(40.1,V(0,0,m['swash_z'])))
    define('STD-GE60-INNEN','Taumel-Gelenklager GE60 Innenring',ball60,'Kaufteil','Kaufen','d60/D90/B44/C36; innere Kugelfläche angenähert','ISO12240-1 GE60ES Nennmaßfamilie')
    define('STD-GE60-AUSSEN','Taumel-Gelenklager GE60 Außenring',outer60,'Kaufteil','Kaufen','D90/C36; innere Kugelfläche angenähert','ISO12240-1 GE60ES Nennmaßfamilie')
    define('P13-GE60-AUSSENDISTANZ','GE60-Außenringdistanz',ring(36,45,0,4),'42CrMo4+QT','Drehen/Schleifen','C36 auf44mm Gehäuse-Axialanschlag abgestimmt; tatsächliche Schultergeometrie nach Lieferteil')
    for sign,label in [(1,'Oben'),(-1,'Unten')]:
        row=next(r for r in scene if r['name']==label+'_Gelenklager')
        s=reflected(outer60,Z) if sign<0 else outer60.copy()
        row.update(id='STD-GE60-AUSSEN',shape=s,manufacturing_shape=s.copy())
        put('STD-GE60-INNEN',label+'_GelenklagerInnen',sign=sign)
        for zz,tag in [(m['swash_z']-22,'Unten'),(m['swash_z']+18,'Oben')]:
            put('P13-GE60-AUSSENDISTANZ',label+'_GE60Distanz'+tag,shape=parts['P13-GE60-AUSSENDISTANZ']['shape'].translated(V(0,0,zz)),sign=sign)
