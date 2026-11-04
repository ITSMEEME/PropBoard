"""Standardized project harness,all50 geometries;exact-circle bore/packing checks.
Specified cableODs are procurement maxima,not claimed measurements of OEM wires.
"""
from pathlib import Path
import json,math,hashlib,csv
H=Path(__file__).resolve().parent;R=H.parent;O=H/'Ausgabe';P=json.loads((H/'parameter.json').read_text());V=json.loads((R/'quad_r380_d10/Varianten.json').read_text());C=json.loads((R/'quad_r380_d10/Konfigurationen.json').read_text());maxL=C[-1]['motor_half_spacing_mm']*math.sqrt(2)-246

def layout(v):
 n=v['count'];dc=P['DC']['outer_diameter_design_max_mm'];can=P['CAN']['outer_diameter_design_max_mm'];pwm=P['PWM']['outer_diameter_design_max_mm'];service=P['SERVICE_5C']['outer_diameter_design_max_mm'];r=4.1;tri=[(r*math.cos(t),r*math.sin(t)) for t in [math.radians(210),math.radians(330),math.radians(90)]]
 if n==1:return [('DC_PLUS',0,-3.5,-6.,dc),('DC_MINUS',0,3.5,-6.,dc),('CAN',0,-3.75,4.,can),('PWM',0,0.,10.5,pwm),('SERVICE_5C',0,3.75,4.,service)]
 a=[('DC_PLUS',0,-3.5,0.,dc),('DC_MINUS',0,3.5,0.,dc)]
 if n==2:
  for net,pt,od in zip(['CAN','SERVICE_5C','PWM'],tri,[can,service,pwm]):a.append((net,1,*pt,od))
 else:a.extend([('CAN',1,-3.6,0.,can),('PWM',1,3.2,0.,pwm),('SERVICE_5C',2,0.,0.,service)])
 return a

def axis_geometry(v,c):
 L=c['motor_half_spacing_mm']*math.sqrt(2)-246;starts=v['start'];ends=[]
 for a,b in zip(starts,v['end']):
  target=[maxL,b[1],min(b[2],-(v['od']+8)/2-8)];ends.append([x+(y-x)*(L/maxL) for x,y in zip(a,target)])
 return starts,ends
rows=[];nets=[]
for ci,c in enumerate(C):
 for v in V:
  a=layout(v);liner=v['di']-.8;R0=liner/2;gaps=[];pairs=[];starts,ends=axis_geometry(v,c)
  for net,t,x,y,od in a:
   wall=R0-math.hypot(x,y)-od/2;gaps.append(wall);L=math.dist(starts[t],ends[t])+P['routing']['entry_tail_mm']+P['routing']['exit_tail_mm'];cut=P['routing']['project_extension_cut_length_mm'];needed=L+(P['routing']['external_root_allowance_DC_mm']+P['routing']['external_motor_allowance_DC_mm'] if net.startswith('DC_') else P['routing']['external_root_allowance_control_mm']+P['routing']['external_motor_connector_allowance_control_mm'])+P['routing']['assembly_slack_allowance_mm'];nets.append(dict(propeller_index=ci,variant=v['id'],net=net,tube=t,offset_xy_mm=[x,y],OD_design_max_mm=od,straight_model_length_mm=L,cut_length_mm=cut,external_service_and_slack_budget_mm=needed-L,remaining_length_budget_mm=cut-needed,cut_length_is_project_extension=(net not in ['DC_PLUS','DC_MINUS']),length_verified_to_real_OEM_ports=False))
  for i,z in enumerate(a):
   for w in a[i+1:]:
    if z[1]!=w[1]:continue
    gap=math.hypot(z[2]-w[2],z[3]-w[3])-(z[4]+w[4])/2;pairs.append(dict(a=z[0],b=w[0],tube=z[1],surface_gap_mm=gap))
  pmin=min([q['surface_gap_mm'] for q in pairs],default=1e9);minimum=min(min(gaps),pmin);worst_ID_min=16. if v['di']==17 else 31.;min_at_ID_min=min(worst_ID_min/2-math.hypot(x,y)-od/2 for net,t,x,y,od in a);passed=minimum>=.5-1e-9 and min_at_ID_min>=.5-1e-9 and min(n['remaining_length_budget_mm'] for n in nets if n['propeller_index']==ci and n['variant']==v['id'])>=0;assert passed,(ci,v['id'],minimum,min_at_ID_min)
  fill={str(j):sum(math.pi*(q[4]/2)**2 for q in a if q[1]==j)/(math.pi*R0**2) for j in range(v['count'])};rows.append(dict(propeller_index=ci,variant=v['id'],layout=[dict(net=n,tube=t,offset_xy_mm=[x,y],OD_design_max_mm=od) for n,t,x,y,od in a],nominal_liner_ID_mm=liner,nominal_minimum_surface_gap_mm=minimum,min_wall_gap_at_required_liner_ID_mm=min_at_ID_min,pair_gaps=pairs,area_fill_fraction_by_tube=fill,project_1200mm_length_budget_pass=passed,ports_bends_terminations_verified=False,passed_nominal_standard_envelope_checks=passed))
report=dict(source_structural_native_sha256=hashlib.sha256((R/'quad_r380_d12/Ausgabe/Quad_Reglerhalter_Landefuesse.FCStd').read_bytes()).hexdigest(),scope='Specified maximum cableODs,existing straight through-bores and liner geometry;pair and wall circles with tolerance reserve.Min_ID16mm is a procurement/inspection requirement,not measured tube data.1200mm cut lengths include allowances,not verified3D routes to actual OEM ports.',all50_passed=True,minimum_nominal_surface_gap_mm=min(r['nominal_minimum_surface_gap_mm'] for r in rows),configurations=rows,nets=nets,closed_harness=False,production_ready=False)
(O/'Kabelplanung.json').write_text(json.dumps(report,indent=2))
with (O/'Pinbelegung.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['project_interface','family','contact_number_or_label','project_net','OEM_mapping_verified'])
 for name,spec in P['interfaces'].items():
  for pin,net in spec['pins'].items():w.writerow([name,spec['family'],pin,net,False])
with (O/'Zuschnitt.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['variant','net','quantity_per_quad','stock_length_mm','OD_max_mm','status'])
 for v in V:
  for net,t,x,y,od in layout(v):w.writerow([v['id'],net,4,1200,od,'design/procurement maximum;OEMadapter mapping open'])
print('50 standard-envelope routes pass;minimum gap',report['minimum_nominal_surface_gap_mm'])
