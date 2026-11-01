/* P11 render kinematics: exact JavaScript port of bewegung_p09/voll_runtime.state(),
 * fertigung_p08/runtime.transforms() and integration_p10/p10_runtime planet frames.
 * Returns 4x4 column-major matrices (mm, CAD frame) for every animated frame key.
 * Validated against FreeCAD reference frames in kinematik_p11_referenz.json (pruefen.js). */
(function(root){'use strict';
const node=typeof module!=='undefined'&&module.exports;
const KIN=node?require('./kinematik.json'):root.H01_KINEMATICS;
const D=Math.PI/180,AZ=[60,180,300].map(v=>v*D),RADIUS=33;
const add=(a,b)=>a.map((v,i)=>v+b[i]),sub=(a,b)=>a.map((v,i)=>v-b[i]),dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2],norm=a=>Math.sqrt(dot(a,a));
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const rz=(v,a)=>[Math.cos(a)*v[0]-Math.sin(a)*v[1],Math.sin(a)*v[0]+Math.cos(a)*v[1],v[2]];
function tilt(v,x,y){x*=D;y*=D;let c=Math.cos(y),s=Math.sin(y),u=[c*v[0]+s*v[2],v[1],-s*v[0]+c*v[2]];c=Math.cos(x);s=Math.sin(x);return[u[0],c*u[1]-s*u[2],s*u[1]+c*u[2]];}
// --- 3x3 rotations (row-major arrays) and placements {R,t}
function axisRot(ax,deg){const a=deg*D,c=Math.cos(a),s=Math.sin(a),[x,y,z]=ax,C=1-c;return[[c+x*x*C,x*y*C-z*s,x*z*C+y*s],[y*x*C+z*s,c+y*y*C,y*z*C-x*s],[z*x*C-y*s,z*y*C+x*s,c+z*z*C]];}
const rotz=deg=>axisRot([0,0,1],deg),roty=deg=>axisRot([0,1,0],deg),rotx=deg=>axisRot([1,0,0],deg);
const I3=[[1,0,0],[0,1,0],[0,0,1]];
function mm3(a,b){return a.map((r,i)=>[0,1,2].map(j=>r[0]*b[0][j]+r[1]*b[1][j]+r[2]*b[2][j]));}
const mv3=(m,v)=>m.map(r=>r[0]*v[0]+r[1]*v[1]+r[2]*v[2]);
const P=(t=[0,0,0],R=I3)=>({R,t});
const pmul=(a,b)=>({R:mm3(a.R,b.R),t:add(mv3(a.R,b.t),a.t)});
function basis(origin,z,x){z=z.map(v=>v/norm(z));let d=dot(x,z);x=sub(x,z.map(v=>v*d));let n=norm(x);x=x.map(v=>v/n);let y=cross(z,x);return P(origin,[[x[0],y[0],z[0]],[x[1],y[1],z[1]],[x[2],y[2],z[2]]]);}
function localWorld(sign){return sign>0?P([0,0,30]):P([0,0,-30],mm3(rotz(180),rotx(180)));}
const swash=p=>P([0,0,p[0]],mm3(rotx(p[1]),roty(p[2])));
// --- closed servo links (same Newton scheme as bewegung_runtime.pose_from_servos)
function stat(p,a){return add([0,0,p[0]],tilt(rz([50.3,0,9.5],a),p[1],p[2]));}
const servoEnd=(al,a)=>rz([58.3-8*Math.cos(al),0,60+8*Math.sin(al)],a);
function residual(p,al,k){return AZ.map((a,i)=>norm(sub(stat(p,a),servoEnd(al[i],a)))-k.link_lengths_mm[i]);}
function solve3(A,b){A=A.map((r,i)=>[...r,b[i]]);for(let i=0;i<3;i++){let k=i;for(let j=i+1;j<3;j++)if(Math.abs(A[j][i])>Math.abs(A[k][i]))k=j;[A[i],A[k]]=[A[k],A[i]];let v=A[i][i];for(let j=i;j<4;j++)A[i][j]/=v;for(let r=0;r<3;r++)if(r!==i){let f=A[r][i];for(let j=i;j<4;j++)A[r][j]-=f*A[i][j];}}return A.map(r=>r[3]);}
function poseFromServos(al,k,guess){let p=[...(guess||k.neutral)];for(let n=0;n<12;n++){let r=residual(p,al,k);if(Math.max(...r.map(Math.abs))<1e-9)break;let cols=[0,1,2].map(j=>{let q=[...p];q[j]+=1e-4;return sub(residual(q,al,k),r).map(v=>v*1e4);});p=sub(p,solve3([0,1,2].map(i=>cols.map(c=>c[i])),r));}return p;}
// --- blade links with the P09 33 mm radius
const hornBall=(t,a,s)=>rz([RADIUS,s*(9*Math.cos(t)-5.5*Math.sin(t)),9*Math.sin(t)+5.5*Math.cos(t)],a);
const ringBall=(p,a,s)=>add([0,0,p[0]],tilt(rz([RADIUS,s*9,-5.5],a),p[1],p[2]));
function pitch(p,a,s,guess){let r=ringBall(p,a,s),t=guess;for(let n=0;n<30;n++){let d=sub(r,hornBall(t,a,s)),dh=rz([0,s*(-9*Math.sin(t)-5.5*Math.cos(t)),9*Math.cos(t)-5.5*Math.sin(t)],a),den=2*dot(d,dh);if(Math.abs(den)<1e-10)break;let st=(dot(d,d)-225)/den;t+=st;if(Math.abs(st)<1e-12)break;}return t;}
const rollerSpin=angle=>64.4/9.55*angle;
/** servos: six servo angles [deg]; angles: two rotor angles [deg]. poses optional warm start. */
function frames(servos,angles,poses){
 const out={},poseOut=[],pitches=[];
 for(let l=0;l<2;l++){const k=KIN[l],sign=l?-1:1,world=localWorld(sign),al=servos.slice(l*3,l*3+3).map(v=>v*D),p=poseFromServos(al,k,poses&&poses[l]),sw=swash(p),a=angles[l];poseOut.push(p);
  out['rotor:'+l]=pmul(world,P([0,0,0],rotz(a)));out['swash:'+l]=pmul(world,sw);out['swashrot:'+l]=pmul(pmul(world,sw),P([0,0,0],rotz(a)));out['sleeve:'+l]=pmul(world,P([0,0,p[0]]));
  out[`p08:${l}:-1:swash`]=pmul(world,sw);
  for(let i=0;i<3;i++){const az=AZ[i],deg=servos[l*3+i],lower=stat(p,az),upper=servoEnd(deg*D,az),vec=sub(upper,lower),rad=[Math.cos(az),Math.sin(az),0],tan=[-Math.sin(az),Math.cos(az),0];
   const lo=basis(lower,vec,rad),hi=basis(upper,vec.map(v=>-v),tan),lowstud=P(lower,mm3(sw.R,rotz(az/D))),highrot=mm3(rotz(az/D),roty(deg)),highstud=P(upper,mm3(highrot,rotz(90))),horn=P(rz([58.3,0,60],az),highrot);
   const e={horn,ball_low:lowstud,ball_high:highstud,body_low:lo,body_high:hi,cap_low:lo,cap_high:hi,rod:lo,jam_low:pmul(lo,P([0,0,7])),jam_high:pmul(hi,P([0,0,7])),horn_nut:pmul(highstud,P([-9.9,0,0],roty(90))),clamp_bolt:pmul(horn,P([5.5,-7.5,4.3])),clamp_nut:pmul(horn,P([5.5,-7.5,-5.9])),washer_high:pmul(horn,P([5.5,-7.5,4])),washer_low:pmul(horn,P([5.5,-7.5,-4.3]))};
   for(const [role,pl] of Object.entries(e))out[`p08:${l}:${i}:${role}`]=pmul(world,pl);
   out[`output:${l}:${i}`]=pmul(world,P(rz([58.3,0,60],az),mm3(rotz([60,180,300][i]),roty(deg))));}
  const ps=[];
  for(let j=0;j<8;j++){const az=(a+j*45)*D,t=pitch(p,az,sign,(l?16.7:14)*D);ps.push(t/D);
   const bladeRot=mm3(rotz(az/D),rotx(sign*t/D));out[`blade:${l}:${j}`]=pmul(world,P([0,0,0],bladeRot));out[`pin:${l}:${j}`]=pmul(world,P([0,0,0],rotz(az/D)));
   const low=hornBall(t,az,sign),high=ringBall(p,az,sign),vec=sub(high,low),rad=[Math.cos(az),Math.sin(az),0],lo=basis(low,vec,rad),hi=basis(high,vec.map(v=>-v),rad);
   const e={stud_low:P(low,bladeRot),stud_high:P(high,mm3(sw.R,rotz(az/D))),body_low:lo,body_high:hi,cap_low:lo,cap_high:hi,rod:lo};
   for(const [role,pl] of Object.entries(e))out[`link:${l}:${j}:${role}`]=pmul(world,pl);}
  pitches.push(ps);
  out[`motor:${l}`]=out[`rotor:${l}`];
  for(let q=0;q<3;q++){const phi=[115,205,330][q],a=phi*D;out[`roller:${l}:${q}`]=pmul(world,P([54.8*Math.cos(a)-.15*Math.sin(a),54.8*Math.sin(a)+.15*Math.cos(a),0],rotz(rollerSpin(angles[l]))));}
 }
 out.fixed=P();
 return{frames:out,poses:poseOut,pitches};}
/** column-major Float32/64 4x4 of a placement */
function toMat4(pl,o=new Float64Array(16)){const R=pl.R,t=pl.t;o[0]=R[0][0];o[1]=R[1][0];o[2]=R[2][0];o[3]=0;o[4]=R[0][1];o[5]=R[1][1];o[6]=R[2][1];o[7]=0;o[8]=R[0][2];o[9]=R[1][2];o[10]=R[2][2];o[11]=0;o[12]=t[0];o[13]=t[1];o[14]=t[2];o[15]=1;return o;}
const api={frames,toMat4,pmul,P,rollerSpin,constants:{RADIUS,CENTRE:Math.hypot(54.8,.15),PHI:[115,205,330],RATIO:1,ROLLER_RATIO:64.4/9.55}};
if(node)module.exports=api;else root.H01KinematikP11=api;
})(globalThis);
