"""Triangulated rotor load path, separate from the pitchable CFK blade shells."""
import math
import FreeCAD as A,Part
from mechanik import V,box,cyl,ring,axial,rotate
from verbindungen import replace

def add(config,parts,scene,q,define,put,mate,screw):
    p=config['parameters'];m=config['mechanics'];z=q['level_z']
    # A single unbraced20mm spoke is not represented as a proven bending beam.
    # Two30x26 axial braces meet each outer bearing carrier, forming a deep V-truss.
    pylon=box(6,56,93,105,-28,-125)
    pylon=pylon.fuse(box(40,50,6,105,-25,-38))
    for zz in [-125,-108]:pylon=pylon.fuse(box(34,56,3,111,-28,zz))
    for yy in [-14,14]:pylon=pylon.cut(cyl(4.2,24,125,yy,-127))
    for xx in [120,135]:
        for yy in [-16,16]:pylon=pylon.cut(cyl(3.3,8,xx,yy,-39))
    pylon=pylon.cut(cyl(3.3,8,125,0,-39))
    define('P13-FACHWERK-PYLON','Rotorfachwerk-Pylon',pylon,'EN AW-7075 T6','5-Achs-Fräsen/Bohren',
           '4×M6 am Innenring; zweiØ8-Gabelbolzen; untere Knoten65mm über Mittelebene; Funktionsflächen spanend')
    carrier=parts['P13-INNENRING']['shape'].copy()
    for i in range(int(p['blade_count'])):
        a=i*360/p['blade_count']
        for xx in [120,135]:
            for yy in [-16,16]:carrier=carrier.cut(rotate(cyl(2.5,12,xx,yy,-33),a))
    replace(parts,scene,'P13-INNENRING',carrier)
    out=parts['P13-AUSSENLAGERTRAEGER']['shape'].copy()
    for zz in [-100,-83]:out=out.fuse(box(30,56,3,703,-28,zz))
    out=out.fuse(box(8,56,36,733,-28,-100)).fuse(box(22,40,6,719,-20,-70))
    for yy in [-14,14]:out=out.cut(cyl(4.2,24,719,yy,-102))
    out=out.common(cyl(744,200,z=-150))
    replace(parts,scene,'P13-AUSSENLAGERTRAEGER',out)
    # Spherical brace ends are a specified M8 standard family with a custom adapter.
    head=cyl(12,8,z=-4).cut(Part.makeSphere(8.1)).cut(cyl(6,12,z=-6))
    head=head.fuse(Part.makeCylinder(4,50,V(10,0,0),V(1,0,0)))
    define('STD-M8-ZUGSTANGENKOPF','ZugstangenkopfM8/Ø8',head,'Kaufteil','Kaufen',
           'M8RH/LH;Ø8-Bolzen;Ø24×8 Einbauhülle; mindestens±10°; reale Norm-/Liefermaße abgleichen',
           'ISO12240-4 / DIN648 Familie; Hüllmaße eigene RFQ-Vorgabe')
    ball=Part.makeSphere(8).common(box(20,20,8,-10,-10,-4)).cut(cyl(4,12,z=-6))
    define('STD-M8-GELENKKUGEL','GelenkkugelØ8',ball,'Kaufteil','Kaufen',
           'Ø8-Gabelbolzen; Kugel und Kopf sind getrennte Körper, so bleibt der Bolzen bei geneigtem Kopf ausgerichtet',
           'ISO12240-4 / DIN648 Familie; Nennkontur')
    insert=Part.makeCylinder(12.8,40,V(30,0,0),V(1,0,0)).cut(Part.makeCylinder(4.1,42,V(29,0,0),V(1,0,0)))
    define('P13-FACHWERK-INSERT','CFK30-Endeinsatz',insert,'TitanGrade5 oder isoliertes Aluminium','Drehen/Gewinde; qualifizierte Klebung',
           'Ø25.6/Ø8.2×40;0.2mm Klebefuge imØ26-Rohr; GewindezugangM8, Sicherung vor Bestellung abstimmen')
    cuts=[]
    for sign,label in [(1,'Oben'),(-1,'Unten')]:
        for i in range(int(p['blade_count'])):
            a=i*360/p['blade_count'];pre=label+f'_Fachwerk{i+1}'
            put('P13-FACHWERK-PYLON',pre+'_Pylon',angle=a,sign=sign,z=z)
            for xx in [120,135]:
                for yy in [-16,16]:screw(6,16,(xx,yy,-38),(0,0,-1),pre+f'_M6{xx}_{yy}',a,sign,z)
            for side in [-1,1]:
                start=V(125,side*14,-115)
                target=V(719,-side*14,-90)
                az=a+side*m['blade_phase']
                # target is in the neighboring blade's radial frame.
                target=rotate_point(target,side*m['blade_phase'])
                d=target-start;L=d.Length;u=d/L
                length=L-60
                id=f'P13-CFK30-STREBE-{i}-{side}'
                tube=Part.makeCylinder(15,length,start+u*30,u).cut(Part.makeCylinder(13,length+2,start+u*29,u))
                define(id,'CFK-Fachwerkstrebe30×26',tube,'CFK30×26 mit Lieferanten-Druck-/Knicknachweis',
                       'Rohr ablängen; Enden versiegeln; isolierte Einsätze einkleben',
                       f'L{length:.3f}; zwei40mm Einbettungen; kein durchbohrtes CFK; Hebelarm und Knickung im Lastscreen')
                put(id,pre+f'_Strebe{side}',angle=a,sign=sign,z=z)
                cuts.append(dict(instance=pre+f'_Strebe{side}',length_mm=length,od_mm=30,id_mm=26,quantity=1))
                for point,direction,tag in [(start,u,'Innen'),(target,-u,'Aussen')]:
                    r=A.Rotation(V(1,0,0),direction)
                    for tid,suffix in [('STD-M8-ZUGSTANGENKOPF','Kopf'),('P13-FACHWERK-INSERT','Insert')]:
                        s=parts[tid]['shape'].copy();s.Placement=A.Placement(point,r).multiply(s.Placement)
                        put(tid,pre+f'_{side}{tag}{suffix}',shape=s,angle=a,sign=sign,z=z)
                    put('STD-M8-GELENKKUGEL',pre+f'_{side}{tag}Kugel',shape=parts['STD-M8-GELENKKUGEL']['shape'].translated(point),angle=a,sign=sign,z=z)
                mate(pre+'_Pylon',pre+f'_Strebe{side}','M8-Gelenkkopf;Ø8-Gabelbolzen;30×26-CFK-Druck/Zugstrebe')
                outer_index=(i if side>0 else (i-1)%int(p['blade_count']))+1
                mate(pre+f'_Strebe{side}',label+f'_Blatt{outer_index}_Aussenlagertraeger','M8-Gelenkkopf; isolierter40mm-Klebeinsert; V-Fachwerk')
        mate(label+'_Innenring',label+'_Aussenring','8 V-Fachwerkfelder; je2CFK30×26-Streben; ursprüngliche20×17-Speichen bleiben Lage-/Torsionsverbindung')
    q['additional_cfk_cuts']=cuts
    from scheren import add as swash_drive
    swash_drive(config,parts,scene,q,define,put,mate,screw)

def rotate_point(p,a):
    return A.Rotation(V(0,0,1),a).multVec(p)
