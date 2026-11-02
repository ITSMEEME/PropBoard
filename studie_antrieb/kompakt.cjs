// Redesigned, separate compact rotors. Geometry/mass are assumed, not P14 CAD.
const fs=require('fs'),path=require('path'),B=path.resolve(__dirname,'..'),A=require(B+'/kreis_r04/simulation/r04_physik.js');
let rows=[];
function layout(n,D){let best;for(let cols=1;cols<=n;cols++){let lines=Math.ceil(n/cols),x=cols*D+(cols-1)*.08,y=lines*D+(lines-1)*.08;let r={x,y,cols,lines,ratio:Math.max(x/2.1,y/1.7)};if(!best||r.ratio<best.ratio)best=r;}return best;}
function ring(n,D){let best,rc=(D+.08)/(2*Math.sin(Math.PI/n));for(let deg=0;deg<=90;deg+=.25){let a=Array.from({length:n},(_,i)=>(2*Math.PI*i/n+deg*Math.PI/180)),xs=a.map(t=>rc*Math.cos(t)),ys=a.map(t=>rc*Math.sin(t)),x=Math.max(...xs)-Math.min(...xs)+D,y=Math.max(...ys)-Math.min(...ys)+D,ratio=Math.max(x/2.1,y/1.7);if(!best||ratio<best.ratio)best={x,y,ratio,orientation_deg:deg};}return best;}
for(let motors=1;motors<=10;motors++)for(let blades of [2,3,4,6,8,10,12])for(let R of [.15,.2,.225,.25,.275,.3,.325,.35,.375,.4,.45,.55,.65,.71,.8]){
 let chord=Math.max(.06,.12*Math.sqrt(R/.71)),root=Math.max(.09,1.05*blades*chord/(2*Math.PI));
 let moduleMass=2.75+(45.13/2-2.75)*(R/.71)**2*(.65+.35*blades/4),totalMass=114+motors*moduleMass;
 let l=layout(motors,2*R),best;
 if(R-root>=.10)for(let pitch of [10,12,14]){
 let rpm=2500,s;
 for(let i=0;i<8;i++){s=A.simulate({blades,rIn:root,rOut:R,chord,thickness:.12,twist:0,pitchUpper:pitch,pitchLower:pitch,rpm,elements:24}).upper;let ratio=totalMass*9.81/(motors*s.T);if(!(ratio>0))break;if(Math.abs(ratio-1)<.0001)break;rpm*=Math.sqrt(ratio);}
 let err=s?.T*motors/(totalMass*9.81)-1,mach=rpm*2*Math.PI/60*R/340;
 if(!Number.isFinite(s?.P)||!(s.P>0)||s.stalledFraction>.1||mach>.65||Math.abs(err)>.005)continue;
 let r={rpm,pitch_deg:pitch,electric_kW:s.P*motors/.82/1000,per_motor_shaft_kW:s.P/1000,torque_Nm:s.Q,thrust_N:s.T*motors,tip_Mach:mach,stall_fraction:s.stalledFraction,thrust_error_fraction:err};if(!best||r.electric_kW<best.electric_kW)best=r;
 }
 let row={architecture:'compact_redesign_single_rotors',motors,blades,radius_mm:R*1000,free_blade_length_mm:(R-root)*1000,blade_root_radius_mm:root*1000,chord_mm:chord*1000,mass_kg:totalMass,module_mass_proxy_kg:moduleMass,envelope_x_m:l.x,envelope_y_m:l.y,rotor_envelope_fits:l.ratio<=1+1e-9,odd_motor_count:motors%2===1,yaw_trim_demonstrated:false,found:!!best};
 if(best)Object.assign(row,best,{minimum_motor_shaft_kW_30pct:1.3*best.per_motor_shaft_kW,hover_min_12kg_220Whkg:12*.220*.8/best.electric_kW*60});row.layout='rectangular_grid';rows.push(row);
 if(motors>=3){let r=ring(motors,2*R);rows.push({...row,layout:'classic_ring',envelope_x_m:r.x,envelope_y_m:r.y,rotor_envelope_fits:r.ratio<=1+1e-9});}
}
let keys=[...new Set(rows.flatMap(r=>Object.keys(r)))];fs.writeFileSync(path.join(__dirname,'Kompakte_Anordnungen.csv'),keys.join(',')+'\n'+rows.map(r=>keys.map(k=>r[k]??'').join(',')).join('\n')+'\n');fs.writeFileSync(path.join(__dirname,'Kompakt.json'),JSON.stringify({rows},null,2));console.log(rows.length,'compact configurations calculated');
