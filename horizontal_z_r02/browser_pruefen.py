from pathlib import Path
from functools import partial
from threading import Thread
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
import json,sys,runpy
HERE=Path(__file__).resolve().parent
if '--pdf-only' in sys.argv:
    runpy.run_path(str(HERE/'zeichnungen_pdf.py'));raise SystemExit
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(HERE.parent)))
Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,
            args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=browser.new_page(viewport={'width':1600,'height':1100});errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(f'http://127.0.0.1:{server.server_port}/horizontal_z_r02/Modelle_3D.html',wait_until='load',timeout=180000)
        page.wait_for_timeout(1000)
        assert page.locator('canvas').count()==5
        checks=page.locator('canvas').evaluate_all('(cs)=>cs.map(c=>({width:c.width,height:c.height,error:c.getContext("webgl").getError()}))')
        assert all(c['error']==0 for c in checks),checks
        for i in range(5):page.locator('canvas').nth(i).screenshot(path=str(HERE/f'Ansicht_{i:02}.png'))
        card=page.locator('section.card').first
        before=card.locator('canvas').screenshot();box=card.locator('canvas').bounding_box()
        x=box['x']+200;y=box['y']+200
        page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+60,y+20,steps=5);page.mouse.up()
        page.wait_for_timeout(100)
        assert before!=card.locator('canvas').screenshot()
        card.locator('button[data-view="reset"]').click()
        card.locator('input[data-kind="pilot"]').uncheck()
        card.locator('canvas').screenshot(path=str(HERE/'Ansicht_00_ohne_Pilot.png'))
        hardware_before=card.locator('canvas').screenshot()
        card.locator('input[data-kind="fastener"]').uncheck();page.wait_for_timeout(100)
        assert hardware_before!=card.locator('canvas').screenshot()
        assert not errors,errors
        # Four actual CAD projections to a standalone A3 reference PDF.
        drawings=sorted((HERE/'zeichnungen').glob('*_Projektion.svg'));assert len(drawings)==4
        html='<!doctype html><html><meta charset="utf-8"><style>@page{size:A3 landscape;margin:0}body{margin:0}.sheet{width:420mm;height:297mm;page-break-after:always}.sheet:last-child{page-break-after:auto}svg{display:block;width:100%;height:100%}</style>'
        for f in drawings:html+='<section class="sheet">'+f.read_text()+'</section>'
        (HERE/'zeichnungen/Referenzblaetter.html').write_text(html+'</html>')
        page.goto(f'http://127.0.0.1:{server.server_port}/horizontal_z_r02/zeichnungen/Referenzblaetter.html')
        assert page.locator('svg').count()==4
        page.pdf(path=str(HERE/'Referenzblaetter.pdf'),prefer_css_page_size=True,print_background=True)
        browser.close()
        (HERE/'Darstellungspruefung.json').write_text(json.dumps({'webgl':checks,'models':5,
            'rotation_changes_image':True,'hardware_toggle_changes_image':True,'reference_pdf_pages':4,'page_errors':errors},indent=2))
        print('Fuenf CAD-Ansichten, Drehung, Hardware-Schalter und vier Referenzblaetter geprueft')
finally:server.shutdown()
