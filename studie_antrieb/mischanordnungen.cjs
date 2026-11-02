const fs=require('fs'),path=require('path'),B=path.resolve(__dirname,'..'),{hover}=require('./simulieren.cjs'),A=require(B+'/kreis_r04/simulation/r04_physik.js'),P=require(B+'/kreis_r04/mn1330_p14/p14_physik.js'),cfg=require(B+'/kreis_r04/mn1330_p14/parameter.json'),m=require(B+'/kreis_r04/mn1330_p14/Ausgabe/Massenvarianten.json');
let rows=[];
for(let motors=3;motors<=10;motors++)for(let pairs=1;pairs<Math.ceil(motors/2);pairs++)for(let radius of [710,800]){
let singles=motors-2*pairs;if(!singles)continue;let sites=pairs+singles,c=JSON.parse(JSON.stringify(cfg));c.geometry.rotor_radius_mm=radius;c.geometry.lift_units=1;
let d=P.derive(c),ref=P.derive(cfg),pairMass=m.cases[8].mass_kg+8.84*(d.blade_span_mm/ref.blade_span_mm-1),mass=114+motors*pairMass/2,best;
for(let pitch of [10,12,14]){let pair=hover(c,mass/sites,pitch);if(!pair)continue;let rpm=1800,s;
for(let i=0;i<8;i++){s=A.simulate({...P.aeroParams(c,rpm,pitch,pitch),elements:24}).upper;let ratio=mass*9.81/sites/s.T;if(!(ratio>0))break;if(Math.abs(ratio-1)<.0001)break;rpm*=Math.sqrt(ratio);}
if(!s||!Number.isFinite(s.P)||s.stalledFraction>.1||rpm*2*Math.PI/60*radius/1000/340>.65)continue;
let r={electric_kW:pair.electric_kW*pairs+s.P*singles/.82/1000,pair_rpm:pair.rpm,single_rpm:rpm,per_motor_shaft_kW:Math.max(pair.per_motor_shaft_kW,s.P/1000),torque_Nm:Math.max(pair.torque_Nm,s.Q),pitch_upper_deg:pitch};if(!best||r.electric_kW<best.electric_kW)best=r;}
rows.push({motors,pairs,singles,sites,blades:8,radius_mm:radius,mass_kg:mass,rotor_envelope_fits:false,found:!!best,...best});}
fs.writeFileSync(path.join(__dirname,'Mischanordnungen.json'),JSON.stringify({rows},null,2));console.log(rows.length,'mixed configurations calculated');
