'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),F=require('./flugphysik.js'),K=require('./kinematik_p11.js'),D=require('./design.js'),S=require('./parameterstudie.js');
const root=path.join(__dirname,'../integration_p11/Ausgabe'),sha=crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'P11_Gesamtbaugruppe.FCStd'))).digest('hex');
for(const [file,key] of [['Massen_P11.json','source_native_sha256'],['Aufbau_P11.json','native_sha256'],['Browserexport_P11.json','source_native_sha256']])assert.equal(JSON.parse(fs.readFileSync(path.join(root,file)))[key],sha,file);
assert.equal(F.P11.source_native_sha256,sha);assert.equal(F.P11.guide_rollers.count_per_rotor,2);
let maxFrame=0,maxPitch=0;
for(const ref of require('./kinematik_p11_referenz.json')){const actual=K.frames(ref.servos,ref.angles);for(const [key,expected] of Object.entries(ref.frames)){const f=actual.frames[key];assert(f,key);const a=[...f.R.flat(),...f.t];for(let i=0;i<12;i++)maxFrame=Math.max(maxFrame,Math.abs(a[i]-expected[i]));}for(let l=0;l<2;l++)for(let j=0;j<8;j++)maxPitch=Math.max(maxPitch,Math.abs(ref.pitches[l][j]-actual.pitches[l][j]));}
assert(maxFrame<1e-6,maxFrame);assert(maxPitch<1e-6,maxPitch);
const s=new F.Flight({drive:'P11_DIRECT',servoMassG:69,servoGeometryProfile:'Savox_SB2271SG_USER',noise:false});assert.equal(s.drive.ratio,1);assert.equal(s.drive.motorSpinJ,0);assert(s.mass>2&&s.mass<3);assert(s.spinInertia.every(v=>v>0));assert(s.J.every((r,i)=>r[i]>0));assert(Math.abs(s.guideRatio-64.4/9.55)<1e-12);
const r=S.evaluate(s,{...D.defaults,rpm:Math.round(s.rpmHover)});assert.equal(r.withinMotorEnvelope,false);assert(r.motorCurrentA.some(v=>v>46));
for(let l=0;l<2;l++)assert(Math.abs(r.sections[l].reduce((a,v)=>a+v.liftN,0)-r.thrustPerRotorN[l])<1e-8);
// Internal motor torques must conserve angular momentum including guide rolling inertia.
s.aero=()=>({force:[0,0,0],moment:[0,0,0],T:[0,0],Q:[0,0]});s.c.controller=false;s.c.dt=.0005;s.p=[0,0,100];s.omega=[100,80];s.omegaTarget=180;
const H=()=>{const h=s.J.map(r=>r.reduce((a,v,i)=>a+v*s.w[i],0));h[2]+=(s.spinInertia[0]+s.idlerSpin*s.guideRatio)*s.omega[0]-(s.spinInertia[1]+s.idlerSpin*s.guideRatio)*s.omega[1];return F.rotate(s.q,h);};const before=H();for(let i=0;i<400;i++)s.step();const error=Math.hypot(...H().map((v,i)=>v-before[i]));assert(error<2e-5,error);
for(const name of ['P11_EMAX_Referenz_Bodenstart','P11_EMAX_Referenz_ANGLE']){const rows=require('./Ergebnisse/P11/'+name+'.json');assert(rows.length>50);assert(rows.every(r=>r.motorCurrentA.every(i=>i<=46+1e-9)));assert(rows.every(r=>r.driveRatio===1));}
const evidence={status:'PASS',native_sha256:sha,maxFrameError:maxFrame,maxPitchErrorDeg:maxPitch,angularMomentumErrorNms:error,massKg:s.mass,driveRatio:1,rollerRatio:s.guideRatio,referenceDemandReachable:r.withinMotorEnvelope,actualCurrentCapA:46};
fs.writeFileSync(path.join(root,'Simulationspruefung_P11.json'),JSON.stringify(evidence,null,2)+'\n');
console.log('PASS P11: synchronized native hashes, Python/JS frames and pitches, 1:1 motor / rolling guide ratios, mass/inertia, radial loads, honest EMAX limits, actual current cap, angular momentum.',evidence);
