#!/usr/bin/env python3
"""H01 holders and integrated review assembly; preserve the F01 rotor snapshot."""
import csv,json,os,sys,tempfile,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE.parent/'cad'))
sys.path.insert(0,os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')))
import FreeCAD as App,Part,MeshPart
from halterungen_features import MountPart,EnvelopeReferences,recipe,box,cylinder,ring,grid,corners
import fertigung_erstellen as drawing

P=json.loads((HERE/'parameter.json').read_text());OUT=HERE/'Ausgabe'
for sub in ('Einzelteile','STEP','STL','Zeichnungen','Vorlagen'): (OUT/sub).mkdir(parents=True,exist_ok=True)
drawing.OUT=OUT;drawing.EnvelopeReferences=EnvelopeReferences
_original_template=drawing.template

def holder_template(*args):
    _original_template(*args)
    path=args[0];path.write_text(path.read_text().replace('ENTWURF F01','HALTERUNGEN H01').replace('Revision F01','Revision H01'))
drawing.template=holder_template

PARTS=[
 ('H01','Rohr_Endadapter',2,'PETG ungefuellt',[
  'Platte 70 x 62 x 4; 4 D3.4 auf Quadrat 30.5', 'Einsteckhuelse D27.8 / D24 x 8',
  'Querbohrung D2.2, 3 mm ab Rohrende, entlang x', 'Ersetzt obere UND untere F01-Kappe; M2 x 35 quer'],
  'Rohr gleichzeitig D2.2 quer bohren; axiale Sicherung, keine reine Steckverbindung.'),
 ('H02','ESC_Distanz_12',4,'PETG ungefuellt',[
  'Aussen D8; innen D3.4; Laenge 12', 'ESC-PCB-Ebene im Montagevorschlag bei z112',
  'Bohrbild Quadrat 30.5; Leiterplattendicke 1.6'],
  'Hersteller-Daempfer und echte Montageebene vor endgueltiger Laenge pruefen.'),
 ('H03','FC_Distanz_14_4',4,'PETG ungefuellt',[
  'Aussen D8; innen D3.4; Laenge 14.4', 'Zwischen ESC-PCB-Oberseite und FC-PCB-Unterseite',
  'FC-PCB-Unterseite z128; USB-Zugang auf +x-Seite'],
  'Hersteller-Daempfer und echte Montageebene vor endgueltiger Laenge pruefen.'),
 ('H04','Akku_Anschlussplatte',1,'PETG ungefuellt',[
  '100 x 64 x 4; z -104 bis -100 im Fahrzeug', '4 D3.4 auf Quadrat 30.5 am Endadapter',
  '4 D3.4 bei x +/-45, y +/-26; Mittelbohrung D20'],
  'Unterer Endadapter traegt Akku ueber formschluessige Querbolzensicherung.'),
 ('H05','Akkuwanne_78x37x52',1,'PETG ungefuellt',[
  'Boden 100 x 64 x 3; Innenraum 82 x 41', 'Fuehrungsrand 2 dick / 6 hoch; offene Kabelausgaenge',
  '4 Gurtschlitze 22 x 3, Mitten x +/-24, y +/-26',
  '4 D3.4 bei x +/-45, y +/-26', 'Akku 78 x 37 x 52; Bodenpolster 2; zwei 20-mm-Gurte'],
  'Zellen nicht mit Schrauben klemmen. Gurte und weiche Auflagen separat.'),
 ('H06','Akku_Distanzrohr_62',4,'Aluminium, Legierung offen',[
  'Aussen D6; innen D3.4; Laenge 62', 'Zuschnitt, plan entgraten; 4 Stueck',
  'Mit durchgehenden M3 x 80, Scheiben und Stoppmuttern'],
  'Zuschnittteil, kein langer gedruckter Zugpfosten.'),
 ('H07','Mittelrohr_Bohrbild_H01',1,'Aluminium, Legierung offen',[
  'Rohr D30 x 1; Laenge 192', 'Zwei Querbohrungen D2.2, entlang x durch BEIDE Waende',
  'Bohrmitten z3 und z189, ab gleicher Rohrstirn', 'Im Fahrzeug z -93 und +93; Endabstand jeweils 3'],
  'Modifiziertes Rohr ersetzt F01-Rohr. Endabstand und lokale Festigkeit pruefen.'),
]


def feature(doc,name,shape,ident,kind,material=''):
    o=doc.addObject('Part::Feature',name);o.Shape=shape;o.Placement=shape.Placement
    for k,v in [('BauteilID',ident),('Herstellung',kind),('Werkstoff',material)]:o.addProperty('App::PropertyString',k);setattr(o,k,v)
    density=2700 if material=='Aluminium' else 7850 if material=='Stahl' else P['density_kg_m3']*P['effective_fill_assumption'] if kind=='Druck' else 0
    o.addProperty('App::PropertyString','Masse_g');o.Masse_g=f'{shape.Volume*density/1e6:.5f}'
    return o


def move(shape,x=0,y=0,z=0,flip=False):
    s=shape.copy()
    if flip:s.rotate(App.Vector(),App.Vector(1,0,0),180)
    s.translate(App.Vector(x,y,z));return s


def board_envelope(spec,p):
    # Component keepout envelope only. Mounting areas are excluded, not asserted
    # as real 8 mm PCB holes. The real board hole and grommet sizes are unknown.
    # The image gives total heights but no component allocation across the two
    # PCB faces. Enclose every possible allocation instead of assuming symmetry.
    bottom=spec['pcb_bottom_z']-(spec['envelope_height']-spec['pcb_thickness'])
    reserved_height=2*spec['envelope_height']-spec['pcb_thickness']
    s=box(spec['width'],spec['length'],reserved_height,bottom)
    tools=[cylinder(8,reserved_height+2,bottom-1,x,y) for x,y in grid(p)]
    return s.cut(Part.makeCompound(tools))


def main():
    records=[]
    for ident,title,count,material,notes,issue in PARTS:
        print('Generate',ident,title,flush=True)
        d=App.newDocument(ident);d.TransientDir=tempfile.mkdtemp(prefix='h01-')+'/'
        o=d.addObject('Part::FeaturePython','Bauteil')
        for k,v in [('Rezept',ident),('BauteilID',ident),('Werkstoff',material),('Status',P['revision']),('ParameterJSON',json.dumps(P)),('OffenePunkte',issue)]:
            o.addProperty('App::PropertyString',k);setattr(o,k,v)
        MountPart(o);o.Proxy.execute(o);d.recompute()
        assert o.Shape.isValid() and len(o.Shape.Solids)==1,ident
        drawing.add_drawing(d,o,(ident,ident,title,count,material,notes,issue))
        d.recompute();d.saveAs(str(OUT/'Einzelteile'/f'{ident}_{title}.FCStd'))
        Part.export([o],str(OUT/'STEP'/f'{ident}_{title}.step'))
        if ident not in ('H06','H07'):
            print_shape=o.Shape.copy()
            if ident=='H01':print_shape.rotate(App.Vector(),App.Vector(1,0,0),180)
            bb=print_shape.BoundBox;print_shape.translate(App.Vector(-bb.XMin,-bb.YMin,-bb.ZMin))
            mesh=MeshPart.meshFromShape(Shape=print_shape,LinearDeflection=.02,AngularDeflection=.25,Relative=False)
            mesh.write(str(OUT/'STL'/f'{ident}_{title}.stl'));assert mesh.isSolid() and mesh.Volume>0
        s=Part.Shape();s.read(str(OUT/'STEP'/f'{ident}_{title}.step'))
        error=abs(s.Volume-o.Shape.Volume)/o.Shape.Volume
        assert s.isValid() and len(s.Solids)==1 and error<1e-5,(ident,error)
        bb=o.Shape.BoundBox
        records.append({'id':ident,'title':title,'count':count,'material':material,'volume_mm3':o.Shape.Volume,
          'dimensions_mm':[bb.XLength,bb.YLength,bb.ZLength],'step_volume_relative_error':error,
          'printed':ident not in ('H06','H07'),'open_issue':issue})
        App.closeDocument(d.Name)
    base=HERE.parent/'cad/R04_Taumelmodell_1zu4.FCStd'
    d=App.openDocument(str(base));d.Label='R04 Taumelmodell + FC ESC Akku – H01 ENTWURF'
    d.Comment='F01 rotor geometry unchanged. H01 replaces endcaps and centre tube; adds holder references. No manufacturing release.'
    legacy=[o for o in d.Objects if hasattr(o,'BauteilID')]
    exclusions={'TM-KAPPE-STACK-PRUEFSTAND','MITTELROHR-AL-D30x1'}
    for o in legacy:
        if o.BauteilID=='MITTELROHR-AL-D30x1':
            s=move(recipe('H07',P),z=-P['tube']['length']/2);o.Shape=s;o.Placement=s.Placement;o.BauteilID='H07'
            o.Masse_g=f'{s.Volume*2700/1e6:.5f}'
        elif o.BauteilID=='TM-KAPPE-STACK-PRUEFSTAND':
            upper=o.Shape.BoundBox.ZMax>0
            s=move(recipe('H01',P),z=96 if upper else -96,flip=not upper)
            o.Shape=s;o.Placement=s.Placement;o.BauteilID='H01';o.Herstellung='Druck'
            o.Masse_g=f'{s.Volume*P["density_kg_m3"]*P["effective_fill_assumption"]/1e6:.5f}'
    new=[]
    def add(name,shape,id,kind='Druck',material=P['material']):
        o=feature(d,name,shape,id,kind,material);new.append(o);return o
    for i,(x,y) in enumerate(grid(P)):
        add('ESC_Distanz_'+str(i),move(recipe('H02',P),x,y,100),'H02')
        add('FC_Distanz_'+str(i),move(recipe('H03',P),x,y,113.6),'H03')
    add('Akku_Anschlussplatte',move(recipe('H04',P),z=-104),'H04')
    add('Akkuwanne',move(recipe('H05',P),z=P['tray']['floor_bottom_z']),'H05')
    for i,(x,y) in enumerate(corners(P)):
        add('Akku_Distanz_'+str(i),move(recipe('H06',P),x,y,P['tray']['floor_bottom_z']+P['tray']['floor']),'H06','Zuschnitt','Aluminium')
    # Electronics envelopes, not board CAD reconstructed from a photograph.
    references=[]
    for id,key in [('REF_ESC','esc'),('REF_FC','fc')]:references.append(add(id,board_envelope(P[key],P),id,'Kaufteil_Bauraum','PCB-Komponentenhuelle'))
    b=P['battery'];floor_top=P['tray']['floor_bottom_z']+P['tray']['floor'];battery_bottom=floor_top+P['tray']['pad_thickness']
    references.append(add('Akku_Referenz',box(b['length'],b['width'],b['height'],battery_bottom),'REF_AKKU','Kaufteil_Bauraum','LiPo'))
    references.append(add('Bodenpolster',box(80,39,P['tray']['pad_thickness'],floor_top),'REF_POLSTER','Kauf','isolierender_weicher_Schaum'))
    # Hardware shanks are reserved with explicit hole clearances.
    for i,(x,y) in enumerate(grid(P)):
        add('M3_Stack_'+str(i),cylinder(3,40,96,x,y),'M3x40','Kauf','Stahl')
    for i,(x,y) in enumerate(corners(P)):
        add('M3_Akku_'+str(i),cylinder(3,80,-174.5,x,y),'M3x80','Kauf','Stahl')
    for sign in (-1,1):
        add('M2_Quer_'+str(sign),Part.makeCylinder(1,35,App.Vector(-17.5,0,sign*93),App.Vector(1,0,0)),'M2x35','Kauf','Stahl')
    # Four H04-to-H01 fixing bolts, independent of the four outer tray rods.
    for i,(x,y) in enumerate(grid(P)):
        add('M3_Anschluss_'+str(i),cylinder(3,12,-107,x,y),'M3x12','Kauf','Stahl')
    keepouts=[('USB_Zugang',box(12,14,11,124,25.5,0)),('ESC_Kabel',box(22,20,18,105,0,-32.45)),
              ('XT60_Zugang',box(24,20,30,-159,53,0)),('JST_XHR_Zugang',box(18,16,25,-155,-50,0))]
    for name,s in keepouts:
        o=feature(d,name,s,'KEEP_'+name,'Zugangsraum','kein_Bauteil')
        if App.GuiUp:o.ViewObject.Transparency=80
    d.recompute()
    bodies=[o for o in d.Objects if hasattr(o,'BauteilID') and not o.BauteilID.startswith('KEEP_')]
    assert all(o.Shape.isValid() for o in bodies)
    # All new solids against unchanged rotor hardware, with broad-phase bounds.
    # Endcap and tube interfaces are checked separately below.
    unchanged=[o for o in legacy if o.BauteilID not in ('H01','H07')]
    collisions=[]
    for a in new:
        for b0 in unchanged:
            if a.Shape.BoundBox.intersect(b0.Shape.BoundBox):
                volume=a.Shape.common(b0.Shape).Volume
                if volume>1e-3:collisions.append([a.Name,b0.Name,volume])
    for i,a in enumerate(new):
        for b0 in new[i+1:]:
            if a.Shape.BoundBox.intersect(b0.Shape.BoundBox):
                volume=a.Shape.common(b0.Shape).Volume
                if volume>1e-3:collisions.append([a.Name,b0.Name,volume])
    adapters=[o for o in legacy if o.BauteilID=='H01'];tube=next(o for o in legacy if o.BauteilID=='H07')
    for a in adapters:
        assert a.Shape.common(tube.Shape).Volume<1e-3
        for b0 in unchanged:
            if a.Shape.BoundBox.intersect(b0.Shape.BoundBox):
                v=a.Shape.common(b0.Shape).Volume
                if v>1e-3:collisions.append([a.Name,b0.Name,v])
    # Access spaces must remain free of structural holder parts, not electronics
    # components/wires which the same space explicitly reserves.
    access=[]
    for name,s in keepouts:
        hits=[]
        for o in new+adapters:
            if o.Herstellung in ('Druck','Zuschnitt') and s.BoundBox.intersect(o.Shape.BoundBox):
                v=s.common(o.Shape).Volume
                if v>1e-3:hits.append([o.Name,v])
        access.append({'name':name,'structural_interferences':hits})
    assert not collisions,collisions
    assert all(not k['structural_interferences'] for k in access),access
    # Battery clearance and fastening load are conditional design calculations.
    p=P['tray'];assert p['inside_length']>=b['length']+2 and p['inside_width']>=b['width']+2
    battery_top=battery_bottom+b['height'];overhead=-104-battery_top
    assert overhead>=5
    assert abs(floor_top+p['standoff_length']-(-104))<1e-8,'tray spacer does not meet both support planes'
    nominal_battery_force=(b['mass_g']+b['mass_tolerance_g'])/1000*9.81*P['prototype_load_case']['battery_total_acceleration_g']
    structure_mass=sum(float(o.Masse_g) for o in bodies if not o.BauteilID.startswith('REF_'))
    mass_budget={'structure_motors_and_modeled_shanks_g':structure_mass,'battery_nominal_g':b['mass_g'],
        'fc_esc_combined_assumption_g':26,'receiver_assumption_g':3,'wiring_assumption_g':45,
        'unmodeled_heads_nuts_washers_assumption_g':15,'straps_pads_assumption_g':10}
    mass_budget['total_nominal_g']=sum(mass_budget.values())
    mass_budget['excluded_mass_note']='Real servo mounting brackets, BEC and protection are not yet fully defined or included; weigh actual assembly.'
    result={'revision':P['revision'],'bodies':len(bodies),'all_shapes_valid':True,'collisions':collisions,
      'access_spaces':access,'battery_inner_clearance_mm':[p['inside_length']-b['length'],p['inside_width']-b['width']],
      'battery_overhead_clearance_mm':overhead,'battery_top_z_mm':battery_top,
      'battery_design_load_N_including_mass_tolerance':nominal_battery_force,
      'tube_end_distance_beyond_cross_hole_mm':P['adapter']['cross_offset_from_end']-P['adapter']['cross_bore']/2,
      'mass_budget':mass_budget,
      'limitations':['Electronics component envelopes and exact grommets are not manufacturer 3D geometry.',
        'PCB component reservation covers all allocations of total component height across both PCB faces; exact mounting planes and grommets still require verification.',
        'Only stored F01 hover geometry is in the integrated assembly; the added holders lie axially outside the rotating assembly.',
        'Screw shanks are shown; head/nut/washer detailed geometry and tightening proof remain open.',
        'Strap strengths, printed part strength, tube end-hole strength and cooling need tests.']}
    d.saveAs(str(OUT/'R04_Taumelmodell_Halterungen_H01.FCStd'))
    Part.export(bodies,str(OUT/'R04_Taumelmodell_Halterungen_H01.step'))
    App.closeDocument(d.Name)
    with (OUT/'Stueckliste_H01.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f,delimiter=';');w.writerow(['ID','Benennung','Anzahl','Werkstoff','Volumen_mm3','Offen'])
        for r in records:w.writerow([r['id'],r['title'],r['count'],r['material'],round(r['volume_mm3'],3),r['open_issue']])
    (OUT/'Geometriepruefung_H01.json').write_text(json.dumps({'parts':records,'assembly':result,'parameters':P},indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
