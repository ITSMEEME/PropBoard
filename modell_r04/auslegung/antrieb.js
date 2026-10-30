/* R04-Testmodell – Antriebsmodell: Akku -> ESC -> BLDC-Motor -> Stirnradstufe -> Rotor.
 * Gleichstrom-Ersatzmodell des Motors (KV, Leitungswiderstand, drehzahlabhaengiger Leerlaufstrom).
 * Herstellerwerte EMAX ECO II 2306 KV1900 (Datenblatt): R 62 mOhm, Leerlauf 1,3 A bei 10 V.
 * Alle uebrigen Werte sind Annahmen und im Prueflauf zu messen. Einheiten SI.
 */
(function (root) {
  'use strict';

  const MOTOR_ECO2_2306_1900 = {
    name: 'EMAX ECO II 2306 KV1900', kv: 1900, R: 0.062, i0Ref: 1.3, i0RefVolt: 10,
    i0Exp: 0.5,          // Annahme: Leerlaufstrom ~ (Drehzahl)^0.5 (Eisen- und Lagerverluste)
    peakCurrent: 46, mass: 0.0302, poles: 14,
  };
  const BATTERY_TATTU_1550_6S = {
    name: 'Tattu 1550 mAh 6S', cells: 6, capacityAh: 1.55, rCell: 0.005, rWiring: 0.005,   // Ri Annahme
    mass: 0.255, usable: 0.8,                                                              // Masse Annahme, wiegen
    // Leerlaufspannung je Zelle ueber Ladezustand (typische LiPo-Kennlinie, Annahme)
    ocv: [[0, 3.30], [0.1, 3.55], [0.2, 3.66], [0.3, 3.72], [0.4, 3.76], [0.5, 3.80], [0.6, 3.84], [0.7, 3.90], [0.8, 3.98], [0.9, 4.08], [1, 4.20]],
  };
  const DEFAULT_DRIVE = { gearEff: 0.92, escEff: 0.95, maxDuty: 0.95 };

  function interp(tab, x) {
    if (x <= tab[0][0]) return tab[0][1];
    for (let i = 1; i < tab.length; i++) if (x <= tab[i][0]) {
      const [x0, y0] = tab[i - 1], [x1, y1] = tab[i]; return y0 + (y1 - y0) * (x - x0) / (x1 - x0);
    }
    return tab[tab.length - 1][1];
  }

  function kt(m) { return 60 / (2 * Math.PI * m.kv); }
  function i0(m, rpm) { const ref = m.kv * m.i0RefVolt; return m.i0Ref * Math.pow(Math.max(rpm, 1) / ref, m.i0Exp); }

  /* Motorarbeitspunkt fuer Rotordrehzahl [U/min] und Rotormoment [Nm] bei Uebersetzung i. */
  function motorPoint(m, rotorRpm, rotorTorque, ratio, drive = DEFAULT_DRIVE) {
    const rpm = rotorRpm * ratio, q = Math.max(rotorTorque, 0) / (ratio * drive.gearEff);
    const I = rotorRpm > 0 ? q / kt(m) + i0(m, rpm) : 0;
    const V = rpm / m.kv + I * m.R;
    const pMech = q * rpm * 2 * Math.PI / 60, pIn = V * I;
    return { rpm, torque: q, current: I, voltage: V, pMech, pIn, eff: pIn > 0 ? pMech / pIn : 0,
      copperLoss: I * I * m.R, ironLoss: i0(m, rpm) * rpm / m.kv, overPeak: I > m.peakCurrent };
  }

  function packVoltage(b, soc, current) {
    return b.cells * interp(b.ocv, soc) - current * (b.cells * b.rCell + b.rWiring);
  }

  /* Elektrischer Systemarbeitspunkt beider Motoren am Akku bei Ladezustand soc. */
  function systemPoint(m, b, upper, lower, ratio, soc, drive = DEFAULT_DRIVE, auxPower = 2) {
    const mu = motorPoint(m, upper.rpm, upper.Q, ratio, drive), ml = motorPoint(m, lower.rpm, lower.Q, ratio, drive);
    const pBus = (mu.pIn + ml.pIn) / drive.escEff + auxPower;
    let I = pBus / (b.cells * 3.7);
    for (let k = 0; k < 30; k++) { const V = packVoltage(b, soc, I); I = pBus / Math.max(V, 1); }
    const Vbus = packVoltage(b, soc, I);
    const duty = Math.max(mu.voltage, ml.voltage) / Vbus;
    return { upper: mu, lower: ml, pBus, batteryCurrent: I, busVoltage: Vbus, duty,
      feasible: duty <= drive.maxDuty && !mu.overPeak && !ml.overPeak };
  }

  /* Flugzeit bei konstantem Arbeitspunkt bis Nutzungsgrenze oder Stellreserve erschoepft. */
  function enduranceSeconds(m, b, upper, lower, ratio, drive = DEFAULT_DRIVE) {
    let soc = 1, t = 0; const dt = 1, socMin = 1 - b.usable;
    while (soc > socMin && t < 3600) {
      const s = systemPoint(m, b, upper, lower, ratio, soc, drive);
      if (!s.feasible) return { seconds: t, limit: 'Stellreserve' };
      soc -= s.batteryCurrent * dt / 3600 / b.capacityAh; t += dt;
    }
    return { seconds: t, limit: t >= 3600 ? 'Zeitlimit' : 'Nutzkapazitaet' };
  }

  const api = { MOTOR_ECO2_2306_1900, BATTERY_TATTU_1550_6S, DEFAULT_DRIVE, kt, i0, motorPoint, packVoltage, systemPoint, enduranceSeconds };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.R04Antrieb = api;
})(typeof window !== 'undefined' ? window : globalThis);
