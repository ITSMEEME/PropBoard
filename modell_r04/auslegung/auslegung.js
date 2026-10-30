#!/usr/bin/env node
/* R04-Testmodell, Phase 1: Auslegung im Massstab 1:4.
 * Aerodynamik: BEMT aus kreis_r04/simulation/r04_physik.js (vereinfachte Polare, nicht validiert).
 * Antrieb: antrieb.js. Ergebnis: Auslegung.json, Auslegung.md, CSV-Dateien in diesem Ordner.
 *   node auslegung.js
 */
'use strict';
const fs = require('fs'), path = require('path');
const P = require('../../kreis_r04/simulation/r04_physik.js');
const A = require('./antrieb.js');
const OUT = __dirname, G = 9.81;

/* ---------- Geometrie 1:4 ---------- */
const SCALE = 0.25;
const GEO = { rIn: 0.15 * SCALE, rOut: 0.75 * SCALE, chord: 0.12 * SCALE, spacing: 0.24 * SCALE, blades: 8, thickness: 0.12, twist: 0 };
const MOTOR = A.MOTOR_ECO2_2306_1900, BAT = A.BATTERY_TATTU_1550_6S, DRIVE = A.DEFAULT_DRIVE;
const MODULE = 1.0;                // Zahnradmodul [mm], gedruckter Zahnkranz + Stahlritzel
const BED = [200, 148, 150];        // Druckbett [mm]
const RHO_PRINT = 1300;             // PETG-CF (konservativ; PA-CF ~1170)
const N_MAX_DESIGN_TW = 2.0;        // Auslegung: Schub/Gewicht 2 am Maximalpunkt
const SPIN_TEST_FACTOR = 1.2;       // Schleudertest 120 % der Maximaldrehzahl
const ALPHA_MARGIN = 2;             // Grad Abstand zum Abrisswinkel der Polare

/* ---------- Fluegelmasse aus Geometrie ---------- */
function nacaArea(tc) { // Flaeche / c^2 des geschlossenen NACA-00xx
  let a = 0; const n = 400;
  for (let i = 0; i < n; i++) { const q = (i + 0.5) / n; a += 2 * 5 * tc * (0.2969 * Math.sqrt(q) - 0.126 * q - 0.3516 * q * q + 0.2843 * q ** 3 - 0.1036 * q ** 4) / n; }
  return a;
}
const span = GEO.rOut - GEO.rIn;
const bladeVolume = nacaArea(GEO.thickness) * GEO.chord ** 2 * span;
const BLADE_FILL = 0.65;            // Annahme: 3 Perimeter + 30 % Infill
const bladeMass = bladeVolume * RHO_PRINT * BLADE_FILL + 0.0015;   // + Wurzelhebel/Stift
const bladeCg = GEO.rIn + span / 2;

/* ---------- Massenbudget ---------- */
const MASS = [
  ['Antriebsakku Tattu 1550 mAh 6S', BAT.mass, 'Annahme, wiegen'],
  ['2 x Motor ECO II 2306 (inkl. Kabel)', 2 * 0.032, 'Datenblatt 30,2 g + Kabel'],
  ['FC SpeedyBee F405 V4 + BLS 55A', 0.026, 'Annahme'],
  ['ELRS-Empfaenger + Antenne', 0.003, 'Annahme'],
  ['16 x Fluegel (gedruckt)', 16 * bladeMass, `Geometrie, ${(RHO_PRINT / 1000).toFixed(2)} g/cm3, Fuellgrad ${BLADE_FILL}`],
  ['16 x Servo HV-Mikro', 16 * 0.007, 'Annahme 7 g'],
  ['2 x Nabenring mit Lagerungen und Gestaenge', 2 * 0.050, 'Schaetzung'],
  ['2 x Zahnkranz m1 inkl. Speichen', 2 * 0.026, 'Schaetzung'],
  ['2 x Stahlritzel + Adapter', 2 * 0.006, 'Annahme'],
  ['2 x Lager 6806-2RS', 2 * 0.019, 'Katalogwert ca.'],
  ['Mittelrohr Al D30 x 1 mm, 160 mm', Math.PI * (0.015 ** 2 - 0.014 ** 2) * 0.16 * 2700, 'Geometrie'],
  ['Rotorelektronik 2 x (ESP32-C3 + 2 x 1S 400 mAh + Schalter)', 2 * (0.003 + 2 * 0.010 + 0.002), 'Annahme'],
  ['Pitch-Bridge ESP32-C3', 0.003, 'Annahme'],
  ['Motorhalteplatten oben/unten, Akkutraeger, Stackhalter', 0.120, 'Schaetzung'],
  ['Kabel, Stecker, Schrauben', 0.050, 'Schaetzung'],
];
const massTotal = MASS.reduce((s, m) => s + m[1], 0);
const rotatingMassPerRotor = 8 * bladeMass + 8 * 0.007 + 0.050 + 0.026 + 0.025;

/* ---------- Hilfsfunktionen Aerodynamik ---------- */
function rotors(rpm, pitchUpper) {
  const base = { ...GEO, rpm, pitchUpper };
  const pl = P.balanceLowerPitch(base);
  const s = P.simulate({ ...base, pitchLower: pl ?? pitchUpper });
  return { s, pitchLower: pl, upper: { rpm, Q: s.upper.Q }, lower: { rpm, Q: s.lower.Q } };
}
function rpmForThrust(T, pitchUpper) {
  let lo = 200, hi = 8000;
  if (rotors(hi, pitchUpper).s.T < T) return null;
  for (let i = 0; i < 40; i++) { const m = 0.5 * (lo + hi); if (rotors(m, pitchUpper).s.T < T) lo = m; else hi = m; }
  return hi;
}
function alphaMargin(s) {   // kleinster Abstand zum lokalen Abrisswinkel ueber beide Rotoren
  let m = Infinity;
  for (const r of [s.upper, s.lower]) r.alpha.forEach((a, i) => { m = Math.min(m, P.stallAngle(r.re[i], GEO.thickness) - Math.abs(a)); });
  return m;
}

/* ---------- 1. Schwebepunkt ueber Pitch (Uebersetzung vorlaeufig 10:1) ---------- */
const W = massTotal * G;
const hoverSweep = [];
for (let pu = 6; pu <= 22; pu += 1) {
  const n = rpmForThrust(W, pu); if (!n) continue;
  const r = rotors(n, pu), sp = A.systemPoint(MOTOR, BAT, r.upper, r.lower, 10, 0.6, DRIVE);
  hoverSweep.push({ pitchUpper: pu, pitchLower: +r.pitchLower.toFixed(2), rotorRpm: +n.toFixed(0), aeroPower: +r.s.P.toFixed(1),
    electricPower: +sp.pBus.toFixed(1), alphaMargin: +alphaMargin(r.s).toFixed(2), figureOfMerit: +r.s.figureOfMerit.toFixed(3), tipSpeed: +r.s.tipSpeed.toFixed(1) });
}
const hoverOk = hoverSweep.filter((h) => h.alphaMargin >= ALPHA_MARGIN);
const hover = hoverOk.reduce((b, h) => (h.electricPower < b.electricPower ? h : b), hoverOk[0]);

/* ---------- 2. Maximalpunkt (Schub/Gewicht 2 bei Schwebepitch) ---------- */
const nMax = rpmForThrust(N_MAX_DESIGN_TW * W, hover.pitchUpper);
const maxPt = rotors(nMax, hover.pitchUpper);
const hoverPt = rotors(hover.rotorRpm, hover.pitchUpper);

/* ---------- 3. Uebersetzung ---------- */
const ratioSweep = [];
for (let z1 = 10; z1 <= 14; z1++) for (let z2 = 80; z2 <= 140; z2++) {
  const tipDia = MODULE * (z2 + 2);
  if (tipDia > Math.min(BED[0], BED[1]) - 10) continue;
  const i = z2 / z1;
  const maxEnd = A.systemPoint(MOTOR, BAT, maxPt.upper, maxPt.lower, i, 1 - BAT.usable, DRIVE);
  const hov = A.systemPoint(MOTOR, BAT, hoverPt.upper, hoverPt.lower, i, 0.6, DRIVE);
  const end = A.enduranceSeconds(MOTOR, BAT, hoverPt.upper, hoverPt.lower, i, DRIVE);
  ratioSweep.push({ z1, z2, ratio: +i.toFixed(3), tipDiameter: tipDia, centerDistance: MODULE * (z1 + z2) / 2,
    hoverPower: +hov.pBus.toFixed(1), hoverMotorCurrent: +hov.upper.current.toFixed(2), hoverMotorEff: +hov.upper.eff.toFixed(3), hoverDuty: +hov.duty.toFixed(3),
    maxDutyEndOfFlight: +maxEnd.duty.toFixed(3), maxMotorCurrent: +Math.max(maxEnd.upper.current, maxEnd.lower.current).toFixed(2),
    maxFeasible: maxEnd.feasible, enduranceMin: +(end.seconds / 60).toFixed(2), enduranceLimit: end.limit });
}
// Zusatzkriterien: ESC-Teillastverluste sind nicht modelliert -> Tastgrad im Schweben >= 0,35;
// Ritzel >= 12 Zaehne (weniger Unterschnitt, Stahlritzel m1 verfuegbar). Das Leistungsoptimum ist flach.
const feasible = ratioSweep.filter((r) => r.maxFeasible && r.maxDutyEndOfFlight <= 0.9 && r.hoverDuty >= 0.35 && r.z1 >= 12);
// Kleinste Schwebeleistung; bei Gleichstand (< 0,5 W) groesseres Ritzel (Zahnfussfestigkeit, kein Unterschnitt)
const gear = feasible.reduce((b, r) => (r.hoverPower < b.hoverPower - 0.5 || (Math.abs(r.hoverPower - b.hoverPower) <= 0.5 && r.z1 > b.z1) ? r : b), feasible[0]);

/* ---------- 4. Lastfaelle beim Schleudertest ---------- */
const nSpin = SPIN_TEST_FACTOR * nMax, om = nSpin * 2 * Math.PI / 60;
const spinPt = rotors(nSpin, hover.pitchUpper);
const qSpin = Math.max(spinPt.upper.Q, spinPt.lower.Q);
const ringPitchR = MODULE * gear.z2 / 2000;
const ft = qSpin / ringPitchR;
const faceWidth = 6e-3, lewisY = Math.PI * (0.154 - 0.912 / gear.z1);
const loads = {
  spinTestRpm: +nSpin.toFixed(0),
  bladeMass_g: +(bladeMass * 1000).toFixed(2),
  bladeCentrifugalForce_N: +(bladeMass * om * om * bladeCg).toFixed(1),
  bladeRootStress_MPa: +(bladeMass * om * om * bladeCg / (nacaArea(GEO.thickness) * GEO.chord ** 2 * BLADE_FILL) / 1e6).toFixed(2),
  servoAccel_g_r30: +(om * om * 0.030 / G).toFixed(0), servoAccel_g_r45: +(om * om * 0.045 / G).toFixed(0),
  servoRadialForce_N_r45_7g: +(0.007 * om * om * 0.045).toFixed(1),
  tipSpeed_m_s: +(om * GEO.rOut).toFixed(1),
  rotorKineticEnergy_J: +(0.5 * om * om * (8 * bladeMass * (bladeCg ** 2 + span ** 2 / 12) + (rotatingMassPerRotor - 8 * bladeMass) * 0.035 ** 2)).toFixed(1),
  gearTangentialForce_N: +ft.toFixed(1),
  pinionToothBendingStress_MPa: +(ft / (faceWidth * MODULE * 1e-3 * lewisY) / 1e6).toFixed(1),
  pitchLineVelocity_m_s: +(om * ringPitchR).toFixed(1),
  pitchMomentPropeller_Nmm: +(1000 * bladeMass * GEO.chord ** 2 / 12 * om * om * Math.sin(2 * hover.pitchUpper * Math.PI / 180) / 2).toFixed(1),
};

/* ---------- 5. Pitchbereich der Servos ---------- */
const pitchSweep = [];
for (let pu = -2; pu <= 24; pu += 1) {
  const r = rotors(hover.rotorRpm, pu);
  pitchSweep.push({ pitchUpper: pu, pitchLower: r.pitchLower == null ? null : +r.pitchLower.toFixed(2), thrust_N: +r.s.T.toFixed(2),
    thrust_g: +(r.s.T / G * 1000).toFixed(0), alphaMargin: +alphaMargin(r.s).toFixed(2), stalledFraction: +r.s.stalledFraction.toFixed(3) });
}
const stallPitch = (pitchSweep.find((p) => p.alphaMargin < 0) || {}).pitchUpper ?? null;
const servoRange = { min: -2, max: stallPitch != null ? Math.min(24, stallPitch + 2) : 24 };

/* ---------- 6. Pruefmatrix ---------- */
const matrix = [];
for (const rpm of [1000, 1500, 2000, 2500, 3000, Math.round(nMax / 100) * 100]) for (let pu = 4; pu <= 18; pu += 2) {
  const r = rotors(rpm, pu), sp = A.systemPoint(MOTOR, BAT, r.upper, r.lower, gear.ratio, 1 - BAT.usable, DRIVE);
  matrix.push({ rotorRpm: rpm, pitchUpper: pu, pitchLower: r.pitchLower == null ? null : +r.pitchLower.toFixed(2), thrust_g: +(r.s.T / G * 1000).toFixed(0),
    electricPower_W: +sp.pBus.toFixed(0), motorCurrent_A: +Math.max(sp.upper.current, sp.lower.current).toFixed(1), duty_endOfFlight: +sp.duty.toFixed(3),
    feasible: sp.feasible, alphaMargin: +alphaMargin(r.s).toFixed(2) });
}

/* ---------- Ausgabe ---------- */
const hov = A.systemPoint(MOTOR, BAT, hoverPt.upper, hoverPt.lower, gear.ratio, 0.6, DRIVE);
const mx = A.systemPoint(MOTOR, BAT, maxPt.upper, maxPt.lower, gear.ratio, 1 - BAT.usable, DRIVE);
const result = {
  status: 'VORAUSLEGUNG_MODELLWERTE_NICHT_VALIDIERT', date: '2026-10-30',
  geometry_m: GEO, scale: SCALE, module_mm: MODULE,
  mass: { items: MASS.map(([name, kg, src]) => ({ name, g: +(kg * 1000).toFixed(1), source: src })), total_g: +(massTotal * 1000).toFixed(0),
    rotatingPerRotor_g: +(rotatingMassPerRotor * 1000).toFixed(0) },
  hover: { ...hover, motorRpm: +(hover.rotorRpm * gear.ratio).toFixed(0), motorCurrent: +hov.upper.current.toFixed(2), motorCurrentLower: +hov.lower.current.toFixed(2),
    batteryCurrent: +hov.batteryCurrent.toFixed(2), duty: +hov.duty.toFixed(3), motorLoss_W: +(hov.upper.copperLoss + hov.upper.ironLoss).toFixed(1),
    enduranceMin: gear.enduranceMin, enduranceLimit: gear.enduranceLimit },
  max: { thrustToWeight: N_MAX_DESIGN_TW, rotorRpm: +nMax.toFixed(0), thrust_g: +(maxPt.s.T / G * 1000).toFixed(0), pitchUpper: hover.pitchUpper,
    pitchLower: +maxPt.pitchLower.toFixed(2), electricPower_W: +mx.pBus.toFixed(0), motorCurrent: +Math.max(mx.upper.current, mx.lower.current).toFixed(2),
    dutyEndOfFlight: +mx.duty.toFixed(3), motorLoss_W: +(mx.upper.copperLoss + mx.upper.ironLoss).toFixed(1) },
  gear, servoRange, stallOnsetPitchUpper: stallPitch, loads,
  assumptions: ['BEMT mit vereinfachter Polare; Re ~ 5-8e4, Abriss bei kleiner Re unsicher', 'Motor: Gleichstrom-Ersatzmodell, Leerlaufstrom ~ n^0.5',
    `Getriebewirkungsgrad ${DRIVE.gearEff}, ESC ${DRIVE.escEff}, max. Tastgrad ${DRIVE.maxDuty}`, 'Akku: typische LiPo-Kennlinie, Ri 5 mOhm/Zelle, 80 % Nutzung',
    'Massen teilweise geschaetzt (Spalte source)', 'Untere Ebene immer auf Drehmomentgleichgewicht geregelt'],
};
fs.writeFileSync(path.join(OUT, 'Auslegung.json'), JSON.stringify(result, null, 2));
const csv = (name, rows) => fs.writeFileSync(path.join(OUT, name), '﻿' + [Object.keys(rows[0]).join(','), ...rows.map((r) => Object.values(r).join(','))].join('\n') + '\n');
csv('Schwebepunkt_ueber_Pitch.csv', hoverSweep); csv('Uebersetzung_Varianten.csv', ratioSweep);
csv('Pitchbereich.csv', pitchSweep); csv('Pruefmatrix.csv', matrix);
console.log(JSON.stringify({ masse_g: result.mass.total_g, hover: result.hover, max: result.max, gear, servoRange, stallPitch, loads }, null, 1));
