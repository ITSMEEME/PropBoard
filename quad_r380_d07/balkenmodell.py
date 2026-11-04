"""6-DOF linear V3 beam screening with ideal rigid nodes and assumed CFK moduli.

This is an Euler-Bernoulli end-stiffness model of the two exposed tube spans;
it is not a full-frame laminate/contact/buckling/fatigue proof.
"""
import json,math,hashlib
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent;O=H/'Ausgabe';P=json.loads((H/'parameter.json').read_text());arms=json.loads((O/'V3_Rohre.json').read_text());selected=[r for r in arms if r['angle_deg']==45];R=P['tube_od_mm']/2000;ri=P['tube_id_mm']/2000;area=math.pi*(R*R-ri*ri);I=math.pi/4*(R**4-ri**4);J=2*I;hub=np.array([425,425,88],float)*.001

def skew(v):
    x,y,z=v;return np.array([[0,-z,y],[z,0,-x],[-y,x,0]])

def solve(E,G,load):
    K=np.zeros((6,6));elements=[]
    for rod in selected:
        a=np.array(rod['cut_start_mm'],float)*.001;b=np.array(rod['cut_end_mm'],float)*.001;d=b-a;d/=np.linalg.norm(d);a+=d*.035;b-=d*.035;L=np.linalg.norm(b-a);t=np.cross([0,0,1],d);t/=np.linalg.norm(t);up=np.cross(d,t);basis=np.column_stack((d,t,up));Q=np.zeros((6,6));Q[:3,:3]=basis.T;Q[3:,3:]=basis.T;k=np.zeros((6,6));k[0,0]=E*area/L;k[3,3]=G*J/L
        for u,theta,sign in [(1,5,-1),(2,4,1)]:
            k[u,u]=12*E*I/L**3;k[theta,theta]=4*E*I/L;k[u,theta]=k[theta,u]=sign*6*E*I/L**2
        T=np.eye(6);T[:3,3:]=-skew(b-hub);kg=Q.T@k@Q;K+=T.T@kg@T;elements.append((rod,a,b,basis,Q,k,T))
    eig=np.linalg.eigvalsh(K);assert eig.min()>0;u=np.linalg.solve(K,np.array(load,float));reactions=[]
    for rod,a,b,basis,Q,k,T in elements:
        local=k@Q@T@u;force=basis@local[:3];tipmoment=basis@local[3:];rootmoment=tipmoment+np.cross(b-a,force);rootlocal=basis.T@rootmoment;bending=max(np.linalg.norm(rootlocal[1:]),np.linalg.norm(local[4:]));stress=abs(local[0])/area+bending*R/I;shear=abs(local[3])*R/J
        reactions.append(dict(side=rod['side'],free_length_mm=np.linalg.norm(b-a)*1000,local_tip_force_N=local[:3].tolist(),local_root_moment_Nm=rootlocal.tolist(),peak_axial_plus_bending_stress_MPa=stress/1e6,torsional_shear_stress_MPa=shear/1e6))
    residual=np.linalg.norm(K@u-np.array(load,float));assert residual<1e-7
    return dict(E_Pa=E,G_Pa=G,load_global_force_N=load[:3],load_global_moment_Nm=load[3:],hub_translation_mm=(u[:3]*1000).tolist(),hub_rotation_deg=(u[3:]*180/math.pi).tolist(),translation_magnitude_mm=np.linalg.norm(u[:3])*1000,rotation_magnitude_deg=np.linalg.norm(u[3:])*180/math.pi,rods=reactions,equilibrium_residual=residual,strength_pass=None)

cases=[]
for E,G in [(70e9,5e9),(140e9,10e9)]:
    for name,load in [('Vertikallast400N',[0,0,400,0,0,0]),('Motorreaktion20Nm',[0,0,0,0,0,20]),('Kombiniert400N20Nm',[0,0,400,0,0,20])]:cases.append(dict(name=name,**solve(E,G,load)))
report=dict(native_sha256=hashlib.sha256((O/'QuadR380_D07_V3.FCStd').read_bytes()).hexdigest(),selected_variant='V3',model='Two spatial Euler-Bernoulli tube end-stiffness elements; rigid motor node and perfectly clamped root/socket interfaces',cases=cases,actual_material_data_verified=False,allowable_stresses_MPa=None,allowable_deflection_mm=None,strength_release=False,full_frame_model=False,scope='Only the two free CFK spans,cut length387mm minus2x35mm grips,with actual motor-node eccentricity. Equivalent isotropic E/G are assumptions,not laminate data.400N and20Nm are comparison loads,not measured demands or approved operating limits. No global-frame/joint compliance,clamp slip/crushing,anisotropic laminate failure,local buckling,fatigue,dynamic amplification,thermal effects or safety factors. Both E and G doubled in second sensitivity case; no acceptable-deflection criterion specified.')
(O/'Balkenmodell.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
for c in cases:print(c['name'],c['E_Pa']/1e9,'GPa',round(c['translation_magnitude_mm'],2),'mm',round(c['rotation_magnitude_deg'],2),'deg',flush=True)
