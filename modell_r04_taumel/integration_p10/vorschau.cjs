#!/usr/bin/env node
/* Vorschaubilder der P10-Baugruppe aus der WebGL-Ansicht des Simulators (echte CAD-Oberflächen).
 * Benötigt Playwright + Chromium (nur Werkzeug, keine Laufzeitabhängigkeit). */
'use strict';
const http=require('http'),fs=require('fs'),path=require('path');
const {chromium}=require('playwright');
const views=[
 {file:'Vorschau_P10_Gesamt.png',cam:{mode:'orbit',yaw:-2.2,elev:.32,dist:.95},hide:[]},
 {file:'Vorschau_P10_Servohalter.png',cam:{mode:'orbit',yaw:-1.0,elev:.55,dist:.33,target:[0.0,0.03,0.12]},hide:['cover']},
 {file:'Vorschau_P10_Planetenstufe.png',cam:{mode:'orbit',yaw:-.35,elev:.12,dist:.30,target:[0,0,.0775]},hide:['blade','servo_case','linkage','cable','electronics']},
 {file:'Vorschau_P10_Kabelbaum.png',cam:{mode:'orbit',yaw:-.7,elev:.18,dist:.55,target:[0,0,0]},hide:['blade','cover']},
 {file:'Vorschau_P10_Landegestell.png',cam:{mode:'orbit',yaw:-2.6,elev:.16,dist:.8,target:[0,0,-.12]},hide:[],ground:true}];
(async()=>{const root=path.resolve(__dirname,'../..');
 const server=http.createServer((req,res)=>{let file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));if(!file.startsWith(root+path.sep)){res.writeHead(403);return res.end();}fs.readFile(file,(e,d)=>{if(e){res.writeHead(404);return res.end();}res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':'text/html');res.end(d);});});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser;
 try{browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:1200,height:900}});
  await page.goto('http://127.0.0.1:'+server.address().port+'/modell_r04_taumel/simulation/H01_Flugsimulator.html');
  await page.waitForFunction(()=>window.H01_APP&&H01_APP.view&&H01_APP.view.drawn>100);
  await page.evaluate(()=>{const A=H01_APP;A.newFree();document.querySelector('#showParticles').checked=false;document.querySelector('#pause').click();A.sim.p=[0,0,.6];document.querySelector('#hud').style.display='none';document.querySelector('.camrow').style.display='none';});
  for(const v of views){await page.evaluate(v=>{const V=H01_APP.view,S=H01_APP.sim;S.p=[0,0,v.ground?S.groundClearanceHeight():.6];Object.assign(V.cam,v.cam);V.setHidden(v.hide);if(v.cam.target){const c=V.camera.bind(V);V.camera=(sim,h)=>{const r=c(sim,h);const t=[sim.p[0]+v.cam.target[0],sim.p[1]+v.cam.target[1],sim.p[2]+v.cam.target[2]];const d=v.cam.dist,y=v.cam.yaw,e=v.cam.elev;return{target:t,eye:[t[0]+d*Math.cos(e)*Math.cos(y),t[1]+d*Math.cos(e)*Math.sin(y),t[2]+d*Math.sin(e)]};};}},v);
   await page.waitForTimeout(700);await page.locator('#scene').screenshot({path:path.join(__dirname,'Ausgabe',v.file)});
   await page.evaluate(()=>{delete H01_APP.view.camera;});console.log('saved',v.file);}
 }finally{if(browser)await browser.close();server.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
