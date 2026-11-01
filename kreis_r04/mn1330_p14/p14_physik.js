/* P14 development bench. SI dynamics; CAD/linkage interface in mm/degrees.
 * No motor curve, continuous servo rating, certified laminate or flight release.
 * Aerodynamics: existing stationary axisymmetric R04 BEMT + linear cyclic
 * perturbation. Rigid body + shaft momentum, no forward-flight/CFD claim.
 */
(function(root){
  'use strict';
  const Aero=typeof module!=='undefined'?require('../simulation/r04_physik.js'):root.R04Physik;
  const Motor=typeof module!=='undefined'?require('./Motor_Daten.json'):root.P14_MOTOR_DATA;
  const D=Math.PI/180,G=9.81;
  const clone=x=>JSON.parse(JSON.stringify(x)),clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
  const add=(a,b)=>a.map((x,i)=>x+b[i]),sub=(a,b)=>a.map((x,i)=>x-b[i]),scale=(a,k)=>a.map(x=>x*k);
  const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  const length=a=>Math.sqrt(dot(a,a)),dist=(a,b)=>length(sub(a,b)),mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
  function motorLimits(c,commands={}){
    const mode=commands.motorMode??c.operating.motor_default_mode??'conservative_spec',eta=c.operating.motor_efficiency_assumption;
    if(!['conservative_spec','bench_peak','free_assumption'].includes(mode))throw Error('Unbekannter Motor-Rechenfall');
    if(mode!=='free_assumption'&&Math.abs(c.operating.battery_voltage_assumption_V-Motor.test.voltage_reference_V)>.5)throw Error('Keine Motor-Prüfreferenz für die geänderte Spannung');
    const torque=mode==='free_assumption'?(commands.torqueCap??46.25):Motor.maxima.recorded_torque_Nm;
    const inputPower=mode==='conservative_spec'?Motor.basic.max_power_180s_W:mode==='bench_peak'?Motor.maxima.recorded_input_power_W:(commands.inputPowerCap??16270);
    if(!Number.isFinite(torque)||torque<0||torque>200||!Number.isFinite(inputPower)||inputPower<0||inputPower>60000||!(eta>0&&eta<=1))throw Error('Ungültige Motorannahme');
    return{mode,torque_Nm:torque,inputPower_W:inputPower,shaftPower_W:inputPower*eta,efficiency_assumed:eta,voltage_reference_V:Motor.test.voltage_reference_V,continuous_rating_verified:false,duty_scope_incomplete:Motor.duty_scope.incomplete,time_reference_s:mode==='conservative_spec'?180:null,scope:mode==='conservative_spec'?'3400W für höchstens180s provisorisch als elektrische Decke; Leistungsseite ungeklärt':mode==='bench_peak'?'Maxima der NS52x20-Prüflinie als Rechenbegrenzung; Haltedauer unbekannt, keine zugesicherte Motorkennlinie':'Frei gewählte Annahmen; keine bestätigten Hardwaregrenzen'};
  }
  function motorEvidence(rpm,torques,inputPowers){
    const points=Motor.test.points;let reference=null;
    if(rpm>=points[0].rpm&&rpm<=points[points.length-1].rpm){let i=1;while(points[i].rpm<rpm)i++;const a=points[i-1],b=points[i],t=(rpm-a.rpm)/(b.rpm-a.rpm);reference={rpm,torque_Nm:a.torque_Nm+t*(b.torque_Nm-a.torque_Nm),input_power_W:a.input_power_W+t*(b.input_power_W-a.input_power_W),scope:'Interpolation of the NS52x20 load line; not a motor limit'};}
    return{source:'User XLS and NS52x20 table',reference_voltage_V:Motor.test.voltage_reference_V,duty_scope_incomplete:Motor.duty_scope.incomplete,power_180s_W:Motor.basic.max_power_180s_W,maximum_recorded_torque_Nm:Motor.maxima.recorded_torque_Nm,maximum_recorded_input_power_W:Motor.maxima.recorded_input_power_W,exceeds_recorded_torque:torques.some(q=>Math.abs(q)>Motor.maxima.recorded_torque_Nm),exceeds_recorded_input:inputPowers.some(p=>p>Motor.maxima.recorded_input_power_W),NS52x20_reference_at_required_rpm:reference,custom_rotor_operating_map_verified:false};
  }
  const rz=(v,a)=>[Math.cos(a)*v[0]-Math.sin(a)*v[1],Math.sin(a)*v[0]+Math.cos(a)*v[1],v[2]];
  function tilt(v,x,y){const [a,b,c]=v,u=Math.cos(y)*a+Math.sin(y)*c,w=-Math.sin(y)*a+Math.cos(y)*c;return[u,Math.cos(x)*b-Math.sin(x)*w,Math.sin(x)*b+Math.cos(x)*w];}
  function derive(c){
    const g=c.geometry,n=g.blades_per_rotor,h=Math.PI/n;
    if(!Number.isInteger(n)||n<4||n>12||n%2||!Number.isInteger(g.lift_units)||g.lift_units<1||g.lift_units>4)throw Error('4, 6, 8, 10 oder 12 Blätter; 1 bis 4 Rotorpaare');
    if(!(g.rotor_radius_mm>=650&&g.rotor_radius_mm<=800&&g.chord_mm>=115&&g.chord_mm<=145&&g.rotor_spacing_mm>=360&&g.rotor_spacing_mm<=440&&g.airfoil_tc>=.10&&g.airfoil_tc<=.16))throw Error('CAD-Parameter außerhalb des untersuchten Bereichs');
    const r=Math.max(g.root_min_radius_mm,(g.root_housing_radius_mm+g.root_clearance_mm)/Math.sin(h),4+(g.root_housing_radius_mm+g.root_phase_arm_half_width_mm+g.root_clearance_mm)/Math.tan(h));
    const br=r+g.blade_root_offset_mm,level=g.rotor_spacing_mm/2;
    if(g.rotor_radius_mm-br<350)throw Error('Freie Spannweite zu kurz');
    const upper=[r-20,g.pitch_lever_mm*Math.cos(g.neutral_pitch_deg*D),level+g.pitch_lever_mm*Math.sin(g.neutral_pitch_deg*D)];
    const delta=Math.atan2(upper[1],upper[0]);
    const lower=[g.swash_joint_r_mm*Math.cos(delta),g.swash_joint_r_mm*Math.sin(delta),g.swash_z_mm];
    const se=[g.servo_r_mm-g.servo_horn_mm*Math.cos(g.servo_neutral_deg*D),g.servo_joint_y_mm,g.servo_z_mm+g.servo_horn_mm*Math.sin(g.servo_neutral_deg*D)];
    let centres=[[0,0,0]];
    if(g.lift_units>1){const R=(2*g.rotor_radius_mm+g.unit_disk_clearance_mm)/(2*Math.sin(Math.PI/g.lift_units));centres=Array.from({length:g.lift_units},(_,i)=>rz([R,0,0],2*Math.PI*i/g.lift_units));}
    return{root_r_mm:r,blade_root_mm:br,blade_span_mm:g.rotor_radius_mm-br,level_mm:level,pitch_joint_delta_deg:delta/D,pitch_link_length_mm:dist(upper,lower),servo_link_length_mm:dist([g.servo_swash_x_mm,g.servo_joint_y_mm,g.swash_z_mm-20],se),unit_centres_mm:centres,phase_pin_r_mm:Math.max(185,r+86)};
  }
  function rootSolve(f,lo,hi,guess){
    const roots=[];let x0=lo,y0=f(x0);
    for(let i=1;i<=80;i++){const x1=lo+(hi-lo)*i/80,y1=f(x1);if(y0*y1<=0){let a=x0,b=x1;for(let j=0;j<35;j++){const m=(a+b)/2;if(f(a)*f(m)<=0)b=m;else a=m;}roots.push((a+b)/2);}x0=x1;y0=y1;}
    if(!roots.length)throw Error('Anlenkung außerhalb Stellbereich');return roots.sort((a,b)=>Math.abs(a-guess)-Math.abs(b-guess))[0];
  }
  function solve(c,collective=0,tx=0,ty=0,rotorAngle=0){
    const g=c.geometry,q=derive(c),x=tx*D,y=ty*D,sw=g.swash_z_mm+collective;
    let gamma=0;
    const fy=a=>tilt(rz([g.servo_swash_x_mm,g.servo_joint_y_mm,-20],a),x,y)[1]-g.servo_joint_y_mm;
    for(let i=0;i<10;i++){const e=fy(gamma);gamma-=e/((fy(gamma+1e-6)-e)/1e-6);}
    const servo=[],sp=[],pitches=[],pp=[];
    for(const az of [0,120,240]){
      const a=az*D,upper=tilt(rz([g.servo_swash_x_mm,g.servo_joint_y_mm,-20],a+gamma),x,y);upper[2]+=sw;
      const end=alpha=>rz([g.servo_r_mm-g.servo_horn_mm*Math.cos(alpha),g.servo_joint_y_mm,g.servo_z_mm+g.servo_horn_mm*Math.sin(alpha)],a);
      const alpha=rootSolve(t=>dist(end(t),upper)-q.servo_link_length_mm,g.servo_min_deg*D,g.servo_max_deg*D,g.servo_neutral_deg*D);
      servo.push(alpha/D);sp.push([end(alpha),upper]);
    }
    for(let i=0;i<g.blades_per_rotor;i++){
      const a=(i*360/g.blades_per_rotor+rotorAngle)*D,lower=tilt(rz([g.swash_joint_r_mm,0,0],a+q.pitch_joint_delta_deg*D),x,y);lower[2]+=sw;
      const end=t=>add(rz([q.root_r_mm-20,g.pitch_lever_mm*Math.cos(t),g.pitch_lever_mm*Math.sin(t)],a),[0,0,q.level_mm]);
      const t=rootSolve(t=>dist(end(t),lower)-q.pitch_link_length_mm,-10*D,35*D,g.neutral_pitch_deg*D);
      pitches.push(t/D);pp.push([lower,end(t)]);
    }
    return{pitches_deg:pitches,servo_deg:servo,servo_points_mm:sp,pitch_points_mm:pp,stationary_phase_deg:gamma/D,swash_z_mm:sw,tilt_deg:[tx,ty]};
  }
  function podPose(c,commands,sign,angle=0){
    // Both local shafts rotate negative about local Z. Ry(180) of the lower
    // pod makes the global rotations oppose. Upper CFK is keyed -24 degrees.
    const upper=sign>0,col=upper?-commands.collectiveUpper:commands.collectiveLower;
    const s=solve(c,col,upper?-commands.cyclicX:commands.cyclicX,-commands.cyclicY,angle);
    s.aero_pitch_deg=s.pitches_deg.map(p=>upper?24-p:p);return s;
  }
  function aeroParams(c,rpm,upper,lower){
    const g=c.geometry,q=derive(c),start=q.blade_root_mm/1000;
    return{blades:g.blades_per_rotor,rIn:start,rOut:g.rotor_radius_mm/1000,chord:g.chord_mm/1000,thickness:g.airfoil_tc,twist:0,spacing:g.rotor_spacing_mm/1000,rpm,pitchUpper:upper,pitchLower:lower,rho:1.225,nu:1.5e-5,elements:32,
      thicknessFunction:r=>{const t=clamp((r-start-.075)/.105,0,1);return Math.max(g.root_tc_min,35.4/g.chord_mm)*(1-t)+g.airfoil_tc*t;}};
  }
  function aerodynamics(c,commands,rpmUpper,rpmLower=rpmUpper){
    const up=podPose(c,commands,1),low=podPose(c,commands,-1);
    const p=aeroParams(c,Math.max(.01,rpmUpper),mean(up.aero_pitch_deg),mean(low.aero_pitch_deg));p.rpmLower=Math.max(.01,rpmLower);
    const result=Aero.simulate(p),eps=.15;
    const perturb=Aero.simulate({...p,pitchUpper:p.pitchUpper+eps,pitchLower:p.pitchLower+eps});
    const slopes=[(perturb.upper.T-result.upper.T)/eps,(perturb.lower.T-result.lower.T)/eps];
    if(![result.T,result.P,result.upper.Q,result.lower.Q,...slopes].every(Number.isFinite))throw Error('BEMT in diesem Betriebspunkt nicht konvergiert');
    return{...result,poses:[up,low],slopes};
  }
  function trimLower(c,rpm,upperCollective){
    const cmd={collectiveUpper:upperCollective,collectiveLower:0,cyclicX:0,cyclicY:0};
    const theta=mean(podPose(c,cmd,1).aero_pitch_deg),p=aeroParams(c,rpm,theta,12);
    // Search the reachable physical linkage range. The old generic -5..35deg
    // trim bracket includes a windmilling branch which can diverge at large
    // scale/RPM; NaN must never be accepted as a valid torque-balance root.
    const evaluate=col=>{const pitch=mean(solve(c,col).pitches_deg),s=Aero.simulate({...p,pitchLower:pitch}),f=s.lower.Q-s.upper.Q;return{pitch,f:Number.isFinite(f)?f:null};};
    let a=0,b=3.5,fa=evaluate(a).f,fb=evaluate(b).f;
    if(fa===null||fb===null||fa*fb>0){
      let found=false,last=null;
      for(let i=0;i<=14;i++){const col=-3.5+i*.5,r=evaluate(col);if(r.f===null){last=null;continue;}if(last&&last.f*r.f<=0){a=last.col;b=col;fa=last.f;fb=r.f;found=true;break;}last={col,f:r.f};}
      if(!found)return null;
    }
    for(let i=0;i<36;i++){const m=(a+b)/2,fm=evaluate(m).f;if(fm===null)return null;if(fa*fm<=0){b=m;fb=fm;}else{a=m;fa=fm;}}
    const col=(a+b)/2;return{collectiveLower:col,pitchLower:evaluate(col).pitch};
  }
  function mmul(a,v){return a.map(row=>dot(row,v));}
  function inverse(a){const[a0,a1,a2]=a,A=cross(a1,a2),B=cross(a2,a0),C=cross(a0,a1),det=dot(a0,A);if(!(det>1e-12))throw Error('Trägheit nicht positiv');return [[A[0],B[0],C[0]],[A[1],B[1],C[1]],[A[2],B[2],C[2]]].map(r=>scale(r,1/det));}
  function massProperties(c,anchors,options={}){
    const g=c.geometry,ref=anchors.reference_config.geometry;
    for(const key of Object.keys(ref))if(!['blades_per_rotor','lift_units'].includes(key)&&JSON.stringify(g[key])!==JSON.stringify(ref[key]))throw Error('Für geänderte Geometrie zuerst CAD-Massenvarianten neu erzeugen');
    const pair=anchors.cases[String(g.blades_per_rotor)];if(!pair||!pair.all_valid)throw Error('CAD-Massenfall fehlt');
    const q=derive(c),pieces=q.unit_centres_mm.map(r=>({m:pair.mass_kg,cg:add(scale(r,.001),pair.cg_m),J:pair.inertia_cg_kgm2}));
    const zero=[[0,0,0],[0,0,0],[0,0,0]],payload=options.payload??c.operating.payload_kg,payloadZ=options.payloadZ??.9;
    if(!(payload>=0&&payload<=150&&payloadZ>=0&&payloadZ<=1.3))throw Error('Nutzlast außerhalb des Rechenbereichs');
    pieces.push({m:payload,cg:[0,0,payloadZ],J:zero},{m:c.operating.battery_mass_assumed_kg+c.operating.electronics_mass_assumed_kg+(options.extraMass??0),cg:[0,0,0],J:zero});
    const m=pieces.reduce((s,p)=>s+p.m,0),cg=[0,1,2].map(i=>pieces.reduce((s,p)=>s+p.m*p.cg[i],0)/m),J=zero.map(r=>r.slice());
    for(const p of pieces){const v=sub(p.cg,cg),r2=dot(v,v);for(let i=0;i<3;i++)for(let j=0;j<3;j++)J[i][j]+=p.J[i][j]+p.m*((i===j?r2:0)-v[i]*v[j]);}
    const bounds=[0,1].map(i=>(Math.max(...q.unit_centres_mm.map(r=>r[i]))-Math.min(...q.unit_centres_mm.map(r=>r[i]))+2*g.rotor_radius_mm)/1000);
    return{mass:m,dryCAD:pair.mass_kg*g.lift_units,cg,inertia:J,inverseInertia:inverse(J),rotorInertia:pair.rotor_relative_inertia_kgm2,centres:q.unit_centres_mm.map(r=>scale(r,.001)),bounds_m:bounds,vehicleEnvelopeMet:bounds[0]<=2.1&&bounds[1]<=1.7&&g.rotor_spacing_mm+110<=600,multiUnitConnectionMissing:g.lift_units>1,payloadLumped:true};
  }
  function hoverStudy(c,anchors,options,commands){
    const mass=massProperties(c,anchors,options),cmd={...commands,cyclicX:0,cyclicY:0};let trim=trimLower(c,850,cmd.collectiveUpper);
    if(!trim)return{found:false,reason:'Drehmomentausgleich außerhalb Pitchbereich'};
    cmd.collectiveLower=trim.collectiveLower;let rpm=850;
    for(let pass=0;pass<2;pass++){
      let a=100,b=2800;
      if(aerodynamics(c,cmd,b).T*c.geometry.lift_units<mass.mass*G)return{found:false,reason:'Bis 2800/min kein Schwebepunkt im Rechenmodell'};
      for(let i=0;i<22;i++){const m=(a+b)/2;if(aerodynamics(c,cmd,m).T*c.geometry.lift_units<mass.mass*G)a=m;else b=m;}
      rpm=(a+b)/2;trim=trimLower(c,rpm,cmd.collectiveUpper);if(!trim)return{found:false,reason:'Pitch zum Drehmomentausgleich nicht erreichbar'};cmd.collectiveLower=trim.collectiveLower;
    }
    const s=aerodynamics(c,cmd,rpm),N=c.geometry.lift_units;
    const inputs=[s.upper.P,s.lower.P].map(p=>p/c.operating.motor_efficiency_assumption),torques=[s.upper.Q,s.lower.Q];
    return{found:true,rpm,collectiveLower:cmd.collectiveLower,thrust_N:s.T*N,shaftPower_W:s.P*N,electricalPowerAssumed_W:inputs.reduce((a,b)=>a+b,0)*N,efficiency_assumed:c.operating.motor_efficiency_assumption,torques_Nm:torques,tipMach:s.tipMach,stallFraction:s.stalledFraction,motorCurveVerified:false,motorEvidence:motorEvidence(rpm,torques,inputs)};
  }
  function qmul(a,b){return[a[0]*b[0]-dot(a.slice(1),b.slice(1)),...add(add(scale(b.slice(1),a[0]),scale(a.slice(1),b[0])),cross(a.slice(1),b.slice(1)))];}
  function qrotate(q,v){return qmul(qmul(q,[0,...v]),[q[0],-q[1],-q[2],-q[3]]).slice(1);}
  class Flight{
    constructor(config,anchors,options={}){this.config=clone(config);this.anchors=anchors;this.options={...options};this.properties=massProperties(this.config,anchors,options);this.commands={rpm:850,collectiveUpper:0,collectiveLower:0,cyclicX:0,cyclicY:0,torqueCap:46.25,inputPowerCap:3400,motorMode:config.operating.motor_default_mode??'conservative_spec'};this.reset();}
    reset(){const p=this.properties;this.floor=this.config.geometry.rotor_spacing_mm/2000+.09+p.cg[2];this.position=[0,0,this.floor];this.velocity=[0,0,0];this.quaternion=[1,0,0,0];this.omega=[0,0,0];this.shaftOmega=[0,0];this.angle=[0,0];this.time=0;this.aeroAge=1;this.aero=null;this.contact=true;this.lastForce=[0,0,0];this.lastMoment=[0,0,0];}
    step(dt){
      if(!(dt>0&&dt<=.025))throw Error('Integrationsschritt muss 0..25ms sein');
      const p=this.properties,c=this.config,cmd=this.commands,q=derive(c),N=c.geometry.lift_units;
      if((cmd.motorMode??c.operating.motor_default_mode)==='conservative_spec'&&this.time+dt>180+1e-8)throw Error('180-s-Zeitbezug erreicht; keine bestätigte Dauerleistung für weitere Flugrechnung');
      if(![cmd.rpm,cmd.collectiveUpper,cmd.collectiveLower,cmd.cyclicX,cmd.cyclicY,cmd.torqueCap].every(Number.isFinite)||cmd.rpm<0||cmd.rpm>2400||Math.abs(cmd.collectiveUpper)>3.5||Math.abs(cmd.collectiveLower)>3.5||Math.hypot(cmd.cyclicX,cmd.cyclicY)>.500001||cmd.torqueCap<0||cmd.torqueCap>200)throw Error('Stellgröße außerhalb des Rechenbereichs');
      this.aeroAge+=dt;
      if(this.aeroAge>=.1){this.aero=aerodynamics(c,cmd,...this.shaftOmega.map(w=>w*60/(2*Math.PI)));this.aeroAge=0;}
      const s=this.aero,rot=[s.upper,s.lower],directions=[-1,1],wdot=[],torque=[],inputPower=[],limits=motorLimits(c,cmd);
      for(let k=0;k<2;k++){
        const before=this.shaftOmega[k],maxMidpoint=before+(limits.torque_Nm+Math.abs(rot[k].Q))*dt/(2*p.rotorInertia[k]);
        const cap=Math.min(limits.torque_Nm,limits.shaftPower_W/Math.max(maxMidpoint,1e-6));
        // Positive drive only; reducing target RPM coasts under aerodynamic
        // torque. No unsupported regenerative ESC/battery behavior is assumed.
        torque[k]=cmd.rpm===0?0:clamp(rot[k].Q+(cmd.rpm*2*Math.PI/60-before)*4,0,cap);
        wdot[k]=(torque[k]-rot[k].Q)/p.rotorInertia[k];
        if(this.shaftOmega[k]<=0&&wdot[k]<0)wdot[k]=0;
        this.shaftOmega[k]=Math.max(0,this.shaftOmega[k]+wdot[k]*dt);this.angle[k]=(this.angle[k]-this.shaftOmega[k]*dt)%(2*Math.PI);
        inputPower[k]=torque[k]*(before+this.shaftOmega[k])*.5/limits.efficiency_assumed;
      }
      const force=[0,0,s.T*N],moment=[0,0,0],n=c.geometry.blades_per_rotor;
      for(let k=0;k<2;k++){
        const sign=k===0?1:-1,pose=podPose(c,cmd,sign,this.angle[k]/D),meanPitch=mean(pose.aero_pitch_deg),rmean=rot[k].T>1e-7?rot[k].r.reduce((sum,r,i)=>sum+r*rot[k].dT[i]*rot[k].dr,0)/rot[k].T:.5*(q.blade_root_mm+c.geometry.rotor_radius_mm)*.001;
        for(const centre of p.centres){
          for(let i=0;i<n;i++){
            const a=i*2*Math.PI/n+this.angle[k];let r=rz([rmean,0,sign*q.level_mm*.001],a);if(sign<0)r=[-r[0],r[1],r[2]];
            const T=(rot[k].T+s.slopes[k]*(pose.aero_pitch_deg[i]-meanPitch))/n;
            const arm=sub(add(centre,r),p.cg);const M=cross(arm,[0,0,T]);for(let j=0;j<3;j++)moment[j]+=M[j];
          }
        }
      }
      const H=N*(directions[0]*p.rotorInertia[0]*this.shaftOmega[0]+directions[1]*p.rotorInertia[1]*this.shaftOmega[1]);
      moment[2]+=N*(-directions[0]*s.upper.Q-directions[1]*s.lower.Q-directions[0]*p.rotorInertia[0]*wdot[0]-directions[1]*p.rotorInertia[1]*wdot[1]);
      const gyro=cross(this.omega,add(mmul(p.inertia,this.omega),[0,0,H]));
      const accOmega=mmul(p.inverseInertia,sub(moment,gyro));
      this.omega=add(this.omega,scale(accOmega,dt));const dq=qmul(this.quaternion,[0,...this.omega]);this.quaternion=add(this.quaternion,scale(dq,.5*dt));this.quaternion=scale(this.quaternion,1/length(this.quaternion));
      let f=qrotate(this.quaternion,force);f[2]-=p.mass*G;
      // Explicit assumed isotropic drag; stationary BEMT is not forward-flight validation.
      f=sub(f,scale(this.velocity,.5*1.225*.8*length(this.velocity)));
      this.velocity=add(this.velocity,scale(f,dt/p.mass));this.position=add(this.position,scale(this.velocity,dt));
      this.contact=this.position[2]<=this.floor;
      if(this.contact){this.position[2]=this.floor;this.velocity=[0,0,Math.max(0,this.velocity[2])];this.omega=[0,0,0];this.quaternion=[1,0,0,0];}
      this.lastForce=force;this.lastMoment=moment;this.lastShaftTorque=torque;this.lastInputPowerPerMotor=inputPower;this.lastMotorLimits=limits;this.time+=dt;
      return this;
    }
    get height(){return this.position[2]-this.floor;}
  }
  const api={D,G,clone,clamp,add,sub,scale,dot,cross,length,rz,tilt,derive,solve,podPose,aeroParams,aerodynamics,trimLower,massProperties,hoverStudy,motorLimits,motorEvidence,qrotate,Flight};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.P14Physics=api;
})(typeof window!=='undefined'?window:globalThis);
