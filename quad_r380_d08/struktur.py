"""All-variant tube beam and clamp demand screening; no material qualification."""
from pathlib import Path
import numpy as np,json,math
H=Path(__file__).resolve().parent;O=H/'Ausgabe';R=H.parent
variants=json.loads((R/'motoranschluss_varianten/Varianten.json').read_text())[:4]
antrieb=json.loads((O/'Antriebsnachweis.json').read_text());cases=[]
def skew(v):
 x,y,z=v;return np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
for v in variants:
 rad=v['od']/2000;ri=v['di']/2000;area=math.pi*(rad**2-ri**2);I=math.pi/4*(rad**4-ri**4);J=2*I;hub=np.array([470*math.sqrt(2)-210,0,0])*.001
 for E,G in [(50e9,3e9),(70e9,5e9),(140e9,10e9)]:
  K=np.zeros((6,6));elements=[]
  for j,(start,end) in enumerate(zip(v['start'],v['end'])):
   a=np.array(start,dtype=float)*.001;b=np.array([end[0]-30+45*math.sqrt(2),end[1],min(end[2],-((v['od']+8)/2+8))])*.001;axis=b-a;axis/=np.linalg.norm(axis);a+=axis*.035;b-=axis*.035;L=np.linalg.norm(b-a);t=np.cross([0,0,1],axis);t/=np.linalg.norm(t);basis=np.column_stack((axis,t,np.cross(axis,t)));Q=np.zeros((6,6));Q[:3,:3]=basis.T;Q[3:,3:]=basis.T;k=np.zeros((6,6));k[0,0]=E*area/L;k[3,3]=G*J/L
   for u,theta,sign in [(1,5,-1),(2,4,1)]:k[u,u]=12*E*I/L**3;k[theta,theta]=4*E*I/L;k[u,theta]=k[theta,u]=sign*6*E*I/L**2
   T=np.eye(6);T[:3,3:]=-skew(b-hub);K+=T.T@Q.T@k@Q@T;elements.append((j,L,basis,Q,k,T,a,b))
  for mass,factor in [(150,1),(175,1),(175,1.5),(200,2)]:
   ref=next(x for x in antrieb['hover'] if x['mass_kg']==mass and x['polar']=='central');load=np.array([0,0,mass*9.81/4*factor,0,0,ref['torque_Nm']*factor]);u=np.linalg.solve(K,load);residual=np.linalg.norm(K@u-load);assert residual<1e-6;rods=[]
   for j,L,basis,Q,k,T,a,b in elements:
    local=k@Q@T@u;force=basis@local[:3];moment=basis@local[3:];root=basis.T@(moment+np.cross(b-a,force));bend=max(np.linalg.norm(root[1:]),np.linalg.norm(local[4:]));stress=abs(local[0])/area+bend*rad/I;torsion=max(abs(root[0]),abs(local[3]));friction_demand=math.hypot(local[0],torsion/rad);grip=.035;projected_pressure=(np.linalg.norm(local[1:3])/(2*rad*grip)+6*bend/(2*rad*grip**2))/1e6
    rods.append(dict(tube=j,free_length_mm=L*1000,root_force_N=local[:3].tolist(),root_moment_Nm=root.tolist(),axial_bending_stress_MPa=stress/1e6,torsional_shear_MPa=torsion*rad/J/1e6,projected_bearing_pressure_screen_MPa=projected_pressure,friction_resultant_demand_N=friction_demand,required_normal_force_N_by_mu={str(mu):friction_demand/mu for mu in [.1,.2,.3]},strength_pass=None,clamp_pass=None))
   cases.append(dict(variant=v['id'],E_GPa=E/1e9,G_GPa=G/1e9,total_mass_kg=mass,thrust_factor=factor,load=load.tolist(),hub_translation_mm=(u[:3]*1000).tolist(),hub_rotation_deg=(u[3:]*180/math.pi).tolist(),rods=rods,equilibrium_residual=residual))
report=dict(cases=cases,scope='Free tube spans between35mm grips; ideal fixed roots and rigid common motor node. E/G and friction coefficients are sensitivities,not identified CFK data. Equivalent-isotropic beam stress is not a laminate failure criterion. No global-frame/node compliance,contact solution,bolt prying,buckling,fatigue or landing shock.',clamp_model='Required friction normal force=sqrt(axial_force²+(tube_torsion/radius)²)/mu. Bearing-pressure screen=Ftrans/(D*L)+6*Mb/(D*L²),linear projected-contact approximation; not contact FEA and not an allowable.',material_verified=False,structure_release=False,clamp_release=False,proof_needed=['CFK orthotropic allowables and laminate','Clamp pressure/slip tests with actual PU/isolation','Bolt grade,friction,preload scatter and retention','Al node FEA,global frame,foot rails,indexing and fatigue','Dynamic modes and loaded rotor clearances'])
(O/'Struktur_Klemmnachweis.json').write_text(json.dumps(report,indent=2))
for c in cases:
 if c['E_GPa']==70 and c['total_mass_kg']==175 and c['thrust_factor']==1:print(c['variant'],'displacement mm',c['hub_translation_mm'],'peak stress MPa',max(x['axial_bending_stress_MPa'] for x in c['rods']),flush=True)
