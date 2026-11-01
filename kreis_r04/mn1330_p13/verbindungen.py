"""Complete explicit fastening stacks and motor interfaces transcribed from user drawing."""
import math
import FreeCAD as A,Part
from spiegeln import reflected, X, Y, Z
from mechanik import V,box,cyl,ring,holes,pcd,axial,annulus_x,rotate

def replace(parts,scene,id,nominal):
    nominal=nominal.removeSplitter()
    if nominal.Volume<0:nominal.reverse()
    if not nominal.isValid() or len(nominal.Solids)!=1 or nominal.Volume<=0:
        raise ValueError(f'{id}: Ersatzkörper ungültig, {len(nominal.Solids)} solids, V={nominal.Volume}')
    old=parts[id]['shape'];parts[id]['shape']=nominal
    for row in scene:
        if row['id']!=id:continue
        if 'pose' in row:
            pose=row['pose'];local=nominal.copy()
            if pose.get('mirror_x'):local=reflected(local,X)
            local.Placement=pose['local'].multiply(local.Placement)
            s=local.copy();s.rotate(V(),V(0,0,1),pose['angle']);s.translate(V(0,0,pose['z']))
            if pose['sign']<0:s=reflected(s,Z)
            row['shape']=s
            row['manufacturing_shape']=reflected(local,Z) if pose['sign']<0 else local.copy()
            continue
        transform=row['shape'].Placement.multiply(row['manufacturing_shape'].Placement.inverse())
        local=reflected(nominal,Z) if row['variant']=='MZ' else nominal.copy()
        row['manufacturing_shape']=local.copy();row['shape']=local
        row['shape'].Placement=transform.multiply(local.Placement)

def add(config,parts,scene,q,define,put,mate,screw):
    p=config['parameters'];m=config['mechanics']
    def washer(d,seat,axis,name,angle=0,sign=1,pitch=0,z=0):
        inner,outer,t={4:(2.15,6,1),6:(3.2,6,1.6)}[d]
        id=f'STD-SCHEIBE-M{d}'
        if id not in parts:define(id,f'ScheibeM{d}',ring(inner,outer,0,t),'Stahl200HV','Kaufen',
           f'Ø{2*inner:g}/Ø{2*outer:g}×{t:g}', 'ISO7093-1 M4' if d==4 else 'ISO7089 M6')
        s=parts[id]['shape'].copy();s.Placement=A.Placement(V(*seat),A.Rotation(V(0,0,1),V(*axis))).multiply(s.Placement)
        if pitch:s.rotate(V(),V(1,0,0),pitch)
        return put(id,name,shape=s,angle=angle,sign=sign,z=z)
    def nut6(seat,axis,name,angle=0,sign=1,pitch=0,z=0):
        id='STD-MUTTER-M6'
        if id not in parts:
            pts=[V(10/math.sqrt(3)*math.cos(i*math.pi/3),10/math.sqrt(3)*math.sin(i*math.pi/3),0) for i in range(6)]
            s=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,5.2)).cut(cyl(3.05,8,z=-1))
            define(id,'SechskantmutterM6',s,'StahlKlasse8','Kaufen','M6/SW10;H5.2; Nennhülle ohne Gewindeflanken; Sicherung gemäß Montageplan',
                   'ISO4032 M6; Sicherungsvariante vor Bestellung festlegen')
        s=parts[id]['shape'].copy();s.Placement=A.Placement(V(*seat),A.Rotation(V(0,0,1),V(*axis))).multiply(s.Placement)
        if pitch:s.rotate(V(),V(1,0,0),pitch)
        return put(id,name,shape=s,angle=angle,sign=sign,z=z)
    motor=cyl(p['motor_diameter']/2,p['motor_length'])
    motor=holes(motor,pcd(4,25,0),5,p['motor_length']-m['motor_stator_engagement_assumed'],m['motor_stator_engagement_assumed']+1)
    motor=holes(motor,pcd(12,20,0),4.2,-1,m['motor_rotor_engagement_assumed']+1)
    motor=holes(motor,pcd(4,35,0),2.5,p['motor_length']-4,5)
    replace(parts,scene,'REF-MN1330',motor)
    parts['REF-MN1330'].update(features='NutzerzeichnungØ150×66;4×M6/PCD50;12×M5/PCD40;4×M3/PCD70; Blindlochtiefen nur Montageannahmen',
        source='Vom Nutzer gelieferte technische Zeichnung,01.11.2026',open='Endgültige Gewindetiefen, Zentrier-/Auflageflächen und elektrische Anschlussdetails vor Bestellung bestätigen')
    # Bushings reconcile the existing Ø8.4 frame bores with M4 core holes in the CFK nodes.
    for L in [8,12]:
        define(f'P13-BUCHSE8-M4-L{L}',f'Zentrierbuchse8.3/4.5×{L}',ring(2.25,4.15,0,L),'EN AW-6082 T6','Drehen',
               'Passung zur vorhandenenØ8.4-Durchgangsbohrung; kein Ersatz für Schraubenvorspannung')
    define('P13-WURZEL-ENDSCHEIBE','Flügelwellen-Endscheibe',annulus_x(2.75,10,200,3),'42CrMo4+QT','Drehen/Schleifen',
           'Axialer Fliehkraftanschlag am Wurzeleinsatz;M5-Endschraube; Kontaktfläche am Einsatz x200')
    define('P13-HEBEL-ENDSCHEIBE','Pitchhebel-Endscheibe',annulus_x(2.2,10,64,4),'42CrMo4+QT','Drehen',
           'M4-Endschraube; abnehmbarer formschlüssiger D-Flach-Hebel')
    define('P13-HEBEL-DISTANZ','Pitchhebel-Axialdistanz',annulus_x(6.05,9,75,27),'42CrMo4+QT','Drehen/Schleifen',
           'Abstimmung gegen KM1; Endschraube darf Lagerpaarvorspannung nicht verändern')
    define('P13-HEBEL-ANLAUF','Pitchhebel-Anlauf',annulus_x(6.05,10,68,1),'42CrMo4+QT','Drehen/Schleifen','Axiale Anlaufscheibe1mm')
    # Counterbore the CFK root block for the positive axial end retention.
    # Positive outer-journal retaining clips, with matching shaft grooves.
    clip=annulus_x(3.8,5,0,.8).cut(box(2,6,2,-.5,0,-1))
    define('STD-DIN471-8','Sicherungsring8',clip,'Federstahl','Kaufen',
           'Nennhülle8mm; Nutbreite0.8, NutgrundØ7.5 vor Bestellung mit realem Ring abgleichen','DIN471 Maßfamilie8')
    # Clear the front of the outer bearing carrier for the shaft end and clips.
    replace(parts,scene,'P13-AUSSENLAGERTRAEGER',parts['P13-AUSSENLAGERTRAEGER']['shape'].cut(axial(6,32,715)))
    for sign,label in [(1,'Oben'),(-1,'Unten')]:
        for i,(x,y) in enumerate(pcd(4,25)):
            screw(6,12,(x,y,q['motor_back']+6),(0,0,1),label+f'_Stator_M6_{i}',sign=sign)
        for i,(x,y) in enumerate(pcd(12,20)):
            screw(5,40,(x,y,q['hub_z']+5),(0,0,-1),label+f'_Rotor_M5_{i}',sign=sign)
        for i,(x,y) in enumerate(pcd(4,50,45)):
            washer(6,(x,y,q['membrane_z']-1.6),(0,0,1),label+f'_Membran_ScheibeU{i}',sign=sign)
            screw(6,25,(x,y,q['membrane_z']-1.6),(0,0,-1),label+f'_Membran_M6_{i}',sign=sign)
            washer(6,(x,y,q['hub_z']+10),(0,0,1),label+f'_Membran_ScheibeO{i}',sign=sign)
            nut6((x,y,q['hub_z']+11.6),(0,0,1),label+f'_Membran_Mutter{i}',sign=sign)
        for i,(x,y) in enumerate(pcd(p['blade_count'],p['drive_post_radius'])):
            for tag,z,axis in [('Unten',q['carrier_bottom']-6,(0,0,-1)),('Oben',q['membrane_z']+p['membrane_t'],(0,0,1))]:
                washer(6,(x,y,z),axis,label+f'_Zuganker{i}_{tag}_Scheibe',sign=sign)
                z2=z+axis[2]*1.6;nut6((x,y,z2),axis,label+f'_Zuganker{i}_{tag}_Mutter',sign=sign)
        for xs in [-1,1]:
            for ys in [-1,1]:
                x=xs*p['motor_mount_bolt_x'];y=ys*p['frame_beam_y']
                washer(4,(x,y,q['motor_back']-1),(0,0,1),label+f'_Motortraeger_Scheibe{xs}_{ys}',sign=sign)
                screw(4,20,(x,y,q['motor_back']-1),(0,0,-1),label+f'_Motortraeger_M4{xs}_{ys}',sign=sign)
                s=parts['P13-BUCHSE8-M4-L12']['shape'].translated(V(x,y,q['motor_back']))
                put('P13-BUCHSE8-M4-L12',label+f'_Motortraeger_Buchse{xs}_{ys}',shape=s,sign=sign)
        for i,a in enumerate(q['guide_angles']):
            r=q['roller_center'];fz=q['fork_inner_z']
            for xx,yy in [(p['fork_web_start']+p['fork_web_depth']/2,y) for y in [-p['fork_bolt_y'],p['fork_bolt_y']]]:
                for side in [-1,1]:screw(6,16,(r+xx,yy,q['level_z']+side*(fz+p['fork_t'])),(0,0,side),label+f'_Gabel{i}_{yy}_{side}',a,sign)
            for dz in [-p['web_bolt_z'],p['web_bolt_z']]:
                face=r+p['fork_web_start'];zz=q['level_z']+dz
                washer(6,(face,0,zz),(-1,0,0),label+f'_Guide{i}_Scheibe{dz}',a,sign)
                screw(6,30,(face-1.6,0,zz),(-1,0,0),label+f'_Guide{i}_M6{dz}',a,sign)
        for i in range(int(p['blade_count'])):
            a=m['blade_phase']+360*i/p['blade_count'];pre=label+f'_Blatt{i+1}'
            for id,tag in [('P13-WURZEL-ENDSCHEIBE','WurzelEndscheibe'),('P13-HEBEL-ENDSCHEIBE','HebelEndscheibe'),('P13-HEBEL-DISTANZ','HebelDistanz'),('P13-HEBEL-ANLAUF','HebelAnlauf')]:
                s=parts[id]['shape'].copy();s.rotate(V(),V(1,0,0),p['pitch_neutral']);put(id,pre+'_'+tag,shape=s,angle=a,sign=sign,z=q['level_z'])
            screw(5,12,(203,0,0),(1,0,0),pre+'_WurzelEnd_M5',a,sign,q['level_z'])
            screw(4,16,(64,0,0),(-1,0,0),pre+'_HebelEnd_M4',a,sign,q['level_z'])
            phi=p['pitch_neutral']
            washer(6,(89,25,0),(1,0,0),pre+'_Pitchpin_ScheibeO',a,sign,phi,q['level_z'])
            washer(6,(69,25,0),(-1,0,0),pre+'_Pitchpin_ScheibeI',a,sign,phi,q['level_z'])
            nut6((67.4,25,0),(-1,0,0),pre+'_Pitchpin_Mutter',a,sign,phi,q['level_z'])
            screw(6,30,(90.6,25,0),(1,0,0),pre+'_Pitchpin_M6',a,sign,q['level_z'],pitch=phi)
            for j,xx in enumerate([719.2,727]):
                put('STD-DIN471-8',pre+f'_AussenSicherungsring{j}',shape=parts['STD-DIN471-8']['shape'].translated(V(xx,0,0)),angle=a,sign=sign,z=q['level_z'])
        mate(label+'_Motor',label+'_Statorplatte','Nutzerzeichnung4×M6/PCD50, Phase0°; ISO4762-M6×12; angenommener Eingriff6mm',pending='Gewindetiefe vor Schraubenbestellung abgleichen')
        mate(label+'_Motor',label+'_Nabe','Nutzerzeichnung12×M5/PCD40; ISO4762-M5×40; angenommener Eingriff5mm',pending='Gewindetiefe/Zentrierung vor Bestellung abgleichen')
    # Shared pedestal: four full through-bolts, with washers and nuts on both faces.
    for x in [-45,45]:
        for y in [-32,32]:
            washer(6,(x,y,40),(0,0,1),f'Zentral_ScheibeO{x}_{y}')
            washer(6,(x,y,-40),(0,0,-1),f'Zentral_ScheibeU{x}_{y}')
            screw(6,90,(x,y,41.6),(0,0,1),f'Zentral_M6{x}_{y}')
            nut6((x,y,-41.6),(0,0,-1),f'Zentral_Mutter{x}_{y}')
    # End plate-to-node joints are M4 with centering sleeves, matching actual node cores.
    for xs in [-1,1]:
        for y in [-32,32]:
            x=xs*120;axis=(-xs,0,0)
            washer(4,(x,y,0),axis,f'Bruecke_Scheibe{xs}_{y}')
            screw(4,16,(x-xs,y,0),axis,f'Bruecke_M4{xs}_{y}')
            s=parts['P13-BUCHSE8-M4-L8']['shape'].copy();s.Placement=A.Placement(V(x,y,0),A.Rotation(V(0,0,1),V(xs,0,0))).multiply(s.Placement)
            put('P13-BUCHSE8-M4-L8',f'Bruecke_Buchse{xs}_{y}',shape=s)
    q['motor_connection_source']=config['motor_source']
    from truss import add as braces
    braces(config,parts,scene,q,define,put,mate,screw)
