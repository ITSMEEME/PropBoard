from pathlib import Path
from functools import partial
from threading import Thread
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
import json
HERE=Path(__file__).resolve().parent
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(HERE.parent)))
Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1440,'height':1000})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(f'http://127.0.0.1:{server.server_port}/konstruktion/Modelle_3D.html',wait_until='load',timeout=120000)
        page.wait_for_timeout(1000)
        assert page.locator('canvas').count()==7
        checks=page.locator('canvas').evaluate_all('(cs)=>cs.map(c=>({width:c.width,height:c.height,error:c.getContext("webgl").getError()}))')
        assert all(c['error']==0 for c in checks),checks
        for i in range(7):
            page.locator('canvas').nth(i).screenshot(path=str(HERE/f'Ansicht_{i:02}.png'))
        detail=page.locator('section.card').nth(6)
        detail.locator('input[data-kind="stator"]').uncheck()
        detail.locator('canvas').screenshot(path=str(HERE/'Ansicht_06_Schlitten_frei.png'))
        card=page.locator('section.card').first
        before=card.locator('canvas').screenshot()
        canvasbox=card.locator('canvas').bounding_box()
        x=canvasbox['x']+200;y=canvasbox['y']+200
        page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+60,y+20,steps=5);page.mouse.up()
        page.wait_for_timeout(100)
        assert before!=card.locator('canvas').screenshot()
        card.locator('button[data-view="reset"]').click()
        card.locator('input[data-kind="pilot"]').uncheck()
        card.locator('canvas').screenshot(path=str(HERE/'Ansicht_00_ohne_Pilot.png'))
        assert not errors,errors
        b.close()
        (HERE/'Darstellungspruefung.json').write_text(json.dumps({'webgl':checks,'models':7,'rotation_changes_image':True,'pilot_toggle':True,'page_errors':errors},indent=2))
        print('Sieben CAD-Modelle dargestellt und Interaktion geprueft')
finally:server.shutdown()
