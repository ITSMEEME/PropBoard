/* Focus-safe keyboard, pointer and standard Gamepad API pilot input. */
(function(root){
  'use strict';
  const keys={KeyW:['forward',1],KeyS:['forward',-1],KeyD:['right',1],KeyA:['right',-1],KeyQ:['yaw',1],KeyE:['yaw',-1],KeyR:['climb',1],KeyF:['climb',-1],ArrowUp:['forward',1],ArrowDown:['forward',-1],ArrowRight:['right',1],ArrowLeft:['right',-1]};
  const actions={KeyT:'start',KeyL:'land',KeyX:'stop',Space:'pause',Backspace:'reset',KeyM:'mode',KeyC:'camera',Escape:'pause'};
  const neutral=()=>({forward:0,right:0,yaw:0,climb:0}),clamp=x=>Math.max(-1,Math.min(1,x));
  const formTarget=e=>e?.closest?.('input,select,textarea,button,[contenteditable="true"]');
  const dead=x=>Math.abs(x)<=.12?0:Math.sign(x)*(Math.abs(x)-.12)/.88;
  class Input{
    constructor({window:win=window,document:doc=document,onAction=()=>{},onBlur=()=>{}}={}){
      this.win=win;this.doc=doc;this.onAction=onAction;this.keys=new Set();this.pointers=new Map();this.active=true;this.padButtons=[];this.padRelease=false;this.padLabel='Gamepad: nicht verbunden';this.listeners=[];
      const listen=(target,event,fn)=>{target.addEventListener(event,fn);this.listeners.push(()=>target.removeEventListener(event,fn));};
      listen(win,'keydown',e=>{if(!this.active||formTarget(e.target)||e.ctrlKey||e.metaKey||e.altKey)return;if(keys[e.code]){e.preventDefault();this.keys.add(e.code);}else if(actions[e.code]){e.preventDefault();if(!e.repeat)this.onAction(actions[e.code]);}});
      listen(win,'keyup',e=>{this.keys.delete(e.code);});
      const blur=()=>{this.clear();this.active=false;this.padRelease=true;onBlur();};
      listen(win,'blur',blur);listen(win,'focus',()=>{this.active=true;});
      listen(doc,'visibilitychange',()=>{if(doc.hidden)blur();else this.active=true;});
      listen(doc,'focusin',e=>{if(formTarget(e.target))this.clear();});
      for(const button of doc.querySelectorAll('[data-pilot]')){
        listen(button,'pointerdown',e=>{e.preventDefault();button.setPointerCapture(e.pointerId);this.pointers.set(e.pointerId,button.dataset.pilot);button.classList.add('held');});
        const release=e=>{this.pointers.delete(e.pointerId);button.classList.remove('held');};
        for(const event of ['pointerup','pointercancel','lostpointercapture'])listen(button,event,release);
      }
    }
    clear(){this.keys.clear();this.pointers.clear();for(const b of this.doc.querySelectorAll('[data-pilot]'))b.classList.remove('held');}
    sample(){
      const out=neutral();if(!this.active||this.doc.hidden)return out;
      for(const code of this.keys){const[k,v]=keys[code];out[k]+=v;}
      const mapping={forward:['forward',1],back:['forward',-1],right:['right',1],left:['right',-1],yawLeft:['yaw',1],yawRight:['yaw',-1],up:['climb',1],down:['climb',-1]};
      for(const key of this.pointers.values()){const[k,v]=mapping[key];out[k]+=v;}
      let pads=[],blocked=false;
      try{pads=Array.from(this.win.navigator?.getGamepads?.()||[]).filter(p=>p?.connected);}catch{blocked=true;}
      const pad=pads.find(p=>p.mapping==='standard');
      this.padLabel=blocked?'Gamepad: Browserzugriff gesperrt':pad?'Gamepad: Mode2 verbunden':pads.length?'Gamepad: Standardbelegung fehlt':'Gamepad: nicht verbunden';
      if(pad){const axes=pad.axes.map(x=>Number.isFinite(x)?clamp(x):0),buttons=pad.buttons.map(b=>b.pressed);
        if(this.padRelease){if(!buttons.some(Boolean))this.padRelease=false;}
        else{out.right+=dead(axes[2]||0);out.forward-=dead(axes[3]||0);out.yaw-=dead(axes[0]||0);out.climb-=dead(axes[1]||0);
          for(const[i,action]of [[0,'start'],[1,'land'],[3,'mode'],[9,'pause']])if(buttons[i]&&!this.padButtons[i])this.onAction(action);}
        this.padButtons=buttons;
      }else{this.padButtons=[];this.padRelease=true;}
      for(const k of Object.keys(out))out[k]=clamp(out[k]);const norm=Math.hypot(out.forward,out.right);if(norm>1){out.forward/=norm;out.right/=norm;}
      return out;
    }
    destroy(){this.clear();for(const off of this.listeners)off();this.listeners=[];}
  }
  const api={Input,keys,actions,neutral};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.P14Input=api;
})(globalThis);
