/* R04 Simulator – 2D-Lattice-Boltzmann (D2Q9, BGK + Smagorinsky) eines abgewickelten Zylinderschnitts.
 * Zwei Fluegelreihen bei z = +-h/2 laufen gegenlaeufig (oben +x, unten -x), periodisch in x
 * (Umfangsrichtung, Laenge = periods * 2*pi*r/B). Oben/unten Gleichgewichtsraender mit Schwammzone.
 * Bewegte Koerper: Maske je Schritt, Bounce-back mit Wandgeschwindigkeit, Kraefte per Impulsaustausch.
 * Re wird kuenstlich niedrig gewaehlt: qualitative Wirbel-/Turbulenzdarstellung, kein Nachweis.
 */
(function (root) {
  'use strict';
  const CX = [0, 1, 0, -1, 0, 1, -1, -1, 1], CY = [0, 0, 1, 0, -1, 1, 1, -1, -1];
  const W = [4 / 9, 1 / 9, 1 / 9, 1 / 9, 1 / 9, 1 / 36, 1 / 36, 1 / 36, 1 / 36];
  const OPP = [0, 3, 4, 1, 2, 7, 8, 5, 6];

  function naca(q, tc, teHalf) { // halbe Dicke / Sehne
    q = Math.min(Math.max(q, 0), 1);
    return 5 * tc * (0.2969 * Math.sqrt(q) - 0.126 * q - 0.3516 * q * q + 0.2843 * q ** 3 - 0.1036 * q ** 4) + teHalf * q ** 10;
  }

  class Cascade {
    /* o: {nx, ny, chordCells, spacingCells, levelGapCells, rows:[{pitch, dir}], tc, teHalf, uBlade, nu, sponge} */
    constructor(o) {
      Object.assign(this, o);
      const n = this.nx * this.ny;
      this.f = new Float32Array(9 * n); this.g = new Float32Array(9 * n);
      this.rho = new Float32Array(n).fill(1); this.ux = new Float32Array(n); this.uy = new Float32Array(n);
      this.mask = new Uint8Array(n); this.prevMask = new Uint8Array(n);
      this.force = [{ x: 0, y: 0 }, { x: 0, y: 0 }]; this.time = 0;
      for (let i = 0; i < n; i++) for (let k = 0; k < 9; k++) this.f[k * n + i] = W[k];
      this.offsets = this.rows.map((_, j) => j * 0.5 * this.spacingCells); // Startversatz der Reihen
      this.rasterize();
      this.prevMask.set(this.mask);
    }

    rowY(j) { return this.ny / 2 + (j === 0 ? 0.5 : -0.5) * this.levelGapCells; }

    bladeX(j, b) {
      const x = this.offsets[j] + b * this.spacingCells + this.rows[j].dir * this.uBlade * this.time;
      return ((x % this.nx) + this.nx) % this.nx;
    }

    /* Maske: 0 Fluid, 1 obere Reihe, 2 untere Reihe. Profil-Nase zeigt in Laufrichtung, Pitch Nase hoch. */
    rasterize() {
      const { nx, ny, chordCells: c, mask } = this; mask.fill(0);
      const nb = Math.round(this.nx / this.spacingCells);
      for (let j = 0; j < this.rows.length; j++) {
        const row = this.rows[j], th = row.pitch * Math.PI / 180, cs = Math.cos(th), sn = Math.sin(th);
        const yc = this.rowY(j), half = 0.55 * c;
        for (let b = 0; b < nb; b++) {
          const xc = this.bladeX(j, b);
          for (let y = Math.max(1, Math.floor(yc - half)); y <= Math.min(ny - 2, Math.ceil(yc + half)); y++) {
            for (let dx = -Math.ceil(half); dx <= Math.ceil(half); dx++) {
              const x = ((Math.round(xc) + dx) % nx + nx) % nx;
              let px = Math.round(xc) + dx - xc, py = y - yc;
              // in Profilkoordinaten: s laengs Sehne (Nase +), n normal; Fluegel um Pitchachse (50 %) gedreht
              const s = row.dir * (px * cs + py * sn * row.dir);
              const nrm = -px * sn * row.dir + py * cs;
              const q = 0.5 - s / c;
              if (q < 0 || q > 1) continue;
              if (Math.abs(nrm) <= naca(q, this.tc, this.teHalf) * c + 0.25) mask[y * nx + x] = j + 1;
            }
          }
        }
      }
    }

    wallU(j) { return this.rows[j].dir * this.uBlade; }

    step() {
      const { nx, ny, f, g, rho, ux, uy, mask, prevMask } = this, n = nx * ny;
      const tau0 = 3 * this.nu + 0.5, cs2 = 0.0289; // Smagorinsky C_s^2 (C_s = 0.17)
      // Kollision mit Smagorinsky-Wirbelviskositaet; Schwammzone erhoeht tau zu den Raendern
      for (let y = 0; y < ny; y++) {
        const dist = Math.min(y, ny - 1 - y), sp = dist < this.sponge ? (1 - dist / this.sponge) ** 2 : 0;
        const tauB = tau0 + sp * 1.5;
        for (let x = 0; x < nx; x++) {
          const i = y * nx + x;
          if (mask[i]) continue;
          let r = 0, mx = 0, my = 0;
          for (let k = 0; k < 9; k++) { const v = f[k * n + i]; r += v; mx += v * CX[k]; my += v * CY[k]; }
          const vx = mx / r, vy = my / r; rho[i] = r; ux[i] = vx; uy[i] = vy;
          const usq = 1.5 * (vx * vx + vy * vy);
          let pxx = 0, pyy = 0, pxy = 0;
          const feq = this._feq || (this._feq = new Float32Array(9));
          for (let k = 0; k < 9; k++) {
            const cu = 3 * (CX[k] * vx + CY[k] * vy);
            feq[k] = W[k] * r * (1 + cu + 0.5 * cu * cu - usq);
            const ne = f[k * n + i] - feq[k];
            pxx += CX[k] * CX[k] * ne; pyy += CY[k] * CY[k] * ne; pxy += CX[k] * CY[k] * ne;
          }
          const qn = Math.sqrt(pxx * pxx + pyy * pyy + 2 * pxy * pxy);
          const tau = 0.5 * (tauB + Math.sqrt(tauB * tauB + 18 * cs2 * qn / r));
          const om = 1 / tau;
          for (let k = 0; k < 9; k++) f[k * n + i] += om * (feq[k] - f[k * n + i]);
        }
      }
      // Koerper bewegen; frei gewordene Zellen mit Gleichgewicht bei Wandgeschwindigkeit fuellen
      this.time += 1;
      prevMask.set(mask); this.rasterize();
      for (let i = 0; i < n; i++) {
        if (prevMask[i] && !mask[i]) {
          const u = this.wallU(prevMask[i] - 1), usq = 1.5 * u * u;
          for (let k = 0; k < 9; k++) { const cu = 3 * CX[k] * u; f[k * n + i] = W[k] * (1 + cu + 0.5 * cu * cu - usq); }
          rho[i] = 1; ux[i] = u; uy[i] = 0;
        }
      }
      // Streaming (pull) mit Bounce-back an bewegten Waenden, Impulsaustausch
      const F = [{ x: 0, y: 0 }, { x: 0, y: 0 }];
      for (let y = 0; y < ny; y++) {
        for (let x = 0; x < nx; x++) {
          const i = y * nx + x;
          if (mask[i]) { for (let k = 0; k < 9; k++) g[k * n + i] = W[k]; continue; }
          for (let k = 0; k < 9; k++) {
            const sx = (x - CX[k] + nx) % nx, sy = y - CY[k];
            if (sy < 0 || sy >= ny) { g[k * n + i] = f[k * n + i]; continue; }
            const s = sy * nx + sx, m = mask[s];
            if (m) {
              const o = OPP[k], uw = this.wallU(m - 1);
              const val = f[o * n + i] + 6 * W[k] * CX[k] * uw;
              g[k * n + i] = val;
              F[m - 1].x += CX[o] * (f[o * n + i] + val); F[m - 1].y += CY[o] * (f[o * n + i] + val);
            } else g[k * n + i] = f[k * n + s];
          }
        }
      }
      // Raender oben/unten: Gleichgewicht rho = 1 mit Geschwindigkeit der Nachbarzeile (Ein-/Ausstroem)
      for (const [y, yn] of [[0, 1], [ny - 1, ny - 2]]) {
        for (let x = 0; x < nx; x++) {
          const i = y * nx + x, j = yn * nx + x;
          const vx = ux[j] * 0.98, vy = uy[j], usq = 1.5 * (vx * vx + vy * vy);
          for (let k = 0; k < 9; k++) { const cu = 3 * (CX[k] * vx + CY[k] * vy); g[k * n + i] = W[k] * (1 + cu + 0.5 * cu * cu - usq); }
        }
      }
      this.f = g; this.g = f;
      const a = 0.002; // gleitender Mittelwert der Reihenkraefte
      for (let j = 0; j < 2; j++) { this.force[j].x += a * (F[j].x - this.force[j].x); this.force[j].y += a * (F[j].y - this.force[j].y); }
      this.lastForce = F;
    }

    /* Auftriebsbeiwert je Fluegel einer Reihe (bezogen auf Wandgeschwindigkeit, Sehne, rho = 1). */
    cl(j) {
      const nb = Math.round(this.nx / this.spacingCells);
      return this.force[j].y / nb / (0.5 * this.uBlade * this.uBlade * this.chordCells);
    }

    vorticity(out) {
      const { nx, ny, ux, uy, mask } = this;
      for (let y = 1; y < ny - 1; y++) for (let x = 0; x < nx; x++) {
        const i = y * nx + x;
        if (mask[i]) { out[i] = NaN; continue; }
        const xp = y * nx + (x + 1) % nx, xm = y * nx + (x - 1 + nx) % nx;
        out[i] = 0.5 * (uy[xp] - uy[xm]) - 0.5 * (ux[i + nx] - ux[i - nx]);
      }
      return out;
    }

    meanDownwash() { // mittlere Vertikalgeschwindigkeit zwischen beiden Reihen und unterhalb
      const { nx, ny, uy } = this; const y = Math.round(this.rowY(1) - this.chordCells); let s = 0;
      for (let x = 0; x < nx; x++) s += uy[y * nx + x];
      return s / nx;
    }
  }

  const api = { Cascade, naca };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.R04LBM = api;
})(typeof window !== 'undefined' ? window : globalThis);
