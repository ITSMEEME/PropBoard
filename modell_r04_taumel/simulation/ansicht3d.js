/* WebGL-Ansicht des H01/P10-Simulators: native P10-CAD-Oberflächen (p10_mesh.js), live aus dem
 * Physikzustand animiert (kinematik_p10.js), Boden, Schatten, Strömungspartikel und Schnittfeld.
 * Nur Darstellung; keine Rückwirkung auf die Physik. */
(function(root){'use strict';
function b64(s,Type){const raw=atob(s),u=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)u[i]=raw.charCodeAt(i);return new Type(u.buffer);}
function mul(a,b,o=new Float32Array(16)){for(let c=0;c<4;c++)for(let r=0;r<4;r++){let s=0;for(let k=0;k<4;k++)s+=a[k*4+r]*b[c*4+k];o[c*4+r]=s;}return o;}
function perspective(fovy,aspect,near,far){const f=1/Math.tan(fovy/2);return new Float32Array([f/aspect,0,0,0,0,f,0,0,0,0,(far+near)/(near-far),-1,0,0,2*far*near/(near-far),0]);}
function lookAt(e,t,u){let z=[e[0]-t[0],e[1]-t[1],e[2]-t[2]],n=Math.hypot(...z);z=z.map(v=>v/n);let x=[u[1]*z[2]-u[2]*z[1],u[2]*z[0]-u[0]*z[2],u[0]*z[1]-u[1]*z[0]];n=Math.hypot(...x)||1;x=x.map(v=>v/n);const y=[z[1]*x[2]-z[2]*x[1],z[2]*x[0]-z[0]*x[2],z[0]*x[1]-z[1]*x[0]],d=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
 return new Float32Array([x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-d(x,e),-d(y,e),-d(z,e),1]);}
function quatMat(q){const[w,x,y,z]=q;return[[1-2*(y*y+z*z),2*(x*y-w*z),2*(x*z+w*y)],[2*(x*y+w*z),1-2*(x*x+z*z),2*(y*z-w*x)],[2*(x*z-w*y),2*(y*z+w*x),1-2*(x*x+y*y)]];}
/** Body (CAD mm) → world (m): T(p)·R(q)·T(−cg)·S(1/1000) */
function bodyMatrix(p,q,cg){const R=quatMat(q),s=.001,o=new Float32Array(16);for(let c=0;c<3;c++)for(let r=0;r<3;r++)o[c*4+r]=R[r][c]*s;
 const t=[0,1,2].map(r=>p[r]-(R[r][0]*cg[0]+R[r][1]*cg[1]+R[r][2]*cg[2]));o[12]=t[0];o[13]=t[1];o[14]=t[2];o[15]=1;return o;}
const VS=`attribute vec3 pos;attribute vec3 nrm;uniform mat4 model;uniform mat4 vp;varying vec3 vN;varying vec3 vW;void main(){vec4 w=model*vec4(pos*0.01,1.0);vW=w.xyz;vN=mat3(model)*nrm;gl_Position=vp*w;}`;
const FS=`precision mediump float;varying vec3 vN;varying vec3 vW;uniform vec3 color;uniform vec3 eye;uniform float alpha;void main(){vec3 n=normalize(vN);vec3 l=normalize(vec3(.35,-.45,.82));vec3 v=normalize(eye-vW);if(dot(n,v)<0.0)n=-n;float d=max(dot(n,l),0.0);float h=pow(max(dot(n,normalize(l+v)),0.0),32.0);float hemi=.5+.5*n.z;vec3 c=color*(.28+.22*hemi+.62*d)+vec3(.22)*h;float fog=clamp((length(eye-vW)-6.0)/20.0,0.0,.7);gl_FragColor=vec4(mix(c,vec3(.08,.11,.15),fog),alpha);}`;
const VS_FLAT=`attribute vec3 pos;attribute vec4 col;uniform mat4 vp;uniform mat4 model;varying vec4 vC;varying vec3 vW;void main(){vec4 w=model*vec4(pos,1.0);vW=w.xyz;vC=col;gl_Position=vp*w;gl_PointSize=2.0;}`;
const FS_FLAT=`precision mediump float;varying vec4 vC;void main(){gl_FragColor=vC;}`;
const VS_GROUND=`attribute vec2 pos;uniform mat4 vp;uniform vec3 shadow;varying vec2 vP;void main(){vP=pos;gl_Position=vp*vec4(pos,0.0,1.0);}`;
const FS_GROUND=`precision mediump float;varying vec2 vP;uniform vec3 shadow;uniform vec3 eye;void main(){vec2 g=abs(fract(vP)-.5);float line=smoothstep(.485,.5,max(g.x,g.y));vec2 g2=abs(fract(vP*10.0)-.5);float fine=smoothstep(.47,.5,max(g2.x,g2.y))*.35;float d=length(vP-shadow.xy);float sh=shadow.z*exp(-d*d/.02);vec3 c=vec3(.16,.19,.17)+vec3(.10,.13,.12)*line+vec3(.03)*fine;c*=1.0-.55*sh;float fog=clamp((length(eye.xy-vP)-5.0)/18.0,0.0,1.0);gl_FragColor=vec4(mix(c,vec3(.08,.11,.15),fog),1.0);}`;
const VS_TEX=`attribute vec3 pos;attribute vec2 uv;uniform mat4 vp;uniform mat4 model;varying vec2 vUV;void main(){vUV=uv;gl_Position=vp*model*vec4(pos,1.0);}`;
const FS_TEX=`precision mediump float;varying vec2 vUV;uniform sampler2D tex;uniform float alpha;void main(){vec4 c=texture2D(tex,vUV);gl_FragColor=vec4(c.rgb,c.a*alpha);}`;
function program(gl,vs,fs){const sh=(t,s)=>{const o=gl.createShader(t);gl.shaderSource(o,s);gl.compileShader(o);if(!gl.getShaderParameter(o,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(o));return o;};const p=gl.createProgram();gl.attachShader(p,sh(gl.VERTEX_SHADER,vs));gl.attachShader(p,sh(gl.FRAGMENT_SHADER,fs));gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));
 const loc={};const n=gl.getProgramParameter(p,gl.ACTIVE_UNIFORMS);for(let i=0;i<n;i++){const u=gl.getActiveUniform(p,i);loc[u.name]=gl.getUniformLocation(p,u.name);}const na=gl.getProgramParameter(p,gl.ACTIVE_ATTRIBUTES);for(let i=0;i<na;i++){const a=gl.getActiveAttrib(p,i);loc[a.name]=gl.getAttribLocation(p,a.name);}return{p,loc};}
function turbo(t){t=Math.max(0,Math.min(1,t));return[Math.max(0,Math.min(1,.13572+t*(4.6153+t*(-42.66+t*(132.13+t*(-152.95+t*59.29)))))),Math.max(0,Math.min(1,.0914+t*(2.194+t*(4.843+t*(-14.18+t*(4.276+t*2.633)))))),Math.max(0,Math.min(1,.1067+t*(12.64+t*(-60.58+t*(110.36+t*(-89.9+t*27.35))))))];}
class View{
 constructor(canvas,mesh,kin){this.canvas=canvas;this.mesh=mesh;this.kin=kin;const gl=canvas.getContext('webgl',{antialias:true,preserveDrawingBuffer:true});if(!gl)throw Error('WebGL nicht verfügbar');this.gl=gl;
  if(!gl.getExtension('OES_element_index_uint'))throw Error('WebGL-Erweiterung OES_element_index_uint fehlt');
  this.solid=program(gl,VS,FS);this.flat=program(gl,VS_FLAT,FS_FLAT);this.ground=program(gl,VS_GROUND,FS_GROUND);this.texp=program(gl,VS_TEX,FS_TEX);
  this.vbo=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,this.vbo);gl.bufferData(gl.ARRAY_BUFFER,b64(mesh.pos,Int16Array),gl.STATIC_DRAW);
  this.nbo=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,this.nbo);gl.bufferData(gl.ARRAY_BUFFER,b64(mesh.nrm,Int8Array),gl.STATIC_DRAW);
  this.ibo=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,this.ibo);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,b64(mesh.idx,Uint32Array),gl.STATIC_DRAW);
  this.gbo=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,this.gbo);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-40,-40,40,-40,40,40,-40,-40,40,40,-40,40]),gl.STATIC_DRAW);
  this.pbo=gl.createBuffer();this.cbo=gl.createBuffer();this.qbo=gl.createBuffer();this.tex=gl.createTexture();
  for(const part of mesh.parts){const m=part.m||[1,0,0,0,1,0,0,0,1,0,0,0];part.M=new Float32Array([m[0],m[1],m[2],0,m[3],m[4],m[5],0,m[6],m[7],m[8],0,m[9],m[10],m[11],1]);}
  this.tmp=new Float32Array(16);this.hidden=new Set(['_none']);this.cam={mode:'chase',yaw:-2.4,elev:.38,dist:1.15,target:[0,0,1]};this.frameMats={};this.drawn=0;this.parts=mesh.parts;this.keys=mesh.keys;
  gl.enable(gl.DEPTH_TEST);gl.clearColor(.08,.11,.15,1);}
 setHidden(groups){this.hidden=new Set(groups);}
 camera(sim,headingYaw){const c=this.cam,p=sim.p;let target=[...p],dist=c.dist,yaw=c.yaw,elev=c.elev;
  const body=(v)=>{const R=quatMat(sim.q),d=[v[0]/1000-sim.cg[0],v[1]/1000-sim.cg[1],v[2]/1000-sim.cg[2]];return[0,1,2].map(r=>p[r]+R[r][0]*d[0]+R[r][1]*d[1]+R[r][2]*d[2]);};
  if(c.mode==='chase'){yaw=headingYaw+Math.PI+c.yaw+2.4;}else if(c.mode==='side'){yaw=-Math.PI/2;elev=.05;}else if(c.mode==='top'){yaw=-Math.PI/2;elev=1.45;}
  else if(c.mode==='detail_upper'){target=body([0,0,85]);dist=Math.min(dist,.42);}else if(c.mode==='detail_lower'){target=body([0,0,-85]);dist=Math.min(dist,.42);}
  else if(c.mode==='gear'){target=body([0,0,-200]);dist=Math.min(dist,.7);}
  const eye=[target[0]+dist*Math.cos(elev)*Math.cos(yaw),target[1]+dist*Math.cos(elev)*Math.sin(yaw),Math.max(.03,target[2]+dist*Math.sin(elev))];return{eye,target};}
 /** state: {sim, servoDeg[6], rotorDeg[2], particles, slice, options} */
 draw(state){const gl=this.gl,sim=state.sim,o=state.options||{};const ratio=Math.min(2,root.devicePixelRatio||1),w=Math.round(this.canvas.clientWidth*ratio),h=Math.round(this.canvas.clientHeight*ratio);if(this.canvas.width!==w||this.canvas.height!==h){this.canvas.width=w;this.canvas.height=h;}
  gl.viewport(0,0,w,h);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);const{eye,target}=this.camera(sim,state.headingYaw||0),proj=perspective(.85,w/Math.max(1,h),.01,60),view=lookAt(eye,target,[0,0,1]),vp=mul(proj,view);this.vp=vp;this.eye=eye;
  // Ground with soft shadow below the vehicle.
  gl.useProgram(this.ground.p);gl.uniformMatrix4fv(this.ground.loc.vp,false,vp);gl.uniform3fv(this.ground.loc.eye,eye);gl.uniform3fv(this.ground.loc.shadow,[sim.p[0],sim.p[1],Math.max(0,1-sim.p[2]/2.5)]);
  gl.bindBuffer(gl.ARRAY_BUFFER,this.gbo);gl.enableVertexAttribArray(this.ground.loc.pos);gl.vertexAttribPointer(this.ground.loc.pos,2,gl.FLOAT,false,0,0);gl.drawArrays(gl.TRIANGLES,0,6);gl.disableVertexAttribArray(this.ground.loc.pos);
  // CAD parts
  const kf=this.kin.frames(state.servoDeg,state.rotorDeg,this._poses);this._poses=kf.poses;this.pitches=kf.pitches;const body=bodyMatrix(sim.p,sim.q,sim.cg),mats=this.keys.map(k=>{const f=kf.frames[k]||kf.frames.fixed;return mul(body,this.kin.toMat4(f,new Float32Array(16)));});
  gl.useProgram(this.solid.p);const L=this.solid.loc;gl.uniformMatrix4fv(L.vp,false,vp);gl.uniform3fv(L.eye,eye);gl.uniform1f(L.alpha,1);
  gl.bindBuffer(gl.ARRAY_BUFFER,this.vbo);gl.enableVertexAttribArray(L.pos);gl.vertexAttribPointer(L.pos,3,gl.SHORT,false,0,0);gl.bindBuffer(gl.ARRAY_BUFFER,this.nbo);gl.enableVertexAttribArray(L.nrm);gl.vertexAttribPointer(L.nrm,3,gl.BYTE,true,0,0);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,this.ibo);
  const pxScale=h/(2*Math.tan(.425));let drawn=0;
  for(const part of this.parts){if(this.hidden.has(part.g))continue;const m=mul(mats[part.k],part.M,this.tmp),c=[m[0]*part.s[0]+m[4]*part.s[1]+m[8]*part.s[2]+m[12],m[1]*part.s[0]+m[5]*part.s[1]+m[9]*part.s[2]+m[13],m[2]*part.s[0]+m[6]*part.s[1]+m[10]*part.s[2]+m[14]];
   const dist=Math.hypot(c[0]-eye[0],c[1]-eye[1],c[2]-eye[2]);if(part.s[3]*.001*pxScale/dist<.6)continue;
   gl.uniformMatrix4fv(L.model,false,m);gl.uniform3fv(L.color,part.c);gl.drawElements(gl.TRIANGLES,part.ic,gl.UNSIGNED_INT,part.io*4);drawn++;}
  gl.disableVertexAttribArray(L.nrm);gl.disableVertexAttribArray(L.pos);this.drawn=drawn;
  // Translucent rotor discs when the true rotor speed would alias at the display rate.
  if(o.rotorDisc){this.rotorDiscs(sim,body,vp,state.discAlpha||[0,0]);}
  if(state.slice&&o.slice)this.drawSlice(state.slice,sim,vp,state.sliceMax||25);
  if(state.particles&&o.particles)this.drawParticles(state.particles,vp,state.speedMax||25);
  return drawn;}
 rotorDiscs(sim,body,vp,alpha){const gl=this.gl,F=this.flat,n=64,pts=[],col=[];for(let l=0;l<2;l++){if(alpha[l]<=.01)continue;const z=l?-30:30,c=l?[.85,.48,.25]:[.2,.65,.78];for(let i=0;i<n;i++){for(const [a,r] of [[i,48],[i,187.5],[i+1,187.5],[i,48],[i+1,187.5],[i+1,48]]){const t=2*Math.PI*a/n;pts.push(r*Math.cos(t),r*Math.sin(t),z);col.push(...c,alpha[l]*(r>100?.5:.35));}}}
  if(!pts.length)return;gl.useProgram(F.p);gl.uniformMatrix4fv(F.loc.vp,false,vp);gl.uniformMatrix4fv(F.loc.model,false,body);this.flatDraw(pts,col,gl.TRIANGLES,true);}
 flatDraw(pts,col,mode,blend,additive){const gl=this.gl,F=this.flat;gl.bindBuffer(gl.ARRAY_BUFFER,this.pbo);gl.bufferData(gl.ARRAY_BUFFER,pts instanceof Float32Array?pts:new Float32Array(pts),gl.DYNAMIC_DRAW);gl.enableVertexAttribArray(F.loc.pos);gl.vertexAttribPointer(F.loc.pos,3,gl.FLOAT,false,0,0);
  gl.bindBuffer(gl.ARRAY_BUFFER,this.cbo);gl.bufferData(gl.ARRAY_BUFFER,col instanceof Float32Array?col:new Float32Array(col),gl.DYNAMIC_DRAW);gl.enableVertexAttribArray(F.loc.col);gl.vertexAttribPointer(F.loc.col,4,gl.FLOAT,false,0,0);
  if(blend){gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,additive?gl.ONE:gl.ONE_MINUS_SRC_ALPHA);gl.depthMask(false);}gl.drawArrays(mode,0,(pts.length/3)|0);if(blend){gl.disable(gl.BLEND);gl.depthMask(true);}gl.disableVertexAttribArray(F.loc.pos);gl.disableVertexAttribArray(F.loc.col);}
 drawParticles(field,vp,vmax){const gl=this.gl,F=this.flat,n=field.n,pts=new Float32Array(6*n),col=new Float32Array(8*n);
  for(let i=0;i<n;i++){let x=field.p[3*i],y=field.p[3*i+1],z=field.p[3*i+2],px=field.prev[3*i],py=field.prev[3*i+1],pz=field.prev[3*i+2];const dx=x-px,dy=y-py,dz=z-pz,L=Math.hypot(dx,dy,dz),k=L>.03?.03/L:1;px=x-dx*k*1.0;py=y-dy*k;pz=z-dz*k;
   pts.set([px,py,pz,x,y,z],6*i);const c=turbo(field.speed[i]/vmax),fade=Math.min(1,field.age[i]*3,(field.life[i]-field.age[i])*3);col.set([c[0],c[1],c[2],0,c[0],c[1],c[2],.85*fade],8*i);}
  gl.useProgram(F.p);gl.uniformMatrix4fv(F.loc.vp,false,vp);gl.uniformMatrix4fv(F.loc.model,false,new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]));this.flatDraw(pts,col,gl.LINES,true,true);}
 drawSlice(slice,sim,vp,vmax){const gl=this.gl,T=this.texp,{nx,nz}=slice,img=new Uint8Array(nx*nz*4);for(let i=0;i<nx*nz;i++){const v=slice.data[i]/vmax,c=turbo(v);img.set([c[0]*255,c[1]*255,c[2]*255,Math.min(210,Math.max(0,v*320-20))],4*i);}
  gl.bindTexture(gl.TEXTURE_2D,this.tex);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,nx,nz,0,gl.RGBA,gl.UNSIGNED_BYTE,img);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
  const x0=slice.x0*1000,x1=slice.x1*1000,z0=slice.z0*1000,z1=slice.z1*1000,y=-1;const q=new Float32Array([x0,y,z0,0,0,x1,y,z0,1,0,x1,y,z1,1,1,x0,y,z0,0,0,x1,y,z1,1,1,x0,y,z1,0,1]);
  gl.useProgram(T.p);gl.uniformMatrix4fv(T.loc.vp,false,vp);gl.uniformMatrix4fv(T.loc.model,false,bodyMatrix(sim.p,sim.q,sim.cg));gl.uniform1f(T.loc.alpha,.55);gl.uniform1i(T.loc.tex,0);
  gl.bindBuffer(gl.ARRAY_BUFFER,this.qbo);gl.bufferData(gl.ARRAY_BUFFER,q,gl.DYNAMIC_DRAW);gl.enableVertexAttribArray(T.loc.pos);gl.vertexAttribPointer(T.loc.pos,3,gl.FLOAT,false,20,0);gl.enableVertexAttribArray(T.loc.uv);gl.vertexAttribPointer(T.loc.uv,2,gl.FLOAT,false,20,12);
  gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.depthMask(false);gl.drawArrays(gl.TRIANGLES,0,6);gl.disable(gl.BLEND);gl.depthMask(true);gl.disableVertexAttribArray(T.loc.pos);gl.disableVertexAttribArray(T.loc.uv);}
 project(world){const m=this.vp,x=world[0],y=world[1],z=world[2],cw=m[3]*x+m[7]*y+m[11]*z+m[15];if(cw<=0)return null;return[(m[0]*x+m[4]*y+m[8]*z+m[12])/cw,(m[1]*x+m[5]*y+m[9]*z+m[13])/cw];}
}
const api={View,bodyMatrix,turbo};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.H01Ansicht3D=api;
})(globalThis);
