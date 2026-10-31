/* Offline-Bedienung des H01/P10-Simulators. Physik, Szenarien und Flugablauf sind dieselben
 * Module wie in der Node-Testserie (testflug.js). */
'use strict';
const $=id=>document.getElementById(id),F=H01Flight,S=H01Scenarios,FS=H01Flugsteuerung,ST=H01Stroemung,KIN=H01KinematikP10,V3=H01Ansicht3D;
const D=Math.PI/180,clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const SAVOX=S.cases.find(c=>c.name==='Savox_7_4V_Manoever').options;
const FREE={...SAVOX,massModel:'P10',drive:'P10_HOHLRAD',ground:true,startOnGround:true};
for(const [i,c] of S.cases.entries())$('case').add(new Option(c.name.replaceAll('_',' '),i));
function loadCase(){const o={...F.defaults,...S.cases[+$('case').value].options};$('mass').value=o.servoMassG;$('torque').value=o.servoStallNm;$('friction').value=o.servoFriction;$('phase_dev').value=o.cyclicPhaseDeg;}
$('case').onchange=loadCase;$('case').value=String(S.cases.findIndex(c=>c.name==='P10_Bodenstart_Schweben_Landung'));loadCase();

let sim,manager,scenario=null,paused=false,rows=[],trail=[],finished=false,rotorAngles=[0,0],accumulator=0,lastFrame=0,gust=[0,0,0],sliceData=null,sliceClock=0;
let particles=new ST.ParticleField(2200,11),view=null,glError=null;
try{view=new V3.View($('scene'),H01_P10_MESH,KIN);}catch(e){glError=e.message;$('glerror').style.display='grid';$('glerror').textContent='WebGL-Ansicht nicht verfügbar ('+e.message+'). Physik, Bedienung und Messdaten laufen weiter.';}
function resetCommon(){rows=[];trail=[];finished=false;rotorAngles=[0,0];accumulator=0;gust=[0,0,0];particles=new ST.ParticleField(2200,11);clearKeys();paused=false;$('pause').textContent='Pause';}
function newFree(){scenario=null;sim=new F.Flight({...FREE});manager=new FS.Manager(sim,{mode:$('angleMode').checked?'ANGLE':'POSITION'});resetCommon();}
function startCase(){for(const id of ['mass','torque','friction','phase_dev'])if(!$(id).reportValidity())return;scenario=S.cases[+$('case').value];
 sim=new F.Flight({...scenario.options,servoMassG:+$('mass').value,servoStallNm:+$('torque').value,servoFriction:+$('friction').value,cyclicPhaseDeg:+$('phase_dev').value});
 if(scenario.initial){if(scenario.initial.p)sim.p=[...scenario.initial.p];if(scenario.initial.angles)sim.q=F.quat(...scenario.initial.angles.map(x=>x*D));}manager=null;resetCommon();}

// ------------------------------------------------------------------ Eingaben: Tastatur, Gamepad, virtuelle Knüppel
const held=new Set();const editable=el=>el?.matches?.('input,select,textarea')||el?.isContentEditable;
function clearKeys(){held.clear();}
const STICK_KEYS={KeyW:1,KeyS:1,KeyA:1,KeyD:1,KeyQ:1,KeyE:1,KeyR:1,KeyF:1,ArrowUp:1,ArrowDown:1,ArrowLeft:1,ArrowRight:1,PageUp:1,PageDown:1};
window.addEventListener('keydown',e=>{if(editable(e.target))return;if(STICK_KEYS[e.code]){if(paused||!manager)return;e.preventDefault();held.add(e.code);return;}
 if(e.code==='KeyT'){e.preventDefault();doTakeoff();}else if(e.code==='KeyL'){e.preventDefault();manager?.land();}else if(e.code==='KeyM'){e.preventDefault();$('angleMode').checked=!$('angleMode').checked;setMode();}else if(e.code==='Space'){e.preventDefault();togglePause();}});
window.addEventListener('keyup',e=>held.delete(e.code));window.addEventListener('blur',clearKeys);document.addEventListener('visibilitychange',()=>{if(document.hidden)clearKeys();});
const keyStick={throttle:0,yaw:0,pitch:0,roll:0},pad={throttle:0,yaw:0,pitch:0,roll:0},game={throttle:0,yaw:0,pitch:0,roll:0,connected:false,id:''};
function keyboardSticks(dt){const k=c=>held.has(c)?1:0,tgt={pitch:k('KeyW')+k('ArrowUp')-k('KeyS')-k('ArrowDown'),roll:k('KeyD')+k('ArrowRight')-k('KeyA')-k('ArrowLeft'),yaw:k('KeyE')-k('KeyQ'),throttle:k('KeyR')+k('PageUp')-k('KeyF')-k('PageDown')};
 for(const a in keyStick)keyStick[a]+=(clamp(tgt[a],-1,1)-keyStick[a])*Math.min(1,dt/.12);}
let padPrev=[];function pollGamepad(){const gp=[...(navigator.getGamepads?.()||[])].find(g=>g&&g.connected);if(!gp){game.connected=false;for(const a of ['throttle','yaw','pitch','roll'])game[a]=0;return;}
 const dz=v=>Math.abs(v)<.08?0:v;game.connected=true;game.id=gp.id;game.yaw=dz(gp.axes[0]||0);game.throttle=-dz(gp.axes[1]||0);game.roll=dz(gp.axes[2]||0);game.pitch=-dz(gp.axes[3]||0);
 const pressed=gp.buttons.map(b=>b.pressed);if(pressed[0]&&!padPrev[0])doTakeoff();if(pressed[1]&&!padPrev[1])manager?.land();if(pressed[3]&&!padPrev[3]){$('angleMode').checked=!$('angleMode').checked;setMode();}padPrev=pressed;}
function sticks(){const out={};for(const a of ['throttle','yaw','pitch','roll'])out[a]=clamp(keyStick[a]+pad[a]+game[a],-1,1);return out;}
// Virtuelle Knüppel und Kamera auf dem HUD-Canvas
const hud=$('hud');let drag=null;
function padRects(){const w=hud.clientWidth,h=hud.clientHeight,s=Math.min(120,Math.max(84,w*.13));return[{x:16,y:h-s-16,s,axes:['yaw','throttle']},{x:w-s-16,y:h-s-16,s,axes:['roll','pitch']}];}
hud.addEventListener('pointerdown',e=>{const r=hud.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;hud.setPointerCapture(e.pointerId);
 const p=padRects().find(q=>x>=q.x&&x<=q.x+q.s&&y>=q.y&&y<=q.y+q.s);drag=p?{pad:p,id:e.pointerId}:{cam:true,x:e.clientX,y:e.clientY,id:e.pointerId};if(p)movePad(p,x,y);});
function movePad(p,x,y){pad[p.axes[0]]=clamp((x-p.x)/p.s*2-1,-1,1);pad[p.axes[1]]=clamp(1-(y-p.y)/p.s*2,-1,1);}
hud.addEventListener('pointermove',e=>{if(!drag||drag.id!==e.pointerId)return;const r=hud.getBoundingClientRect();if(drag.pad)movePad(drag.pad,e.clientX-r.left,e.clientY-r.top);
 else if(view){view.cam.yaw-=(e.clientX-drag.x)*.006;view.cam.elev=clamp(view.cam.elev+(e.clientY-drag.y)*.006,-.2,1.5);drag.x=e.clientX;drag.y=e.clientY;}});
function endDrag(e){if(drag&&drag.pad)for(const a of drag.pad.axes)pad[a]=0;drag=null;}
hud.addEventListener('pointerup',endDrag);hud.addEventListener('pointercancel',endDrag);
hud.addEventListener('wheel',e=>{if(!view)return;e.preventDefault();view.cam.dist=clamp(view.cam.dist*Math.exp(e.deltaY*.001),.15,6);},{passive:false});
for(const b of document.querySelectorAll('[data-cam]'))b.onclick=()=>{if(!view)return;view.cam.mode=b.dataset.cam;if(b.dataset.cam==='orbit'&&view.cam.dist<.6)view.cam.dist=1.2;for(const o of document.querySelectorAll('[data-cam]'))o.setAttribute('aria-pressed',String(o===b));};

// ------------------------------------------------------------------ Knöpfe
function doTakeoff(){if(scenario||!manager||sim.crashed){newFree();}manager.start();if(paused)togglePause();}
function setMode(){if(manager)manager.setMode($('angleMode').checked?'ANGLE':'POSITION');$('modeLabel').innerHTML='<small>'+($('angleMode').checked?'ANGLE-Modus: Knüppel = Lagewinkel, Steigrate, Gierrate':'Positionsmodus: Knüppel verschieben den Haltepunkt')+'</small>';}
function togglePause(){clearKeys();paused=!paused;$('pause').textContent=paused?'Fortsetzen':'Pause';}
$('takeoff').onclick=doTakeoff;$('land').onclick=()=>manager?.land();$('kill').onclick=()=>manager?.stop();$('reset').onclick=()=>{newFree();};$('pause').onclick=togglePause;$('angleMode').onchange=setMode;$('start').onclick=startCase;
$('export').onclick=()=>{const blob=new Blob([JSON.stringify({scenario:scenario?.name||'P10_Freiflug',options:sim.c,mode:manager?manager.mode:'SCENARIO',events:manager?.events||sim._manager?.events||[],cad_sha256:F.CAD.source_sha256,p10_sha256:F.P10?.source_native_sha256||null,rows},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='H01-P10-Fluglog.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
for(const id of ['wind','windDir','gust'])$(id).oninput=()=>{$('windLabel').textContent=`Wind ${(+$('wind').value).toFixed(1).replace('.',',')} m/s aus Richtung ${$('windDir').value}° (wehend nach ${((+$('windDir').value+180)%360)}°), Böigkeit ${Math.round(100*$('gust').value)} %`;};
function updateHidden(){if(!view)return;const g=[];if($('hideCovers').checked)g.push('cover');if($('hideCases').checked)g.push('servo_case');if(!$('showCables').checked)g.push('cable');view.setHidden(g);}
for(const id of ['hideCovers','hideCases','showCables'])$(id).onchange=updateHidden;

// ------------------------------------------------------------------ Simulation
function windVector(dt){const w=+$('wind').value,dir=(+$('windDir').value+180)*D,g=+$('gust').value;for(let i=0;i<3;i++)gust[i]+=(-gust[i]*dt/.8)+Math.sqrt(2*dt/.8)*(Math.random()*2-1)*1.7*g*Math.max(.5,w)*(i===2?.4:1);
 return[w*Math.cos(dir)+gust[0],w*Math.sin(dir)+gust[1],gust[2]];}
function physicsInputs(){if(manager)return manager.update(sticks(),sim.c.dt);return S.inputs(sim,scenario);}
function advance(simSeconds){let steps=0,adv=0;accumulator+=simSeconds;
 while(accumulator>=sim.c.dt&&steps<40){keyboardSticks(sim.c.dt);if(manager&&!scenario)sim.c.wind=windVector(sim.c.dt);const inp=physicsInputs();sim.step(inp.target,inp.external);steps++;adv+=sim.c.dt;
  for(let l=0;l<2;l++)rotorAngles[l]=(rotorAngles[l]+sim.omega[l]*sim.c.dt/D)%360;accumulator-=sim.c.dt;
  if(Math.round(sim.t/sim.c.dt)%20===0){rows.push(sim.snapshot(inp.target));if(rows.length>20000)rows.shift();trail.push([...sim.p]);if(trail.length>600)trail.shift();}
  if(sim.crashed||(scenario&&sim.t>=scenario.duration)){finished=true;break;}}
 if(steps>=40)accumulator=0;return adv;}
function vehicleState(){const s=sim,a=s.lastAero;return{p:s.p,q:s.q,cg:s.cg,v:s.v,wind:s.c.wind,vi:s.vi,Q:a?a.Q:[0,0],sense:[1,-1],groundZ:0};}

// ------------------------------------------------------------------ HUD und Anzeigen
function hudDraw(snap){const dpr=Math.min(2,devicePixelRatio||1),w=hud.clientWidth,h=hud.clientHeight;if(hud.width!==Math.round(w*dpr)||hud.height!==Math.round(h*dpr)){hud.width=Math.round(w*dpr);hud.height=Math.round(h*dpr);}
 const c=hud.getContext('2d');c.setTransform(dpr,0,0,dpr,0,0);c.clearRect(0,0,w,h);c.font='12px ui-monospace,monospace';c.textBaseline='top';
 const box=(x,y,bw,bh)=>{c.fillStyle='rgba(8,14,22,.62)';c.fillRect(x,y,bw,bh);c.strokeStyle='rgba(120,160,190,.35)';c.strokeRect(x+.5,y+.5,bw-1,bh-1);};
 const phase=manager?manager.phase:(finished?'TESTENDE':'TESTFALL');box(10,10,220,98);c.fillStyle='#e4edf5';
 const agl=sim.c.ground?Math.max(0,sim.p[2]-sim.groundClearanceHeight()):sim.p[2];
 [`${phase}${paused?' · PAUSE':''}`,`t ${snap.t.toFixed(2)} s · ${manager?manager.mode:'Szenario'}`,`Höhe über Kufe ${agl.toFixed(2)} m`,`v ${Math.hypot(...sim.v).toFixed(2)} m/s · Gier ${snap.euler[2].toFixed(0)}°`,`Rotor ${snap.rpm.map(x=>x.toFixed(0)).join(' / ')} U/min`,`Akku ${snap.bus.toFixed(1)} V · ${snap.current.toFixed(1)} A`].forEach((t,i)=>c.fillText(t,18,16+i*14));
 // Lageanzeige
 const cx=w/2,cy=h-72,r=48,roll=snap.euler[0]*D,pit=snap.euler[1];c.save();c.beginPath();c.arc(cx,cy,r,0,2*Math.PI);c.clip();c.translate(cx,cy);c.rotate(-roll);const off=clamp(pit*2.2,-r,r);c.fillStyle='#2b5f8a';c.fillRect(-2*r,-2*r+off,4*r,2*r);c.fillStyle='#6a4a2b';c.fillRect(-2*r,off,4*r,2*r);c.strokeStyle='#fff';c.beginPath();c.moveTo(-r,off);c.lineTo(r,off);c.stroke();c.restore();
 c.strokeStyle='#f1cc80';c.lineWidth=2;c.beginPath();c.moveTo(cx-26,cy);c.lineTo(cx-8,cy);c.moveTo(cx+8,cy);c.lineTo(cx+26,cy);c.stroke();c.lineWidth=1;c.strokeStyle='rgba(200,220,240,.6)';c.beginPath();c.arc(cx,cy,r,0,2*Math.PI);c.stroke();
 c.fillStyle='#c9deef';c.fillText(`R ${snap.euler[0].toFixed(1)}°  N ${snap.euler[1].toFixed(1)}°`,cx-48,cy+r+4);
 // Knüppel
 const st=sticks();for(const p of padRects()){box(p.x,p.y,p.s,p.s);c.strokeStyle='rgba(160,190,215,.35)';c.beginPath();c.moveTo(p.x+p.s/2,p.y+6);c.lineTo(p.x+p.s/2,p.y+p.s-6);c.moveTo(p.x+6,p.y+p.s/2);c.lineTo(p.x+p.s-6,p.y+p.s/2);c.stroke();
  const vx=st[p.axes[0]],vy=st[p.axes[1]];c.fillStyle='#3aa7d8';c.beginPath();c.arc(p.x+p.s/2*(1+vx),p.y+p.s/2*(1-vy),8,0,2*Math.PI);c.fill();c.fillStyle='#9fb2c4';c.fillText(p.axes[0]==='yaw'?'Gier / Steigen':'Roll / Nick',p.x+6,p.y+4);}
 // Servos und Blattwinkel
 const bx=w-272,by0=46;c.save();c.translate(0,by0-10);box(bx,10,262,176);c.fillStyle='#e4edf5';c.fillText('Servo [°]   Blattpitch je Azimut',bx+8,16);
 snap.servoDeg.forEach((v,i)=>{const y=34+i*13;c.fillStyle='#9fb2c4';c.fillText((i<3?'O':'U')+(i%3+1),bx+8,y);c.fillStyle='rgba(120,150,180,.3)';c.fillRect(bx+30,y+2,60,8);c.fillStyle=i<3?'#39b7c9':'#d98d55';const z=bx+60;c.fillRect(Math.min(z,z+v*3),y+2,Math.abs(v*3),8);});
 if(view&&view.pitches){view.pitches.forEach((ps,l)=>{const pcx=bx+130+l*0,pcy=l?140:70,R=30;c.strokeStyle='rgba(160,190,215,.35)';c.beginPath();c.arc(bx+150,pcy,R,0,2*Math.PI);c.stroke();c.beginPath();const mean=ps.reduce((a,b)=>a+b,0)/8;
  ps.forEach((t,j)=>{const a=(rotorAngles[l]+45*j)*D*(l?-1:1),rr=R*(.55+(t-mean)/8);const x=bx+150+rr*Math.cos(a),y=pcy-rr*Math.sin(a);j?c.lineTo(x,y):c.moveTo(x,y);});c.closePath();c.strokeStyle=l?'#d98d55':'#39b7c9';c.stroke();c.fillStyle='#c9deef';c.fillText(`${l?'unten':'oben'} ${mean.toFixed(1)}°`,bx+186,pcy-6);});}c.restore();
 if(manager?.events?.length){box(10,h-200,240,62);c.fillStyle='#c9deef';manager.events.slice(-4).forEach((e,i)=>c.fillText(`${e.t.toFixed(1)} s ${e.text}`,16,h-194+i*14));}
 c.fillStyle='#9fb2c4';c.fillText(`${view?view.drawn+' CAD-Teile':'ohne WebGL'} · Zeitlupe ${$('timescale').value}×`,240,16);}
function readout(snap){const s=sim;$('readout').textContent=`${s.crashed?'ABBRUCH: '+(s.hardLanding?'harter Bodenkontakt':'Bodennähe / große Neigung'):finished?'Testzeit beendet':paused?'PAUSE':'SIMULATION LÄUFT'} · ${scenario?scenario.name:'P10-Freiflug'}
Zeit ${snap.t.toFixed(2)} s · Masse ${s.mass.toFixed(3)} kg · Modell ${s.c.massModel}${s.c.drive==='P10_HOHLRAD'?' · Planetenstufe (Motor gleichsinnig)':''}
Position ${snap.p.map(x=>x.toFixed(2)).join(' / ')} m
Soll     ${snap.target?snap.target.map(x=>x.toFixed(2)).join(' / ')+' m':'Lagewinkel/Steigrate (ANGLE)'}
Roll/Nick/Gier ${snap.euler.map(x=>x.toFixed(1)).join(' / ')} °
Rotoren ${snap.rpm.map(x=>x.toFixed(0)).join(' / ')} U/min · Motor ${snap.rpm.map(x=>(x*6.5).toFixed(0)).join(' / ')} U/min
Induziert ${snap.vi.map(x=>x.toFixed(2)).join(' / ')} m/s · Schub ${snap.thrust.map(x=>x.toFixed(2)).join(' / ')} N
Akku ${snap.bus.toFixed(2)} V · ${snap.current.toFixed(1)} A · SoC ${(100*snap.soc).toFixed(0)} %
Servos ${snap.servoDeg.map(x=>x.toFixed(1)).join(' / ')} °
Max. geschätzte Servolast ${Math.max(...snap.servoLoadNm).toFixed(3)} Nm · Kinematiküberschreitungen ${s.envelopeViolations}
Boden ${snap.onGround?'Kontakt '+snap.contactForce.toFixed(1)+' N':'frei'} · Wind ${s.c.wind.map(x=>x.toFixed(1)).join(' / ')} m/s
Profilquelle ${s.c.polarSource} · Ersatzmodell ${(100*snap.polarFallbackFraction).toFixed(1)} %`;
 const p=$('plot'),dpr=Math.min(2,devicePixelRatio||1),w=p.clientWidth,h=p.clientHeight;if(p.width!==Math.round(w*dpr)||p.height!==Math.round(h*dpr)){p.width=Math.round(w*dpr);p.height=Math.round(h*dpr);}
 const ctx=p.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);const data=rows.slice(-500),maxT=Math.max(5,data.at(-1)?.t||5),minT=Math.max(0,maxT-25);
 for(const [color,get] of [['#61c9ff',x=>x.p[2]],['#f5d779',x=>x.target?x.target[2]:null],['#75d5a8',x=>x.euler[0]/10+1],['#e997bc',x=>x.euler[1]/10+1]]){ctx.strokeStyle=color;ctx.beginPath();let first=true;for(const r of data){const v=get(r);if(v===null)continue;const x=(r.t-minT)/(maxT-minT)*w,y=h-15-v/3*(h-25);first?ctx.moveTo(x,y):ctx.lineTo(x,y);first=false;}ctx.stroke();}}
let lastHud=0;
function frame(ts){const real=Math.min(.05,(ts-lastFrame)/1000||0);lastFrame=ts;pollGamepad();if(paused||!sim||finished)keyboardSticks(real);
 $('gamepad').textContent=game.connected?`Gamepad: ${game.id.slice(0,40)} (Mode 2)`:'Gamepad: nicht verbunden (Mode 2, A = Start, B = Landen, Y = Modus)';
 let simDt=0;if(sim&&!paused&&!finished)simDt=advance(real*+$('timescale').value);
 const snap=sim.snapshot({position:rows.at(-1)?.target});
 if(view){const st=vehicleState();if($('showParticles').checked&&simDt>0)particles.step(st,simDt);
  sliceClock+=real;if($('showSlice').checked&&(sliceClock>.15||!sliceData)){sliceData=ST.sliceField(st);sliceClock=0;}
  const vmax=Math.max(8,2.2*Math.max(...sim.vi));$('vmaxLabel').textContent=vmax.toFixed(0)+' m/s';
  const revPerFrame=sim.omega.map(o=>o/(2*Math.PI)*+$('timescale').value/60);
  view.draw({sim,servoDeg:sim.servos.map(s=>s.a/D),rotorDeg:rotorAngles,particles:particles.ready?particles:null,slice:sliceData,options:{particles:$('showParticles').checked,slice:$('showSlice').checked,rotorDisc:$('rotorDisc').checked},discAlpha:revPerFrame.map(r=>clamp((r-.12)*3,0,.55)),headingYaw:snap.euler[2]*D,speedMax:vmax,sliceMax:vmax});}
 hudDraw(snap);$('phase').textContent=manager?manager.phase:(finished?'TESTENDE':'TESTFALL');
 if(ts-lastHud>120){readout(snap);lastHud=ts;}requestAnimationFrame(frame);}
$('results').innerHTML='<table><thead><tr><th>Fall</th><th>Modellergebnis</th><th>RMS letzte 5 s</th><th>Max. Neigung</th></tr></thead><tbody>'+H01_TESTS.results.map(r=>`<tr><td>${r.name.replaceAll('_',' ')}</td><td class="${r.status==='STABIL_IM_MODELL'?'good':'bad'}">${r.status.replaceAll('_',' ')}</td><td>${r.position_rms_last5s_m===null?'–':r.position_rms_last5s_m.toFixed(3)+' m'}</td><td>${r.max_tilt_deg.toFixed(1)}°</td></tr>`).join('')+'</tbody></table>';
setMode();updateHidden();newFree();$('wind').oninput();
window.H01_APP={get sim(){return sim;},get manager(){return manager;},get view(){return view;},get particles(){return particles;},get rows(){return rows;},sticks,pad,held,glError,newFree,startCase,advance};
requestAnimationFrame(frame);
