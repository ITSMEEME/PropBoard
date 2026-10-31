/* Calibration dialog; control and physics remain in ui.js. */
'use strict';
window.H01GamepadUI=function(controller,hooks){
 const el=id=>document.getElementById(id),dialog=el('calibration');let message='';
 const names={yaw:'Gier: rechts',throttle:'Steigen: nach oben',roll:'Roll: rechts',pitch:'Nick: nach oben'};
 function controls(){const p=controller.draft;el('calChannels').replaceChildren();
  for(const c of H01Gamepad.channels){const row=document.createElement('tr'),label=document.createElement('td'),axisCell=document.createElement('td'),invertCell=document.createElement('td'),live=document.createElement('td'),range=document.createElement('td');
   label.textContent=names[c];const axis=document.createElement('select');axis.id='calAxis_'+c;axis.setAttribute('aria-label','Achse '+names[c]);
   p.center.forEach((_,i)=>axis.add(new Option('Achse '+i,i)));axis.value=p.channels[c].axis;axis.onchange=()=>{p.channels[c].axis=+axis.value;message='';};
   const inv=document.createElement('input');inv.type='checkbox';inv.id='calInvert_'+c;inv.checked=p.channels[c].invert;inv.setAttribute('aria-label','Invertieren '+names[c]);inv.onchange=()=>p.channels[c].invert=inv.checked;
   axisCell.append(axis);invertCell.append(inv);live.id='calLive_'+c;range.id='calRange_'+c;row.append(label,axisCell,invertCell,live,range);el('calChannels').append(row);
  }el('calDeadzone').value=Math.round(p.deadzone*100);
 }
 el('calibrate').onclick=()=>{if(!controller.begin()){el('gamepad').textContent='Zum Kalibrieren Gamepad verbinden und einen Knopf drücken (mindestens 4 Achsen).';return;}
  hooks.pause();hooks.clear();message='';controls();dialog.showModal();update();};
 el('calCenter').onclick=()=>{message=controller.captureCenter()?'Mitte erfasst. Jetzt alle zugeordneten Achsen in beide Richtungen bis zum Anschlag bewegen.':'Gerät nicht verfügbar. Ursprüngliches Gamepad wieder verbinden.';update();};
 el('calDeadzone').oninput=()=>{if(el('calDeadzone').checkValidity()&&controller.draft)controller.draft.deadzone=+el('calDeadzone').value/100;};
 el('calSave').onclick=()=>{if(!el('calDeadzone').reportValidity())return;const result=controller.save();if(result.ok){hooks.clear();dialog.close();el('gamepad').textContent=result.persisted?'Kalibrierung gespeichert. Mit „Fortsetzen“ weiterfliegen.':'Kalibrierung für diese Sitzung aktiv; Browser-Speicher nicht verfügbar.';}else{message=result.message;update();}};
 const cancel=()=>{controller.cancel();hooks.clear();dialog.close();};el('calCancel').onclick=cancel;dialog.addEventListener('cancel',e=>{e.preventDefault();cancel();});
 el('calReset').onclick=()=>{if(controller.reset()){hooks.clear();dialog.close();}else{message='Ursprüngliches Gamepad wieder verbinden oder abbrechen.';update();}};
 function update(){if(!controller.active)return;const gp=controller.gp,p=controller.draft,connected=controller.identify(gp)===controller.key;
  el('calDevice').textContent=connected?gp.id:'Gamepad getrennt oder anderes Gerät verbunden. Ursprüngliches Gerät wieder verbinden oder abbrechen.';
  el('calRaw').textContent=connected?'Rohachsen: '+gp.axes.map((v,i)=>i+': '+v.toFixed(3)).join(' · '):'Keine Rohwerte';
  for(const c of H01Gamepad.channels){const i=p.channels[c].axis;el('calLive_'+c).textContent=connected?H01Gamepad.normalize(gp.axes,p,c).toFixed(3):'–';el('calRange_'+c).textContent=[p.min[i],p.center[i],p.max[i]].map(v=>v.toFixed(2)).join(' / ');}
  el('calCenter').disabled=!connected;el('calSave').disabled=!connected||controller.stage!=='range';
  el('calStatus').textContent=message||(controller.stage==='center'?'Zuerst die Mittelstellung erfassen.':'Endpunkte werden erfasst. Livewerte prüfen und speichern.');
 }
 return {update};
};
