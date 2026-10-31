'use strict';
const {chromium}=require('playwright'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const errors=[];
 let browser;try{
  browser=await chromium.launch({executablePath:process.env.H01_CHROMIUM||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-crashpad-for-testing','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:1440,height:1000}});page.on('pageerror',e=>errors.push(e.message));
  // Exercise input integration in the supported no-WebGL mode, using a mocked storage adapter.
  await page.evaluate(()=>{
   window.testPad={id:'Calibration integration stick',mapping:'standard',index:0,connected:true,axes:[.1,-.1,.05,-.05],buttons:Array.from({length:4},()=>({pressed:false,value:0}))};
   Object.defineProperty(navigator,'getGamepads',{value:()=>window.testPad?[window.testPad]:[]});
   const get=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...args){return String(kind).includes('webgl')?null:get.call(this,kind,...args);};
   const memory=new Map();Object.defineProperty(window,'localStorage',{value:{getItem:k=>memory.get(k)||null,setItem:(k,v)=>memory.set(k,v),removeItem:k=>memory.delete(k)}});
  });
  const file=path.join(__dirname,'H01_Flugsimulator.html');
  const html=fs.readFileSync(file,'utf8').replace(/<script src="([^"]+)"><\/script>/g,(_,src)=>'<script>'+fs.readFileSync(path.resolve(__dirname,src),'utf8').replace(/<\/script/gi,'<\\/script')+'</script>');
  await page.setContent(html,{waitUntil:'domcontentloaded',timeout:30000});
  await page.waitForFunction(()=>window.H01_APP&&H01_APP.calibration.gp);
  const sample=async axes=>{await page.evaluate(a=>window.testPad.axes=a,axes);await page.waitForTimeout(80);};
  await page.click('#calibrate');await page.waitForFunction(()=>H01_APP.calibration.active);
  assert(await page.evaluate(()=>H01_APP.paused));await page.click('#calCenter');
  await page.keyboard.press('KeyT');await page.keyboard.press('Space');assert(await page.evaluate(()=>H01_APP.paused));
  await page.evaluate(()=>{window.testPad.buttons[0].pressed=true;window.testPad.buttons[3].pressed=true;});
  await sample([-.7,-.8,-.65,-.75]);await sample([.9,.7,.85,.65]);
  assert.deepEqual(await page.evaluate(()=>H01_APP.sticks()),{throttle:0,yaw:0,pitch:0,roll:0});
  assert.equal(await page.evaluate(()=>H01_APP.manager.phase),'AUS');
  await page.selectOption('#calAxis_yaw','2');await page.selectOption('#calAxis_roll','0');await page.check('#calInvert_yaw');await page.fill('#calDeadzone','10');
  await page.screenshot({path:'/tmp/PropBoard_Gamepad_Kalibrierung.png'});
  await page.click('#calSave');assert(!(await page.locator('#calibration').isVisible()));assert(await page.evaluate(()=>H01_APP.calibration.saved&&H01_APP.paused));
  await sample([.9,-.1,.05,-.05]);assert.equal(await page.evaluate(()=>H01_APP.sticks().roll),1);
  await sample([.1,-.1,-.65,-.05]);assert.equal(await page.evaluate(()=>H01_APP.sticks().yaw),1);
  assert.equal(await page.evaluate(()=>H01_APP.manager.phase),'AUS','held calibration buttons must not trigger takeoff');
  assert(await page.evaluate(()=>{const c=new H01Gamepad.Controller(localStorage);c.sample(window.testPad);return c.saved&&c.profile.channels.yaw.axis===2;}));
  assert.equal(await page.evaluate(()=>H01_APP.calibration.profile.channels.yaw.axis),2);
  await page.evaluate(()=>window.testPad=null);await page.waitForTimeout(80);assert.deepEqual(await page.evaluate(()=>H01_APP.sticks()),{throttle:0,yaw:0,pitch:0,roll:0});
  await page.evaluate(()=>window.testPad={id:'Calibration integration stick',mapping:'standard',index:0,connected:true,axes:[.1,-.1,.05,-.05],buttons:Array.from({length:4},()=>({pressed:false,value:0}))});await page.waitForTimeout(80);
  await page.click('#calibrate');await page.click('#calCenter');await page.click('#calSave');assert(await page.locator('#calibration').isVisible());assert((await page.locator('#calStatus').innerText()).includes('beide Richtungen'));
  await page.keyboard.press('Escape');assert(!await page.evaluate(()=>H01_APP.calibration.active));
  await page.click('#calibrate');await page.click('#calReset');assert(!await page.evaluate(()=>H01_APP.calibration.saved));
  await page.setViewportSize({width:390,height:844});await page.click('#calibrate');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));await page.click('#calCancel');
  await page.evaluate(()=>window.testPad.buttons[0].pressed=true);await page.waitForFunction(()=>H01_APP.manager.phase==='HOCHLAUF');
  assert(!await page.evaluate(()=>H01_APP.paused));
  await page.evaluate(()=>{window.testPad.buttons[0].pressed=false;H01_APP.held.add('KeyW');H01_APP.advance(.05);});assert((await page.evaluate(()=>H01_APP.sticks().pitch))>0);
  assert(await page.evaluate(()=>!!H01_APP.glError),'supported no-WebGL fallback');
  assert.deepEqual(errors,[]);console.log('PASS: dialog, pause/input lock, center/range, mapping/inversion, profile reloading (mock browser storage), disconnect, invalid save, Escape, reset, gamepad takeoff and keyboard in supported no-WebGL mode. GPU rendering and real-browser storage persistence not tested (storage behavior covered by unit tests).');
 }finally{if(browser)await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
