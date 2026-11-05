// Physikpruefung des globalen Flugsimulators (Node, ohne Browser).
// Aufruf: node flugsimulator/pruefen_physik.cjs
// Schreibt Ergebnisse/Physik_Pruefung.json, Ergebnisse/Schwebeanalyse_alle.json und .csv
const fs = require('fs'), path = require('path');
const P = require('./physik.js'); require('./modelle.js'); const D = globalThis.SIM_DATEN;
const OUT = path.join(__dirname, 'Ergebnisse'); fs.mkdirSync(OUT, {recursive: true});
const E = {}, pr = (name, ok, wert) => { E[name] = {bestanden: !!ok, wert}; console.log(ok ? 'OK  ' : 'FEHL', name, JSON.stringify(wert)); };
const G = P.G, Q42 = 'QUAD_HEP_S_42_16_V3';

// 1) Motormodell gegen die 19 MN1330-Pruefpunkte
const fit = D.motor.fit_punkte, maxAbw = Math.max(...fit.map(p => Math.abs(p.modell_W/p.gemessen_W - 1)));
pr('Motor: Eingangsleistung an allen 19 Prüfpunkten innerhalb 5 %', maxAbw < 0.05, {max_abweichung: +maxAbw.toFixed(4), kt: D.motor.kt_fit, R: D.motor.r_phase_fit, I0: D.motor.i0_fit});

// 2) Rotor: statischer Schub/Leistung im Schwebepunkt = D13-Ersatzmodell (CT/CP)
{ const s = new P.Sim(D, Q42), r = s.rotoren[0], rho = 1.225, n = 50, Om = 2*Math.PI*n;
  for (let i = 0; i < 6; i++) r.aero(Om, [0, 0, 0], 0, 100, rho, s.r, 0.001);
  const D_ = D.modelle[Q42].d_m, Tref = r.CTp*rho*n*n*D_**4, Pref = r.CPp*rho*n**3*D_**5;
  pr('Rotor: statischer Schub = D13-Koeffizientenmodell (±1 %)', Math.abs(r.aus.T/Tref - 1) < 0.01, {T: r.aus.T, Tref});
  pr('Rotor: statische Wellenleistung = D13-Koeffizientenmodell (±3 %)', Math.abs(r.aus.Q*Om/Pref - 1) < 0.03, {P: r.aus.Q*Om, Pref});
  const Pid = Math.pow(r.aus.T, 1.5)/Math.sqrt(2*rho*r.A), FM = Pid/(r.aus.Q*Om);
  pr('Rotor: Gütegrad < 1 (Impulstheorie eingehalten) und plausibel 0,6–0,85', FM < 1 && FM > 0.6 && FM < 0.85, {FM, sigma: r.sigma, Cd0: r.Cd0, kappa: r.kappa, CL_schweben: r.CL_schweben});
  // Steigflug senkt, Vorwaertsflug hebt den Schub bei gleicher Drehzahl; Bodeneffekt erhoeht ihn
  const T = (v, h = 100) => { for (let i = 0; i < 6; i++) r.aero(Om, v, 0, h, rho, s.r, 0.001); return r.aus.T; };
  const T0 = T([0, 0, 0]), Tc = T([0, 0, 4]), Tf = T([10, 0, 0]), Tg = T([0, 0, 0], 0.5*r.R), Tg2 = T([0, 0, 0], 2*r.R);
  pr('Rotor: Steigflug 4 m/s senkt Schub', Tc < 0.95*T0, {T0, Tc});
  pr('Rotor: Vorwärtsflug 10 m/s erhöht Schub (Translationsauftrieb)', Tf > 1.03*T0, {T0, Tf});
  pr('Rotor: Bodeneffekt z = R/2 deutlich, z = 2R schwach', Tg > 1.04*T0 && Tg2 < 1.02*T0 && Tg2 >= T0, {T0, Tg, Tg2});
  let vrs = 0; for (let i = 0; i < 6; i++) r.aero(Om, [0, 0, -0.6*r.aus.vi], 0, 100, rho, s.r, 0.001); vrs = r.aus.vrs;
  pr('Rotor: Wirbelringstadium bei Sinkrate 0,6·v_h erkannt', vrs > 0.3, {vrs}); }

// 3) Koax: unterer Rotor im Nachlauf -> Mehrleistung gegenueber gleich vielen freien Rotoren
{ const k = P.Sim.schwebeAnalyse(D, 'KOAX_HEP_S_42_16_V2', {nutzlast: 100}), o = P.Sim.schwebeAnalyse(D, 'OKTO_HEP_S_42_16_V2', {nutzlast: 100});
  const pk = k.P_kW/Math.pow(k.masse_kg, 1.5), po = o.P_kW/Math.pow(o.masse_kg, 1.5);
  pr('Koax: induzierter Mehrbedarf gegenüber 8 freien Rotoren (massenbereinigt) 15–60 %', pk/po > 1.15 && pk/po < 1.6, {koax_kW: k.P_kW, okto_kW: o.P_kW, verhaeltnis_massenbereinigt: pk/po}); }

// 4) Akku: Energiebilanz und Spannungseinbruch
{ const r = P.rng(1), a = new P.Akku(r, {S: 24, P: 2, Ah: 22, streuung: 0});
  const U0 = a.leerlauf(); let Wh = 0; for (let i = 0; i < 600*10; i++) { a.schritt(200, 0.1); }
  const dSOC = 1 - a.soc, Ah = a.Ah_entnommen;
  pr('Akku: entnommene Ladung = SoC-Änderung × Kapazität (±1 %)', Math.abs(Ah/(dSOC*44) - 1) < 0.01, {Ah, dSOC});
  pr('Akku: Spannung unter 200 A unter Leerlauf, Zellen erwärmen sich', a.U < a.leerlauf() && a.Tmax > 21, {U: a.U, leerlauf: a.leerlauf(), U_start: U0, T: a.Tmax}); }

// 5) Zeitbereich: Schweben Quad 42″ V3 (100 kg Person) – Kräftegleichgewicht und Energie
{ const s = new P.Sim(D, Q42, {turbulenz: 0, wind: 0, boeen: 0, streuung: 0}); s.regler.start();
  for (let i = 0; i < 25000; i++) s.schritt(0.001);
  const t = s.telemetrie(), ana = P.Sim.schwebeAnalyse(D, Q42, {});
  pr('Zeitbereich: stabiler Schwebeflug (Neigung < 0,5°, |vz| < 0,1 m/s)', Math.abs(t.roll) < 0.5/57.3 && Math.abs(t.nick) < 0.5/57.3 && Math.abs(t.v[2]) < 0.1 && t.phase === 'FLUG', {h: t.hoehe, roll: t.roll*57.3, nick: t.nick*57.3, vz: t.v[2]});
  pr('Zeitbereich: Leistung im Schwebeflug ≈ stationäre Analyse (±12 %, Bodennähe und Akkuspannung)', Math.abs(t.P_kW/ana.P_kW - 1) < 0.12, {zeitbereich_kW: t.P_kW, analyse_kW: ana.P_kW}); }

// 6) Strukturgrenze: Ausleger brechen, wenn der Schub die Screeninggrenze ueberschreitet
{ const D2 = JSON.parse(JSON.stringify(D)); D2.modelle.OKTO_HEP_S_42_16_V2.arme.forEach(a => a.grenze_N = 150);
  const s = new P.Sim(D2, 'OKTO_HEP_S_42_16_V2', {turbulenz: 0}); s.regler.start();
  for (let i = 0; i < 8000 && !s.armBruch.size; i++) s.schritt(0.001);
  pr('Lastgrenze: Überschreiten bricht den Ausleger', s.armBruch.size > 0, {gebrochen: s.armBruch.size, ereignisse: s.ereignisse.slice(-2).map(e => e.text)}); }

// 7) Motorausfall
const ausfall = k => { const s = new P.Sim(D, k, {turbulenz: 0.5}); s.regler.start(); for (let i = 0; i < 14000; i++) s.schritt(0.001);
  s.regler.setStick({hoch: 1}); for (let i = 0; i < 4000; i++) s.schritt(0.001); s.regler.setStick({hoch: 0}); for (let i = 0; i < 4000; i++) s.schritt(0.001);
  const h0 = s.telemetrie().hoehe; s.motorAusfall(0); for (let i = 0; i < 20000; i++) s.schritt(0.001); const t = s.telemetrie(); return {h0, h: t.hoehe, zerstoert: t.zerstoert, gierrate: s.w[2]}; };
{ const o = ausfall('OKTO_HEP_S_42_16_V3'), k = ausfall('KOAX_HEP_S_42_16_V2'), q = ausfall(Q42);
  pr('Motorausfall: Okto und Koax halten die Höhe (±2 m)', !o.zerstoert && !k.zerstoert && Math.abs(o.h - o.h0) < 2 && Math.abs(k.h - k.h0) < 2, {okto: o, koax: k});
  pr('Motorausfall: Quad verliert die Gierachse und stürzt ab', !!q.zerstoert, q); }

// 8) Schwebeanalyse aller 120 Konfigurationen (Standard: 100 kg Person, 24S2P 22 Ah, 20 °C, NN)
const alle = Object.keys(D.modelle).map(k => { const m = D.modelle[k], a = P.Sim.schwebeAnalyse(D, k, {});
  return {schluessel: k, bauweise: m.bauweise, propeller: m.propeller, variante: m.variante, masse_kg: +a.masse_kg.toFixed(2), schub_max_kg: +a.schub_max_kg.toFixed(1), schub_gewicht: +a.tw_max.toFixed(3),
    schwebe_rpm: Math.round(a.rpm), leistung_kW: +a.P_kW.toFixed(2), akkustrom_A: Math.round(a.I_bus_A), phasenstrom_A: Math.round(a.I_phase_max_A), drehmoment_Nm: +a.Q_max_Nm.toFixed(1),
    flugzeit_min: a.gesaettigt ? 0 : +a.flugzeit_min.toFixed(2), schwebefaehig: !a.gesaettigt, arm_lastfaktor_grenze: +a.arm_lastfaktor_grenze.toFixed(2), mach_spitze: +a.mach_spitze.toFixed(3), FM: +a.FM.toFixed(3)}; });
const fl = alle.filter(a => a.schwebefaehig);
pr('Analyse aller 120 Konfigurationen gerechnet', alle.length === 120, {schwebefaehig: fl.length, beste_flugzeit: fl.sort((a, b) => b.flugzeit_min - a.flugzeit_min)[0]});
fs.writeFileSync(path.join(OUT, 'Schwebeanalyse_alle.json'), JSON.stringify({annahmen: {nutzlast_kg: 100, akku: '24S2P 22 Ah, 165 Wh/kg, Reserve 15 %', temp_C: 20, hoehe_m: 0, bordnetz_W: 30,
  hinweis: 'Stationaerer Schwebeflug ausserhalb Bodeneffekt; Propellerbeiwerte aus NS52x20-Tabelle uebertragen, kein HEP-S-Kennfeld'}, konfigurationen: alle}, null, 1));
const sp = Object.keys(alle[0]); fs.writeFileSync(path.join(OUT, 'Schwebeanalyse_alle.csv'), sp.join(';') + '\n' + alle.map(a => sp.map(k => a[k]).join(';')).join('\n') + '\n');
const ok = Object.values(E).every(e => e.bestanden);
fs.writeFileSync(path.join(OUT, 'Physik_Pruefung.json'), JSON.stringify({bestanden: ok, pruefungen: E}, null, 1));
console.log(ok ? 'ALLE BESTANDEN' : 'NICHT BESTANDEN'); process.exit(ok ? 0 : 1);
