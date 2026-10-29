"""Analytical reference cases, not aerodynamic performance predictions."""
import json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
rho=1.225;nu=1.5e-5;g=9.80665;m=185.32;c=.12;span=.6
area=16*c*span
cases=[]
for speed in [10,30,50]:
    cases.append({'speed_m_s':speed,'Re_chord':speed*c/nu,
                  'q_Pa':.5*rho*speed**2,'CL_reference_required':m*g/(.5*rho*speed**2*area),
                  'a_vertical_m_s2':speed**2/.18,'a_horizontal_m_s2':speed**2/.45,
                  'a_vertical_g':speed**2/.18/g,'a_horizontal_g':speed**2/.45/g,
                  'tangent_rotation_vertical_rad_s':speed/.18,'tangent_rotation_horizontal_rad_s':speed/.45})
result={'scope':'Analytical illustrative conditions, no flight-scale CFD or closed mass model',
        'rho_kg_m3':rho,'nu_m2_s':nu,'g_m_s2':g,'illustrative_legacy_mass_kg':m,
        'required_hover_force_N':m*g,'geometrical_wing_area_m2':area,'cases':cases,
        'horizontal_curve':{'inner_wing_radius_m':.15,'centre_radius_m':.45,'outer_wing_radius_m':.75,
                            'inner_tip_speed_ratio':.15/.45,'outer_tip_speed_ratio':.75/.45,
                            'inner_guide_radius_m':.13,'outer_guide_radius_m':.77,
                            'outer_inner_guide_speed_ratio_on_curve':.77/.13},
        'forward_flight_m_s':80/3.6,'forward_flight_q_Pa':.5*rho*(80/3.6)**2}
(HERE/'Reale_Lastfaelle.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
