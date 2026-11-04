"""Physical lower bounds and conditional centrifugal loads, not a thrust map."""
import sys,json,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
P=json.loads((H/'parameter.json').read_text());S=json.loads((O/'Status.json').read_text());parts=json.loads((O/'Bauteile.json').read_text());rows=json.loads((O/'Instanzen.json').read_text());D=A.openDocument(str(O/'QuadR380_D06_Propeller.FCStd'));old=json.loads((H.parent/'quad_r380_d05/Ausgabe/MN1330_Betriebsgrenzen.json').read_text())
area=4*math.pi*.38**2;mass=S['mass_modeled_kg']+100;ideal=(mass*9.81)**1.5/math.sqrt(2*1.225*area)/1000
keys=['D06_BLADE_CCW','D06_CORE_1_CCW','D06_CORE_2_CCW'];total=sum(parts[k]['mass_kg'] for k in keys);first=[0,0,0]
for k in keys:
    row=next(r for r in rows if r['id']==k);s=D.getObject(row['instance']).LinkedObject.Shape
    for i,c in enumerate(s.Solids[0].CenterOfMass):first[i]+=parts[k]['mass_kg']*c
cg=[x/total for x in first];loads=[]
for rpm in [3000,3456,4032]:
    omega=rpm*math.pi/30;force=total*omega**2*math.hypot(cg[0],cg[1])*.001
    loads.append(dict(rpm=rpm,blade_body_centrifugal_resultant_N=force,tip_speed_m_s=omega*.38,tip_mach_at343m_s=omega*.38/343))
report=dict(native_sha256=S['native_sha256'],own_propeller_map_available=False,legacy_R380_hover_rpm_not_transferred=True,legacy_NS52x20_data_not_transferred=True,blade_geometry_origin=P['source_status'],series_cells_reference=24,ideal_no_load_full_rpm=old['ideal_no_load_full_rpm'],motor_continuous_rating_verified=False,ideal_hover_mass_with100kg_person_kg=mass,ideal_out_of_ground_effect_disk_area_m2=area,ideal_out_of_ground_effect_shaft_lower_bound_kW=ideal,ideal_hover_ignores_profile_swirl_and_electrical_losses=True,four3400W_reference_kW=13.6,motor_3400W_only180s_side_unknown=True,one_blade_skin_and_core_mass_kg=total,one_blade_skin_and_core_cg_mm=cg,conditional_centrifugal_cases=loads,centrifugal_scope='Only skin/root and foam bodies; assumed material densities. Conditional rigid-body loads at illustrative rpm including ideal no-load rpm, not approved operating speeds; no airloads, gravity, hub/bolts, fatigue, strength or laminate proof.',propeller_max_rpm_approved=None,motor_bearing_axial_load_verified=False,flight_release=False)
(O/'Betriebsgrenzen.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print('D06 ideal hover lower bound kW',ideal,'blade body mass',total)
