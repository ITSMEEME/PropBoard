'use strict';
window.H01Betaflight=class{
 constructor(){this.ready=false;this.armed=false;this.actualArmed=false;this.version='';this.busy=false;this.abort=null;this.previousV=null;this.error='';}
 async connect(){const r=await fetch('/api/betaflight/status',{signal:AbortSignal.timeout(3000)});const data=await r.json();if(!r.ok||!data.realFirmware||data.mspVersion.join('.')!=='4.5.2')throw Error(data.error||'Keine echte Betaflight 4.5.2 SITL-Verbindung');this.version=data.firmware;this.ready=true;this.actualArmed=data.armed;this.armingDisabled=data.armingDisabled;this.lastStatus=performance.now();this.error='';return data;}
 async refresh(){if(!this.ready||this.refreshing)return;this.refreshing=true;this.lastStatus=performance.now();try{const r=await fetch('/api/betaflight/status',{signal:AbortSignal.timeout(1500)}),data=await r.json();if(!r.ok)throw Error(data.error||'MSP-Status nicht erreichbar');if(this.ready){this.actualArmed=data.armed;this.armingDisabled=data.armingDisabled;}}catch(e){this.disconnect();this.error=e.message;}finally{this.refreshing=false;}}
 disarm(){this.armed=false;}
 disconnect(){this.armed=false;this.actualArmed=false;this.ready=false;this.abort?.abort();this.previousV=null;}
 async step(sim,sticks,angle){if(!this.ready)throw Error('Betaflight ist nicht verbunden');this.abort=new AbortController();const timer=setTimeout(()=>this.abort.abort(),1000);
  try{const dt=sim.c.dt,acc=this.previousV?sim.v.map((v,i)=>(v-this.previousV[i])/dt):[0,0,0];this.previousV=[...sim.v];acc[2]+=9.80665;const specificForce=H01Flight.rotate(H01Flight.conj(sim.q),acc);
   const response=await fetch('/api/betaflight/frame',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({state:{dt,q:sim.q,w:sim.w,p:sim.p,v:sim.v,specificForce},sticks,armed:this.armed,angle}),signal:this.abort.signal});
   const out=await response.json();if(!response.ok)throw Error(out.error||'SITL-Kommunikation fehlgeschlagen');if(out.motorCount!==2||out.servoRad?.length!==6||out.duty?.length!==2||out.ageMs>150)throw Error('Ungueltige/veraltete Firmware-Ausgaenge');this.actualArmed=out.armed;this.armingDisabled=out.armingDisabled;return out;
  }catch(e){this.disconnect();this.error=e.message;throw e;}finally{clearTimeout(timer);this.abort=null;}
 }
};
