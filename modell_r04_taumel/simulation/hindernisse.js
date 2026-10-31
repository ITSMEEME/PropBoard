/* Axis-aligned obstacle course; conservative swept-sphere vehicle collision. SI. */
(function(root){'use strict';
const scenes={none:[],training:[
 {id:'Pfeiler links',min:[1.5,-1.3,0],max:[1.8,-.8,1.8]},
 {id:'Pfeiler rechts',min:[1.5,.8,0],max:[1.8,1.3,1.8]},
 {id:'Tor links',min:[3.5,-1.2,0],max:[3.8,-.8,2.3]},
 {id:'Tor rechts',min:[3.5,.8,0],max:[3.8,1.2,2.3]},
 {id:'Tor Querbalken',min:[3.5,-.8,1.9],max:[3.8,.8,2.3]},
 {id:'Block',min:[5.2,-.4,0],max:[5.9,.4,.8]}
],slalom:[
 {id:'Slalom 1',min:[1.5,-.9,0],max:[1.9,.2,1.8]},
 {id:'Slalom 2',min:[3,-.2,0],max:[3.4,.9,1.8]},
 {id:'Slalom 3',min:[4.5,-.9,0],max:[4.9,.2,1.8]}
]};
function valid(items){return Array.isArray(items)&&items.length<=100&&items.every(b=>typeof b.id==='string'&&['min','max'].every(k=>Array.isArray(b[k])&&b[k].length===3&&b[k].every(Number.isFinite))&&b.min.every((v,i)=>v<b.max[i]));}
function course(name){if(!Object.hasOwn(scenes,name))throw Error('Unbekannter Parcours');return scenes[name].map(b=>({id:b.id,min:[...b.min],max:[...b.max]}));}
// Slab test against the Minkowski-expanded AABB. Conservative at box edges/corners.
function segmentHit(a,b,r,box){let enter=0,exit=1;for(let k=0;k<3;k++){let lo=box.min[k]-r,hi=box.max[k]+r,d=b[k]-a[k];if(Math.abs(d)<1e-12){if(a[k]<lo||a[k]>hi)return null;continue;}let x=(lo-a[k])/d,y=(hi-a[k])/d;if(x>y)[x,y]=[y,x];enter=Math.max(enter,x);exit=Math.min(exit,y);if(enter>exit)return null;}return enter;}
function collision(a,b,r,items){let hit=null;for(const item of items){let t=segmentHit(a,b,r,item);if(t!==null&&(!hit||t<hit.t))hit={id:item.id,t,point:a.map((v,i)=>v+(b[i]-v)*t)};}return hit;}
const api={scenes,course,valid,segmentHit,collision};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.H01Obstacles=api;
})(globalThis);
