#!/usr/bin/env node
'use strict';
const {run}=require('./testflug.js'),fs=require('fs'),path=require('path');let seed=4711;const rnd=()=>{seed=(1664525*seed+1013904223)>>>0;return seed/4294967296;};let results=[];
for(let i=0;i<12;i++){const options={seed:i+101,servoMassG:20+40*rnd(),servoStallNm:.6865+.7845*rnd(),servoFriction:.02+.13*rnd(),cyclicPhaseDeg:-25+50*rnd(),servoDelay:.006+.019*rnd(),servoSpeedRadS:6+4*rnd(),thrustScale:.85+.3*rnd(),initialSoc:.3+.6*rnd()};let c={name:'Kombinierte_Annahmen_'+String(i+1).padStart(2,'0'),duration:18,options,initial:{p:[.15,-.1,1.15],angles:[5,-4,5]},gust:true};let r=run(c);results.push(r.summary);console.log(c.name,r.summary.status,r.summary.position_rms_last5s_m?.toFixed(3));}
fs.writeFileSync(path.join(__dirname,'Ergebnisse/Robustheit.json'),JSON.stringify({status:'DETERMINISTIC_ASSUMPTION_SWEEP_NOT_RELIABILITY_STATISTICS',sampling_seed:4711,results},null,2));
