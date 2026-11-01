/* Deterministic finite search over all eleven design parameters, not a global optimum. */
(function(root){'use strict';
const node=typeof module!=='undefined'&&module.exports,D=node?require('./design.js'):root.H01Design,S=node?require('./parameterstudie.js'):root.H01Study;
const keys=Object.keys(D.defaults).filter(k=>k!=='rpm'),primes=[2,3,5,7,11,13,17,19,23,29];
function halton(n,b){let f=1,v=0;while(n){f/=b;v+=f*(n%b);n=Math.floor(n/b);}return v;}
function sample(n,center=null,scale=.12){const d={};keys.forEach((k,j)=>{const [lo,hi]=D.ranges[k],u=halton(n,primes[j]);d[k]=center?Math.max(lo,Math.min(hi,center[k]+(2*u-1)*(hi-lo)*scale)):lo+u*(hi-lo);if(k==='blades')d[k]=Math.round(d[k]);});
 if(!center){const lo=-2-Math.min(0,d.twistDeg),hi=21-Math.max(0,d.twistDeg);d.pitchUpperDeg=lo+halton(n,23)*(hi-lo);d.pitchLowerDeg=lo+halton(n,29)*(hi-lo);}
 try{return D.validate({...d,rpm:3000});}catch{return null;}}
function noBladeOverlap(d){return d.chordMm<=2*d.rootRadiusMm*Math.sin(Math.PI/d.blades)&&d.chordMm*d.taper<=d.diameterMm*Math.sin(Math.PI/d.blades);}
// Conservative common disk area for equal-diameter coaxial rotors, including hub.
// Reject model artifacts below even the ideal actuator-disc induced-power bound.
function idealPower(r){const area=Math.PI*(r.design.diameterMm/2000)**2;return Math.max(0,r.thrustN)**1.5/Math.sqrt(2*1.225*area);}
function aeroOK(r){return r.converged&&r.hoverError>=.05-1e-6&&r.hoverError<=.08&&r.yawError<=.1&&r.stalledFraction<=.1&&r.tipMach<.65&&r.thrustPerRotorN.every(v=>v>0)&&r.torqueNm.every(v=>v>0)&&r.mechanicalPowerW>=idealPower(r);}
const byMechanical=(a,b)=>a.mechanicalPowerW-b.mechanicalPowerW,byElectric=(a,b)=>a.powerW-b.powerW;
async function run(base,options={}){
 const samples=options.samples??4096,refinements=options.refinements??1024,currentLimit=options.currentLimit??20;
 if(!Number.isInteger(samples)||samples<1||samples>20000||!Number.isInteger(refinements)||refinements<0||refinements>10000)throw Error('Suchumfang ungültig');
 if(!(currentLimit>0&&currentLimit<=46))throw Error('EMAX-Stromgrenze muss >0 und ≤46 A sein');
 const wanted=base.mass*9.81*1.055,stats={attempted:0,invalidGeometry:0,evaluations:0,aeroAccepted:0,electricalAccepted:0},pool=[],seen=new Set(),failures={convergence:0,thrust:0,yaw:0,stall:0,tipMach:0,positiveLoads:0,energyBound:0,motor:0};let stopped=false;
 const evaluate=d=>{stats.evaluations++;return S.evaluate(base,d,{collectSections:false,currentLimit});};
 function consider(d){stats.attempted++;if(!d||!noBladeOverlap(d)){stats.invalidGeometry++;return;}
  const id=JSON.stringify(d);if(seen.has(id))return;seen.add(id);
  let r=evaluate(d);
  // RPM is optimized against a common thrust target, then checked with the full model.
  for(let j=0;j<5;j++){if(!r.converged||r.thrustN<=0)break;const rpm=Math.max(500,Math.min(6000,r.design.rpm*Math.sqrt(wanted/r.thrustN)));if(Math.abs(rpm-r.design.rpm)<.01)break;r=evaluate({...d,rpm});if(Math.abs(r.thrustN/wanted-1)<.002)break;}
  r.idealInducedPowerW=idealPower(r);const valid=aeroOK(r);if(!r.converged)failures.convergence++;if(r.hoverError<.05-1e-6||r.hoverError>.08)failures.thrust++;if(r.yawError>.1)failures.yaw++;if(r.stalledFraction>.1)failures.stall++;if(r.tipMach>=.65)failures.tipMach++;if(!r.thrustPerRotorN.every(v=>v>0)||!r.torqueNm.every(v=>v>0))failures.positiveLoads++;if(r.mechanicalPowerW<r.idealInducedPowerW)failures.energyBound++;
  if(!valid)return;stats.aeroAccepted++;r.electricallyAccepted=r.withinMotorEnvelope&&r.motorCurrentA.every(v=>v<=currentLimit);if(r.electricallyAccepted)stats.electricalAccepted++;else failures.motor++;
  pool.push(r);
 }
 const progress=async(i,total,phase)=>{if(options.cancelled?.()){stopped=true;return false;}if(i%8===0||i===total){options.progress?.({phase,done:i,total,...stats});if(options.yield)await options.yield();}return true;};
 for(let i=1;i<=samples;i++){consider(sample(i));if(!await progress(i,samples,'global'))break;}
 const seeds=[...pool].sort(byMechanical).slice(0,32);
 if(!stopped&&seeds.length)for(let i=1;i<=refinements;i++){const seed=seeds[(i-1)%seeds.length];consider(sample(i+samples,seed.design,i<=refinements/2?.1:.035));if(!await progress(i,refinements,'refine'))break;}
 // Check leading designs on two finer quadratures before publishing any winner.
 const finalists=[...new Set([...pool].sort(byMechanical).slice(0,100).concat([...pool].filter(r=>r.electricallyAccepted).sort(byElectric).slice(0,100)))],verified=[];
 stats.verifiedAccepted=0;stats.verificationEvaluations=0;stats.electricalScreened=stats.electricalAccepted;
 if(!stopped)for(let i=0;i<finalists.length;i++){
  const r=finalists[i];r.verification=[];
  for(const [radial,azimuths] of [[20,32],[40,64]]){const q=S.evaluate({...base,c:{...base.c,radial,azimuths}},r.design,{collectSections:false,currentLimit});stats.evaluations++;stats.verificationEvaluations++;r.verification.push({radial,azimuths,mechanicalPowerW:q.mechanicalPowerW,thrustN:q.thrustN,hoverError:q.hoverError,stalledFraction:q.stalledFraction,yawError:q.yawError,idealInducedPowerW:idealPower(q),aeroAccepted:aeroOK(q),electricallyAccepted:q.withinMotorEnvelope&&q.motorCurrentA.every(v=>v<=currentLimit)});if(!aeroOK(q))break;}
  if(r.verification.length===2&&r.verification.every(v=>v.aeroAccepted)){r.electricallyAccepted=r.electricallyAccepted&&r.verification.every(v=>v.electricallyAccepted);verified.push(r);stats.verifiedAccepted++;}
  if(!await progress(i+1,finalists.length,'verify'))break;
 }
 stats.electricalAccepted=verified.filter(r=>r.electricallyAccepted).length;
 const top=(rows,compare)=>[...rows].sort(compare).slice(0,10);
 return {status:stopped?'PARTIAL_CANCELLED':'COMPLETE_FINITE_SEARCH',method:'Halton over ten geometry/pitch parameters; full-model RPM trim to 5.5% thrust reserve; local refinement of 32 mechanical-power leaders. Screening 10x16 quadrature, finalists must pass 20x32 and 40x64. Ranking uses screening power.',native_sha256:(node?require('./flugphysik.js').P11:root.H01Flight.P11).source_native_sha256,massKg:base.mass,ranges:D.ranges,parameters:[...keys,'rpm'],settings:{samples,refinements,currentLimit,minReserve:.05,maxReserve:.08,maxYawError:.1,maxStalledFraction:.1,maxTipMach:.65,minMechanicalToIdealPower:1},stats,failures,top10Electrical:top(verified.filter(r=>r.electricallyAccepted),byElectric),top10Aerodynamic:top(verified,byMechanical),limitations:['Finite sampled search, not all continuous combinations or a proven global optimum','Unchanged P11 mass/inertia for all geometries; no structural or CAD clearance validation','Simplified polar and coaxial inflow; no measured real-world efficiency','Electrical EMAX extrapolations outside limits are not operating points; future motor efficiency unknown','20 A default screening limit is an assumption, not verified continuous thermal rating; 46 A is model peak cap','Conservative planar blade-overlap screen; full 3D kinematics not checked','Reject mechanical power below T^1.5 / sqrt(2 rho pi R^2), rho=1.225 kg/m3, common coaxial disk area including hub; necessary plausibility test only']};
}
const api={run,sample,noBladeOverlap,aeroOK,idealPower};if(node)module.exports=api;else root.H01Search=api;
})(globalThis);
