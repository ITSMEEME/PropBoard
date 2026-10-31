'use strict';
// Requirements from the same stationary model as the visual bench; no motor SKU assumed.
const fs=require('node:fs'),path=require('node:path'),F=require('../simulation/flugphysik.js'),D=require('../simulation/design.js'),S=require('../simulation/parameterstudie.js');
const s=new F.Flight({drive:'P11_DIRECT',servoMassG:69,servoGeometryProfile:'Savox_SB2271SG_USER',noise:false});
const point=S.evaluate(s,{...D.defaults,rpm:Math.round(s.rpmHover)}),omega=point.design.rpm*Math.PI/30;
const report={method:'Stationary Flight.aero, simplified polar, assumed P11 mass budget, prescribed RPM',native_sha256:F.P11.source_native_sha256,massKg:s.mass,rpm:point.design.rpm,thrustN:point.thrustN,thrustEquivalentKg:point.thrustN/9.81,ratio:1,motorSelectionPending:true,
 motors:point.torqueNm.map((q,i)=>({rotor:i,continuousTorqueNm:q/s.drive.efficiency,mechanicalPowerW:q*omega/s.drive.efficiency,additionalAccelerationTorqueNm_3s:(s.spinInertia[i]+s.idlerSpin*s.guideRatio**2)*omega/3})),
 emaxReference:{reachable:point.withinMotorEnvelope,requiredPhaseCurrentA:point.motorCurrentA,batteryPowerW:point.powerW,copperLossW:point.copperLossW},
 limitations:['No load safety factor or thermal design included','No measured polar or validated coaxial interference','Acceleration estimate is inertia only; add aero torque at each speed','Not a motor specification or flight release']};
fs.writeFileSync(path.join(__dirname,'Ausgabe/Motoranforderungen_P11.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
