// Preliminary propulsion requirement ranges; not a selected or measured rotor.
const fs=require('fs'),path=require('path'),A=require('../kreis_r04/simulation/r04_physik.js');
let rows=[];
for(const mass of [150,175,200]){
 let rpm=5000,s;for(let k=0;k<14;k++){s=A.simulate({blades:3,rIn:.09,rOut:.38,chord:.08778976166684316,thickness:.12,twist:0,pitchUpper:14,pitchLower:14,rpm,elements:48}).upper;let r=mass*9.81/(4*s.T);if(Math.abs(r-1)<.00001)break;rpm*=Math.sqrt(r);}
 rows.push({mass_case_kg:mass,rpm,thrust_each_N:s.T,shaft_each_kW:s.P/1000,torque_each_Nm:s.Q,required_continuous_shaft_plus30pct_kW:s.P/1000*1.3,electric_total_at_eta082_kW:s.P*4/.82/1000,pack_current_at92V_A:s.P*4/.82/92,energy_only_minutes_12kg_220Whkg:12*.220*.8/(s.P*4/.82/1000)*60,tip_Mach:rpm*2*Math.PI/60*.38/340,scope:'Legacy assumed 3-blade polar and geometry; actual OEM rotor/map must replace this reference'});
}
fs.writeFileSync(path.join(__dirname,'Ausgabe/Antriebsanforderungen.json'),JSON.stringify(rows,null,2));console.log(rows.map(r=>[r.mass_case_kg,r.required_continuous_shaft_plus30pct_kW.toFixed(2),r.rpm.toFixed(0)]));
