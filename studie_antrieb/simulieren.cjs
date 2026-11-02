// Stationary P14 design sweep; speculative ratings are mechanical shaft ratings.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const base=path.resolve(__dirname,'..'), P=require(base+'/kreis_r04/mn1330_p14/p14_physik.js'), A=require(base+'/kreis_r04/simulation/r04_physik.js');
const config=require(base+'/kreis_r04/mn1330_p14/parameter.json'), masses=require(base+'/kreis_r04/mn1330_p14/Ausgabe/Massenvarianten.json');
const clone=x=>JSON.parse(JSON.stringify(x)), G=9.81, eta=.82;
function run(c,rpm,pitch,lower,elements=24){let local=clone(c);local.geometry.lift_units=1;return A.simulate({...P.aeroParams(local,rpm,pitch,lower),elements});}
function balance(c,rpm,pitch,elements=24){
 c=clone(c);c.geometry.lift_units=1;
 const cmd={collectiveUpper:0,collectiveLower:0,cyclicX:0,cyclicY:0};
 const lim=[-3.5,3.5].map(col=>{cmd.collectiveLower=col;return P.podPose(c,cmd,-1).aero_pitch_deg.reduce((a,b)=>a+b)/c.geometry.blades_per_rotor;});
 let [lo,hi]=lim, f=x=>{let s=run(c,rpm,pitch,x,elements);return s.lower.Q-s.upper.Q;},fl=f(lo),fh=f(hi);
 if(!Number.isFinite(fl)||!Number.isFinite(fh)||fl*fh>0)return null;
 for(let i=0;i<15;i++){let mid=(lo+hi)/2,fm=f(mid);if(!Number.isFinite(fm))return null;if(fl*fm<=0)hi=mid;else{lo=mid;fl=fm;}}
 let lower=(lo+hi)/2,s=run(c,rpm,pitch,lower,elements);return {s,lower};
}
function hover(c,mass,pitch,elements=24){
 let rpm=1800,res;
 for(let i=0;i<7;i++){res=balance(c,rpm,pitch,elements);if(!res||!(res.s.T>0))return null;let ratio=mass*G/(c.geometry.lift_units*res.s.T);if(Math.abs(ratio-1)<.00015)break;rpm*=Math.sqrt(ratio);if(rpm>4500||rpm<100)return null;}
 res=balance(c,rpm,pitch,elements);if(!res)return null;
 let s=res.s,N=c.geometry.lift_units;
 return {rpm,pitch_upper_deg:pitch,pitch_lower_deg:res.lower,thrust_N:s.T*N,shaft_kW:s.P*N/1000,electric_kW:s.P*N/eta/1000,torque_Nm:Math.max(s.upper.Q,s.lower.Q),per_motor_shaft_kW:Math.max(s.upper.P,s.lower.P)/1000,tip_Mach:s.tipMach,stall_fraction:s.stalledFraction,FM:s.figureOfMerit,thrust_error_fraction:s.T*N/(mass*G)-1,torque_error_fraction:Math.abs(s.upper.Q-s.lower.Q)/Math.max(s.upper.Q,s.lower.Q)};
}
if(require.main===module){
const extra=process.argv.includes('--add-five-pairs');
let prior=extra?require('./Ergebnisse.json'):null;
let rows=prior?prior.rows:[],designs=prior?prior.designs:[],checks=[];
for(let units of (extra?[5]:[1,2,3,4,5]))for(let blades of [4,6,8,10,12])for(let radius of [650,710,750,800]){
 let c=clone(config);Object.assign(c.geometry,{lift_units:units,blades_per_rotor:blades,rotor_radius_mm:radius});
 let local=clone(c);local.geometry.lift_units=1;
 let d=P.derive(local),ref=clone(local);ref.geometry.rotor_radius_mm=710;let dr=P.derive(ref);
 if(units>1){let ring=(2*radius+80)/(2*Math.sin(Math.PI/units));d.unit_centres_mm=Array.from({length:units},(_,i)=>[ring*Math.cos(i*2*Math.PI/units),ring*Math.sin(i*2*Math.PI/units),0]);}
 // Only the measured reference-radius mass is CAD-derived. Radius adjustment is an explicitly assumed blade-span proxy.
 let spanRatio=d.blade_span_mm/dr.blade_span_mm;
 let pairMass=masses.cases[blades].mass_kg + 8.84*(blades/8)*(spanRatio-1);
 let mass=100+12+2+pairMass*units, xs=d.unit_centres_mm.map(v=>v[0]),ys=d.unit_centres_mm.map(v=>v[1]);
 let width=(Math.max(...xs)-Math.min(...xs)+2*radius)/1000,height=(Math.max(...ys)-Math.min(...ys)+2*radius)/1000;
 let fits=Math.max(width,height)<=2.1+1e-9&&Math.min(width,height)<=1.7+1e-9;
 let candidates=[10,12,14].map(p=>hover(c,mass,p)).filter(Boolean).filter(v=>v.stall_fraction<=.1&&v.tip_Mach<=.65&&Math.abs(v.thrust_error_fraction)<.005&&v.torque_error_fraction<.001);
 let best=candidates.sort((a,b)=>a.electric_kW-b.electric_kW)[0];
 let row={units,motors:2*units,blades,radius_mm:radius,free_blade_length_mm:d.blade_span_mm,blade_root_radius_mm:d.blade_root_mm,pair_mass_proxy_kg:pairMass,mass_kg:mass,envelope_x_m:width,envelope_y_m:height,rotor_envelope_fits:fits,connector_missing:units>1,found:!!best};
 if(best)Object.assign(row,best,{hover_min_12kg_220Whkg:12*.220*.8/best.electric_kW*60,battery_kg_15min_frozen_mass:best.electric_kW*.25/(.220*.8),minimum_motor_shaft_kW_30pct:best.per_motor_shaft_kW*1.3});
 rows.push(row);
 if(best)for(let rating of [3.4,10,20,30,40,60]){
  // A hypothetical torque capability at the hover RPM, not an inferred real motor map.
  let cap=rating*1000/(best.rpm*2*Math.PI/60),factor=Math.min(rating/best.per_motor_shaft_kW,cap/best.torque_Nm);
  designs.push({...row,rated_shaft_kW_assumed:rating,assumed_torque_cap_Nm:cap,hover_power_covered:factor>=1,reserve_30pct_covered:factor>=1.3,thrust_weight_power_similarity_estimate:factor**(2/3),motor_mass_not_resized:true});
 }
 console.log(`pairs=${units} blades=${blades} R=${radius}: ${best?best.electric_kW.toFixed(2)+' kW':'no admissible trim'}`);
}
let standard=rows.find(r=>r.units===1&&r.blades===8&&r.radius_mm===710),c=clone(config);
checks.push({name:'standard_12deg_24_elements',result:hover(c,174.56,12,24)});
checks.push({name:'standard_12deg_48_elements',result:hover(c,174.56,12,48)});
let same=P.hoverStudy(c,masses,{}, {collectiveUpper:0});checks.push({name:'existing_P14_hoverStudy',result:same});
if(rows.length!==100||!standard?.found)throw Error('Incomplete sweep');
for(let r of rows.filter(r=>r.found))if(!Number.isFinite(r.electric_kW)||r.electric_kW<=0||r.torque_error_fraction>.001)throw Error('Invalid trim');
function csv(file,rs){let keys=[...new Set(rs.flatMap(r=>Object.keys(r)))];fs.writeFileSync(path.join(__dirname,file),keys.join(',')+'\n'+rs.map(r=>keys.map(k=>r[k]??'').join(',')).join('\n')+'\n');}
csv('Rotorvergleich.csv',rows);csv('Motorkombinationen.csv',designs);
let inputs=['kreis_r04/mn1330_p14/parameter.json','kreis_r04/mn1330_p14/Ausgabe/Massenvarianten.json','kreis_r04/simulation/r04_physik.js','kreis_r04/mn1330_p14/p14_physik.js','studie_antrieb/simulieren.cjs'];
fs.writeFileSync(path.join(__dirname,'Ergebnisse.json'),JSON.stringify({scope:'Stationary hover BEMT, preliminary design study; no continuous motor certification',inputs:inputs.map(file=>({file,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(base,file))).digest('hex')})),rows,designs,checks},null,2));
}
module.exports={hover};
