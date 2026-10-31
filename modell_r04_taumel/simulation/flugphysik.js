/* H01 reduced-order rigid-blade 6DOF simulation. SI except CAD linkage mm/degrees.
 * Not CFD or a flight release. See README for model domain and unknowns. */
(function(root){'use strict';
const node=typeof module!=='undefined'&&module.exports;
const CAD=node?require('./modell_h01.json'):root.H01_MODEL;
const KIN=node?require('./kinematik.json'):root.H01_KINEMATICS;
const SERVO_PROFILES=node?require('./servo_profiles.json'):root.H01_SERVO_PROFILES;
const A=node?require('../../modell_r04/auslegung/antrieb.js'):root.R04Antrieb;
const P=node?require('../../kreis_r04/simulation/r04_physik.js'):root.R04Physik;
const PL=node?require('../aerodynamik/polar_lookup.js'):root.H01PolarLookup;
// Optional P10 revision data (servo brackets, ring-gear stage, harness, landing gear) exported from native CAD.
const P10=node?(()=>{try{return require('./p10_massen.json');}catch(e){return null;}})():root.H01_P10_MASSEN||null;
const D=Math.PI/180,G=9.81,clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const add=(a,b)=>a.map((v,i)=>v+b[i]),sub=(a,b)=>a.map((v,i)=>v-b[i]),scale=(a,s)=>a.map(v=>v*s),dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
function solve(a,b){a=a.map((r,i)=>[...r,b[i]]);let n=b.length;
 for(let i=0;i<n;i++){let k=i;for(let j=i+1;j<n;j++)if(Math.abs(a[j][i])>Math.abs(a[k][i]))k=j;[a[i],a[k]]=[a[k],a[i]];
 if(Math.abs(a[i][i])<1e-12)throw Error('Singular linkage/allocation matrix');let v=a[i][i];for(let j=i;j<=n;j++)a[i][j]/=v;
 for(let k=0;k<n;k++)if(k!==i){let s=a[k][i];for(let j=i;j<=n;j++)a[k][j]-=s*a[i][j];}}
 return a.map(r=>r[n]);}
const mv=(m,v)=>m.map(r=>dot(r,v));
function shiftInertia(J,m,d){for(let i=0;i<3;i++)for(let j=0;j<3;j++)J[i][j]+=m*((i===j?dot(d,d):0)-d[i]*d[j]);}
// Remove/add rigid components (CAD frame, SI) and re-express the full tensor about the new CG.
function recombine(mass,cg,J,remove,addList){let m=mass,mc=scale(cg,mass);for(const x of remove){m-=x.mass_kg;mc=sub(mc,scale(x.cg_m,x.mass_kg));}for(const x of addList){m+=x.mass_kg;mc=add(mc,scale(x.cg_m,x.mass_kg));}
 let c=scale(mc,1/m),K=J.map(r=>[...r]);shiftInertia(K,mass,sub(cg,c));
 for(const [list,sgn] of [[remove,-1],[addList,1]])for(const x of list){for(let i=0;i<3;i++)for(let j=0;j<3;j++)K[i][j]+=sgn*x.inertia_cg_kgm2[i][j];shiftInertia(K,sgn*x.mass_kg,sub(x.cg_m,c));}
 return{mass:m,cg:c,J:K};}
function qmul(a,b){return[a[0]*b[0]-dot(a.slice(1),b.slice(1)),...add(add(scale(b.slice(1),a[0]),scale(a.slice(1),b[0])),cross(a.slice(1),b.slice(1)))];}
const conj=q=>[q[0],-q[1],-q[2],-q[3]];
const rotate=(q,v)=>qmul(qmul(q,[0,...v]),conj(q)).slice(1);
function quat(roll,pitch,yaw){const cr=Math.cos(roll/2),sr=Math.sin(roll/2),cp=Math.cos(pitch/2),sp=Math.sin(pitch/2),cy=Math.cos(yaw/2),sy=Math.sin(yaw/2);return[cr*cp*cy+sr*sp*sy,sr*cp*cy-cr*sp*sy,cr*sp*cy+sr*cp*sy,cr*cp*sy-sr*sp*cy];}
function euler(q){return[Math.atan2(2*(q[0]*q[1]+q[2]*q[3]),1-2*(q[1]**2+q[2]**2)),Math.asin(clamp(2*(q[0]*q[2]-q[3]*q[1]),-1,1)),Math.atan2(2*(q[0]*q[3]+q[1]*q[2]),1-2*(q[2]**2+q[3]**2))];}
class PID{
 constructor(kp,ki,kd,limit,tau=.02){Object.assign(this,{kp,ki,kd,limit,tau});this.i=0;this.last=null;this.d=0;}
 step(error,measurement,dt){let raw=this.last===null?0:(measurement-this.last)/dt;this.last=measurement;this.d+=(raw-this.d)*dt/(this.tau+dt);
 let candidate=clamp(this.i+error*dt,-this.limit/Math.max(this.ki,1e-9),this.limit/Math.max(this.ki,1e-9));let u=this.kp*error+this.ki*candidate-this.kd*this.d;
 if(Math.abs(u)<this.limit||u*error<0)this.i=candidate;return clamp(this.kp*error+this.ki*this.i-this.kd*this.d,-this.limit,this.limit);}
}
// Explicit fixed-length servo link -> swash pose -> fixed blade link. Same geometry as audit.
function tilt(v,x,y){x*=D;y*=D;let a=[Math.cos(y)*v[0]+Math.sin(y)*v[2],v[1],-Math.sin(y)*v[0]+Math.cos(y)*v[2]];return[a[0],Math.cos(x)*a[1]-Math.sin(x)*a[2],Math.sin(x)*a[1]+Math.cos(x)*a[2]];}
const rz=(v,a)=>[Math.cos(a)*v[0]-Math.sin(a)*v[1],Math.sin(a)*v[0]+Math.cos(a)*v[1],v[2]];
const AZ=[60,180,300].map(v=>v*D);
function stat(p,a){return add([0,0,p[0]],tilt(rz([50.3,0,9.5],a),p[1],p[2]));}
const end=(alpha,a)=>rz([58.3-8*Math.cos(alpha),0,60+8*Math.sin(alpha)],a);
function residual(p,alpha,k){return AZ.map((a,i)=>{let d=sub(stat(p,a),end(alpha[i],a));return Math.sqrt(dot(d,d))-k.link_lengths_mm[i];});}
function poseFromServos(alpha,k,guess=k.neutral){let p=[...guess];for(let n=0;n<7;n++){let r=residual(p,alpha,k);if(Math.max(...r.map(Math.abs))<1e-8)break;let cols=[0,1,2].map(j=>{let t=[...p];t[j]+=1e-4;return scale(sub(residual(t,alpha,k),r),1e4);});let dx=solve([0,1,2].map(i=>cols.map(c=>c[i])),r);p=sub(p,dx);}return p;}
function bladePitch(p,a,sign,guess){let rb=add([0,0,p[0]],tilt(rz([32,sign*9,-5.5],a),p[1],p[2]));let t=guess;
 for(let n=0;n<8;n++){let hb=rz([32,sign*(9*Math.cos(t)-5.5*Math.sin(t)),9*Math.sin(t)+5.5*Math.cos(t)],a),dh=rz([0,sign*(-9*Math.sin(t)-5.5*Math.cos(t)),9*Math.cos(t)-5.5*Math.sin(t)],a),d=sub(rb,hb);let dx=(dot(d,d)-225)/(2*dot(d,dh));t+=dx;if(Math.abs(dx)<1e-10)break;}return t;}
const defaults={dt:.0025,servoMassG:20,servoStallNm:.6865,servoSpeedRadS:8.73,servoFriction:.03,servoDelay:.012,cyclicPhaseDeg:0,thrustScale:1,dragArea:.025,initialSoc:.8,controller:true,seed:17,noise:true,radial:10,azimuths:16,inflowTau:.08,wind:[0,0,0],motorCurrentLimit:46,servoJammed:-1,motorScale:[1,1],servoGeometryProfile:'H01_PLACEHOLDER',servoSupplyV:null,servoTorqueReference:'ASSUMED_STALL_MODEL',polarSource:'SIMPLIFIED',massModel:'H01',drive:'H01_AUSSENVERZAHNUNG',ground:false,groundEffect:true,startOnGround:false,groundStiffness:6000,groundDamping:30,groundFriction:.5,groundSlipVelocity:.15,hardLandingSpeed:3};
class Flight{
 constructor(options={}){this.c={...defaults,...options};this.t=0;this.p=[0,0,1];this.v=[0,0,0];this.q=[1,0,0,0];this.w=[0,0,0];this.rng=this.c.seed;
 this.mass=CAD.mass_kg+6*(this.c.servoMassG-9)/1000;this.cg=[...CAD.cg_m];this.J=CAD.inertia_cg_kgm2.map(r=>[...r]);
 // Additional mass remains at the actual CAD servo placeholder centres; recompute full tensor/CG.
 let servo=CAD.components.filter(x=>/SERVO|servo/i.test(x.name));
 // Native object names contain group + index; identify six 9g components by CAD ID exported below.
 if(servo.length!==6)servo=CAD.components.filter(x=>x.part_id==='SERVO-PLATZHALTER');
 if(servo.length!==6)throw Error('Six CAD servo masses required');
 let profile=this.c.servoGeometryProfile==='H01_PLACEHOLDER'?null:SERVO_PROFILES[this.c.servoGeometryProfile];if(this.c.servoGeometryProfile!=='H01_PLACEHOLDER'&&!profile)throw Error('Missing candidate CAD servo profile');
 const dm=(this.c.servoMassG-9)/1000;let newParts=profile?profile.components.map(x=>({...x,mass_kg:this.c.servoMassG/1000,inertia_cg_kgm2:x.inertia_cg_kgm2.map(r=>r.map(v=>v*this.c.servoMassG/profile.mass_g))})):servo.map(x=>({...x,mass_kg:this.c.servoMassG/1000,inertia_cg_kgm2:x.inertia_cg_kgm2.map(r=>r.map(v=>v*this.c.servoMassG/9))}));
 let newcg=scale(add(sub(scale(this.cg,CAD.mass_kg),servo.reduce((s,x)=>add(s,scale(x.cg_m,x.mass_kg)),[0,0,0])),newParts.reduce((s,x)=>add(s,scale(x.cg_m,x.mass_kg)),[0,0,0])),1/this.mass);
 function shift(J,m,d){for(let i=0;i<3;i++)for(let j=0;j<3;j++)J[i][j]+=m*((i===j?dot(d,d):0)-d[i]*d[j]);}
 shift(this.J,CAD.mass_kg,sub(this.cg,newcg));
 for(const x of servo){for(let i=0;i<3;i++)for(let j=0;j<3;j++)this.J[i][j]-=x.inertia_cg_kgm2[i][j];shift(this.J,-x.mass_kg,sub(x.cg_m,newcg));}
 for(const x of newParts){for(let i=0;i<3;i++)for(let j=0;j<3;j++)this.J[i][j]+=x.inertia_cg_kgm2[i][j];shift(this.J,x.mass_kg,sub(x.cg_m,newcg));}this.cg=newcg;
 this.spinInertia=[...CAD.rotor_spin_inertia_kgm2];this.motorSense=-1;this.idlerSpin=0;this.contacts=[];
 if(this.c.massModel==='P10'||this.c.drive==='P10_HOHLRAD'||this.c.ground){if(!P10)throw Error('P10-Massendaten fehlen (p10_massen.js/json)');}
 if(this.c.massModel==='P10'){const rem=P10.remove_components.map(n=>CAD.components.find(x=>x.name===n));if(rem.some(x=>!x))throw Error('P10-Bauteilzuordnung unvollständig');const r=recombine(this.mass,this.cg,this.J,rem,P10.add_components);this.mass=r.mass;this.cg=r.cg;this.J=r.J;this.spinInertia=this.spinInertia.map((v,i)=>v+P10.rotor_spin_inertia_delta_kgm2[i]);}
 if(this.c.drive==='P10_HOHLRAD'){this.motorSense=1;this.idlerSpin=P10.idler_planets.count_per_rotor*P10.idler_planets.spin_inertia_kgm2;}
 if(this.c.ground)this.contacts=P10.landing_gear.contact_points_cad_m.map(c=>[...c]);
 this.rpmHover=2324.96*Math.sqrt(this.mass/CAD.mass_kg);this.omega=[0,0].map(()=>this.rpmHover*Math.PI/30);this.omegaTarget=this.rpmHover*Math.PI/30;
 this.soc=this.c.initialSoc;this.bus=A.packVoltage(A.BATTERY_TATTU_1550_6S,this.soc,0);this.batteryCurrent=0;
 this.servos=Array.from({length:6},()=>({a:0,v:0,pid:new PID(35,3,.10,8.73,.01),queue:[]}));this.command=[0,0,0,0,0,0];this.poses=KIN.map(k=>[...k.neutral]);this.vi=[4,6];
 this.motorPID=[0,1].map(()=>new PID(.0016,.003,.00003,.25,.025));
 this.positionPID=[0,1,2].map(()=>new PID(1.8,.45,2.6,3,.06));this.ratePID=[new PID(.10,.035,.002,.18),new PID(.10,.035,.002,.18),new PID(.045,.015,.001,.08)];
 this.sensorW=[0,0,0];this.verticalAccelMeasured=0;this.verticalAccelPID=new PID(.6,2.0,0,5,.04);this.maxClosure=0;this.servoLoad=[0,0,0,0,0,0];this.saturation=0;this.envelopeViolations=0;this.minPitch=Infinity;this.maxPitch=-Infinity;this.maxCyclic=0;this.crashed=false;this.history=[];this.duty=[.36,.36];
 // Calibrate controller using nominal aero/phase only. Off-nominal plant is restored afterwards.
 const actualScale=this.c.thrustScale,actualPhase=this.c.cyclicPhaseDeg;this.c.thrustScale=1;this.c.cyclicPhaseDeg=0;
 for(let n=0;n<9;n++){
  for(let i=0;i<70;i++){let f=this.aero();this.updateInflow(f,.02);}
  let thrust=this.aero().force[2],factor=clamp(Math.sqrt(this.mass*G/Math.max(thrust,1)),.8,1.2);this.omega=this.omega.map(v=>v*factor);
 }
 this.omegaTarget=this.omega[0];this.rpmHover=this.omega[0]*30/Math.PI;
 for(let i=0;i<70;i++){let f=this.aero();this.updateInflow(f,.02);}
 let trim=this.aero(),eps=.002;this.trim=trim;this.B=Array.from({length:4},()=>Array(6).fill(0));
 for(let j=0;j<6;j++){let alpha=Array(6).fill(0);alpha[j]=eps;let poses=KIN.map((k,i)=>poseFromServos(alpha.slice(i*3,i*3+3),k));let f=this.aero(poses);let y=[f.force[2],...f.moment],b=[trim.force[2],...trim.moment];for(let k=0;k<4;k++)this.B[k][j]=(y[k]-b[k])/eps;}
 this.BBt=this.B.map(r=>this.B.map(s=>dot(r,s)));
 this.c.thrustScale=actualScale;this.c.cyclicPhaseDeg=actualPhase;this.polarLookups=0;this.polarFallbacks=0;
 this.onGround=false;this.contactForce=0;this.maxImpactSpeed=0;this.hardLanding=false;this.groundMoment=[0,0,0];
 if(this.c.ground&&this.c.startOnGround){this.p=[0,0,this.groundClearanceHeight()+.0003];this.omega=[0,0];this.omegaTarget=0;this.vi=[0,0];this.duty=[0,0];}
 }
 rand(){this.rng=(1664525*this.rng+1013904223)>>>0;return this.rng/4294967296-.5;}
 sectionPolar(alpha,re,tc){if(this.c.polarSource==='SIMPLIFIED')return P.polar(alpha,re,tc);this.polarLookups=(this.polarLookups||0)+1;let p=PL.query(alpha,re,this.c.polarSource==='XFOIL_N9'?9:4);if(p)return p;this.polarFallbacks=(this.polarFallbacks||0)+1;return P.polar(alpha,re,tc);}
 aero(poses=this.poses){const c=this.c,g=CAD.geometry.blade,R=g.r_tip/1000,r0=g.r_airfoil_start/1000,chord=g.chord/1000,dr=(R-r0)/c.radial;
 let force=[0,0,0],moment=[0,0,0],T=[0,0],Q=[0,0],inplane=[0,0];let bodyV=rotate(conj(this.q),sub(this.v,c.wind));
 for(let l=0;l<2;l++){let sign=l===0?1:-1,om=this.omega[l],vi=this.vi[l];
 // Upper wake contraction at lower rotor: area-weighted finite-gap approximation.
 let wakeFactor=1+.06/Math.sqrt(.06**2+R**2),wakeRadius=R/Math.sqrt(wakeFactor),wakeArea=Math.PI*(R*R-r0*r0)/wakeFactor;
 let wake=l===1?this.vi[0]*wakeFactor:0;
 for(let ia=0;ia<c.azimuths;ia++){let a=2*Math.PI*(ia+.5)/c.azimuths,theta=bladePitch(poses[l],a,sign,CAD.geometry.pitch_hover_deg[l]*D);let physicalA=l===0?a:Math.PI-a;
 // Unknown dynamic phase is an explicit sensitivity parameter, not an automatic mixer correction.
 physicalA+=c.cyclicPhaseDeg*D;let er=[Math.cos(physicalA),Math.sin(physicalA),0],et=scale([-er[1],er[0],0],sign);
 for(let ir=0;ir<c.radial;ir++){let r=r0+(ir+.5)*dr,pos=sub([r*er[0],r*er[1],l===0?.03:-.03],this.cg),localV=add(bodyV,cross(this.w,pos));
 let wakeWeight=l===1?clamp((wakeRadius-r)/.012+.5,0,1)*clamp((r-r0/Math.sqrt(wakeFactor))/.012+.5,0,1):0;
 let swirl=l===1?(Q[0]/Math.max(.01,2*1.225*wakeArea*this.vi[0]*wakeFactor*r))*wakeWeight:0;
 let ut=om*r+dot(localV,et)+swirl,up=vi+wake*wakeWeight+localV[2];if(ut<.5)continue;let phi=Math.atan2(up,ut),vel2=ut*ut+up*up,pol=this.sectionPolar((theta-phi)/D,Math.sqrt(vel2)*chord/1.5e-5,g.tc);
 let q=.5*1.225*vel2*chord*dr*g.count/c.azimuths*c.thrustScale;
 let lift=q*(pol.cl*Math.cos(phi)-pol.cd*Math.sin(phi)),drag=q*(pol.cl*Math.sin(phi)+pol.cd*Math.cos(phi));
 let f=add([0,0,lift],scale(et,-drag));force=add(force,f);moment=add(moment,cross(pos,f));T[l]+=lift;Q[l]+=drag*r;inplane[l]+=Math.abs(drag);}}
 }
 return {force,moment,T,Q,inplane};}
 updateInflow(f,dt){let R=.1875,area=Math.PI*(R*R-.048**2),vz=rotate(conj(this.q),sub(this.v,this.c.wind))[2];
 for(let l=0;l<2;l++){let ext=vz+(l?this.vi[0]:0),v=clamp(this.vi[l],.1,35);
 // Momentum target in normal working state. Descent/VRS flagged, not represented as validated physics.
 for(let i=0;i<6;i++)v=.5*v+.5*Math.max(0,f.T[l])/(2*1.225*area*Math.max(.8,ext+v));
 // Empirical Cheeseman-Bennett ground effect on inflow (P10 ground option only).
 if(this.c.ground&&this.c.groundEffect){let h=Math.max(.05,this.rotorHeight(l));v*=clamp(1-(R/(4*h))**2,.7,1);}
 this.vi[l]+= (v-this.vi[l])*dt/(this.c.inflowTau+dt);}}
 control(target,dt){let acc,desired;
 if(target.mode==='angle'||target.mode==='idle'){[acc,desired]=this.manualSetpoint(target,dt);}
 else{acc=this.positionPID.map((pid,i)=>pid.step(target.position[i]-this.p[i],this.p[i],dt));
 let yaw=target.yaw||0;desired=quat(clamp((acc[0]*Math.sin(yaw)-acc[1]*Math.cos(yaw))/G,-.30,.30),clamp((acc[0]*Math.cos(yaw)+acc[1]*Math.sin(yaw))/G,-.30,.30),yaw);this.yawSet=undefined;}
 let err=qmul(conj(this.q),desired),rates=scale(err.slice(1),2*(err[0]<0?-1:1)*4);
 for(let i=0;i<3;i++)this.sensorW[i]+=(this.w[i]+(this.c.noise?this.rand()*.012:0)-this.sensorW[i])*dt/(.008+dt);
 let moments=this.ratePID.map((pid,i)=>pid.step(clamp(rates[i],-1.5,1.5)-this.sensorW[i],this.sensorW[i],dt));let zaxis=rotate(this.q,[0,0,1]);let correction=this.verticalAccelPID.step(acc[2]-this.verticalAccelMeasured,this.verticalAccelMeasured,dt);let thrust=this.mass*(G+acc[2]+correction)/Math.max(.7,zaxis[2]);
 if(target.mode==='idle'){thrust=target.thrust??0;this.verticalAccelPID.i=0;this.ratePID.forEach(p=>p.i=0);}
 let dy=[thrust-this.trim.force[2],...sub(moments,this.trim.moment)];let weights=solve(this.BBt,dy);let angles=this.B[0].map((_,j)=>this.B.reduce((sum,r,i)=>sum+r[j]*weights[i],0));
 const lim=.45;let factor=Math.min(1,lim/Math.max(lim,...angles.map(Math.abs)));this.command=angles.map(a=>a*factor);
 // Respect the independently screened collective/cyclic envelope before commanding hardware.
 function inside(cmd){for(let l=0;l<2;l++){let pose=poseFromServos(cmd.slice(l*3,l*3+3),KIN[l]),ps=Array.from({length:8},(_,i)=>bladePitch(pose,i*Math.PI/4,KIN[l].sign,CAD.geometry.pitch_hover_deg[l]*D)/D),mean=ps.reduce((a,b)=>a+b,0)/8,cy=Math.hypot(...[0,1].map(j=>ps.reduce((s,p,i)=>s+p*(j?Math.sin(i*Math.PI/4):Math.cos(i*Math.PI/4))/4,0)));if(mean< -1.9||mean>20.9||cy>3.95)return false;}return true;}
 if(Math.max(...this.command.map(Math.abs))>.01&&!inside(this.command)){let lo=0,hi=1;for(let i=0;i<7;i++){let mid=(lo+hi)/2;if(inside(this.command.map(a=>a*mid)))lo=mid;else hi=mid;}factor*=lo;this.command=this.command.map(a=>a*lo);}
 if(factor<1)this.saturation++;
 // Tracking back-calculation prevents outer integrators winding up when allocation loses authority.
 if(factor<1){this.verticalAccelPID.i*=Math.max(0,1-4*dt);this.positionPID.forEach(p=>p.i*=Math.max(0,1-4*dt));this.ratePID.forEach(p=>p.i*=Math.max(0,1-4*dt));}
 }
 // ANGLE-artige Handsteuerung: Roll/Nick-Sollwinkel, Gierrate, Steigrate. 'idle' = Bodenbetrieb.
 manualSetpoint(target,dt){if(this.yawSet===undefined)this.yawSet=euler(this.q)[2];this.yawSet+=clamp(target.yawRate||0,-2,2)*dt;
 this.positionPID.forEach((p,i)=>{p.i=0;p.last=this.p[i];p.d=0;});
 const lim=.45,accZ=target.mode==='idle'?0:clamp(2.2*((target.climbRate||0)-this.v[2]),-4,4);
 return[[0,0,accZ],quat(target.mode==='idle'?0:clamp(target.roll||0,-lim,lim),target.mode==='idle'?0:clamp(target.pitch||0,-lim,lim),this.yawSet)];}
 // Height of the CG above ground when all contact points touch the ground plane z=0 (upright).
 groundClearanceHeight(){return Math.max(...this.contacts.map(c=>this.cg[2]-c[2]));}
 rotorHeight(l){return this.p[2]+rotate(this.q,sub([0,0,l?-.03:.03],this.cg))[2];}
 groundContact(){let force=[0,0,0],torque=[0,0,0],n=0,c=this.c;
 for(const pt of this.contacts){let r=rotate(this.q,sub(pt,this.cg)),pos=add(this.p,r),pen=-pos[2];if(pen<=0)continue;
 let vel=add(this.v,rotate(this.q,cross(this.w,sub(pt,this.cg))));if(!this.onGround)this.maxImpactSpeed=Math.max(this.maxImpactSpeed,-vel[2]);
 let fn=Math.max(0,c.groundStiffness*pen-c.groundDamping*vel[2]),vt=Math.hypot(vel[0],vel[1]),mu=c.groundFriction*fn/Math.max(vt,c.groundSlipVelocity);
 let f=[-mu*vel[0],-mu*vel[1],fn];force=add(force,f);torque=add(torque,cross(r,f));n++;}
 this.contactCount=n;this.contactForce=force[2];return{force,moment:rotate(conj(this.q),torque)};}
 step(target={position:[0,0,1],yaw:0},external={}){let dt=this.c.dt;if(this.crashed)return;
 if(this.c.controller)this.control(target,dt);else this.command.fill(0);
 let omegaMax=Math.max(...this.omega),bladeMass=.00891974484,rcg=.109463584,deltaI=4.5081223e-7;
 for(let l=0;l<2;l++){
 // Conservative neutral-Jacobian virtual-work load bound. Not a claimed exact off-neutral servo load.
 let torques=KIN[l].pitch_servo_jacobian[0].map((_,j)=>KIN[l].pitch_servo_jacobian.reduce((s,row)=>s+Math.abs(row[j]),0));
 let theta=CAD.geometry.pitch_hover_deg[l]*D,perBlade=deltaI*this.omega[l]**2*Math.abs(Math.sin(theta)*Math.cos(theta))+this.c.servoFriction*bladeMass*rcg*this.omega[l]**2*.0048+Math.abs((this.lastAero?.T[l]||6)/8)*.002;
 for(let j=0;j<3;j++){let n=l*3+j,s=this.servos[n];this.servoLoad[n]=torques[j]*perBlade;let margin=clamp(1-this.servoLoad[n]/this.c.servoStallNm,0,1);s.queue.push(this.command[n]);let delaySteps=Math.round(this.c.servoDelay/dt),cmd=s.queue.length>delaySteps?s.queue.shift():0;
 let rawCommand=s.pid.step(cmd-s.a,s.a,dt);let vcmd=clamp(rawCommand,-this.c.servoSpeedRadS*margin,this.c.servoSpeedRadS*margin);if(Math.abs(rawCommand-vcmd)>1e-6)s.pid.i*=Math.max(0,1-5*dt);if(n===this.c.servoJammed||margin===0){vcmd=0;s.v=0;}
 s.v+=clamp(vcmd-s.v,-180*margin*dt,180*margin*dt);if(n===this.c.servoJammed)s.v=0;s.a=clamp(s.a+s.v*dt,-.6,.6);if(margin===0)this.saturation++;}
 this.poses[l]=poseFromServos(this.servos.slice(l*3,l*3+3).map(s=>s.a),KIN[l],this.poses[l]);let closure=residual(this.poses[l],this.servos.slice(l*3,l*3+3).map(s=>s.a),KIN[l]);this.maxClosure=Math.max(this.maxClosure,...closure.map(Math.abs));}
 if(Math.round(this.t/dt)%8===0){for(let l=0;l<2;l++){
 let pitches=Array.from({length:16},(_,i)=>bladePitch(this.poses[l],i*2*Math.PI/16,KIN[l].sign,CAD.geometry.pitch_hover_deg[l]*D)/D);
 let mean=pitches.reduce((a,b)=>a+b,0)/16,cyclic=Math.hypot(...[0,1].map(j=>pitches.reduce((s,p,i)=>s+2*p*(j?Math.sin(i*2*Math.PI/16):Math.cos(i*2*Math.PI/16))/16,0)));
 this.minPitch=Math.min(this.minPitch,...pitches);this.maxPitch=Math.max(this.maxPitch,...pitches);this.maxCyclic=Math.max(this.maxCyclic,cyclic);
 if(mean< -2||mean>21||cyclic>4.05)this.envelopeViolations++;
 }}
 let f=this.aero();this.lastAero=f;this.updateInflow(f,dt);
 let currents=[],torque=[],oldOmega=[...this.omega],busCurrent=6/Math.max(this.bus,12); // assumed 6 W FC/BEC idle; moving servo demand below
 const m=A.MOTOR_ECO2_2306_1900,ratio=6.5,kt=A.kt(m);
 for(let l=0;l<2;l++){let rpm=this.omega[l]*30/Math.PI,needed=A.motorPoint(m,rpm,Math.max(0,this.trim.Q[l])*(this.c.ground?(this.omegaTarget/(this.rpmHover*Math.PI/30))**2:this.omegaTarget>1?(this.omega[l]/this.omegaTarget)**2:0),ratio);let feed=needed.voltage/Math.max(this.bus,12);let correction=this.motorPID[l].step(this.omegaTarget-this.omega[l],this.omega[l],dt);this.duty[l]=clamp(feed+correction,0,.95);
 let current=clamp((this.duty[l]*this.bus-rpm*ratio/m.kv)/m.R,0,this.c.motorCurrentLimit);current*=this.c.motorScale[l];let qm=Math.max(0,kt*(current-A.i0(m,rpm*ratio)))*ratio*.92;
 if(this.duty[l]>=.95)this.motorPID[l].i*=Math.max(0,1-5*dt);
 let spinJ=this.spinInertia[l]+(1.2e-6*ratio*ratio)+this.idlerSpin*ratio*ratio; // motor inertia assumption reflected through gear
 let acceleration=(qm-f.Q[l])/spinJ;this.omega[l]=Math.max(0,this.omega[l]+acceleration*dt);currents.push(current);torque.push(qm);busCurrent+=this.duty[l]*current/.95;}
 let servoPower=this.servos.reduce((s,x,i)=>s+Math.abs(x.v*this.servoLoad[i])/.5,0);busCurrent+=servoPower/Math.max(this.bus,12);this.batteryCurrent=busCurrent;this.bus=A.packVoltage(A.BATTERY_TATTU_1550_6S,this.soc,busCurrent);this.soc=Math.max(0,this.soc-busCurrent*dt/(1.55*3600));
 let bodyAir=rotate(conj(this.q),sub(this.v,this.c.wind));let drag=bodyAir.map(v=>-.5*1.225*this.c.dragArea*v*Math.abs(v));let forceWorld=rotate(this.q,add(f.force,drag));forceWorld=add(forceWorld,external.force||[0,0,0]);
 if(this.c.ground){let g=this.groundContact();forceWorld=add(forceWorld,g.force);this.groundMoment=g.moment;if(this.contactCount&&this.maxImpactSpeed>this.c.hardLandingSpeed)this.hardLanding=true;this.onGround=this.contactCount>0;}let accel=scale(forceWorld,1/this.mass);accel[2]-=G;
 this.verticalAccelMeasured+=(accel[2]+(this.c.noise?this.rand()*.06:0)-this.verticalAccelMeasured)*dt/(.04+dt);
 this.v=add(this.v,scale(accel,dt));this.p=add(this.p,scale(this.v,dt));
 // Aero moment already contains drag reaction. Rotor angular momentum change transfers to fuselage.
 let spinH=this.spinInertia.map(v=>v+this.motorSense*(1.2e-6+this.idlerSpin)*6.5);
 let angularMomentum=spinH[0]*oldOmega[0]-spinH[1]*oldOmega[1];let moment=add(f.moment,external.moment||[0,0,0]);if(this.c.ground)moment=add(moment,this.groundMoment);
 moment[2]-=spinH[0]*(this.omega[0]-oldOmega[0])/dt-spinH[1]*(this.omega[1]-oldOmega[1])/dt;
 let H=add(mv(this.J,this.w),[0,0,angularMomentum]);let dw=solve(this.J,sub(moment,cross(this.w,H)));this.w=add(this.w,scale(dw,dt));let dq=qmul(this.q,[0,...this.w]);this.q=add(this.q,scale(dq,dt/2));this.q=scale(this.q,1/Math.sqrt(dot(this.q,this.q)));this.t+=dt;
 if(![...this.p,...this.w,...this.q].every(Number.isFinite))throw Error('Nonfinite flight state');
 if((!this.c.ground&&this.p[2]<.18)||this.hardLanding||Math.abs(euler(this.q)[0])>1.3||Math.abs(euler(this.q)[1])>1.3){this.crashed=true;this.crashTime=this.t;}
 return this.snapshot(target);
 }
 snapshot(target={position:[0,0,1],yaw:0}){return{t:this.t,p:[...this.p],v:[...this.v],euler:euler(this.q).map(x=>x/D),omega:[...this.w],rpm:this.omega.map(x=>x*30/Math.PI),rpmTarget:this.omegaTarget*30/Math.PI,servoDeg:this.servos.map(x=>x.a/D),servoCommandDeg:this.command.map(x=>x/D),servoLoadNm:[...this.servoLoad],duty:[...this.duty],bus:this.bus,current:this.batteryCurrent,soc:this.soc,thrust:this.lastAero?.T||[0,0],polarFallbackFraction:this.polarLookups?this.polarFallbacks/this.polarLookups:0,target:target.position,crashed:this.crashed,vi:[...this.vi],onGround:!!this.onGround,contactForce:this.contactForce||0,hardLanding:!!this.hardLanding};}
}
const api={Flight,PID,CAD,KIN,P10,recombine,defaults,solve,quat,euler,rotate,conj,poseFromServos,bladePitch,residual,D};if(node)module.exports=api;else root.H01Flight=api;
})(globalThis);
