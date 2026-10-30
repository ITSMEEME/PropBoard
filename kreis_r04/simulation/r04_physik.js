/* R04 Simulator – Blattelement-Impuls-Theorie (BEMT) fuer zwei gegenlaeufige Ringrotoren.
 * Vereinfachtes Modell, KEIN Nachweis. Schwebeflug, stationaer, axialsymmetrisch gemittelt.
 * Oberer Rotor ungestoert; unterer Rotor im kontrahierten Nachlauf des oberen
 * (Aktuatorscheiben-Entwicklung v(h) = v*(1 + h/sqrt(h^2+R^2)), Drall mit Drehimpulserhaltung).
 * Rueckwirkung des unteren auf den oberen Rotor, Blattpassagen, Bodeneffekt und Vorwaertsflug fehlen.
 * Einheiten SI, Winkel in Grad an der Schnittstelle.
 */
(function (root) {
  'use strict';
  const DEG = Math.PI / 180, G = 9.81;

  const DEFAULTS = {
    blades: 8, rIn: 0.15, rOut: 0.75, chord: 0.12, thickness: 0.12, twist: 0,
    pitchUpper: 12, pitchLower: 12, rpm: 850, spacing: 0.24,
    rho: 1.225, nu: 1.5e-5, elements: 40,
  };

  /* Vereinfachte Profilpolare, symmetrisches NACA-00xx-artiges Profil.
   * Linearer Bereich 0.9*2*pi, Abrisswinkel abhaengig von Re und Dicke, danach Uebergang zur ebenen Platte. */
  function stallAngle(re, tc) {
    const s = Math.min(1, Math.max(0, Math.log10(Math.max(re, 1) / 1e5)));
    return Math.min(18, Math.max(5, 8 + 6 * s + (tc - 0.12) * 50));
  }

  function polar(alphaDeg, re, tc) {
    const a = alphaDeg * DEG, sgn = Math.sign(a) || 1, aa = Math.abs(a);
    const as = stallAngle(re, tc) * DEG, cla = 0.9 * 2 * Math.PI;
    const cd0 = 0.0055 * (1 + 2 * tc + 60 * tc ** 4) * Math.pow(Math.max(re, 2e4) / 1e6, -0.2) + 0.0005;
    const flatCl = 2 * Math.sin(aa) * Math.cos(aa), flatCd = 1.98 * Math.sin(aa) ** 2 + cd0;
    let cl, cd, stalled = aa > as;
    if (!stalled) {
      cl = cla * aa; cd = cd0 + 0.012 * cl * cl;
    } else {
      const clMax = cla * as, t = Math.min(1, (aa - as) / (8 * DEG));
      const post = clMax * (1 - 0.3 * t);
      cl = Math.max(post * Math.exp(-Math.max(0, aa - as - 8 * DEG) / (25 * DEG)), flatCl);
      cd = Math.max(cd0 + 0.012 * clMax * clMax + (flatCd - cd0) * t, cd0);
    }
    return { cl: sgn * cl, cd, stalled };
  }

  /* Verwindung linear ueber die Spannweite, Bezug Spannweitenmitte (R04: (r - 0,45) / 0,6). */
  function twistShape(p, r) { return (r - (p.rIn + p.rOut) / 2) / (p.rOut - p.rIn); }

  function prandtl(B, dist, r, phi) {
    const s = Math.abs(Math.sin(phi));
    if (s < 1e-4) return 1;
    const f = B * dist / (2 * r * s);
    return (2 / Math.PI) * Math.acos(Math.min(1, Math.exp(-f)));
  }

  /* Ein Ringrotor. ext(r) liefert {v0, wt}: axiale Zustroemung und Fremddrall (erhoeht Relativgeschwindigkeit). */
  function solveRotor(p, pitchDeg, ext) {
    const { blades: B, rIn, rOut, chord: c, rho, nu } = p, n = p.elements;
    const omega = p.rpm * 2 * Math.PI / 60, dr = (rOut - rIn) / n;
    const out = { r: [], v: [], w: [], v0: [], wt: [], phi: [], alpha: [], cl: [], cd: [], dT: [], dQ: [], re: [], stalled: [], F: [] };
    let T = 0, Q = 0, stalledLen = 0;
    for (let k = 0; k < n; k++) {
      const r = rIn + (k + 0.5) * dr;
      const theta = (pitchDeg + p.twist * twistShape(p, r)) * DEG;
      const e = ext ? ext(r) : { v0: 0, wt: 0 };
      let w = 0, last = null;
      const evalV = (v) => {
        let res;
        for (let it = 0; it < 6; it++) {
          const up = e.v0 + v, ut = omega * r + e.wt - w;
          const phi = Math.atan2(up, ut), vrel2 = up * up + ut * ut;
          const alpha = theta - phi, re = Math.sqrt(vrel2) * c / nu;
          const pol = p.polarFunction ? p.polarFunction(alpha / DEG, re, p.thickness) : polar(alpha / DEG, re, p.thickness);
          const F = Math.max(0.05, prandtl(B, rOut - r, r, phi) * prandtl(B, r - rIn, r, phi));
          const q = 0.5 * rho * vrel2 * B * c;
          const dTbe = q * (pol.cl * Math.cos(phi) - pol.cd * Math.sin(phi));
          const dQbe = q * (pol.cl * Math.sin(phi) + pol.cd * Math.cos(phi)) * r;
          const flux = 4 * Math.PI * r * rho * F * Math.max(Math.abs(up), 0.05);
          const wNew = dQbe / (flux * r);
          res = { up, ut, phi, alpha, re, pol, F, dTbe, dQbe, mom: flux * v };
          if (Math.abs(wNew - w) < 1e-6) break;
          w = 0.5 * w + 0.5 * wNew;
        }
        last = res;
        return res.mom - res.dTbe;
      };
      let lo = -e.v0 - 40, hi = 200;
      let flo = evalV(lo), fhi = evalV(hi);
      let v;
      if (flo > 0) v = lo; else if (fhi < 0) v = hi;
      else {
        for (let it = 0; it < 60; it++) {
          const mid = 0.5 * (lo + hi), fm = evalV(mid);
          if (fm > 0) hi = mid; else lo = mid;
          if (hi - lo < 1e-5) break;
        }
        v = 0.5 * (lo + hi);
      }
      evalV(v);
      const s = last;
      out.r.push(r); out.v.push(v); out.w.push(w); out.v0.push(e.v0); out.wt.push(e.wt);
      out.phi.push(s.phi / DEG); out.alpha.push(s.alpha / DEG);
      out.cl.push(s.pol.cl); out.cd.push(s.pol.cd); out.dT.push(s.dTbe); out.dQ.push(s.dQbe);
      out.re.push(s.re); out.stalled.push(s.pol.stalled); out.F.push(s.F);
      T += s.dTbe * dr; Q += s.dQbe * dr; if (s.pol.stalled) stalledLen += dr;
    }
    out.T = T; out.Q = Q; out.P = Q * omega; out.omega = omega;
    out.stalledFraction = stalledLen / (rOut - rIn); out.dr = dr;
    return out;
  }

  function interp(xs, ys, x) {
    if (x <= xs[0]) return ys[0];
    if (x >= xs[xs.length - 1]) return ys[ys.length - 1];
    let i = 1; while (xs[i] < x) i++;
    const t = (x - xs[i - 1]) / (xs[i] - xs[i - 1]);
    return ys[i - 1] * (1 - t) + ys[i] * t;
  }

  /* Nachlauf des oberen Rotors in der Ebene des unteren Rotors. */
  function wakeModel(p, upper) {
    const s = 1 + p.spacing / Math.sqrt(p.spacing ** 2 + p.rOut ** 2);   // Geschwindigkeitsfaktor
    const k = 1 / Math.sqrt(s);                                          // radiale Kontraktion
    const lo = p.rIn * k, hi = p.rOut * k;
    return {
      factor: s, contraction: k, rIn: lo, rOut: hi,
      /* Scherschicht am Nachlaufrand: weicher Uebergang ueber edge (statt Sprung). */
      edge: 0.08 * (hi - lo),
      at(r) {
        const e = this.edge, x = Math.min((r - lo + e / 2) / e, (hi + e / 2 - r) / e);
        if (x <= 0) return { v0: 0, wt: 0 };
        const blend = x >= 1 ? 1 : x * x * (3 - 2 * x);
        const ru = Math.min(Math.max(r / k, p.rIn), p.rOut);
        return { v0: blend * s * interp(upper.r, upper.v, ru), wt: blend * s * interp(upper.r, upper.w, ru) * (ru / r) };
      },
    };
  }

  function simulate(input) {
    const p = Object.assign({}, DEFAULTS, input);
    const upper = solveRotor(p, p.pitchUpper, null);
    const wake = wakeModel(p, upper);
    const lower = solveRotor(p, p.pitchLower, (r) => wake.at(r));
    const T = upper.T + lower.T, P = upper.P + lower.P;
    const area = Math.PI * (p.rOut ** 2 - p.rIn ** 2);
    const pIdeal = T > 0 ? Math.pow(T, 1.5) / Math.sqrt(2 * p.rho * area) : 0;
    const omega = upper.omega;
    return {
      params: p, upper, lower, wake, T, P, Q: upper.Q - lower.Q,
      kgEquivalent: T / G, area, pIdeal, figureOfMerit: P > 0 ? pIdeal / P : 0,
      diskLoading: T / area, tipSpeed: omega * Math.hypot(p.rOut, p.chord / 2),
      tipMach: omega * p.rOut / 340, rRef: 0.6 * p.rOut, accelRef: omega * omega * 0.6 * p.rOut / G,
      stalledFraction: 0.5 * (upper.stalledFraction + lower.stalledFraction),
      wingArea: 2 * p.blades * (p.rOut - p.rIn) * p.chord,
    };
  }

  /* Pitch der unteren Ebene, bei dem beide Drehmomente gleich sind (kein Giermoment). */
  function balanceLowerPitch(input) {
    let lo = -5, hi = 35;
    const f = (th) => { const s = simulate(Object.assign({}, input, { pitchLower: th })); return s.lower.Q - s.upper.Q; };
    let flo = f(lo), fhi = f(hi);
    if (flo * fhi > 0) return null;
    for (let i = 0; i < 40; i++) {
      const m = 0.5 * (lo + hi), fm = f(m);
      if (fm * flo > 0) { lo = m; flo = fm; } else hi = m;
    }
    return 0.5 * (lo + hi);
  }

  function sweep(input, key, values, map) {
    return values.map((x) => {
      const s = simulate(map ? map(input, x) : Object.assign({}, input, { [key]: x }));
      return { x, total: s.T, upper: s.upper.T, lower: s.lower.T, power: s.P };
    });
  }

  const api = { DEFAULTS, G, polar, stallAngle, twistShape, simulate, balanceLowerPitch, sweep };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.R04Physik = api;
})(typeof window !== 'undefined' ? window : globalThis);
