"""Independent native/STEP round trip and blade inertia register."""
from pathlib import Path
import sys,json,hashlib,math
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as App,Part
H=Path(__file__).resolve().parent;cfg=json.loads((H/'parameter.json').read_text());results=[]
for c in cfg['cases']:
    out=H/'Ausgabe'/c['id'];r=json.loads((out/'Pruefung.json').read_text());rows=json.loads((out/'Massendaten.json').read_text());native=out/(c['id']+'.FCStd')
    assert hashlib.sha256(native.read_bytes()).hexdigest()==r['native_sha256']
    doc=App.openDocument(str(native));inertia=0
    assert len([o for o in doc.Objects if hasattr(o,'Shape')])==r['body_count']
    for p in rows:
        s=doc.getObject(p['id']).Shape
        assert s.isValid(),p['id']
        if 'CFK01' in p['label'] or p['id'].startswith('BLADE_'):
            if c['type']=='coax':x=y=0
            else:x,y=r['centres_mm'][int(p['id'].split('_')[1])]
            for solid in s.Solids:
                m=p['mass_kg']*solid.Volume/s.Volume;cg=solid.CenterOfMass
                inertia+=solid.MatrixOfInertia.A33*m/solid.Volume*1e-6 + m*((cg.x-x)**2+(cg.y-y)**2)*1e-6
    step=Part.read(str(out/(c['id']+'_Rahmen.step')))
    reference=[p for p in rows if p['group']!='P14_existing'];refvol=sum(p['volume_mm3'] for p in reference);expected_solids=sum(p['solid_count'] for p in reference)
    difference=abs(step.Volume/refvol-1)
    assert step.isValid() and len(step.Solids)==expected_solids,(c['id'],len(step.Solids),expected_solids)
    assert difference<.0001,(c['id'],difference)
    inertia/=2 if c['type']=='coax' else c['motors']
    q=dict(id=c['id'],native_shape_valid=True,native_objects=r['body_count'],frame_step_valid=True,frame_step_solids=len(step.Solids),relative_frame_step_volume_difference=difference,blade_polar_inertia_each_motor_kgm2=inertia,inertia_scope='CAD equivalent blade mass distribution only; hub, grip, shaft and motor rotor inertia excluded',native_sha256=r['native_sha256'])
    q['envelope_with_3mm_tolerance_each_side_pass']=all(a+6<=b for a,b in zip(r['bounds_mm'],[2100,1700,600]));results.append(q);App.closeDocument(doc.Name);print(c['id'],'native/STEP passed',flush=True)
(H/'Geometrie_Pruefung.json').write_text(json.dumps(results,indent=2))
