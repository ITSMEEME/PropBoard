'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const H=__dirname,O=path.join(H,'Ausgabe'),P=require('./p14_physik.js'),{Pilot,euler}=require('./p14_pilot.js');
const read=n=>JSON.parse(fs.readFileSync(path.join(O,n),'utf8')),config=read('Eingaben.json'),anchors=read('Massenvarianten.json'),checks=[],cases=[];
const near=(a,b,eps)=>assert(Math.abs(a-b)<eps,`${a} != ${b}`);
function create(c=config,mode='free_assumption'){
  const f=new P.Flight(c,anchors);Object.assign(f.commands,{motorMode:mode,torqueCap:mode==='free_assumption'?150:46.25,inputPowerCap:mode==='free_assumption'?40000:3400});
  const p=new Pilot(f);p.start();return{f,p,peakPower:0,maxTilt:0};
}
function run(s,seconds,input={}){
  const {f,p}=s;
  for(let i=0;i<Math.round(seconds*120);i++){
    p.update(input,1/120);const before={vz:f.velocity[2]};f.step(1/120);p.afterStep(before);
    assert.notEqual(p.phase,'CRASH',p.reason);assert([...f.position,...f.velocity,...f.quaternion,...f.omega].every(Number.isFinite));near(P.length(f.quaternion),1,1e-9);
    assert(Math.hypot(f.commands.cyclicX,f.commands.cyclicY)<=.500001);assert(Math.abs(f.commands.collectiveUpper)<=3.5&&Math.abs(f.commands.collectiveLower)<=3.5);
    const lim=P.motorLimits(f.config,f.commands);assert(f.lastInputPowerPerMotor.every(w=>w<=lim.inputPower_W+1e-5));assert(f.lastShaftTorque.every(t=>t<=lim.torque_Nm+1e-6));
    s.peakPower=Math.max(s.peakPower,...f.lastInputPowerPerMotor);s.maxTilt=Math.max(s.maxTilt,...euler(f.quaternion).slice(0,2).map(Math.abs));
  }
}
function check(name,fn){fn();checks.push(name);console.log('OK',name);}
const s=create();
check('Cold start reaches hover through real shaft spin-up, power caps and rigid-body integration',()=>{
  assert.equal(s.f.height,0);assert.deepEqual(s.f.shaftOmega,[0,0]);run(s,1);assert.equal(s.f.height,0);assert(Math.max(...s.f.shaftOmega)<s.p.hover.rpm*Math.PI/30);
  run(s,13);assert.equal(s.p.phase,'FLIGHT');near(s.f.height,1.2,.1);assert(s.f.shaftOmega.every(w=>w>150));
});
check('Forward control moves the vehicle and release brakes into position hold',()=>{
  const x=s.f.position[0];run(s,4,{forward:1});assert(s.f.position[0]>x+3);const hold=s.p.reference.slice();run(s,14);assert(Math.hypot(...s.f.velocity.slice(0,2))<.2);assert(Math.hypot(s.f.position[0]-hold[0],s.f.position[1]-hold[1])<.5);
});
check('Yaw control turns right and releases into zero yaw rate',()=>{
  const before=euler(s.f.quaternion)[2];run(s,1.5,{yaw:-1});const after=euler(s.f.quaternion)[2],delta=Math.atan2(Math.sin(after-before),Math.cos(after-before));assert(delta<-20*P.D);run(s,5);assert(Math.abs(s.f.omega[2])<.03);
});
check('Lateral control follows the current heading',()=>{
  const before=s.f.position.slice(),yaw=euler(s.f.quaternion)[2],right=[Math.sin(yaw),-Math.cos(yaw),0];run(s,2,{right:1});assert(P.dot(P.sub(s.f.position,before),right)>.3);run(s,12);
});
check('Climb and descent change held altitude without overriding gravity',()=>{
  const start=s.f.height;run(s,2,{climb:1});run(s,6);assert(s.f.height>start+1);run(s,2,{climb:-1});run(s,6);near(s.f.height,start,.18);
});
check('ANGLE mode levels attitude on release without promising position hold',()=>{
  s.p.setMode('ANGLE');run(s,3,{right:.5});assert(euler(s.f.quaternion)[0]>3*P.D);run(s,4);assert(Math.abs(euler(s.f.quaternion)[0])<.6*P.D);assert(Math.hypot(...s.f.velocity.slice(0,2))>.2);s.p.setMode('POSITION');run(s,14);
});
check('Landing reaches the floor gently and commands physical motor coast-down',()=>{
  s.p.land();run(s,10);assert(s.f.contact);assert.equal(s.f.height,0);assert.equal(s.f.commands.rpm,0);assert.equal(s.p.phase,'STOPPING');const rpm=s.f.shaftOmega.slice();run(s,1);assert(s.f.shaftOmega.every((w,k)=>w>0&&w<rpm[k]));
});
check('Every supported blade count uses its own CAD mass and hover reference',()=>{
  for(const n of [4,6,10,12]){const c=P.clone(config);c.geometry.blades_per_rotor=n;const v=create(c);run(v,14);assert.equal(v.p.phase,'FLIGHT');near(v.f.height,1.2,.18);near(v.f.properties.dryCAD,anchors.cases[String(n)].mass_kg,1e-9);cases.push({blades:n,pairs:1,mass_kg:v.f.properties.mass,hover_rpm:v.p.hover.rpm,height_m:v.f.height,peak_input_power_each_W:v.peakPower});}
});
check('Multiple rotor pairs preserve their changed CAD inertia and model limits',()=>{
  for(const n of [2,4]){const c=P.clone(config);c.geometry.lift_units=n;const v=create(c);run(v,14);near(v.f.height,1.2,.18);assert(v.f.properties.multiUnitConnectionMissing);cases.push({blades:8,pairs:n,mass_kg:v.f.properties.mass,hover_rpm:v.p.hover.rpm,height_m:v.f.height,peak_input_power_each_W:v.peakPower});}
});
check('Controller never upgrades the documented MN1330 power case to obtain lift',()=>{
  const v=create(config,'conservative_spec');run(v,12,{forward:1,climb:1});assert.equal(v.f.commands.motorMode,'conservative_spec');assert.equal(v.f.commands.inputPowerCap,3400);assert.equal(v.f.commands.torqueCap,46.25);assert.equal(v.f.height,0);assert(v.peakPower<=3400+1e-6);
  v.f.time=179.999;assert.throws(()=>v.f.step(.01),/180-s/);near(v.f.time,179.999,1e-9);
});
check('Landing during cold spin-up cancels takeoff and coasts at the floor',()=>{
  const v=create();run(v,.5);assert(v.f.contact);v.p.land();assert.equal(v.p.phase,'STOPPING');run(v,1);assert.equal(v.f.commands.rpm,0);assert.equal(v.f.height,0);
});
check('Extended RPM is confined to free assumptions; real-data cases retain2400/min',()=>{
  const f=new P.Flight(config,anchors);f.commands.rpm=2500;assert.throws(()=>f.step(1/120),/Stellgröße/);Object.assign(f.commands,{motorMode:'free_assumption',torqueCap:150,inputPowerCap:40000,rpm:2800});f.step(1/120);f.commands.rpm=2801;assert.throws(()=>f.step(1/120),/Stellgröße/);
});
check('Excess attitude ends the run instead of silently recovering the airframe',()=>{
  const f=create();f.f.quaternion=[Math.cos(40*P.D),Math.sin(40*P.D),0,0];f.p.update({});assert.equal(f.p.phase,'CRASH');assert.equal(f.f.commands.rpm,0);
});
const sourcefiles=['p14_pilot.js','p14_physik.js'];
const out={passed:true,production_ready:false,controller:'ideal position/angle model pilot; no verified hardware firmware',native_sha256:read('Modell.json').source_native_sha256,source_sha256:Object.fromEntries(sourcefiles.map(n=>[n,crypto.createHash('sha256').update(fs.readFileSync(path.join(H,n))).digest('hex')])),checks,cases,baseline:{mass_kg:s.f.properties.mass,max_tilt_deg:s.maxTilt/P.D,peak_input_power_each_W:s.peakPower},scope:'Fixed120Hz model flight, no measured flight/servo/forward-flight validation'};
fs.writeFileSync(path.join(O,'Flugsteuerung_Pruefung.json'),JSON.stringify(out,null,2)+'\n');console.log(JSON.stringify(out,null,2));
