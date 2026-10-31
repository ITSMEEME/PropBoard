// ARCHIV F01: damalige Auslegung. Aktuelle P11-Anforderungen: ../integration_p11/anforderungen.cjs
#!/usr/bin/env node
/* R04-Taumelmodell: Betriebspunkte und Steuerwirkung aus CAD-Masse und -Geometrie (../cad/Pruefbericht.json, parameter.json).
 * Aerodynamik: BEMT des Simulators; Antrieb: modell_r04/auslegung/antrieb.js. Modellwerte, nicht validiert.
 *   node nachrechnung.js
 */
'use strict';
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '../..');
const P = require(path.join(ROOT, 'kreis_r04/simulation/r04_physik.js'));
const A = require(path.join(ROOT, 'modell_r04/auslegung/antrieb.js'));
const cad = JSON.parse(fs.readFileSync(path.join(__dirname, '../cad/Pruefbericht.json')));
const par = JSON.parse(fs.readFileSync(path.join(__dirname, '../cad/parameter.json')));
const G = 9.81, DEG = Math.PI / 180, rho = 1.225, nu = 1.5e-5, M = A.MOTOR_ECO2_2306_1900, B = A.BATTERY_TATTU_1550_6S;
const geo = { rIn: par.blade.r_airfoil_start / 1000, rOut: par.blade.r_tip / 1000, chord: par.blade.chord / 1000,
  spacing: (par.levels_z[0] - par.levels_z[1]) / 1000, blades: par.blade.count, thickness: par.blade.tc, twist: 0 };
const ratio = par.gear.z_ring / par.gear.z_pinion, mass = cad.masse_g.gesamt / 1000, pu = par.pitch_hover_deg[0];

function rotors(rpm, pitch = pu) {
  const base = { ...geo, rpm, pitchUpper: pitch }, pl = P.balanceLowerPitch(base), s = P.simulate({ ...base, pitchLower: pl });
  return { s, pl, up: { rpm, Q: s.upper.Q }, lo: { rpm, Q: s.lower.Q } };
}
function rpmFor(T) { let lo = 300, hi = 8000; for (let i = 0; i < 40; i++) { const m = (lo + hi) / 2; if (rotors(m).s.T < T) lo = m; else hi = m; } return hi; }
function cyclicMoment(rot, th0, thc, n = 72) {   // quasistatisch, Abwind aus dem Schwebezustand eingefroren
  let Mx = 0;
  for (let j = 0; j < n; j++) {
    const psi = 2 * Math.PI * j / n;
    rot.r.forEach((r, i) => {
      const up = rot.v0[i] + rot.v[i], ut = rot.omega * r + rot.wt[i] - rot.w[i], phi = Math.atan2(up, ut);
      const pol = P.polar((th0 + thc * Math.sin(psi)) - phi / DEG, Math.hypot(up, ut) * geo.chord / nu, geo.thickness);
      Mx += 0.5 * rho * (up * up + ut * ut) * geo.chord * (pol.cl * Math.cos(phi) - pol.cd * Math.sin(phi)) * rot.dr * r * Math.sin(psi) * geo.blades / n;
    });
  }
  return Mx;
}

const nh = rpmFor(mass * G), h = rotors(nh), hs = A.systemPoint(M, B, h.up, h.lo, ratio, 0.6), he = A.enduranceSeconds(M, B, h.up, h.lo, ratio);
const nm = rpmFor(2 * mass * G), m = rotors(nm), ms = A.systemPoint(M, B, m.up, m.lo, ratio, 1 - B.usable);
const mDeg = (cyclicMoment(h.s.upper, pu, 3) - cyclicMoment(h.s.upper, pu, 0) + cyclicMoment(h.s.lower, h.pl, 3) - cyclicMoment(h.s.lower, h.pl, 0)) / 3;
const om = nh * 2 * Math.PI / 60, bladeMass = cad.druckteile.Fluegel.volumen_cm3 * 1e-6 * par.print.density['PA-CF'] * par.print.fill.blade;
const omS = 1.2 * nm * 2 * Math.PI / 60, rCg = (par.blade.r_airfoil_start + par.blade.r_tip) / 2000;
const propMoment = bladeMass * geo.chord ** 2 / 12 * om * om * Math.sin(2 * pu * DEG) / 2, aeroMoment = mass * G / 16 * 0.25 * geo.chord;
const out = {
  status: 'TAUMELMODELL_NACHRECHNUNG_MODELLWERTE', masse_g: cad.masse_g.gesamt, uebersetzung: +ratio.toFixed(3), fluegel_r_innen_mm: par.blade.r_airfoil_start,
  schweben: { rotor_rpm: +nh.toFixed(0), pitch_oben: pu, pitch_unten: +h.pl.toFixed(2), motorstrom_A: +hs.upper.current.toFixed(2), tastgrad: +hs.duty.toFixed(3),
    p_elektrisch_W: +hs.pBus.toFixed(1), laufzeit_min: +(he.seconds / 60).toFixed(1) },
  maximal_tw2: { rotor_rpm: +nm.toFixed(0), motorstrom_A: +Math.max(ms.upper.current, ms.lower.current).toFixed(2), tastgrad_flugende: +ms.duty.toFixed(3),
    p_elektrisch_W: +ms.pBus.toFixed(0), machbar: ms.feasible },
  zyklik: { rollmoment_Nm_je_grad: { obere: +mDeg.toFixed(3), untere_faktor_0_5: +(0.5 * mDeg).toFixed(3) },
    schwerpunktversatz_mm_bei_max_zyklik: { obere: +(par.cyclic_max_deg * mDeg / (mass * G) * 1000).toFixed(1), untere: +(0.5 * par.cyclic_max_deg * mDeg / (mass * G) * 1000).toFixed(1) },
    frequenz_Hz: +(nh / 60).toFixed(1) },
  stellkraefte: { propellermoment_Nmm: +(propMoment * 1000).toFixed(1), luftkraftmoment_Nmm: +(aeroMoment * 1000).toFixed(1),
    stangenkraft_N: +(Math.max(propMoment, aeroMoment) / (par.horn.arm / 1000)).toFixed(2),
    pitch_je_0_1mm_spiel_grad: +(Math.atan(0.1 / par.horn.arm) / DEG).toFixed(2) },
  schleudertest: { rpm: +(1.2 * nm).toFixed(0), fluegelmasse_g: +(bladeMass * 1000).toFixed(2), fliehkraft_fluegel_N: +(bladeMass * omS * omS * rCg).toFixed(1) },
};
fs.writeFileSync(path.join(__dirname, 'Nachrechnung.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 1));
