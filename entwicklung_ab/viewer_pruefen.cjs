const {chromium}=require('playwright'),path=require('path'),fs=require('fs'),http=require('http');
(async()=>{
const server=http.createServer((req,res)=>{let file=path.resolve(__dirname,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));if(!file.startsWith(__dirname+path.sep)){res.writeHead(403);res.end();return;}fs.readFile(file,(e,data)=>{if(e){res.writeHead(404);res.end();return;}res.setHeader('Content-Type',file.endsWith('.js')?'application/javascript':file.endsWith('.html')?'text/html; charset=utf-8':'application/octet-stream');res.end(data);});});await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const systemBrowser=process.env.AB_CHROMIUM_PATH||(fs.existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined);
const browser=await chromium.launch({headless:true,executablePath:systemBrowser,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1440,height:980}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:'+server.address().port+'/Modelle.html');await page.waitForFunction(()=>window.AB_VIEWER?.current==='QUAD_R380');let checks=[];
for(const id of ['P14_R750','P14_R800','QUAD_R380','HEXA_R265_B4']){
 await page.selectOption('#case',id);await page.waitForFunction(expected=>AB_VIEWER.current===expected,id);
 let info=await page.evaluate(()=>{const c=document.querySelector('canvas'),g=c.getContext('webgl'),a=new Uint8Array(c.width*c.height*4);g.readPixels(0,0,c.width,c.height,g.RGBA,g.UNSIGNED_BYTE,a);let visible=0;for(let i=0;i<a.length;i+=40)if(Math.abs(a[i]-237)+Math.abs(a[i+1]-245)+Math.abs(a[i+2]-247)>30)visible++;return{webgl_error:g.getError(),visible_samples:visible,facts:document.getElementById('facts').innerText};});
 if(info.webgl_error||info.visible_samples<100)throw Error('Rendering failed '+id);checks.push({case:id,passed:true,...info});
}
await page.selectOption('#case','QUAD_R380');let before=await page.locator('canvas').screenshot();await page.click('#deck');let hidden=await page.locator('canvas').screenshot();if(before.equals(hidden))throw Error('Deck visibility did not change');await page.click('#deck');checks.push({test:'deck visibility',passed:true});
const box=await page.locator('canvas').boundingBox();await page.mouse.move(box.x+box.width*.5,box.y+box.height*.5);await page.mouse.down();await page.mouse.move(box.x+box.width*.7,box.y+box.height*.57,{steps:6});await page.mouse.up();let rotated=await page.locator('canvas').screenshot();if(rotated.equals(before))throw Error('Orbit did not change view');checks.push({test:'pointer orbit',passed:true});
await page.click('#iso');await page.screenshot({path:path.join(__dirname,'Viewer_Vorschau.png'),fullPage:true});
await page.setViewportSize({width:480,height:920});await page.selectOption('#case','HEXA_R265_B4');await page.click('#top');checks.push({test:'mobile layout and top view',passed:await page.evaluate(()=>AB_VIEWER.current==='HEXA_R265_B4'&&!document.querySelector('#error').textContent)});
if(errors.length||checks.some(c=>!c.passed))throw Error(JSON.stringify(errors));
fs.writeFileSync(path.join(__dirname,'Viewer_Pruefung.json'),JSON.stringify({checks,page_errors:errors},null,2));console.log(checks.length+' viewer checks passed');await browser.close();await new Promise(resolve=>server.close(resolve));
})().catch(e=>{console.error(e);process.exit(1);});
