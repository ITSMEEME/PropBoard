/* Run against a local repository HTTP server. Optional dependency: Playwright. */
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert/strict');
const H=__dirname,url=process.env.P14_TEST_URL||'http://127.0.0.1:8050/kreis_r04/mn1330_p14/P14_Entwicklungspruefstand.html';
(async()=>{
  const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader','--use-angle=swiftshader']});
  const page=await browser.newPage({viewport:{width:1600,height:1050}}),errors=[],checks=[];page.on('pageerror',e=>errors.push(e.message));
  try{
    await page.goto(url,{waitUntil:'load'});await page.waitForFunction(()=>globalThis.P14_APP?.viewer?.lastDrawCount>100,{timeout:30000});
    assert.equal(await page.locator('#error').isVisible(),false);await page.click('#animate');checks.push('Local HTML, all source scripts, Float32 WebGL and actual CAD render');
    const before=await page.evaluate(()=>({mass:P14_APP.flight.properties.mass,blades:P14_APP.config.geometry.blades_per_rotor,draws:P14_APP.viewer.lastDrawCount,error:P14_APP.viewer.gl.getError(),native_sha256:P14_MODEL.source_native_sha256}));assert.equal(before.blades,8);assert.equal(before.error,0);assert(before.mass>167);
    assert.equal(await page.inputValue('#powerCap'),'3400');assert(await page.isDisabled('#cap'));await page.selectOption('#motorMode','bench_peak');assert.equal(await page.inputValue('#powerCap'),'16270');assert((await page.textContent('#configurationWarning')).includes('Haltedauer'));await page.selectOption('#motorMode','conservative_spec');checks.push('Separate180s and unknown-duration motor cases; bounds visibly locked');
    await page.click('#trim');assert(+await page.inputValue('#cl')>1);checks.push('Torque trim updates real lower swashplate control');
    for(const [id,value]of [['cx','.4'],['cy','.4']])await page.locator('#'+id).evaluate((e,v)=>{e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}));},value);
    const norm=await page.evaluate(()=>Math.hypot(P14_APP.commands.cyclicX,P14_APP.commands.cyclicY));assert(norm<=.500001);checks.push('Cyclic vector limit is enforced');
    await page.selectOption('#blades','12');await page.waitForFunction(()=>P14_APP.config.geometry.blades_per_rotor===12&&P14_APP.flight.config.geometry.blades_per_rotor===12);
    await page.selectOption('#pairs','2');await page.waitForFunction(()=>P14_APP.flight.config.geometry.lift_units===2);
    const changed=await page.evaluate(()=>({mass:P14_APP.flight.properties.mass,cg:P14_APP.flight.properties.cg,connection:P14_APP.flight.properties.multiUnitConnectionMissing,missing:document.querySelector('#configurationWarning').textContent,hash:P14_VARIANTS[12].geometry_source_sha256,expected:P14_MASS.geometry_source_sha256}));assert(changed.mass>before.mass);assert(changed.connection);assert(changed.missing.includes('Verbindungsstruktur'));assert.equal(changed.hash,changed.expected);checks.push('12-blade rebuilt CAD and 2-pair mass/inertia layout; missing connection visibly flagged');
    const download=page.waitForEvent('download');await page.click('#export');const file=await download;const saved=JSON.parse(fs.readFileSync(await file.path(),'utf8'));assert.equal(saved.geometry.blades_per_rotor,12);assert.equal(saved.geometry.lift_units,2);assert.equal(saved.production_ready,false);checks.push('Parameterized profile exports with release gate intact');
    await page.selectOption('#blades','8');await page.selectOption('#pairs','1');await page.waitForFunction(()=>P14_APP.flight.config.geometry.blades_per_rotor===8&&P14_APP.flight.config.geometry.lift_units===1);
    for(const id of ['cx','cy'])await page.locator('#'+id).evaluate(e=>{e.value=0;e.dispatchEvent(new Event('input',{bubbles:true}));});
    await page.click('#trim');await page.click('#study');await page.waitForFunction(()=>globalThis.P14_LAST_STUDY?.found,{timeout:30000});
    const hover=await page.evaluate(()=>P14_LAST_STUDY);assert(hover.rpm>1800&&hover.torques_Nm[0]>60);checks.push('Hover study reports power demand and unverified motor curve');
    await page.click('#fly');await page.waitForFunction(()=>P14_APP.flight.time>.1);const moving=await page.evaluate(()=>({height:P14_APP.flight.height,rpm:P14_APP.flight.shaftOmega[0]}));assert.equal(moving.height,0);assert(moving.rpm>0);await page.evaluate(()=>{P14_APP.flight.time=179.999;});await page.waitForFunction(()=>document.querySelector('#fly').disabled);assert((await page.textContent('#status')).includes('180-s'));await page.click('#reset');checks.push('Runtime shaft spin-up, insufficient thrust and180s stop of the calculation');
    await page.screenshot({path:path.join(H,'Ansichten/P14_Pruefstand.png'),fullPage:true});
    await page.selectOption('#camera','centre');await page.uncheck('#foils');await page.uncheck('#lower');await page.waitForTimeout(400);await page.locator('.viewport').screenshot({path:path.join(H,'Ansichten/P14_Zentrum_Interaktiv.png')});
    await page.selectOption('#camera','all');await page.check('#foils');await page.check('#lower');await page.setViewportSize({width:390,height:844});await page.waitForTimeout(400);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));checks.push('Mobile layout fits viewport');
    assert.deepEqual(errors,[]);assert.equal(await page.locator('#error').isVisible(),false);
    const report={passed:true,native_sha256:before.native_sha256,checks,before,changed,hover,console_page_errors:errors};fs.writeFileSync(path.join(H,'Ausgabe/Browser_Pruefung.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
  }catch(e){await page.screenshot({path:'/tmp/p14-browser-failure.png',fullPage:true});console.error('PAGE ERRORS',errors);throw e;}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
