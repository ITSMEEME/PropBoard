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
 let exe=process.env.H01_CHROMIUM||(fs.existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined);
 browser=await chromium.launch({executablePath:exe,headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true});page.on('pageerror',error=>errors.push(error.message));
 await page.goto('http://127.0.0.1:'+server.address().port+'/modell_r04_taumel/simulation/H01_Flugsimulator.html');
 await page.waitForFunction(()=>document.querySelector('#readout').textContent.includes('Zeit'));
 assert.equal(await page.locator('#results tbody tr').count(),19);
 await page.click('#start');await page.waitForFunction(()=>Number(document.querySelector('#readout').textContent.match(/Zeit ([0-9.]+)/)?.[1])>.5);await page.click('#pause');
 const state=await page.locator('#readout').innerText();assert(state.includes('1.578 kg'));assert(!state.includes('NaN'));
 const download=page.waitForEvent('download');await page.click('#export');const file=await(await download).path();const log=JSON.parse(fs.readFileSync(file));assert(log.rows.length>0&&log.cad_sha256.length===64);
 await page.screenshot({path:path.join(__dirname,'Ergebnisse/Browser_Desktop.png'),fullPage:true});
 await page.selectOption('#case','5');assert.equal(await page.inputValue('#mass'),'60');await page.click('#start');await page.waitForFunction(()=>document.querySelector('#readout').textContent.includes('1.524 kg'));await page.click('#pause');
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(250);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));
 assert.deepEqual(errors,[]);let result={status:'PASS',checks:['Desktop initializes','Simulation advances','19 result rows','JSON download contains real log','60g servo case loads and runs','Mobile fits viewport','No JavaScript page errors'],cad_sha256:log.cad_sha256};
 fs.writeFileSync(path.join(__dirname,'Ergebnisse/Browserpruefung.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 }finally{if(browser)await browser.close();server.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
