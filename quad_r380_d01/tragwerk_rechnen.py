"""Demand-only checks from the exact modeled arm section and declared load case."""
import sys,json,math
from pathlib import Path
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as A,Part
H=Path(__file__).resolve().parent;O=H/'Ausgabe';p=json.loads((H/'parameter.json').read_text());shape=Part.read(str(O/'Einzelteile/QD_R01.step'))
cut=shape.common(Part.makeBox(80,80,1,A.Vector(-40,-40,230)));Amm2=cut.Volume
solid=cut.Solids[0];I=solid.MatrixOfInertia.A11-Amm2/12
L=(math.sqrt(2)*p['motor_centres_half_spacing_mm']-p['arm_root_radius_mm'])/1000
F=p['design_mass_load_case_kg']*9.81*p['load_factor']/4;M=F*L;E=p['frame_E_assumed_Pa'];I_m4=I*1e-12
sigma=M*.025/I_m4/1e6;deflection=F*L**3/(3*E*I_m4)*1000
pitch=.060;extra_each=M/pitch/2;preload=p['root_bolt_preload_target_N'];proof=20.1*830
normal=4*preload;friction=2*normal*p['root_friction_assumed'];p_contact=normal/(50*95)
# The loose original insert is unacceptable at this preload. Fitted support is required.
strip_I=3**3/12;unsupported_roof_defl=p_contact*44**4/(384*(E/1e6)*strip_I)
unsupported_roof_sigma=p_contact*44**2/(2*3**2)
gap=p['arm_insert_face_clearance_max_mm'];sigma_at_support_contact=unsupported_roof_sigma*min(1,gap/unsupported_roof_defl)
out=dict(scope='Linear static demand screen. Exact nominal CAD arm section, homogeneous E. No full 3D contact/FEM, fatigue, local notch, tolerance or flight approval.',load_case_kg=p['design_mass_load_case_kg'],load_factor=p['load_factor'],arm=dict(unsupported_length_m=L,area_mm2=Amm2,exact_section_I_mm4=I,force_N=F,root_moment_Nm=M,nominal_bending_stress_MPa=sigma,tip_deflection_mm=deflection,assumed_E_Pa=E,assumed_Rp02_MPa=250,nominal_yield_ratio_under_assumption=250/sigma),root_joint=dict(bolt='ISO4762 M6 class10.9',preload_target_each_N=preload,moment_extra_each_N=extra_each,peak_tension_each_N=preload+extra_each,proof_load_reference_N=proof,remaining_preload_unloaded_row_each_N=preload-extra_each,friction_reference_N=friction,transverse_force_N=F,friction_force_ratio=friction/F,mean_nominal_contact_pressure_MPa=p_contact,preload_torque_K018_024_Nm=[.18*preload*.006,.24*preload*.006],scope='Two bolt rows 60mm apart, two bolts/row, no joint-stiffness or contact redistribution certification'),insert_support=dict(maximum_face_gap_mm=gap,free_roof_strip_deflection_mm=unsupported_roof_defl,free_roof_strip_stress_MPa=unsupported_roof_sigma,linear_strip_stress_at_first_support_MPa=sigma_at_support_contact,required='Root internal faces finish/measure 44.00..44.02mm along135mm, matched plug43.97±0.01; max face gap0.03mm. Preload contact must be validated; loose inserts prohibited.'),release_blockers=['Material certificates and actual section tolerances required','VDI2230 joint stiffness, preload scatter and fatigue unresolved','Contact verification of fitted tube inserts required','Gait, hard landing, rotor imbalance, gyroscopic, resonant and motor-failure loads not covered'])
(O/'Tragwerk_Lastscreen.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
