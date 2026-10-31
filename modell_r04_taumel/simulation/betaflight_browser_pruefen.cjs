'use strict';
// Uses the REAL running firmware. Only browser->localhost transport is adapted
// through Playwright IPC because this runner blocks browser loopback navigation.
const {chromium}=require('playwright'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{let browser;try{
 const status=await(await fetch('http://127.0.0.1:8765/api/betaflight/status')).json();assert(status.realFirmware);
 browser=await chromium.launch({executablePath:process.env.H01_CHROMIUM||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-crashpad-for-testing']});
 const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.exposeFunction('realFirmwareRequest',async(url,options)=>{assert(url.startsWith('/api/betaflight/'));const r=await fetch('http://127.0.0.1:8765'+url,{method:options?.method||'GET',body:options?.body,headers:options?.headers,signal:AbortSignal.timeout(3000)});return{status:r.status,text:await r.text()};});
 await page.evaluate(()=>{
  window.fetch=async(url,options)=>{const r=await window.realFirmwareRequest(url,{method:options?.method,body:options?.body,headers:options?.headers});return new Response(r.text,{status:r.status,headers:{'Content-Type':'application/json'}});};
  window.firmwarePad={id:'SITL test controller',index:0,connected:true,mapping:'standard',axes:[0,1,0,0],buttons:[]};Object.defineProperty(navigator,'getGamepads',{value:()=>[window.firmwarePad]});
  const get=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(k,...args){return String(k).includes('webgl')?null:get.call(this,k,...args);};
 });
 const html=fs.readFileSync(path.join(__dirname,'H01_Flugsimulator.html'),'utf8').replace(/<script src="([^"]+)"><\/script>/g,(_,src)=>'<script>'+fs.readFileSync(path.resolve(__dirname,src),'utf8').replace(/<\/script/gi,'<\\/script')+'</script>');
 await page.setContent(html);await page.waitForFunction(()=>window.H01_APP?.sticks().throttle===-1);
 await page.selectOption('#firmwareMode','betaflight');await page.click('#connectFirmware');await page.waitForFunction(()=>H01_APP.firmware.ready);
 assert((await page.locator('#firmwareStatus').innerText()).includes('4.5.2'));assert(await page.locator('#timescale').isDisabled());
 await page.click('#takeoff');await page.waitForFunction(()=>H01_APP.firmware.actualArmed,{timeout:10000});
 await page.evaluate(()=>window.firmwarePad.axes[1]=0);await page.waitForFunction(()=>Math.min(...H01_APP.sim.duty)>.2&&Math.max(...H01_APP.sim.omega)>10,{timeout:10000});
 await page.click('#pause');assert(await page.evaluate(()=>H01_APP.paused));await page.waitForTimeout(800);
 const actual=await(await fetch('http://127.0.0.1:8765/api/betaflight/status')).json();assert(!actual.armed,'pause/watchdog must disarm the actual firmware');
 assert.deepEqual(errors,[]);console.log('PASS: browser selects genuine firmware, verified 4.5.2 handshake, actual ARM, real motor outputs advance the plant, pause disarms. Firmware was not mocked; test uses IPC only for localhost HTTP transport.');
}finally{if(browser)await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
