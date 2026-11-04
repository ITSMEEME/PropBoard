"""Quantified reference changes,without modifying or certifying the D12 CAD."""
from pathlib import Path
import json,math,copy,numpy as np
from balken import arm_model,section
from threadpoolctl import threadpool_limits
threadpool_limits(1)
H=Path(__file__).resolve().parents[1];O=H/'Ausgabe/Festigkeit';cad=json.loads((O/'CAD_Geometrie.json').read_text());base=next(c for c in cad['configurations'] if c['propeller_index']==9 and c['variant']=='V4');F=2354.4;rows=[]
for od,di in [(20,17),(22,19),(25,21),(30,26)]:
 c=copy.deepcopy(base);oldmass=0;newmass=0
 for t in c['tubes']:
  oldmass+=section(t['od_mm'],t['id_mm'])[0]*t['length_mm']*1.6e-6;t['od_mm']=od;t['id_mm']=di;newmass+=section(od,di)[0]*t['length_mm']*1.6e-6
 m=arm_model(c,mesh_mm=25);m.nodes[m.foot]['dofs']=[2,3,4,5];m.assemble();r=m.result(m.foot,[0,0,F,0,0,0],buckling=True);a=[e for e in r['elements'] if e['tag'].startswith('arm')];rootpull=max(max(e['N_N'],0) for e in a if e['node_a'] in m.rootnodes);rows.append(dict(option='arm_diameter',od_mm=od,id_mm=di,arm_CFK_added_four_arms_kg=4*(newmass-oldmass),foot_displacement_mm=r['foot_displacement'][2],peak_arm_stress_MPa=max(max(x['tensile_demand_MPa'],x['compressive_demand_MPa']) for x in a),peak_root_pullout_N=rootpull,buckling_factor=r['linearized_buckling_factor'],note='Existing clamps/nodes/clearances do NOT fit changed sizes;model dimensions only,Al masses excluded.'))
# Route vertical landing load to the common motor node,not a single tube midspan.
m=arm_model(base,mesh_mm=25,include_legs=False);r=m.result(m.hub,[0,0,F,0,0,0],buckling=True);a=[e for e in r['elements'] if e['tag'].startswith('arm')];rows.append(dict(option='ideal_motor_node_load',peak_arm_stress_MPa=max(max(x['tensile_demand_MPa'],x['compressive_demand_MPa']) for x in a),hub_displacement_mm=r['foot_displacement'][2],buckling_factor=r['linearized_buckling_factor'],note='Ideal load introduction comparison only;no landing members,ground restraint or revised CAD.'))
# Reference A-frame with ideal pins at frame node and motor node;no bonded end moments.
foot=np.array([base['foot_centre'][0],0.,-268]);p0=np.array([0.,0.,0.]);p1=np.array(base['hub']);a=(p0-foot);b=(p1-foot);La=np.linalg.norm(a);Lb=np.linalg.norm(b);a/=La;b/=Lb;N=np.linalg.solve(np.array([[a[0],b[0]],[a[2],b[2]]]),[0,F]);hubload=np.r_[N[1]*b,[0,0,0]];m=arm_model(base,mesh_mm=25,include_legs=False);r=m.result(m.hub,hubload,buckling=True);arm=[e for e in r['elements'] if e['tag'].startswith('arm')];A,I,J=section(20,17);oldCFK=sum(x['length_mm'] for x in base['legs'])*A*1.6e-6
rows.append(dict(option='ideal_pinned_A_frame_reference',long_leg_mm=La,short_leg_mm=Lb,axial_leg_forces_N=N.tolist(),CFK_stress_MPa=(N/A).tolist(),pinned_Euler_factors=(math.pi**2*50000*I/np.array([La,Lb])**2/N).tolist(),hub_force_N=hubload[:3].tolist(),core_direct_force_N=(N[0]*a).tolist(),added_four_feet_CFK_only_kg=4*((La+Lb)*A*1.6e-6-oldCFK),peak_arm_stress_MPa=max(max(x['tensile_demand_MPa'],x['compressive_demand_MPa']) for x in arm),note='Concept reference only:rigid ideal frame/motor anchors and pins;clevis masses,side stability,contact,clearance,frame,bolts and joint capacities not qualified.No new CAD.No drop-in safe design.'))
(O/'Aenderungsoptionen.json').write_text(json.dumps(dict(native_sha256=cad['native_sha256'],qualified=False,scope='Reference sensitivities to locate effective redesign levers;does not replace D12 or constitute production geometry.',options=rows),indent=2));print(json.dumps(rows,indent=2))
