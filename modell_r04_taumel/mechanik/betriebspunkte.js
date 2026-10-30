#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path');
const root=path.join(__dirname,'../..');
const P=require(path.join(root,'kreis_r04/simulation/r04_physik.js'));
const A=require(path.join(root,'modell_r04/auslegung/antrieb.js'));
const par=JSON.parse(fs.readFileSync(path.join(__dirname,'../cad/parameter.json')));
const holders=JSON.parse(fs.readFileSync(path.join(__dirname,'../halterungen/Ausgabe/Geometriepruefung_H01.json')));
const base=holders.assembly.mass_budget.total_nominal_g/1000;
const geo={rIn:par.blade.r_airfoil_start/1000,rOut:par.blade.r_tip/1000,chord:par.blade.chord/1000,
 spacing:(par.levels_z[0]-par.levels_z[1])/1000,blades:par.blade.count,thickness:par.blade.tc,twist:0};
function at(rpm){
 const input={...geo,rpm,pitchUpper:par.pitch_hover_deg[0]};
 const pl=P.balanceLowerPitch(input);if(pl===null)throw Error('No torque-balanced lower pitch');
 const s=P.simulate({...input,pitchLower:pl});return {s,pl};
}
function forThrust(thrust){
 let lo=300,hi=8000;
 for(let i=0;i<21;i++){const mid=(lo+hi)/2;if(at(mid).s.T<thrust)lo=mid;else hi=mid;}
 const {s,pl}=at(hi);
 const system=A.systemPoint(A.MOTOR_ECO2_2306_1900,A.BATTERY_TATTU_1550_6S,{rpm:hi,Q:s.upper.Q},{rpm:hi,Q:s.lower.Q},6.5,.6);
 return {rpm:hi,pitch_upper_deg:par.pitch_hover_deg[0],pitch_lower_deg:pl,total_thrust_N:s.T,
  upper_thrust_N:s.upper.T,lower_thrust_N:s.lower.T,torque_each_Nm:[s.upper.Q,s.lower.Q],
  model_bus_power_W:system.pBus,model_duty:system.duty,feasible_model:system.feasible,
  limitations:'BEMT and electrical model unvalidated; no servo/BEC electrical power included'};
}
const out=[];
for(const servoMassG of [9,20,60]){
 const mass=base+6*(servoMassG-9)/1000;
 const hover=forThrust(mass*9.81),tw2=forThrust(2*mass*9.81);
 out.push({name:'H01_servo_'+servoMassG+'g_each',assumed_servo_mass_g:servoMassG,mass_kg:mass,
  hover,tw2,overspeed_screening_rpm:1.2*tw2.rpm});
 console.log(out.at(-1).name,'mass kg',mass.toFixed(3),'hover',hover.rpm.toFixed(0),'TW2',tw2.rpm.toFixed(0));
}
fs.writeFileSync(path.join(__dirname,'Betriebspunkte_H01.json'),JSON.stringify({status:'CONDITIONAL_BEMT_MASS_FEEDBACK_NOT_PROOF',scenarios:out},null,2));
