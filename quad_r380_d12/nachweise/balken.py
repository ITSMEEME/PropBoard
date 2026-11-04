"""3-D linear Timoshenko beam FE, rigid offsets and optional joint springs.
Units N, mm, rad. E_long and G are independent equivalent section parameters;
this is not a ply-resolved composite failure or contact analysis.
"""
import numpy as np
from scipy.linalg import cho_factor,cho_solve,eigh
import math

def skew(v):
 x,y,z=v;return np.array([[0,-z,y],[z,0,-x],[-y,x,0.]])

def section(od,di):
 A=math.pi/4*(od**2-di**2);I=math.pi/64*(od**4-di**4);return A,I,2*I

def beam(a,b,E,G,od,di,kappa=.5,bending_scale=1.):
 a=np.asarray(a,float);b=np.asarray(b,float);ex=(b-a)/np.linalg.norm(b-a);ref=np.array([0.,0.,1.]) if abs(ex[2])<.9 else np.array([0.,1.,0.]);ey=np.cross(ref,ex);ey/=np.linalg.norm(ey);ez=np.cross(ex,ey);Q=np.array([ex,ey,ez]);T=np.zeros((12,12))
 for i in [0,3,6,9]:T[i:i+3,i:i+3]=Q
 L=float(np.linalg.norm(b-a));A,I,J=section(od,di);EI=E*I*bending_scale;phi=12*EI/(kappa*G*A*L**2);k=np.zeros((12,12))
 for ids,s in [([0,6],E*A/L),([3,9],G*J*bending_scale/L)]:k[np.ix_(ids,ids)]+=s*np.array([[1.,-1],[-1,1]])
 kb=EI/(L**3*(1+phi))*np.array([[12,6*L,-12,6*L],[6*L,(4+phi)*L**2,-6*L,(2-phi)*L**2],[-12,-6*L,12,-6*L],[6*L,(2-phi)*L**2,-6*L,(4+phi)*L**2]])
 for ids,s in [([1,5,7,11],np.ones(4)),([2,4,8,10],np.array([1,-1,1,-1]))]:k[np.ix_(ids,ids)]+=s[:,None]*kb*s[None,:]
 return dict(k=k,T=T,L=L,A=A,I=I,J=J,ro=od/2,E=E,G=G,Q=Q,axis=ex,bending_scale=bending_scale)

def geometric_local(e,N):
 L=e['L'];kg=np.zeros((12,12));g=N/(30*L)*np.array([[36,3*L,-36,3*L],[3*L,4*L**2,-3*L,-L**2],[-36,-3*L,36,-3*L],[3*L,-L**2,-3*L,4*L**2]])
 for ids,s in [([1,5,7,11],np.ones(4)),([2,4,8,10],np.array([1,-1,1,-1]))]:kg[np.ix_(ids,ids)]+=s[:,None]*g*s[None,:]
 return kg

class Model:
 def __init__(self):self.nodes=[];self.elements=[];self.springs=[]
 def node(self,p,kind='free',master=None):
  self.nodes.append(dict(p=np.asarray(p,float),kind=kind,master=master));return len(self.nodes)-1
 def element(self,i,j,E,G,od,di,tag,kappa=.5,bending_scale=1.):
  e=beam(self.nodes[i]['p'],self.nodes[j]['p'],E,G,od,di,kappa,bending_scale);e.update(i=i,j=j,tag=tag);self.elements.append(e);return len(self.elements)-1
 def assemble(self):
  cols={};nd=0
  for i,n in enumerate(self.nodes):
   dofs=range(6) if n['kind']=='free' else range(3,6) if n['kind'] in ['rootrot','slave_translation'] else []
   for d in n.get('dofs',dofs):cols[i,d]=nd;nd+=1
  self.nd=nd;R=np.zeros((6*len(self.nodes),nd));done=set()
  def fill(i):
   if i in done:return
   n=self.nodes[i];m=n['master']
   if m is not None:
    fill(m);A=np.eye(6);A[:3,3:]=-skew(n['p']-self.nodes[m]['p']);rr=A@R[6*m:6*m+6];R[6*i:6*i+6]=rr
    if n['kind']=='slave_translation':R[6*i+3:6*i+6]=0
   for d in range(6):
    if (i,d) in cols:R[6*i+d,cols[i,d]]=1
   done.add(i)
  for i in range(len(self.nodes)):fill(i)
  self.R=R;self.K=np.zeros((nd,nd))
  for e in self.elements:
   idx=list(range(6*e['i'],6*e['i']+6))+list(range(6*e['j'],6*e['j']+6));rr=R[idx];ids=np.flatnonzero(np.any(rr,axis=0));r=rr[:,ids];e['rr']=r;e['ids']=ids;e['rr_all']=rr;A=e['T']@r;self.K[np.ix_(ids,ids)]+=A.T@e['k']@A
  for i,j,k in self.springs:
   B=R[6*i+3:6*i+6]-(R[6*j+3:6*j+6] if j is not None else 0);self.K+=k*B.T@B
  self.scale=np.ones(nd)
  for (i,d),col in cols.items():
   if d>=3:self.scale[col]=.01
  Ks=self.scale[:,None]*self.K*self.scale[None,:];self.factor=cho_factor((Ks+Ks.T)/2,lower=True,check_finite=False)
 def solve(self,node,load):
  F=self.R[6*node:6*node+6].T@np.asarray(load);q=self.scale*cho_solve(self.factor,self.scale*F,check_finite=False);U=self.R@q;res=np.linalg.norm(self.K@q-F)/max(1,np.linalg.norm(F));assert res<1e-6,res
  return q,U.reshape(-1,6),F,res
 def result(self,node,load,buckling=False):
  q,u,F,res=self.solve(node,load);rows=[];nodal=np.zeros_like(u);KG=np.zeros_like(self.K)
  for e in self.elements:
   ud=np.r_[u[e['i']],u[e['j']]];f=e['k']@e['T']@ud;fg=e['T'].T@f;nodal[e['i']]+=fg[:6];nodal[e['j']]+=fg[6:];N=float((f[6]-f[0])/2);B=max(float(np.linalg.norm(f[4:6])),float(np.linalg.norm(f[10:12])));sig=N/e['A'];bend=B*e['ro']/e['I'];tau=abs(float(f[3]))*e['ro']/e['J']+2*float(np.linalg.norm(f[1:3]))/e['A'];rows.append(dict(tag=e['tag'],node_a=e['i'],node_b=e['j'],length_mm=e['L'],N_N=N,bending_Nmm=B,torsion_Nmm=abs(float(f[3])),tensile_demand_MPa=max(0,sig+bend),compressive_demand_MPa=max(0,-sig+bend),shear_demand_MPa=tau,local_end_forces=f.tolist(),global_end_forces=fg.tolist()))
   if buckling:
    A=e['T']@e['rr'];kg=geometric_local(e,N);ids=e['ids'];KG[np.ix_(ids,ids)]+=A.T@kg@A
  reaction=[];rf=np.zeros(3);rm=np.zeros(3)
  for i,n in enumerate(self.nodes):
   if n['kind'] in ['fixed','rootrot']:
    r=nodal[i].copy()
    if i==node:r-=np.asarray(load)
    reaction.append(dict(node=i,point_mm=n['p'].tolist(),force_N=r[:3].tolist(),moment_Nmm=r[3:].tolist()));rf+=r[:3];rm+=r[3:]+np.cross(n['p'],r[:3])
  applied=np.asarray(load);constraint=None
  if 'dofs' in self.nodes[node]:
   Fc=-rf-applied[:3];Mc=-rm-np.cross(self.nodes[node]['p'],applied[:3]+Fc)-applied[3:];constraint=np.r_[Fc,Mc]
   free=self.nodes[node]['dofs'];assert np.linalg.norm(constraint[free])/max(1,np.linalg.norm(applied))<1e-6
   rf+=Fc;rm+=Mc+np.cross(self.nodes[node]['p'],Fc)
  force_err=np.linalg.norm(rf+applied[:3])/max(1,np.linalg.norm(applied[:3]));moment_err=np.linalg.norm(rm+applied[3:]+np.cross(self.nodes[node]['p'],applied[:3]))/max(1,np.linalg.norm(rm));assert force_err<1e-6 and moment_err<1e-6,(force_err,moment_err)
  lam=None
  if buckling:
   L=np.tril(self.factor[0]);from scipy.linalg import solve_triangular
   G=-self.scale[:,None]*KG*self.scale[None,:];A=solve_triangular(L,G,lower=True,check_finite=False);B=solve_triangular(L,A.T,lower=True,check_finite=False).T;mu=eigh((B+B.T)/2,eigvals_only=True,check_finite=False);positive=mu[mu>1e-10];lam=float(1/max(positive)) if len(positive) else None
  maxlen=getattr(self,'characteristic_span',max(e['L'] for e in self.elements));disp=float(np.max(np.linalg.norm(u[:,:3],axis=1)));rotation=float(np.max(np.linalg.norm(u[:,3:],axis=1)));maxstrain=max(max(r['tensile_demand_MPa'],r['compressive_demand_MPa'])/e['E'] for r,e in zip(rows,self.elements));return dict(foot_displacement=u[node].tolist(),max_node_translation_mm=disp,max_rotation_rad=rotation,max_equivalent_longitudinal_strain=maxstrain,elements=rows,reactions=reaction,normalized_equilibrium_residual=res,force_balance_error=force_err,moment_balance_error=moment_err,linearized_buckling_factor=lam,ground_constraint_reaction=(constraint.tolist() if constraint is not None else None),linear_model_extrapolated=bool(rotation>math.radians(5) or disp>0.05*maxlen or maxstrain>.005),_q=q,_u=u)

def arm_model(c,E=50000.,G=3000.,mesh_mm=40.,root_rot_Nmm=None,bond_rot_Nmm=None,grip_EI_scale=1.,include_legs=True):
 M=Model();hub=M.node(c['hub']);foot=M.node(c['foot_centre']);clampnodes={};rootnodes=[]
 if not include_legs:M.nodes[foot]['kind']='fixed'
 for j,t in enumerate(c['tubes']):
  a=np.asarray(t['a']);b=np.asarray(t['b']);d=(b-a)/np.linalg.norm(b-a);a=a+35*d;b=b-35*d;L=np.linalg.norm(b-a);breaks=[0.,L];scl=[]
  if j==c['support_tube_index']:
   for ci,cl in enumerate(c['clamps']):
    x=float(np.dot(np.asarray(cl['clamp_centre'])-a,d));scl.append((x,ci));breaks.extend([x,x-16,x+16])
  breaks=sorted(set(round(x,9) for x in breaks if -1e-6<=x<=L+1e-6));ss=[]
  for lo,hi in zip(breaks[:-1],breaks[1:]):ss.extend(np.linspace(lo,hi,max(1,math.ceil((hi-lo)/mesh_mm))+1)[:-1])
  ss.append(L);ns=[]
  for k,s in enumerate(ss):
   p=a+s*d
   if k==0:
    n=M.node(p,'fixed' if root_rot_Nmm is None else 'rootrot');rootnodes.append(n)
    if root_rot_Nmm is not None:M.springs.append((n,None,root_rot_Nmm))
   elif k==len(ss)-1:n=M.node(p,'slave',hub)
   else:n=M.node(p)
   ns.append(n)
   for sc,ci in scl:
    if abs(s-sc)<1e-5:clampnodes[ci]=n
  for k,(n1,n2) in enumerate(zip(ns[:-1],ns[1:])):
   centre=(ss[k]+ss[k+1])/2;scale=grip_EI_scale if any(abs(centre-sc)<16 for sc,ci in scl) else 1.;M.element(n1,n2,E,G,t['od_mm'],t['id_mm'],f'arm{j}',bending_scale=scale)
 for ci,t in enumerate(c['legs'] if include_legs else []):
  bottom=np.asarray(t['a']);top=np.asarray(t['b']);L=np.linalg.norm(top-bottom);ns=[]
  for k,s in enumerate(np.linspace(0,1,max(1,math.ceil(L/mesh_mm))+1)):
   p=top+(bottom-top)*s
   if k==0:
    m=clampnodes[ci];n=M.node(p,'slave' if bond_rot_Nmm is None else 'slave_translation',m)
    if bond_rot_Nmm is not None:M.springs.append((n,m,bond_rot_Nmm))
   elif abs(s-1)<1e-9:
    n=M.node(p,'slave' if bond_rot_Nmm is None else 'slave_translation',foot)
    if bond_rot_Nmm is not None:M.springs.append((n,foot,bond_rot_Nmm))
   else:n=M.node(p)
   ns.append(n)
  for a,b in zip(ns[:-1],ns[1:]):M.element(a,b,E,G,t['od_mm'],t['id_mm'],f'leg{ci}')
 M.characteristic_span=max(t['length_mm']-70 for t in c['tubes']);M.hub=hub;M.foot=foot;M.clampnodes=clampnodes;M.rootnodes=rootnodes;M.assemble();return M
