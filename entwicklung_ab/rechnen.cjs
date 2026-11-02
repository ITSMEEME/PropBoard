// Recompute hover from the CAD-derived mass register; no nominal power is invented.
const fs=require('fs'),path=require('path');
const H=__dirname,ROOT=path.resolve(H,'..'),A=require(ROOT+'/kreis_r04/simulation/r04_physik.js'),P=require(ROOT+'/kreis_r04/mn1330_p14/p14_physik.js'),{hover}=require(ROOT+'/studie_antrieb/simulieren.cjs');
const cfg=require('./parameter.json'),motor=require(ROOT+'/kreis_r04/mn1330_p14/Motor_Daten.json');
function single(c,mass,elements=32){
 let n=c.motors,rpm=5000,s;
 for(let i=0;i<12;i++){
  s=A.simulate({blades:c.blades,rIn:.09,rOut:c.radius_mm/1000,chord:c.chord_mm/1000,thickness:.12,twist:0,pitchUpper:14,pitchLower:14,rpm,elements}).upper;
  if(!(s.T>0))return null;let ratio=mass*9.81/(n*s.T);if(Math.abs(ratio-1)<.00001)break;rpm*=Math.sqrt(ratio);
 }
 return {rpm,thrust_N:s.T*n,shaft_kW:s.P*n/1000,electric_kW:s.P*n/.82/1000,per_motor_shaft_kW:s.P/1000,torque_Nm:s.Q,tip_Mach:rpm*2*Math.PI/60*c.radius_mm/1000/340,stall_fraction:s.stalledFraction,thrust_error_fraction:s.T*n/(mass*9.81)-1,pitch_upper_deg:14,pitch_lower_deg:null};
}
function study(case_,mass,elements=32){
 if(case_.type!=='coax')return single(case_,mass,elements);
 let c=JSON.parse(fs.readFileSync(path.join(H,'configs',case_.id+'.json')));
 return hover(c,mass,14,elements);
}
let rows=[],sens=[],closure=[],failure=[],demand=[],loadpoints=[];
for(let item of cfg.cases){
 let file=path.join(H,'Ausgabe',item.id,'Pruefung.json'),cad=JSON.parse(fs.readFileSync(file));let c=cad.case,mass=cad.total_mass_with_payload_kg,n=c.type==='coax'?2:c.motors;
 let s=study(c,mass),fine=study(c,mass,64);if(!s||!fine)throw Error('No hover solution '+c.id);
 let q={id:c.id,type:c.type,motors:n,blades:c.blades,radius_mm:c.radius_mm,mass_kg:mass,...s,minimum_shaft_rating_30pct_kW:s.per_motor_shaft_kW*1.3,minimum_shaft_rating_30pct_thrust_kW:s.per_motor_shaft_kW*1.3**1.5,electric_per_motor_kW:s.electric_kW/n,continuous_pack_current_at_92V_A:s.electric_kW*1000/92,per_motor_input_current_at_92V_A:s.electric_kW*1000/92/n,input_per_motor_plus30pct_kW:s.electric_kW/n*1.3,required_KV_lower_bound_at_92V:s.rpm/92,usable_battery_kWh:12*.220*.8,hover_minutes_energy_only:12*.220*.8/s.electric_kW*60,capacity_at_92V_Ah:12*.220*1000/92,c_rate_at_92V:s.electric_kW/(12*.220),rotor_hull_fits:cad.envelope_pass,rotor_clearance_screen_pass:cad.rotor_envelope_intersections.length===0&&cad.new_vs_inherited_static_intersections.length===0,aerodynamic_screen_pass:s.tip_Mach<=.65&&s.stall_fraction<=.1,numerical_power_difference_32_64_fraction:Math.abs(fine.electric_kW/s.electric_kW-1),motor_continuous_map_verified:false,esc_verified:false,battery_verified:false};
 rows.push(q);
 for(let factor of [1,1.19,1.3,1.5]){let lp=study(c,mass*factor);if(lp)loadpoints.push({id:c.id,thrust_weight_factor:factor,...lp,aerodynamic_screen_pass:lp.tip_Mach<=.65&&lp.stall_fraction<=.1,scope:'Stationary BEMT demand for increased thrust; no certified maneuver or motor limit'});}
 for(let extra of [0,5,10,20])for(let eta of [.75,.82,.9]){
  let z=study(c,mass+extra);sens.push({id:c.id,extra_mass_kg:extra,motor_eta_assumed:eta,electric_kW:z.shaft_kW/eta,required_shaft_kW_each_plus30pct:z.per_motor_shaft_kW*1.3,tip_Mach:z.tip_Mach});
 }
 for(let specific of [1,3,6])for(let kw of [10,15,20,25,30,40]){
  let revised=mass+n*(kw/specific-2.75),z=study(c,revised);
  if(z)closure.push({id:c.id,rated_shaft_kW_assumed:kw,specific_shaft_kWkg_assumed:specific,motor_mass_each_kg:kw/specific,revised_mass_kg:revised,electric_kW:z.electric_kW,required_shaft_kW_each_plus30pct:z.per_motor_shaft_kW*1.3,reserve30pct_covered:kw>=z.per_motor_shaft_kW*1.3});
 }
 // Static allocation, fixed rotor axes, equal CW/CCW split. Not a flight controller.
 const centres=cad.centres_mm;
 for(let fail=0;fail<n;fail++){
  let coords=c.type==='coax'?[[0,0],[0,0]]:centres;
  let signs=c.type==='coax'?[1,-1]:Array.from({length:n},(_,i)=>i%2?1:-1);
  failure.push({id:c.id,failed_motor_index:fail,remaining:n-1,allocation_model:'fixed-axis hover; thrust, roll, pitch and yaw; equal yaw torque/thrust ratio approximation',requires_solver:true,coords,signs,required_thrust_N:mass*9.81,assumed_healthy_max_thrust_N:mass*9.81/n*1.3**(2/3)});
 }
 // Demand-only beam screen; no fabricated material allowable.
 let beams=c.type==='coax'?[{name:'Unterer Lastarm',L:(c.radius_mm+45-140)/1000,outer:.05,wall:.003,force:mass*9.81*2/4},{name:'Oberer Deckträger',L:Math.hypot((c.radius_mm+45)/Math.sqrt(2)-280,(c.radius_mm+45)/Math.sqrt(2)-150)/1000,outer:.04,wall:.0025,force:(100+3.0)*9.81*2/4}]:[{name:'Rotorarm',L:Math.hypot(...centres[0])/1000-.135,outer:.04,wall:.0025,force:mass*9.81*2/n}];
 for(let b of beams){let I=(b.outer**4-(b.outer-2*b.wall)**4)/12;for(let E of [70e9,110e9])demand.push({id:c.id,member:b.name,load_factor:2,force_N:b.force,length_m:b.L,I_m4:I,E_assumed_Pa:E,root_moment_Nm:b.force*b.L,nominal_bending_stress_MPa:b.force*b.L*b.outer/2/I/1e6,cantilever_deflection_mm:b.force*b.L**3/(3*E*I)*1000,scope:'uniform isotropic cantilever; no joint, composite laminate, torsion, shear or buckling certification'});}
 console.log(c.id,s.electric_kW.toFixed(2)+' kW',s.rpm.toFixed(0)+'/min','geometry',q.rotor_clearance_screen_pass);
}
function csv(name,rs){let keys=[...new Set(rs.flatMap(r=>Object.keys(r)))];fs.writeFileSync(path.join(H,name),keys.join(',')+'\n'+rs.map(r=>keys.map(k=>{let v=r[k]??'';return typeof v==='string'?JSON.stringify(v):v;}).join(',')).join('\n')+'\n');}
csv('Leistungsbedarf.csv',rows);csv('Massen_Wirkungsgrad_Sensitivitaet.csv',sens);csv('Motor_Massenschluss.csv',closure);csv('Rahmen_Lastscreen.csv',demand);csv('Lastpunkte.csv',loadpoints);
fs.writeFileSync(path.join(H,'Leistungsbedarf.json'),JSON.stringify({rows,sens,closure,demand,motor_evidence:{recorded_torque_Nm:motor.maxima.recorded_torque_Nm,recorded_input_W:motor.maxima.recorded_input_power_W,power_180s_W:motor.basic.max_power_180s_W,continuous_verified:false}},null,2));
fs.writeFileSync(path.join(H,'Ausfall_Eingaben.json'),JSON.stringify(failure,null,2));
