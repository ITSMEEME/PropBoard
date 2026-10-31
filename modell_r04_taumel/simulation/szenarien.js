(function(root){'use strict';
const SAVOX74={servoGeometryProfile:'Savox_SB2271SG_USER',servoMassG:69,servoStallNm:1.96133,servoSpeedRadS:17.453292519943297,servoSupplyV:7.4,servoTorqueReference:'USER_ADVERTISED_DYNAMIC_TORQUE_NOT_VERIFIED_STALL'};
const P10={massModel:'P10',drive:'P10_HOHLRAD',ground:true,startOnGround:true};
const node=typeof module!=='undefined'&&module.exports,FS=node?require('./flugsteuerung.js'):root.H01Flugsteuerung;
const cases=[
 {name:'P11_EMAX_Referenz_Bodenstart',duration:8,mission:'p11_position',options:{...SAVOX74,massModel:'P11',drive:'P11_DIRECT',ground:true,startOnGround:true}},
 {name:'P11_EMAX_Referenz_ANGLE',duration:8,mission:'p11_angle',options:{...SAVOX74,massModel:'P11',drive:'P11_DIRECT',ground:true,startOnGround:true}},
 {name:'Schweben',duration:20,options:{}},
 {name:'Versetztes_Schweben',duration:25,options:{},initial:{p:[.35,-.25,1.25],angles:[8,-6,12]}},
 {name:'Steigen_und_Translation',duration:28,options:{},mission:true},
 {name:'Motor_Drehzahlsprung_10Prozent',duration:22,options:{},rpmStep:true},
 {name:'Boee_3ms',duration:24,options:{},gust:true},
 {name:'Massenvariante_60g_Servos',duration:20,options:{servoMassG:60,servoStallNm:1.471}},
 {name:'Reibung_hoch_starkes_Servo',duration:20,options:{servoFriction:.20,servoStallNm:1.471}},
 {name:'9g_Servo_hohe_Reibung',duration:20,options:{servoMassG:9,servoFriction:.20,servoStallNm:.1569}},
 {name:'Phase_30_Grad_falsch',duration:20,options:{cyclicPhaseDeg:30},initial:{angles:[8,-6,0]}},
 {name:'Phase_90_Grad_falsch',duration:20,options:{cyclicPhaseDeg:90},initial:{angles:[8,-6,0]}},
 {name:'Servo_blockiert',duration:20,options:{servoJammed:0},initial:{angles:[8,-6,0]}},
 {name:'Motor_unten_Ausfall',duration:16,options:{},motorFailure:true},
 {name:'Aerodynamik_minus25',duration:24,options:{thrustScale:.75}},
 {name:'Akku_20_Prozent',duration:20,options:{initialSoc:.2}},
 {name:'Savox_7_4V_Manoever',duration:28,mission:true,options:{servoGeometryProfile:'Savox_SB2271SG_USER',servoMassG:69,servoStallNm:1.96133,servoSpeedRadS:17.453292519943297,servoSupplyV:7.4,servoTorqueReference:'USER_ADVERTISED_DYNAMIC_TORQUE_NOT_VERIFIED_STALL'}},
 {name:'Savox_6_0V_Boee',duration:24,gust:true,options:{servoGeometryProfile:'Savox_SB2271SG_USER',servoMassG:69,servoStallNm:1.4709975,servoSpeedRadS:13.08996938995747,servoSupplyV:6,servoTorqueReference:'USER_ADVERTISED_DYNAMIC_TORQUE_NOT_VERIFIED_STALL'}},
 {name:'Savox_7_4V_Reibung_0_20',duration:24,mission:true,options:{servoGeometryProfile:'Savox_SB2271SG_USER',servoMassG:69,servoStallNm:1.96133,servoSpeedRadS:17.453292519943297,servoSupplyV:7.4,servoFriction:.2,servoTorqueReference:'USER_ADVERTISED_DYNAMIC_TORQUE_NOT_VERIFIED_STALL'}},
 {name:'Savox_7_4V_XFOIL_N4',duration:28,mission:true,options:{servoGeometryProfile:'Savox_SB2271SG_USER',servoMassG:69,servoStallNm:1.96133,servoSpeedRadS:17.453292519943297,servoSupplyV:7.4,servoTorqueReference:'USER_ADVERTISED_DYNAMIC_TORQUE_NOT_VERIFIED_STALL',polarSource:'XFOIL_N4'}},
 {name:'Ohne_Regelung',duration:20,options:{controller:false},initial:{angles:[8,-6,0]}},
 // P10: Servohalter, Planetenstufe (Motor gleichsinnig), Kabelbaum und Landegestell im Massenmodell; Bodenkontakt.
 {name:'P10_Bodenstart_Schweben_Landung',duration:30,mission:'p10_position',options:{...SAVOX74,...P10}},
 {name:'P10_ANGLE_Handsteuerung',duration:32,mission:'p10_angle',options:{...SAVOX74,...P10}},
 {name:'P10_Boee_3ms_Schweben',duration:24,gust:true,options:{...SAVOX74,...P10,startOnGround:false}}
];
// Scripted stick inputs for the P10 ground missions; the same Manager runs the interactive flight.
function missionSticks(c,t){const k={throttle:0,yaw:0,pitch:0,roll:0},on=(a,b)=>t>=a&&t<b;
 if(c.mission==='p10_position'){if(on(10,12))k.pitch=.5;if(on(13,14))k.roll=.5;if(on(15,16))k.yaw=.5;}
 else{if(on(8,9.5))k.pitch=.5;if(on(9.5,11))k.pitch=-.5;if(on(12,13))k.roll=.4;if(on(13,14))k.roll=-.4;if(on(15,16))k.throttle=.3;if(on(16.5,17.5))k.yaw=.5;}
 return k;}
function missionInputs(s,c){if(!s._manager)s._manager=new FS.Manager(s,{mode:String(c.mission).endsWith('_angle')?'ANGLE':'POSITION'});const m=s._manager;
 if(s.t>=.2&&m.phase==='AUS'&&!m._started){m._started=true;m.start();}if(s.t>=(String(c.mission).endsWith('_angle')?18:19)&&!m._landing){m._landing=true;m.land();}
 return m.update(missionSticks(c,s.t),s.c.dt);}
function inputs(s,c){if(c.mission&&/^p1[01]/.test(String(c.mission)))return missionInputs(s,c);let target={position:[0,0,1],yaw:0};if(c.mission&&s.t>=3)target={position:[.5,-.3,1.5],yaw:.35};
 if(c.gust)s.c.wind=s.t>=4&&s.t<7?[3,0,0]:[0,0,0];
 if(c.rpmStep)s.omegaTarget=s.rpmHover*Math.PI/30*(s.t>=4?1.1:1);
 if(c.motorFailure&&s.t>=4)s.c.motorScale=[1,0];
 let external=c.gust&&s.t>=4&&s.t<4.25?{moment:[.025,-.015,0]}:{};return{target,external};}
const api={cases,inputs,missionSticks};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.H01Scenarios=api;
})(globalThis);
