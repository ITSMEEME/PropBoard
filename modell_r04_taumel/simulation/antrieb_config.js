/* Active direct drive and explicit historical drive definitions. No motor data is invented. */
(function(root){'use strict';
const modes={H01_AUSSENVERZAHNUNG:{ratio:6.5,efficiency:.92,motorSense:-1,motorSpinJ:1.2e-6,motorSelectionPending:false},P10_HOHLRAD:{ratio:6.5,efficiency:.92,motorSense:1,motorSpinJ:1.2e-6,motorSelectionPending:false},P11_DIRECT:{ratio:1,efficiency:.98,motorSense:1,motorSpinJ:0,motorSelectionPending:true}};
function resolve(name='P11_DIRECT'){if(!Object.hasOwn(modes,name))throw Error('Unbekannter Antrieb '+name);return{...modes[name],name,electricalReference:'EMAX ECO II 2306 KV1900'};}
const api={resolve,active:'P11_DIRECT'};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.H01Drive=api;
})(globalThis);
