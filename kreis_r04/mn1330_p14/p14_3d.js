/* Draw actual variant CAD meshes with Float32 positions (full-size millimetres).
 * Transforms mirror animieren.py; shafts, blades, swashplates and rods stay rigid.
 */
(function(root){
  'use strict';
  const P=root.P14Physics,D=P.D;
  const I=()=>[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
  function mul(a,b){const o=new Array(16).fill(0);for(let i=0;i<4;i++)for(let j=0;j<4;j++)for(let k=0;k<4;k++)o[i*4+j]+=a[i*4+k]*b[k*4+j];return o;}
  const chain=(...ms)=>ms.reduce(mul,I());
  const T=(x=0,y=0,z=0)=>[1,0,0,x,0,1,0,y,0,0,1,z,0,0,0,1];
  function R(axis,angle){const [x,y,z]=P.scale(axis,1/P.length(axis)),a=angle*D,c=Math.cos(a),s=Math.sin(a),v=1-c;return[c+x*x*v,x*y*v-z*s,x*z*v+y*s,0,y*x*v+z*s,c+y*y*v,y*z*v-x*s,0,z*x*v-y*s,z*y*v+x*s,c+z*z*v,0,0,0,0,1];}
  const Rz=a=>R([0,0,1],a);
  function quat(q){const [w,x,y,z]=q;return[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),0,2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),0,2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y),0,0,0,0,1];}
  function point(m,p){return[0,1,2].map(i=>m[i*4]*p[0]+m[i*4+1]*p[1]+m[i*4+2]*p[2]+m[i*4+3]);}
  const transpose=a=>new Float32Array([0,4,8,12,1,5,9,13,2,6,10,14,3,7,11,15].map(i=>a[i]));
  function rod(old,current){
    let u=P.sub(old[1],old[0]),v=P.sub(current[1],current[0]);u=P.scale(u,1/P.length(u));v=P.scale(v,1/P.length(v));
    const cs=P.clamp(P.dot(u,v),-1,1);let axis=P.cross(u,v),r=I();
    if(P.length(axis)>1e-10)r=R(axis,Math.acos(cs)/D);else if(cs<0){axis=P.cross(u,[0,0,1]);if(P.length(axis)<1e-10)axis=P.cross(u,[0,1,0]);r=R(axis,180);}
    const shift=P.sub(current[0],point(r,old[0]));return mul(T(...shift),r);
  }
  function localDelta(row,c,pose,angle,neutral){
    const g=c.geometry,f=row.frame,a=row.a,sz=g.swash_z_mm,level=g.rotor_spacing_mm/2;
    if(f==='fixed'||f==='shared')return I();if(f==='rotor')return Rz(angle);
    if(f==='pitch')return chain(Rz(angle),T(0,0,level),R([Math.cos(a*D),Math.sin(a*D),0],pose.pitches_deg[row.blade_index]-g.neutral_pitch_deg),T(0,0,-level));
    if(f==='swash_slider')return T(0,0,pose.swash_z_mm-sz);
    if(f==='swash_fixed'||f==='swash_rotor')return chain(T(0,0,pose.swash_z_mm),R([1,0,0],pose.tilt_deg[0]),R([0,1,0],pose.tilt_deg[1]),Rz(f==='swash_rotor'?angle:pose.stationary_phase_deg),T(0,0,-sz));
    if(f==='servo_horn'||f==='servo_shaft')return chain(Rz(a),T(g.servo_r_mm,0,g.servo_z_mm),R([0,1,0],pose.servo_deg[row.servo_index]-g.servo_neutral_deg),T(-g.servo_r_mm,0,-g.servo_z_mm),Rz(-a));
    if(f==='pitch_link'){const conv=Rz(angle),old=neutral.pitch_points_mm[row.blade_index].map(p=>point(conv,p));return mul(rod(old,pose.pitch_points_mm[row.blade_index]),conv);}
    if(f==='servo_link')return rod(neutral.servo_points_mm[row.servo_index],pose.servo_points_mm[row.servo_index]);
    throw Error('Unbekannte Bewegungsgruppe '+f);
  }
  function colour(id,type){
    if(id==='CFK01')return[.12,.17,.21];if(id==='MN1330')return[.66,.13,.16];if(id==='SERVO')return[.94,.43,.13];
    if(type.material==='PTFE')return[.68,.87,.91];if(type.kind==='Normlager')return[.43,.50,.57];
    if(id.startsWith('ROD_')||id==='A27'||id==='A18')return[.13,.50,.67];return[.71,.76,.81];
  }
  class Viewer{
    constructor(canvas){
      this.canvas=canvas;const gl=canvas.getContext('webgl',{antialias:true,preserveDrawingBuffer:true});if(!gl)throw Error('WebGL ist nicht verfügbar');this.gl=gl;
      const make=(kind,src)=>{const s=gl.createShader(kind);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
      const program=gl.createProgram();gl.attachShader(program,make(gl.VERTEX_SHADER,'attribute vec3 p; attribute vec3 n; uniform mat4 model; uniform mat4 vp; varying vec3 normal; void main(){gl_Position=vp*model*vec4(p,1.);normal=mat3(model)*n;}'));
      gl.attachShader(program,make(gl.FRAGMENT_SHADER,'precision mediump float; varying vec3 normal; uniform vec3 color; void main(){float light=.4+.6*abs(dot(normalize(normal),normalize(vec3(.4,-.5,.8))));gl_FragColor=vec4(color*light,1.);}'));
      gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));gl.useProgram(program);this.program=program;
      this.loc={p:gl.getAttribLocation(program,'p'),n:gl.getAttribLocation(program,'n'),model:gl.getUniformLocation(program,'model'),vp:gl.getUniformLocation(program,'vp'),color:gl.getUniformLocation(program,'color')};
      gl.enable(gl.DEPTH_TEST);this.buffers={};this.az=-65;this.el=26;this.distance=2700;this.target=[0,0,370];this.showLower=true;this.showBlades=true;this.showDetails=false;
      let drag=null;canvas.addEventListener('pointerdown',e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);});canvas.addEventListener('pointermove',e=>{if(!drag)return;this.az-=(e.clientX-drag[0])*.35;this.el=P.clamp(this.el+(e.clientY-drag[1])*.3,-60,85);drag=[e.clientX,e.clientY];});canvas.addEventListener('pointerup',()=>drag=null);
      canvas.addEventListener('wheel',e=>{e.preventDefault();this.distance=P.clamp(this.distance*Math.exp(e.deltaY*.001),300,13000);},{passive:false});
      const grid=[];for(let i=-4000;i<=4000;i+=250){grid.push(i,-4000,0,0,0,1,i,4000,0,0,0,1,-4000,i,0,0,0,1,4000,i,0,0,0,1);}this.grid=this.buffer(grid);
    }
    buffer(array){const gl=this.gl,b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(array),gl.STATIC_DRAW);return{buffer:b,count:array.length/6};}
    setVariant(v){
      for(const b of Object.values(this.buffers))this.gl.deleteBuffer(b.buffer);this.buffers={};this.variant=v;
      for(const [id,m] of Object.entries(v.meshes)){const a=[];for(const face of m.triangles){const p=face.map(i=>m.vertices_mm[i]),normal=P.cross(P.sub(p[1],p[0]),P.sub(p[2],p[0])),nn=P.length(normal);if(nn<1e-15)continue;const n=P.scale(normal,1/nn);for(const x of p)a.push(...x,...n);}this.buffers[id]=this.buffer(a);}
    }
    drawBuffer(buffer,m,color,lines=false){const gl=this.gl,l=this.loc;gl.bindBuffer(gl.ARRAY_BUFFER,buffer.buffer);gl.enableVertexAttribArray(l.p);gl.enableVertexAttribArray(l.n);gl.vertexAttribPointer(l.p,3,gl.FLOAT,false,24,0);gl.vertexAttribPointer(l.n,3,gl.FLOAT,false,24,12);gl.uniformMatrix4fv(l.model,false,transpose(m));gl.uniform3fv(l.color,new Float32Array(color));gl.drawArrays(lines?gl.LINES:gl.TRIANGLES,0,buffer.count);}
    draw(c,commands,angles=[0,0],flight=null){
      if(!this.variant)return;const gl=this.gl,canvas=this.canvas,dpr=Math.min(devicePixelRatio||1,1.7),w=Math.max(1,Math.floor(canvas.clientWidth*dpr)),h=Math.max(1,Math.floor(canvas.clientHeight*dpr));if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}gl.viewport(0,0,w,h);gl.clearColor(.91,.94,.96,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
      const target=this.target.slice();if(flight)target[2]+=flight.height*1000;
      const eye=P.add(target,[this.distance*Math.cos(this.el*D)*Math.cos(this.az*D),this.distance*Math.cos(this.el*D)*Math.sin(this.az*D),this.distance*Math.sin(this.el*D)]);
      const f=P.scale(P.sub(target,eye),1/P.length(P.sub(target,eye))),side=P.scale(P.cross(f,[0,0,1]),1/P.length(P.cross(f,[0,0,1]))),up=P.cross(side,f);
      const view=[...side,-P.dot(side,eye),...up,-P.dot(up,eye),...P.scale(f,-1),P.dot(f,eye),0,0,0,1],a=1/Math.tan(40*D/2),near=10,far=30000;
      const projection=[a/(w/h),0,0,0,0,a,0,0,0,0,(far+near)/(near-far),2*far*near/(near-far),0,0,-1,0];gl.uniformMatrix4fv(this.loc.vp,false,transpose(mul(projection,view)));
      this.drawBuffer(this.grid,I(),[.64,.72,.77],true);
      const derived=P.derive(c),floor=c.geometry.rotor_spacing_mm/2+90;
      const world=flight?chain(T(...P.scale(flight.position,1000)),quat(flight.quaternion),T(...P.scale(flight.properties.cg,-1000))):T(0,0,floor);
      const poses=[P.podPose(c,commands,1,angles[0]),P.podPose(c,commands,-1,angles[1])];let count=0;
      for(const centre of derived.unit_centres_mm){
        const unit=chain(world,T(...centre));
        for(const row of this.variant.scene){
          if(!this.showLower&&row.sign<0)continue;if(!this.showBlades&&row.part==='CFK01')continue;if(!this.showDetails&&/^(F[0-9]|N[0-9]|TIE)/.test(row.part))continue;
          const k=row.sign>0?0:1,delta=localDelta(row,c,poses[k],angles[k],this.variant.derived.neutral),pod=row.sign<0?R([0,1,0],180):I();
          const model=chain(unit,pod,delta,row.neutral_transform);this.drawBuffer(this.buffers[row.part],model,colour(row.part,this.variant.types[row.part]));count++;
        }
      }
      this.lastDrawCount=count;this.lastPoses=poses;
    }
  }
  root.P14View={Viewer,I,mul,chain,T,R,point,localDelta};
})(globalThis);
