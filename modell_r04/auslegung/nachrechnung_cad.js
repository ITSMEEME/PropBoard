#!/usr/bin/env node
/* Nachrechnung der Betriebspunkte mit der Masse aus dem CAD (../cad/Pruefbericht.json).
 * Geometrie: aerodynamischer Fluegelbeginn aus cad/parameter.json (r_airfoil_start).  node nachrechnung_cad.js
 */
'use strict';
const fs = require('fs'), path = require('path');
const P = require('../../kreis_r04/simulation/r04_physik.js'), A = require('./antrieb.js');
const cad = JSON.parse(fs.readFileSync(path.join(__dirname, '../cad/Pruefbericht.json')));
const par = JSON.parse(fs.readFileSync(path.join(__dirname, '../cad/parameter.json')));
const ausl = JSON.parse(fs.readFileSync(path.join(__dirname, 'Auslegung.json')));
const G = 9.81, M = A.MOTOR_ECO2_2306_1900, B = A.BATTERY_TATTU_1550_6S;
const GEO = { ...ausl.geometry_m, rIn: par.blade.r_airfoil_start / 1000 };
const ratio = par.gear.z_ring / par.gear.z_pinion, mass = cad.masse_g.gesamt / 1000, pu = ausl.hover.pitchUpper;

function rotors(rpm) {
  const base = { ...GEO, rpm, pitchUpper: pu }, pl = P.balanceLowerPitch(base), s = P.simulate({ ...base, pitchLower: pl });
  return { s, pl, up: { rpm, Q: s.upper.Q }, lo: { rpm, Q: s.lower.Q } };
}
function rpmFor(T) { let lo = 300, hi = 8000; for (let i = 0; i < 40; i++) { const m = (lo + hi) / 2; if (rotors(m).s.T < T) lo = m; else hi = m; } return hi; }

const nh = rpmFor(mass * G), h = rotors(nh), hs = A.systemPoint(M, B, h.up, h.lo, ratio, 0.6), he = A.enduranceSeconds(M, B, h.up, h.lo, ratio);
const nm = rpmFor(2 * mass * G), m = rotors(nm), ms = A.systemPoint(M, B, m.up, m.lo, ratio, 1 - B.usable);
const om = 1.2 * nm * 2 * Math.PI / 60, bladeMass = cad.druckteile.Fluegel.volumen_cm3 * 1e-6 * par.print.density['PA-CF'] * par.print.fill.blade;
const rCg = (par.blade.r_airfoil_start + par.blade.r_tip) / 2000;
const out = {
  status: 'NACHRECHNUNG_MIT_CAD_MASSE_MODELLWERTE', masse_g: cad.masse_g.gesamt, masse_phase1_g: ausl.mass.total_g, uebersetzung: +ratio.toFixed(3),
  fluegel_r_innen_mm: par.blade.r_airfoil_start,
  schweben: { rotor_rpm: +nh.toFixed(0), pitch_oben: pu, pitch_unten: +h.pl.toFixed(2), motorstrom_A: +hs.upper.current.toFixed(2), tastgrad: +hs.duty.toFixed(3),
    p_elektrisch_W: +hs.pBus.toFixed(1), laufzeit_min: +(he.seconds / 60).toFixed(1) },
  maximal_tw2: { rotor_rpm: +nm.toFixed(0), motorstrom_A: +Math.max(ms.upper.current, ms.lower.current).toFixed(2), tastgrad_flugende: +ms.duty.toFixed(3),
    p_elektrisch_W: +ms.pBus.toFixed(0), machbar: ms.feasible },
  schleudertest: { rpm: +(1.2 * nm).toFixed(0), fluegelmasse_g: +(bladeMass * 1000).toFixed(2), fliehkraft_fluegel_N: +(bladeMass * om * om * rCg).toFixed(1),
    servo_g_r37: +(om * om * 0.037 / G).toFixed(0) },
};
fs.writeFileSync(path.join(__dirname, 'Nachrechnung_CAD.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 1));
