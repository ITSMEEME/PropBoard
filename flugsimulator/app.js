/* Globaler Flugsimulator: Modellwahl, CAD-Laden, Simulationsschleife, Partikel, Testprogramme, Vergleich aller Modelle */
(function(){
'use strict';
const $ = id => document.getElementById(id), D = globalThis.SIM_DATEN, P = globalThis.SimPhysik, {fmt: f, mmss} = globalThis.SimDashboard;
const VIEWER = '../multirotor_d14/Ausgabe/viewer/';
const fehler = t => { $('fehler').hidden = false; $('fehler').textContent = t; };
if (!D || !P) { fehler('Daten oder Physikmodul fehlen (modelle.js / physik.js).'); return; }

// ------------------------------------------------------------------ Auswahl
const modelle = Object.values(D.modelle), uniq = (k, l) => [...new Map(modelle.map(m => [m[k], m[l]])).entries()];
const opt = (el, items, sel) => { $(el).innerHTML = items.map(([v, t]) => `<option value="${v}" ${v === sel ? 'selected' : ''}>${t}</option>`).join(''); };
const hash = Object.fromEntries(location.hash.slice(1).split('&').filter(Boolean).map(x => x.split('=')));
opt('bauweise', uniq('bauweise', 'bauweise_label'), hash.b || D.standard.bauweise);
opt('propeller', uniq('propeller', 'propeller_label'), hash.p || D.standard.propeller);
opt('variante', uniq('variante', 'variante_label').map(([k, t]) => [k, `${k} · ${t}`]), hash.v || D.standard.variante);
const schluessel = () => `${$('bauweise').value}_${$('propeller').value}_${$('variante').value}`;

// ------------------------------------------------------------------ CAD-Netze per <script> (funktioniert auch ueber file://)
const cad = {daten: {}, ecken: {}, prop: {}, d12: null};
globalThis.D14_DATEN = d => { cad.daten[d.schluessel] = d; };
globalThis.D14_ECKE = d => { cad.ecken[d.bauweise] = d; };
globalThis.D14_PROPELLER = d => { cad.prop[d.id] = d; };
globalThis.D14_D12 = d => { cad.d12 = d; };
globalThis.D14_INDEX = () => {};
const lade = src => new Promise((ok, err) => { const s = document.createElement('script'); s.src = src; s.onload = ok; s.onerror = () => err(Error(src)); document.body.appendChild(s); });

// ------------------------------------------------------------------ Zustand
let sim = null, ansicht = null, laeuft = false, pausiert = false, letzte = performance.now(), winkel = [], tDash = 0, tChart = 0, tLog = 0, log = [], programm = null, md = null;
const dash = new globalThis.SimDashboard.Dashboard();
try { ansicht = new globalThis.SimAnsicht.Ansicht($('view')); } catch (e) { fehler('3D-Ansicht nicht verfügbar: ' + e.message + '. Die Simulation läuft trotzdem.'); }
const eingabe = new globalThis.SimEingabe.Input({onAction: aktion, onBlur: () => { if (laeuft) setPause(true, 'Pausiert nach Fokusverlust. Leertaste setzt fort.'); }});

function optionen() {
  return {nutzlast: +$('nutzlast').value, akku_P: +$('akkuP').value, akku_Ah: +$('akkuAh').value, temp_C: +$('temp').value, hoehe_m: +$('hoehe').value,
    wind: +$('wind').value, windrichtung: (+$('windrichtung').value + 180) % 360, turbulenz: +$('turbulenz').value, boeen: +$('boeen').value, streuung: $('streuung').checked ? 1 : 0, seed: 7};
}
function beschriften() {
  $('nutzlastOut').textContent = `${$('nutzlast').value} kg`; $('windOut').textContent = `${f(+$('wind').value, 1)} m/s`;
  $('windrichtungOut').textContent = `${$('windrichtung').value}°`; $('turbulenzOut').textContent = `${f(+$('turbulenz').value, 1)}×`;
  $('boeenOut').textContent = `${f(+$('boeen').value, 1)} m/s`; $('tempOut').textContent = `${$('temp').value} °C`; $('hoeheOut').textContent = `${$('hoehe').value} m`;
}

async function neuesModell() {
  const k = schluessel(); md = D.modelle[k];
  if (!md) { fehler('Konfiguration fehlt: ' + k); return; }
  history.replaceState(null, '', `#b=${md.bauweise}&p=${md.propeller}&v=${md.variante}`);
  $('cadPill').textContent = 'CAD wird geladen …';
  try {
    if (!cad.daten[k]) await lade(VIEWER + k + '.js');
    if (!cad.ecken[md.bauweise]) await lade(VIEWER + `Eckknoten_${md.bauweise}.js`);
    if (!cad.prop[md.propeller]) await lade(VIEWER + `Propeller_${md.propeller}.js`).catch(() => {});
    if (!cad.d12) await lade(VIEWER + 'Fussschlitten_D12.js').catch(() => {});
  } catch (e) { /* Ersatzdarstellung */ }
  zuruecksetzen();
  markiereVergleich();
}

function ansichtInfo() {
  const d = cad.daten[md.schluessel], nm = md.arme.length;
  const delta = d ? Math.atan2(d.I[1], d.I[0])*180/Math.PI : 45;
  const winkelDiff = (a, b) => Math.abs(((a - b) % 360 + 540) % 360 - 180);
  const info = {
    armVonPaar: (j, side) => { const ziel = d.paarwinkel[j] + (side ? -delta : delta); let best = 0, bd = 1e9; d.motoren.forEach(m => { const w = winkelDiff(m.winkel_grad, ziel); if (w < bd) { bd = w; best = m.nr; } }); return md.arme.findIndex(a => a.nr === best); },
    rotorVon: (j, unten) => { const nr = d.motoren[j].nr + (unten ? nm : 0); return md.rotoren.findIndex(r => r.nr === nr); },
    person: $('zeigePerson').checked && sim.opt.nutzlast > 0 ? {z: md.plattform_z_m*1000, fx: md.fuss_x_m*1000, groesse: 1.75} : null,
    ersatz: [], ersatzProps: [],
  };
  if (!d) {
    md.arme.forEach((a, k) => { info.ersatz.push({typ: 'rohr', a: [0, 0, 0], b: [a.xy[0]*1000, a.xy[1]*1000, 50], od: 30, id: 26, arm: k}); });
    md.rotoren.forEach((r, i) => { const z = r.z*1000; info.ersatz.push({typ: 'zyl', r: 75, h: 66, p: [r.xy[0]*1000, r.xy[1]*1000, r.lage === 'oben' ? z - 80 : z + 14], farbe: 'motor', arm: r.arm});
      info.ersatzProps.push({xy: [r.xy[0]*1000, r.xy[1]*1000], winkel: 0, rotor: i, r: md.d_m*500, z}); });
    info.ersatz.push({typ: 'zyl', r: md.rahmen.umkreis_m*1000, h: 220, p: [0, 0, -110], farbe: 'alu'});
  }
  return info;
}

function zuruecksetzen() {
  programm = null; $('programmInfo').textContent = 'Programme laufen mit dem aktuellen Modell und der aktuellen Umgebung.';
  try { sim = new P.Sim(D, md.schluessel, optionen()); } catch (e) { fehler(e.message); return; }
  sim.regler.modus = $('modus').value;
  try { sim.restSchaetzung = P.Sim.schwebeAnalyse(D, md.schluessel, optionen()).flugzeit_min; } catch (e) { sim.restSchaetzung = 0; }
  winkel = sim.rotoren.map(() => Math.random()*6.28); log = []; dash.reset(); partikelReset();
  if (ansicht) { const d = cad.daten[md.schluessel]; ansicht.ladeModell(d, d ? cad.ecken[md.bauweise] : null, d ? cad.prop[md.propeller] : null, cad.d12, ansichtInfo()); ansicht.kam.glatt = null; }
  $('cadPill').textContent = ansicht && ansicht.cadGeladen ? 'D14-CAD-Netze' : 'Ersatzdarstellung (CAD-Netze nicht gefunden)';
  $('modellPill').textContent = `${md.bauweise_label.replace('Multirotor ', '')} · ${md.propeller_label} · ${md.variante}`;
  opt('ausfallMotor', sim.rotoren.map((r, i) => [i, `M${r.nr}${r.lage === 'unten' ? ' (unten)' : ''} ${r.s > 0 ? 'CCW' : 'CW'}`]), '0');
  const a = sim.akku; $('akkuInfo').textContent = `${a.S}S${a.P}P ${a.Ah} Ah: ${f(a.S*a.P*a.Ah*3.7/1000, 2)} kWh, ${f(a.masse, 1)} kg (${a.Whkg} Wh/kg), Reserve ${f(a.reserve*100, 0)} %`;
  const offen = Object.entries(md.pruefungen).filter(([k, v]) => v === false && !['systemlinien_zentrisch'].includes(k)).map(([k]) => k.replace(/_/g, ' ').replace(/ ok$/, ''));
  const tw = sim.Tmax.reduce((x, y) => x + y, 0)/(sim.mm.M*P.G);
  const hinweise = []; if (tw < 1) hinweise.push(`Mit MN1330 KV40 bei ${f(a.leerlauf(), 0)} V erreicht dieser Propeller höchstens ${f(sim.Tmax.reduce((x, y) => x + y, 0)/P.G, 0)} kg Schub bei ${f(sim.mm.M, 0)} kg Gewicht – das Modell kann nicht abheben.`);
  if (offen.length) hinweise.push('Offene D14-Prüfungen: ' + offen.join(', ') + '.');
  $('modellInfo').hidden = !hinweise.length; $('modellInfo').textContent = hinweise.join(' ');
  laeuft = true; setPause(false); $('meldung').hidden = true; status();
}

function setPause(p, text) { pausiert = p; $('pause').textContent = p ? 'Fortsetzen / Leertaste' : 'Pause / Leertaste'; if (text) $('phase').textContent = text; eingabe.clear(); }
function aktion(a) {
  if (!sim) return;
  if (a === 'start') { if (sim.zerstoert) return; sim.regler.start(); setPause(false); }
  if (a === 'land') sim.regler.landen();
  if (a === 'stop') sim.regler.aus();
  if (a === 'pause') setPause(!pausiert);
  if (a === 'reset') zuruecksetzen();
  if (a === 'mode') { $('modus').value = $('modus').value === 'POSITION' ? 'WINKEL' : 'POSITION'; sim.regler.modus = $('modus').value; }
  if (a === 'camera') { const s = $('kamera'); s.selectedIndex = (s.selectedIndex + 1) % s.options.length; if (ansicht) ansicht.kam.modus = s.value; }
}
$('start').onclick = () => aktion('start'); $('land').onclick = () => aktion('land'); $('pause').onclick = () => aktion('pause'); $('reset').onclick = () => aktion('reset'); $('motorenAus').onclick = () => aktion('stop');
$('ausfall').onclick = () => sim && sim.motorAusfall(+$('ausfallMotor').value);
$('modus').onchange = () => { if (sim) sim.regler.modus = $('modus').value; };
$('kamera').onchange = () => { if (ansicht) ansicht.kam.modus = $('kamera').value; };
['bauweise', 'propeller', 'variante'].forEach(i => $(i).onchange = neuesModell);
['nutzlast', 'akkuP', 'akkuAh', 'temp', 'hoehe', 'streuung'].forEach(i => $(i).onchange = () => { beschriften(); zuruecksetzen(); vergleichPlanen(); });
['wind', 'windrichtung', 'turbulenz', 'boeen'].forEach(i => $(i).oninput = () => { beschriften(); if (sim) sim.wind.set({mittel: +$('wind').value, richtung: (+$('windrichtung').value + 180) % 360, turbulenz: +$('turbulenz').value, boeen: +$('boeen').value}); });
['nutzlast', 'temp', 'hoehe'].forEach(i => $(i).oninput = beschriften);
$('zeigePerson').onchange = () => zuruecksetzen();

// ------------------------------------------------------------------ Partikel: Abwind jedes Rotors + Umgebungswind
const NP = 2400, pp = new Float32Array(NP*3), pv = new Float32Array(NP*3), pl = new Float32Array(NP), pk = new Uint8Array(NP);
const linie = new Float32Array(NP*6), farbe = new Float32Array(NP*8);
let pNext = 0;
function partikelReset() { pl.fill(0); }
function spawn(x, v, art, leben) { const i = pNext; pNext = (pNext + 1) % NP; pp.set(x, i*3); pv.set(v, i*3); pl[i] = leben; pk[i] = art; }
function partikel(dt) {
  if (!sim || !$('zeigePartikel').checked) return {n: 0};
  const q = sim.q, n = P.qrot(q, [0, 0, 1]), w = sim.wind.aktuell, rng = Math.random;
  // Abwind
  sim.rotoren.forEach((ro, i) => {
    const vi = ro.aus.vi; if (!(vi > 1)) return;
    const c = sim.rpos[i], cw = sim.x.map((x, k) => x + P.qrot(q, c)[k]), anz = Math.min(6, vi*dt*45*ro.R);
    for (let k = 0; k < anz; k++) { const a = rng()*6.283, r = ro.R*Math.sqrt(rng())*0.95, off = P.qrot(q, [r*Math.cos(a), r*Math.sin(a), 0.02]);
      spawn([cw[0] + off[0], cw[1] + off[1], cw[2] + off[2]], [-n[0]*vi + w[0], -n[1]*vi + w[1], -n[2]*vi + w[2]], 0, 2.2); }
  });
  // Umgebungswind um das Fahrzeug
  const wl = Math.hypot(w[0], w[1]);
  if (wl > 0.3) for (let k = 0; k < Math.min(8, wl*dt*60); k++) { const c = sim.x; spawn([c[0] - w[0]/wl*12 + (rng()-0.5)*24, c[1] - w[1]/wl*12 + (rng()-0.5)*24, Math.max(0.2, c[2] + (rng()-0.5)*10)], [w[0], w[1], w[2]], 1, 5); }
  let m = 0; const vis = sim.rotoren.map(r => r.aus.vi);
  for (let i = 0; i < NP; i++) {
    if (pl[i] <= 0) continue; pl[i] -= dt;
    const o = i*3; let x = pp[o], y = pp[o+1], z = pp[o+2];
    if (pk[i] === 0) { // Strahl beschleunigt (bis 2 v_i), am Boden radiale Ausbreitung
      const vz = pv[o+2], vmax = -2*Math.max(...vis);
      pv[o+2] += (Math.max(vmax, vz*1.0) - vz)*Math.min(1, dt*1.2);
      if (z < 0.25) { const dx = x - sim.x[0], dy = y - sim.x[1], d = Math.hypot(dx, dy) || 1, sp = Math.abs(pv[o+2])*0.7; pv[o] = dx/d*sp + w[0]; pv[o+1] = dy/d*sp + w[1]; pv[o+2] = 0.3; }
      pv[o] += (w[0] - pv[o])*dt*0.15; pv[o+1] += (w[1] - pv[o+1])*dt*0.15;
    } else { pv[o] = w[0]; pv[o+1] = w[1]; pv[o+2] = w[2]; }
    x += pv[o]*dt; y += pv[o+1]*dt; z = Math.max(0.03, z + pv[o+2]*dt); pp[o] = x; pp[o+1] = y; pp[o+2] = z;
    const L = pk[i] === 0 ? 0.035 : 0.12, sp = Math.hypot(pv[o], pv[o+1], pv[o+2]);
    linie.set([x*1000, y*1000, z*1000, (x - pv[o]*L)*1000, (y - pv[o+1]*L)*1000, (z - pv[o+2]*L)*1000], m*6);
    const a = Math.min(1, pl[i]/0.8)*(pk[i] === 0 ? 0.75 : 0.45), k = Math.min(1, sp/25);
    const c = pk[i] === 0 ? [0.95 - 0.5*k, 0.97 - 0.35*k, 1, a] : [1, 1, 1, a];
    farbe.set(c, m*8); farbe.set(c, m*8 + 4); m++;
  }
  return {pos: linie.subarray(0, m*6), farbe: farbe.subarray(0, m*8), n: m};
}

// ------------------------------------------------------------------ Testprogramme
const PROGRAMME = {
  schwebe: {name: 'Schwebeflug bis Akkureserve', zeitraffer: 8, schritte: [[0, s => s.regler.start()], [6, s => s.regler.setStick({hoch: 0.6})], [9, s => s.regler.setStick({hoch: 0})]],
    ende: (s, t) => { if (t.rest_Wh <= 1 && s.regler.phase === 'FLUG') { s.regler.landen(); return 'Reserve erreicht – Landung'; } } },
  manoever: {name: 'Manöver', zeitraffer: 1, schritte: [[0, s => s.regler.start()], [6, s => s.regler.setStick({hoch: 1})], [10, s => s.regler.setStick({hoch: 0})], [14, s => s.regler.setStick({vor: 1})], [24, s => s.regler.setStick({vor: 0})], [32, s => s.regler.setStick({gier: 1, rechts: 0.6})], [40, s => s.regler.setStick({gier: 0, rechts: 0})], [46, s => s.regler.landen()]]},
  boe: {name: 'Böentest', zeitraffer: 1, vorher: () => { $('wind').value = 8; $('boeen').value = 6; $('turbulenz').value = 1.5; $('wind').oninput(); }, schritte: [[0, s => s.regler.start()], [6, s => s.regler.setStick({hoch: 1})], [9, s => s.regler.setStick({hoch: 0})], [70, s => s.regler.landen()]]},
  vrs: {name: 'Wirbelringtest', zeitraffer: 1, schritte: [[0, s => s.regler.start()], [5, s => { s.regler.vzZwang = 3; }], [25, s => { s.regler.vzZwang = null; }], [30, s => { s.regler.vzZwang = -6; }], [38, s => { s.regler.vzZwang = null; }], [48, s => s.regler.landen()]]},
  ausfall: {name: 'Motorausfall', zeitraffer: 1, schritte: [[0, s => s.regler.start()], [5, s => s.regler.setStick({hoch: 1})], [9, s => s.regler.setStick({hoch: 0})], [16, s => s.motorAusfall(0)], [36, s => s.regler.landen()]]},
  vollgas: {name: 'Vollgas-Steigflug', zeitraffer: 1, schritte: [[0, s => s.regler.start()], [5, s => { s.regler.vzZwang = 12; }], [17, s => { s.regler.vzZwang = null; }], [24, s => s.regler.landen()]]},
};
$('programmStart').onclick = () => {
  const p = PROGRAMME[$('programm').value]; if (p.vorher) p.vorher(); zuruecksetzen();
  programm = {p, i: 0, t0: sim.t}; $('zeitraffer').value = p.zeitraffer; $('programmInfo').textContent = `Läuft: ${p.name}`;
};
function programmSchritt(t) {
  if (!programm) return; const pr = programm.p, dt = sim.t - programm.t0;
  while (programm.i < pr.schritte.length && pr.schritte[programm.i][0] <= dt) { pr.schritte[programm.i][1](sim); programm.i++; }
  if (pr.ende) { const r = pr.ende(sim, t); if (r) { $('programmInfo').textContent = `${pr.name}: ${r} nach ${mmss(sim.t)} min`; programm.ende = true; } }
  if (sim.regler.phase === 'AUS' && dt > 3 && programm.i >= pr.schritte.length || sim.zerstoert) {
    $('programmInfo').textContent = `${pr.name} beendet nach ${mmss(sim.t)} min · ${f(t.Wh, 0)} Wh · max. ${f(t.maxLast.g, 2)} g · Ausleger max. ${f(t.maxLast.arm*100, 0)} %` + (sim.zerstoert ? ` · ${sim.zerstoert}` : '');
    programm = null; $('zeitraffer').value = 1;
  }
}

// ------------------------------------------------------------------ Hauptschleife
function status() {
  const t = sim.telemetrie(), ph = {AUS: 'Bereit', HOCHLAUF: 'Hochlauf', START: 'Abheben', FLUG: 'Freiflug', LANDUNG: 'Landung', ABSTURZ: 'Versuch beendet'}[t.phase] || t.phase;
  $('phase').textContent = pausiert ? 'Pausiert' : ph + (t.phase === 'FLUG' ? ` · ${t.modus === 'POSITION' ? 'Position halten' : 'Winkel + Höhe'}` : '');
  $('phase').className = 'pill' + (sim.zerstoert ? ' kritisch' : t.phase === 'FLUG' ? ' ok' : '');
  $('hHoehe').textContent = f(t.hoehe, 1); $('hV').textContent = f(Math.hypot(t.v[0], t.v[1]), 1); $('hVz').textContent = f(t.v[2], 1);
  $('hKurs').textContent = f(((t.gier*180/Math.PI) % 360 + 360) % 360, 0); $('hZeit').textContent = f(t.t, 1);
  const wl = Math.hypot(t.wind[0], t.wind[1]); $('windHinweis').textContent = `Wind ${f(wl, 1)} m/s aus ${f(((Math.atan2(-t.wind[1], -t.wind[0])*180/Math.PI) + 360) % 360, 0)}°`;
  if (sim.zerstoert) { $('meldung').hidden = false; $('meldung').textContent = `${sim.zerstoert}. Zurücksetzen mit ⌫.`; }
  return t;
}
function horizont(t) {
  const c = $('horizont'), g = c.getContext('2d'), W = c.width, H = c.height, r = W/2;
  g.save(); g.clearRect(0, 0, W, H); g.beginPath(); g.arc(r, r, r - 1, 0, 7); g.clip();
  g.translate(r, r); g.rotate(-t.roll); const py = t.nick*180/Math.PI*2.2;
  g.fillStyle = '#3d7ab0'; g.fillRect(-W, -2*H + py, 2*W, 2*H); g.fillStyle = '#7a5a36'; g.fillRect(-W, py, 2*W, 2*H);
  g.strokeStyle = '#fff'; g.lineWidth = 1.5; g.beginPath(); g.moveTo(-W, py); g.lineTo(W, py); g.stroke();
  g.font = '9px system-ui'; g.fillStyle = '#fff';
  for (const d of [-20, -10, 10, 20]) { const y = py - d*2.2; g.beginPath(); g.moveTo(-14, y); g.lineTo(14, y); g.stroke(); g.fillText(String(Math.abs(d)), 17, y + 3); }
  g.restore(); g.strokeStyle = '#ffd696'; g.lineWidth = 3; g.beginPath(); g.moveTo(r - 30, r); g.lineTo(r - 10, r); g.lineTo(r, r + 6); g.lineTo(r + 10, r); g.lineTo(r + 30, r); g.stroke();
}
function schleife(jetzt) {
  const real = Math.min(0.05, (jetzt - letzte)/1000); letzte = jetzt;
  if (sim && laeuft) {
    const st = eingabe.sample(); $('gamepad').textContent = eingabe.padLabel;
    if (!programm) sim.regler.setStick({vor: st.forward, rechts: st.right, gier: st.yaw, hoch: st.climb});
    if (!pausiert) {
      const zr = +$('zeitraffer').value, soll = real*zr, n = Math.round(soll/0.001), t0 = performance.now(); let k = 0;
      for (; k < n; k++) { sim.schritt(0.001); if ((k & 63) === 0 && performance.now() - t0 > 30) break; }
      const simdt = k*0.001;
      $('zeitPill').textContent = k < n ? `Zeitraffer begrenzt: ${f(simdt/real, 1)}× (Rechenleistung)` : `${f(zr, zr < 1 ? 2 : 0)}× Echtzeit · 1 kHz`;
      sim.rotoren.forEach((r, i) => { winkel[i] += r.s*sim.antriebe[i].Om*Math.min(simdt, 0.02) * (sim.antriebe[i].Om > 50 ? 0.12 : 1); });
      const pt = partikel(Math.min(simdt, 0.05));
      tDash += real; tChart += simdt; tLog += simdt;
      const t = status(); programmSchritt(t);
      if (tChart > 0.2) { tChart = 0; dash.aufzeichnen(t); dash.zeichneDiagramme(); }
      if (tLog > 0.1) { tLog = 0; log.push(t); if (log.length > 40000) log.shift(); }
      if (tDash > 0.12) { tDash = 0; dash.aktualisiere(t, sim); horizont(t); }
      zeichne(pt);
    } else zeichne(null);
  }
  requestAnimationFrame(schleife);
}
function zeichne(pt) {
  if (!ansicht || !sim) return;
  ansicht.zeichne({x: sim.x, q: sim.q, cg: sim.mm.cg, om: sim.antriebe.map(a => a.Om), winkel, aus: sim.antriebe.map(a => a.ausgefallen), armBruch: sim.armBruch,
    partikel: pt || ansicht._pt, person: $('zeigePerson').checked && sim.opt.nutzlast > 0, gierWelt: P.euler(sim.q).yaw});
  if (pt) ansicht._pt = pt;
}

// ------------------------------------------------------------------ Fluglog
$('export').onclick = () => {
  if (!log.length) return;
  const kopf = ['t_s', 'hoehe_m', 'vx', 'vy', 'vz', 'roll_grad', 'nick_grad', 'gier_grad', 'masse_kg', 'auftrieb_kg', 'U_V', 'I_A', 'P_kW', 'soc', 'zelle_min_V', 'akku_T', 'rest_Wh', 'wind_x', 'wind_y', 'wind_z', 'nz_g', 'arm_max_u',
    ...log[0].motoren.flatMap(m => [`M${m.nr}_rpm`, `M${m.nr}_schub_kg`, `M${m.nr}_I_A`, `M${m.nr}_Tw`])];
  const z = log.map(t => [t.t, t.hoehe, ...t.v, t.roll*57.3, t.nick*57.3, t.gier*57.3, t.masse_kg, t.auftrieb_kg, t.U, t.I, t.P_kW, t.soc, t.zelle_min, t.akku_T, t.rest_Wh, ...t.wind, t.nz, Math.max(...t.arme.map(a => a.u)),
    ...t.motoren.flatMap(m => [m.rpm, m.T_kg, m.I, m.Tw])].map(v => typeof v === 'number' ? v.toFixed(4) : v).join(';'));
  const b = new Blob([`# ${md.schluessel}; ${JSON.stringify(sim.opt)}\n` + kopf.join(';') + '\n' + z.join('\n')], {type: 'text/csv'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = `Fluglog_${md.schluessel}.csv`; a.click(); URL.revokeObjectURL(a.href);
};

// ------------------------------------------------------------------ Vergleich aller Modelle
let vergleich = [], sortKey = 'flugzeit_min', sortAuf = false, vTimer = null;
const SPALTEN = [['bauweise', 'Bauweise'], ['prop', 'Propeller'], ['variante', 'Ausleger'], ['masse_kg', 'Masse kg', 1], ['schub_max_kg', 'Max. Schub kg', 0], ['tw_max', 'Schub/Gew.', 2], ['rpm', 'Schwebe-U/min', 0],
  ['P_kW', 'Leistung kW', 1], ['I_bus_A', 'Akkustrom A', 0], ['I_phase_max_A', 'Phasenstrom A', 0], ['flugzeit_min', 'Flugzeit min', 1], ['arm_lastfaktor_grenze', 'Arm-Grenze g', 2], ['mach_spitze', 'Mach', 2], ['status', 'Status']];
function vergleichPlanen() { clearTimeout(vTimer); vTimer = setTimeout(vergleichRechnen, 300); }
function vergleichRechnen() {
  const keys = Object.keys(D.modelle), o = optionen(); vergleich = []; let i = 0; $('vergleichStart').disabled = true;
  const chunk = () => { const t0 = performance.now();
    while (i < keys.length && performance.now() - t0 < 25) { const m = D.modelle[keys[i]]; try { const a = P.Sim.schwebeAnalyse(D, keys[i], o);
      a.bauweise = m.bauweise_label.replace('Multirotor ', ''); a.prop = m.propeller_label; a.d = m.d_m; a.variante = m.variante;
      a.status = a.gesaettigt ? 'kann nicht schweben' : a.arm_lastfaktor_grenze < 1.5 ? 'Ausleger knapp' : a.tw_max < 1.4 ? 'Reserve knapp' : a.mach_spitze > 0.6 ? 'Mach hoch' : 'flugfähig';
      a.stufe = a.gesaettigt ? 'kritisch' : a.status === 'flugfähig' ? 'gut' : 'ernst'; vergleich.push(a); } catch (e) { } i++; }
    $('vergleich').innerHTML = `<p class="note">Berechnet ${i} / ${keys.length} …</p>`;
    if (i < keys.length) setTimeout(chunk, 0); else { $('vergleichStart').disabled = false; vergleichZeigen(); } };
  chunk();
}
function vergleichZeigen() {
  const nur = $('nurFlugfaehig').checked, rows = vergleich.filter(a => !nur || !a.gesaettigt).sort((a, b) => {
    const x = a[sortKey], y = b[sortKey]; const r = typeof x === 'string' ? x.localeCompare(y) : (x - y) || (a.d - b.d); return sortAuf ? r : -r; });
  const ICON = {gut: '●', ernst: '▲', kritisch: '■'};
  $('vergleich').innerHTML = '<table><tr>' + SPALTEN.map(([k, t]) => `<th data-k="${k}">${t}${k === sortKey ? (sortAuf ? ' ▲' : ' ▼') : ''}</th>`).join('') + '</tr>' +
    rows.map(a => `<tr data-s="${a.schluessel}" class="${md && a.schluessel === md.schluessel ? 'aktiv' : ''}">` + SPALTEN.map(([k, , d]) => {
      if (k === 'status') return `<td class="st-${a.stufe}">${ICON[a.stufe]} ${a.status}</td>`;
      if (k === 'flugzeit_min' && a.gesaettigt) return '<td>–</td>';
      return `<td>${d === undefined ? a[k] : f(a[k], d)}</td>`; }).join('') + '</tr>').join('') + '</table>';
  $('vergleich').querySelectorAll('th').forEach(th => th.onclick = () => { const k = th.dataset.k; if (k === sortKey) sortAuf = !sortAuf; else { sortKey = k; sortAuf = typeof vergleich[0][k] === 'string'; } vergleichZeigen(); });
  $('vergleich').querySelectorAll('tr[data-s]').forEach(tr => tr.onclick = () => { const m = D.modelle[tr.dataset.s]; $('bauweise').value = m.bauweise; $('propeller').value = m.propeller; $('variante').value = m.variante; neuesModell(); $('view').scrollIntoView({behavior: 'smooth', block: 'center'}); });
}
function markiereVergleich() { if (vergleich.length) vergleichZeigen(); }
$('vergleichStart').onclick = vergleichRechnen; $('nurFlugfaehig').onchange = vergleichZeigen;

// ------------------------------------------------------------------ Modellbeschreibung
const mo = D.motor;
$('modellText').innerHTML = [
  `<b>Starrkörper.</b> 6 Freiheitsgrade, Quaternionen, 1 kHz. Masse und Trägheitstensor aus den D14-CAD-Massen (Struktur, Ausrüstung, Regler), ${f(mo.masse_kg, 2)} kg je Motor, Propeller (Annahme 0,56 kg bei 42″), Akku (165 Wh/kg), 2 kg Bordnetz und der Person als Zylinder auf der Fußplattform. Kreiselmomente der Rotoren sind enthalten.`,
  `<b>Rotor.</b> Blattelement-Impuls-Modell je Rotor mit gemeinsamer Lösung von Schub und Zustrom: Steig-/Sinkflug, Vorwärtsflug (Translationsauftrieb, Blattschlag-Neigung, H-Kraft, Nick- und Rollmomente), Wirbelringstadium (empirische Zustromkurve, Schubschwankung), Windmühlenzustand, Strömungsabriss ab C<sub>L</sub> 1,25, Bodeneffekt (Cheeseman–Bennett), Abschattung durch Ausleger und Regler. Statische Beiwerte wie D13: NS52×20-Tabelle mit Steigungsskalierung, kein HEP-S-Kennfeld.`,
  `<b>Prop wash.</b> Koaxial: der untere Rotor arbeitet im Nachlauf des oberen; der Nachlauf wandert im Vorwärtsflug ab. Hintere Rotoren nehmen bei Wind oder Vorwärtsflug den Nachlauf der vorderen auf. Der Abwind kühlt die Motoren. Die Partikel zeigen Abwind und Bodenausbreitung.`,
  `<b>Antrieb.</b> MN1330 KV40 mit k<sub>t</sub> = ${f(mo.kt_fit, 3)} Nm/A, R = ${f(mo.r_phase_fit*1000, 1)} mΩ und I<sub>0</sub> = ${f(mo.i0_fit, 1)} A, angepasst an die 19 Prüfstandspunkte (RMS-Abweichung ${f(mo.fit_rms_anteil*100, 1)} %). Drehzahlregelung im Regler, Aussteuerungs- und Stromgrenze (${D.regler.spitze_A} A), aktives Bremsen bis 40 A. Thermik von Wicklung, Gehäuse und Regler mit Leistungsreduzierung ab 150 °C bzw. 100 °C.`,
  `<b>Akku.</b> 24 Einzelzellen in Reihe mit Leerlaufkennlinie, Innenwiderstand (temperaturabhängig), RC-Polarisation (τ 25 s), Erwärmung, Streuung von Kapazität, Widerstand und Ladezustand sowie Messrauschen. Die schwächste Zelle begrenzt die Restenergie. Unterspannung: Warnung, nach 0,5 s Leistungsbegrenzung, nach 2 s unter 3,0 V Abschaltung.`,
  `<b>Wind.</b> Logarithmisches Höhenprofil, Dryden-Turbulenz nach MIL-F-8785C (Niedrighöhe), räumlicher Vertikalgradient (erzeugt Roll- und Nickstörungen) und zufällige 1-cos-Böen. Luftdichte aus Temperatur und Standorthöhe (ISA).`,
  `<b>Lastgrenzen.</b> Zulässiger Schub je Ausleger aus dem D14-Screening (Lastfall ÷ höchste Ausnutzung bei 3 g); Überschreiten bricht den Ausleger. Landestoß gegen die Fußauslegung, Bodenberührung der Propeller, Umkippen am Boden (Feder-Dämpfer-Kontakt an allen Sohlen) und Aufschlag beenden den Versuch.`,
  `<b>Flugregler.</b> Kaskade aus Position, Geschwindigkeit (ruckbegrenzt), Lage (Wurzelregler mit verfügbarer Winkelbeschleunigung) und Drehrate, Steuerzuordnung als Pseudoinverse mit Vorrang Roll/Nick vor Schub vor Gier. Ein Motorausfall wird nach 150 ms erkannt und neu verteilt; beim Quad entfällt die Gierachse.`,
  `<b>Nicht enthalten.</b> Blattelastizität, Strukturschwingung, ESC-Kommutierung, Sensorschätzung (die Lage ist ideal bekannt), Bewegung der Person, CFD-Strömungsfeld. Ergebnisse sind Entwicklungsmodelle und ersetzen keine Messung.`,
].map(t => `<p>${t}</p>`).join('');

if (hash.kam && ansicht) { $('kamera').value = hash.kam; ansicht.kam.modus = hash.kam; }
beschriften(); neuesModell().then(() => { vergleichPlanen(); if (hash.auto && PROGRAMME[hash.auto]) { $('programm').value = hash.auto; $('programmStart').onclick(); } }); requestAnimationFrame(schleife);
// Pruefschnittstelle: Simulation ohne Darstellung vorspulen (gleiche Schritte wie die Hauptschleife)
function vorspulen(sek) {
  const n = Math.round(sek/0.001); let t = null;
  for (let k = 0; k < n; k++) { sim.schritt(0.001); if (k % 50 === 0) { t = sim.telemetrie(); programmSchritt(t); if (k % 200 === 0) { dash.aufzeichnen(t); log.push(t); } } }
  if (ansicht) ansicht.kam.glatt = null; t = status(); dash.aktualisiere(t, sim); dash.zeichneDiagramme(); horizont(t); sim.rotoren.forEach((r, i) => { winkel[i] += 0.7*i; }); zeichne(partikel(0.05)); return t;
}
window.SIM_APP = {get sim() { return sim; }, get vergleich() { return vergleich; }, get programm() { return programm; }, vorspulen, neuesModell, zuruecksetzen,
  programmStart: n => { $('programm').value = n; $('programmStart').onclick(); }, pause: p => setPause(p)};
})();
