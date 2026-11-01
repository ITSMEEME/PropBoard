#!/usr/bin/env python3
"""Meaningful regression: native spreadsheet propagation, save/restore and invalid states."""
import argparse,json,sys,tempfile,math
from pathlib import Path
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as A
from parameter_schema import load,validate,ParameterError,SCHEMA
import parametrik
from erstellen import collisions
H=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--native',type=Path,default=H/'Ausgabe/P12_MN1330.FCStd');a=ap.parse_args();p=load(H/'parameter.json');tests=[]
    for values in [{'rotor_radius':650},{'level_spacing':300},{'blade_count':6,'blade_chord':140},{'blade_count':10,'blade_chord':90},{'blade_taper':.75,'blade_twist':-5},{'groove_angle':100}]:
        validate(p|values);tests.append(dict(test='valid_parameter_combination',values=values,passed=True))
    for values in [{'rotor_radius':100},{'blade_count':8.5},{'blade_root':800},{'guide_angle_3':205},{'motor_face_offset':70},{'bearing_od':48},{'beam_wall':40},{'stator_head_depth':12},{'groove_angle':60},{'frame_beam_y':180}]:
        try:validate(p|values)
        except ParameterError:pass
        else:raise AssertionError(('invalid inputs accepted',values))
        tests.append(dict(test='invalid_parameter_combination_rejected',values=values,passed=True))
    d=A.openDocument(str(a.native));model=d.getObject('P12_Modell')
    assert isinstance(model.Proxy,parametrik.Model)
    assert len(model.ExpressionEngine)==len(SCHEMA)
    assert json.loads(model.LastValidParameters)==p
    def objs():return [o for o in d.Objects if 'P12Key' in o.PropertiesList]
    def part(id):return next(o for o in objs() if o.BauteilID==id)
    baseline_count=len(objs());track=part('P12-014');r0=track.Shape.BoundBox.XLength/2
    parametrik.set_values(d,{'rotor_radius':650,'level_spacing':300,'blade_count':6,'blade_taper':.8,'blade_twist':-4,'upper_phase':17,'lower_phase':33})
    q=json.loads(model.DerivedJSON);assert abs(q['height']-(836 if p['frame_mode']==1 else 872))<1e-8;assert q['guide_ring_outer']<850 if p['frame_mode']==1 else abs(q['guide_ring_outer']-860)<1e-8
    assert abs(part('P12-014').Shape.BoundBox.XLength/2-(r0-100))<1e-6
    assert sum(o.BauteilID=='REF-FLUEGEL' for o in objs())==12
    assert sum(o.BauteilID=='P12-004' for o in objs())==12
    assert len(objs())==baseline_count-8
    post=next(o for o in objs() if o.P12Key=='Oben_Distanz_1').Shape.Solids[0].CenterOfMass
    assert abs(math.degrees(math.atan2(post.y,post.x))-17)<1e-7
    assert all(o.Shape.isValid() and len(o.Shape.Solids)==1 for o in objs())
    hit=collisions(objs());assert not hit,hit
    tests.append(dict(test='native_spreadsheet_changes_radius_gap_count_taper_twist_and_all_mating_parts',passed=True,parts=len(objs())))
    valid_hash=model.LastValidHash;old_volume=part('P12-014').Shape.Volume
    try:parametrik.set_values(d,{'guide_angle_3':205})
    except ValueError:pass
    else:raise AssertionError('Invalid native spreadsheet accepted')
    assert model.Error and model.LastValidHash==valid_hash and abs(part('P12-014').Shape.Volume-old_volume)<1e-6
    assert 'UNGUELTIG' in model.P12Status
    parametrik.set_values(d,{'guide_angle_3':330});assert not model.Error
    tests.append(dict(test='invalid_native_input_keeps_last_good_geometry_with_explicit_error_status',passed=True))
    with tempfile.TemporaryDirectory(prefix='p12-native-') as temp:
        dest=Path(temp)/'Variant.FCStd';d.saveAs(str(dest));A.closeDocument(d.Name);d=A.openDocument(str(dest));model=d.getObject('P12_Modell')
        assert isinstance(model.Proxy,parametrik.Model)
        parametrik.set_values(d,{'motor_length':80})
        q=json.loads(model.DerivedJSON);assert abs(q['height']-(864 if p['frame_mode']==1 else 900))<1e-8
        assert abs(part('REF-MN1330').Shape.BoundBox.ZLength-80)<1e-8
        assert model.InstanceCount==baseline_count-8
    tests.append(dict(test='saved_native_variant_restores_proxy_and_remains_editable',passed=True))
    result=dict(passed=True,tests=tests,parameter_count=len(SCHEMA),scope='native model and selected variants, not structural or full motion qualification')
    (H/'Ausgabe/Parametrik_Pruefung.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'passed':True,'tests':len(tests),'parameters':len(SCHEMA)}))
if __name__=='__main__':main()
