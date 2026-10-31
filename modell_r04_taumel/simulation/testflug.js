#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),F=require('./flugphysik.js'),S=require('./szenarien.js');
const out=path.join(__dirname,'Ergebnisse');fs.mkdirSync(out,{recursive:true});
function run(c,extra={}){let s=new F.Flight({...c.options,...extra});if(c.initial){if(c.initial.p)s.p=[...c.initial.p];if(c.initial.angles)s.q=F.quat(...c.initial.angles.map(v=>v*F.D));}
 const rows=[];let errorSq=0,count=0,maxTilt=0,maxError=0,minBus=99,maxCurrent=0,maxLoad=0,maxDuty=0;
 for(let n=0;n<Math.round(c.duration/s.c.dt)&&!s.crashed;n++){let{target,external}=S.inputs(s,c);let r=s.step(target,external);let e=Math.hypot(...r.p.map((v,i)=>v-target.position[i]));if(s.t>c.duration-5){errorSq+=e*e;count++;}maxTilt=Math.max(maxTilt,Math.hypot(r.euler[0],r.euler[1]));maxError=Math.max(maxError,e);minBus=Math.min(minBus,r.bus);maxCurrent=Math.max(maxCurrent,r.current);maxLoad=Math.max(maxLoad,...r.servoLoadNm);maxDuty=Math.max(maxDuty,...r.duty);if(n%Math.round(.05/s.c.dt)===0)rows.push(r);}
 const rms=count?Math.sqrt(errorSq/count):null,last=s.snapshot(S.inputs(s,c).target),positionError=Math.hypot(...last.p.map((v,i)=>v-last.target[i]));
 let status=s.crashed?'ABSTURZ_IM_MODELL':s.envelopeViolations?'AUSSERHALB_GEPRUEFTER_KINEMATIK':rms!==null&&rms<.15&&positionError<.15?'STABIL_IM_MODELL':'REGELZIEL_VERFEHLT';
 // P10 ground missions: success = no crash, inside envelope, landed upright and motors stopped.
 const mission=String(c.mission||'').startsWith('p10')?s._manager:null;
 if(mission&&!s.crashed&&!s.envelopeViolations)status=mission.phase==='AUS'&&s.onGround&&Math.hypot(last.euler[0],last.euler[1])<5?'STABIL_IM_MODELL':'REGELZIEL_VERFEHLT';
 return{summary:{name:c.name,status,duration_s:s.t,mass_kg:s.mass,hover_rpm:s.rpmHover,options:{...s.c},position_rms_last5s_m:rms,final_position_error_m:positionError,max_position_error_m:maxError,max_tilt_deg:maxTilt,min_bus_V:minBus,max_bus_current_A:maxCurrent,max_servo_load_Nm:maxLoad,max_duty:maxDuty,max_link_closure_mm:s.maxClosure,kinematic_envelope_violations:s.envelopeViolations,min_blade_pitch_deg:s.minPitch,max_blade_pitch_deg:s.maxPitch,max_cyclic_deg:s.maxCyclic,saturation_events:s.saturation,final:last,...(mission?{mission_phase:mission.phase,mission_events:mission.events,max_touchdown_speed_mps:s.maxImpactSpeed,landed:!!s.onGround}:{})},rows};}
if(require.main===module){const results=[];for(const c of S.cases){let r=run(c);results.push(r.summary);fs.writeFileSync(path.join(out,c.name+'.json'),JSON.stringify(r.rows));console.log(c.name,r.summary.status,'rms',r.summary.position_rms_last5s_m?.toFixed(3),'tilt',r.summary.max_tilt_deg.toFixed(1));}
 const report={status:'UNVALIDATED_MODEL_TESTS_NOT_FLIGHT_CLEARANCE',cad_sha256:F.CAD.source_sha256,results};fs.writeFileSync(path.join(out,'Testbericht.json'),JSON.stringify(report,null,2));fs.writeFileSync(path.join(out,'Testbericht.js'),'globalThis.H01_TESTS='+JSON.stringify(report)+';\n');}
module.exports={run};
