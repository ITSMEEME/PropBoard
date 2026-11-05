/* Globaler Multirotor-Flugsimulator – Physikkern (SI-Einheiten, z nach oben).
 * Welt: x/y horizontal, z oben, Boden z = 0. Koerper: CAD-Achsen (x vorn, y links, z oben), Ursprung im Schwerpunkt.
 * Bestandteile: 6-DOF-Starrkoerper, Blattelement-Impuls-Rotormodell (Zustrom, Vorwaertsflug, Wirbelringstadium,
 * Stroemungsabriss, Bodeneffekt, Koax-/Nachlaufinterferenz, Abschattung), MN1330/V200A-Antrieb mit Drehzahlregler,
 * Strom-/Temperaturgrenzen, 24S-Akku mit Einzelzellen (Streuung, RC-Glied, Temperatur), Wind (Profil, Dryden-Turbulenz, Boeen),
 * Bodenkontakt (Feder/Daempfer/Reibung) und kaskadierter Flugregler mit Steuerzuordnung und Ausfallbehandlung.
 * Kalibrierung: statische CT/CP wie D13 (NS52x20-Referenz, Steigungsskalierung). Keine Validierung am Fahrzeug.
 */
(function(root){
'use strict';
const G = 9.80665, DEG = Math.PI/180;
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const add = (a, b) => [a[0]+b[0], a[1]+b[1], a[2]+b[2]], sub = (a, b) => [a[0]-b[0], a[1]-b[1], a[2]-b[2]];
const scl = (a, k) => [a[0]*k, a[1]*k, a[2]*k], dot = (a, b) => a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
const crs = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
const len = a => Math.sqrt(dot(a, a));
// Quaternion [w,x,y,z], Koerper -> Welt
function qrot(q, v) { const [w, x, y, z] = q, t = scl(crs([x, y, z], v), 2); return add(add(v, scl(t, w)), crs([x, y, z], t)); }
function qinv(q, v) { return qrot([q[0], -q[1], -q[2], -q[3]], v); }
function qmul(a, b) { return [a[0]*b[0]-a[1]*b[1]-a[2]*b[2]-a[3]*b[3], a[0]*b[1]+a[1]*b[0]+a[2]*b[3]-a[3]*b[2], a[0]*b[2]-a[1]*b[3]+a[2]*b[0]+a[3]*b[1], a[0]*b[3]+a[1]*b[2]-a[2]*b[1]+a[3]*b[0]]; }
function qnorm(q) { const l = Math.hypot(...q); return q.map(v => v/l); }
function qachse(ax, ang) { const s = Math.sin(ang/2); return [Math.cos(ang/2), ax[0]*s, ax[1]*s, ax[2]*s]; }
function euler(q) { const [w, x, y, z] = q; return {roll: Math.atan2(2*(w*x+y*z), 1-2*(x*x+y*y)), pitch: Math.asin(clamp(2*(w*y-z*x), -1, 1)), yaw: Math.atan2(2*(w*z+x*y), 1-2*(y*y+z*z))}; }
function inv3(m) {
  const [a, b, c, d, e, f, g, h, i] = m, A = e*i-f*h, B = -(d*i-f*g), C = d*h-e*g, det = a*A+b*B+c*C;
  return [A/det, -(b*i-c*h)/det, (b*f-c*e)/det, B/det, (a*i-c*g)/det, -(a*f-c*d)/det, C/det, -(a*h-b*g)/det, (a*e-b*d)/det];
}
const mv3 = (m, v) => [m[0]*v[0]+m[1]*v[1]+m[2]*v[2], m[3]*v[0]+m[4]*v[1]+m[5]*v[2], m[6]*v[0]+m[7]*v[1]+m[8]*v[2]];
function invN(M) { // Gauss-Jordan, kleine quadratische Matrix (Array von Zeilen)
  const n = M.length, A = M.map((r, i) => [...r, ...Array.from({length: n}, (_, j) => +(i === j))]);
  for (let c = 0; c < n; c++) {
    let p = c; for (let r = c+1; r < n; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
    if (Math.abs(A[p][c]) < 1e-12) return null; [A[c], A[p]] = [A[p], A[c]];
    const k = A[c][c]; for (let j = 0; j < 2*n; j++) A[c][j] /= k;
    for (let r = 0; r < n; r++) if (r !== c) { const f = A[r][c]; if (f) for (let j = 0; j < 2*n; j++) A[r][j] -= f*A[c][j]; }
  }
  return A.map(r => r.slice(n));
}
// reproduzierbarer Zufall
function rng(seed) { let s = seed >>> 0; const u = () => { s += 0x6D2B79F5; let t = s; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  let spare = null; u.gauss = () => { if (spare !== null) { const r = spare; spare = null; return r; } let a, b, q; do { a = 2*u()-1; b = 2*u()-1; q = a*a+b*b; } while (q >= 1 || q === 0); const f = Math.sqrt(-2*Math.log(q)/q); spare = b*f; return a*f; }; return u; }

// ------------------------------------------------------------------ Atmosphaere
function atmosphaere(hoehe_m, temp_C) {
  const p = 101325*Math.pow(1-2.25577e-5*hoehe_m, 5.25588), T = temp_C + 273.15;
  return {rho: p/(287.05*T), p, T, a: Math.sqrt(1.4*287.05*T)};
}

// ------------------------------------------------------------------ Wind
class Wind {
  constructor(r, opt = {}) { this.r = r; this.set(opt); this.u = [0, 0, 0]; this.grad = [0, 0]; this.boe = null; this.naechsteBoe = 4; this.t = 0; this.aktuell = [0, 0, 0]; }
  set(o) { this.mittel = o.mittel ?? this.mittel ?? 0; this.richtung = o.richtung ?? this.richtung ?? 0; this.turbulenz = o.turbulenz ?? this.turbulenz ?? 1; this.boeen = o.boeen ?? this.boeen ?? 0; }
  // Windgeschwindigkeit an Hoehe h (Weltkoordinaten); Profil logarithmisch (z0 = 5 cm), Bezug 10 m
  profil(h) { return this.mittel*Math.log(Math.max(h, 0.3)/0.05)/Math.log(10/0.05); }
  schritt(dt, h, vLuft) {
    this.t += dt; const r = this.r, hf = Math.max(h, 3)/0.3048;          // MIL-F-8785C Niedrighoehe (Fuss)
    const W20 = this.profil(6.1), sw = 0.1*Math.max(W20, 0.5)*this.turbulenz, su = sw/Math.pow(0.177+0.000823*hf, 0.4);
    const Lu = hf/Math.pow(0.177+0.000823*hf, 1.2)*0.3048, Lw = hf*0.3048, V = Math.max(vLuft, W20, 1);
    const sig = [su, su, sw], L = [Lu, Lu, Lw];
    for (let k = 0; k < 3; k++) { const a = V/L[k]; this.u[k] += -a*this.u[k]*dt + sig[k]*Math.sqrt(2*a*dt)*r.gauss(); }
    const ag = V/Math.max(Lw, 2); for (let k = 0; k < 2; k++) this.grad[k] += -ag*this.grad[k]*dt + 0.6*sw/Math.max(Lw, 2)*Math.sqrt(2*ag*dt)*r.gauss();
    // diskrete 1-cos-Boeen
    let b = [0, 0, 0];
    if (this.boeen > 0) {
      if (!this.boe && this.t > this.naechsteBoe) { const ri = this.richtung*DEG + (r()-0.5)*1.4, A = this.boeen*(0.5+0.5*r());
        this.boe = {t0: this.t, T: 1.2+2.8*r(), v: [A*Math.cos(ri), A*Math.sin(ri), A*0.25*(r()-0.5)]}; }
      if (this.boe) { const s = (this.t-this.boe.t0)/this.boe.T; if (s >= 1) { this.boe = null; this.naechsteBoe = this.t + 3 + 10*r(); } else b = scl(this.boe.v, 0.5*(1-Math.cos(2*Math.PI*s))); }
    }
    const m = this.profil(h), ri = this.richtung*DEG;
    // Turbulenzachsen an der mittleren Windrichtung ausgerichtet
    const c = Math.cos(ri), s = Math.sin(ri);
    this.aktuell = [m*c + this.u[0]*c - this.u[1]*s + b[0], m*s + this.u[0]*s + this.u[1]*c + b[1], this.u[2] + b[2]];
    return this.aktuell;
  }
  // ortsabhaengige Vertikalboe (Gradient) fuer Rotorposition in Welt-xy relativ zum Schwerpunkt
  lokal(dxy) { const w = this.aktuell; return [w[0], w[1], w[2] + this.grad[0]*dxy[0] + this.grad[1]*dxy[1]]; }
}

// ------------------------------------------------------------------ Akku
const OCV = [[0, 3.27], [0.05, 3.50], [0.1, 3.61], [0.15, 3.67], [0.2, 3.70], [0.3, 3.74], [0.4, 3.78], [0.5, 3.82], [0.6, 3.87], [0.7, 3.93], [0.8, 4.00], [0.9, 4.08], [1.0, 4.20]];
function ocv(s) { s = clamp(s, 0, 1); let i = 1; while (OCV[i][0] < s) i++; const [a, va] = OCV[i-1], [b, vb] = OCV[i]; return va + (vb-va)*(s-a)/(b-a); }
class Akku {
  constructor(r, o) {
    this.S = o.S || 24; this.P = o.P || 2; this.Ah = o.Ah || 22; this.Whkg = o.Whkg || 165; this.T_amb = o.T_amb ?? 20; this.streuung = o.streuung ?? 1;
    this.masse = this.S*this.P*this.Ah*3.7/this.Whkg;
    const R0 = 0.0018*22/this.Ah, R1 = 0.0012*22/this.Ah, tau = 25, mc = this.masse/(this.S*this.P);
    this.zellen = Array.from({length: this.S}, () => ({
      cap: this.Ah*this.P*(1 + 0.015*this.streuung*r.gauss()), R0: R0*(1 + 0.08*this.streuung*Math.abs(r.gauss()))/this.P,
      R1: R1/this.P, C1: tau/(R1/this.P), soc: clamp((o.soc0 ?? 1)*(1 + 0.004*this.streuung*r.gauss()), 0, 1), vrc: 0, T: o.T0 ?? this.T_amb,
      m: mc*this.P, hA: 0.06*Math.pow(this.Ah/22, 0.66)*this.P}));
    this.r = r; this.rausch = 0; this.I = 0; this.U = this.leerlauf(); this.reserve = o.reserve ?? 0.15; this.Ah_entnommen = 0; this.Wh_entnommen = 0;
  }
  leerlauf() { return this.zellen.reduce((s, z) => s + ocv(z.soc), 0); }
  R0T(z) { return z.R0*Math.exp(2800*(1/(z.T+273.15) - 1/298.15)); }
  kapT(z) { return z.cap*(z.T < 25 ? 1 - 0.006*(25-z.T) : 1); }
  spannung(I) { let U = 0; for (const z of this.zellen) U += ocv(z.soc) - I*this.R0T(z) - z.vrc; return U + this.rausch; }
  zellSpannungen(I) { return this.zellen.map(z => ocv(z.soc) - I*this.R0T(z) - z.vrc); }
  schritt(I, dt) {
    this.I = I;
    for (const z of this.zellen) {
      z.soc -= I*dt/(3600*this.kapT(z));
      z.vrc += dt*(I/z.C1 - z.vrc/(z.R1*z.C1));
      const q = I*I*(this.R0T(z) + z.R1); z.T += dt*(q - z.hA*(z.T - this.T_amb))/(z.m*1000);
    }
    { const a = Math.exp(-dt/0.05); this.rausch = a*this.rausch + 0.08*Math.sqrt(1 - a*a)*this.r.gauss()*this.streuung; }   // Kontakt-/Welligkeitsanteil (exakt diskretisiert)
    this.U = this.spannung(I); this.Ah_entnommen += I*dt/3600; this.Wh_entnommen += I*this.U*dt/3600;
  }
  // nutzbare Restenergie bis zur Reserve (schwaechste Zelle begrenzt den Strang)
  restWh() {
    let qmin = Infinity; for (const z of this.zellen) qmin = Math.min(qmin, (z.soc - this.reserve)*this.kapT(z));
    if (qmin <= 0) return 0; const zm = this.zellen.reduce((a, z) => a + z.soc, 0)/this.S;
    let e = 0; const n = 12, s0 = this.reserve; for (let i = 0; i < n; i++) e += ocv(s0 + (zm - s0)*(i+0.5)/n)/n;
    return qmin*e*this.S;
  }
  get soc() { return this.zellen.reduce((a, z) => a + z.soc, 0)/this.S; }
  get socMin() { return Math.min(...this.zellen.map(z => z.soc)); }
  get Tmax() { return Math.max(...this.zellen.map(z => z.T)); }
}

// ------------------------------------------------------------------ Rotor (Blattelement + Impuls)
class Rotor {
  constructor(md, rd, A0) {
    this.R = md.d_m/2; this.A = Math.PI*this.R*this.R; this.s = rd.dreh; this.lage = rd.lage; this.nr = rd.nr; this.arm = rd.arm;
    const k = (md.steigung_in/md.d_in)/(A0.p_ref_in/A0.d_ref_in);
    this.CTp = A0.ct_ref*k; this.CPp = A0.cp_ref*Math.pow(k, 1.5);
    this.CT0 = 4*this.CTp/Math.pow(Math.PI, 3); this.CP0 = 4*this.CPp/Math.pow(Math.PI, 4);
    this.th = Math.atan(md.steigung_in/(0.75*Math.PI*md.d_in)) + 4*DEG;  // geometrische Steigung 75 % + Profil-Nullauftrieb
    const lh = Math.sqrt(this.CT0/2); this.sa2 = this.CT0/(this.th/3 - lh/2); this.sigma = 2*this.sa2/5.73;
    this.kappa = 1.15; this.Cd0 = 8*(this.CP0 - this.kappa*this.CT0*lh)/this.sigma;
    if (this.Cd0 < 0.007) { this.Cd0 = 0.007; this.kappa = Math.max(1.0, (this.CP0 - this.sigma*this.Cd0/8)/(this.CT0*lh)); }
    this.CLmax = 1.25; this.CL_schweben = 6*this.CT0/this.sigma;
    this.J = 0.0425*Math.pow(md.d_m/1.0668, 4.5) + 0.004;
    this.masse = 0.56*Math.pow(md.d_m/1.0668, 2.5);
    this.li = lh; this.vrsRausch = 0; this.aus = {T: 0, Q: 0, F: [0, 0, 0], M: [0, 0, 0], vi: 0, mu: 0, lam: 0, abriss: 0, vrs: 0, ge: 1, CT: 0};
    this.fdl = 1.2*md.abschattung_m2/this.A; this.sys = md.rotoren.some(r => r.lage === 'unten') ? Math.SQRT2 : 1;
  }
  // statischer Schub-/Drehmomentbeiwert bei Stillluft (fuer Regler-Vorsteuerung)
  kT(rho) { return this.CT0*rho*this.A*this.R*this.R; }
  kQ(rho) { return this.CP0*rho*this.A*Math.pow(this.R, 3); }
  /* Om: Drehzahl [rad/s]; v: Anstroemung der Nabe relativ zur Luft im Koerpersystem (Nabe minus Wind) [m/s];
     wz: zusaetzliche Durchstroemung von oben durch fremde Nachlaeufe [m/s]; h: Hoehe der Rotorebene ueber Boden [m] */
  aero(Om, v, wz, h, rho, r, dt) {
    const o = this.aus, R = this.R, VR = Om*R, n = [0, 0, 1];
    if (VR < 2) { Object.assign(o, {T: 0, Q: 0, F: [0, 0, 0], M: [0, 0, 0], vi: 0, mu: 0, lam: 0, abriss: 0, vrs: 0, ge: 1, CT: 0}); return o; }
    const Vc = v[2], vp = [v[0], v[1], 0], Vt = Math.hypot(v[0], v[1]);
    const mu = Vt/VR, lc = (Vc + wz)/VR;
    const CTst = this.CLmax*this.sigma/6;
    let ab = 0, vrs = 0;
    const CTvon = l => { let c = this.sa2*(this.th*(1/3 + mu*mu/2) - (lc + l)/2); if (c > CTst) c = CTst + (c - CTst)*0.25; return Math.max(c, -0.003); };
    // Bodeneffekt (Cheeseman–Bennett), mit Vorwaertsflug abklingend
    const zr = Math.max(h, 0.25*R*1.05);
    const ge = h < 4*R ? 1 - Math.pow(R/(4*zr), 2)/(1 + Math.pow(mu/Math.max(this.li, 1e-3), 2)) : 1;
    // Impuls (Glauert) und Blattelement gemeinsam: Bisektion auf lambda_i
    let lo = 0, hi = 0.6;
    const g = l => l*2*Math.sqrt(mu*mu + (lc + l)*(lc + l)) - ge*CTvon(l);
    if (g(lo) >= 0) hi = 0; else for (let k = 0; k < 40; k++) { const m_ = (lo + hi)/2; if (g(m_) < 0) lo = m_; else hi = m_; }
    let li = (lo + hi)/2;
    if (lc < 0 || Vc < 0) {   // Sinkflug: Wirbelringstadium bzw. Windmuehlenbremszustand (empirisch, Leishman)
      let lv = li;
      for (let k = 0; k < 12; k++) {
        const c = CTvon(lv), lh = Math.sqrt(Math.max(c, 1e-6)/2), x = lc/lh, m = mu/lh;
        let ln = x <= -2 ? lh*(-x/2 - Math.sqrt(x*x/4 - 1)) : lh*(1 - 1.125*x - 1.372*x*x - 1.718*x*x*x - 0.655*x*x*x*x);
        const w = clamp(1 - m/1.2, 0, 1); ln = ge*(w*Math.max(ln, 0) + (1 - w)*li);
        lv = 0.5*lv + 0.5*ln;
        // VRS-Kriterium am Gesamtsystem: Sinkrate ohne Fremdnachlauf gegen v_h des Systems (Koax: sqrt(2)-fach)
        const xs = (Vc/VR)/(lh*this.sys), ms = mu/(lh*this.sys);
        vrs = (xs < -0.25 && xs > -1.9) ? Math.sin(Math.PI*(-xs - 0.25)/1.65)*clamp(1 - ms/1.0, 0, 1) : 0;
      }
      li = lv;
    }
    let CT = CTvon(li); ab = CT >= CTst ? clamp((this.sa2*(this.th*(1/3 + mu*mu/2) - (lc + li)/2) - CTst)/(0.5*CTst), 0, 1) : 0;
    this.li = li;
    // Wirbelringstadium: Schubschwankung und -verlust
    { const a = Math.exp(-dt/0.25); this.vrsRausch = a*this.vrsRausch + Math.sqrt(1 - a*a)*r.gauss(); }
    if (vrs > 0) CT *= 1 - 0.18*vrs + 0.22*vrs*this.vrsRausch;
    const q = rho*this.A*VR*VR, T = CT*q;
    const Cd = this.Cd0 + 0.03*ab + 0.004*mu;
    const CP = this.kappa*CT*li + CT*lc + this.sigma*Cd/8*(1 + 4.65*mu*mu);
    const Q = CP*q*R;
    // Kraftvektor: Schub entlang Achse, rueckwaerts geneigt (Blattschlag steifer Propeller), Profil-H-Kraft
    const lt = lc + li, beta = 0.25*2*mu*(4*this.th/3 - lt)/(1 - mu*mu/2);
    const H = this.sigma*Cd*mu/4*q, e = Vt > 1e-3 ? scl(vp, 1/Vt) : [0, 0, 0];
    const dl = this.fdl/(1 + Math.pow(mu/Math.max(lt, 1e-3), 2));          // Abschattung durch Ausleger/Regler im Abwind
    const F = add(scl(n, T*Math.cos(beta)*(1 - dl)), scl(e, -(T*Math.sin(beta) + H)));
    // Momente aus ungleicher Scheibenbelastung: Nickmoment (Zustrom-Schraeglage) und Rollmoment (vorlaufendes Blatt)
    const kSk = 0.10*Math.min(mu/Math.max(lt, 0.01), 1.5), kVl = 0.12*mu/0.3;
    const M = add(scl(crs(e, n), kSk*T*R), scl(e, -this.s*Math.min(kVl, 0.2)*T*R));
    Object.assign(o, {T, Q, F, M, vi: li*VR, mu, lam: lt, abriss: ab, vrs, ge, CT, CL: 6*CT/this.sigma, mach: 0});
    return o;
  }
}

// ------------------------------------------------------------------ Motor + Regler (MN1330 KV40 / V200A)
class Antrieb {
  constructor(D, rotor, T_amb) {
    const m = D.motor; this.Kt = m.kt_fit; this.Rfit = m.r_phase_fit; this.Rcu = m.r_datenblatt; this.I0 = m.i0_fit;
    this.Imax = Math.min(m.max_strom_A, D.regler.spitze_A); this.Idauer = D.regler.dauer_A; this.eta = D.regler.wirkungsgrad;
    this.rotor = rotor; this.J = rotor.J; this.Om = 0; this.Tw = T_amb; this.Th = T_amb; this.Te = T_amb; this.Tamb = T_amb;
    this.I = 0; this.Idc = 0; this.d = 0; this.integ = 0; this.ausgefallen = false; this.grenze = ''; this.Iesc_mittel = 0; this.Qm = 0;
  }
  // Drehzahlregler im Regler (Governor), Sollwert Om_soll; U: Busspannung
  schritt(OmSoll, U, Qlast, vKuehl, dt) {
    if (this.ausgefallen || OmSoll <= 0) { this.d = 0; this.I = 0; this.Qm = 0; this.integ = 0; this.grenze = ''; }   // ausgefallen bzw. Regler entschaerft: Freilauf
    else {
      const e = OmSoll - this.Om; this.integ = clamp(this.integ + e*dt, -40, 40);
      const Ivor = Qlast/this.Kt + this.I0;
      let d = (this.Kt*OmSoll + this.Rfit*Ivor)/Math.max(U, 1) + (0.012*e + 0.06*this.integ)*this.Kt*10/Math.max(U, 1);
      // Temperatur-Derating
      let Ilim = this.Imax; this.grenze = '';
      if (this.Tw > 150) { Ilim *= clamp(1 - (this.Tw - 150)/30, 0, 1); this.grenze = 'Motortemperatur'; }
      if (this.Te > 100) { Ilim *= clamp(1 - (this.Te - 100)/20, 0, 1); this.grenze = 'Reglertemperatur'; }
      d = clamp(d, 0, 1); if (d >= 0.999) this.grenze = this.grenze || 'Spannungsgrenze';
      let I = (d*U - this.Kt*this.Om)/this.Rfit;
      if (I > Ilim) { I = Ilim; d = (this.Kt*this.Om + I*this.Rfit)/Math.max(U, 1); this.grenze = this.grenze || 'Strombegrenzung'; }
      if (I < -40) { I = -40; d = clamp((this.Kt*this.Om - 40*this.Rfit)/Math.max(U, 1), 0, 1); }   // aktives Bremsen begrenzt
      if (e < -5 && d <= 0) this.integ *= 0.98;
      this.d = d; this.I = I;
      const I0e = this.I0*Math.min(1, this.Om/40);
      this.Qm = this.Kt*(I - I0e);
    }
    this.Om = Math.max(0, this.Om + (this.Qm - Qlast)*dt/this.J);
    const Pm = this.d*U*this.I; this.Idc = Pm >= 0 ? Pm/(U*this.eta) : Pm*this.eta/U;
    // Thermik: Wicklung/Stator, Gehaeuse, Regler
    const Pcu = this.I*this.I*this.Rcu*(1 + 0.0039*(this.Tw - 25)), Pfe = this.Kt*this.Om*this.I0*Math.min(1, this.Om/40);
    const Pesc = this.I*this.I*Math.max(this.Rfit - this.Rcu, 0.004) + 0.008*Math.abs(Pm);
    const hA = 2 + 0.9*vKuehl, hE = 1.5 + 0.45*vKuehl;
    this.Tw += dt*(Pcu + Pfe - (this.Tw - this.Th)/0.08)/320;
    this.Th += dt*((this.Tw - this.Th)/0.08 - hA*(this.Th - this.Tamb))/1300;
    this.Te += dt*(Pesc - hE*(this.Te - this.Tamb))/350;
    this.Iesc_mittel += (Math.abs(this.I) - this.Iesc_mittel)*dt/20;
    this.Pv = Pcu + Pfe + Pesc;
  }
  // maximal erreichbare Drehzahl bei Spannung U fuer Last Q ~ kQ Om^2 (stationaer, Vollaussteuerung/Stromgrenze)
  omMax(U, kQ) {
    let lo = 0, hi = U/this.Kt;
    for (let i = 0; i < 30; i++) { const w = (lo+hi)/2, I = kQ*w*w/this.Kt + this.I0; if (I <= this.Imax && this.Kt*w + this.Rfit*I <= U) lo = w; else hi = w; }
    return lo;
  }
}

// ------------------------------------------------------------------ Masse und Traegheit
function massenmodell(md, D, opt, rotoren, akku) {
  const T = [], m = md.massen, nr = md.rotoren.length;
  const box = (mass, p, a, b, c) => T.push({mass, p, I: [mass*(b*b+c*c)/12, mass*(a*a+c*c)/12, mass*(a*a+b*b)/12]});
  const punkt = (mass, p) => T.push({mass, p, I: [0, 0, 0]});
  const zentral = m.struktur_kg - m.motortraeger_kg - m.arme_kg, ap = md.rahmen.apothem_m;
  box(zentral, [0, 0, 0], 2*ap, 2*ap, 0.24);
  md.arme.forEach(a => { punkt(m.motortraeger_kg/md.arme.length, [a.xy[0], a.xy[1], 0.05]); punkt(m.arme_kg/md.arme.length, [a.xy[0]*0.55, a.xy[1]*0.55, 0.03]); });
  md.rotoren.forEach((r, i) => { punkt(D.motor.masse_kg, [r.xy[0], r.xy[1], r.lage === 'oben' ? r.z - 0.05 : r.z + 0.05]); punkt(rotoren[i].masse, [r.xy[0], r.xy[1], r.z]); });
  const rm = md.massen.regler_kg/nr; md.rotoren.forEach(r => punkt(rm, [r.xy[0]*0.6, r.xy[1]*0.6, 0.03]));   // Regler vor dem Motortraeger
  box(m.ausruestung_kg, [0, 0, 0.2], 2*md.bock_x_m, 0.25, 0.1);
  box(akku.masse, [0, 0, opt.akku_z ?? -0.02], 0.36, 0.26, 0.2);
  box(opt.bordnetz_kg ?? 2.0, [0, 0, 0.02], 0.2, 0.2, 0.1);
  const zP = md.plattform_z_m + 0.97*(opt.person_groesse ?? 1.75)/1.75;
  if (opt.nutzlast > 0) T.push({mass: opt.nutzlast, p: [opt.nutzlast_x ?? 0, 0, zP], I: [opt.nutzlast*(3*0.17*0.17 + 1.75*1.75)/12, opt.nutzlast*(3*0.17*0.17 + 1.75*1.75)/12, opt.nutzlast*0.17*0.17/2]});
  const M = T.reduce((s, t) => s + t.mass, 0), cg = scl(T.reduce((s, t) => add(s, scl(t.p, t.mass)), [0, 0, 0]), 1/M);
  const I = [0, 0, 0, 0, 0, 0, 0, 0, 0];
  for (const t of T) { const r = sub(t.p, cg), m_ = t.mass;
    I[0] += t.I[0] + m_*(r[1]*r[1]+r[2]*r[2]); I[4] += t.I[1] + m_*(r[0]*r[0]+r[2]*r[2]); I[8] += t.I[2] + m_*(r[0]*r[0]+r[1]*r[1]);
    I[1] -= m_*r[0]*r[1]; I[2] -= m_*r[0]*r[2]; I[5] -= m_*r[1]*r[2]; }
  I[3] = I[1]; I[6] = I[2]; I[7] = I[5];
  const anteile = {struktur: m.struktur_kg, ausruestung: m.ausruestung_kg, regler: m.regler_kg, motoren: nr*D.motor.masse_kg,
    propeller: rotoren.reduce((s, r) => s + r.masse, 0), akku: akku.masse, bordnetz: opt.bordnetz_kg ?? 2.0, nutzlast: opt.nutzlast || 0};
  return {M, cg, I, Iinv: inv3(I), anteile, zPerson: zP};
}

// ------------------------------------------------------------------ Simulation
const STANDARD = {nutzlast: 100, akku_S: 24, akku_P: 2, akku_Ah: 22, akku_Whkg: 165, temp_C: 20, hoehe_m: 0, wind: 0, windrichtung: 0, turbulenz: 1, boeen: 0, seed: 7, streuung: 1, reserve: 0.15, soc0: 1};

class Sim {
  constructor(D, schluessel, opt = {}) {
    this.D = D; this.md = D.modelle[schluessel]; if (!this.md) throw Error('Modell unbekannt: ' + schluessel);
    this.opt = Object.assign({}, STANDARD, opt); const o = this.opt;
    this.r = rng(o.seed); this.atm = atmosphaere(o.hoehe_m, o.temp_C);
    this.rotoren = this.md.rotoren.map(rd => new Rotor(this.md, rd, D.antrieb));
    this.akku = new Akku(this.r, {S: o.akku_S, P: o.akku_P, Ah: o.akku_Ah, Whkg: o.akku_Whkg, T_amb: o.temp_C, streuung: o.streuung, reserve: o.reserve, soc0: o.soc0});
    this.mm = massenmodell(this.md, D, o, this.rotoren, this.akku);
    this.antriebe = this.rotoren.map(r => new Antrieb(D, r, o.temp_C));
    this.wind = new Wind(this.r, {mittel: o.wind, richtung: o.windrichtung, turbulenz: o.turbulenz, boeen: o.boeen});
    const cg = this.mm.cg;
    this.rpos = this.md.rotoren.map(r => sub([r.xy[0], r.xy[1], r.z], cg));
    // Kontaktpunkte: Sohlen (Fuesse) + Strukturpunkte (Blattspitzen, Rahmenoberseite, Person)
    this.kontakte = this.md.fuesse.map(f => ({p: sub([f[0], f[1], this.md.boden_z_m], cg), art: 'fuss', last: 0}));
    this.rotoren.forEach((ro, i) => { for (let k = 0; k < 8; k++) { const a = k*Math.PI/4, p = this.rpos[i]; this.kontakte.push({p: [p[0] + ro.R*Math.cos(a), p[1] + ro.R*Math.sin(a), p[2]], art: 'blatt', rotor: i, last: 0}); } });
    this.md.arme.forEach(a => this.kontakte.push({p: sub([a.xy[0], a.xy[1], -0.03], cg), art: 'struktur', last: 0}));
    if (o.nutzlast > 0) this.kontakte.push({p: sub([0, 0, this.mm.zPerson + 0.8], cg), art: 'person', last: 0});
    // Zustand: Schwerpunkt so, dass die Sohlen auf dem Boden stehen
    this.x = [0, 0, -this.kontakte[0].p[2] - 0.0005]; this.v = [0, 0, 0]; this.q = [1, 0, 0, 0]; this.w = [0, 0, 0];
    this.t = 0; this.ereignisse = []; this.zerstoert = null; this.armBruch = new Set(); this.maxLast = {arm: 0, fuss: 0, g: 1};
    this.armLast = this.md.arme.map(() => 0); this.dtA = 0; this.Pbat = 0; this.Pmittel = 0;
    const rho = this.atm.rho; this.kTs = this.rotoren.map(r => r.kT(rho)); this.kQs = this.rotoren.map(r => r.kQ(rho));
    this.Tmax = this.rotoren.map((r, i) => this.kTs[i]*Math.pow(this.antriebe[i].omMax(this.akku.leerlauf(), this.kQs[i]), 2));
    this.regler = new Flugregler(this);
    this.cdA = [0.18 + (o.nutzlast > 0 ? 0.55 : 0), 0.18 + (o.nutzlast > 0 ? 0.55 : 0), 0.35 + (o.nutzlast > 0 ? 0.15 : 0)];
    this.zDruck = sub([0, 0, o.nutzlast > 0 ? this.mm.zPerson : 0.1], cg);
    this.telemetrie();
  }
  ereignis(text, stufe = 'info') { this.ereignisse.push({t: this.t, text, stufe}); if (this.ereignisse.length > 200) this.ereignisse.shift(); }
  motorAusfall(i) { if (this.antriebe[i] && !this.antriebe[i].ausgefallen) { this.antriebe[i].ausgefallen = true; this.ereignis(`Motor M${this.rotoren[i].nr} ausgefallen`, 'kritisch'); } }
  schritt(dt) {
    if (this.zerstoert) { this.t += dt; return; }
    const o = this.opt, rho = this.atm.rho, R = this.q, hCG = this.x[2];
    const vLuftW = sub(this.v, this.wind.aktuell);
    const windW = this.wind.schritt(dt, Math.max(hCG, 0.3), len(vLuftW));
    // Flugregler (500 Hz)
    this.dtA += dt; if (this.dtA >= 0.002 - 1e-9) { this.regler.schritt(this.dtA); this.dtA = 0; }
    const U = this.akku.U;
    let F = [0, 0, -this.mm.M*G], Mb = [0, 0, 0], Hr = [0, 0, 0], Ibus = 0.0;
    const n = this.rotoren.length;
    const vb = qinv(R, this.v), wb = this.w;
    // Nachlaufinterferenz: zuerst induzierte Geschwindigkeiten des letzten Schritts
    const vi = this.rotoren.map(r => r.aus.vi);
    for (let i = 0; i < n; i++) {
      const ro = this.rotoren[i], an = this.antriebe[i], p = this.rpos[i];
      const pw = qrot(R, p), wl = this.wind.lokal([pw[0], pw[1]]);
      const vHub = add(vb, crs(wb, p)), vRel = sub(vHub, qinv(R, wl));
      // fremde Nachlaeufe
      let wz = 0; const uLuft = [-vRel[0], -vRel[1]], uL = Math.hypot(...uLuft);
      for (let j = 0; j < n; j++) {
        if (j === i || !vi[j]) continue; const q = this.rpos[j], dz = q[2] - p[2], dx = p[0] - q[0], dy = p[1] - q[1], ro2 = this.rotoren[j];
        if (Math.hypot(dx, dy) < 0.05) {                    // Koax-Paar gleiche Achse
          const sep = Math.abs(dz), vab = Math.max(vi[j] - vRel[2]*0, 0.5);
          const vers = sep*Math.hypot(...uLuft)/Math.max(vab - vRel[2], 0.5), ueb = clamp(1 - vers/(1.6*ro.R), 0, 1);
          if (dz > 0) wz += vi[j]*ueb;                         // unterer Rotor im Nachlauf des oberen
          else wz += vi[j]*(1 - sep/Math.hypot(sep, ro2.R))*ueb; // Ansaugwirkung des unteren auf den oberen
        } else if (uL > 0.5) {                                // Vorwaertsflug: hinterer Rotor im Nachlauf des vorderen
          const ux = uLuft[0]/uL, uy = uLuft[1]/uL, s = dx*ux + dy*uy, l = Math.abs(-dx*uy + dy*ux);
          if (s > 0) { const fall = s*(vi[j] - vRel[2])/uL + Math.max(-dz, 0); wz += 1.1*vi[j]*clamp(1 - l/(2*ro.R), 0, 1)*clamp(1 - fall/(0.8*ro.R), 0, 1); }
        }
      }
      const pW = add(this.x, pw), h = Math.max(pW[2], 0.02);
      const a = ro.aero(an.Om, vRel, wz, h, rho, this.r, dt);
      a.mach = (an.Om*ro.R + Math.hypot(vRel[0], vRel[1]))/this.atm.a;
      an.schritt(this.regler.omSoll[i], U, a.Q, a.vi + Math.hypot(...vRel)*0.5, dt);
      Ibus += an.Idc;
      F = add(F, qrot(R, a.F));
      Mb = add(Mb, add(crs(p, a.F), a.M));
      Mb = add(Mb, [0, 0, -ro.s*an.Qm]);                     // Reaktion des Statormoments
      Hr = add(Hr, [0, 0, ro.s*ro.J*an.Om]);
    }
    // Arm-Lasten (Schub der Rotoren je Ausleger + Traegheitsanteil Motor)
    const azb = qinv(R, [0, 0, G])[2];
    this.armLast.fill(0); this.rotoren.forEach((ro, i) => { this.armLast[ro.arm] += ro.aus.T - (this.D.motor.masse_kg + ro.masse)*(azb + (this.aLetzt ? this.aLetzt[2] : 0)); });
    this.md.arme.forEach((a, k) => {
      const u = Math.abs(this.armLast[k])/a.grenze_N; this.maxLast.arm = Math.max(this.maxLast.arm, u);
      if (u > 1 && !this.armBruch.has(k)) {
        this.armBruch.add(k); this.ereignis(`Ausleger M${a.nr}: Lastgrenze ${Math.round(a.grenze_N)} N überschritten – Strukturversagen`, 'kritisch');
        this.rotoren.forEach((ro, i) => { if (ro.arm === k) this.antriebe[i].ausgefallen = true; });
      }
    });
    // Rumpfwiderstand (Druckpunkt ueber dem Schwerpunkt bei Person)
    const vLb = qinv(R, sub(this.v, windW)), Fd = vLb.map((c, k) => -0.5*rho*this.cdA[k]*Math.abs(c)*c*1.1);
    F = add(F, qrot(R, Fd)); Mb = add(Mb, crs(this.zDruck, Fd));
    // Bodenkontakt
    let amBoden = false, fussN = 0;
    for (const k of this.kontakte) {
      const pw = qrot(R, k.p), P = add(this.x, pw); k.last = 0;
      if (P[2] >= 0) continue;
      const vp = add(this.v, qrot(R, crs(this.w, k.p))), d = -P[2];
      if (k.art === 'blatt') { const ro = this.rotoren[k.rotor]; if (this.antriebe[k.rotor].Om > 30) { this.crash(`Propeller M${ro.nr} berührt den Boden`); return; } }
      if (k.art === 'person') { this.crash('Person/Plattform am Boden – Fahrzeug umgekippt'); return; }
      if (k.art === 'struktur' && -vp[2] > 1.5) { this.crash(`Aufschlag Ausleger mit ${(-vp[2]).toFixed(1)} m/s`); return; }
      const kf = k.art === 'fuss' ? 3.0e5 : 1.5e5, cf = k.art === 'fuss' ? 6000 : 4000;
      const Fn = Math.max(0, kf*d - cf*vp[2]); const vt = Math.hypot(vp[0], vp[1]), mu = 0.6*Math.min(1, vt/0.03);
      const Fk = [-mu*Fn*vp[0]/(vt + 1e-9), -mu*Fn*vp[1]/(vt + 1e-9), Fn];
      F = add(F, Fk); Mb = add(Mb, crs(k.p, qinv(R, Fk))); k.last = Fn;
      if (k.art === 'fuss') { amBoden = true; fussN = Math.max(fussN, Fn); }
    }
    this.amBoden = amBoden; this.maxLast.fuss = Math.max(this.maxLast.fuss, fussN/this.md.fuss_grenze_N);
    if (fussN > 2*this.md.fuss_grenze_N) { this.crash(`Landestoß ${Math.round(fussN)} N je Fuß (Grenze ${Math.round(this.md.fuss_grenze_N)} N) – Fahrwerk beschädigt`); return; }
    if (fussN > this.md.fuss_grenze_N && !this.landeWarnung) { this.landeWarnung = true; this.ereignis(`Landelast ${Math.round(fussN)} N über Auslegung ${Math.round(this.md.fuss_grenze_N)} N`, 'ernst'); }
    if (amBoden && Math.abs(euler(this.q).roll) + Math.abs(euler(this.q).pitch) > 1.0) { this.crash('Fahrzeug am Boden umgekippt'); return; }
    // Starrkoerper
    const a = scl(F, 1/this.mm.M); this.aLetzt = qinv(R, a);
    this.v = add(this.v, scl(a, dt)); this.x = add(this.x, scl(this.v, dt));
    const Iw = mv3(this.mm.I, this.w), wd = mv3(this.mm.Iinv, sub(Mb, crs(this.w, add(Iw, Hr))));
    this.w = add(this.w, scl(wd, dt));
    const wl = len(this.w); if (wl > 1e-9) this.q = qnorm(qmul(this.q, qachse(scl(this.w, 1/wl), wl*dt)));
    // Akku
    Ibus += 30/Math.max(U, 1);   // Bordnetz 30 W
    this.akku.schritt(Ibus, dt); this.Ibus = Ibus; this.Pbat = Ibus*this.akku.U;
    this.Pmittel += (this.Pbat - this.Pmittel)*dt/3;
    this.nz = len(sub(a, [0, 0, -G]))/G; this.maxLast.g = Math.max(this.maxLast.g, this.amBoden ? 1 : this.nz);
    // Unterspannung: Warnung sofort, Leistungsbegrenzung nach 0,5 s, Abschaltung nach 2 s unter 3,0 V je Zelle
    const zmin = Math.min(...this.akku.zellSpannungen(Ibus)); this.zelleMin = zmin;
    this.lvcT = zmin < 3.0 ? (this.lvcT || 0) + dt : Math.max((this.lvcT || 0) - 2*dt, 0);
    this.leistungsBegrenzung = this.lvcT > 0.5;
    if (zmin < 3.3 && !this.warnZelle) { this.warnZelle = true; this.ereignis(`Zellspannung unter Last ${zmin.toFixed(2)} V`, 'ernst'); }
    if (this.lvcT > 2 && !this.lvc) { this.lvc = true; this.ereignis('Zellspannung 2 s unter 3,0 V: Unterspannungsabschaltung des Reglers', 'kritisch'); this.antriebe.forEach(x => x.ausgefallen = true); }
    this.t += dt;
  }
  crash(text) { this.zerstoert = text; this.regler.phase = 'ABSTURZ'; this.ereignis(text, 'kritisch'); this.antriebe.forEach(a => { a.Om = 0; a.I = 0; a.Idc = 0; }); this.v = [0, 0, 0]; this.w = [0, 0, 0]; if (this.x[2] < 0.3) this.x[2] = Math.max(this.x[2], 0.2); }
  // fasst den Zustand fuer Anzeige und Pruefung zusammen
  telemetrie() {
    const e = euler(this.q), M = this.mm.M, Tsum = this.rotoren.reduce((s, r) => s + r.aus.T, 0);
    const U = this.akku.U, U0 = this.akku.leerlauf(), Tmaxsum = this.Tmax.reduce((s, t, i) => s + (this.antriebe[i].ausgefallen ? 0 : t), 0);
    const zs = this.akku.zellSpannungen(this.Ibus || 0), rest = this.akku.restWh(), P = Math.max(this.Pmittel, 1);
    return {
      t: this.t, x: this.x, v: this.v, hoehe: this.x[2] - (-this.kontakte[0].p[2]), roll: e.roll, nick: e.pitch, gier: e.yaw,
      masse_kg: M, auftrieb_kg: Tsum/G, schub_max_kg: Tmaxsum/G, tw_max: Tmaxsum/(M*G), U, U0, I: this.Ibus || 0, P_kW: (this.Pbat || 0)/1000,
      soc: this.akku.soc, zelle_min: Math.min(...zs), zelle_max: Math.max(...zs), akku_T: this.akku.Tmax, rest_Wh: rest,
      flugzeit_s: rest*3600/P, Wh: this.akku.Wh_entnommen, Ah: this.akku.Ah_entnommen,
      wind: this.wind.aktuell, nz: this.nz || 1, amBoden: this.amBoden, zerstoert: this.zerstoert,
      motoren: this.rotoren.map((r, i) => { const a = this.antriebe[i]; return {nr: r.nr, lage: r.lage, dreh: r.s, rpm: a.Om*30/Math.PI, d: a.d, I: a.I, Idc: a.Idc, T_kg: r.aus.T/G,
        Q: a.Qm, Tw: a.Tw, Te: a.Te, grenze: a.grenze, aus: a.ausgefallen, mu: r.aus.mu, abriss: r.aus.abriss, vrs: r.aus.vrs, ge: r.aus.ge, mach: r.aus.mach, vi: r.aus.vi, CL: r.aus.CL}; }),
      arme: this.md.arme.map((a, k) => ({nr: a.nr, last_N: this.armLast[k], grenze_N: a.grenze_N, u: Math.abs(this.armLast[k])/a.grenze_N, bruch: this.armBruch.has(k)})),
      fuesse: this.kontakte.filter(k => k.art === 'fuss').map(k => k.last), phase: this.regler.phase, modus: this.regler.modus, maxLast: this.maxLast,
    };
  }
  // stationaere Schwebeanalyse (ohne Zeitintegration): Drehzahl, Strom, Leistung, Flugzeit
  static schwebeAnalyse(D, schluessel, opt = {}) {
    const s = new Sim(D, schluessel, Object.assign({}, opt, {turbulenz: 0, wind: 0, boeen: 0, streuung: 0}));
    const n = s.rotoren.length, G_ = s.mm.M*G, rho = s.atm.rho, U = s.akku.leerlauf() - 0.0;
    // Rotoren bei gleicher Drehzahl, Ebene weit ueber Grund; Koax-Interferenz iteriert
    let Om = Math.sqrt(G_/n/s.kTs[0]), res = null;
    for (let it = 0; it < 60; it++) {
      let T = 0; const vi = s.rotoren.map(r => r.aus.vi);
      s.rotoren.forEach((ro, i) => { let wz = 0; const p = s.rpos[i];
        s.rotoren.forEach((r2, j) => { if (j === i) return; const q = s.rpos[j]; if (Math.hypot(p[0]-q[0], p[1]-q[1]) < 0.05) { const dz = q[2]-p[2], sep = Math.abs(dz); wz += dz > 0 ? vi[j] : vi[j]*(1 - sep/Math.hypot(sep, r2.R)); } });
        for (let k = 0; k < 3; k++) ro.aero(Om, [0, 0, 0], wz, 100, rho, s.r, 0.001); T += ro.aus.F[2]; });
      const k = G_/Math.max(T, 1e-6); Om *= Math.pow(k, 0.5*0.6 + 0.2); if (Math.abs(k-1) < 1e-5) break;
    }
    let P = 0, Imax = 0, sat = false, Qmax = 0, abriss = 0, Ib = 0, PvMax = 0;
    s.rotoren.forEach((ro, i) => { const a = s.antriebe[i], Q = ro.aus.Q, I = Q/a.Kt + a.I0, Vm = a.Kt*Om + a.Rfit*I, d = Vm/U;
      if (d > 1 || I > a.Imax) sat = true; const Pi = Vm*I/a.eta; P += Pi; Ib += Pi/U; Imax = Math.max(Imax, I); Qmax = Math.max(Qmax, Q); abriss = Math.max(abriss, ro.aus.abriss); });
    P += 30;
    const Tmax = s.Tmax.reduce((a, b) => a + b, 0), Tmax_arm = Math.max(...s.md.arme.map((a, k) => s.rotoren.filter(r => r.arm === k).reduce((x, r) => x + r.aus.T, 0)/a.grenze_N));
    const E = s.akku.restWh(), t = sat ? 0 : E*3600/P;
    return {schluessel, masse_kg: s.mm.M, anteile: s.mm.anteile, rpm: Om*30/Math.PI, schub_max_kg: Tmax/G, tw_max: Tmax/G_, P_kW: P/1000, I_bus_A: Ib,
      I_phase_max_A: Imax, Q_max_Nm: Qmax, gesaettigt: sat || Tmax < G_, flugzeit_min: t/60, arm_ausnutzung_schweben: Tmax_arm,
      arm_lastfaktor_grenze: 1/Tmax_arm, mach_spitze: Om*s.rotoren[0].R/s.atm.a, CL_mittel: s.rotoren[0].aus.CL, abriss, rho, Wh_nutzbar: E,
      FM: Math.pow(G_/n, 1.5)/Math.sqrt(2*rho*s.rotoren[0].A)/(s.rotoren.reduce((x, r) => x + r.aus.Q, 0)/n*Om) };
  }
}

// ------------------------------------------------------------------ Flugregler (kaskadiert) + Steuerzuordnung
class Flugregler {
  constructor(sim) {
    this.s = sim; const n = sim.rotoren.length; this.omSoll = new Array(n).fill(0); this.phase = 'AUS'; this.modus = 'POSITION';
    this.stick = {vor: 0, rechts: 0, gier: 0, hoch: 0}; this.iRate = [0, 0, 0]; this.iVel = [0, 0, 0]; this.ziel = null; this.gierZiel = 0; this.tPhase = 0;
    this.ausgefallen = new Set(); this.erkannt = new Set(); this.altW = [0, 0, 0];
    // Reglerbandbreite aus der Hochlaufzeitkonstanten der Rotoren (grosse Propeller sind traege)
    const ro = sim.rotoren[0], an = sim.antriebe[0], OmH = Math.sqrt(sim.mm.M*G/n/sim.kTs[0]);
    const dQdw = 2*sim.kQs[0]*OmH + an.Kt*an.Kt/an.Rfit; this.tauM = ro.J/dQdw;
    this.kpRate = clamp(0.3/this.tauM, 2.5, 10); this.kdRate = 0.0; this.kpLage = Math.min(this.kpRate/2.8, 3.5); this.kpGier = 1.6;
    this.B = null; this.zuordnung();
  }
  zuordnung() {
    const s = this.s, n = s.rotoren.length, kq = s.kQs.map((k, i) => k/s.kTs[i]);
    const akt = [...Array(n).keys()].filter(i => !this.erkannt.has(i));
    const zeilen = [akt.map(() => 1), akt.map(i => s.rpos[i][1]), akt.map(i => -s.rpos[i][0]), akt.map(i => -s.rotoren[i].s*kq[i])];
    const tryInv = rows => { const BBt = rows.map(a => rows.map(b => a.reduce((x, v, k) => x + v*b[k], 0))), inv = invN(BBt); if (!inv) return null;
      return akt.map((_, k) => rows.map((_, r) => rows.reduce((x, row, c) => x + row[k]*inv[c][r], 0))); };
    let P = tryInv(zeilen), ohneGier = false;
    if (!P) { P = tryInv(zeilen.slice(0, 3)); ohneGier = true; if (P) P = P.map(r => [...r, 0]); }
    this.akt = akt; this.Pinv = P; this.ohneGier = ohneGier;
    // verfuegbare Winkelbeschleunigung je Achse aus Schubreserve um den Schwebepunkt
    const Th = s.mm.M*G/Math.max(akt.length, 1), I = s.mm.I;
    const mr = [0, 0, 0]; akt.forEach(i => { const d = Math.max(Math.min(s.Tmax[i]*0.97 - Th, Th*0.9), 0)*0.5; mr[0] += Math.abs(s.rpos[i][1])*d; mr[1] += Math.abs(s.rpos[i][0])*d; mr[2] += kq[i]*d; });
    this.alphaMax = [mr[0]/I[0], mr[1]/I[4], mr[2]/I[8]].map(a => Math.max(a, 0.05));
    if (ohneGier) s.ereignis('Steuerzuordnung ohne Gierachse (zu wenige Rotoren): Fahrzeug dreht sich', 'ernst');
  }
  setStick(st) { Object.assign(this.stick, st); }
  start() { if (this.s.zerstoert) return; if (this.phase === 'AUS') { this.phase = 'HOCHLAUF'; this.tPhase = 0; this.ziel = [...this.s.x]; this.gierZiel = euler(this.s.q).yaw; this.s.ereignis('Start: Hochlauf'); } }
  landen() { if (['FLUG', 'START'].includes(this.phase)) { this.phase = 'LANDUNG'; this.s.ereignis('Landung eingeleitet'); } }
  aus() { this.phase = 'AUS'; this.omSoll.fill(0); this.s.ereignis('Motoren aus'); }
  schritt(dt) {
    const s = this.s, n = s.rotoren.length; this.tPhase += dt;
    // Ausfallerkennung (Drehzahl bricht trotz Sollwert ein, 150 ms)
    s.antriebe.forEach((a, i) => { if (a.ausgefallen && !this.erkannt.has(i)) { a._t = (a._t || 0) + dt; if (a._t > 0.15) { this.erkannt.add(i); s.ereignis(`Flugregler: Ausfall M${s.rotoren[i].nr} erkannt, Neuverteilung`, 'ernst'); this.zuordnung(); } } });
    this.tTmax = (this.tTmax || 0) + dt;
    if (this.tTmax > 0.1) { this.tTmax = 0; const U = s.akku.U, k = s.leistungsBegrenzung ? 0.8 : 1; s.Tmax = s.rotoren.map((r, i) => k*s.kTs[i]*Math.pow(s.antriebe[i].omMax(U, s.kQs[i]), 2)); }
    if (this.phase === 'AUS' || !this.Pinv) { this.omSoll.fill(0); return; }
    const M = s.mm.M, e = euler(s.q), st = this.stick;
    const hoeheBoden = s.x[2] + s.kontakte[0].p[2];
    // ----- Sollbeschleunigung (Welt)
    let aSoll = [0, 0, 0], vSoll = [0, 0, 0];
    const cy = Math.cos(e.yaw), sy = Math.sin(e.yaw);
    if (this.phase === 'HOCHLAUF') {
      const F = M*G*Math.min(0.25 + this.tPhase*0.35, 0.85);
      this.verteile(F, [0, 0, 0], true); if (this.tPhase > 2.2) { this.phase = 'START'; this.tPhase = 0; s.ereignis('Abheben'); } return;
    }
    if (this.phase === 'START') { vSoll = [0, 0, 1.0]; if (hoeheBoden > 1.5) { this.phase = 'FLUG'; this.ziel = [...s.x]; s.ereignis('Schwebeflug'); } }
    else if (this.phase === 'LANDUNG') { vSoll = [0, 0, hoeheBoden > 2 ? -1.0 : -0.35];
      if (s.amBoden && Math.abs(s.v[2]) < 0.15 && this.tPhase > 0.5) { this.phase = 'AUS'; this.omSoll.fill(0); s.ereignis('Gelandet, Motoren aus'); return; } }
    else {
      const vmax = 8, vz = st.hoch >= 0 ? 3*st.hoch : 2.5*st.hoch;
      // Sticks im Kurssystem: vor = +x_Koerper, rechts = -y_Koerper
      vSoll = [vmax*(st.vor*cy + st.rechts*sy), vmax*(st.vor*sy - st.rechts*cy), vz];
      if (this.modus === 'POSITION') {
        if (Math.hypot(st.vor, st.rechts) < 0.02) {
          // erst abbremsen, dann Position am Haltepunkt festhalten
          if (this.halteNeu) { if (Math.hypot(s.v[0], s.v[1]) < 0.4) { this.ziel = [...s.x]; this.halteNeu = false; } }
          else { if (!this.ziel) this.ziel = [...s.x]; const ex = sub(this.ziel, s.x); vSoll[0] = clamp(0.9*ex[0], -vmax, vmax); vSoll[1] = clamp(0.9*ex[1], -vmax, vmax); }
        } else this.halteNeu = true;
      }
      if (Math.abs(st.hoch) < 0.02) {
        if (this.zNeu) { vSoll[2] = 0; if (Math.abs(s.v[2]) < 0.3) { this.zielZ = s.x[2]; this.zNeu = false; } }
        else { if (this.zielZ === null || this.zielZ === undefined) this.zielZ = s.x[2]; vSoll[2] = clamp(1.2*(this.zielZ - s.x[2]), -2, 2); }
      } else this.zNeu = true;
      if (this.vzZwang !== undefined && this.vzZwang !== null) { vSoll[2] = this.vzZwang; this.zNeu = true; }
      this.gierZiel += st.gier*0.6*dt;
    }
    // ruckbegrenzte Sollgeschwindigkeit (horizontal 2,5 m/s², vertikal 2 m/s²)
    this.vF = this.vF || [...s.v];
    for (let k = 0; k < 3; k++) { const am = k < 2 ? 2.5 : (this.vzZwang !== undefined && this.vzZwang !== null ? 6 : 2.0); this.vF[k] += clamp(vSoll[k] - this.vF[k], -am*dt, am*dt); }
    if (this.phase !== 'FLUG') this.vF = [...vSoll];
    vSoll = this.vF;
    const ev = sub(vSoll, s.v);
    if (this.modus === 'POSITION' || this.phase !== 'FLUG') { for (let k = 0; k < 3; k++) this.iVel[k] = clamp(this.iVel[k] + ev[k]*dt*0.5, -4, 4); aSoll = [1.6*ev[0] + this.iVel[0], 1.6*ev[1] + this.iVel[1], 2.2*ev[2] + this.iVel[2]]; }
    else { this.iVel[2] = clamp(this.iVel[2] + ev[2]*dt*0.5, -4, 4); aSoll = [0, 0, 2.2*ev[2] + this.iVel[2]]; }
    aSoll[2] = clamp(aSoll[2], -0.5*G, 0.6*G); const ah = Math.hypot(aSoll[0], aSoll[1]); if (ah > 3.5) { aSoll[0] *= 3.5/ah; aSoll[1] *= 3.5/ah; }
    // Schubvektor und Sollneigung
    let f = scl(add(aSoll, [0, 0, G]), M); let tilt;
    if (this.modus === 'WINKEL' && this.phase === 'FLUG') {
      const mx = 25*DEG, r = st.rechts*mx, p = st.vor*mx;     // direkte Neigung
      const bz = [Math.sin(p)*cy + Math.sin(r)*sy, Math.sin(p)*sy - Math.sin(r)*cy, 1]; f = scl(bz, f[2]/1);
    }
    const fh = Math.hypot(f[0], f[1]), maxT = 30*DEG; if (fh > f[2]*Math.tan(maxT)) { const k = f[2]*Math.tan(maxT)/fh; f[0] *= k; f[1] *= k; }
    // Schubreserve: Hoehe hat Vorrang vor Horizontalbeschleunigung
    const Tav = 0.92*this.akt.reduce((x, i) => x + s.Tmax[i], 0);
    if (len(f) > Tav) { f[2] = Math.min(f[2], Tav); const hz = Math.sqrt(Math.max(Tav*Tav - f[2]*f[2], 0)), fh2 = Math.hypot(f[0], f[1]); if (fh2 > hz) { f[0] *= hz/fh2; f[1] *= hz/fh2; } }
    this.reserve = 1 - len(f)/Math.max(Tav, 1);
    const fl = len(f), zs = scl(f, 1/fl);
    // Sollquaternion aus Schubrichtung + Kurs
    const xc = [Math.cos(this.gierZiel), Math.sin(this.gierZiel), 0], yb = crs(zs, xc), ybn = scl(yb, 1/len(yb)), xb = crs(ybn, zs);
    const Rm = [xb, ybn, zs];   // Spalten
    const tr = Rm[0][0] + Rm[1][1] + Rm[2][2];
    let qd; if (tr > 0) { const S = Math.sqrt(tr+1)*2; qd = [0.25*S, (Rm[1][2]-Rm[2][1])/S, (Rm[2][0]-Rm[0][2])/S, (Rm[0][1]-Rm[1][0])/S]; }
    else { const [a, b, c] = [Rm[0][0], Rm[1][1], Rm[2][2]];
      if (a > b && a > c) { const S = Math.sqrt(1+a-b-c)*2; qd = [(Rm[1][2]-Rm[2][1])/S, 0.25*S, (Rm[1][0]+Rm[0][1])/S, (Rm[2][0]+Rm[0][2])/S]; }
      else if (b > c) { const S = Math.sqrt(1+b-a-c)*2; qd = [(Rm[2][0]-Rm[0][2])/S, (Rm[1][0]+Rm[0][1])/S, 0.25*S, (Rm[2][1]+Rm[1][2])/S]; }
      else { const S = Math.sqrt(1+c-a-b)*2; qd = [(Rm[0][1]-Rm[1][0])/S, (Rm[2][0]+Rm[0][2])/S, (Rm[2][1]+Rm[1][2])/S, 0.25*S]; } }
    let qe = qmul([s.q[0], -s.q[1], -s.q[2], -s.q[3]], qnorm(qd)); if (qe[0] < 0) qe = qe.map(x => -x);
    // Wurzelregler: Sollrate so begrenzt, dass mit der verfuegbaren Winkelbeschleunigung ohne Ueberschwingen abgebremst werden kann
    const sq = (e, kp, a, wmax) => { const ae = Math.abs(e), lin = a/(kp*kp); const w = ae < lin ? kp*ae : Math.sqrt(2*a*(ae - lin/2)); return Math.sign(e)*Math.min(w, wmax); };
    const am = this.alphaMax || [2, 2, 0.5];
    const wSoll = [sq(2*qe[1], this.kpLage, 0.5*am[0], 1.0), sq(2*qe[2], this.kpLage, 0.5*am[1], 1.0), sq(2*qe[3], this.kpGier, 0.5*am[2], 0.6)];
    if (this.ohneGier) wSoll[2] = s.w[2];
    // Ratenregler, inertial skaliert
    const ew = sub(wSoll, s.w), I = s.mm.I;
    for (let k = 0; k < 3; k++) this.iRate[k] = clamp(this.iRate[k] + ew[k]*dt, -1, 1);
    const wd = [this.kpRate*ew[0] + 0.4*this.kpRate*this.iRate[0] - 0.02*this.kpRate*(s.w[0] - this.altW[0])/dt*0,
                this.kpRate*ew[1] + 0.4*this.kpRate*this.iRate[1], 2.0*ew[2] + 0.6*this.iRate[2]];
    this.altW = [...s.w];
    const Mz = mv3(I, wd);
    this.verteile(dot(f, qrot(s.q, [0, 0, 1])), Mz, false);
  }
  // Steuerzuordnung als gewichtete Kleinste-Quadrate-Loesung mit Stellgrenzen (Koordinatenabstieg, warm gestartet).
  // Gewichte: Roll/Nick vor Gesamtschub vor Gier – bei Saettigung gibt zuerst die Gierachse nach.
  verteile(F, Mv, gleich) {
    const s = this.s, akt = this.akt, k = akt.length;
    const lo = akt.map(i => 0.04*s.Tmax[i]), hi = akt.map(i => s.Tmax[i]*0.97);
    const setze = u => { this.omSoll.fill(0); akt.forEach((i, c) => { this.omSoll[i] = Math.sqrt(Math.max(u[c], 0)/s.kTs[i]); }); };
    if (gleich) { setze(akt.map((_, c) => clamp(F/k, lo[c], hi[c]))); this.uAlt = null; return; }
    if (!this.wls || this.wls.akt !== akt) {
      const kq = akt.map(i => s.kQs[i]/s.kTs[i]), Mg = s.mm.M*G, rA = akt.reduce((q, i) => q + Math.hypot(s.rpos[i][0], s.rpos[i][1]), 0)/k, kqm = kq.reduce((q, v) => q + v, 0)/k;
      const B = [akt.map(() => 1), akt.map(i => s.rpos[i][1]), akt.map(i => -s.rpos[i][0]), akt.map((i, c) => -s.rotoren[i].s*kq[c])];
      const w = [1/Mg, 4/(Mg*rA), 4/(Mg*rA), this.ohneGier ? 0 : 0.5/(Mg*kqm)].map(x => x*x), eps = 1e-5/((Mg/k)*(Mg/k));
      const Q = akt.map((_, i) => akt.map((_, j) => B.reduce((q, row, r) => q + w[r]*row[i]*row[j], 0) + (i === j ? eps : 0)));
      this.wls = {akt, B, w, Q, eps};
    }
    const {B, w, Q, eps} = this.wls, tau = [F, Mv[0], Mv[1], Mv[2]];
    const c = akt.map((_, i) => B.reduce((q, row, r) => q + w[r]*row[i]*tau[r], 0) + eps*F/k);
    const u = (this.uAlt && this.uAlt.length === k) ? this.uAlt.slice() : akt.map((_, i) => clamp(F/k, lo[i], hi[i]));
    for (let sweep = 0; sweep < 25; sweep++) {
      let d = 0;
      for (let i = 0; i < k; i++) { let r = c[i]; for (let j = 0; j < k; j++) if (j !== i) r -= Q[i][j]*u[j]; const n = clamp(r/Q[i][i], lo[i], hi[i]); d = Math.max(d, Math.abs(n - u[i])); u[i] = n; }
      if (d < 0.05) break;
    }
    this.uAlt = u;
    const ist = B.map(row => row.reduce((q, v, i) => q + v*u[i], 0));
    this.saettigung = Math.abs(ist[0] - F) > 0.02*F || Math.hypot(ist[1] - Mv[0], ist[2] - Mv[1]) > 0.05*s.mm.M*G*0.1 || (!this.ohneGier && Math.abs(ist[3] - Mv[2]) > 0.5*Math.abs(Mv[2]) + 2);
    this.momentFaktor = 1;
    setze(u);
  }
}

const api = {Sim, Rotor, Akku, Antrieb, Wind, Flugregler, atmosphaere, ocv, rng, euler, qrot, qinv, G, STANDARD};
if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.SimPhysik = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
