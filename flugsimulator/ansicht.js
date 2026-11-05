/* 3D-Ansicht des Flugsimulators: D14-CAD-Netze (aus ../multirotor_d14/Ausgabe/viewer) im Flugzustand,
 * drehende D13-Propeller, Boden mit Raster, Schatten, Person, Abwind-/Windpartikel. Welt in mm, z oben. */
(function(root){
'use strict';
const I4 = () => [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1];
function mul(a, b) { const o = new Array(16).fill(0); for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) { let s = 0; for (let k = 0; k < 4; k++) s += a[k*4+r]*b[c*4+k]; o[c*4+r] = s; } return o; }
const rz = d => { const c = Math.cos(d*Math.PI/180), s = Math.sin(d*Math.PI/180); return [c,s,0,0, -s,c,0,0, 0,0,1,0, 0,0,0,1]; };
const tr = (x, y, z) => [1,0,0,0, 0,1,0,0, 0,0,1,0, x,y,z,1];
const SY = [1,0,0,0, 0,-1,0,0, 0,0,1,0, 0,0,0,1], SZ = [1,0,0,0, 0,1,0,0, 0,0,-1,0, 0,0,0,1];
function persp(f, a, n, fa) { const t = 1/Math.tan(f/2); return [t/a,0,0,0, 0,t,0,0, 0,0,(fa+n)/(n-fa),-1, 0,0,2*fa*n/(n-fa),0]; }
function lookAt(e, c, u) {
  let z = [e[0]-c[0], e[1]-c[1], e[2]-c[2]]; let l = Math.hypot(...z); z = z.map(v => v/l);
  let x = [u[1]*z[2]-u[2]*z[1], u[2]*z[0]-u[0]*z[2], u[0]*z[1]-u[1]*z[0]]; l = Math.hypot(...x) || 1; x = x.map(v => v/l);
  const y = [z[1]*x[2]-z[2]*x[1], z[2]*x[0]-z[0]*x[2], z[0]*x[1]-z[1]*x[0]];
  return [x[0],y[0],z[0],0, x[1],y[1],z[1],0, x[2],y[2],z[2],0, -(x[0]*e[0]+x[1]*e[1]+x[2]*e[2]), -(y[0]*e[0]+y[1]*e[1]+y[2]*e[2]), -(z[0]*e[0]+z[1]*e[1]+z[2]*e[2]), 1];
}
function quatMat(q) { const [w, x, y, z] = q;
  return [1-2*(y*y+z*z), 2*(x*y+w*z), 2*(x*z-w*y), 0, 2*(x*y-w*z), 1-2*(x*x+z*z), 2*(y*z+w*x), 0, 2*(x*z+w*y), 2*(y*z-w*x), 1-2*(x*x+y*y), 0, 0,0,0,1]; }
function achse(a, b) {
  const d = [b[0]-a[0], b[1]-a[1], b[2]-a[2]], L = Math.hypot(...d), z = d.map(v => v/L);
  let x = Math.abs(z[2]) < .9 ? [z[1], -z[0], 0] : [1, 0, 0]; let l = Math.hypot(...x); x = x.map(v => v/l);
  const y = [z[1]*x[2]-z[2]*x[1], z[2]*x[0]-z[0]*x[2], z[0]*x[1]-z[1]*x[0]];
  return [x[0],x[1],x[2],0, y[0],y[1],y[2],0, z[0]*L,z[1]*L,z[2]*L,0, a[0],a[1],a[2],1];
}
const FARBE = {alu: [.74,.77,.80], carbon: [.12,.14,.16], schraube: [.30,.31,.33], motor: [.86,.50,.16], rahmen: [.12,.14,.16], sohle: [.10,.10,.11], regler: [.16,.30,.52], d12: [.62,.70,.78], person: [.30,.42,.58], haut: [.85,.68,.55], scheibe: [.55,.65,.75], bruch: [.85,.2,.2]};

class Ansicht {
  constructor(canvas) {
    this.canvas = canvas;
    const gl = this.gl = canvas.getContext('webgl', {antialias: true, alpha: false, preserveDrawingBuffer: true});
    if (!gl) throw Error('WebGL nicht verfügbar');
    const sh = (t, s) => { const o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o); if (!gl.getShaderParameter(o, gl.COMPILE_STATUS)) throw Error(gl.getShaderInfoLog(o)); return o; };
    const prog = (vs, fs) => { const p = gl.createProgram(); gl.attachShader(p, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(p, sh(gl.FRAGMENT_SHADER, fs)); gl.linkProgram(p); return p; };
    this.p = prog('attribute vec3 p;attribute vec3 n;uniform mat4 m;uniform mat4 vp;varying vec3 vn;varying vec3 wp;void main(){vec4 w=m*vec4(p,1.);wp=w.xyz;vn=mat3(m)*n;gl_Position=vp*w;}',
      'precision mediump float;varying vec3 vn;varying vec3 wp;uniform vec3 col;uniform float alpha;uniform float carbon;uniform float unlit;uniform vec3 eye;void main(){vec3 N=normalize(vn);float l=.34+.52*abs(dot(N,normalize(vec3(.35,-.45,.82))))+.16*pow(abs(dot(N,normalize(vec3(-.6,.3,.4)))),8.);float w=mod(floor(wp.x/6.)+floor(wp.y/6.)+floor(wp.z/6.),2.);vec3 c=col*mix(1.,.86+.14*w,carbon);vec3 o=mix(c*l,col,unlit);float d=length(wp-eye);float f=clamp((d-18000.)/110000.,0.,.92);gl_FragColor=vec4(mix(o,vec3(.80,.86,.90),f),alpha);}');
    this.pc = prog('attribute vec3 p;attribute vec4 c;uniform mat4 vp;varying vec4 vc;void main(){vc=c;gl_Position=vp*vec4(p,1.);gl_PointSize=3.;}', 'precision mediump float;varying vec4 vc;void main(){gl_FragColor=vc;}');
    this.loc = {}; for (const k of ['p', 'n']) this.loc[k] = gl.getAttribLocation(this.p, k);
    for (const k of ['m', 'vp', 'col', 'alpha', 'carbon', 'unlit', 'eye']) this.loc[k] = gl.getUniformLocation(this.p, k);
    this.lc = {p: gl.getAttribLocation(this.pc, 'p'), c: gl.getAttribLocation(this.pc, 'c'), vp: gl.getUniformLocation(this.pc, 'vp')};
    this.cache = {}; this.objekte = []; this.propObjekte = []; this.kam = {modus: 'verfolger', az: -2.4, el: 0.32, dist: 6500, ziel: [0, 0, 1000], glatt: null};
    this.partikelBuf = gl.createBuffer(); this.partikelFarbe = gl.createBuffer();
    this.boden(); this.mausSteuerung();
  }
  upload(pos, nor, mode) { const gl = this.gl;
    const b1 = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b1); gl.bufferData(gl.ARRAY_BUFFER, pos, gl.STATIC_DRAW);
    const b2 = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b2); gl.bufferData(gl.ARRAY_BUFFER, nor, gl.STATIC_DRAW);
    return {b1, b2, n: pos.length/3, mode: mode ?? gl.TRIANGLES}; }
  decode(m) {
    if (!m) return null;
    const b64 = (s, T) => { const bin = atob(s), u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); return new T(u.buffer); };
    const q = b64(m.v, Int16Array), idx = b64(m.i, m.i32 ? Uint32Array : Uint16Array), pos = new Float32Array(idx.length*3);
    for (let i = 0; i < idx.length; i++) for (let k = 0; k < 3; k++) pos[i*3+k] = m.c[k] + q[idx[i]*3+k]*m.s;
    const n = new Float32Array(pos.length);
    for (let i = 0; i < pos.length; i += 9) {
      const ax = pos[i+3]-pos[i], ay = pos[i+4]-pos[i+1], az = pos[i+5]-pos[i+2], bx = pos[i+6]-pos[i], by = pos[i+7]-pos[i+1], bz = pos[i+8]-pos[i+2];
      let x = ay*bz-az*by, y = az*bx-ax*bz, z = ax*by-ay*bx; const l = Math.hypot(x, y, z) || 1;
      for (let k = 0; k < 3; k++) { n[i+3*k] = x/l; n[i+3*k+1] = y/l; n[i+3*k+2] = z/l; }
    }
    return this.upload(pos, n);
  }
  rohr(od, id) { const key = 'r' + od + '/' + id; if (this.cache[key]) return this.cache[key];
    const N = 24, P = [], Nn = [], ro = od/2, ri = id/2;
    for (let i = 0; i < N; i++) { const a0 = 2*Math.PI*i/N, a1 = 2*Math.PI*(i+1)/N, c0 = Math.cos(a0), s0 = Math.sin(a0), c1 = Math.cos(a1), s1 = Math.sin(a1);
      for (const [r, sg] of [[ro, 1], [ri, -1]]) { P.push(r*c0,r*s0,0, r*c1,r*s1,0, r*c1,r*s1,1, r*c0,r*s0,0, r*c1,r*s1,1, r*c0,r*s0,1);
        for (let k = 0; k < 6; k++) { const c = k===1||k===2||k===4 ? c1 : c0, s = k===1||k===2||k===4 ? s1 : s0; Nn.push(sg*c, sg*s, 0); } } }
    return this.cache[key] = this.upload(new Float32Array(P), new Float32Array(Nn)); }
  zylinder(r, N = 40) { const key = 'z' + r + '/' + N; if (this.cache[key]) return this.cache[key];
    const P = [], Nn = [];
    for (let i = 0; i < N; i++) { const a0 = 2*Math.PI*i/N, a1 = 2*Math.PI*(i+1)/N, c0 = Math.cos(a0), s0 = Math.sin(a0), c1 = Math.cos(a1), s1 = Math.sin(a1);
      P.push(r*c0,r*s0,0, r*c1,r*s1,0, r*c1,r*s1,1, r*c0,r*s0,0, r*c1,r*s1,1, r*c0,r*s0,1);
      for (let k = 0; k < 6; k++) { const c = k===1||k===2||k===4 ? c1 : c0, s = k===1||k===2||k===4 ? s1 : s0; Nn.push(c, s, 0); }
      for (const z of [0, 1]) { P.push(0,0,z, r*c0,r*s0,z, r*c1,r*s1,z); Nn.push(0,0,z?1:-1, 0,0,z?1:-1, 0,0,z?1:-1); } }
    return this.cache[key] = this.upload(new Float32Array(P), new Float32Array(Nn)); }
  kugel(r) { const key = 'k' + r; if (this.cache[key]) return this.cache[key];
    const P = [], Nn = [], A = 16, B = 10, pt = (a, b) => [Math.cos(a)*Math.sin(b), Math.sin(a)*Math.sin(b), Math.cos(b)];
    for (let i = 0; i < A; i++) for (let j = 0; j < B; j++) { const a0 = 2*Math.PI*i/A, a1 = 2*Math.PI*(i+1)/A, b0 = Math.PI*j/B, b1 = Math.PI*(j+1)/B;
      for (const v of [pt(a0, b0), pt(a1, b0), pt(a1, b1), pt(a0, b0), pt(a1, b1), pt(a0, b1)]) { P.push(v[0]*r, v[1]*r, v[2]*r); Nn.push(...v); } }
    return this.cache[key] = this.upload(new Float32Array(P), new Float32Array(Nn)); }
  boden() {
    const P = [], N = [], S = 200000;
    P.push(-S,-S,0, S,-S,0, S,S,0, -S,-S,0, S,S,0, -S,S,0); for (let i = 0; i < 6; i++) N.push(0, 0, 1);
    this.bodenFlaeche = this.upload(new Float32Array(P), new Float32Array(N));
    const L = [], L2 = [];
    for (let i = -25; i <= 25; i++) { const a = i*1000; if (i % 10) L.push(a, -25000, 2, a, 25000, 2, -25000, a, 2, 25000, a, 2); }
    for (let i = -6; i <= 6; i++) { const a = i*10000; L2.push(a, -60000, 2, a, 60000, 2, -60000, a, 2, 60000, a, 2); }
    this.raster = this.upload(new Float32Array(L), new Float32Array(L.length), this.gl.LINES);
    this.raster10 = this.upload(new Float32Array(L2), new Float32Array(L2.length), this.gl.LINES);
    // Startkreis
    const K = []; for (let i = 0; i < 64; i++) { const a0 = i/64*2*Math.PI, a1 = (i+1)/64*2*Math.PI; K.push(2500*Math.cos(a0), 2500*Math.sin(a0), 3, 2500*Math.cos(a1), 2500*Math.sin(a1), 3); }
    this.startkreis = this.upload(new Float32Array(K), new Float32Array(K.length), this.gl.LINES);
  }
  /* D14-Daten in Koerperobjekte (CAD-mm) uebersetzen. rotorIndex: Zuordnung Motor/Lage -> Physikrotor */
  ladeModell(d, e, pm, d12, info) {
    const ob = [], props = [];
    this.info = info; this.cache.d14 = {};
    if (d && e) {
      const ms = {}; for (const [k, m] of Object.entries(d.meshes)) ms[k] = this.decode(m);
      const eq = d.eck_meshes || e;          // V4: konfigurationseigene Eckknoten
      const em = this.decode(eq.eckknoten), es = this.decode(eq.eckknoten_schrauben), eu = this.decode(eq.eckknoten_unten);
      d.paarwinkel.forEach((phi, j) => {
        const R = rz(phi), RS = mul(R, SY);
        ob.push({g: ms.verbinder, m: R, c: FARBE.alu}, {g: ms.verbinder_schrauben, m: R, c: FARBE.schraube});
        [R, RS].forEach((M, side) => {
          const arm = info.armVonPaar(j, side);
          ob.push({g: ms.motortraeger, m: M, c: FARBE.alu, arm}, {g: ms.motortraeger_schrauben, m: M, c: FARBE.schraube, arm});
          d.rohre.forEach(r => ob.push({g: this.rohr(r.od, r.id), m: mul(M, achse(r.a, r.b)), c: FARBE.carbon, carbon: 1, arm}));
          d.motor.lagen.forEach(l => { const md_ = info.motorMass || [d.motor.d, l.h], h = md_[1], z0 = l.z0 + l.h - h;   // Flanschseite bleibt, Gehaeuse nach gewaehltem Motor
            ob.push({g: this.zylinder(md_[0]/2), m: mul(M, [1,0,0,0, 0,1,0,0, 0,0,h,0, d.motor.xy[0], d.motor.xy[1], z0, 1]), c: FARBE.motor, arm}); });
        });
        if (!d.ecken) for (const M of [R, RS, mul(R, SZ), mul(RS, SZ)]) ob.push({g: em, m: M, c: FARBE.alu}, {g: es, m: M, c: FARBE.schraube});
        if (d.regler_meshes) { const h = this.cache.d14.h || (this.cache.d14 = {h: this.decode(d.regler_meshes.halter), s: this.decode(d.regler_meshes.schrauben), r: this.decode(d.regler_meshes.regler)});
          for (const M of [R, RS]) ob.push({g: this.cache.d14.h, m: M, c: FARBE.alu}, {g: this.cache.d14.r, m: M, c: FARBE.regler}, {g: this.cache.d14.s, m: M, c: FARBE.schraube}); }
      });
      if (d.ecken) { const esu = eq.eckknoten_schrauben_unten ? this.decode(eq.eckknoten_schrauben_unten) : es; d.ecken.forEach(E => ob.push({g: E.u ? eu : em, m: E.m, c: FARBE.alu}, {g: E.u ? esu : es, m: E.m, c: FARBE.schraube})); }
      if (d.aus_meshes) {
        ob.push({g: this.decode(d.aus_meshes.alu), m: I4(), c: FARBE.d12}, {g: this.decode(d.aus_meshes.sohle), m: I4(), c: FARBE.sohle}, {g: this.decode(d.aus_meshes.schrauben), m: I4(), c: FARBE.schraube});
        d.aus_rohre.forEach(r => ob.push({g: this.rohr(r.od, r.id), m: achse(r.a, r.b), c: FARBE.carbon, carbon: 1}));
        if (d12) { const dx = d.d12_versatz_x || 0; for (const [seite, sx] of [['plus', 1], ['minus', -1]]) { const g = d12[seite]; g._a = g._a || this.decode(g.alu); g._s = g._s || this.decode(g.schrauben);
          ob.push({g: g._a, m: tr(sx*dx, 0, 0), c: FARBE.d12}, {g: g._s, m: tr(sx*dx, 0, 0), c: FARBE.schraube}); } }
      }
      d.rahmen.forEach(r => ob.push({g: this.rohr(r.od, r.id), m: achse(r.a, r.b), c: FARBE.rahmen, carbon: 1}));
      const g = pm ? {CW: this.decode(pm.cw), CCW: this.decode(pm.ccw)} : null;
      d.motoren.forEach((m, j) => {
        const base = [m.xy[0], m.xy[1]], lagen = [{unten: false}]; if (d.propeller && d.propeller.nabe_unten_z !== null) lagen.push({unten: true});
        lagen.forEach(L => props.push({g: g ? g[m.drehrichtung] : null, xy: base, winkel: m.winkel_grad, unten: L.unten, mz: L.unten ? [1,0,0,0, 0,1,0,0, 0,0,-1,0, 0,0, d.propeller.nabe_unten_z + d.propeller.nabe_z, 1] : null,
          rotor: info.rotorVon(j, L.unten), r: d.rotor.d/2, z: L.unten ? d.rotor.lagen[1].z : d.rotor.lagen[0].z}));
      });
      this.cadGeladen = true;
    } else {
      // Ersatzdarstellung ohne CAD-Netze: Rahmen, Ausleger, Motoren, Scheiben
      info.ersatz.forEach(o => ob.push(o.typ === 'rohr' ? {g: this.rohr(o.od, o.id), m: achse(o.a, o.b), c: FARBE.carbon, carbon: 1, arm: o.arm} : {g: this.zylinder(o.r), m: [1,0,0,0, 0,1,0,0, 0,0,o.h,0, o.p[0], o.p[1], o.p[2], 1], c: FARBE[o.farbe] || FARBE.alu, arm: o.arm}));
      info.ersatzProps.forEach(p => props.push(Object.assign({g: null}, p)));
      this.cadGeladen = false;
    }
    // Person (Groessenreferenz, starr), Fuesse auf den Fussplatten
    if (info.person) { const P = info.person, z0 = P.z, fx = P.fx, sk = P.groesse/1.75;
      const zyl = (r, a, b, c) => ob.push({g: this.rohr(2*r, 0.01), m: achse(a, b), c, person: 1});
      zyl(55*sk, [fx, 0, z0], [fx*0.35, 0, z0 + 880*sk], FARBE.person); zyl(55*sk, [-fx, 0, z0], [-fx*0.35, 0, z0 + 880*sk], FARBE.person);
      zyl(150*sk, [0, 0, z0 + 860*sk], [0, 0, z0 + 1430*sk], FARBE.person);
      zyl(40*sk, [130*sk, 0, z0 + 1400*sk], [260*sk, -120*sk, z0 + 1000*sk], FARBE.person); zyl(40*sk, [-130*sk, 0, z0 + 1400*sk], [-260*sk, -120*sk, z0 + 1000*sk], FARBE.person);
      ob.push({g: this.kugel(105*sk), m: tr(0, 0, z0 + 1600*sk), c: FARBE.haut, person: 1}); }
    this.objekte = ob.filter(o => o.g); this.propObjekte = props; this.scheibe = this.zylinder(1, 64);
  }
  mausSteuerung() {
    const c = this.canvas; let drag = null;
    c.addEventListener('contextmenu', e => e.preventDefault());
    c.addEventListener('pointerdown', e => { drag = {x: e.clientX, y: e.clientY}; c.setPointerCapture(e.pointerId); });
    c.addEventListener('pointerup', () => drag = null);
    c.addEventListener('pointermove', e => { if (!drag) return; const dx = e.clientX - drag.x, dy = e.clientY - drag.y; drag.x = e.clientX; drag.y = e.clientY;
      this.kam.az -= dx*0.008; this.kam.el = Math.max(-0.2, Math.min(1.5, this.kam.el + dy*0.006)); this.kam.manuell = performance.now(); });
    c.addEventListener('wheel', e => { e.preventDefault(); this.kam.dist = Math.max(1200, Math.min(80000, this.kam.dist*Math.exp(e.deltaY*0.001))); }, {passive: false});
  }
  /* z: {x(m), q, cg(m), om[], winkel[], aus[], armBruch Set, partikel {pos Float32Array, farbe, n}, gierWelt} */
  zeichne(z) {
    const gl = this.gl, c = this.canvas, w = c.clientWidth, h = c.clientHeight, dpr = Math.min(2, devicePixelRatio || 1);
    if (c.width !== Math.round(w*dpr) || c.height !== Math.round(h*dpr)) { c.width = Math.round(w*dpr); c.height = Math.round(h*dpr); }
    gl.viewport(0, 0, c.width, c.height); gl.clearColor(.80, .86, .90, 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT); gl.enable(gl.DEPTH_TEST);
    const pos = z.x.map(v => v*1000), cg = z.cg.map(v => v*1000);
    const W = mul(mul(tr(...pos), quatMat(z.q)), tr(-cg[0], -cg[1], -cg[2]));
    // Kamera
    const k = this.kam, ziel = [pos[0], pos[1], pos[2]];
    if (!k.glatt) k.glatt = [...ziel]; for (let i = 0; i < 3; i++) k.glatt[i] += (ziel[i] - k.glatt[i])*0.12;
    let eye, t = k.glatt;
    if (k.modus === 'verfolger') { const az = (performance.now() - (k.manuell || 0) < 2500) ? k.az : (k.az += ((z.gierWelt + Math.PI) - k.az - Math.round(((z.gierWelt + Math.PI) - k.az)/(2*Math.PI))*2*Math.PI)*0.02);
      eye = [t[0] + k.dist*Math.cos(k.el)*Math.cos(az), t[1] + k.dist*Math.cos(k.el)*Math.sin(az), t[2] + k.dist*Math.sin(k.el)]; }
    else if (k.modus === 'orbit') eye = [t[0] + k.dist*Math.cos(k.el)*Math.cos(k.az), t[1] + k.dist*Math.cos(k.el)*Math.sin(k.az), t[2] + k.dist*Math.sin(k.el)];
    else if (k.modus === 'boden') eye = [-9000, -9000, 1700];
    else if (k.modus === 'oben') eye = [t[0] + 1, t[1] - 1, t[2] + Math.max(k.dist*1.6, 6000)];
    eye[2] = Math.max(eye[2], 300);
    const VP = mul(persp(k.modus === 'boden' ? 0.55 : 0.8, w/h, 60, 400000), lookAt(eye, t, [0, 0, 1]));
    this.VP = VP;
    gl.useProgram(this.p); gl.uniformMatrix4fv(this.loc.vp, false, VP); gl.uniform3fv(this.loc.eye, eye);
    const L = this.loc;
    const draw = (g, m, col, alpha = 1, carbon = 0, unlit = 0) => {
      gl.bindBuffer(gl.ARRAY_BUFFER, g.b1); gl.enableVertexAttribArray(L.p); gl.vertexAttribPointer(L.p, 3, gl.FLOAT, false, 0, 0);
      gl.bindBuffer(gl.ARRAY_BUFFER, g.b2); gl.enableVertexAttribArray(L.n); gl.vertexAttribPointer(L.n, 3, gl.FLOAT, false, 0, 0);
      gl.uniformMatrix4fv(L.m, false, m); gl.uniform3fv(L.col, col); gl.uniform1f(L.alpha, alpha); gl.uniform1f(L.carbon, carbon); gl.uniform1f(L.unlit, unlit);
      gl.drawArrays(g.mode, 0, g.n); };
    // Boden + Raster
    draw(this.bodenFlaeche, I4(), [.60, .66, .58], 1, 0, 1);
    gl.depthMask(false); draw(this.raster, I4(), [.55, .61, .54], 1, 0, 1); draw(this.raster10, I4(), [.46, .52, .46], 1, 0, 1); draw(this.startkreis, I4(), [.85, .55, .2], 1, 0, 1); gl.depthMask(true);
    // Schatten: Projektion auf z = 1 mm entlang Lichtrichtung
    const ld = [0.25, -0.2, 1], S = [1,0,0,0, 0,1,0,0, -ld[0]/ld[2], -ld[1]/ld[2], 0, 0, 0,0,1.5,1];
    gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); gl.depthMask(false);
    const alpha = Math.max(0.08, 0.32 - pos[2]/40000);
    for (const o of this.objekte) if (!o.person || z.person) draw(o.g, mul(S, mul(W, o.m)), [0.2, 0.25, 0.2], alpha, 0, 1);
    gl.depthMask(true); gl.disable(gl.BLEND);
    // Fahrzeug
    for (const o of this.objekte) { if (o.person && !z.person) continue; const br = o.arm !== undefined && z.armBruch && z.armBruch.has(o.arm);
      draw(o.g, mul(W, o.m), br ? FARBE.bruch : o.c, 1, o.carbon || 0); }
    // Propeller
    gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    const scheiben = [];
    for (const p of this.propObjekte) {
      const om = z.om[p.rotor] || 0, ang = (z.winkel[p.rotor] || 0)*180/Math.PI, schnell = om > 50;
      if (p.g) { let M = mul(tr(p.xy[0], p.xy[1], 0), rz(p.winkel + ang)); if (p.mz) M = mul(M, p.mz); draw(p.g, mul(W, M), z.aus[p.rotor] ? [.5, .15, .1] : FARBE.carbon, schnell ? 0.30 : 1, 1); }
      if (schnell) scheiben.push(p);
    }
    gl.depthMask(false);
    for (const p of scheiben) { const om = z.om[p.rotor]; draw(this.scheibe, mul(W, [p.r,0,0,0, 0,p.r,0,0, 0,0,2,0, p.xy[0], p.xy[1], p.z - 1, 1]), FARBE.scheibe, Math.min(0.22, om/2500), 0, 1); }
    // Partikel (Abwind/Wind)
    if (z.partikel && z.partikel.n) {
      gl.useProgram(this.pc); gl.uniformMatrix4fv(this.lc.vp, false, VP);
      gl.bindBuffer(gl.ARRAY_BUFFER, this.partikelBuf); gl.bufferData(gl.ARRAY_BUFFER, z.partikel.pos, gl.DYNAMIC_DRAW);
      gl.enableVertexAttribArray(this.lc.p); gl.vertexAttribPointer(this.lc.p, 3, gl.FLOAT, false, 0, 0);
      gl.bindBuffer(gl.ARRAY_BUFFER, this.partikelFarbe); gl.bufferData(gl.ARRAY_BUFFER, z.partikel.farbe, gl.DYNAMIC_DRAW);
      gl.enableVertexAttribArray(this.lc.c); gl.vertexAttribPointer(this.lc.c, 4, gl.FLOAT, false, 0, 0);
      gl.drawArrays(gl.LINES, 0, z.partikel.n*2);
      gl.disableVertexAttribArray(this.lc.c);
    }
    gl.depthMask(true); gl.disable(gl.BLEND);
  }
  projiziere(p) { const VP = this.VP, c = [VP[0]*p[0]+VP[4]*p[1]+VP[8]*p[2]+VP[12], VP[1]*p[0]+VP[5]*p[1]+VP[9]*p[2]+VP[13], VP[3]*p[0]+VP[7]*p[1]+VP[11]*p[2]+VP[15]];
    if (c[2] <= 0) return null; return [(c[0]/c[2]+1)/2*this.canvas.clientWidth, (1-c[1]/c[2])/2*this.canvas.clientHeight]; }
}
root.SimAnsicht = {Ansicht, mul, quatMat};
})(globalThis);
