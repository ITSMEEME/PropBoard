/* Offline UI: the exact same engine and scenarios run under Node in testflug.js. */
'use strict';
const $=id=>document.getElementById(id),F=H01Flight,S=H01Scenarios;
for(const [i,c]of S.cases.entries())$('case').add(new Option(c.name.replaceAll('_',' '),i));
function loadCase(){let o={...F.defaults,...S.cases[+$('case').value].options};$('mass').value=o.servoMassG;$('torque').value=o.servoStallNm;$('friction').value=o.servoFriction;$('phase').value=o.cyclicPhaseDeg;}
$('case').onchange=loadCase;$('case').value=String(S.cases.findIndex(c=>c.name==='Savox_7_4V_Manoever'));loadCase();
let sim,scenario,paused=true,rows=[],lastFrame=0,accumulator=0,trail=[],finished=false,rotorAngles=[0,0];
function start(){clearKeys();manualTarget=null;for(let id of ['mass','torque','friction','phase'])if(!$(id).reportValidity())return;scenario=S.cases[+$('case').value];sim=new F.Flight({...scenario.options,servoMassG:+$('mass').value,servoStallNm:+$('torque').value,servoFriction:+$('friction').value,cyclicPhaseDeg:+$('phase').value});if(scenario.initial){if(scenario.initial.p)sim.p=[...scenario.initial.p];if(scenario.initial.angles)sim.q=F.quat(...scenario.initial.angles.map(x=>x*F.D));}rows=[];trail=[];paused=false;finished=false;accumulator=0;rotorAngles=[0,0];$('pause').textContent='Pause';draw();}
// WASD moves a position setpoint at 0.6 m/s in the commanded heading.
const heldKeys=new Set();let manualTarget=null;
function clearKeys(){heldKeys.clear();}
function editable(el){return el?.matches?.('input,select,textarea')||el?.isContentEditable;}
window.addEventListener('keydown',e=>{if(!['KeyW','KeyA','KeyS','KeyD'].includes(e.code)||editable(e.target)||!$('manual').checked||paused||finished||sim?.crashed)return;e.preventDefault();heldKeys.add(e.code);});
window.addEventListener('keyup',e=>{heldKeys.delete(e.code);});
window.addEventListener('blur',clearKeys);
document.addEventListener('visibilitychange',()=>{if(document.hidden)clearKeys();});
$('manual').onchange=()=>{clearKeys();manualTarget=null;};
function flightInputs(advance=false){
 const inp=S.inputs(sim,scenario);
 if(!$('manual').checked)return inp;
 if(!manualTarget)manualTarget={position:[...sim.p],yaw:inp.target.yaw};
 if(advance){let forward=Number(heldKeys.has('KeyW'))-Number(heldKeys.has('KeyS')),right=Number(heldKeys.has('KeyD'))-Number(heldKeys.has('KeyA')),norm=Math.max(1,Math.hypot(forward,right)),c=Math.cos(manualTarget.yaw),s=Math.sin(manualTarget.yaw),step=.6*sim.c.dt/norm;manualTarget.position[0]+=step*(c*forward-s*right);manualTarget.position[1]+=step*(s*forward+c*right);}
 return {...inp,target:{position:[...manualTarget.position],yaw:manualTarget.yaw}};
}
$('start').onclick=start;$('pause').onclick=()=>{clearKeys();paused=!paused;$('pause').textContent=paused?'Fortsetzen':'Pause';};
$('export').onclick=()=>{let blob=new Blob([JSON.stringify({scenario:scenario.name,options:sim.c,controlMode:$('manual').checked?'WASD_POSITION':'SCENARIO',cad_sha256:F.CAD.source_sha256,rows},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='H01-Fluglog.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
function context(id){let el=$(id),dpr=window.devicePixelRatio||1,w=el.clientWidth,h=el.clientHeight;if(el.width!==Math.round(w*dpr)||el.height!==Math.round(h*dpr)){el.width=Math.round(w*dpr);el.height=Math.round(h*dpr);}let ctx=el.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);return{ctx,w,h};}
function draw(){if(!sim)return;let {ctx,w,h}=context('scene');let factor=Math.min(w,h)*1.05,center=[sim.p[0],sim.p[1],sim.p[2]-.10];
 function project(v){let a=v.map((x,i)=>x-center[i]);return[w/2+factor*(.78*a[0]+.62*a[1]),h*.62+factor*(.35*a[0]-.44*a[1]-.83*a[2]),.5*a[0]-.63*a[1]+.6*a[2]];}
 ctx.strokeStyle='#2d4054';for(let i=-3;i<=3;i++){for(let axis=0;axis<2;axis++){let a=project(axis?[i,-3,0]:[-3,i,0]),b=project(axis?[i,3,0]:[3,i,0]);ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.lineTo(b[0],b[1]);ctx.stroke();}}
 ctx.strokeStyle='#66bff0';ctx.beginPath();trail.forEach((p,i)=>{let a=project(p);i?ctx.lineTo(a[0],a[1]):ctx.moveTo(a[0],a[1]);});ctx.stroke();
 let tris=[];for(let part of (sim.c.servoGeometryProfile==='Savox_SB2271SG_USER'?[...H01_MESH.filter(p=>!H01_SERVO_MESH.some(s=>s.name===p.name)),...H01_SERVO_MESH]:H01_MESH)){let rot=part.group==='upper'?rotorAngles[0]:part.group==='lower'?-rotorAngles[1]:0,cr=Math.cos(rot),sr=Math.sin(rot);let points=part.vertices.map(v=>{let a=[cr*v[0]-sr*v[1],sr*v[0]+cr*v[1],v[2]];return project(F.rotate(sim.q,a.map((x,i)=>x-sim.cg[i])).map((x,i)=>x+sim.p[i]));});let color=part.group==='upper'?'#39b7c9':part.group==='lower'?'#d98d55':/Akku_Referenz/.test(part.name)?'#546994':'#a0adb9';for(let f of part.faces){let a=points[f[0]],b=points[f[1]],c=points[f[2]];tris.push({a,b,c,z:(a[2]+b[2]+c[2])/3,color});}}
 tris.sort((a,b)=>a.z-b.z);for(let t of tris){ctx.fillStyle=t.color;ctx.beginPath();ctx.moveTo(t.a[0],t.a[1]);ctx.lineTo(t.b[0],t.b[1]);ctx.lineTo(t.c[0],t.c[1]);ctx.closePath();ctx.fill();}
 ctx.fillStyle='#c9deef';ctx.font='13px system-ui';ctx.fillText('CAD H01 · Ø 375 mm · '+(paused?'pausiert':'Flugversuch'),14,22);
 let r=sim.snapshot(flightInputs().target);$('readout').textContent=`${sim.crashed?'ABBRUCH: Bodennähe / große Neigung':finished?'Testzeit beendet':paused?'PAUSE':'SIMULATION LÄUFT'}\nZeit ${r.t.toFixed(2)} s · Masse ${sim.mass.toFixed(3)} kg\nPosition ${r.p.map(x=>x.toFixed(2)).join(' / ')} m\nSoll     ${r.target.map(x=>x.toFixed(2)).join(' / ')} m\nRoll/Nick/Gier ${r.euler.map(x=>x.toFixed(1)).join(' / ')} °\nRotoren ${r.rpm.map(x=>x.toFixed(0)).join(' / ')} U/min\nServotyp ${sim.c.servoGeometryProfile==='Savox_SB2271SG_USER'?'Savöx laut Nutzerangabe':'generische Annahme'} · ${sim.c.servoSupplyV??'–'} V\nAkku ${r.bus.toFixed(2)} V · ${r.current.toFixed(1)} A\nServos ${r.servoDeg.map(x=>x.toFixed(1)).join(' / ')} °\nMax. geschätzte Servolast ${Math.max(...r.servoLoadNm).toFixed(3)} Nm\nKinematiküberschreitungen ${sim.envelopeViolations}\nProfilquelle ${sim.c.polarSource} · Ersatzmodell ${(100*r.polarFallbackFraction).toFixed(1)} %`;
 let p=context('plot'),data=rows.slice(-500),maxTime=Math.max(5,data.at(-1)?.t||5),minTime=Math.max(0,maxTime-25);for(let [color,get,range]of [['#61c9ff',x=>x.p[2],3],['#f5d779',x=>x.target[2],3],['#75d5a8',x=>x.euler[0]/10+1,3],['#e997bc',x=>x.euler[1]/10+1,3]]){p.ctx.strokeStyle=color;p.ctx.beginPath();data.forEach((r,i)=>{let x=(r.t-minTime)/(maxTime-minTime)*p.w,y=p.h-15-get(r)/range*(p.h-25);i?p.ctx.lineTo(x,y):p.ctx.moveTo(x,y);});p.ctx.stroke();}
}
function frame(ts){let elapsed=Math.min(.05,(ts-lastFrame)/1000||0);lastFrame=ts;if(sim&&!paused&&!sim.crashed&&!finished){accumulator+=elapsed;let steps=0;while(accumulator>=sim.c.dt&&steps<20){let inp=flightInputs(true);sim.step(inp.target,inp.external);for(let l=0;l<2;l++)rotorAngles[l]=(rotorAngles[l]+sim.omega[l]*sim.c.dt)%(2*Math.PI);accumulator-=sim.c.dt;steps++;if(Math.round(sim.t/sim.c.dt)%20===0){rows.push(sim.snapshot(inp.target));trail.push([...sim.p]);if(trail.length>500)trail.shift();}if(sim.crashed||sim.t>=scenario.duration){finished=true;break;}}}if(ts-(frame.lastDraw||0)>100){draw();frame.lastDraw=ts;}requestAnimationFrame(frame);}
$('results').innerHTML='<table><thead><tr><th>Fall</th><th>Modellergebnis</th><th>RMS letzte 5 s</th><th>Max. Neigung</th></tr></thead><tbody>'+H01_TESTS.results.map(r=>`<tr><td>${r.name.replaceAll('_',' ')}</td><td class="${r.status==='STABIL_IM_MODELL'?'good':'bad'}">${r.status.replaceAll('_',' ')}</td><td>${r.position_rms_last5s_m===null?'–':r.position_rms_last5s_m.toFixed(3)+' m'}</td><td>${r.max_tilt_deg.toFixed(1)}°</td></tr>`).join('')+'</tbody></table>';
start();paused=true;$('pause').textContent='Fortsetzen';requestAnimationFrame(frame);
