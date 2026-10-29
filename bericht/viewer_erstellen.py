from pathlib import Path
HERE=Path(__file__).resolve().parent
data=(HERE/'Modelldaten.json').read_text()
template=r'''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PropBoard – native CAD-Geometrien im Vergleich</title>
<style>body{font:16px system-ui;margin:24px;background:#f1f4f8;color:#152336}h1{font-size:25px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:20px}.card{background:white;border-radius:12px;padding:18px}canvas{width:100%;height:440px;touch-action:none;border:1px solid #ddd}button{padding:8px;margin:4px}a{color:#006978}.note{max-width:1100px;line-height:1.6}.small{font-size:12px;overflow-wrap:anywhere}label{margin:8px}</style>
<h1>PropBoard: tatsächliche 3D-Modellgeometrien</h1>
<p class="note">Aus den beiden nativen FreeCAD-Dateien trianguliert. Ziehen zum Drehen, Mausrad zum Zoomen. Die Darstellung ist eine geometrische Momentaufnahme: keine Bewegungssimulation, kein Strömungsfeld, kein Tragfähigkeitsnachweis. Führung und Schlitten sind Bauraumplatzhalter.</p>
<div id="models" class="grid"></div><p class="note">Maße, Prüfungen und Grenzen stehen im <a href="Vergleichsbericht.html">Vergleichsbericht</a>. Die Geometriedaten sind vollständig eingebettet; diese Ansicht benötigt keine Internetverbindung. Erforderlich ist ein Browser mit WebGL.</p>
<script>const models=__DATA__;
for (const model of models){
 const card=document.createElement('section');card.className='card';
 card.innerHTML=`<h2>${model.title}</h2><canvas aria-label="Drehbare CAD-Geometrie"></canvas><div><button data-view="reset">Schrägansicht</button><button data-view="top">Draufsicht</button><button data-view="side">Seitenansicht</button></div><label><input type="checkbox" data-kind="wing" checked> Flügel</label><label><input type="checkbox" data-kind="structure" checked> Strukturplatzhalter</label><p><a href="../${model.file}">Native FreeCAD-Datei</a></p><p class="small">SHA-256: ${model.sha256}</p>`;
 document.querySelector('#models').appendChild(card);const canvas=card.querySelector('canvas');const gl=canvas.getContext('webgl');
 if(!gl){canvas.replaceWith(document.createTextNode('WebGL nicht verfügbar. Bitte native FCStd-Datei öffnen.'));continue}
 const vertex=`attribute vec3 position;attribute vec3 color;attribute vec3 normal;uniform mat3 rotation;uniform vec2 scale;varying vec3 tint;void main(){vec3 p=rotation*(position-vec3(0.,0.,.07));vec3 n=rotation*normal;float light=.3+.7*abs(dot(normalize(n),normalize(vec3(.3,.5,1.))));tint=color*light;gl_Position=vec4(p.x*scale.x,p.y*scale.y,-p.z*.15,1.);}`;
 const fragment=`precision mediump float;varying vec3 tint;void main(){gl_FragColor=vec4(tint,1.);}`;
 function shader(type,src){const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s}
 const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vertex));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fragment));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));gl.useProgram(program);
 const count=model.parts.reduce((s,p)=>s+p.faces.length*3,0);const array=new Float32Array(count*9);const ranges=[];let offset=0;
 for(const part of model.parts){const start=offset/9;const color=part.color.slice(1).match(/../g).map(x=>parseInt(x,16)/255);
  for(const face of part.faces){const a=part.vertices[face[0]],b=part.vertices[face[1]],c=part.vertices[face[2]];let u=b.map((v,k)=>v-a[k]),v=c.map((v,k)=>v-a[k]);let n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];const len=Math.hypot(...n)||1;n=n.map(x=>x/len);
   for(const index of face){const point=part.vertices[index];for(let k=0;k<3;k++)array[offset++]=point[k]/1000;for(const x of color)array[offset++]=x;for(const x of n)array[offset++]=x}}
  ranges.push({start,count:offset/9-start,kind:part.kind})}
 const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,array,gl.STATIC_DRAW);
 for(const [name,index]of[['position',0],['color',1],['normal',2]]){const a=gl.getAttribLocation(program,name);gl.enableVertexAttribArray(a);gl.vertexAttribPointer(a,3,gl.FLOAT,false,36,index*12)}
 gl.enable(gl.DEPTH_TEST);gl.clearColor(.98,.985,1,1);const rot=gl.getUniformLocation(program,'rotation'),scale=gl.getUniformLocation(program,'scale');let yaw=-.7,elev=.5,zoom=.8;const visible={wing:true,structure:true};
 function draw(){const ratio=canvas.clientWidth/canvas.clientHeight,dpr=Math.min(window.devicePixelRatio||1,2);canvas.width=Math.round(canvas.clientWidth*dpr);canvas.height=Math.round(canvas.clientHeight*dpr);gl.viewport(0,0,canvas.width,canvas.height);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);let c=Math.cos(yaw),s=Math.sin(yaw),se=Math.sin(elev),ce=Math.cos(elev);gl.uniformMatrix3fv(rot,false,new Float32Array([c,-se*s,ce*s,-s,-se*c,ce*c,0,ce,se]));gl.uniform2f(scale,zoom/ratio,zoom);for(const r of ranges)if(visible[r.kind])gl.drawArrays(gl.TRIANGLES,r.start,r.count)}
 let last=null;canvas.onpointerdown=e=>{last=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId)};canvas.onpointerup=()=>last=null;canvas.onpointercancel=()=>last=null;canvas.onpointermove=e=>{if(!last)return;yaw+=(e.clientX-last[0])*.008;elev=Math.max(-1.57,Math.min(1.57,elev+(e.clientY-last[1])*.008));last=[e.clientX,e.clientY];requestAnimationFrame(draw)};canvas.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.2,Math.min(4,zoom*Math.exp(-e.deltaY*.001)));draw()},{passive:false});
 card.querySelectorAll('button').forEach(b=>b.onclick=()=>{yaw=b.dataset.view==='reset'?-.7:0;elev=b.dataset.view==='top'?Math.PI/2:b.dataset.view==='side'?0:.5;zoom=.8;draw()});card.querySelectorAll('input').forEach(input=>input.onchange=()=>{visible[input.dataset.kind]=input.checked;draw()});new ResizeObserver(draw).observe(canvas);draw();
}
</script></html>'''
(HERE/'Modelle_3D.html').write_text(template.replace('__DATA__',data))
print('Offline-WebGL-Ansicht erstellt')
