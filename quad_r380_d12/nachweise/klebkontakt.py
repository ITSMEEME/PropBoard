"""Reduced cylindrical bond N/M shear-lag with unilateral CFK/GFK end bearing.
Two adherends with axial EA and bending EI fields; interfacial longitudinal shear.
Not a3D peel/cohesive/laminate model. Contact face stiffness is a sensitivity.
"""
from pathlib import Path
import numpy as np,json,math
from scipy.linalg import cho_factor,cho_solve
from threadpoolctl import threadpool_limits
threadpool_limits(1)
from balken import section
H=Path(__file__).resolve().parents[1];O=H/'Ausgabe/Festigkeit';D=json.loads((O/'Verbindungen.json').read_text());base=next(c for c in D['cases'] if c['propeller_index']==9 and c['variant']=='V4')

def solve(N,M,Ga=1000.,dt=0.,Eface=10000.,n=80,face=True):
 L=29.7;r=8.3;Ac,Ic,_=section(20,17);Aa,Ia,_=section(16.6,12.6);EAc=50000*Ac;EAa=70000*Aa;EIc=50000*Ic;EIa=70000*Ia;h=L/n;nd=4*(n+1);K=np.zeros((nd,nd));F=np.zeros(nd);F[0]=N;F[1]=M;kN=2*math.pi*r*Ga/.2;kM=math.pi*r**3*Ga/.2
 for i in range(n):
  for j,EA,alpha in [(0,EAc,3e-6),(1,EIc,0),(2,EAa,23e-6),(3,EIa,0)]:
   ids=[4*i+j,4*(i+1)+j];K[np.ix_(ids,ids)]+=EA/h*np.array([[1,-1],[-1,1]]);F[ids]+=EA*alpha*dt*np.array([-1,1])
  W=h/6*np.array([[2,1],[1,2]])
  for j,k in [(0,kN),(1,kM)]:
   c=[4*i+j,4*(i+1)+j];a=[4*i+j+2,4*(i+1)+j+2];K[np.ix_(c,c)]+=k*W;K[np.ix_(a,a)]+=k*W;K[np.ix_(c,a)]-=k*W;K[np.ix_(a,c)]-=k*W
 fixed=[4*n+2,4*n+3];ids=np.setdiff1d(np.arange(nd),fixed);S=np.ones(nd);S[1::4]=.01;S[3::4]=.01;thetas=np.linspace(0,2*math.pi,64,endpoint=False);rface=math.sqrt(2*Ic/Ac);B=np.zeros((len(thetas),nd));B[:,4*n]=1;B[:,4*n+1]=rface*np.cos(thetas);kf=Eface/.3*Ac/len(thetas);active=np.zeros(len(thetas),bool);q=np.zeros(nd)
 for step in range(30):
  Kc=K+(kf*B[active].T@B[active] if face else 0);Ks=S[:,None]*Kc*S[None,:];q[:]=0;q[ids]=S[ids]*cho_solve(cho_factor(Ks[np.ix_(ids,ids)],lower=True),S[ids]*F[ids]);nextactive=(B@q)>1e-12
  if not face or np.array_equal(active,nextactive):break
  active=nextactive
 else:raise RuntimeError('Contact active set did not converge')
 faceforce=kf*np.maximum(B@q,0) if face else np.zeros(len(thetas));faceN=float(np.sum(faceforce));faceM=float(np.dot(faceforce,rface*np.cos(thetas)));reaction=K@q-F;Nal=-reaction[4*n+2];Mal=-reaction[4*n+3]
 assert abs((faceN+Nal-N))/max(1,abs(N))<1e-6,(faceN,Nal,N);assert abs((faceM+Mal-M))/max(1,abs(M))<1e-6,(faceM,Mal,M)
 du=q[0::4]-q[2::4];dphi=q[1::4]-q[3::4];tau=Ga/.2*(np.abs(du)+r*np.abs(dphi));uA=q[2::4];pA=q[3::4];Nax=EAa*(np.diff(uA)/h-23e-6*dt);Mx=EIa*np.diff(pA)/h;spigot=np.abs(Nax)/Aa+np.abs(Mx)*r/Ia
 return dict(axial_force_N=N,bending_Nm=M/1000,Ga_assumed_MPa=Ga,deltaT_K=dt,end_GFK_E_assumed_MPa=Eface,contact_enabled=face,n_elements=n,face_compressive_force_N=faceN,face_moment_Nm=faceM/1000,Al_plug_force_N=Nal,Al_plug_moment_Nm=Mal/1000,peak_longitudinal_adhesive_shear_MPa=float(np.max(tau)),max_ideal_end_pressure_MPa=float(np.max(faceforce)/(Ac/len(thetas))),max_plug_longitudinal_MPa=float(np.max(spigot)),contact_fraction=float(np.mean(active)),contact_iterations=step+1,force_balance_error=abs(faceN+Nal-N)/max(1,abs(N)),moment_balance_error=abs(faceM+Mal-M)/max(1,abs(M)),face_only_model=False)

rows=[]
for b in base['bonds']:
 w=b['wrench_N_Nmm'];N=abs(w[2]);M=math.hypot(w[3],w[4])
 for ga,dt,Ef,face in [(150,0,10000,True),(500,0,10000,True),(1000,0,10000,True),(1500,0,10000,True),(1000,40,10000,True),(1000,-40,10000,True),(1000,0,1000,True),(1000,0,100000,True),(1000,0,10000,False)]:rows.append(dict(leg=b['leg'],end=b['end'],**solve(N,M,ga,dt,Ef,face=face)))
# Convergence and independent Volkersen axial/no-bearing check.
values=[solve(1074,65850,n=n) for n in [40,80,160]];err=abs(values[-1]['peak_longitudinal_adhesive_shear_MPa']/values[-2]['peak_longitudinal_adhesive_shear_MPa']-1);assert err<.01
r=solve(1000,0,n=160,face=False);ro=8.3;Ac,Ic,_=section(20,17);Aa,Ia,_=section(16.6,12.6);S1=1/(50000*Ac);S2=1/(70000*Aa);beta=math.sqrt(2*math.pi*ro*1000/.2*(S1+S2));Neq=1000*S2/(S1+S2);C=1000-Neq;DD=(-Neq-C*math.cosh(beta*29.7))/math.sinh(beta*29.7);analytic=max(abs(-beta*DD/(2*math.pi*ro)),abs(-beta*(C*math.sinh(beta*29.7)+DD*math.cosh(beta*29.7))/(2*math.pi*ro)));error=abs(r['peak_longitudinal_adhesive_shear_MPa']/analytic-1);assert error<.01
(O/'Klebung_Stirnkontakt.json').write_text(json.dumps(dict(native_sha256=D['native_sha256'],qualified=False,scope='Two-harmonic N/M shear-lag plus unilateral compressive end bearing;actual CFK/Al EA/EI,64 angular face springs;not3D cohesive,radial peel,local shoulder bending,hoop or delamination FE.Ga,Eface,CTE and temperatures are hypotheses.No actual strength allowable.',cases=rows,verification=dict(mesh_relative_peak_difference=err,independent_Volkersen_peak_error=error,passed=True),mesh_cases=values),indent=2));print('Refined bond contact study complete',len(rows));print([r for r in rows if r['leg']==0 and r['end']=='top' and r['Ga_assumed_MPa']==1000 and r['deltaT_K']==0])
