#!/usr/bin/env python3
"""P02 purchased-parts integration review; never claims the complete assembly is released.

Imported ISO fasteners are actual library STEP solids. OEM interface references are
explicitly segregated until original CAD / drawings are supplied.
"""
import sys,os,json,csv,math,hashlib,collections
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
sys.path[:0]=[os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')),str(H.parent/'bewegung')]
import FreeCAD as A,Part
V=A.Vector;OUT=H/'Ausgabe'
source=H.parent/'bewegung/Ausgabe/Cohexial_R04_M01_Bewegung.FCStd';d=A.openDocument(str(source));d.Label='P02 Kaufteile-Integration – FREIGABE GESPERRT'
base=A.openDocument(str(H.parent/'halterungen/Ausgabe/R04_Taumelmodell_Halterungen_H01.FCStd'))
# Keep purchased components whole. Arbitrary interior geometry is not a production drawing.
remove_roles={'bearing_inner','bearing_cage','bearing_ball','motor_bell','motor_shaft'}
for o in list(d.Objects):
    if o.Name=='Bewegungssteuerung' or getattr(o,'MotionRole',None) in remove_roles:d.removeObject(o.Name)
for o in list(d.Objects):
    role=getattr(o,'MotionRole',None)
    if role in ('bearing_outer','motor_stator'):
        b=base.getObject(o.Name);assert b is not None
        shape=b.Shape.copy()
        if role=='motor_stator':
            # Complete external module reference; original purchased motor body + external shaft.
            src=[x for x in base.Objects if hasattr(x,'BauteilID') and x.BauteilID=='MOTORWELLE-M5' and x.Name.startswith('Oben_' if o.Rotor==0 else 'Unten_')]
            shape=Part.makeCompound([shape]+[x.Shape for x in src])
        o.Shape=Part.makeCompound([shape]);o.Placement=A.Placement()
    if not hasattr(o,'BauteilID'):continue
    for typ,name in [('App::PropertyString','P02_Klasse'),('App::PropertyString','P02_Freigabe'),('App::PropertyString','P02_Offen')]:o.addProperty(typ,name)
    ident=o.BauteilID
    purchased=role in ('bearing_outer','motor_stator','servo_housing','servo_horn','servo_shaft','servo_tip') or getattr(o,'Herstellung','') in ('Kauf','Teil Motor','Kaufteil_Bauraum') or ident.startswith(('M3','M2','REF_','KEEP_'))
    o.P02_Klasse='Kaufteil_Anschlussreferenz' if purchased else 'Eigenfertigung_Entwurf'
    o.P02_Freigabe='GESPERRT'
    o.P02_Offen='Original-CAD und Anschluss-/Befestigungsnachweis fehlen' if purchased else 'F01/M01 offene Montage-, Toleranz-, Werkstoff- und Schnittstellennachweise'
manifest=json.loads((H/'Quellen/Quellenmanifest.json').read_text())
assets={x['id']:x for x in manifest['assets']}
shapes={key:Part.read(str(H/'Quellen'/val['filename'])) for key,val in assets.items()}
replaced=[];nuts=[]
def actual(o,shape,key):
    o.Shape=Part.makeCompound([shape]);o.Placement=A.Placement();o.P02_Klasse='Importiertes_Normteil';o.P02_Freigabe='NENNMASSE_GEPRUEFT_MONTAGE_NOCH_NICHT_FREIGEGEBEN';o.P02_Offen='Schraubensicherung/Anzug und vollständige Klemmlängen/Dämpfer prüfen'
    for typ,name in [('App::PropertyString','P02_Quelle'),('App::PropertyString','P02_Quell_SHA256')]:
        if name not in o.PropertiesList:o.addProperty(typ,name)

    if 'Masse_g' not in o.PropertiesList:o.addProperty('App::PropertyString','Masse_g')
    o.Masse_g=f'{shape.Volume*.00785:.5f}'
    if 'P02_Massenquelle' not in o.PropertiesList:o.addProperty('App::PropertyString','P02_Massenquelle')
    o.P02_Massenquelle='Nominales CAD-Volumen x 7850 kg/m3 Stahl, nicht gewogen; H01-Zusatzbudget nicht neu bilanziert'
    o.P02_Quelle=assets[key]['source_url'];o.P02_Quell_SHA256=assets[key]['sha256'];o.Label=key+'__'+o.Name
    return o
for o in list(d.Objects):
    if not hasattr(o,'BauteilID'):continue
    if o.BauteilID not in ('M3x40','M3x12'):continue
    b=o.Shape.BoundBox;x=(b.XMin+b.XMax)/2;y=(b.YMin+b.YMax)/2
    key='N03_M3x40' if o.BauteilID=='M3x40' else 'N02_M3x12';z=96 if key=='N03_M3x40' else -104
    s=shapes[key].copy();s.rotate(V(),V(1,0,0),180);s.translate(V(x,y,z));actual(o,s,key);replaced.append((o,key,z))
    if key=='N02_M3x12':
        nut=d.addObject('Part::Feature','P02_Mutter_Anschluss_'+str(len(nuts)));nut.Shape=shapes['N04_Mutter_M3'];nut.Placement.Base=V(x,y,-96)
        nut.addProperty('App::PropertyString','BauteilID');nut.BauteilID='ISO4032-M3'
        for name in ('P02_Klasse','P02_Freigabe','P02_Offen'):nut.addProperty('App::PropertyString',name)
        # Bake source translation into a child location, preserving the intended world position.
        actual(nut,nut.Shape.copy(),'N04_Mutter_M3');nuts.append(nut)
A.closeDocument(base.Name)
# Explicit, queryable production gate. Imported models alone cannot satisfy it.
info=d.addObject('App::FeaturePython','P02_Fertigungsstatus')
for typ,name in [('App::PropertyBool','Gesamt_Fertigungsfreigabe'),('App::PropertyString','Begruendung'),('App::PropertyString','Kaufteilstrategie'),('App::PropertyString','Motorlochbild_IST')]:info.addProperty(typ,name)
info.Gesamt_Fertigungsfreigabe=False;info.setEditorMode('Gesamt_Fertigungsfreigabe',1)
info.Begruendung='Original-CAD/Anschlüsse von Lagern, Motoren, Servo/Horn sowie F01/M01 Fertigungs- und Montagepunkte offen. Keine Eigenfertigung von Kaufteil-Innenteilen.'
info.Kaufteilstrategie='Lager, EMAX ECO II 2306 KV1900 und Savox SB-2271SG(+) als komplette Kaufteile; Hersteller und exakter Artikel bei Lagern noch festzulegen.'
info.Motorlochbild_IST='PCD 16 mm; quadratische Achsabstände 11.3137085 x 11.3137085 mm; muss Originalzeichnung entsprechen'
d.recompute();allparts=[o for o in d.Objects if hasattr(o,'BauteilID') and hasattr(o,'Shape') and not o.Shape.isNull()];assert all(o.Shape.isValid() for o in allparts)
# Check real bolt heads, the new cap nuts, and the two cap/plate contact stacks.
checks=[];interferences=[]
capbottom=[o for o in allparts if getattr(o,'BauteilID','')=='H01' and o.Shape.BoundBox.ZMax<0][0]
capupper=[o for o in allparts if getattr(o,'BauteilID','')=='H01' and o.Shape.BoundBox.ZMin>0][0]
plate=[o for o in allparts if getattr(o,'BauteilID','')=='H04'][0]
for o,key,z in replaced:
    assembly_part=capupper if key=='N03_M3x40' else plate
    volume=o.Shape.common(assembly_part.Shape).Volume;checks.append(dict(bolt=o.Name,head_bearing_plane_z_mm=z,reference=assembly_part.Name,interference_mm3=volume));assert volume<1e-3,(o.Name,volume)
    if key=='N02_M3x12':
        assert abs(o.Shape.BoundBox.ZMax-(-92))<.002
for o in nuts:
    vol=o.Shape.common(capbottom.Shape).Volume;assert vol<1e-3,(o.Name,vol);checks.append(dict(nut=o.Name,clamping_plane_z_mm=-96,reference=capbottom.Name,interference_mm3=vol))
for nut in nuts:
    for bolt,key,z in replaced:
        if key!='N02_M3x12':continue
        a,b=nut.Shape.BoundBox,bolt.Shape.BoundBox
        if abs((a.XMin+a.XMax)-(b.XMin+b.XMax))<.01 and abs((a.YMin+a.YMax)-(b.YMin+b.YMax))<.01:
            # Nominal thread solids need not encode the real mating helical flanks.
            protrusion=bolt.Shape.BoundBox.ZMax-nut.Shape.BoundBox.ZMax
            assert protrusion>1.4;checks.append(dict(bolt=bolt.Name,nut=nut.Name,thread_end_protrusion_mm=protrusion))
path=OUT/'P02_Kaufteile_Integration_GESPERRT.FCStd';d.Comment=info.Begruendung;d.saveAs(str(path));Part.export([o for o in allparts if not getattr(o,'BauteilID','').startswith('KEEP_')],str(OUT/'P02_Kaufteile_Integration_GESPERRT.step'));A.closeDocument(d.Name)
d=A.openDocument(str(path));assert not d.getObject('P02_Fertigungsstatus').Gesamt_Fertigungsfreigabe;assert all(o.Shape.isValid() for o in d.Objects if hasattr(o,'Shape') and not o.Shape.isNull());A.closeDocument(d.Name)
report=dict(status='PARTIAL_STANDARD_PART_INTEGRATION_COMPLETE_FULL_PRODUCTION_BLOCKED',native_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),source_m01_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),imported_bolts=len(replaced),imported_cap_nuts=len(nuts),checks=checks,native_reopen_pass=True,production_release=False,hardware_not_completed=['Stack upper nuts/grommets and bearing planes not defined','Four M3x80 battery fasteners not replaced by a different or scaled length','Two M2x35 cross fasteners and their bearing surfaces not defined'],motor_mount_current=dict(pcd_mm=16,square_pitch_mm=16/math.sqrt(2)),source_class='Community library dimension-checked standard models, not original OEM CAD or supplier certification')
(OUT/'Integrationspruefung.json').write_text(json.dumps(report,indent=2));print('Imported bolts',len(replaced),'cap nuts',len(nuts),'native reopen PASS; production release FALSE')
