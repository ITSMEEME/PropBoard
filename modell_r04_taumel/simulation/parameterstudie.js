/* Stationary screening with the SAME blade-element force model as Flight.aero(). */
(function(root){'use strict';
const node=typeof module!=='undefined'&&module.exports,F=node?require('./flugphysik.js'):root.H01Flight,
 D=node?require('./design.js'):root.H01Design,A=node?require('../../modell_r04/auslegung/antrieb.js'):root.R04Antrieb;
function evaluate(base,input,limits={}){const design=D.validate(input);if(design.rpm===null)throw Error('Für die Studie Drehzahl explizit angeben');
 const s=Object.create(F.Flight.prototype);Object.assign(s,{c:{...base.c,noise:false,wind:[0,0,0],ground:false,polarSource:'SIMPLIFIED'},design,geometry:D.blade(design),spacing:design.spacingMm/1000,mass:base.mass,cg:[...base.cg],q:[1,0,0,0],p:[0,0,1],v:[0,0,0],w:[0,0,0],vi:[4,6],omega:[design.rpm,design.rpm].map(v=>v*Math.PI/30),poses:F.KIN.map(k=>[...k.neutral])});
 let converged=false,iterations=0;
 for(;iterations<180;iterations++){const before=[...s.vi],f=s.aero();s.updateInflow(f,.02);if(iterations>30&&Math.max(...s.vi.map((v,i)=>Math.abs(v-before[i])))<1e-5){converged=true;break;}}
 const aero=s.aero(),drive=A.systemPoint(A.MOTOR_ECO2_2306_1900,A.BATTERY_TATTU_1550_6S,{rpm:design.rpm,Q:aero.Q[0]},{rpm:design.rpm,Q:aero.Q[1]},6.5,base.c.initialSoc,undefined,6);
 const target=base.mass*9.81,thrust=aero.T[0]+aero.T[1],hoverError=(thrust-target)/target,yawError=Math.abs(aero.Q[0]-aero.Q[1])/Math.max(1e-9,Math.abs(aero.Q[0])+Math.abs(aero.Q[1])),tipMach=s.omega[0]*design.diameterMm/2000/340;
 const constraints={converged,hover:hoverError>=0&&hoverError<=(limits.hoverTolerance??.08),yaw:yawError<=(limits.yawTolerance??.1),motor:drive.feasible&&Math.max(drive.upper.current,drive.lower.current)<=(limits.currentLimit??20),stall:aero.stalledFraction<=(limits.stallTolerance??.1),tipMach:tipMach<.65};
 return {design,massKg:base.mass,thrustN:thrust,targetN:target,hoverError,yawError,powerW:drive.pBus,currentA:drive.batteryCurrent,motorCurrentA:[drive.upper.current,drive.lower.current],duty:drive.duty,torqueNm:aero.Q,stalledFraction:aero.stalledFraction,tipMach,iterations,converged,constraints,feasible:Object.values(constraints).every(Boolean)};
}
function grid(base,axes){let rows=[{}];for(const [k,values] of Object.entries(axes)){if(!Object.hasOwn(D.defaults,k)||!Array.isArray(values)||!values.length||!values.every(Number.isFinite))throw Error('Ungueltige Parameterliste '+k);if(rows.length*values.length>2000)throw Error('Maximal 2000 Kombinationen; Listen verkleinern');rows=rows.flatMap(row=>values.map(value=>({...row,[k]:value})));}return rows.map(row=>D.validate({...base,...row}));}
function rank(rows){return rows.filter(r=>r.feasible).sort((a,b)=>a.powerW-b.powerW);}
const api={evaluate,grid,rank};if(node)module.exports=api;else root.H01Study=api;
})(globalThis);
