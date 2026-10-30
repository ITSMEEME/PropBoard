// Plausibilitaetspruefungen des R04-Simulators:  node pruefen.js
'use strict';
const P = require('./r04_physik.js'), { Cascade } = require('./lbm.js');
const checks = [];
const check = (name, ok, info) => { checks.push(ok); console.log(`${ok ? 'OK  ' : 'FAIL'} ${name}  ${info}`); };

const s = P.simulate({});
let mom = 0;
s.upper.r.forEach((r, i) => { mom += 4 * Math.PI * r * 1.225 * s.upper.F[i] * s.upper.v[i] * Math.abs(s.upper.v[i]) * s.upper.dr; });
check('Impulsbilanz oberer Rotor', Math.abs(mom - s.upper.T) / s.upper.T < 1e-3, `${mom.toFixed(2)} N vs ${s.upper.T.toFixed(2)} N`);
check('Guetegrad < 1', s.figureOfMerit > 0 && s.figureOfMerit < 1, s.figureOfMerit.toFixed(3));
check('kein Auftrieb ohne Drehzahl', Math.abs(P.simulate({ rpm: 0 }).T) < 1e-6, '');
check('kein Auftrieb bei 0 Grad Pitch', Math.abs(P.simulate({ pitchUpper: 0, pitchLower: 0 }).T) < 1, '');
const t1 = P.simulate({ rpm: 600 }).T, t2 = P.simulate({ rpm: 1200 }).T;
check('Auftrieb ~ n^2 ohne Abriss', Math.abs(t2 / t1 - 4) < 0.2, `Faktor ${(t2 / t1).toFixed(2)}`);
const th = P.balanceLowerPitch({}), b = P.simulate({ pitchLower: th });
check('Drehmomentausgleich', Math.abs(b.upper.Q - b.lower.Q) < 0.01, `Pitch unten ${th.toFixed(2)} Grad`);

const cas = new Cascade({ nx: 150, ny: 200, chordCells: 24, spacingCells: 75, levelGapCells: 48,
  rows: [{ pitch: 12, dir: 1 }, { pitch: 12, dir: -1 }], tc: 0.12, teHalf: 0.4 / 120, uBlade: 0.08, nu: 0.08 * 24 / 5000, sponge: 28 });
for (let i = 0; i < 2000; i++) cas.step();
const bad = cas.rho.filter((v) => !(v > 0.8 && v < 1.2)).length;
check('LBM stabil (2000 Schritte, Re 5000)', bad === 0, `${bad} Zellen ausserhalb 0.8..1.2`);
check('LBM Abwaertsstroemung', cas.meanDownwash() < 0, (cas.meanDownwash() / 0.08).toFixed(3) + ' U');
process.exit(checks.every(Boolean) ? 0 : 1);
