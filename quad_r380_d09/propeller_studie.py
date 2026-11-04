"""HEP-S size screening from user diameter/pitch only; no invented OEM thrust maps."""
from pathlib import Path
import math,json,csv
H=Path(__file__).resolve().parent;O=H/'Ausgabe'
sizes=[(18,6.7),(22,7.2),(26,8.8),(28,9),(29,11),(30,10.5),(32,11),(34,11.5),(36,12),(42,16)];rho=1.225;configs=[];cases=[]
for diameter,pitch in sizes:
 D=diameter*.0254;area=4*math.pi*(D/2)**2;tag=f'HEP_S_{diameter}_{str(pitch).replace(".","p")}'
 # Conservative shared-frame rectangle at rotor height: x±393,y±120mm.
 # Coplanar neighboring rotor-edge clearance and frame clearance both20mm.
 R=D*500;gap=20;lo=max(R+gap/2,260);hi=1000
 for _ in range(70):
  h=(lo+hi)/2;distance=math.hypot(max(h-393,0),max(h-120,0))
  if distance<R+gap:lo=h
  else:hi=h
 h=max(420,math.ceil(hi/5)*5)
 cfg=dict(id=tag,label=f'HEP-S {diameter}×{pitch}',diameter_in=diameter,pitch_in=pitch,diameter_mm=D*1000,pitch_mm=pitch*25.4,radius_mm=R,motor_half_spacing_mm=h,unprotected_width_mm=2*h+D*1000,rotor_edge_gap_mm=2*h-D*1000,frame_rectangle_clearance_lower_bound_mm=math.hypot(max(h-393,0),max(h-120,0))-R,oem_shape_available=False,oem_performance_available=False,visualization='Rotor swept-space envelope only; not an OEM propeller solid')
 configs.append(cfg)
 for fm in [.55,.65,.75]:
  for minutes in [3,5,8]:
   dry=35;payload=100;mass=dry+payload;converged=False
   for _ in range(250):
    ideal=(mass*9.81)**1.5/math.sqrt(2*rho*area);shaft=ideal/fm;electric=shaft/.82;battery=electric*(minutes/60)/(150*.8);nextmass=dry+payload+battery
    if nextmass>1500:break
    if abs(nextmass-mass)<1e-7:converged=True;mass=nextmass;break
    mass=nextmass
   if converged:
    thrust=mass*9.81/4;cts={str(rpm):thrust/(rho*(rpm/60)**2*D**4) for rpm in [2434,2744,3000,3456,4032]};qs={str(rpm):shaft/4/(rpm*math.pi/30) for rpm in [2434,3000,3456,4032]}
    cases.append(dict(propeller=tag,figure_of_merit_assumed=fm,flight_minutes=minutes,total_mass_kg=mass,battery_mass_kg=battery,total_shaft_power_kW=shaft/1000,total_electric_power_kW=electric/1000,thrust_per_motor_N=thrust,required_CT_by_rpm=cts,required_torque_Nm_by_rpm=qs,within_4x_observed_80percent_shaft_power=shaft<=4*8915.97818096459,converged=True))
   else:cases.append(dict(propeller=tag,figure_of_merit_assumed=fm,flight_minutes=minutes,converged=False))
report=dict(configurations=configs,cases=cases,assumptions=dict(payload_kg=100,dry_vehicle_budget_kg=35,usable_pack_specific_energy_before_reserve_Wh_kg=150,energy_reserve_fraction=.2,motor_ESC_efficiency=.82,air_density_kg_m3=rho),comparison_point='4×8.916kW is the calculated shaft power of the observed MN1330 NS52 80%/10min point,not a universal motor power limit or an HEP-S approval.',diameter_pitch_only=True,blade_count_verified=False,positive_propeller_selections=[],scope='Actuator-disk lower bound plus assumed figure of merit,efficiency and battery feedback. CT requirements are target values to request from manufacturer,not inferred HEP-S coefficients. Pitch alone cannot determine thrust/torque/efficiency or rated RPM. No manufacturer profile,chord,twist or hub CAD supplied.20mm planning clearance is nominal and not a verified deflection allowance.')
(O/'Propeller_Studie.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));(H/'Konfigurationen.json').write_text(json.dumps(configs,indent=2,ensure_ascii=False))
rows=[]
for cfg in configs:
 c=next(c for c in cases if c['propeller']==cfg['id'] and c['figure_of_merit_assumed']==.65 and c['flight_minutes']==5)
 row=dict(propeller=cfg['label'],diameter_mm=cfg['diameter_mm'],width_mm=cfg['unprotected_width_mm'],motor_half_spacing_mm=cfg['motor_half_spacing_mm'],converged=c['converged'])
 if c['converged']:row.update(total_mass_kg=c['total_mass_kg'],battery_kg=c['battery_mass_kg'],shaft_per_motor_kW=c['total_shaft_power_kW']/4,CT_required_3000rpm=c['required_CT_by_rpm']['3000'],torque_required_3000rpm=c['required_torque_Nm_by_rpm']['3000'])
 rows.append(row);print(row,flush=True)
with (O/'Propeller_Vergleich.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=sorted({k for r in rows for k in r}));w.writeheader();w.writerows(rows)
