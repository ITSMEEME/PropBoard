(async function(){
  'use strict';
  const $=id=>document.getElementById(id),P=P14Physics,C=P14Pilot,fmt=(x,d=1)=>Number(x).toLocaleString('de-DE',{minimumFractionDigits:d,maximumFractionDigits:d});
  const labels={OFF:'Bereit',TAKEOFF:'Hochlauf / Start',FLIGHT:'Freiflug',LANDING:'Landung',STOPPING:'Motoren aus · Auslauf',CRASH:'Versuch beendet'};
  try{
    let config=P.clone(P14_MODEL.config),flight,pilot,running=false,busy=false,expired=false,last=performance.now(),hudAge=1,angles=[0,0],trace=[],request=0,operation=0,aircraftCase='conservative_spec';
    const viewer=new P14View.Viewer($('view'));viewer.enableNavigation();viewer.distance=4700;viewer.target=[0,0,450];viewer.el=23;viewer.az=-145;
    const options=()=>({payload:+$('payload').value,payloadZ:+$('payloadZ').value});
    const status=text=>{$('status').textContent=text;};
    const focus=()=>$('view').focus({preventScroll:true});
    const hoverOutsideLimits=()=>{if(!pilot.hover)return false;const limits=P.motorLimits(config,flight.commands),w=pilot.hover.rpm*Math.PI/30;return pilot.hover.torques_Nm.some(q=>q>limits.torque_Nm||q*w/limits.efficiency_assumed>limits.inputPower_W);};
    const input=new P14Input.Input({onAction:action,onBlur:()=>pause('Pausiert nach Fokusverlust. Mit Leertaste fortsetzen.')});
    function pause(message){running=false;input.clear();$('pause').textContent='Fortsetzen / Leertaste';if(message)status(message);}
    function motorInfo(){const training=aircraftCase==='free_assumption';$('motorBadge').textContent=training?'Flugtraining · freie Motorleistung':aircraftCase==='bench_peak'?'Prüfmaxima · Dauer unbekannt':'MN1330 · 3,4 kW / 180 s';$('motorBadge').classList.toggle('training-active',training);$('motorInfo').textContent=training?'Flugtraining mit150 Nm /40 kW je Motor. Diese Leistung ist für den MN1330 nicht belegt.':aircraftCase==='bench_peak'?'46,25 Nm /16,27 kW je Motor als Prüfmaxima. Haltedauer unbekannt; keine Dauerkennlinie.':'46,25 Nm und3,4 kW je Motor. Der180-s-Zeitbezug bleibt aktiv; im Standardfall reicht der Schub nicht zum Abheben.';}
    function reset(){operation++;busy=false;expired=false;input.clear();flight=new P.Flight(config,P14_MASS,options());flight.commands.motorMode=aircraftCase;flight.commands.torqueCap=aircraftCase==='free_assumption'?150:46.25;flight.commands.inputPowerCap=aircraftCase==='free_assumption'?40000:aircraftCase==='bench_peak'?16270:3400;pilot=new C.Pilot(flight);pilot.setMode($('controlMode').value);running=false;angles=[0,0];trace=[];$('blades').value=config.geometry.blades_per_rotor;$('pairs').value=config.geometry.lift_units;$('pause').textContent='Pause / Leertaste';motorInfo();hudAge=1;status('Bereit. T startet den gewählten Motorfall. „Trainingsflug“ wählt freie Motorleistung.');refresh();}
    async function start(){
      if(busy)return;if(pilot.phase==='CRASH'){status('Versuch beendet. Zuerst mit ⌫ zurücksetzen.');return;}
      if(expired||(flight.time>=180&&aircraftCase==='conservative_spec')){status('180-s-Zeitbezug erreicht. Zuerst zurücksetzen.');return;}
      if(['FLIGHT','TAKEOFF','LANDING'].includes(pilot.phase)){running=true;$('pause').textContent='Pause / Leertaste';return;}
      const op=++operation;busy=true;status('Schwebereferenz und Steuerwirkung werden berechnet …');await new Promise(resolve=>setTimeout(resolve,20));
      try{if(op!==operation)return;pilot.start();running=true;$('pause').textContent='Pause / Leertaste';status(hoverOutsideLimits()?'Schwebereferenz über dem gewählten Motorrahmen. Nutzlast/Blattzahl ändern oder ausdrücklich Trainingsleistung wählen.':aircraftCase==='free_assumption'?'Trainingsflug gestartet. WASD bewegen · RF Höhe · QE drehen.':'MN1330-Rechenfall gestartet. Der gewählte Leistungsrahmen bleibt wirksam; eine bestätigte Sonderrotorkennlinie fehlt.');}catch(e){status(e.message);}finally{if(op===operation){busy=false;focus();}}
    }
    function action(name){if(name==='reset'){reset();return;}if(busy)return;
      if(name==='start'){void start();return;}
      if(name==='land'){pilot.land();if(['LANDING','STOPPING'].includes(pilot.phase)){running=true;status('Landung / Abbruch des Starts. Die Rotoren laufen nach dem Aufsetzen aus.');}return;}
      if(name==='stop'){pilot.stop();running=true;status('Motoren aus: Die Rotoren laufen physikalisch aus.');return;}
      if(name==='pause'){if(running)pause('Pausiert. Mit Leertaste fortsetzen.');else if(pilot.phase==='OFF')status('Bereit. T startet den gewählten Motorfall.');else if(!expired&&pilot.phase!=='CRASH'&&!(flight.time>=180&&aircraftCase==='conservative_spec')){running=true;input.clear();$('pause').textContent='Pause / Leertaste';status('Fortgesetzt.');}return;}
      if(name==='mode'){$('controlMode').value=pilot.mode==='POSITION'?'ANGLE':'POSITION';setMode();return;}
      if(name==='camera'){const values=['follow','orbit','overview'];$('camera').value=values[(values.indexOf($('camera').value)+1)%values.length];setCamera();}
    }
    function setMode(){pilot.setMode($('controlMode').value);$('modeInfo').textContent=pilot.mode==='POSITION'?'WASD bewegt das Modell. Beim Loslassen bremst der Modellregler und hält die Position.':'WASD gibt Roll/Nick bis10° vor. Beim Loslassen richtet sich das Modell auf; Geschwindigkeit wird nicht automatisch abgebaut.';}
    function setCamera(){const mode=$('camera').value;viewer.el=mode==='overview'?75:23;viewer.distance=mode==='overview'?Math.max(10000,...flight.properties.bounds_m.map(x=>x*2300)):Math.max(mode==='orbit'?6000:4700,...flight.properties.bounds_m.map(x=>x*1800));viewer.az=mode==='orbit'?-65:viewer.az;$('cameraHint').textContent=(mode==='follow'?'Verfolger':mode==='orbit'?'Orbit':'Übersicht')+' · Raster1 m · Pfeil = vorne';}
    async function loadVariant(n){if(globalThis.P14_VARIANTS?.[n])return P14_VARIANTS[n];await new Promise((resolve,reject)=>{const script=document.createElement('script');script.src='Ausgabe/variante_'+n+'.js';script.onload=resolve;script.onerror=()=>reject(Error('CAD-Variante'+n+' fehlt.'));document.head.appendChild(script);});return P14_VARIANTS[n];}
    async function changeModel(){const id=++request,op=++operation,n=+$('blades').value,pairs=+$('pairs').value;pause();busy=true;status('CAD-Variante und Trägheit werden geladen …');try{const variant=await loadVariant(n);if(id!==request||op!==operation)return;config.geometry.blades_per_rotor=n;config.geometry.lift_units=pairs;viewer.setVariant(variant);reset();setCamera();}catch(e){status(e.message);}finally{if(id===request&&op===operation)busy=false;}}
    function advance(dt){
      if(!running||busy)return;if(!(dt>0&&dt<=.1))throw Error('Modellzeitschritt muss0..100ms sein');let remaining=dt;
      while(remaining>1e-8&&running){const h=Math.min(1/120,remaining),previous={vz:flight.velocity[2]};
        try{pilot.update(sticks,h);if(pilot.phase==='CRASH'){pause(pilot.reason);break;}flight.step(h);pilot.afterStep(previous);if(pilot.phase==='CRASH')pause(pilot.reason);}
        catch(e){if(e.message.includes('180-s'))expired=true;pause(e.message+' · Zurücksetzen oder Motorfall ändern.');break;}
        for(let k=0;k<2;k++)angles[k]=(angles[k]-flight.shaftOmega[k]*h/P.D*.035)%360;
        remaining-=h;
      }
    }
    const row=(label,value)=>'<div><span>'+label+'</span><strong>'+value+'</strong></div>';
    function map(){const canvas=$('map'),ctx=canvas.getContext('2d'),w=canvas.width,h=canvas.height,span=20,scale=Math.min(w,h)/(span*2),origin=[w/2,h/2];ctx.clearRect(0,0,w,h);ctx.strokeStyle='#2b4454';ctx.lineWidth=1;for(let x=-20;x<=20;x+=5){ctx.beginPath();ctx.moveTo(origin[0]+x*scale,0);ctx.lineTo(origin[0]+x*scale,h);ctx.moveTo(0,origin[1]+x*scale);ctx.lineTo(w,origin[1]+x*scale);ctx.stroke();}const to=p=>[origin[0]+p[0]*scale,origin[1]-p[1]*scale];ctx.strokeStyle='#68dcca';ctx.beginPath();for(let i=0;i<trace.length;i++){const p=to(trace[i]);i?ctx.lineTo(...p):ctx.moveTo(...p);}ctx.stroke();ctx.fillStyle='#b2cbd8';ctx.font='10px system-ui';ctx.fillText('±20 m · Startzentrum',8,15);const p=to(flight.position),yaw=C.euler(flight.quaternion)[2];ctx.save();ctx.translate(...p);ctx.rotate(-yaw);ctx.fillStyle='#fff';ctx.beginPath();ctx.moveTo(10,0);ctx.lineTo(-6,-5);ctx.lineTo(-6,5);ctx.closePath();ctx.fill();ctx.restore();}
    function refresh(){
      const f=flight,anglesEuler=C.euler(f.quaternion).map(x=>x/P.D),limits=P.motorLimits(config,f.commands),rpm=f.shaftOmega.map(w=>w*60/(2*Math.PI));
      $('height').textContent=fmt(f.height,2);$('speed').textContent=fmt(Math.hypot(...f.velocity),2);$('heading').textContent=fmt(Math.round((anglesEuler[2]+360)%360)%360,0);$('time').textContent=fmt(f.time,1);
      $('phase').textContent=(running?labels[pilot.phase]:'Pausiert / '+labels[pilot.phase])+' · '+(pilot.mode==='POSITION'?'Position':'Winkel');
      $('geometry').textContent=config.geometry.blades_per_rotor+' Blätter · '+config.geometry.lift_units+' Rotorpaar'+(config.geometry.lift_units>1?'e':'');
      $('payloadOut').textContent=fmt(+$('payload').value,0)+' kg';$('payloadZOut').textContent=fmt(+$('payloadZ').value,2)+' m';
      const power=(f.lastInputPowerPerMotor||[0,0]).reduce((a,b)=>a+b,0)*config.geometry.lift_units;
      $('telemetry').innerHTML=row('Gesamtmasse',fmt(f.properties.mass,2)+' kg')+row('Zielhöhe',fmt(pilot.targetHeight,2)+' m')+row('Position X / Y',fmt(f.position[0],2)+' / '+fmt(f.position[1],2)+' m')+row('Roll / Nick',fmt(anglesEuler[0],1)+' / '+fmt(anglesEuler[1],1)+'°')+row('Drehzahl oben / unten',rpm.map(n=>fmt(n,0)).join(' / ')+'/min')+row('Motoraufnahme gesamt',fmt(power/1000,2)+' kW')+row('Decke je Motor',fmt(limits.torque_Nm,2)+' Nm / '+fmt(limits.inputPower_W/1000,2)+' kW');
      const warnings=[];if(f.properties.multiUnitConnectionMissing)warnings.push('Verbindungsrahmen zwischen den Rotorpaaren fehlt; dessen Masse und Steifigkeit sind nicht enthalten.');if(!f.properties.vehicleEnvelopeMet)warnings.push('Diese Anordnung überschreitet das Fahrzeug-Zielmaß.');$('modelWarning').hidden=warnings.length===0;$('modelWarning').textContent=warnings.join(' ');
      if(running&&f.contact&&f.time>4&&hoverOutsideLimits())status('Leistungsgrenze: Die Schwebereferenz liegt über dem gewählten Motorrahmen. Nutzlast/Blattzahl ändern oder ausdrücklich Trainingsleistung wählen.');
      $('gamepad').textContent=input.padLabel+'. Mode2: links Höhe/Gier, rechts Bewegung; A Start, B Landung, Y Modus, Start Pause.';
      trace.push(f.position.slice(0,2));if(trace.length>600)trace.shift();map();
    }
    let sticks=P14Input.neutral();
    function frame(now){const elapsed=Math.min(.1,(now-last)/1000);last=now;sticks=input.sample();advance(elapsed*+$('timescale').value);if($('camera').value==='follow')viewer.az=C.euler(flight.quaternion)[2]/P.D-145;viewer.draw(config,flight.commands,angles,flight);hudAge+=elapsed;if(hudAge>.15){refresh();hudAge=0;}requestAnimationFrame(frame);}
    $('start').onclick=()=>{void start();};$('land').onclick=()=>{action('land');focus();};$('pause').onclick=()=>{action('pause');focus();};$('reset').onclick=()=>{reset();focus();};
    $('training').onclick=()=>{aircraftCase='free_assumption';$('motorMode').value=aircraftCase;reset();void start();};
    $('motorMode').onchange=()=>{aircraftCase=$('motorMode').value;reset();};
    $('controlMode').onchange=setMode;$('camera').onchange=setCamera;
    for(const id of ['blades','pairs'])$(id).onchange=()=>{void changeModel();};
    for(const id of ['payload','payloadZ'])$(id).oninput=()=>reset();
    let pointerStart=null;
    $('view').addEventListener('pointerdown',e=>{focus();pointerStart=[e.clientX,e.clientY];});
    $('view').addEventListener('pointermove',e=>{if(pointerStart&&Math.hypot(e.clientX-pointerStart[0],e.clientY-pointerStart[1])>3&&$('camera').value==='follow'){$('camera').value='orbit';$('cameraHint').textContent='Orbit · Raster1 m · Pfeil = vorne';}});
    for(const event of ['pointerup','pointercancel','lostpointercapture'])$('view').addEventListener(event,()=>pointerStart=null);
    $('export').onclick=()=>{const saved=P.clone(config);saved.production_ready=false;saved.operating.payload_kg=options().payload;saved.development_profile={commands:{...flight.commands},options:options(),pilot_mode:pilot.mode,interactive_training:aircraftCase==='free_assumption',source_native_sha256:P14_MODEL.source_native_sha256,unverified_motor_curve:true,multi_unit_connection_missing:config.geometry.lift_units>1};const url=URL.createObjectURL(new Blob([JSON.stringify(saved,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='P14_Flugsimulator_'+config.geometry.blades_per_rotor+'B_'+config.geometry.lift_units+'Paare.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
    viewer.setVariant(await loadVariant(config.geometry.blades_per_rotor));reset();for(const id of ['start','land','pause','reset','training'])$(id).disabled=false;
    globalThis.P14_SIM={get config(){return config;},get flight(){return flight;},get pilot(){return pilot;},get running(){return running;},get busy(){return busy;},viewer,input,action,refresh,advance:dt=>{sticks=input.sample();advance(dt);}};
    requestAnimationFrame(frame);focus();
  }catch(e){$('error').hidden=false;$('error').textContent=e.message;console.error(e);}
})();
