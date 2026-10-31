/* Parameter definitions for aerodynamic screening. Existing motor and gear ratio stay fixed. */
(function(root){'use strict';
const defaults={diameterMm:375,rootRadiusMm:48,chordMm:30,blades:8,thickness:.12,taper:1,twistDeg:0,spacingMm:60,rpm:null,pitchUpperDeg:14,pitchLowerDeg:16.7};
const ranges={diameterMm:[200,500],rootRadiusMm:[30,90],chordMm:[10,60],blades:[2,12],thickness:[.06,.2],taper:[.3,1.5],twistDeg:[-12,12],spacingMm:[30,180],rpm:[500,6000],pitchUpperDeg:[-2,21],pitchLowerDeg:[-2,21]};
function validate(input={}){for(const k of Object.keys(input))if(!Object.hasOwn(defaults,k))throw Error('Unbekannter Parameter '+k);const p={...defaults,...input};for(const [k,[min,max]] of Object.entries(ranges)){if(k==='rpm'&&p[k]===null)continue;if(!Number.isFinite(p[k])||p[k]<min||p[k]>max)throw Error(k+': Bereich '+min+' … '+max);}if(!Number.isInteger(p.blades))throw Error('Blattzahl muss ganzzahlig sein');if(p.rootRadiusMm>=p.diameterMm/2)throw Error('Innenradius muss kleiner als Außenradius sein');for(const k of ['pitchUpperDeg','pitchLowerDeg'])if(p[k]+Math.min(0,p.twistDeg)<-2||p[k]+Math.max(0,p.twistDeg)>21)throw Error('Pitch plus Verwindung muss im Bereich -2 … 21 Grad bleiben');return p;}
function blade(p){return{r_tip:p.diameterMm/2,r_airfoil_start:p.rootRadiusMm,chord:p.chordMm,count:p.blades,tc:p.thickness};}
const api={defaults,ranges,validate,blade};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.H01Design=api;
})(globalThis);
