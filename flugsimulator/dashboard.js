/* Statusdashboard: Kennwerte, Warnungen, Motortabelle, Strukturlast, Verlaufsdiagramme */
(function(root){
'use strict';
const $ = id => document.getElementById(id);
const f = (x, d = 1) => Number.isFinite(x) ? x.toLocaleString('de-DE', {minimumFractionDigits: d, maximumFractionDigits: d}) : '–';
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const ICON = {kritisch: '■', ernst: '▲', warnung: '▲', gut: '●', info: '○'};
const mmss = s => { if (!Number.isFinite(s) || s <= 0) return '0:00'; s = Math.min(s, 359999); const m = Math.floor(s/60), r = Math.floor(s % 60); return `${m}:${String(r).padStart(2, '0')}`; };

// ------------------------------------------------------------------ Verlaufsdiagramm (eine Reihe, optionale Bezugslinie)
class Diagramm {
  constructor(el, o) {
    this.o = o; el.innerHTML = `<h3>${o.titel} <small>${o.einheit}</small></h3><canvas></canvas><div class="tip"></div>`;
    this.c = el.querySelector('canvas'); this.tip = el.querySelector('.tip'); this.daten = []; this.hover = null;
    this.c.addEventListener('pointermove', e => { const r = this.c.getBoundingClientRect(); this.hover = (e.clientX - r.left)/r.width; this.zeichne(); });
    this.c.addEventListener('pointerleave', () => { this.hover = null; this.tip.style.display = 'none'; this.zeichne(); });
  }
  push(t, y, ref) { this.daten.push([t, y, ref]); while (this.daten.length && this.daten[0][0] < t - 90) this.daten.shift(); }
  reset() { this.daten = []; this.zeichne(); }
  zeichne() {
    const c = this.c, dpr = Math.min(2, devicePixelRatio || 1), w = c.clientWidth, h = c.clientHeight; if (!w) return;
    if (c.width !== Math.round(w*dpr)) { c.width = Math.round(w*dpr); c.height = Math.round(h*dpr); }
    const g = c.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, w, h);
    const D = this.daten, L = 34, R = 6, T = 6, B = 16;
    g.font = '10px system-ui'; g.fillStyle = css('--muted'); g.strokeStyle = css('--line'); g.lineWidth = 1;
    if (D.length < 2) { g.fillText('noch keine Daten', L, h/2); return; }
    const t0 = D[0][0], t1 = Math.max(D[D.length-1][0], t0 + 1);
    let lo = Infinity, hi = -Infinity; for (const d of D) { lo = Math.min(lo, d[1], d[2] ?? Infinity); hi = Math.max(hi, d[1], d[2] ?? -Infinity); }
    if (this.o.null) lo = Math.min(lo, 0); if (hi - lo < (this.o.min || 1)) { const m = (hi + lo)/2; lo = m - (this.o.min || 1)/2; hi = m + (this.o.min || 1)/2; }
    const pad = (hi - lo)*0.08; lo -= pad; hi += pad;
    const X = t => L + (t - t0)/(t1 - t0)*(w - L - R), Y = y => T + (1 - (y - lo)/(hi - lo))*(h - T - B);
    // Raster (zurueckhaltend)
    const step = (() => { const r = (hi - lo)/3, p = Math.pow(10, Math.floor(Math.log10(r))); return [1, 2, 5, 10].map(k => k*p).find(k => k >= r) || r; })();
    for (let v = Math.ceil(lo/step)*step; v <= hi; v += step) { const y = Math.round(Y(v)) + .5; g.beginPath(); g.moveTo(L, y); g.lineTo(w - R, y); g.stroke(); g.fillText(f(v, step < 1 ? 1 : 0), 2, y + 3); }
    g.fillText(`${f(t1 - t0, 0)} s`, w - R - 26, h - 3);
    // Bezugslinie
    if (D[D.length-1][2] !== undefined) { g.strokeStyle = css('--ref'); g.setLineDash([4, 3]); g.beginPath(); D.forEach((d, i) => i ? g.lineTo(X(d[0]), Y(d[2])) : g.moveTo(X(d[0]), Y(d[2]))); g.stroke(); g.setLineDash([]);
      g.fillStyle = css('--muted'); g.fillText(this.o.refName, L + 3, Y(D[D.length-1][2]) - 4); }
    g.strokeStyle = css('--serie'); g.lineWidth = 2; g.lineJoin = 'round'; g.beginPath(); D.forEach((d, i) => i ? g.lineTo(X(d[0]), Y(d[1])) : g.moveTo(X(d[0]), Y(d[1]))); g.stroke();
    if (this.hover !== null) {
      const tt = t0 + clamp01((this.hover*w - L)/(w - L - R))*(t1 - t0); let best = D[0]; for (const d of D) if (Math.abs(d[0] - tt) < Math.abs(best[0] - tt)) best = d;
      const x = X(best[0]); g.strokeStyle = css('--muted'); g.lineWidth = 1; g.beginPath(); g.moveTo(x, T); g.lineTo(x, h - B); g.stroke();
      g.fillStyle = css('--serie'); g.strokeStyle = css('--card'); g.lineWidth = 2; g.beginPath(); g.arc(x, Y(best[1]), 4, 0, 7); g.fill(); g.stroke();
      this.tip.style.display = 'block'; this.tip.textContent = `t ${f(best[0], 1)} s · ${f(best[1], this.o.d ?? 1)} ${this.o.einheit}` + (best[2] !== undefined ? ` · ${this.o.refName} ${f(best[2], this.o.d ?? 1)}` : '');
      this.tip.style.left = Math.min(x + 6, w - this.tip.offsetWidth) + 'px'; this.tip.style.top = '18px';
    }
  }
}
const clamp01 = x => Math.max(0, Math.min(1, x));

// ------------------------------------------------------------------ Warnungen aus Telemetrie
function warnungen(t, s) {
  const W = [], add = (stufe, text) => W.push({stufe, text});
  if (t.zerstoert) add('kritisch', t.zerstoert);
  if (t.tw_max < 1) add('kritisch', `Maximaler Schub ${f(t.schub_max_kg, 0)} kg unter Gewicht ${f(t.masse_kg, 0)} kg – kein Abheben möglich`);
  else if (t.tw_max < 1.4) add('ernst', `Schub/Gewicht nur ${f(t.tw_max, 2)} – geringe Steuerreserve`);
  const mx = t.arme.reduce((a, b) => b.u > a.u ? b : a, t.arme[0]);
  if (t.arme.some(a => a.bruch)) add('kritisch', 'Ausleger gebrochen (Lastgrenze überschritten)');
  else if (mx.u > 0.8) add('ernst', `Ausleger M${mx.nr}: ${f(mx.u*100, 0)} % der Lastgrenze`);
  const sat = t.motoren.filter(m => m.grenze && !m.aus);
  if (sat.length) add(sat.length >= t.motoren.length/2 ? 'ernst' : 'warnung', `Motor ${sat.map(m => 'M' + m.nr).join(', ')} an der Grenze: ${[...new Set(sat.map(m => m.grenze))].join(', ')}`);
  const aus = t.motoren.filter(m => m.aus); if (aus.length) add('kritisch', `Motor ${aus.map(m => 'M' + m.nr).join(', ')} ohne Leistung`);
  const Tw = Math.max(...t.motoren.map(m => m.Tw)), Te = Math.max(...t.motoren.map(m => m.Te));
  if (Tw > 150) add('kritisch', `Wicklungstemperatur ${f(Tw, 0)} °C – Leistung wird reduziert`); else if (Tw > 120) add('ernst', `Wicklungstemperatur ${f(Tw, 0)} °C`);
  if (Te > 100) add('kritisch', `Reglertemperatur ${f(Te, 0)} °C – Leistung wird reduziert`); else if (Te > 80) add('ernst', `Reglertemperatur ${f(Te, 0)} °C`);
  const Iesc = Math.max(...s.antriebe.map(a => a.Iesc_mittel)); if (Iesc > 100) add('ernst', `Reglerstrom im 20-s-Mittel ${f(Iesc, 0)} A über 100 A Dauer`);
  if (t.zelle_min < 3.3) add(t.zelle_min < 3.1 ? 'kritisch' : 'ernst', `Zellspannung unter Last ${f(t.zelle_min, 2)} V`);
  else if (t.soc < 0.3) add('warnung', `Akku ${f(t.soc*100, 0)} % – Landung planen`);
  if (t.U0 - t.U > 0.12*t.U0) add('warnung', `Spannungseinbruch ${f((t.U0 - t.U)/t.U0*100, 0)} % unter Last`);
  if (t.akku_T > 60) add('ernst', `Akkutemperatur ${f(t.akku_T, 0)} °C`);
  const vrs = Math.max(...t.motoren.map(m => m.vrs)); if (vrs > 0.25) add(vrs > 0.6 ? 'kritisch' : 'ernst', `Wirbelringstadium (Intensität ${f(vrs*100, 0)} %) – vorwärts aus dem eigenen Abwind fliegen`);
  const ab = Math.max(...t.motoren.map(m => m.abriss)); if (ab > 0.02) add('ernst', `Strömungsabriss am Blatt (${f(ab*100, 0)} %)`);
  const ma = Math.max(...t.motoren.map(m => m.mach)); if (ma > 0.6) add('warnung', `Blattspitzen-Machzahl ${f(ma, 2)}`);
  if (s.regler.saettigung && s.regler.phase === 'FLUG') add('warnung', 'Steuerzuordnung gesättigt – Reserve aufgebraucht');
  const ge = Math.min(...t.motoren.map(m => m.ge)); if (ge < 0.97 && !t.amBoden) add('info', `Bodeneffekt aktiv (induzierte Geschwindigkeit −${f((1-ge)*100, 0)} %)`);
  const wl = Math.hypot(t.wind[0], t.wind[1]); if (wl > 10) add('warnung', `Wind ${f(wl, 1)} m/s`);
  if (t.amBoden && t.phase !== 'AUS') { const fu = t.fuesse, mn = Math.min(...fu), mxF = Math.max(...fu); if (mxF > 50 && mn < 0.05*mxF) add('warnung', 'Ein Fuß ohne Last – Kippgefahr am Boden'); }
  if (t.maxLast.fuss > 1) add('ernst', `Landestoß bis ${f(t.maxLast.fuss*100, 0)} % der Fußauslegung`);
  if (s.md.pruefungen && !s.md.pruefungen.stabwerk_screening_ok) add('info', 'Konstruktion: Stabwerk-Screening (3 g) nicht bestanden – Lastgrenze entsprechend niedriger');
  const rang = {kritisch: 0, ernst: 1, warnung: 2, info: 3}; W.sort((a, b) => rang[a.stufe] - rang[b.stufe]);
  return W;
}

class Dashboard {
  constructor() {
    this.diagramme = {
      P: new Diagramm(this.neu(), {titel: 'Leistung aus dem Akku', einheit: 'kW', null: true, min: 2}),
      U: new Diagramm(this.neu(), {titel: 'Akkuspannung unter Last', einheit: 'V', min: 4}),
      h: new Diagramm(this.neu(), {titel: 'Höhe über Grund', einheit: 'm', null: true, min: 2}),
      T: new Diagramm(this.neu(), {titel: 'Auftrieb', einheit: 'kg', null: true, min: 20, refName: 'Gewicht', d: 0}),
    };
    this.letzt = 0;
  }
  neu() { const d = document.createElement('div'); d.className = 'chart'; $('charts').appendChild(d); return d; }
  reset() { Object.values(this.diagramme).forEach(d => d.reset()); }
  aufzeichnen(t) { const D = this.diagramme; D.P.push(t.t, t.P_kW); D.U.push(t.t, t.U); D.h.push(t.t, t.hoehe); D.T.push(t.t, t.auftrieb_kg, t.masse_kg); }
  zeichneDiagramme() { Object.values(this.diagramme).forEach(d => d.zeichne()); }
  aktualisiere(t, s) {
    const W = warnungen(t, s), schlimm = W[0] ? W[0].stufe : 'gut';
    const st = $('gesamtStatus'); st.className = 'status st-' + (schlimm === 'info' ? 'gut' : schlimm);
    st.textContent = `${ICON[schlimm === 'info' ? 'gut' : schlimm]} ${{kritisch: 'Kritisch', ernst: 'Grenzbereich', warnung: 'Hinweis', info: 'Normal', gut: 'Normal'}[schlimm]}`;
    const Tw = Math.max(...t.motoren.map(m => m.Tw)), am = t.arme.reduce((a, b) => b.u > a.u ? b : a, t.arme[0]);
    const kp = [
      ['Gewicht', f(t.masse_kg, 1), 'kg', `davon Nutzlast ${f(s.mm.anteile.nutzlast, 0)} kg`],
      ['Erzeugter Auftrieb', f(t.auftrieb_kg, 1), 'kg', `${f(t.auftrieb_kg/t.masse_kg*100, 0)} % des Gewichts`],
      ['Max. Schub', f(t.schub_max_kg, 0), 'kg', `Schub/Gewicht ${f(t.tw_max, 2)}`],
      ['Restflugzeit', mmss(t.flugzeit_s), 'min', 'bei aktueller Leistung (3-s-Mittel)'],
      ['Akku', f(t.soc*100, 0), '%', `${f(t.rest_Wh/1000, 2)} kWh bis Reserve`],
      ['Spannung', f(t.U, 1), 'V', `Leerlauf ${f(t.U0, 1)} V`],
      ['Stromverbrauch', f(t.I, 0), 'A', `${f(t.Ah, 2)} Ah entnommen`],
      ['Leistung', f(t.P_kW, 1), 'kW', `${f(t.Wh, 0)} Wh verbraucht`],
      ['Min. Zelle', f(t.zelle_min, 2), 'V', `max. ${f(t.zelle_max, 2)} V · 24S`],
      ['Motor max.', f(Tw, 0), '°C', `Regler ${f(Math.max(...t.motoren.map(m => m.Te)), 0)} °C`],
      ['Akku', f(t.akku_T, 1), '°C', 'wärmste Zelle'],
      ['Lastvielfaches', f(t.nz, 2), 'g', `max. ${f(t.maxLast.g, 2)} g`],
      ['Ausleger max.', f(am.u*100, 0), '%', `M${am.nr} · Grenze ${f(am.grenze_N, 0)} N`],
      ['Wind', f(Math.hypot(t.wind[0], t.wind[1]), 1), 'm/s', `vertikal ${f(t.wind[2], 1)} m/s`],
      ['Luftdichte', f(s.atm.rho, 3), 'kg/m³', `${f(s.opt.temp_C, 0)} °C · ${f(s.opt.hoehe_m, 0)} m`],
    ];
    if (['AUS', 'HOCHLAUF', 'START'].includes(t.phase) && s.restSchaetzung !== undefined) { s.E0 = s.E0 || t.rest_Wh; kp[3][1] = mmss(s.restSchaetzung*60*t.rest_Wh/Math.max(s.E0, 1)); kp[3][3] = 'Schätzung Schwebeflug'; }
    $('kpis').innerHTML = kp.map(([a, b, c, d]) => `<div class="kpi"><span>${a}</span><strong>${b}<small>${c}</small></strong><em>${d}</em></div>`).join('');
    $('warnungen').innerHTML = W.length ? W.slice(0, 12).map(w => `<li class="st-${w.stufe}"><b aria-hidden="true">${ICON[w.stufe]}</b><span style="color:var(--ink)">${{kritisch: 'Kritisch', ernst: 'Grenze', warnung: 'Hinweis', info: 'Info'}[w.stufe]}: ${w.text}</span></li>`).join('') : '<li class="leer">● Keine Grenzwerte erreicht</li>';
    const dm = t.motoren;
    $('motoren').innerHTML = '<table><tr><th>Motor</th><th>U/min</th><th>Aussteu.</th><th>Schub kg</th><th>Strom A</th><th>Wickl. °C</th><th>Regler °C</th><th>Status</th></tr>' +
      dm.map(m => `<tr><td>M${m.nr}${m.lage === 'unten' ? ' u' : ''} ${m.dreh > 0 ? '↺' : '↻'}</td><td>${f(m.rpm, 0)}</td><td><div class="bar" title="${f(m.d*100, 0)} %"><i style="width:${Math.min(100, m.d*100)}%"></i></div></td><td>${f(m.T_kg, 1)}</td><td>${f(m.I, 0)}</td><td class="${m.Tw > 150 ? 'st-kritisch' : m.Tw > 120 ? 'st-ernst' : ''}">${f(m.Tw, 0)}</td><td class="${m.Te > 100 ? 'st-kritisch' : m.Te > 80 ? 'st-ernst' : ''}">${f(m.Te, 0)}</td><td class="${m.aus ? 'st-kritisch' : m.grenze ? 'st-warnung' : 'st-gut'}">${m.aus ? '■ aus' : m.grenze ? '▲ ' + m.grenze : '● ok'}</td></tr>`).join('') + '</table>';
    $('arme').innerHTML = t.arme.map(a => `<div class="z"><span>M${a.nr}</span><div class="bar"><i style="width:${Math.min(100, a.u*100)}%;background:${a.bruch ? 'var(--kritisch)' : a.u > 0.8 ? 'var(--ernst)' : 'var(--serie)'}"></i></div><span>${f(a.last_N, 0)} / ${f(a.grenze_N, 0)} N</span></div>`).join('');
    const fu = t.fuesse, ab = Math.max(...dm.map(m => m.abriss)), vrs = Math.max(...dm.map(m => m.vrs)), ma = Math.max(...dm.map(m => m.mach)), mu = Math.max(...dm.map(m => m.mu));
    $('struktur').innerHTML = [['Fußlast max.', `${f(Math.max(...fu), 0)} N`], ['Fußauslegung', `${f(s.md.fuss_grenze_N, 0)} N`], ['Wirbelring', `${f(vrs*100, 0)} %`], ['Strömungsabriss', `${f(ab*100, 0)} %`],
      ['Blattspitze Mach', f(ma, 2)], ['Fortschrittsgrad μ', f(mu, 3)], ['Neigung', `${f(t.roll*57.3, 1)}° / ${f(t.nick*57.3, 1)}°`], ['Reglerreserve', s.regler.reserve !== undefined ? `${f(s.regler.reserve*100, 0)} %` : '–']]
      .map(([a, b]) => `<div><span>${a}</span><strong>${b}</strong></div>`).join('');
  }
}
root.SimDashboard = {Dashboard, warnungen, fmt: f, mmss};
})(globalThis);
