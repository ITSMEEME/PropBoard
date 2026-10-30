/* Strict interpolation of calculated, converged XFOIL points; no silent extrapolation. */
(function(root){'use strict';const node=typeof module!=='undefined'&&module.exports;
const data=node?require('./Ausgabe/Polaren.json'):root.H01_POLARS;
function alphaPoint(table,alpha){let a=Math.floor(alpha),b=Math.ceil(alpha),lo=table.rows.find(r=>r.alpha===a),hi=table.rows.find(r=>r.alpha===b);if(!lo||!hi)return null;let f=b===a?0:(alpha-a)/(b-a);return{cl:lo.cl+(hi.cl-lo.cl)*f,cd:lo.cd+(hi.cd-lo.cd)*f,cm:lo.cm+(hi.cm-lo.cm)*f};}
function query(alpha,re,ncrit=4){const tables=data.tables.filter(t=>t.ncrit===ncrit).sort((a,b)=>a.re-b.re);if(re<tables[0].re||re>tables.at(-1).re||alpha< -6||alpha>16)return null;
 let i=0;while(i<tables.length-2&&re>tables[i+1].re)i++;let lo=alphaPoint(tables[i],alpha),hi=alphaPoint(tables[i+1],alpha);if(!lo||!hi)return null;
 let f=(Math.log(re)-Math.log(tables[i].re))/(Math.log(tables[i+1].re)-Math.log(tables[i].re));return{cl:lo.cl+(hi.cl-lo.cl)*f,cd:lo.cd+(hi.cd-lo.cd)*f,cm:lo.cm+(hi.cm-lo.cm)*f,stalled:Math.abs(alpha)>10,source:'COMPUTED_XFOIL_INTERPOLATION'};}
const api={query,data};if(node)module.exports=api;else root.H01PolarLookup=api;
})(globalThis);
