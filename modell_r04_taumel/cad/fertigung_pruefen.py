#!/usr/bin/env python3
"""Independently reopen every deliverable and exercise spreadsheet regeneration."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,os.environ.get('FREECAD_LIB','/usr/lib/freecad/lib'))
import FreeCAD as App
import Part
import Mesh
import fertigung_features
from fertigung_erstellen import PARTS

OUT=HERE/'Fertigung'
parameters=json.loads((HERE/'parameter.json').read_text())
assert json.loads((OUT/'Parameterstand.json').read_text())==parameters,'stale parameter snapshot'
results=[]
for spec in PARTS:
    ident,recipe,title,*_=spec
    p=OUT/'Einzelteile'/f'{ident}_{title}.FCStd'
    d=App.openDocument(str(p))
    d.TransientDir=tempfile.mkdtemp(prefix='propboard-validation-')+'/'
    d.recompute()
    o=d.getObject('Bauteil')
    assert json.loads(o.ParameterJSON)==parameters,(ident,'stale part parameters')
    assert o.Shape.isValid() and len(o.Shape.Solids)==1,ident
    broken=[(x.Name,x.State) for x in d.Objects if any(s in x.State for s in ('Invalid','Error'))]
    assert not broken,(ident,broken)
    assert len([x for x in d.Objects if x.TypeId=='TechDraw::DrawPage'])==1,ident
    view_count=4 if recipe in ('Nabe','Taumel_Gleitkugel','Taumel_Innenring','Taumel_Drehring') else 3
    assert len([x for x in d.Objects if x.TypeId=='TechDraw::DrawViewPart'])==view_count,ident
    assert len([x for x in d.Objects if x.TypeId=='TechDraw::DrawViewDimension'])==3,ident
    for name in ('Gesamtmass_X','Gesamtmass_Y','Gesamtmass_Z'):
        assert d.getObject(name).References3D, (ident,name)
    datums=d.getObject('Bemassungsbezug').Shape.Vertexes
    bbox=o.Shape.BoundBox
    measured=[abs(getattr(datums[1].Point,k)-getattr(datums[0].Point,k)) for k in ('x','y','z')]
    expected=[bbox.XLength,bbox.YLength,bbox.ZLength]
    assert all(abs(a-b)<1e-8 for a,b in zip(measured,expected)),(ident,measured,expected)
    before=o.Shape.Volume
    if recipe=='Fluegel':
        sh=d.getObject('Parameter')
        row=next(r for r in range(2,o.ParameterZeilen+2) if sh.get('A'+str(r))=='blade.chord')
        old=sh.get('B'+str(row)); assert float(old)==30
        sh.set('B'+str(row),'31');d.recompute()
        assert o.Shape.isValid() and abs(o.Shape.Volume-before)>1,(ident,'parameter edit did not regenerate')
        datum_points=d.getObject('Bemassungsbezug').Shape.Vertexes
        assert abs(datum_points[1].Point.y-datum_points[0].Point.y-31)<1e-8,'dimension datums did not follow parameter edit'
        changed=o.Shape.Volume
        sh.set('B'+str(row),'30');d.recompute()
        assert abs(o.Shape.Volume-before)<1e-6,(ident,'restore differs')
        # Cache must return independent copies despite callers transforming a part.
        params=json.loads(o.ParameterJSON)
        a=fertigung_features.shape_for('Fluegel',params);base=a.BoundBox.XMin
        a.translate(App.Vector(100,0,0))
        b=fertigung_features.shape_for('Fluegel',params)
        assert abs(b.BoundBox.XMin-base)<1e-9,'cached shape mutated'
        results.append({'id':ident,'parameter_chord_30_31_30':True,'volume_before':before,'volume_changed':changed,'independent_cached_shapes':True})
    else:results.append({'id':ident,'reopened':True,'valid':True,'native_views':view_count,'native_dimensions':3})
    App.closeDocument(d.Name)
    if recipe!='Mittelrohr':
        mesh=Mesh.Mesh(str(OUT/'STL'/f'{ident}_{title}.stl'))
        assert mesh.isSolid() and mesh.Volume>0,ident
        results[-1]['stl_closed']=True
# Assembly review is reported separately from the individual shape checks.
assembly=App.openDocument(str(HERE/'R04_Taumelmodell_1zu4.FCStd'))
objects=[o for o in assembly.Objects if hasattr(o,'BauteilID')]
assert objects and all(o.Shape.isValid() for o in objects)
assembly_result={'bodies':len(objects),'all_shapes_valid':True}
caps=[o for o in objects if o.BauteilID=='TM-KAPPE-STACK-PRUEFSTAND']
plates=[o for o in objects if o.BauteilID=='TM-HALTEPLATTE']
tubes=[o for o in objects if o.BauteilID=='MITTELROHR-AL-D30x1']
cap_hits=[]
for cap in caps:
    for plate in plates:
        if cap.Shape.BoundBox.intersect(plate.Shape.BoundBox):
            volume=cap.Shape.common(plate.Shape).Volume
            if volume>1e-3:cap_hits.append({'cap':cap.Name,'plate':plate.Name,'overlap_mm3':volume})
assembly_result['additional_cap_plate_collisions']=cap_hits
cap_tube_hits=[]
for cap in caps:
    for tube in tubes:
        volume=cap.Shape.common(tube.Shape).Volume
        if volume>1e-3:cap_tube_hits.append({'cap':cap.Name,'tube':tube.Name,'overlap_mm3':volume})
assembly_result['additional_cap_tube_collisions']=cap_tube_hits
model=fertigung_features.model
fertigung_features.configure(parameters)
guide_checks=[]
for state in parameters['check_states']:
    for angle in state['angles']:
        for sign,ix in ((1,0),(-1,1)):
            theta=parameters['pitch_hover_deg'][ix] if state['theta0']=='hover' else state['theta0']
            x,_,_=model.solve_swash(theta,state['cyclic'],angle,sign,model.link_len_hover())
            pin=model.placed(next(s for s,i in model.swash_stat_hardware() if i=='FUEHRUNGSSTIFT-D3'),model.swash_placement(*x))
            pin_world=model.place([(pin,'FUEHRUNGSSTIFT-D3')],sign)[0][0]
            plate=next(p for p in plates if (p.Shape.BoundBox.ZMin>0)==(sign>0))
            overlap=pin_world.common(plate.Shape).Volume
            guide_checks.append({'state':state['name'],'angle_deg':angle,'side':sign,'overlap_mm3':overlap})
            assert overlap<1e-3,guide_checks[-1]
assembly_result['guide_pin_checks']=guide_checks
assembly_result['guide_pin_checks_passed']=len(guide_checks)==24
App.closeDocument(assembly.Name)
report=json.loads((HERE/'Pruefbericht.json').read_text())
assert report['status']==parameters['status'],'stale assembly report'
assembly_result['sampled_cases']=len(report['zustaende'])
assembly_result['sampled_checks_passed']=report['alle_pruefungen_bestanden']
assembly_result['interlevel_collisions']=report['kollisionen_oben_unten']
assembly_result['manufacturing_release']=False
(OUT/'Validierung.json').write_text(json.dumps({'individual_parts':results,'assembly':assembly_result},ensure_ascii=False,indent=2))
# Content manifest can be verified using sha256sum -c from Fertigung.
paths=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS' and p.suffix not in ('.FCStd1','.FCBak','.zip'))
(OUT/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(OUT))+'\n' for p in paths))
print('Reopened',len(results),'parts; spreadsheet edit/restore and cache copies passed')
print('Assembly',assembly_result)
if not assembly_result['sampled_checks_passed'] or cap_hits or cap_tube_hits or assembly_result['interlevel_collisions']:
    print('FAIL: assembly has documented collisions; manufacturing release blocked.')
    sys.exit(1)
