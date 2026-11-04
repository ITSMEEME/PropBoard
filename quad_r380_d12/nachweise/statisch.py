"""All50 CAD configurations: beam demands, clamp wrench/preload envelopes and bond shear lag."""
from pathlib import Path
import json,math,csv,numpy as np
from threadpoolctl import threadpool_limits
threadpool_limits(1)
from balken import arm_model,section
H=Path(__file__).resolve().parents[1];O=H/'Ausgabe/Festigkeit';cad=json.loads((O/'CAD_Geometrie.json').read_text());rows=[];details=[];compliances=[]

def shear_lag(P,L,b,k,s1,s2):
 beta=math.sqrt(b*k*(s1+s2));ne=P*s2/(s1+s2);C=P-ne;D=(-ne-C*math.cosh(beta*L))/math.sinh(beta*L);x=np.linspace(0,L,301);N=ne+C*np.cosh(beta*x)+D*np.sinh(beta*x);tau=-beta*(C*np.sinh(beta*x)+D*np.cosh(beta*x))/b
 return dict(mean_MPa=abs(P)/(b*L),peak_MPa=float(np.max(np.abs(tau))),beta_per_mm=beta,transfer_integral_N=float(b*np.trapezoid(tau,x)),x_mm=x.tolist(),tau_MPa=tau.tolist())

def bond(wrench,E=50000,G=3000,L=29.7,Ga=1000,t=.2,deltaT=0):
 F=np.asarray(wrench[:3]);M=np.asarray(wrench[3:]);r=8.3;b=2*math.pi*r;Ac,Ic,Jc=section(20,17);Aa,Ia,Ja=section(16.6,12.6);N=abs(F[2]);V=float(np.linalg.norm(F[:2]));Mb=float(np.linalg.norm(M[:2]));T=abs(M[2]);effective=N+2*Mb/r
 a=shear_lag(effective,L,b,Ga/t,1/(E*Ac),1/(70000*Aa));tors=shear_lag(T,L,2*math.pi*r*r,(Ga/t)*r,1/(G*Jc),1/(26000*Ja))
 S=1/(E*Ac)+1/(70000*Aa);beta=a['beta_per_mm'];dalpha=20e-6;thermal_peak=abs(dalpha*deltaT/S*beta*math.tanh(beta*L/2)/b)
 return dict(axial_force_N=N,transverse_force_N=V,bending_moment_Nmm=Mb,torsion_Nmm=T,Ga_assumed_MPa=Ga,deltaT_assumed_K=deltaT,mean_axial_shear_MPa=N/(b*L),peak_axial_plus_bending_shear_MPa=a['peak_MPa'],peak_torsion_shear_MPa=tors['peak_MPa'],combined_shear_envelope_MPa=math.hypot(a['peak_MPa']+thermal_peak,tors['peak_MPa']),thermal_elastic_shear_peak_MPa=thermal_peak,radial_normal_idealization_MPa=V/(math.pi*r*L)+6*Mb/(math.pi*r*L*L),radial_free_thermal_mismatch_mm=abs(dalpha*deltaT*r),qualified=False)

def clamp(w,L,D,where):
 N=abs(w[0]);V=math.hypot(w[1],w[2]);T=abs(w[3]);Mb=math.hypot(w[4],w[5]);slip=math.hypot(N,T/(D/2));bearing=V/(D*L)+6*Mb/(D*L**2);Sp=580.;As=8.78;Fbolt=.7*Sp*As
 return dict(location=where,axial_friction_demand_N=N,tube_torsion_Nmm=T,resultant_slip_demand_N=slip,transverse_N=V,bending_Nmm=Mb,projected_bearing_screen_MPa=bearing,normal_force_required_N={str(mu):slip/mu for mu in [.1,.2,.35,.5]},two_M4_8p8_preload_each_assumed_N=Fbolt,uniform_ring_mean_preload_pressure_MPa=2*Fbolt/(D*L),friction_capacity_N_mu02_normal_factor1=.2*2*Fbolt,friction_capacity_N_mu02_normal_factorPi=.2*math.pi*2*Fbolt,required_mu_uniform_ring=slip/(math.pi*2*Fbolt),qualified=False)

def clean(r):return {k:v for k,v in r.items() if not k.startswith('_')}

for c in cad['configurations']:
 for mode,dofs in [('point',None),('stick',[2,3,4,5]),('flat',[2])]:
  model=arm_model(c,mesh_mm=35)
  if dofs is not None:model.nodes[model.foot]['dofs']=dofs;model.assemble()
  F=160*9.81*3/2;result=model.result(model.foot,[0,0,F,0,0,0],buckling=True);arms=[e for e in result['elements'] if e['tag'].startswith('arm')];legs=[e for e in result['elements'] if e['tag'].startswith('leg')];peak=max(max(e['tensile_demand_MPa'],e['compressive_demand_MPa']) for e in arms);R=result['ground_constraint_reaction'];mu=(math.hypot(R[0],R[1])/F if R is not None else 0.);copx=(-R[4]/F if R is not None else 0.);copy=(R[3]/F if R is not None else 0.);cop_ok=abs(copx)<=64 and abs(copy)<=14 # Necessary bounding rectangle check,not sufficient for the rounded footprint.
  summary=dict(propeller_index=c['propeller_index'],variant=c['variant'],contact_mode=mode,force_per_foot_N=F,E_MPa=50000,G_MPa=3000,foot_displacement_mm=result['foot_displacement'][2],peak_arm_tension_MPa=max(e['tensile_demand_MPa'] for e in arms),peak_arm_compression_MPa=max(e['compressive_demand_MPa'] for e in arms),peak_arm_shear_MPa=max(e['shear_demand_MPa'] for e in arms),required_longitudinal_allowable_with_study_factor1p5_MPa=1.5*peak,peak_leg_stress_MPa=max(max(e['tensile_demand_MPa'],e['compressive_demand_MPa']) for e in legs),linearized_buckling_factor=result['linearized_buckling_factor'],required_ground_mu=mu,ground_COP_x_mm=copx,ground_COP_y_mm=copy,COP_inside_necessary_rectangle=cop_ok,linear_model_extrapolated=result['linear_model_extrapolated'],maximum_rotation_deg=math.degrees(result['max_rotation_rad']),max_equivalent_strain=result['max_equivalent_longitudinal_strain'],force_balance_error=result['force_balance_error'],moment_balance_error=result['moment_balance_error'],qualified=False);rows.append(summary)
  if mode!='flat':
   # Vertical point stiffness at the current contact constraints, in N/mm.
   compliances.append(dict(propeller_index=c['propeller_index'],variant=c['variant'],mode=mode,k_vertical_N_mm=F/result['foot_displacement'][2],force_unit_response_stress_MPa_N=peak/F,buckling_force_N=(F*result['linearized_buckling_factor'] if result['linearized_buckling_factor'] else None),required_ground_mu=mu,COP_ok=cop_ok))
  if mode=='stick':
   joints=[];bonds=[]
   for j,t in enumerate(c['tubes']):
    elements=[e for e in result['elements'] if e['tag']==f'arm{j}'];first,last=elements[0],elements[-1]
    for where,element,w in [('root',first,first['local_end_forces'][:6]),('motor',last,last['local_end_forces'][6:])]:
     # Compression can bear on an existing end stop; friction must retain tensile pullout and torsion.
     Npull=max(element['N_N'],0);ww=list(w);ww[0]=Npull;joints.append(clamp(ww,35,t['od_mm'],f'{where}_tube{j}'))
   for ci in [0,1]:
    el=[e for e in result['elements'] if e['tag']==f'leg{ci}'];top,bottom=el[0],el[-1];f=np.array(top['global_end_forces'][:6]);p=model.nodes[top['node_a']]['p'];centre=np.array(c['clamps'][ci]['clamp_centre']);w=-f.copy();w[3:]+=np.cross(p-centre,w[:3]);tube=c['tubes'][c['support_tube_index']];axis=np.array(tube['b'])-tube['a'];axis/=np.linalg.norm(axis);ey=np.cross([0,0,1],axis);ey/=np.linalg.norm(ey);basis=np.array([axis,ey,np.cross(axis,ey)]);local=np.r_[basis@w[:3],basis@w[3:]];joints.append(clamp(local,32,tube['od_mm'],f'landing_clamp{ci}'))
    for end,wr in [('top',top['global_end_forces'][:6]),('bottom',bottom['global_end_forces'][6:])]:bonds.append(dict(leg=ci,end=end,wrench_N_Nmm=wr,scenarios=[bond(wr,Ga=ga,deltaT=dt) for ga,dt in [(150,0),(500,0),(1000,0),(1500,0),(1000,40),(1000,60)]]))
   details.append(dict(propeller_index=c['propeller_index'],variant=c['variant'],F_per_foot_N=F,contact_mode=mode,clamps=joints,bonds=bonds,FE_result=clean(result)))
 print('Static',c['propeller_index'],c['variant'],flush=True)

# Quantify joint, root stiffness, modulus, local clamp stiffening and tolerance sensitivity at V4/42.
base=next(c for c in cad['configurations'] if c['propeller_index']==9 and c['variant']=='V4');sensitivity=[]
for name,E,G,root,bondk,grip,oddelta in [('E30',30000,2000,None,None,1,0),('E50',50000,3000,None,None,1,0),('E70',70000,5000,None,None,1,0),('root1e5',50000,3000,1e5,None,1,0),('root1e6',50000,3000,1e6,None,1,0),('bond1e4',50000,3000,None,1e4,1,0),('bond1e6',50000,3000,None,1e6,1,0),('grip_EI10',50000,3000,None,None,10,0),('OD_minus0p2',50000,3000,None,None,1,-.2),('OD_plus0p2',50000,3000,None,None,1,.2)]:
 c=json.loads(json.dumps(base))
 for t in c['tubes']+c['legs']:t['od_mm']+=oddelta
 m=arm_model(c,E,G,mesh_mm=25,root_rot_Nmm=root,bond_rot_Nmm=bondk,grip_EI_scale=grip);m.nodes[m.foot]['dofs']=[2,3,4,5];m.assemble();r=m.result(m.foot,[0,0,2354.4,0,0,0],buckling=True);a=[e for e in r['elements'] if e['tag'].startswith('arm')];sensitivity.append(dict(name=name,E_MPa=E,G_MPa=G,root_rotation_spring_Nmm_rad=root,bond_rotation_spring_Nmm_rad=bondk,grip_EI_factor=grip,OD_delta_mm=oddelta,displacement_mm=r['foot_displacement'][2],peak_arm_stress_MPa=max(max(e['tensile_demand_MPa'],e['compressive_demand_MPa']) for e in a),buckling_factor=r['linearized_buckling_factor'],extrapolated=r['linear_model_extrapolated']))
# An explicit oblique contact wrench,without additional fixed-foot constraints swallowing lateral load.
lateral=[]
for direction in [0,1]:
 for ratio in [.1,.2,.3]:
  m=arm_model(base,mesh_mm=25);f=np.zeros(6);f[2]=2354.4;f[direction]=ratio*f[2];f[3]=8*f[1];f[4]=-8*f[0];r=m.result(m.foot,f,buckling=True);a=[e for e in r['elements'] if e['tag'].startswith('arm')];lateral.append(dict(force_ratio=ratio,direction=('radial' if direction==0 else 'tangential'),load_N_Nmm=f.tolist(),peak_arm_stress_MPa=max(max(e['tensile_demand_MPa'],e['compressive_demand_MPa']) for e in a),foot_u=r['foot_displacement'],buckling_factor=r['linearized_buckling_factor'],extrapolated=r['linear_model_extrapolated']))
# Independent integral check of the shear-lag transfer model.
x=shear_lag(1000,29.7,2*math.pi*8.3,1000/.2,1/(50000*section(20,17)[0]),1/(70000*section(16.6,12.6)[0]));assert abs(x['transfer_integral_N']/1000-1)<.001
for name,value in [('Statik_Uebersicht.json',dict(native_sha256=cad['native_sha256'],material_verified=False,qualified=False,study_factor=1.5,scope='Linear equivalent-orthotropic section beam model;ideal rigid vehicle roots/motor nodes except explicit sensitivities;ground modes are bounds requiring friction/COP checks;no laminate strength criterion or contact stress solution.',cases=rows,sensitivities=sensitivity,lateral_cases=lateral)),('Verbindungen.json',dict(native_sha256=cad['native_sha256'],qualified=False,bolt_property_class_assumed='8.8,not verified as installed',clamp_normal_factor_bounds=[1,math.pi],pressure_scope='Linear projected pressure F/(D L)+6M/(D L²);uniform split-ring preload proxy p=2Fbolt/(D L),not contact FEA. Full normal pressure integral varies with actual contact;factor pi assumes uniform full-ring pressure.',bond_scope='Elastic cylindrical Volkersen shear-lag;axial+bending traction envelope and torsion;full compression conservatively assigned to bond despite face bearing.Thermal model deltaCTE20e-6/K assumed.Radial-normal expression is a separate idealized load path,not a computed edge-peel maximum.No cohesive failure/laminate delamination/adhesive plasticity/cure/aging model.',cases=details)),('Federdaten.json',dict(native_sha256=cad['native_sha256'],cases=compliances))]:
 (O/name).write_text(json.dumps(value,indent=2))
with (O/'Statik_Uebersicht.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('Static study completed',len(rows),'conditions; no release',flush=True)
