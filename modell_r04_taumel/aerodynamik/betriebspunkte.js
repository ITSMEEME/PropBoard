#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),P=require('../../kreis_r04/simulation/r04_physik.js'),A=require('../../modell_r04/auslegung/antrieb.js'),L=require('./polar_lookup.js'),M=require('../simulation/modell_h01.json');
const mass=M.mass_kg+6*(69-9)/1000,par=M.geometry;
const geo={rIn:.048,rOut:.1875,chord:.03,blades:8,spacing:.06,thickness:.12,twist:0,elements:40,pitchUpper:14};
function at(rpm,n){const input={...geo,rpm};if(n)input.polarFunction=(alpha,re,tc)=>L.query(alpha,re,n)||P.polar(alpha,re,tc);let lo=0,hi=25;
 for(let i=0;i<14;i++){let mid=(lo+hi)/2,s=P.simulate({...input,pitchLower:mid});if(s.lower.Q>s.upper.Q)hi=mid;else lo=mid;}
 const pl=(lo+hi)/2,s=P.simulate({...input,pitchLower:pl});return{s,pl};}
function point(thrust,n){let lo=800,hi=5000;for(let i=0;i<15;i++){let mid=(lo+hi)/2;if(at(mid,n).s.T<thrust)lo=mid;else hi=mid;}
 let rpm=(lo+hi)/2,{s,pl}=at(rpm,n),system=A.systemPoint(A.MOTOR_ECO2_2306_1900,A.BATTERY_TATTU_1550_6S,{rpm,Q:s.upper.Q},{rpm,Q:s.lower.Q},6.5,.6);
 let final=0,missing=0,alphas=[],res=[];for(let rotor of [s.upper,s.lower])for(let i=0;i<rotor.r.length;i++){final++;if(n&&!L.query(rotor.alpha[i],rotor.re[i],n))missing++;alphas.push(rotor.alpha[i]);res.push(rotor.re[i]);}
 return{rpm,pitch_upper_deg:14,pitch_lower_deg:pl,total_thrust_N:s.T,upper_thrust_N:s.upper.T,lower_thrust_N:s.lower.T,rotor_Q_Nm:[s.upper.Q,s.lower.Q],shaft_power_W:s.P,bus_power_W:system.pBus,bus_current_A:system.batteryCurrent,duty:system.duty,feasible_electrical_model:system.feasible,pitch_inside_nominal_range:pl<=21,final_section_fallback_fraction:n?missing/final:0,alpha_range_deg:[Math.min(...alphas),Math.max(...alphas)],re_range:[Math.min(...res),Math.max(...res)]};}
const scenarios=[];for(let n of [0,4,9]){let scenario={name:n?'CAD_XFOIL_N'+n:'SIMPLIFIED_HISTORICAL',mass_kg:mass,assumed_servo_mass_g:69,hover:point(mass*9.81,n),tw2:point(2*mass*9.81,n)};scenarios.push(scenario);console.log(scenario.name,'hover',scenario.hover.rpm.toFixed(0),'TW2',scenario.tw2.rpm.toFixed(0),'hover Pbus',scenario.hover.bus_power_W.toFixed(0),'W','fallback',scenario.hover.final_section_fallback_fraction);}
fs.writeFileSync(path.join(__dirname,'Ausgabe/Betriebspunkte_Savox.json'),JSON.stringify({status:'CALCULATED_HYBRID_BEMT_NOT_STAND_MEASUREMENTS',mass_kg:mass,scenarios,limitations:'Actual CAD-profile XFOIL polars with explicit original-polar fallback outside converged range; no measured roughness, wake, thrust, torque or thermal validation. Motor/BEC/servo current incomplete.'},null,2));
