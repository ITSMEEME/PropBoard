"""Independent closed-form checks of the numerical beam implementation."""
from pathlib import Path
import sys,json,math
import numpy as np
from threadpoolctl import threadpool_limits
threadpool_limits(1)
from balken import Model,beam,section,arm_model
O=Path(__file__).resolve().parents[1]/'Ausgabe/Festigkeit';checks=[];E=50000.;G=3000.;D=20.;di=17.;L=500.;A,I,J=section(D,di)
def check(name,actual,expected,tol=1e-7):
 err=abs(actual-expected)/max(abs(expected),1e-12);assert err<tol,(name,actual,expected,err);checks.append(dict(name=name,actual=actual,expected=expected,relative_error=err,passed=True))
M=Model();a=M.node([0,0,0],'fixed');b=M.node([L,0,0]);M.element(a,b,E,G,D,di,'test');M.assemble()
for name,f,idx,expected in [('axial',[1000,0,0,0,0,0],0,1000*L/(E*A)),('bending_shear',[0,0,100,0,0,0],2,100*L**3/(3*E*I)+100*L/(.5*G*A)),('torsion',[0,0,0,10000,0,0],3,10000*L/(G*J))]:
 r=M.result(b,f);check(name,r['foot_displacement'][idx],expected)
e=beam([0,0,0],[L,30,80],E,G,D,di);theta=np.array([.001,-.002,.0005]);translation=np.array([.2,.3,.1]);u=np.r_[translation,theta,translation+np.cross(theta,np.array([L,30,80])),theta];f=e['k']@e['T']@u;energy=abs(float(u@e['T'].T@f));assert energy<1e-9;checks.append(dict(name='rigid_motion_energy',absolute_energy_Nmm=energy,limit_Nmm=1e-9,passed=True))
M=Model();a=M.node([0,0,0],'fixed');M.nodes[a]['dofs']=[4,5];b=M.node([L,0,0],'fixed');M.nodes[b]['dofs']=[4,5];mid=M.node([L/2,0,0]);M.element(a,mid,E,G,D,di,'test');M.element(mid,b,E,G,D,di,'test');M.assemble();r=M.result(mid,[0,0,100,0,0,0]);check('simply_supported_midpoint',r['foot_displacement'][2],100*L**3/(48*E*I)+100*L/(4*.5*G*A))
# Linear eigenvalue convergence to the shear-flexible pinned-column buckling load.
buckling=[]
for count in [10,20,40]:
 M=Model();ns=[]
 for i,x in enumerate(np.linspace(0,L,count+1)):
  n=M.node([x,0,0],'fixed' if i in [0,count] else 'free');ns.append(n)
  if i==0:M.nodes[n]['dofs']=[4,5]
  if i==count:M.nodes[n]['dofs']=[0,4,5]
 for a,b in zip(ns[:-1],ns[1:]):M.element(a,b,E,G,D,di,'column')
 M.assemble();r=M.result(ns[-1],[-1,0,0,0,0,0],buckling=True);buckling.append(r['linearized_buckling_factor'])
expected=1/(1/(math.pi**2*E*I/L**2)+1/(.5*G*A));check('Timoshenko_column_buckling',buckling[-1],expected,.01);checks.append(dict(name='buckling_mesh_convergence',values=buckling,relative_last_change=abs(buckling[-1]-buckling[-2])/buckling[-1],passed=abs(buckling[-1]-buckling[-2])/buckling[-1]<.01));assert checks[-1]['passed']
cad=json.loads((O/'CAD_Geometrie.json').read_text());c=next(c for c in cad['configurations'] if c['variant']=='V4' and c['propeller_index']==9);vals=[]
for mesh in [50,25,12.5]:
 M=arm_model(c,mesh_mm=mesh);r=M.result(M.foot,[0,0,2354.4,0,0,0],buckling=True);arm=[e for e in r['elements'] if e['tag'].startswith('arm')];vals.append(dict(mesh_mm=mesh,displacement_mm=r['foot_displacement'][2],peak_CFK_stress_MPa=max(max(e['tensile_demand_MPa'],e['compressive_demand_MPa']) for e in arm),buckling_factor=r['linearized_buckling_factor'],equilibrium_residual=r['normalized_equilibrium_residual']))
for key in ['displacement_mm','peak_CFK_stress_MPa','buckling_factor']:check('D12_mesh_'+key,vals[-1][key],vals[-2][key],.01)
(O/'Solver_Validierung.json').write_text(json.dumps(dict(passed=True,native_sha256=cad['native_sha256'],checks=checks,D12_mesh=vals,scope='Solver implementation verification against independent analytical solutions and mesh refinement;not experimental validation of material or joints.'),indent=2));print(json.dumps(vals,indent=2));print('All numerical verification checks passed')
