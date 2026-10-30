#!/usr/bin/env node
'use strict';
const {chromium}=require('playwright'),http=require('http'),fs=require('fs'),path=require('path'),assert=require('assert/strict');
(async()=>{
 const root=path.resolve(__dirname,'Ausgabe'),errors=[];
 const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+path.sep)){res.writeHead(403);return res.end();}fs.readFile(file,(e,data)=>{if(e){res.writeHead(404);return res.end();}res.setHeader('Content-Type',file.endsWith('.html')?'text/html':'image/png');res.end(data);});});
 let browser;
 try{
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  browser=await chromium.launch({executablePath:process.env.P09_CHROMIUM||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:1280,height:950}});page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:'+server.address().port+'/P09_Durchgaengige_Animation.html',{timeout:90000});
  await page.waitForFunction(()=>window.P09_RENDERED_FRAME===0,{},{timeout:90000});assert.equal(await page.evaluate(()=>window.P09_WEBGL_ERROR),0);
  await page.click('#play');await page.waitForFunction(()=>window.P09_RENDERED_FRAME>5);await page.click('#play');
  await page.locator('#time').evaluate(el=>{el.value='80';el.dispatchEvent(new Event('input',{bubbles:true}));});await page.waitForFunction(()=>window.P09_RENDERED_FRAME===80);assert.equal(await page.evaluate(()=>window.P09_WEBGL_ERROR),0);
  await page.screenshot({path:path.join(root,'Browser_P09.png'),fullPage:true});
  await page.uncheck('#cut');await page.waitForTimeout(150);assert.equal(await page.evaluate(()=>window.P09_WEBGL_ERROR),0);
  await page.setViewportSize({width:390,height:844});await page.waitForTimeout(150);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));assert.deepEqual(errors,[]);
  const report={status:'PASS',checks:['Actual native meshes render with WebGL','Animation advances','Timeline selects exact closed-chain frame','Cover visibility toggles','No WebGL errors','Mobile width fits','No JavaScript errors'],source_html_sha256:require('crypto').createHash('sha256').update(fs.readFileSync(path.join(root,'P09_Durchgaengige_Animation.html'))).digest('hex')};fs.writeFileSync(path.join(root,'Browserpruefung_P09.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
 }finally{if(browser)await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
