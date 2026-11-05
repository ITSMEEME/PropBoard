// Browserpruefung des Flugsimulators ueber das Chrome DevTools Protocol (ohne Zusatzpakete).
// Aufruf: node flugsimulator/pruefen_browser.cjs   (google-chrome erforderlich)
const {spawn} = require('child_process'), fs = require('fs'), path = require('path'), os = require('os');
const H = __dirname, OUT = path.join(H, 'Ergebnisse'), PORT = 9333;
const url = 'file://' + path.join(H, 'Flugsimulator.html');
const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'simpruef-'));
const chrome = spawn('google-chrome', ['--headless=new', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--no-sandbox', `--remote-debugging-port=${PORT}`, `--user-data-dir=${prof}`, '--window-size=1680,1500', 'about:blank'], {stdio: 'ignore'});
const warte = ms => new Promise(r => setTimeout(r, ms));
let ws, id = 0; const offen = new Map(), fehler = [];
function cdp(method, params = {}) { return new Promise((ok, err) => { const i = ++id; offen.set(i, {ok, err}); ws.send(JSON.stringify({id: i, method, params})); }); }
async function js(expr) { const r = await cdp('Runtime.evaluate', {expression: expr, awaitPromise: true, returnByValue: true}); if (r.exceptionDetails) throw Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text); return r.result.value; }
async function bild(name, breite = 1680, hoehe = 1500) { await cdp('Emulation.setDeviceMetricsOverride', {width: breite, height: hoehe, deviceScaleFactor: 1, mobile: breite < 800});
  await warte(1500); const r = await cdp('Page.captureScreenshot', {format: 'png'}); fs.writeFileSync(path.join(OUT, name), Buffer.from(r.data, 'base64')); }
(async () => {
  let list; for (let i = 0; i < 50; i++) { try { list = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json(); break; } catch { await warte(200); } }
  ws = new WebSocket(list.find(t => t.type === 'page').webSocketDebuggerUrl); await new Promise(r => ws.onopen = r);
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && offen.has(m.id)) { const p = offen.get(m.id); offen.delete(m.id); m.error ? p.err(Error(m.error.message)) : p.ok(m.result); }
    if (m.method === 'Runtime.exceptionThrown') fehler.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
    if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') fehler.push(m.params.args.map(a => a.value || a.description).join(' ')); };
  await cdp('Runtime.enable'); await cdp('Page.enable');
  await cdp('Emulation.setDeviceMetricsOverride', {width: 1680, height: 1500, deviceScaleFactor: 1, mobile: false});
  await cdp('Page.navigate', {url: url + '#b=HEXA&p=HEP_S_42_16&v=V2&m=MN1330_KV40'});
  for (let i = 0; i < 100 && !(await js('!!(window.SIM_APP && SIM_APP.sim && SIM_APP.vergleich.length === Object.keys(SIM_DATEN.modelle).length)').catch(() => false)); i++) await warte(300);
  const E = {}, P = (name, ok, wert) => { E[name] = {bestanden: !!ok, wert}; console.log(ok ? 'OK  ' : 'FEHL', name, JSON.stringify(wert)); };
  P('Standardakku nach Laden: LiPo 2P', await js('SIM_APP.sim.akku.P === 2 && SIM_APP.sim.akkuTyp === "LIPO_TATTU22"'), await js('[SIM_APP.sim.akkuTyp, SIM_APP.sim.akku.P]'));
  P('CAD-Netze geladen', await js("document.getElementById('cadPill').textContent === 'D14-CAD-Netze'"), await js("document.getElementById('cadPill').textContent"));
  P('Vergleich aller Konfigurationen (160 inkl. V4)', (await js('SIM_APP.vergleich.length')) === 160, await js('SIM_APP.vergleich.length'));
  const flug = await js('SIM_APP.vergleich.filter(a => !a.gesaettigt).length'); P('Vergleich: flugfähige Konfigurationen ermittelt', flug > 0 && flug < 160, flug);
  // 1) Manoeverprogramm Quad 42 V3 mit Person
  await js("SIM_APP.programmStart('manoever')"); let t = await js('(() => { const t = SIM_APP.vorspulen(20); return {h: t.hoehe, v: Math.hypot(t.v[0], t.v[1]), phase: t.phase, T: t.auftrieb_kg, M: t.masse_kg, P: t.P_kW, z: t.zerstoert}; })()');
  P('Hexa 42″ V2 (MN1330): Manöver im Vorwärtsflug ohne Absturz', !t.z && t.phase === 'FLUG' && t.h > 3 && t.v > 4, t);
  const kpi = await js("[...document.querySelectorAll('#kpis .kpi')].map(k => k.querySelector('span').textContent + '=' + k.querySelector('strong').textContent)");
  P('Dashboard zeigt Gewicht, Auftrieb, Restflugzeit, Strom', ['Gewicht', 'Erzeugter Auftrieb', 'Restflugzeit', 'Stromverbrauch'].every(n => kpi.some(k => k.startsWith(n))), kpi.slice(0, 8));
  await bild('Simulator_Hexa42_Vorwaertsflug.png');
  t = await js('(() => { const t = SIM_APP.vorspulen(50); return {phase: t.phase, z: t.zerstoert, h: t.hoehe, fuss: t.maxLast.fuss, g: t.maxLast.g}; })()');
  P('Hexa 42″ V2: Programm endet mit Landung', t.phase === 'AUS' && !t.z && t.h < 0.1, t);
  // 2) Hexa Motorausfall
  await js("SIM_APP.neuesModell()"); await warte(2500);
  await js("SIM_APP.programmStart('ausfall')"); t = await js('(() => { const t = SIM_APP.vorspulen(30); return {phase: t.phase, z: t.zerstoert, h: t.hoehe, aus: t.motoren.filter(m => m.aus).map(m => m.nr), erkannt: SIM_APP.sim.ereignisse.some(e => /erkannt/.test(e.text))}; })()');
  P('Hexa 42″ V2 (MN1330): Ausfall M1 erkannt und neu verteilt (Ausgang wird protokolliert)', t.erkannt && t.aus.length === 1, t);
  await bild('Simulator_Hexa42_Motorausfall.png');
  // 3) Quad Motorausfall -> Gierachse entfaellt
  await js("document.getElementById('bauweise').value='QUAD'; SIM_APP.neuesModell()"); await warte(2500);
  await js("SIM_APP.programmStart('ausfall')"); t = await js('(() => { const t = SIM_APP.vorspulen(26); const s = SIM_APP.sim; return {z: t.zerstoert, gierRate: s.w[2], ohneGier: s.regler.ohneGier, h: t.hoehe}; })()');
  P('Quad 42″ V2: Ausfall M1 – Gierachse aufgegeben (Drehung)', t.ohneGier === true, t);
  // 4) Koax Wirbelring
  await js("document.getElementById('bauweise').value='KOAX'; SIM_APP.neuesModell()"); await warte(2500);
  await js("SIM_APP.programmStart('vrs')"); t = await js('(() => { let vrs = 0, t; for (let i = 0; i < 40; i++) { t = SIM_APP.vorspulen(1); vrs = Math.max(vrs, ...t.motoren.map(m => m.vrs)); } return {vrsMax: vrs, z: t.zerstoert, h: t.hoehe, w: [...document.querySelectorAll(\"#warnungen li\")].map(l => l.textContent).join(\" | \").slice(0, 200)}; })()');
  P('Koax 42″ V2: Sinkflug 6 m/s löst Wirbelringstadium aus', t.vrsMax > 0.15 && !t.z, t);
  await bild('Simulator_Koax42_Wirbelring.png');
  // 5) zu kleiner Propeller
  await js("document.getElementById('bauweise').value='QUAD'; document.getElementById('propeller').value='HEP_S_26_8p8'; SIM_APP.neuesModell()"); await warte(2500);
  await js("SIM_APP.programmStart('schwebe')"); t = await js('(() => { const t = SIM_APP.vorspulen(12); return {h: t.hoehe, tw: t.tw_max, info: document.getElementById(\"modellInfo\").textContent.slice(0, 160)}; })()');
  P('Quad 26″: hebt nicht ab und wird gekennzeichnet', t.h < 0.05 && t.tw < 1 && t.info.includes('nicht abheben'), t);
  // 6) Okto Ausdauer bis Reserve (Zeitraffer intern)
  await js("document.getElementById('bauweise').value='OKTO'; document.getElementById('propeller').value='HEP_S_42_16'; document.getElementById('variante').value='V3'; SIM_APP.neuesModell()"); await warte(2500);
  const ana = await js("SIM_APP.vergleich.find(a => a.schluessel === 'OKTO_HEP_S_42_16_V3')");
  await js("SIM_APP.programmStart('schwebe')"); t = await js('(() => { let t; for (let i = 0; i < 60; i++) { t = SIM_APP.vorspulen(10); if (t.phase === "AUS" && t.t > 20) break; } return {t: t.t, phase: t.phase, z: t.zerstoert, Wh: t.Wh, soc: t.soc, Tw: Math.max(...t.motoren.map(m => m.Tw))}; })()');
  P('Okto 42″ V3: Schwebeflug bis Reserve, Flugzeit nahe Analyse', !t.z && Math.abs(t.t/60 - ana.flugzeit_min) < 0.25*ana.flugzeit_min + 0.6, {flug_min: t.t/60, analyse_min: ana.flugzeit_min, ...t});
  await bild('Simulator_Okto42_Dashboard.png');
  // 7) Motorwahl: U15 II KV80 macht kleine Propeller flugfaehig, Masse folgt dem Motor
  const vorher = await js('SIM_APP.sim.mm.M');
  await js("document.getElementById('motor').value='U15II_KV80'; document.getElementById('propeller').value='HEP_S_30_10p5'; document.getElementById('variante').value='V2'; SIM_APP.neuesModell()"); await warte(2500);
  await js("SIM_APP.programmStart('manoever')"); t = await js('(() => { const t = SIM_APP.vorspulen(22); return {motor: SIM_APP.sim.motor.typ, M: t.masse_kg, h: t.hoehe, v: Math.hypot(t.v[0], t.v[1]), z: t.zerstoert, pill: document.getElementById("modellPill").textContent}; })()');
  P('Motorwahl U15 II KV80: Okto 30″ V2 fliegt Manöver', t.motor.includes('U15') && !t.z && t.h > 3 && t.v > 4 && t.pill.includes('U15'), {...t, masse_MN1330_okto42v3: vorher});
  await bild('Simulator_Okto30_U15II.png');
  for (let i = 0; i < 100 && !(await js('!!window.SIM_MOTORVERGLEICH && Object.keys(SIM_MOTORVERGLEICH).length === 4')); i++) await warte(500);
  const mv = await js('window.SIM_MOTORVERGLEICH'); P('Motorvergleich für 4 Motoren angezeigt', mv && Object.keys(mv).length === 4 && mv.U15II_KV80.schwebefaehig > mv.MN1330_KV40.schwebefaehig, mv);
  // 8) Akkutypen: Datenblattwerte, Masse und Dauerstromwarnung
  await js("document.getElementById('motor').value='MN1330_KV40'; document.getElementById('bauweise').value='OKTO'; document.getElementById('propeller').value='HEP_S_42_16'; document.getElementById('variante').value='V2'; SIM_APP.neuesModell()"); await warte(2500);
  const akku = {};
  for (const [typ, p] of [['LIPO_TATTU22', 2], ['LIION_P45B', 12], ['SEMI_TATTU33', 2]]) {
    await js(`document.getElementById('akkuTyp').value='${typ}'; document.getElementById('akkuTyp').onchange(); document.getElementById('akkuP').value='${p}'; document.getElementById('akkuP').onchange()`); await warte(800);
    akku[typ] = await js('({masse: SIM_APP.sim.akku.masse, Idauer: SIM_APP.sim.akku.Idauer, info: document.getElementById("akkuInfo").textContent.slice(0, 400), rest: SIM_APP.sim.restSchaetzung})');
  }
  P('Akkutyp-Schalter: drei Typen mit Datenblattmasse', Math.abs(akku.LIPO_TATTU22.masse - 24.232) < 0.01 && Math.abs(akku.LIION_P45B.masse - 23.664) < 0.01 && akku.LIION_P45B.Idauer === 420 && akku.SEMI_TATTU33.Idauer === 198, Object.fromEntries(Object.entries(akku).map(([k, v]) => [k, {masse: +v.masse.toFixed(2), Idauer: v.Idauer, flugzeit_min: +v.rest.toFixed(2)}])));
  P('Semi-Solid 2P: Warnung Dauerbelastbarkeit', akku.SEMI_TATTU33.info.includes('über Dauerbelastbarkeit'), akku.SEMI_TATTU33.info.slice(0, 200));
  await js("SIM_APP.programmStart('schwebe')"); t = await js('(() => { let t; for (let i = 0; i < 8; i++) t = SIM_APP.vorspulen(10); return {w: [...document.querySelectorAll("#warnungen li")].map(l => l.textContent).join(" | "), T: t.akku_T, I30: t.akku_I_mittel}; })()');
  P('Semi-Solid 2P im Flug: Dashboard warnt vor Akkustrom', /Dauerbelastbarkeit/.test(t.w), t);
  await bild('Simulator_Akku_SemiSolid.png');
  await js("document.getElementById('akkuTyp').value='LIPO_TATTU22'; document.getElementById('akkuTyp').onchange()"); await warte(800);
  // 9) Neue Auslegervariante V4 (Raumfachwerk durch Umordnung)
  const v4 = await js("Object.keys(SIM_DATEN.modelle).filter(k => k.endsWith('_V4')).length");
  if (v4) {
    await js("document.getElementById('bauweise').value='QUAD'; document.getElementById('variante').value='V4'; SIM_APP.neuesModell()"); await warte(3000);
    await js("SIM_APP.programmStart('manoever')"); t = await js('(() => { const t = SIM_APP.vorspulen(22); return {cad: document.getElementById("cadPill").textContent, h: t.hoehe, v: Math.hypot(t.v[0], t.v[1]), z: t.zerstoert}; })()');
    P('V4 Quad 42″: CAD geladen und Manöverflug', t.cad === 'D14-CAD-Netze' && !t.z && t.h > 3, {...t, v4_konfigurationen: v4});
    await bild('Simulator_Quad42_V4.png');
  }
  // 10) Mobil
  await cdp('Emulation.setDeviceMetricsOverride', {width: 390, height: 844, deviceScaleFactor: 2, mobile: true}); await warte(1200);
  const sw = await js('[document.documentElement.scrollWidth, window.innerWidth]'); P('Mobil 390 px: kein horizontales Scrollen', sw[0] <= sw[1], sw);
  await bild('Simulator_mobil.png', 390, 844);
  P('Keine Skriptfehler', fehler.length === 0, fehler.slice(0, 5));
  const ok = Object.values(E).every(e => e.bestanden);
  fs.writeFileSync(path.join(OUT, 'Browser_Pruefung.json'), JSON.stringify({bestanden: ok, datum: new Date().toISOString(), pruefungen: E}, null, 1));
  console.log(ok ? 'ALLE BESTANDEN' : 'NICHT BESTANDEN'); chrome.kill(); process.exit(ok ? 0 : 1);
})().catch(e => { console.error(e); chrome.kill(); process.exit(2); });
