from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent
drawings=sorted((HERE/'zeichnungen').glob('*_Projektion.svg'))
assert len(drawings)==4
html='<!doctype html><html><meta charset="utf-8"><title>PropBoard Referenzblaetter</title><style>@page{size:A3 landscape;margin:0}body{margin:0}.sheet{width:420mm;height:297mm;page-break-after:always}.sheet:last-child{page-break-after:auto}svg{display:block;width:100%;height:100%}</style>'
for p in drawings:html+='<section class="sheet">'+p.read_text()+'</section>'
html+='</html>'
(HERE/'zeichnungen/Referenzblaetter.html').write_text(html)
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(HERE)))
Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        page=b.new_page()
        page.goto(f'http://127.0.0.1:{server.server_port}/zeichnungen/Referenzblaetter.html')
        assert page.locator('svg').count()==4
        page.pdf(path=str(HERE/'Referenzblaetter.pdf'),prefer_css_page_size=True,print_background=True)
        b.close()
finally:server.shutdown()
print('Vier Referenzblaetter als PDF erstellt')
