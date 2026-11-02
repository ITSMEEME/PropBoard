// Alternative separated single-rotor modules: every motor count 1..10.
// Aerodynamic screening only; odd counts have NO demonstrated yaw trim.
const fs=require('fs'),path=require('path');
const B=path.resolve(__dirname,'..'),P=require(B+'/kreis_r04/mn1330_p14/p14_physik.js'),A=require(B+'/kreis_r04/simulation/r04_physik.js');
const cfg=require(B+'/kreis_r04/mn1330_p14/parameter.json'),mass=require(B+'/kreis_r04/mn1330_p14/Ausgabe/Massenvarianten.json');
let rows=[];
function layout(n,D){let best;for(let cols=1;cols<=n;cols++){let lines=Math.ceil(n/cols),x=cols*D+(cols-1)*.08,y=lines*D+(lines-1)*.08;let r={x,y,cols,lines,ratio:Math.max(x/2.1,y/1.7)};if(!best||r.ratio<best.ratio)best=r;}return best;}
for(let motors=1;motors<=10;motors++)for(let blades of [4,6,8,10,12])for(let radius of [650,710,750,800]){
 let c=JSON.parse(JSON.stringify(cfg));Object.assign(c.geometry,{blades_per_rotor:blades,rotor_radius_mm:radius});let d=P.derive(c),ref=JSON.parse(JSON.stringify(c));ref.geometry.rotor_radius_mm=710;let dr=P.derive(ref);
 let moduleMass=(mass.cases[blades].mass_kg+8.84*blades/8*(d.blade_span_mm/dr.blade_span_mm-1))/2;
 let totalMass=114+motors*moduleMass,best;
 for(let pitch of [10,12,14]){
  let rpm=1800,s;
  for(let i=0;i<7;i++){s=A.simulate({...P.aeroParams(c,rpm,pitch,pitch),elements:24}).upper;if(!(s.T>0))break;let ratio=totalMass*9.81/(motors*s.T);if(Math.abs(ratio-1)<.00015)break;rpm*=Math.sqrt(ratio);}
  if(!s||!Number.isFinite(s.P)||!(s.P>0)||s.stalledFraction>.1||rpm*2*Math.PI/60*radius/1000/340>.65||Math.abs(s.T*motors/totalMass/9.81-1)>.005)continue;
  let r={rpm,pitch_deg:pitch,electric_kW:s.P*motors/.82/1000,per_motor_shaft_kW:s.P/1000,torque_Nm:s.Q,thrust_N:s.T*motors,stall_fraction:s.stalledFraction};if(!best||r.electric_kW<best.electric_kW)best=r;
 }
 let l=layout(motors,2*radius/1000),row={architecture:'separate_single_rotors',motors,blades,radius_mm:radius,free_blade_length_mm:d.blade_span_mm,mass_kg:totalMass,module_mass_proxy_kg:moduleMass,envelope_x_m:l.x,envelope_y_m:l.y,rotor_envelope_fits:l.ratio<=1+1e-9,yaw_trim_demonstrated:false,odd_motor_count:motors%2===1,found:!!best};
 if(best)Object.assign(row,best,{minimum_motor_shaft_kW_30pct:best.per_motor_shaft_kW*1.3,hover_min_12kg_220Whkg:12*.220*.8/best.electric_kW*60});rows.push(row);
}
let designs=rows.filter(r=>r.found).flatMap(r=>[3.4,10,20,30,40,60].map(kW=>({...r,rated_shaft_kW_assumed:kW,hover_power_covered:kW>=r.per_motor_shaft_kW,reserve_30pct_covered:kW>=r.per_motor_shaft_kW*1.3})));
function csv(name,rs){let keys=[...new Set(rs.flatMap(r=>Object.keys(r)))];fs.writeFileSync(path.join(__dirname,name),keys.join(',')+'\n'+rs.map(r=>keys.map(k=>r[k]??'').join(',')).join('\n')+'\n');}
csv('Einzelrotoren_1_bis_10.csv',rows);csv('Einzelrotoren_Motorkombinationen.csv',designs);fs.writeFileSync(path.join(__dirname,'Einzelrotoren.json'),JSON.stringify({rows,designs},null,2));
console.log('Calculated',rows.length,'rotor configurations;',designs.length,'assumed motor ratings');
