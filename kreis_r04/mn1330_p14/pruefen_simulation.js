'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),vm=require('vm'),crypto=require('crypto');
const H=__dirname,O=path.join(H,'Ausgabe'),P=require('./p14_physik.js'),Aero=require('../simulation/r04_physik.js');
const Motor=require('./Motor_Daten.json');
const read=name=>JSON.parse(fs.readFileSync(path.join(O,name),'utf8'));
const config=read('Eingaben.json'),anchors=read('Massenvarianten.json'),model=read('Modell.json'),kin=read('Kinematik_Pruefung.json');
const checks=[];
function check(name,fn){fn();checks.push(name);console.log('OK',name);}
const maxdiff=(a,b)=>Math.max(...a.map((v,i)=>Math.abs(v-b[i]))),near=(a,b,eps=1e-7)=>assert(Math.abs(a-b)<=eps,`${a} != ${b}`);
check('Source matches CAD and every mass variant',()=>{
  near(model.mass.dry_cad_mass_assumed_kg,anchors.cases['8'].mass_kg,1e-8);
  const gh=crypto.createHash('sha256');for(const name of ['geometrie.py','gelenke.py','kinematik.py'])gh.update(Buffer.concat([Buffer.from(name+'\0'),fs.readFileSync(path.join(H,name))]));assert.equal(anchors.geometry_source_sha256,gh.digest('hex'));
  const sha=crypto.createHash('sha256').update(fs.readFileSync(path.join(O,'P14_MN1330_Leichtbau.FCStd'))).digest('hex');assert.equal(sha,model.source_native_sha256);assert.equal(sha,kin.native_sha256);
});
check('Legacy BEMT default is numerically unchanged',()=>{
  const baseline=JSON.parse(fs.readFileSync(path.join(H,'Quellen/Legacy_BEMT_4dc7252.json'),'utf8'));
  for(const {input,result:a} of baseline.cases){const b=Aero.simulate(input);for(const k of ['T','P','Q','tipMach'])assert.equal(a[k],b[k]);for(const k of ['upper','lower'])for(const field of ['dT','dQ','re','alpha'])assert.equal(maxdiff(a[k][field],b[k][field]),0);}
});
check('Optional second shaft RPM affects lower rotor, preserves upper',()=>{
  const a=Aero.simulate({rpm:850}),b=Aero.simulate({rpm:850,rpmLower:700});assert.equal(a.upper.T,b.upper.T);assert(b.lower.T<a.lower.T);
});
check('Python and browser close the same real linkage',()=>{
  for(const fixture of kin.fixtures){const s=P.solve(fixture.config,...fixture.inputs),e=fixture.solution;assert(maxdiff(s.pitches_deg,e.pitches_deg)<1e-7);assert(maxdiff(s.servo_deg,e.servo_deg)<1e-7);for(const k of ['servo_points_mm','pitch_points_mm'])for(let i=0;i<s[k].length;i++)for(let j=0;j<2;j++)assert(maxdiff(s[k][i][j],e[k][i][j])<1e-7);}
});
const context={P14Physics:P};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(H,'p14_3d.js'),'utf8'),context);const V=context.P14View;
check('WebGL and native CAD use the same rigid motion',()=>{
  const refs=read('Bewegung_Referenzen.json');let max=0;
  for(const r of refs){const[a,cu,cl,cx,cy]=r.state,pose=P.podPose(config,{collectiveUpper:cu,collectiveLower:cl,cyclicX:cx,cyclicY:cy},1,a);const mat=V.localDelta(r.row,config,pose,a,model.derived.neutral);max=Math.max(max,maxdiff(mat,r.matrix));}
  assert(max<1e-7,`matrix delta ${max}`);
});
check('Upper/lower foils have correct opposed handedness',()=>{
  const br=model.derived.blade_root_mm,LE=[br+70,-30,0],TE=[br+70,90,0];
  for(const sign of [1,-1]){const row=model.scene.find(r=>r.sign===sign&&r.part==='CFK01'&&r.blade_index===0),m=sign>0?row.neutral_transform:V.mul(V.R([0,1,0],180),row.neutral_transform);assert(V.point(m,LE)[2]>V.point(m,TE)[2]);}
  assert.equal(new Float32Array([710])[0],710);
});
check('Mass and inertia update from rebuilt CAD for 5 blade counts and 4 pair counts',()=>{
  let previous=0;
  for(const blades of [4,6,8,10,12]){assert(anchors.cases[String(blades)].all_valid);assert(anchors.cases[String(blades)].mass_kg>previous);previous=anchors.cases[String(blades)].mass_kg;
    for(const pairs of [1,2,3,4])for(const payload of [0,100,150]){const c=P.clone(config);c.geometry.blades_per_rotor=blades;c.geometry.lift_units=pairs;const m=P.massProperties(c,anchors,{payload,payloadZ:.9}),J=m.inertia;assert(m.mass>0);assert(J[0][0]>0&&J[1][1]>0&&J[2][2]>0);assert(J[0][0]*J[1][1]-J[0][1]*J[1][0]>0);near(m.dryCAD,anchors.cases[String(blades)].mass_kg*pairs);assert.equal(m.multiUnitConnectionMissing,pairs>1);for(let i=0;i<3;i++)for(let j=0;j<3;j++)near(J[i][j],J[j][i]);}
  }
  const low=P.massProperties(config,anchors,{payload:100,payloadZ:0}),high=P.massProperties(config,anchors,{payload:100,payloadZ:.9});assert(high.cg[2]>low.cg[2]);assert(high.inertia[0][0]>low.inertia[0][0]);
});
check('Unsupported dimensions require rebuilt mass data',()=>{const c=P.clone(config);c.geometry.rotor_radius_mm=750;assert.throws(()=>P.massProperties(c,anchors));for(const n of [0,3,5,14]){const c=P.clone(config);c.geometry.blades_per_rotor=n;assert.throws(()=>P.derive(c));}});
check('Uploaded mass and all19 bench points retain source units and duty scope',()=>{
  assert.equal(Motor.basic.mass_including_leads_kg,2.75);assert.equal(Motor.test.points.length,19);assert.equal(Motor.basic.max_power_180s_W,3400);assert.equal(Motor.maxima.recorded_input_power_W,16270);assert.equal(Motor.maxima.recorded_torque_Nm,46.25);assert.equal(Motor.test.duration_s,null);assert(Motor.duty_scope.incomplete);assert(Motor.test.points.every(p=>Math.abs(p.current_A*p.voltage_V/p.input_power_W-1)<.002));near(model.types.MN1330.mass_kg,2.75);
});
const commands={rpm:850,collectiveUpper:0,collectiveLower:0,cyclicX:0,cyclicY:0,torqueCap:46.25,inputPowerCap:3400,motorMode:'conservative_spec'};
const trim=P.trimLower(config,850,0);assert(trim);commands.collectiveLower=trim.collectiveLower;
check('Torque trim cancels steady yaw without inventing thrust',()=>{const s=P.aerodynamics(config,commands,850);assert(Math.abs(s.upper.Q-s.lower.Q)<1e-6);assert(s.T<400);assert(s.T<P.massProperties(config,anchors).mass*9.81);});
check('Large-model trim remains finite beyond the legacy windmilling bracket',()=>{for(const rpm of [2000,2100,2400]){const t=P.trimLower(config,rpm,0);assert(t);const s=P.aerodynamics(config,{...commands,collectiveLower:t.collectiveLower},rpm);assert(Number.isFinite(s.T));assert(Math.abs(s.upper.Q-s.lower.Q)<1e-6);}});
check('Blade count changes aerodynamic result as well as CAD mass',()=>{const values=[];for(const n of [4,8,12]){const c=P.clone(config);c.geometry.blades_per_rotor=n;values.push(P.aerodynamics(c,commands,850).T);}assert(new Set(values.map(x=>x.toFixed(2))).size===3);});
check('Countershaft spin-up conserves yaw and shaft work',()=>{
  const f=new P.Flight(config,anchors);f.commands={...commands};const before=f.shaftOmega.slice(),dt=1/120;f.step(dt);near(f.lastMoment[2],0,1e-7);
  let work=0,energy=0;for(let k=0;k<2;k++){const I=f.properties.rotorInertia[k],Q=k===0?f.aero.upper.Q:f.aero.lower.Q;energy+=.5*I*(f.shaftOmega[k]**2-before[k]**2);work+=(f.lastShaftTorque[k]-Q)*(f.shaftOmega[k]+before[k])*.5*dt;}near(work,energy,1e-8);
});
check('Pitch cyclic creates body torque in the requested direction',()=>{
  const f=new P.Flight(config,anchors);f.position[2]+=5;f.shaftOmega=[850,850].map(n=>n*2*Math.PI/60);f.commands={...commands,cyclicX:.3};f.step(1/120);assert(f.lastMoment[0]>0);assert(f.omega[0]>0);near(P.length(f.quaternion),1,1e-10);
});
check('180s-case electrical power and recorded torque bound shaft spin-up',()=>{
  const f=new P.Flight(config,anchors);f.commands={...commands,rpm:2100};for(let i=0;i<1800;i++){f.step(1/120);assert(f.lastInputPowerPerMotor.every(p=>p<=3400+1e-6));}
  assert(f.height<1e-8);assert(Math.max(...f.shaftOmega)*60/(2*Math.PI)<1800);assert(f.shaftOmega.every(Number.isFinite));assert(f.lastForce[2]<f.properties.mass*9.81);assert(f.lastShaftTorque.every(t=>Math.abs(t)<=46.250001));
});
check('Recorded maxima remain an unqualified bounded study, not a continuous curve',()=>{
  const f=new P.Flight(config,anchors);f.commands={...commands,motorMode:'bench_peak',rpm:2100};for(let i=0;i<1200;i++){f.step(1/120);assert(f.lastInputPowerPerMotor.every(p=>p<=16270+1e-6));assert(f.lastShaftTorque.every(t=>t<=46.250001));}assert.equal(f.height,0);assert.equal(f.lastMotorLimits.continuous_rating_verified,false);assert.equal(f.lastMotorLimits.time_reference_s,null);
});
check('180s is a time boundary; larger test points acquire no invented dwell time',()=>{
  const f=new P.Flight(config,anchors);f.commands={...commands};f.time=179.999;assert.throws(()=>f.step(.01),/180-s/);near(f.time,179.999);
  assert.equal(P.motorLimits(config,{motorMode:'bench_peak'}).time_reference_s,null);assert.equal(P.motorLimits(config,{motorMode:'conservative_spec'}).time_reference_s,180);
  const free=P.motorLimits(config,{motorMode:'free_assumption',torqueCap:150,inputPowerCap:40000});assert.equal(free.torque_Nm,150);assert.equal(free.inputPower_W,40000);assert.equal(free.continuous_rating_verified,false);
});
check('Motor off creates no RPM or free hover',()=>{const f=new P.Flight(config,anchors);f.commands={...commands,rpm:0,torqueCap:0};for(let i=0;i<120;i++)f.step(1/120);assert.equal(f.height,0);assert.equal(Math.max(...f.shaftOmega),0);assert(f.lastForce[2]<.01);});
const hover=P.hoverStudy(config,anchors,{payload:100,payloadZ:.9},commands);
check('Hover demand is compared to the actual NS52x20 reference without transferring its thrust',()=>{assert(hover.found);assert(hover.rpm>1800);assert(hover.shaftPower_W>10000);assert(hover.torques_Nm.every(t=>t>Motor.maxima.recorded_torque_Nm));assert.equal(hover.motorCurveVerified,false);assert(hover.motorEvidence.exceeds_recorded_input&&hover.motorEvidence.exceeds_recorded_torque);assert.equal(hover.motorEvidence.custom_rotor_operating_map_verified,false);});
const out={passed:true,checks,hover_demand:hover,production_ready:false,native_sha256:model.source_native_sha256};fs.writeFileSync(path.join(O,'Simulation_Pruefung.json'),JSON.stringify(out,null,2)+'\n');console.log(JSON.stringify(hover,null,2));
