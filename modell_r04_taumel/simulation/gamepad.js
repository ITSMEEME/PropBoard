/* Gamepad normalization and per-device calibration. Also usable by Node tests. */
(function(root){
'use strict';
const channels=['yaw','throttle','roll','pitch'];
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const defaults=n=>({version:1,deadzone:.08,channels:Object.fromEntries(channels.map((c,i)=>[c,{axis:i,invert:i===1||i===3}])),center:Array(n).fill(0),min:Array(n).fill(-1),max:Array(n).fill(1)});
function valid(p,n){return p?.version===1&&Number.isFinite(p.deadzone)&&p.deadzone>=0&&p.deadzone<=.4&&
 ['center','min','max'].every(k=>Array.isArray(p[k])&&p[k].length===n&&p[k].every(Number.isFinite))&&
 channels.every(c=>{const q=p.channels?.[c];return q&&Number.isInteger(q.axis)&&q.axis>=0&&q.axis<n&&typeof q.invert==='boolean'&&p.center[q.axis]-p.min[q.axis]>=.15&&p.max[q.axis]-p.center[q.axis]>=.15;})&&
 new Set(channels.map(c=>p.channels[c].axis)).size===4;}
function normalize(raw,p,c){const q=p.channels[c];if(!q||!Number.isFinite(raw[q.axis]))return 0;
 const delta=raw[q.axis]-p.center[q.axis],range=delta>=0?p.max[q.axis]-p.center[q.axis]:p.center[q.axis]-p.min[q.axis];
 if(!(range>0))return 0;let v=clamp(delta/range,-1,1);if(Math.abs(v)<=p.deadzone)return 0;v=Math.sign(v)*(Math.abs(v)-p.deadzone)/(1-p.deadzone);return q.invert?-v:v;}
class Controller{
 constructor(storage){this.storage=storage;this.key=null;this.gp=null;this.profile=null;this.draft=null;this.active=false;this.stage='';this.storageError=false;this.saved=false;}
 identify(gp){return gp?JSON.stringify([gp.id,gp.mapping||'',gp.axes.length]):null;}
 sample(gp){this.gp=gp;const key=this.identify(gp);
  // Keep the draft bound to its original device, including during disconnection.
  if(!this.active&&key!==this.key){this.key=key;this.profile=gp?defaults(gp.axes.length):null;this.saved=false;this.storageError=false;
   if(gp)try{const stored=JSON.parse(this.storage?.getItem('H01.gamepad.v1:'+key)||'null');if(valid(stored,gp.axes.length)){this.profile=stored;this.saved=true;}}catch(e){this.storageError=true;}}
  if(this.active&&this.stage==='range'&&key===this.key)gp.axes.forEach((v,i)=>{if(Number.isFinite(v)){this.draft.min[i]=Math.min(this.draft.min[i],v);this.draft.max[i]=Math.max(this.draft.max[i],v);}});
  return Object.fromEntries(channels.map(c=>[c,!this.active&&gp&&this.profile?normalize(gp.axes,this.profile,c):0]));
 }
 begin(){if(!this.gp||this.gp.axes.length<4)return false;this.active=true;this.draft=JSON.parse(JSON.stringify(this.profile));this.stage='center';return true;}
 captureCenter(){if(!this.active||this.identify(this.gp)!==this.key||!this.gp.axes.every(Number.isFinite))return false;
  this.draft.center=[...this.gp.axes];this.draft.min=[...this.gp.axes];this.draft.max=[...this.gp.axes];this.stage='range';return true;}
 save(){if(!this.active||this.stage!=='range'||this.identify(this.gp)!==this.key||!valid(this.draft,this.gp.axes.length))return {ok:false,message:'Jeden zugeordneten Stick in beide Richtungen bewegen; vier unterschiedliche Achsen wählen.'};
  this.profile=JSON.parse(JSON.stringify(this.draft));this.active=false;this.draft=null;this.stage='';this.saved=true;
  try{if(!this.storage)throw Error('Kein Speicher');this.storage.setItem('H01.gamepad.v1:'+this.key,JSON.stringify(this.profile));this.storageError=false;return {ok:true,persisted:true};}
  catch(e){this.storageError=true;return {ok:true,persisted:false};}}
 cancel(){this.active=false;this.draft=null;this.stage='';}
 reset(){if(!this.gp||this.identify(this.gp)!==this.key)return false;this.profile=defaults(this.gp.axes.length);this.saved=false;this.cancel();try{this.storage?.removeItem('H01.gamepad.v1:'+this.key);}catch(e){this.storageError=true;}return true;}
}
const api={Controller,channels,defaults,valid,normalize};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.H01Gamepad=api;
})(typeof globalThis!=='undefined'?globalThis:this);
