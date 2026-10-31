'use strict';
// Offline custom-airframe mixer from the nominal P10 force/moment Jacobian.
const F=require('./flugphysik.js'),S=require('./szenarien.js');
const s=new F.Flight({...S.cases.find(c=>c.name==='Savox_7_4V_Manoever').options,massModel:'P10',drive:'P10_HOHLRAD',noise:false});
const columns=[1,2,3].map(axis=>{const w=F.solve(s.BBt,[0,1,2,3].map(i=>i===axis?1:0));return s.B[0].map((_,j)=>s.B.reduce((v,r,i)=>v+r[j]*w[i],0));});
const lines=['mixer CUSTOMAIRPLANE','mmix reset','mmix 0 1 0 0 0','mmix 1 1 0 0 0','smix reset'];let rule=0;
// Betaflight body pitch/yaw have opposite signs to the NWU model convention.
for(let j=0;j<6;j++)for(let k=0;k<3;k++){const max=Math.max(...columns[k].map(Math.abs)),rate=Math.round(90*columns[k][j]/max*(k===0?1:-1));lines.push(`smix ${rule++} ${j+2} ${k} ${rate} 0 0 100 0`);}
for(let j=2;j<8;j++)lines.push(`servo ${j} 1000 2000 1500 100 6`); // AUX3 is collective center, PID outputs are native firmware rules.
lines.push('feature RX_MSP','feature -GPS','feature -TELEMETRY','set motor_pwm_protocol = PWM','set motor_pwm_rate = 480','set min_command = 1000','set min_throttle = 1000','set max_throttle = 2000','set small_angle = 180','set gyro_cal_on_first_arm = OFF','set acc_calibration = 0,0,0,0','set pid_process_denom = 1','set yaw_motors_reversed = OFF','aux 0 0 0 1700 2100 0 0','aux 1 1 1 1700 2100 0 0','map AETR1234');
process.stdout.write(lines.join('\n')+'\n');
