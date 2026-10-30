#!/usr/bin/env node
/* Abschaetzung der Steuerwirkung einer Taumelscheibe (zyklischer Pitch) am Testmodell 1:4.
 * Quasistatisch: induzierte Stroemung aus dem axialsymmetrischen Schwebezustand eingefroren, Pitch je
 * Fluegel theta = theta0 + thetaC * sin(psi). Ein gefrorener Abwind ueberschaetzt das Moment
 * (in Wirklichkeit passt sich der Abwind teilweise an) -> obere Abschaetzung, Faktor ~0,5 als untere.
 * Starre (gelenklose) Fluegelanbindung: Das Moment wirkt direkt auf Nabe, Lager und Rohr.   node zyklik.js
 */
'use strict';
const fs = require('fs'), path = require('path');
const P = require('../../kreis_r04/simulation/r04_physik.js');
const nach = JSON.parse(fs.readFileSync(path.join(__dirname, 'Nachrechnung_CAD.json')));
const ausl = JSON.parse(fs.readFileSync(path.join(__dirname, 'Auslegung.json')));
const par = JSON.parse(fs.readFileSync(path.join(__dirname, '../cad/parameter.json')));
const DEG = Math.PI / 180, G = 9.81, rho = 1.225, nu = 1.5e-5;
const geo = { ...ausl.geometry_m, rIn: par.blade.r_airfoil_start / 1000 };
const rpm = nach.schweben.rotor_rpm, pu = nach.schweben.pitch_oben, pl = nach.schweben.pitch_unten;
const s = P.simulate({ ...geo, rpm, pitchUpper: pu, pitchLower: pl });

function cyclic(rot, theta0, thetaC, nPsi = 72) {
  const B = geo.blades, c = geo.chord, om = rot.omega; let T = 0, Mx = 0, My = 0;
  for (let j = 0; j < nPsi; j++) {
    const psi = 2 * Math.PI * j / nPsi;
    rot.r.forEach((r, i) => {
      const up = rot.v0[i] + rot.v[i], ut = om * r + rot.wt[i] - rot.w[i];   // inkl. Fremddrall (unterer Rotor)
      const phi = Math.atan2(up, ut), th = (theta0 + thetaC * Math.sin(psi)) * DEG;
      const pol = P.polar((th - phi) / DEG, Math.hypot(up, ut) * c / nu, geo.thickness);
      const dT = 0.5 * rho * (up * up + ut * ut) * c * (pol.cl * Math.cos(phi) - pol.cd * Math.sin(phi)) * rot.dr;
      const w = B / nPsi; T += dT * w; Mx += dT * r * Math.sin(psi) * w; My += -dT * r * Math.cos(psi) * w;
    });
  }
  return { T, Mx, My };
}
const res = {};
for (const [name, rot, th0] of [['oben', s.upper, pu], ['unten', s.lower, pl]]) {
  const a = cyclic(rot, th0, 0), b = cyclic(rot, th0, 3);
  res[name] = { schub_N: +a.T.toFixed(2), moment_je_grad_zyklisch_Nm: +((b.Mx - a.Mx) / 3).toFixed(4), schubaenderung_bei_3grad_N: +(b.T - a.T).toFixed(3) };
}
const W = nach.masse_g / 1000 * G, mPerDeg = res.oben.moment_je_grad_zyklisch_Nm + res.unten.moment_je_grad_zyklisch_Nm;
// Steuerkraefte: Propellermoment (Zentrifugal, zieht Richtung 0 Grad) und Luftkraftmoment (Auftrieb bei 25 % vor der 50-%-Achse)
const om = rpm * 2 * Math.PI / 60, mBlade = nach.schleudertest.fluegelmasse_g / 1000, c = geo.chord;
const propMoment = mBlade * c * c / 12 * om * om * Math.sin(2 * pu * DEG) / 2;
const aeroMoment = W / 16 * 0.25 * c;
const out = {
  status: 'ABSCHAETZUNG_QUASISTATISCH', rotor_rpm: rpm, pitch_oben: pu, pitch_unten: pl,
  rotoren: res,
  rollmoment_je_grad_zyklisch_Nm: { obere_abschaetzung: +mPerDeg.toFixed(3), untere_abschaetzung_faktor_0_5: +(0.5 * mPerDeg).toFixed(3) },
  schwerpunktversatz_ausgleichbar_mm_bei_4grad: { obere: +(4 * mPerDeg / W * 1000).toFixed(1), untere: +(2 * mPerDeg / W * 1000).toFixed(1) },
  steuerfrequenz_1_umlauf_Hz: +(rpm / 60).toFixed(1),
  fluegel_pitchmoment_Nmm: { propellermoment: +(propMoment * 1000).toFixed(1), luftkraftmoment: +(aeroMoment * 1000).toFixed(1),
    netto_ca: +((propMoment - aeroMoment) * 1000).toFixed(1) },
  gestaengekraft_N_bei_horn_12mm: +(Math.max(propMoment, aeroMoment) / 0.012).toFixed(2),
  pitch_je_0_1mm_spiel_grad_horn_12mm: +(Math.atan(0.1 / 12) / DEG).toFixed(2),
  gestaengeweg_mm_fuer_minus2_bis_21grad_horn_12mm: +(12 * (Math.sin(21 * DEG) + Math.sin(2 * DEG))).toFixed(2),
};
fs.writeFileSync(path.join(__dirname, 'Zyklik_Abschaetzung.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 1));
