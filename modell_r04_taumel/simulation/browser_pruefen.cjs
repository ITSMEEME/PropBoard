#!/usr/bin/env node
/* Optional integration test; Playwright + Chromium required, not used by the simulator. */
'use strict';
const http=require('http'),fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {chromium}=require('playwright');
(async()=>{
 const root=path.resolve(__dirname,'../..'),errors=[];
 const server=http.createServer((req,res)=>{let file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));if(!file.startsWith(root+path.sep)){res.writeHead(403);return res.end();}fs.readFile(file,(error,data)=>{if(error){res.writeHead(404);return res.end();}res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':file.endsWith('.html')?'text/html':'application/octet-stream');res.end(data);});});
 let browser;try{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 let exe=process.env.H01_CHROMIUM||(fs.existsSync('/opt/pw-browsers/chromium')?undefined:fs.existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined);
 browser=await chromium.launch({executablePath:exe,headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true});page.on('pageerror',error=>errors.push(error.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.goto('http://127.0.0.1:'+server.address().port+'/modell_r04_taumel/simulation/H01_Flugsimulator.html');
 await page.waitForFunction(()=>document.querySelector('#readout').textContent.includes('Zeit'));
 const tests=await page.evaluate(()=>H01_TESTS.results.length);assert.equal(await page.locator('#results tbody tr').count(),tests);
 const gl=await page.evaluate(()=>({error:H01_APP.glError,parts:H01_APP.view?H01_APP.view.parts.length:0}));assert(!gl.error&&gl.parts>500,JSON.stringify(gl));
 await page.waitForFunction(()=>H01_APP.view.drawn>100);
 // Ground start: phase sequence and real progress of the free flight (accelerated by calling the shared advance()).
 const flight=await page.evaluate(()=>{const A=H01_APP;A.newFree();const m=A.manager,s=A.sim,phases=[m.phase];m.start();
  for(let i=0;i<400&&m.phase!=='FLUG';i++){A.advance(.05);if(phases.at(-1)!==m.phase)phases.push(m.phase);}
  const z=s.p[2];return{phases,z,ground:s.groundClearanceHeight(),mass:s.mass,crashed:s.crashed};});
 assert.deepEqual(flight.phases,['AUS','HOCHLAUF','START','FLUG']);assert(flight.z>flight.ground+.8&&!flight.crashed,JSON.stringify(flight));
 // Keyboard sticks move the position reference forward; release holds it; keys ignored in fields and pause.
 const keys=await page.evaluate(()=>{const A=H01_APP,m=A.manager,press=c=>window.dispatchEvent(new KeyboardEvent('keydown',{code:c,bubbles:true,cancelable:true})),release=c=>window.dispatchEvent(new KeyboardEvent('keyup',{code:c,bubbles:true}));
  const before=[...m.reference];press('KeyW');for(let i=0;i<40;i++){A.advance(.05);}const during=A.sticks().pitch;release('KeyW');for(let i=0;i<20;i++)A.advance(.05);const after=[...m.reference];
  document.querySelector('#mass').dispatchEvent(new KeyboardEvent('keydown',{code:'KeyD',bubbles:true}));const fieldIgnored=!A.held.has('KeyD');window.dispatchEvent(new Event('blur'));return{before,after,during,fieldIgnored,cleared:A.held.size===0};});
 assert(keys.during>.5&&keys.after[0]-keys.before[0]>.5,JSON.stringify(keys));assert(keys.fieldIgnored&&keys.cleared);
 // Virtual stick (pointer) and ANGLE mode
 const box=await page.locator('#hud').boundingBox();await page.mouse.move(box.x+box.width-80,box.y+box.height-110);await page.mouse.down();await page.mouse.move(box.x+box.width-30,box.y+box.height-110);
 const padRoll=await page.evaluate(()=>H01_APP.pad.roll);await page.mouse.up();assert(padRoll>.3,String(padRoll));
 await page.check('#angleMode');const angle=await page.evaluate(()=>{const A=H01_APP;A.pad.pitch=.6;for(let i=0;i<30;i++)A.advance(.05);A.pad.pitch=0;const r=A.sim.snapshot();return{mode:A.manager.mode,pitch:r.euler[1],x:A.sim.v[0]};});
 assert(angle.mode==='ANGLE'&&angle.pitch>5,JSON.stringify(angle));
 // Landing → motors off
 const landed=await page.evaluate(()=>{const A=H01_APP;A.manager.land();for(let i=0;i<300&&A.manager.phase!=='AUS';i++)A.advance(.05);return{phase:A.manager.phase,onGround:A.sim.onGround,crashed:A.sim.crashed,events:A.manager.events.map(e=>e.text)};});
 assert(landed.phase==='AUS'&&landed.onGround&&!landed.crashed,JSON.stringify(landed));
 // Flow visualisation exists and moves; slice toggles.
 await page.check('#showSlice');await page.evaluate(()=>{const A=H01_APP;A.newFree();A.manager.start();for(let i=0;i<160;i++)A.advance(.05);});await page.waitForTimeout(600);
 const flow=await page.evaluate(()=>({ready:H01_APP.particles.ready,n:H01_APP.particles.n,vmax:Math.max(...H01_APP.particles.speed)}));assert(flow.ready&&flow.vmax>1,JSON.stringify(flow));
 await page.selectOption('#timescale','0.04');await page.click('[data-cam="detail_upper"]');await page.waitForTimeout(800);
 await page.screenshot({path:path.join(__dirname,'Ergebnisse/Browser_Desktop.png')});
 await page.click('[data-cam="chase"]');await page.selectOption('#timescale','1');
 // Scripted case playback and JSON export
 await page.selectOption('#case',{label:'Savox 7 4V Manoever'});await page.click('#start');await page.waitForFunction(()=>{const t=document.querySelector('#readout').textContent;return t.includes('Savox_7_4V_Manoever')&&Number(t.match(/Zeit ([0-9.]+)/)?.[1])>.5;});
 const state=await page.locator('#readout').innerText();assert(state.includes('1.578 kg')&&!state.includes('NaN'),state);
 const download=page.waitForEvent('download');await page.click('#export');const file=await(await download).path();const log=JSON.parse(fs.readFileSync(file));assert(log.rows.length>0&&log.cad_sha256.length===64&&log.p10_sha256.length===64);
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(300);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));
 await page.screenshot({path:path.join(__dirname,'Ergebnisse/Browser_Mobil.png')});
 assert.deepEqual(errors,[]);let result={status:'PASS',checks:['WebGL scene with native P10 parts','Ground start phases AUS→HOCHLAUF→START→FLUG','Keyboard sticks move and hold position reference','Editable fields and blur clear keys','Virtual pointer stick','ANGLE mode tilts vehicle','Landing to motors off','Flow particles move','Detail camera + slow motion screenshot','Scripted case playback','JSON export with CAD hashes','Mobile fits viewport','No JavaScript errors'],parts_rendered:gl.parts,flight,landed:landed.events,cad_sha256:log.cad_sha256,p10_sha256:log.p10_sha256};
 fs.writeFileSync(path.join(__dirname,'Ergebnisse/Browserpruefung.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 }finally{if(browser)await browser.close();server.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
