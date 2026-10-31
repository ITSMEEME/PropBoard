/* P10 Flugablauf für Simulator und Testserie: Bodenstart, Hochlauf, Schwebeflug, Landung, Auslauf.
 * Erzeugt aus Steuereingaben (Sticks −1…1) die Sollwerte für flugphysik.js. Gleicher Code in
 * Browser und Node. Kein Firmware-Modell (ArduPilot o. Ä.); reine Simulationslogik. */
(function(root){'use strict';
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x)),D=Math.PI/180;
const LIMITS={angleDeg:25,yawRateDeg:90,climbAngle:1.5,climbPosition:.8,speedPosition:1.0,spoolUpS:3.0,spoolDownS:2.0,takeoffHeight:1.0,landingRate:.4,idleThrustFraction:.25};
class Manager{
 constructor(sim,options={}){this.sim=sim;this.mode=options.mode||'POSITION';this.limits={...LIMITS,...(options.limits||{})};
  this.phase=sim.c.ground&&sim.c.startOnGround?'AUS':'FLUG';this.spool=this.phase==='AUS'?0:1;this.timer=0;this.events=[];
  this.groundHeight=sim.c.ground?sim.groundClearanceHeight():0;this.reference=[...sim.p];this.yaw=0;this.autoClimb=false;
  this.hoverOmega=sim.rpmHover*Math.PI/30;}
 log(text){this.events.push({t:+this.sim.t.toFixed(3),phase:this.phase,text});}
 setMode(mode){if(mode===this.mode)return;this.mode=mode;this.reference=[...this.sim.p];this.yaw=this.sim.snapshot().euler[2]*D;this.log('Modus '+mode);}
 start(){if(this.phase==='AUS'){this.phase='HOCHLAUF';this.timer=0;this.reference=[...this.sim.p];this.yaw=this.sim.snapshot().euler[2]*D;this.log('Hochlauf');}
  else if(this.phase==='AM_BODEN'||this.phase==='BEREIT'){this.phase='START';this.log('Start');}this.autoClimb=true;}
 land(){if(['FLUG','START'].includes(this.phase)){this.phase='LANDUNG';this.timer=0;this.reference=[...this.sim.p];this.log('Landung');}}
 stop(){if(this.phase!=='AUS'){this.phase='AUSLAUF';this.timer=0;this.log('Motoren aus');}}
 update(sticks={},dt=this.sim.c.dt){const s=this.sim,L=this.limits;let thr=clamp(sticks.throttle||0,-1,1),yaw=clamp(sticks.yaw||0,-1,1),pitch=clamp(sticks.pitch||0,-1,1),roll=clamp(sticks.roll||0,-1,1);
  this.timer+=dt;if(s.crashed&&this.phase!=='ABSTURZ'){this.phase='ABSTURZ';this.log('Absturz/Bodenkontakt außerhalb der Grenzen');}
  const hover=this.hoverOmega,idle={mode:'idle',thrust:L.idleThrustFraction*s.mass*9.81};
  // Rotordrehzahl: Rampe statt Sprung (ESC-Anlauf idealisiert).
  if(this.phase==='HOCHLAUF'){this.spool=Math.min(1,this.spool+dt/L.spoolUpS);if(this.spool>=1&&Math.min(...s.omega)>.95*hover){this.phase=this.autoClimb?'START':'BEREIT';this.log(this.autoClimb?'Start':'Bereit');}}
  else if(this.phase==='AUSLAUF'||this.phase==='ABSTURZ'){this.spool=Math.max(0,this.spool-dt/L.spoolDownS);if(this.spool<=0&&this.phase==='AUSLAUF'){this.phase='AUS';this.log('Aus');}}
  s.omegaTarget=this.spool*hover;
  let target;
  if(['AUS','HOCHLAUF','AUSLAUF','ABSTURZ','BEREIT'].includes(this.phase)){target={...idle,position:[s.p[0],s.p[1],this.groundHeight]};this.reference=[...s.p];if(this.phase==='BEREIT'&&thr>.3)this.start();}
  else if(this.phase==='START'){this.reference[2]=Math.min(this.groundHeight+L.takeoffHeight,this.reference[2]+.5*dt,s.p[2]+.2);
   if(this.mode==='POSITION')target={position:[...this.reference],yaw:this.yaw};else target={mode:'angle',roll:roll*L.angleDeg*D,pitch:pitch*L.angleDeg*D,yawRate:-yaw*L.yawRateDeg*D,climbRate:clamp(1.2*(this.reference[2]-s.p[2]),-.6,.6)};
   if(s.p[2]>this.groundHeight+.95*L.takeoffHeight){this.phase='FLUG';this.log('Schwebeflug');this.reference=[s.p[0],s.p[1],this.groundHeight+L.takeoffHeight];s.positionPID[2].i=0;}}
  else if(this.phase==='FLUG'){
   if(this.mode==='POSITION'){const c=Math.cos(this.yaw),sn=Math.sin(this.yaw),f=pitch*L.speedPosition,r=roll*L.speedPosition;this.reference[0]+=(c*f+sn*r)*dt;this.reference[1]+=(sn*f-c*r)*dt;this.reference[2]=Math.max(this.groundHeight+.15,this.reference[2]+thr*L.climbPosition*dt);this.yaw-=yaw*L.yawRateDeg*D*dt;target={position:[...this.reference],yaw:this.yaw};}
   else target={mode:'angle',roll:roll*L.angleDeg*D,pitch:pitch*L.angleDeg*D,yawRate:-yaw*L.yawRateDeg*D,climbRate:thr*L.climbAngle};}
  else if(this.phase==='LANDUNG'){this.reference[2]-=L.landingRate*dt;const z=Math.max(this.groundHeight-.06,this.reference[2]);
   if(this.mode==='POSITION'){const c=Math.cos(this.yaw),sn=Math.sin(this.yaw);this.reference[0]+=(c*pitch+sn*roll)*.3*dt;this.reference[1]+=(sn*pitch-c*roll)*.3*dt;target={position:[this.reference[0],this.reference[1],z],yaw:this.yaw};}
   else target={mode:'angle',roll:roll*10*D,pitch:pitch*10*D,yawRate:0,climbRate:-L.landingRate};
   // Aufsetzerkennung: mindestens vier Kufenpunkte 0,3 s im Kontakt, dann Leerlaufschub und Auslauf.
   if(s.onGround&&s.contactCount>=4){this.groundTimer=(this.groundTimer||0)+dt;if(this.groundTimer>.3){this.phase='AUSLAUF';this.timer=0;this.groundTimer=0;this.log('Aufgesetzt');}}else this.groundTimer=0;}
  if(this.mode==='POSITION'&&target.mode===undefined&&!target.position)target.position=[...this.reference];
  if(!target.position)target.position=[...(['FLUG','START','LANDUNG'].includes(this.phase)&&this.mode==='POSITION'?this.reference:s.p)];
  return{target,external:{}};}
}
const api={Manager,LIMITS};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.H01Flugsteuerung=api;
})(globalThis);
