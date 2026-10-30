#!/usr/bin/env python3
"""Reopen native H01 models, test one parameter edit and verify joint planes."""
import json,os,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));sys.path.insert(0,os.environ.get('FREECAD_LIB',str(HERE.parents[1]/'.cfd-tools/freecad/usr/lib')))
import FreeCAD as App,Part,Mesh
import halterungen_features as F
OUT=HERE/'Ausgabe';data=json.loads((OUT/'Geometriepruefung_H01.json').read_text());p=json.loads((HERE/'parameter.json').read_text())
assert data['parameters']==p
rows=[]
for item in data['parts']:
    name=f"{item['id']}_{item['title']}";d=App.openDocument(str(OUT/'Einzelteile'/f'{name}.FCStd'))
    d.TransientDir=tempfile.mkdtemp(prefix='h01-validate-')+'/'
    d.recompute();o=d.getObject('Bauteil')
    assert json.loads(o.ParameterJSON)==p and o.Shape.isValid() and len(o.Shape.Solids)==1
    assert not [(x.Name,x.State) for x in d.Objects if 'Invalid' in x.State or 'Error' in x.State]
    assert len([x for x in d.Objects if x.TypeId=='TechDraw::DrawViewPart'])==3
    assert len([x for x in d.Objects if x.TypeId=='TechDraw::DrawViewDimension'])==3
    if item['id']=='H01':
        original=o.ParameterJSON;volume=o.Shape.Volume;changed=json.loads(original);changed['adapter']['length']=72
        o.ParameterJSON=json.dumps(changed);d.recompute()
        assert abs(o.Shape.BoundBox.XLength-72)<1e-7 and o.Shape.Volume>volume
        vertices=d.getObject('Bemassungsbezug').Shape.Vertexes
        assert abs(vertices[1].Point.x-vertices[0].Point.x-72)<1e-7
        o.ParameterJSON=original;d.recompute();assert abs(o.Shape.Volume-volume)<1e-6
    if item['printed']:
        mesh=Mesh.Mesh(str(OUT/'STL'/f'{name}.stl'));assert mesh.isSolid() and mesh.Volume>0
        assert mesh.BoundBox.ZMin>=-1e-6
    rows.append({'id':item['id'],'reopened':True,'solid_valid':True,'views':3,'associative_dimensions':3,'printed_mesh_closed':True if item['printed'] else None})
    App.closeDocument(d.Name)
d=App.openDocument(str(OUT/'R04_Taumelmodell_Halterungen_H01.FCStd'))
objects=[o for o in d.Objects if hasattr(o,'BauteilID') and not o.BauteilID.startswith('KEEP_')]
assert len(objects)==data['assembly']['bodies']
assert all(o.Shape.isValid() for o in objects)
# Contact of all four battery standoffs with BOTH support planes, not just
# absence of collisions. A floating 1 mm spacer would fail these checks.
tray=next(o for o in objects if o.BauteilID=='H05');connection=next(o for o in objects if o.BauteilID=='H04')
floor_top=p['tray']['floor_bottom_z']+p['tray']['floor']
spacers=[o for o in objects if o.BauteilID=='H06']
assert len(spacers)==4
for spacer in spacers:
    assert abs(spacer.Shape.BoundBox.ZMin-floor_top)<1e-7
    assert abs(spacer.Shape.BoundBox.ZMax-connection.Shape.BoundBox.ZMin)<1e-7
foam=next(o for o in objects if o.BauteilID=='REF_POLSTER');battery=next(o for o in objects if o.BauteilID=='REF_AKKU')
assert abs(foam.Shape.BoundBox.ZMin-floor_top)<1e-7
assert abs(foam.Shape.BoundBox.ZMax-battery.Shape.BoundBox.ZMin)<1e-7
assert not data['assembly']['collisions']
assert all(not x['structural_interferences'] for x in data['assembly']['access_spaces'])
App.closeDocument(d.Name)
out={'parts':rows,'battery_standoff_joint_checks':8,'pad_contact_checks':2,'assembly_bodies':len(objects),
     'parameter_adapter_70_72_70_passed':True,'recorded_static_collisions':0,
     'status':'PASS_GEOMETRY_AND_REFERENCE_ENVELOPES_NOT_STRENGTH_OR_PRODUCT_FIT_RELEASE'}
(OUT/'Validierung_H01.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
