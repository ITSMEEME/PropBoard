from playwright.sync_api import sync_playwright
from pathlib import Path
import json
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
root=Path(__file__).resolve().parent
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(root.parent)))
Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}/bericht/'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,
          args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(base+'Modelle_3D.html',wait_until='load')
    page.wait_for_timeout(1000)
    assert page.locator('canvas').count()==2
    checks=page.locator('canvas').evaluate_all('(cs)=>cs.map(c=>({webgl:!!c.getContext("webgl"),error:c.getContext("webgl").getError(),width:c.width,height:c.height}))')
    assert all(c['webgl'] and c['error']==0 for c in checks),checks
    before=page.locator('canvas').first.screenshot()
    page.mouse.move(250,340);page.mouse.down();page.mouse.move(330,370,steps=8);page.mouse.up()
    page.wait_for_timeout(200)
    after=page.locator('canvas').first.screenshot()
    assert before!=after
    page.locator('button[data-view="reset"]').first.click()
    page.screenshot(path=str(root/'3D_Ansicht.png'),full_page=True)
    page.locator('input[data-kind="structure"]').first.uncheck()
    assert not errors,errors
    page.goto(base+'Vergleichsbericht.html',wait_until='load')
    images=page.locator('img').evaluate_all('(es)=>es.map(e=>({complete:e.complete,width:e.naturalWidth}))')
    assert images and all(i['complete'] and i['width']>0 for i in images)
    browser.close()
    (root/'Darstellungspruefung.json').write_text(json.dumps({'webgl':checks,'rotation_changes_image':True,'page_errors':errors,'report_images_loaded':len(images)},indent=2))
    print('Browserprüfung bestanden',checks,'Berichtsbilder:',len(images))
server.shutdown()
