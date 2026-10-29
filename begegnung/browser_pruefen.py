from playwright.sync_api import sync_playwright
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
from pathlib import Path
import json
root=Path(__file__).resolve().parent
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(root)))
Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        page=b.new_page(viewport={'width':1200,'height':1000})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(f'http://127.0.0.1:{server.server_port}/results/Flow_Interaktiv.html')
        page.wait_for_function('document.querySelector("#field").complete && document.querySelector("#field").naturalWidth>0')
        assert 'GLEICHE x-POSITION' in page.locator('#time').inner_text()
        first=page.locator('#field').get_attribute('src')
        page.locator('#scalar').select_option('1')
        assert page.locator('#field').get_attribute('src')!=first
        page.locator('#scalar').select_option('2')
        assert 'Druckbeiwert' in page.locator('#scale').inner_text()
        page.locator('#slider').evaluate('(e)=>{e.value=40;e.dispatchEvent(new Event("input"))}')
        assert 'GLEICHE x-POSITION' not in page.locator('#time').inner_text()
        page.locator('#meet').click()
        assert '19.000' in page.locator('#time').inner_text()
        page.locator('#scalar').select_option('0')
        page.locator('#play').click();page.wait_for_timeout(250);page.locator('#play').click()
        page.locator('#meet').click()
        page.screenshot(path=str(root/'results/Flow_Ansicht.png'),full_page=True)
        assert not errors,errors
        b.close()
        (root/'results/Browserpruefung.json').write_text(json.dumps({'page_errors':errors,'scalar_switch':True,'slider':True,'alignment_button':True,'playback':True},indent=2))
        print('Interaktive Strömungsansicht geprüft')
finally:server.shutdown()
