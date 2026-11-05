/* D14 Viewer: eigenstaendiges WebGL, laedt Konfigurationen per <script> (auch ueber file://). */
(() => {
'use strict';
const $ = id => document.getElementById(id);
const canvas = $('view');
const gl = canvas.getContext('webgl', {antialias: true, preserveDrawingBuffer: true});
const state = {index: null, daten: {}, ecken: {}, eckeU: {}, prop: {}, ausCache: {}, reglerCache: {}, sel: null, yaw: -0.9, pitch: 0.45, dist: 3.2, target: [0, 0, 0], ready: false};
window.D14 = state;

// ------------------------------------------------------------ Mathe
const I4 = () => [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1];
function mul(a, b) { const o = new Array(16).fill(0); for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) for (let k = 0; k < 4; k++) o[c*4+r] += a[k*4+r] * b[c*4+k]; return o; }
const rz = d => { const c = Math.cos(d*Math.PI/180), s = Math.sin(d*Math.PI/180); return [c,s,0,0, -s,c,0,0, 0,0,1,0, 0,0,0,1]; };
const SY = [1,0,0,0, 0,-1,0,0, 0,0,1,0, 0,0,0,1], SZ = [1,0,0,0, 0,1,0,0, 0,0,-1,0, 0,0,0,1];
function tf(m, p) { return [m[0]*p[0]+m[4]*p[1]+m[8]*p[2]+m[12], m[1]*p[0]+m[5]*p[1]+m[9]*p[2]+m[13], m[2]*p[0]+m[6]*p[1]+m[10]*p[2]+m[14]]; }
function persp(f, a, n, fa) { const t = 1/Math.tan(f/2); return [t/a,0,0,0, 0,t,0,0, 0,0,(fa+n)/(n-fa),-1, 0,0,2*fa*n/(n-fa),0]; }
function lookAt(e, c, u) {
  let z = [e[0]-c[0], e[1]-c[1], e[2]-c[2]]; let l = Math.hypot(...z); z = z.map(v => v/l);
  let x = [u[1]*z[2]-u[2]*z[1], u[2]*z[0]-u[0]*z[2], u[0]*z[1]-u[1]*z[0]]; l = Math.hypot(...x); x = x.map(v => v/l);
  const y = [z[1]*x[2]-z[2]*x[1], z[2]*x[0]-z[0]*x[2], z[0]*x[1]-z[1]*x[0]];
  return [x[0],y[0],z[0],0, x[1],y[1],z[1],0, x[2],y[2],z[2],0, -(x[0]*e[0]+x[1]*e[1]+x[2]*e[2]), -(y[0]*e[0]+y[1]*e[1]+y[2]*e[2]), -(z[0]*e[0]+z[1]*e[1]+z[2]*e[2]), 1];
}

// ------------------------------------------------------------ Shader
function sh(t, s) { const o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o); if (!gl.getShaderParameter(o, gl.COMPILE_STATUS)) throw Error(gl.getShaderInfoLog(o)); return o; }
const prog = gl.createProgram();
gl.attachShader(prog, sh(gl.VERTEX_SHADER, 'attribute vec3 p;attribute vec3 n;uniform mat4 m;uniform mat4 vp;varying vec3 vn;varying vec3 wp;void main(){vec4 w=m*vec4(p,1.);wp=w.xyz;vn=mat3(m)*n;gl_Position=vp*w;}'));
gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, 'precision mediump float;varying vec3 vn;varying vec3 wp;uniform vec3 col;uniform float alpha;uniform float carbon;uniform float unlit;void main(){vec3 N=normalize(vn);float l=.32+.55*abs(dot(N,normalize(vec3(.35,-.45,.82))))+.18*pow(abs(dot(N,normalize(vec3(-.6,.3,.4)))),8.);float w=mod(floor(wp.x/6.)+floor(wp.y/6.)+floor(wp.z/6.),2.);vec3 c=col*mix(1.,.86+.14*w,carbon);gl_FragColor=vec4(mix(c*l,col,unlit),alpha);}'));
gl.linkProgram(prog); gl.useProgram(prog);
const loc = {p: gl.getAttribLocation(prog, 'p'), n: gl.getAttribLocation(prog, 'n')};
['m','vp','col','alpha','carbon','unlit'].forEach(k => loc[k] = gl.getUniformLocation(prog, k));

function upload(pos, nor, mode) {
  const b1 = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b1); gl.bufferData(gl.ARRAY_BUFFER, pos, gl.STATIC_DRAW);
  const b2 = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b2); gl.bufferData(gl.ARRAY_BUFFER, nor, gl.STATIC_DRAW);
  return {b1, b2, n: pos.length/3, mode: mode || gl.TRIANGLES};
}
function flatNormals(pos) {
  const n = new Float32Array(pos.length);
  for (let i = 0; i < pos.length; i += 9) {
    const ax = pos[i+3]-pos[i], ay = pos[i+4]-pos[i+1], az = pos[i+5]-pos[i+2], bx = pos[i+6]-pos[i], by = pos[i+7]-pos[i+1], bz = pos[i+8]-pos[i+2];
    let x = ay*bz-az*by, y = az*bx-ax*bz, z = ax*by-ay*bx; const l = Math.hypot(x, y, z) || 1;
    for (let k = 0; k < 3; k++) { n[i+3*k] = x/l; n[i+3*k+1] = y/l; n[i+3*k+2] = z/l; }
  }
  return n;
}
function b64(s, T) { const bin = atob(s), u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); return new T(u.buffer); }
function decode(m) {
  if (!m) return null;
  const q = b64(m.v, Int16Array), idx = b64(m.i, m.i32 ? Uint32Array : Uint16Array);
  const pos = new Float32Array(idx.length*3);
  for (let i = 0; i < idx.length; i++) for (let k = 0; k < 3; k++) pos[i*3+k] = m.c[k] + q[idx[i]*3+k]*m.s;
  return upload(pos, flatNormals(pos));
}
// Rohr (Huelse) entlang +z, Laenge 1, skaliert ueber Matrix
const rohrCache = {};
function rohrMesh(od, id) {
  const key = od + '/' + id; if (rohrCache[key]) return rohrCache[key];
  const N = 28, P = [], Nn = [], ro = od/2, ri = id/2;
  for (let i = 0; i < N; i++) {
    const a0 = 2*Math.PI*i/N, a1 = 2*Math.PI*(i+1)/N, c0 = Math.cos(a0), s0 = Math.sin(a0), c1 = Math.cos(a1), s1 = Math.sin(a1);
    for (const [r, sg] of [[ro, 1], [ri, -1]]) {
      P.push(r*c0,r*s0,0, r*c1,r*s1,0, r*c1,r*s1,1, r*c0,r*s0,0, r*c1,r*s1,1, r*c0,r*s0,1);
      for (let k = 0; k < 6; k++) { const c = k===1||k===2||k===4 ? c1 : c0, s = k===1||k===2||k===4 ? s1 : s0; Nn.push(sg*c, sg*s, 0); }
    }
    for (const z of [0, 1]) {
      P.push(ri*c0,ri*s0,z, ro*c0,ro*s0,z, ro*c1,ro*s1,z, ri*c0,ri*s0,z, ro*c1,ro*s1,z, ri*c1,ri*s1,z);
      for (let k = 0; k < 6; k++) Nn.push(0, 0, z ? 1 : -1);
    }
  }
  return rohrCache[key] = upload(new Float32Array(P), new Float32Array(Nn));
}
function zylinder(r) {
  const key = 'z' + r; if (rohrCache[key]) return rohrCache[key];
  const N = 48, P = [], Nn = [];
  for (let i = 0; i < N; i++) {
    const a0 = 2*Math.PI*i/N, a1 = 2*Math.PI*(i+1)/N, c0 = Math.cos(a0), s0 = Math.sin(a0), c1 = Math.cos(a1), s1 = Math.sin(a1);
    P.push(r*c0,r*s0,0, r*c1,r*s1,0, r*c1,r*s1,1, r*c0,r*s0,0, r*c1,r*s1,1, r*c0,r*s0,1);
    for (let k = 0; k < 6; k++) { const c = k===1||k===2||k===4 ? c1 : c0, s = k===1||k===2||k===4 ? s1 : s0; Nn.push(c, s, 0); }
    for (const z of [0, 1]) { P.push(0,0,z, r*c0,r*s0,z, r*c1,r*s1,z); Nn.push(0,0,z?1:-1, 0,0,z?1:-1, 0,0,z?1:-1); }
  }
  return rohrCache[key] = upload(new Float32Array(P), new Float32Array(Nn));
}
function achse(a, b) {
  const d = [b[0]-a[0], b[1]-a[1], b[2]-a[2]], L = Math.hypot(...d), z = d.map(v => v/L);
  let x = Math.abs(z[2]) < .9 ? [z[1], -z[0], 0] : [1, 0, 0]; let l = Math.hypot(...x); x = x.map(v => v/l);
  const y = [z[1]*x[2]-z[2]*x[1], z[2]*x[0]-z[0]*x[2], z[0]*x[1]-z[1]*x[0]];
  return [x[0],x[1],x[2],0, y[0],y[1],y[2],0, z[0]*L,z[1]*L,z[2]*L,0, a[0],a[1],a[2],1];
}

// ------------------------------------------------------------ Szene
const FARBE = {alu: [.74,.77,.80], carbon: [.12,.14,.16], schraube: [.30,.31,.33], motor: [.86,.50,.16], rotor: [.35,.55,.75], system: [.85,.12,.12], rahmen: [.12,.14,.16], sohle: [.10,.10,.11], regler: [.16,.30,.52], d12: [.62,.70,.78]};
let szene = [], linien = null, labels = [];
function baueSzene() {
  const d = state.daten[state.sel.key], e = state.ecken[state.sel.bw]; if (!d || !e) return;
  szene = []; labels = [];
  const ms = {}; for (const [k, m] of Object.entries(d.meshes)) ms[k] = decode(m);
  const eq = d.eck_meshes || e;              // V4: konfigurationseigene Eckknoten mit Gurthuelsen
  const em = decode(eq.eckknoten), es = decode(eq.eckknoten_schrauben);
  const zr = $('zeigeRotor').checked, zs = $('zeigeSystem').checked, zb = $('zeigeSchrauben').checked, za = $('zeigeAusruestung').checked;
  const linPts = [];
  d.paarwinkel.forEach(phi => {
    const R = rz(phi), RS = mul(R, SY);
    szene.push({g: ms.verbinder, m: R, c: FARBE.alu});
    if (zb) szene.push({g: ms.verbinder_schrauben, m: R, c: FARBE.schraube});
    for (const M of [R, RS]) {
      szene.push({g: ms.motortraeger, m: M, c: FARBE.alu});
      if (zb) szene.push({g: ms.motortraeger_schrauben, m: M, c: FARBE.schraube});
      d.rohre.forEach(r => szene.push({g: rohrMesh(r.od, r.id), m: mul(M, achse(r.a, r.b)), c: FARBE.carbon, carbon: 1}));
      d.motor.lagen.forEach(l => szene.push({g: zylinder(d.motor.d/2), m: mul(M, [1,0,0,0, 0,1,0,0, 0,0,l.h,0, d.motor.xy[0], d.motor.xy[1], l.z0, 1]), c: FARBE.motor}));
      if (zr) d.rotor.lagen.forEach(l => szene.push({g: zylinder(d.rotor.d/2), m: mul(M, [1,0,0,0, 0,1,0,0, 0,0,2*d.rotor.halb,0, d.motor.xy[0], d.motor.xy[1], l.z-d.rotor.halb, 1]), c: FARBE.rotor, alpha: .07}));
      if (zs) d.systemlinien.forEach(([a, b]) => { linPts.push(...tf(M, a), ...tf(M, b)); });
    }
    if (!d.ecken) for (const M of [R, RS, mul(R, SZ), mul(RS, SZ)]) {
      szene.push({g: em, m: M, c: FARBE.alu});
      if (zb) szene.push({g: es, m: M, c: FARBE.schraube});
    }
    if (d.regler_meshes && za) {
      const rm = state.reglerCache[state.sel.key] || (state.reglerCache[state.sel.key] = {h: decode(d.regler_meshes.halter), s: decode(d.regler_meshes.schrauben), r: decode(d.regler_meshes.regler)});
      for (const M of [R, RS]) {
        szene.push({g: rm.h, m: M, c: FARBE.alu}); szene.push({g: rm.r, m: M, c: FARBE.regler});
        if (zb) szene.push({g: rm.s, m: M, c: FARBE.schraube});
      }
    }
  });
  if (d.ecken) { const eu = d.eck_meshes ? decode(d.eck_meshes.eckknoten_unten) : (state.eckeU[state.sel.bw] || (state.eckeU[state.sel.bw] = decode(e.eckknoten_unten)));
    const esu = d.eck_meshes && d.eck_meshes.eckknoten_schrauben_unten ? decode(d.eck_meshes.eckknoten_schrauben_unten) : es;
    d.ecken.forEach(E => { szene.push({g: E.u ? eu : em, m: E.m, c: FARBE.alu}); if (zb) szene.push({g: E.u ? esu : es, m: E.m, c: FARBE.schraube}); }); }
  const pm = state.prop[d.propeller && d.propeller.id];
  if (pm && $('zeigePropeller').checked) {
    const g = {CW: pm.cw || (pm.cw = decode(pm.raw.cw)), CCW: pm.ccw || (pm.ccw = decode(pm.raw.ccw))};
    d.motoren.forEach(m => {
      const T = mul([1,0,0,0, 0,1,0,0, 0,0,1,0, m.xy[0], m.xy[1], 0, 1], rz(m.winkel_grad));
      szene.push({g: g[m.drehrichtung], m: T, c: FARBE.carbon, carbon: 1});
      if (d.propeller.nabe_unten_z !== null) {
        const Mz = [1,0,0,0, 0,1,0,0, 0,0,-1,0, 0,0, d.propeller.nabe_unten_z + d.propeller.nabe_z, 1];
        szene.push({g: g[m.drehrichtung], m: mul(T, Mz), c: FARBE.carbon, carbon: 1});
      }
    });
  }
  if (d.aus_meshes && za) {
    const am = state.ausCache[state.sel.key] || (state.ausCache[state.sel.key] = {a: decode(d.aus_meshes.alu), s: decode(d.aus_meshes.schrauben), so: decode(d.aus_meshes.sohle)});
    szene.push({g: am.a, m: I4(), c: FARBE.d12}); szene.push({g: am.so, m: I4(), c: FARBE.sohle});
    if (zb) szene.push({g: am.s, m: I4(), c: FARBE.schraube});
    d.aus_rohre.forEach(r => szene.push({g: rohrMesh(r.od, r.id), m: achse(r.a, r.b), c: FARBE.carbon, carbon: 1}));
    if (state.d12) {
      const dx = d.d12_versatz_x || 0;
      for (const [seite, sx] of [['plus', 1], ['minus', -1]]) {
        const g = state.d12[seite], T = [1,0,0,0, 0,1,0,0, 0,0,1,0, sx*dx,0,0,1];
        g.a = g.a || decode(g.alu); g.s = g.s || decode(g.schrauben);
        szene.push({g: g.a, m: T, c: FARBE.d12});
        if (zb) szene.push({g: g.s, m: T, c: FARBE.schraube});
      }
    }
  }
  d.rahmen.forEach(r => szene.push({g: rohrMesh(r.od, r.id), m: achse(r.a, r.b), c: FARBE.rahmen, carbon: 1}));
  d.motoren.forEach(m => labels.push({t: 'M' + m.nr, p: [m.xy[0], m.xy[1], state.index.konfigurationen[state.sel.key].rotor_oben_z + 40]}));
  linien = linPts.length ? upload(new Float32Array(linPts), new Float32Array(linPts.length), gl.LINES) : null;
  const lab = $('labels'); lab.innerHTML = '';
  labels.forEach(l => { l.el = document.createElement('div'); l.el.textContent = l.t; lab.appendChild(l.el); });
  state.ready = true; state.count = szene.length;
}

let VP = I4();
function draw() {
  const w = canvas.clientWidth, h = canvas.clientHeight, dpr = Math.min(2, devicePixelRatio || 1);
  if (canvas.width !== Math.round(w*dpr) || canvas.height !== Math.round(h*dpr)) { canvas.width = Math.round(w*dpr); canvas.height = Math.round(h*dpr); }
  gl.viewport(0, 0, canvas.width, canvas.height);
  const dark = getComputedStyle(document.body).backgroundColor;
  const bg = dark.match(/\d+/g).map(Number);
  gl.clearColor(bg[0]/255, bg[1]/255, bg[2]/255, 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST);
  const t = state.target, D = state.dist*1000;
  const eye = [t[0] + D*Math.cos(state.pitch)*Math.cos(state.yaw), t[1] + D*Math.cos(state.pitch)*Math.sin(state.yaw), t[2] + D*Math.sin(state.pitch)];
  VP = mul(persp(0.7, w/h, D*0.02, D*10), lookAt(eye, t, [0, 0, 1]));
  gl.uniformMatrix4fv(loc.vp, false, VP);
  const pass = (transparent) => szene.forEach(o => {
    if (!o.g || (!!o.alpha) !== transparent) return;
    gl.bindBuffer(gl.ARRAY_BUFFER, o.g.b1); gl.enableVertexAttribArray(loc.p); gl.vertexAttribPointer(loc.p, 3, gl.FLOAT, false, 0, 0);
    gl.bindBuffer(gl.ARRAY_BUFFER, o.g.b2); gl.enableVertexAttribArray(loc.n); gl.vertexAttribPointer(loc.n, 3, gl.FLOAT, false, 0, 0);
    gl.uniformMatrix4fv(loc.m, false, o.m); gl.uniform3fv(loc.col, o.c); gl.uniform1f(loc.alpha, o.alpha || 1);
    gl.uniform1f(loc.carbon, o.carbon || 0); gl.uniform1f(loc.unlit, 0);
    gl.drawArrays(o.g.mode, 0, o.g.n);
  });
  pass(false);
  if (linien) {
    gl.disable(gl.DEPTH_TEST);
    gl.bindBuffer(gl.ARRAY_BUFFER, linien.b1); gl.vertexAttribPointer(loc.p, 3, gl.FLOAT, false, 0, 0);
    gl.bindBuffer(gl.ARRAY_BUFFER, linien.b2); gl.vertexAttribPointer(loc.n, 3, gl.FLOAT, false, 0, 0);
    gl.uniformMatrix4fv(loc.m, false, I4()); gl.uniform3fv(loc.col, FARBE.system); gl.uniform1f(loc.alpha, 1); gl.uniform1f(loc.unlit, 1);
    gl.drawArrays(gl.LINES, 0, linien.n); gl.enable(gl.DEPTH_TEST);
  }
  gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); gl.depthMask(false);
  pass(true); gl.depthMask(true); gl.disable(gl.BLEND);
  labels.forEach(l => {
    const p = l.p, c = [VP[0]*p[0]+VP[4]*p[1]+VP[8]*p[2]+VP[12], VP[1]*p[0]+VP[5]*p[1]+VP[9]*p[2]+VP[13], VP[3]*p[0]+VP[7]*p[1]+VP[11]*p[2]+VP[15]];
    if (c[2] <= 0) { l.el.style.display = 'none'; return; }
    l.el.style.display = ''; l.el.style.left = ((c[0]/c[2]+1)/2*w) + 'px'; l.el.style.top = ((1-c[1]/c[2])/2*h) + 'px';
  });
  requestAnimationFrame(draw);
}

// ------------------------------------------------------------ Ansichten
function ansicht(v) {
  const k = state.index.konfigurationen[state.sel.key], d = state.daten[state.sel.key]; if (!d) return;
  const R = k.R, W = d.W, I = d.I;
  const set = (t, dist, yaw, pitch) => Object.assign(state, {target: t, dist, yaw, pitch});
  if (v === 'gesamt') set([0, 0, 0], (R + k.rotor_oben_z) * 0.0042 + 0.6, -0.9, 0.5);
  if (v === 'drauf') set([0, 0, 0], (R + 600) * 0.0042, -Math.PI/2, 1.5);
  if (v === 'verbinder') set([W[0] + 20, 0, 40], 0.75, -0.55, 0.35);
  if (v === 'verbinderUnten') set([W[0] + 20, 0, -60], 0.75, -0.4, -0.45);
  if (v === 'motor') set([I[0] - 60, I[1] - 30, 40], 0.65, -1.25, 0.3);
  if (v === 'motorSeite') { const a = Math.atan2(I[1] - W[1], I[0] - W[0]); set([I[0] - Math.cos(a)*k.ce*0.55, I[1] - Math.sin(a)*k.ce*0.55, 40], 0.42 + k.ce*0.0014, a - Math.PI/2, 0.12); }
  if (v === 'seite') { const a = Math.atan2(I[1] - W[1], I[0] - W[0]); set([(W[0] + I[0])/2, (W[1] + I[1])/2, 0], k.Lr*0.0024 + 0.3, a - Math.PI/2, 0.05); }
  if (v === 'fuss' && d.ausruestung) { const f = d.ausruestung.fussschlitten; set([f.bock_x_mm*0.55, f.schiene_y_mm, 170], 1.05, -0.75, 0.42); }
  if (v === 'lande' && d.ausruestung) { const f = d.ausruestung.landegestell.fuesse[0]; set([f[0], f[1], f[2] + 60], 0.55, -0.6, 0.12); }
  if (v === 'regler' && d.ausruestung) { const r = d.ausruestung.regler.mitte; set([r[0], r[1], r[2]], 0.6, Math.atan2(I[1] - W[1], I[0] - W[0]) - Math.PI/2 + 0.35, 0.25); }
  if (v === 'ecke') { const r = d.rahmen[0].a; set([d.rahmen[0].a[0], d.rahmen[0].a[1], 110], 0.55, -0.4, 0.45); }
  state.ansicht = v;
}

// ------------------------------------------------------------ Panel
const f1 = (x, n = 1) => x === null || x === undefined ? '–' : Number(x).toLocaleString('de-DE', {minimumFractionDigits: n, maximumFractionDigits: n});
const dl = (id, rows) => $(id).innerHTML = rows.map(([a, b, c]) => `<dt>${a}</dt><dd class="${c || ''}">${b}</dd>`).join('');
const ja = b => b ? ['bestanden', 'ok'] : ['offen', 'bad'];
function panel() {
  const k = state.index.konfigurationen[state.sel.key]; const p = k.pruef;
  dl('geo', [['Motorradius', f1(k.R) + ' mm'], ['Radius bestimmt durch', k.R_quelle], ['Ausleger (Grundriss)', f1(k.Lr) + ' mm'],
    ['Winkel Ausleger/Symmetrie', f1(k.gamma) + '°'], ['Kragmaß Motorträger c<sub>e</sub>', f1(k.ce, 0) + ' mm'],
    ['Blattspitzenabstand', f1(p.spitzenabstand_mm) + ' mm'], ['Rotorebene oben', 'z = ' + f1(k.rotor_oben_z, 0) + ' mm'],
    ...(k.rotor_unten ? [['Rotorebene unten', 'z = ' + f1(k.rotor_unten.rotorebene_z_mm, 0) + ' mm'], ['Hülle unten (Unterkante)', 'z = ' + f1(k.rotor_unten.huelle_unterkante_z_mm, 0) + ' mm']] : [])]);
  dl('pruef', [['Volumenkollisionen (' + k.tests + ' Paare)', ...ja(k.kollisionsfrei)], ['Grundrissfreiraum Rotor', f1(p.grundriss_freiraum_mm) + ' mm', p.grundriss_ok ? 'ok' : 'bad'],
    ['Freiraum oberer Rotor', f1(p.oberer_rotor_freiraum_mm) + ' mm', p.oberer_rotor_ok ? 'ok' : 'bad'],
    ...(k.rotor_unten ? [['Freiraum unterer Rotor', f1(k.rotor_unten.freiraum_struktur_mm) + ' mm', p.unterer_rotor_ok ? 'ok' : 'bad']] : []),
    ['Systemlinien zentrisch', p.systemlinien_zentrisch ? 'ja' : 'nein (Biegung)', p.systemlinien_zentrisch ? 'ok' : 'warn'],
    ['Stabwerk-Screening', ...ja(p.stabwerk_screening_ok)],
    ...(k.statik.dynamik ? [['Eigenfrequenz seitlich / vertikal', `${f1(k.statik.dynamik.f_seitlich_Hz)} / ${f1(k.statik.dynamik.f_vertikal_Hz)} Hz`, k.statik.dynamik.f_min_Hz >= 15 ? 'ok' : 'bad']] : [])]);
  const s = k.statik;
  if (s.staebe) $('statik').innerHTML = `<p class="note">Schub je Ausleger ${f1(s.schub_je_ausleger_N, 0)} N (Lastfall × LF)</p><table><tr><th>Rohr</th><th>Kraft N</th><th>σ CFK</th><th>Knick CFK</th><th>Knick Alu</th></tr>` +
    s.staebe.map(r => `<tr><td>${r.anschluss && r.anschluss !== 'verbinder' ? (r.anschluss === 'ecke_oben' ? 'Ecke oben' : 'Ecke unten') : 'Verbinder'} z<sub>0</sub>=${f1(r.wurzel_z_mm, 0)}</td><td>${f1(r.stabkraft_N, 0)}</td><td>${f1(r.cfk_ausnutzung, 2)}</td><td class="${r.knick_ausnutzung > 1 ? 'bad' : ''}">${f1(r.knick_ausnutzung, 2)}</td><td>${f1(r.alu_strebe_knick_ausnutzung, 2)}</td></tr>`).join('') + '</table>';
  else $('statik').innerHTML = `<p>Einrohr-Kragarm: Wurzelmoment ${f1(s.wurzelmoment_Nm, 0)} Nm, Biegespannung ${f1(s.biegespannung_MPa, 0)} MPa, Ausnutzung <b class="${s.ausnutzung > 1 ? 'bad' : 'ok'}">${f1(s.ausnutzung, 2)}</b></p>`;
  const a = k.ausruestung, sa = k.statik_ausruestung;
  if (a) {
    const f = a.fussschlitten, l = a.landegestell, r = a.regler, ma = (k.massen || {}).ausruestung || {};
    dl('aus', [['Fußschlitten', f.modus], ['Schienenlänge', f1(2*f.bock_x_mm, 0) + ' mm'], ['Fußmitte (min / gewählt / max)', `±${f1(f.fuss_x_min_mm, 0)} / ±${f1(f.fuss_x_mm, 0)} / ±${f1(f.fuss_x_max_mm, 0)}`, f.verstellbereich_ok ? '' : 'bad'],
      ['Nennstand ±200 mm', f.nennstand_200mm_moeglich ? 'möglich' : 'nicht möglich', f.nennstand_200mm_moeglich ? 'ok' : 'warn'],
      ['Schiene / Stütze / Strebe', `${f1(sa.fussschlitten.schienen_ausnutzung, 2)} / ${f1(sa.fussschlitten.stuetze_knick_ausnutzung, 2)} / ${f1(sa.fussschlitten.strebe_knick_ausnutzung, 2)}`, sa.fussschlitten.bestanden ? 'ok' : 'bad'],
      ['Bock über Rotor', f.bock_rotor_ok ? 'frei' : 'zu knapp', f.bock_rotor_ok ? 'ok' : 'bad'],
      ['Landefüße', `${l.anzahl} Eckfüße, Boden z ${f1(l.boden_z_mm, 0)} mm`], ['Kippkante zur Mitte', f1(l.kippkante_mm, 0) + ' mm', 'warn'],
      ...(l.unterer_rotor_ueber_boden_mm !== null ? [['Unterer Rotor über Boden', f1(l.unterer_rotor_ueber_boden_mm, 0) + ' mm', l.unterer_rotor_boden_ok ? 'ok' : 'bad']] : []),
      ['Pfosten (3 g, 2 Füße)', `${f1(sa.landung.pfosten_druck_N, 0)} N / Knick ${f1(sa.landung.pfosten_knick_ausnutzung, 2)}`, sa.landung.bestanden ? 'ok' : 'bad'],
      ['Regler', `${r.seiten.length} je Ausleger, ${r.lage}`, r.passt ? '' : 'bad'], ['Reglerende–Motorachse', f1(r.abstand_reglerende_motorachse_mm, 0) + ' mm', r.phasenkabel_reicht ? 'ok' : 'bad'],
      ['Freiraum Regler–Rotor', f1(r.freiraum_oben_mm, 0) + (r.freiraum_unten_mm !== null ? ' / ' + f1(r.freiraum_unten_mm, 0) : '') + ' mm'],
      ['Ausrüstung (ohne Regler)', f1(ma.ausruestung_gesamt_ohne_regler_kg, 2) + ' kg'], ['Regler (Katalog)', `${ma.regler_anzahl} × 748 g`]]);
  }
  const m = k.massen;
  dl('masse', [['Dreiecksverbinder', `${m.verbinder_anzahl} × ${f1(m.verbinder_je_stueck_kg * 1000, 0)} g`], ['Motorträger', `${m.motortraeger_anzahl} × ${f1(m.motortraeger_je_stueck_kg * 1000, 0)} g`],
    ['Eckknoten', `${m.eckknoten_anzahl} × ${f1(m.eckknoten_je_stueck_kg * 1000, 0)} g`], ['CFK je Ausleger', f1(m.auslegerrohre_je_ausleger_kg * 1000, 0) + ' g'],
    ['Struktur gesamt', f1(m.struktur_gesamt_kg, 2) + ' kg'], ['Motoren', m.motoren_gesamt]]);
  $('zuschnitt').innerHTML = '<table><tr><th>Teil</th><th>Ø</th><th>Länge</th><th>Stk.</th></tr>' + k.zuschnitt.map(z => `<tr><td>${z.teil}${z.index !== undefined ? ' ' + (z.index + 1) : ''}</td><td>${z.od}/${z.id}</td><td>${f1(z.laenge_mm)}</td><td>${z.anzahl}</td></tr>`).join('') + '</table>';
}

function lade(src) { return new Promise((ok, err) => { const s = document.createElement('script'); s.src = src; s.onload = ok; s.onerror = () => err(Error('Datei fehlt: ' + src)); document.body.appendChild(s); }); }
window.D14_DATEN = d => { state.daten[d.schluessel] = d; };
window.D14_ECKE = d => { state.ecken[d.bauweise] = d; };
window.D14_PROPELLER = d => { state.prop[d.id] = {raw: d}; };
window.D14_D12 = d => { state.d12 = d; };
async function waehle() {
  const bw = $('bauweise').value, p = $('propeller').value, v = $('variante').value, key = `${bw}_${p}_${v}`;
  state.sel = {bw, p, v, key}; state.ready = false;
  try {
    if (!state.index.konfigurationen[key]) throw Error('Konfiguration nicht gebaut: ' + key);
    if (!state.daten[key]) await lade(`Ausgabe/viewer/${key}.js`);
    if (!state.ecken[bw]) await lade(`Ausgabe/viewer/Eckknoten_${bw}.js`);
    if (!state.prop[p]) await lade(`Ausgabe/viewer/Propeller_${p}.js`).catch(() => {});
    if (!state.d12) await lade('Ausgabe/viewer/Fussschlitten_D12.js').catch(() => {});
    $('fehler').textContent = '';
    const neu = state.letzteBw !== bw || state.letzterP !== p; state.letzteBw = bw; state.letzterP = p;
    baueSzene(); panel(); if (neu || !state.ansicht) ansicht(state.ansicht || 'gesamt'); else ansicht(state.ansicht);
    location.hash = `b=${bw}&p=${p}&v=${v}&a=${state.ansicht}`;
  } catch (e) { $('fehler').textContent = e.message; }
}
window.D14_INDEX = idx => {
  state.index = idx;
  const h = Object.fromEntries(location.hash.slice(1).split('&').filter(Boolean).map(x => x.split('=')));
  const opt = (el, items, sel) => { $(el).innerHTML = items.map(([v, t]) => `<option value="${v}" ${v === sel ? 'selected' : ''}>${t}</option>`).join(''); };
  opt('bauweise', Object.entries(idx.bauweisen), h.b || idx.standard.bauweise);
  opt('propeller', idx.propeller.map(p => [p.id, p.label]), h.p || idx.standard.propeller);
  opt('variante', Object.entries(idx.varianten).map(([k, t]) => [k, k + ' · ' + t]), h.v || idx.standard.variante);
  state.ansicht = h.a || 'gesamt';
  ['bauweise', 'propeller', 'variante'].forEach(i => $(i).onchange = waehle);
  ['zeigeRotor', 'zeigePropeller', 'zeigeSystem', 'zeigeSchrauben', 'zeigeAusruestung'].forEach(i => $(i).onchange = baueSzene);
  document.querySelectorAll('button[data-v]').forEach(b => b.onclick = () => { ansicht(b.dataset.v); location.hash = location.hash.replace(/a=\w+/, 'a=' + b.dataset.v); });
  waehle(); requestAnimationFrame(draw);
};

// ------------------------------------------------------------ Maus
let drag = null;
canvas.addEventListener('contextmenu', e => e.preventDefault());
canvas.addEventListener('pointerdown', e => { drag = {x: e.clientX, y: e.clientY, pan: e.shiftKey || e.button === 2}; canvas.setPointerCapture(e.pointerId); });
canvas.addEventListener('pointerup', () => drag = null);
canvas.addEventListener('pointermove', e => {
  if (!drag) return; const dx = e.clientX - drag.x, dy = e.clientY - drag.y; drag.x = e.clientX; drag.y = e.clientY;
  if (drag.pan) { const s = state.dist*0.9, cy = Math.cos(state.yaw), sy = Math.sin(state.yaw);
    state.target = [state.target[0] + (sy*dx)*s, state.target[1] - (cy*dx)*s, state.target[2] + dy*s]; }
  else { state.yaw -= dx*0.008; state.pitch = Math.max(-1.55, Math.min(1.55, state.pitch + dy*0.008)); }
});
canvas.addEventListener('wheel', e => { e.preventDefault(); state.dist *= Math.exp(e.deltaY*0.001); }, {passive: false});
})();
