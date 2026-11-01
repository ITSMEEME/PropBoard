'use strict';
window.P11SearchUI=function(hooks){
 const $=id=>document.getElementById(id);let result=null,running=false,cancelled=false;
 function render(r){result=r;const rows=r.top10Electrical.length?r.top10Electrical:r.top10Aerodynamic,actual=r.top10Electrical.length>0;
  $('searchStatus').textContent=`${r.status==='PARTIAL_CANCELLED'?'Abgebrochenes Teilergebnis':'Suchergebnis'} · ${r.stats.attempted} Entwürfe · ${r.stats.evaluations} Rechnungen · ${r.stats.aeroAccepted} aerodynamisch vorgeprüft · ${r.stats.verifiedAccepted??0} in feinen Rastern bestätigt · ${r.stats.electricalAccepted} innerhalb EMAX-Suchgrenzen. Masse ${r.massKg.toFixed(3)} kg.`;
  $('searchRanking').textContent=actual?'Top 10 innerhalb EMAX-Suchgrenzen, sortiert nach elektrischer Leistung. Stromgrenze ist eine Screening-Annahme, keine Dauerfreigabe.':'Keine Treffer innerhalb der EMAX-Suchgrenzen (20 A je Motor). Top 10 aerodynamische Entwürfe nach mechanischer Rotorleistung; passender Motor offen. Elektrische Zahlen sind extrapolierter EMAX-Bedarf.';
  $('searchRows').replaceChildren();rows.forEach((p,i)=>{const tr=document.createElement('tr'),d=p.design;for(const v of [i+1,d.diameterMm.toFixed(1),d.rootRadiusMm.toFixed(1),d.chordMm.toFixed(1),d.blades,d.thickness.toFixed(3),d.taper.toFixed(2),d.twistDeg.toFixed(2),d.spacingMm.toFixed(1),d.rpm.toFixed(0),d.pitchUpperDeg.toFixed(2)+' / '+d.pitchLowerDeg.toFixed(2),(p.thrustN/9.81).toFixed(3),p.mechanicalPowerW.toFixed(1),p.powerW.toFixed(1),p.currentA.toFixed(2),(100*p.mechanicalPowerW/p.powerW).toFixed(1),p.motorCurrentA.map(v=>v.toFixed(1)).join(' / ')]){const td=document.createElement('td');td.textContent=v;tr.append(td);}const td=document.createElement('td'),button=document.createElement('button');button.textContent='Ansehen';button.onclick=()=>hooks.apply(d,r.massKg);td.append(button);tr.append(td);$('searchRows').append(tr);});
  $('exportSearch').disabled=false;
 }
 $('runSearch').onclick=async()=>{if(running)return;running=true;cancelled=false;$('runSearch').disabled=true;$('cancelSearch').disabled=false;try{
  const b=hooks.base(),r=await H01Search.run(b,{samples:4096,refinements:1024,progress:p=>{$('searchStatus').textContent=`${p.phase==='global'?'Gesamter Bereich':p.phase==='verify'?'Feinprüfung':'Lokale Verfeinerung'} ${p.done} / ${p.total} · ${p.aeroAccepted} aerodynamisch · ${p.electricalAccepted} elektrisch zulässig`;},cancelled:()=>cancelled,yield:()=>new Promise(resolve=>setTimeout(resolve,0))});render(r);
 }catch(e){$('searchStatus').textContent=e.message;}finally{running=false;$('runSearch').disabled=false;$('cancelSearch').disabled=true;}};
 $('cancelSearch').onclick=()=>{cancelled=true;};
 $('exportSearch').onclick=()=>{if(!result)return;const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='P11-Kandidatensuche.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 if(window.P11_SEARCH_RESULTS){if(P11_SEARCH_RESULTS.native_sha256===H01Flight.P11.source_native_sha256)render(P11_SEARCH_RESULTS);else $('searchStatus').textContent='Gespeicherte Suche gehört zu einer älteren CAD-Revision. Suche erneut starten.';}
 return{get result(){return result;},get running(){return running;}};
};
