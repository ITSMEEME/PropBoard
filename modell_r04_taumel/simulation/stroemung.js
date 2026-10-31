/* Strömungsdarstellung für den H01/P10-Simulator: Partikel und Schnittfeld aus dem reduzierten
 * Impulsmodell des Simulators (induzierte Geschwindigkeit je Rotor, Drall aus Rotormoment).
 * Keine CFD und kein zusätzlicher Physiklöser: die Partikel wirken nicht auf das Fahrzeug zurück.
 *
 * Achsiales Profil je Aktuatorscheibe (klassische Wirbelzylinder-Näherung auf der Achse):
 *   v_ax(d) = v_i · (1 + d/√(d²+R²)),  d = Abstand stromab der Scheibe
 * → 0 weit stromauf, v_i in der Scheibe, 2 v_i im fernen Nachlauf. Radiale Geschwindigkeit aus der
 * Kontinuität (v_r = −r/2 · ∂v_z/∂z) erzeugt die Strahleinschnürung auf R/√2. Drall unterhalb der
 * Scheibe aus der Drehimpulsbilanz ω = 2Q/(ρ A v_ax R²). Bodennähe: Umlenkung in radiale Abströmung. */
(function(root){'use strict';
const R=.1875,R0=.048,RHO=1.225,AREA=Math.PI*(R*R-R0*R0),Z_DISC=[.03,-.03];
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
function qrot(q,v){const[w,x,y,z]=q,ix=w*v[0]+y*v[2]-z*v[1],iy=w*v[1]+z*v[0]-x*v[2],iz=w*v[2]+x*v[1]-y*v[0],iw=-x*v[0]-y*v[1]-z*v[2];return[ix*w+iw*-x+iy*-z-iz*-y,iy*w+iw*-y+iz*-x-ix*-z,iz*w+iw*-z+ix*-y-iy*-x];}
const qconj=q=>[q[0],-q[1],-q[2],-q[3]];
/** Induced velocity in the body (CAD) frame [m/s] at body point b [m]. state: {vi:[u,l], Q:[u,l], sense:[+1,-1]} */
function inducedBody(b,state){const R=(state.geometry?.r_tip||187.5)/1000,R0=(state.geometry?.r_airfoil_start||48)/1000,AREA=Math.PI*(R*R-R0*R0),Z_DISC=[(state.spacing??.06)/2,-(state.spacing??.06)/2];const r=Math.hypot(b[0],b[1]);let vz=0,vr=0,omega=0;
 for(let l=0;l<2;l++){const vi=Math.max(0,state.vi[l]||0);if(vi<1e-3)continue;const d=Z_DISC[l]-b[2],s=Math.sqrt(d*d+R*R),f=1+d/s,fp=R*R/(s*s*s);
  const rt=R*Math.sqrt(1/Math.max(f,.12)),w=1/(1+Math.pow(r/rt,8)),va=vi*f*w;vz-=va;vr-=.5*r*vi*fp*w;
  if(d>0){const q=Math.abs(state.Q?.[l]||0),wake=2*q/(RHO*AREA*Math.max(.5,vi*f)*R*R);omega+=(state.sense?.[l]??(l?-1:1))*wake*clamp(d/.02,0,1)*w;}}
 const er=r>1e-9?[b[0]/r,b[1]/r]:[0,0],et=[-er[1],er[0]];
 return[vr*er[0]+omega*r*et[0],vr*er[1]+omega*r*et[1],vz];}
function rng(seed){let s=seed>>>0;return()=>{s=(1664525*s+1013904223)>>>0;return s/4294967296;};}
class ParticleField{
 constructor(count=2400,seed=7){this.n=count;this.rand=rng(seed);this.p=new Float32Array(3*count);this.prev=new Float32Array(3*count);this.age=new Float32Array(count);this.life=new Float32Array(count);this.speed=new Float32Array(count);this.ready=false;}
 spawn(i,vehicle){const R=(vehicle.geometry?.r_tip||187.5)/1000,top=(vehicle.spacing??.06)/2;const rand=this.rand,a=2*Math.PI*rand(),near=rand()<.35,rr=(near?1.05:1.5)*R*Math.sqrt(rand()),zb=near?top+.005+.03*rand():top+.03+.28*rand();
  const b=[rr*Math.cos(a),rr*Math.sin(a),zb],w=qrot(vehicle.q,[b[0]-vehicle.cg[0],b[1]-vehicle.cg[1],b[2]-vehicle.cg[2]]);
  for(let k=0;k<3;k++){this.p[3*i+k]=vehicle.p[k]+w[k];this.prev[3*i+k]=this.p[3*i+k];}this.age[i]=0;this.life[i]=1.2+2.2*rand();this.speed[i]=0;}
 /** Advance particles by dt [s] of simulated time. vehicle: {p,q,cg,v,wind,vi,Q,sense,groundZ} */
 step(vehicle,dt){if(!this.ready){for(let i=0;i<this.n;i++){this.spawn(i,vehicle);this.age[i]=this.life[i]*this.rand();}this.ready=true;}
  const qi=qconj(vehicle.q),wind=vehicle.wind||[0,0,0],gz=vehicle.groundZ??null,sub=Math.max(1,Math.ceil(dt/.004)),h=dt/sub;
  for(let i=0;i<this.n;i++){let x=this.p[3*i],y=this.p[3*i+1],z=this.p[3*i+2];this.prev[3*i]=x;this.prev[3*i+1]=y;this.prev[3*i+2]=z;let v=[0,0,0];
   for(let k=0;k<sub;k++){const rel=qrot(qi,[x-vehicle.p[0],y-vehicle.p[1],z-vehicle.p[2]]),b=[rel[0]+vehicle.cg[0],rel[1]+vehicle.cg[1],rel[2]+vehicle.cg[2]];
    v=qrot(vehicle.q,inducedBody(b,vehicle));v=[v[0]+wind[0],v[1]+wind[1],v[2]+wind[2]];
    if(gz!==null&&z-gz<.05&&v[2]<0){const dx=x-vehicle.p[0],dy=y-vehicle.p[1],L=Math.hypot(dx,dy)||1,s=-v[2]*.9;v=[v[0]+s*dx/L,v[1]+s*dy/L,v[2]*.05];}
    x+=v[0]*h;y+=v[1]*h;z+=v[2]*h;if(gz!==null&&z<gz+.002)z=gz+.002;}
   this.p[3*i]=x;this.p[3*i+1]=y;this.p[3*i+2]=z;this.speed[i]=Math.hypot(...v);this.age[i]+=dt;
   const far=Math.hypot(x-vehicle.p[0],y-vehicle.p[1],z-vehicle.p[2])>1.6;if(this.age[i]>this.life[i]||far)this.spawn(i,vehicle);}}
}
/** Speed magnitude on a body-frame x–z slice through the rotor axis. Returns Float32Array nx*nz [m/s]. */
function sliceField(state,nx=48,nz=64,x0=-.36,x1=.36,z0=-.55,z1=.30){const out=new Float32Array(nx*nz);
 for(let j=0;j<nz;j++)for(let i=0;i<nx;i++){const b=[x0+(x1-x0)*(i+.5)/nx,0,z0+(z1-z0)*(j+.5)/nz],v=inducedBody(b,state);out[j*nx+i]=Math.hypot(...v);}return{data:out,nx,nz,x0,x1,z0,z1};}
const api={inducedBody,ParticleField,sliceField,R,Z_DISC};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.H01Stroemung=api;
})(globalThis);
