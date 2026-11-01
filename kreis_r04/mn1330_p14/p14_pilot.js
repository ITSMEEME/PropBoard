/* Ideal model pilot, shared by browser and deterministic flight checks.
 * Changes only motor/pitch commands. Forces, power limits, CAD inertia and
 * the180s boundary remain those of P14Physics.Flight. No verified firmware.
 */
(function(root){
  'use strict';
  const P=typeof module!=='undefined'&&module.exports?require('./p14_physik.js'):root.P14Physics;
  const clamp=P.clamp,D=P.D,neutral=()=>({forward:0,right:0,yaw:0,climb:0});
  const wrap=a=>Math.atan2(Math.sin(a),Math.cos(a));
  function euler(q){const[w,x,y,z]=q;return[Math.atan2(2*(w*x+y*z),1-2*(x*x+y*y)),Math.asin(clamp(2*(w*y-z*x),-1,1)),Math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))];}
  const mv=(a,v)=>a.map(r=>P.dot(r,v));
  class Pilot{
    constructor(flight){this.flight=flight;this.mode='POSITION';this.phase='OFF';this.hover=null;this.targetHeight=0;this.reference=flight.position.slice();this.lastInput=neutral();this.airborne=false;this.reason='';}
    prepare(){
      const f=this.flight,h=P.hoverStudy(f.config,f.anchors,f.options,f.commands);
      if(!h.found)throw Error(h.reason);
      const ceiling=f.commands.motorMode==='free_assumption'?2800:2400;
      if(h.rpm>ceiling)throw Error('Der Schwebebedarf liegt über '+ceiling+'/min. Nutzlast oder Modellvariante ändern.');
      this.hover=h;
      // Measure the command-to-moment map at the hover reference. Probe flights
      // use enough assumed power solely to measure derivatives; actual flight
      // retains the motor case selected by the user, including every limit.
      const probe=extra=>{const p=new P.Flight(f.config,f.anchors,f.options);p.position[2]+=5;p.shaftOmega=[h.rpm,h.rpm].map(r=>r*2*Math.PI/60);p.commands={...f.commands,rpm:h.rpm,collectiveUpper:0,collectiveLower:h.collectiveLower,cyclicX:0,cyclicY:0,motorMode:'free_assumption',torqueCap:200,inputPowerCap:60000,...extra};p.step(1/120);return p.lastMoment;};
      const b=probe({}),x=probe({cyclicX:.1}),y=probe({cyclicY:.1}),z=probe({collectiveLower:h.collectiveLower+.05});
      this.bias=b;this.map=[[10*(x[0]-b[0]),10*(y[0]-b[0])],[10*(x[1]-b[1]),10*(y[1]-b[1])]];this.yawGain=(z[2]-b[2])/.05;
      const a=this.map;this.det=a[0][0]*a[1][1]-a[0][1]*a[1][0];
      if(Math.abs(this.det)<1e-6||Math.abs(this.yawGain)<1e-6)throw Error('Für diese Variante fehlt eine nutzbare Steuerwirkung.');
      return h;
    }
    start(){if(!this.hover)this.prepare();this.phase='TAKEOFF';this.targetHeight=Math.max(1.2,this.flight.height);this.reference=this.flight.position.slice();this.reason='';this.airborne=this.flight.height>.05;}
    land(){if(!['OFF','STOPPING','CRASH'].includes(this.phase)){if(!this.airborne&&this.flight.contact){this.stop();return;}this.phase='LANDING';this.reference=this.flight.position.slice();}}
    stop(){this.phase='STOPPING';this.flight.commands.rpm=0;this.flight.commands.cyclicX=this.flight.commands.cyclicY=0;}
    setMode(mode){if(!['POSITION','ANGLE'].includes(mode))throw Error('Unbekannter Steuerungsmodus');this.mode=mode;this.reference=this.flight.position.slice();}
    update(input={},dt=1/120){
      const f=this.flight,cmd=f.commands;
      const s={};for(const k of Object.keys(neutral()))s[k]=clamp(Number.isFinite(input[k])?input[k]:0,-1,1);this.lastInput=s;
      if(['OFF','STOPPING','CRASH'].includes(this.phase)){cmd.rpm=0;cmd.cyclicX=cmd.cyclicY=0;return;}
      const [roll,pitch,yaw]=euler(f.quaternion);
      if(Math.max(Math.abs(roll),Math.abs(pitch))>65*D){this.phase='CRASH';this.reason='Versuch beendet: Neigung über65°. Zurücksetzen.';cmd.rpm=0;return;}
      const h=this.hover,bodyForward=s.forward*2,bodyLeft=-s.right*2,cs=Math.cos(yaw),sn=Math.sin(yaw);
      let rollTarget=s.right*10*D,pitchTarget=s.forward*10*D;
      if(this.mode==='POSITION'||this.phase==='LANDING'){
        const moving=Math.hypot(s.forward,s.right)>.01&&this.phase!=='LANDING';
        if(moving)this.reference=f.position.slice();
        const vx=moving?cs*bodyForward-sn*bodyLeft:clamp((this.reference[0]-f.position[0])*.3,-2,2);
        const vy=moving?sn*bodyForward+cs*bodyLeft:clamp((this.reference[1]-f.position[1])*.3,-2,2);
        const ax=clamp((vx-f.velocity[0])*.7,-1.7,1.7),ay=clamp((vy-f.velocity[1])*.7,-1.7,1.7);
        pitchTarget=clamp(Math.atan2(cs*ax+sn*ay,P.G),-10*D,10*D);rollTarget=clamp(-Math.atan2(-sn*ax+cs*ay,P.G),-10*D,10*D);
      }
      if(this.phase==='TAKEOFF'&&f.height>1.05)this.phase='FLIGHT';
      if(this.phase==='FLIGHT')this.targetHeight=clamp(this.targetHeight+s.climb*.8*dt,.15,80);
      let vz=clamp((Math.min(this.targetHeight,f.height+.6)-f.height)*.85,-.7,.7);
      if(this.phase==='LANDING')vz=f.height>.15?-.35:-.12;
      const az=clamp((vz-f.velocity[2])*1.6,-2.5,2.5),up=P.qrotate(f.quaternion,[0,0,1])[2];
      const ceiling=cmd.motorMode==='free_assumption'?2800:2400;
      cmd.rpm=clamp(h.rpm*Math.sqrt((P.G+az)/(P.G*Math.max(.5,up))),0,ceiling);
      const accel=[6*wrap(rollTarget-roll)-4.5*f.omega[0],6*wrap(pitchTarget-pitch)-4.5*f.omega[1],2.5*(s.yaw*40*D-f.omega[2])];
      const J=f.properties.inertia,I=f.properties.rotorInertia,N=f.config.geometry.lift_units,H=N*(I[1]*f.shaftOmega[1]-I[0]*f.shaftOmega[0]);
      const gyro=P.cross(f.omega,P.add(mv(J,f.omega),[0,0,H])),moment=P.add(mv(J,accel),gyro);
      const ratio=Math.max(.12,((f.shaftOmega[0]+f.shaftOmega[1])*.5/(h.rpm*2*Math.PI/60))**2),a=this.map;
      const mx=moment[0]/ratio-this.bias[0],my=moment[1]/ratio-this.bias[1];
      let x=(a[1][1]*mx-a[0][1]*my)/this.det,y=(-a[1][0]*mx+a[0][0]*my)/this.det;
      const norm=Math.hypot(x,y);if(norm>.5){x*=.5/norm;y*=.5/norm;}
      const ready=!f.contact&&Math.min(...f.shaftOmega)>h.rpm*2*Math.PI/60*.6;
      cmd.cyclicX=ready?x:0;cmd.cyclicY=ready?y:0;cmd.collectiveUpper=0;
      cmd.collectiveLower=clamp(h.collectiveLower+(ready?(moment[2]/ratio-this.bias[2])/this.yawGain:0),-3.5,3.5);
    }
    afterStep(previous){
      const f=this.flight;if(f.height>.05)this.airborne=true;
      if(f.contact&&this.airborne&&previous.vz < -2){this.phase='CRASH';this.reason='Versuch beendet: harter Bodenkontakt. Zurücksetzen.';f.commands.rpm=0;}
      else if(f.contact&&this.airborne&&this.phase==='LANDING'){this.phase='STOPPING';f.commands.rpm=0;}
      if(this.phase==='STOPPING'&&Math.max(...f.shaftOmega)<1)this.phase='OFF';
    }
  }
  const api={Pilot,euler,neutral};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.P14Pilot=api;
})(globalThis);
