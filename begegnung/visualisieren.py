"""Phase-resolved actual computed fields; no interpolated flow snapshots."""
import os,sys,json,base64,io,math
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/propboard-matplotlib')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/propboard-cache')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colormaps
from PIL import Image
HERE=Path(__file__).resolve().parent
out=HERE/'results'
d=np.load(out/'Zeitfelder.npz');fields=d['fields'];times=d['times'];dx=float(d['dx']);u=float(d['u'])
ny,nx=fields.shape[2:];x=(np.arange(nx)-nx/2)*dx;z=float(d['z_start'])+np.arange(ny)*dx
extent=[x[0]-dx/2,x[-1]+dx/2,z[0]-dx/2,z[-1]+dx/2]
derived=[];encoded=[];metrics=[]
configs=[('Geschwindigkeit |u|/U','viridis',0,1.2),('Wirbelstärke ωc/U','RdBu_r',-3,3),('Druckbeiwert Cp','RdBu_r',-2,2)]
for k,(rho,ux,uz,mask) in enumerate(fields):
    omega=(np.gradient(uz,axis=1)-np.gradient(ux,axis=0))*24/u
    speed=np.sqrt(ux**2+uz**2)/u
    cp=2*(rho-1)/(3*u*u)
    arrays=[speed,omega,cp];derived.append(arrays)
    ims=[]
    for values,(_,cmap,lo,hi) in zip(arrays,configs):
        rgba=(colormaps[cmap](np.clip((values-lo)/(hi-lo),0,1))*255).astype(np.uint8)
        rgba[mask>.5]=[30,35,45,255]
        image=Image.fromarray(rgba[::-1]).resize((384,580),resample=Image.Resampling.NEAREST)
        buf=io.BytesIO();image.save(buf,format='PNG')
        ims.append(base64.b64encode(buf.getvalue()).decode())
    encoded.append(ims)
    region=(np.abs(z[:,None])<.06)&(np.abs(x[None,:])<.06)
    metrics.append({'passage':float(times[k]),'phase':float((2*times[k])%1),
                    'mean_uz_over_U_centre_gap':float((uz/u)[region].mean()),
                    'mean_Cp_centre_gap':float(cp[region].mean())})
targets=[18.9,19.,19.1];indices=[int(np.argmin(abs(times-t))) for t in targets]
for scalar,filename in [(0,'Begegnung_Geschwindigkeit.png'),(1,'Begegnung_Wirbel.png'),(2,'Begegnung_Druck.png')]:
    fig,axes=plt.subplots(1,3,figsize=(12,7),sharex=True,sharey=True)
    _,cmap,lo,hi=configs[scalar]
    for ax,k,label in zip(axes,indices,['Vor Begegnung','Direkt übereinander','Nach Begegnung']):
        rho,ux,uz,mask=fields[k];values=np.ma.array(derived[k][scalar],mask=mask>.5)
        im=ax.imshow(values,origin='lower',extent=extent,cmap=cmap,vmin=lo,vmax=hi,interpolation='nearest')
        ax.contour(mask,levels=[.5],colors='#111111',linewidths=.8,origin='lower',extent=extent)
        xx,zz=np.meshgrid(x,z);step=8
        ax.quiver(xx[::step,::step],zz[::step,::step],(ux/u)[::step,::step],(uz/u)[::step,::step],color='black',alpha=.7,scale=15,width=.003)
        ax.axvline(0,color='white',lw=.6,alpha=.7)
        ax.set(xlabel='x [m], Geometrieskalierung',ylim=(-.30,.30),title=f'{label}\nDurchgang {times[k]:.2f}')
        ax.text(.02,.97,'oben ←\nunten →',transform=ax.transAxes,va='top',bbox={'facecolor':'white','alpha':.75,'edgecolor':'none'})
    axes[0].set_ylabel('z [m]')
    color_axis=fig.add_axes([.90,.18,.018,.58])
    fig.colorbar(im,cax=color_axis,label=configs[scalar][0])
    fig.suptitle('Gegenläufige Flügel, 240 mm Ebenenabstand / 120 mm Sehne\nTatsächliche 2D-LBM-Zeitfelder bei Re = 40 – keine realmaßstäbliche 3D-CFD')
    fig.text(.5,.025,'Pfeile: momentane Fluidgeschwindigkeit im ruhenden Board-Bezugssystem. Keine Partikelbahnen.',ha='center',fontsize=9)
    fig.subplots_adjust(top=.82,bottom=.12,right=.86,wspace=.08)
    fig.savefig(out/filename,dpi=170);plt.close(fig)

a=d['history'];sel=(a[:,1]>=18.75)&(a[:,1]<=19.25)
fig,ax=plt.subplots(figsize=(11,4.5))
for col,label in [(4,'Unterer Flügel →'),(6,'Oberer Flügel ←')]:
    part=a[sel];window=80
    ax.plot(part[:,1],part[:,col],lw=.4,alpha=.15)
    smooth=np.convolve(part[:,col],np.ones(window)/window,mode='valid')
    ax.plot(part[window//2:len(part)-(window-1)//2,1],smooth,label=label,lw=1.5)
ax.axvline(19,color='black',ls='--',label='gleiche x-Position')
ax.set(xlabel='Flügeldurchgänge',ylabel='Cz pro Reihe',title='Kraftverlauf um die direkte Begegnung – Re = 40\nDünn: ungeglättet; dick: gleitendes Mittel über 80 Rechenschritte')
ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/'Begegnung_Kraefte.png',dpi=170);plt.close(fig)

gif=[]
for k in range(len(times)):
    image=Image.open(io.BytesIO(base64.b64decode(encoded[k][0]))).convert('RGB')
    from PIL import ImageDraw
    draw=ImageDraw.Draw(image)
    _,ux,uz,mask=fields[k]
    for jj in range(4,ny-4,10):
        for ii in range(4,nx-4,10):
            if mask[jj,ii]>.5:continue
            px=ii/nx*384;py=(ny-1-jj)/ny*580
            vx=25*float(ux[jj,ii])/u;vy=-25*float(uz[jj,ii])/u
            if math.hypot(vx,vy)<1:continue
            draw.line((px,py,px+vx,py+vy),fill='white',width=1)
            angle=math.atan2(vy,vx)
            for delta in [-.5,.5]:
                draw.line((px+vx,py+vy,px+vx-3*math.cos(angle+delta),py+vy-3*math.sin(angle+delta)),fill='white')
    draw.rectangle((0,0,384,54),fill='white')
    draw.text((10,6),f'2D CFD Re=40 | passage {times[k]:.3f}',fill='black')
    draw.text((10,25),'Upper wing <- | Lower wing -> | speed/U',fill='black')
    gif.append(image)
gif[0].save(out/'Begegnung_Flow.gif',save_all=True,append_images=gif[1:],duration=80,loop=0)
(out/'Spaltkennwerte.json').write_text(json.dumps(metrics,indent=2))

legends=[]
for _,cmap,_,_ in configs:
    rgba=(colormaps[cmap](np.linspace(0,1,256))[None,:,:]*255).astype(np.uint8)
    buffer=io.BytesIO();Image.fromarray(rgba).resize((300,16)).save(buffer,format='PNG')
    legends.append(base64.b64encode(buffer.getvalue()).decode())
payload={'times':times.tolist(),'images':encoded,'metrics':metrics,'legends':legends,
         'ranges':[{'label':name,'low':lo,'high':hi} for name,_,lo,hi in configs]}
html=r'''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Flügelbegegnung – CFD-Zeitfelder</title>
<style>body{font:16px system-ui;max-width:1050px;margin:25px auto;padding:0 20px;color:#182b3b} .layout{display:flex;gap:24px;flex-wrap:wrap}img{width:384px;max-width:100%;border:1px solid #ccc}input{width:95%}button,select{padding:8px;margin:6px}aside{max-width:520px;line-height:1.6}.box{background:#eff4f7;padding:16px}h1{font-size:26px}</style>
<h1>Direkte Begegnung zweier gegenläufiger Flügel</h1><p class="box"><b>Vorhandenes Modell:</b> lokaler gerader 2D-Bahnausschnitt, Re = 40, künstliche Viskosität. Ebenenabstand 240 mm, Sehne 120 mm, Pitch 12°. Keine reale Fluglast, keine vollständige 3D-Strömung, kein Konvergenznachweis.</p>
<div class="layout"><img id="field" alt="Tatsächlich berechnetes Strömungsfeld"><aside><select id="scalar"><option value="0">Geschwindigkeit |u|/U</option><option value="1">Wirbelstärke ωc/U</option><option value="2">Druckbeiwert Cp</option></select><br><button id="play">Abspielen</button><button id="meet">Direkt übereinander</button><p id="time"></p><input id="slider" type="range" min="0" step="1"><p id="scale"></p><img id="legend" style="width:300px;height:16px" alt="Farbskala: links Minimum, rechts Maximum"><p id="gap"></p><p><b>Oben: ← &nbsp; Unten: →</b><br>x horizontal, z nach oben. Bildbereich: eine periodische Länge von 480 mm, z ungefähr −360 bis +360 mm. Dunkel: bewegte Festkörperzellen.</p><p>Alle Bilder sind gespeicherte CFD-Zeitfelder; es wird keine Zwischenströmung erfunden oder interpoliert. Die Animation ist verlangsamt und zeigt keine reale Flugzeit. Die Farben ändern sich beim Umschalten der Größe; Farbbereiche bleiben innerhalb einer Größe konstant.</p><p>Spaltmittel beziehen sich auf das zentrale Rechteck |x| &lt; 60 mm, |z| &lt; 60 mm. Das Vorzeichen von u_z ist nach oben positiv. Cp stammt aus dem LBM-Dichtefeld, nicht aus einer Bernoulli-Schätzung. Rand- und Zeiteinflüsse sind nicht abschließend untersucht.</p></aside></div>
<script>const data=__DATA__;const slider=document.querySelector('#slider'),scalar=document.querySelector('#scalar');slider.max=data.times.length-1;let timer=null;
function show(){let k=+slider.value,s=+scalar.value,t=data.times[k],phase=(2*t)%1;document.querySelector('#field').src='data:image/png;base64,'+data.images[k][s];document.querySelector('#legend').src='data:image/png;base64,'+data.legends[s];let aligned=Math.min(phase,1-phase)<.001;document.querySelector('#time').textContent='Durchgang '+t.toFixed(3)+' · Begegnungsphase '+phase.toFixed(3)+(aligned?' · GLEICHE x-POSITION':'');let r=data.ranges[s];document.querySelector('#scale').textContent=r.label+' · Farbbereich '+r.low+' bis '+r.high;let m=data.metrics[k];document.querySelector('#gap').textContent='Zentrales Spaltmittel: uz/U = '+m.mean_uz_over_U_centre_gap.toFixed(4)+'; Cp = '+m.mean_Cp_centre_gap.toFixed(4)}
slider.oninput=show;scalar.onchange=show;document.querySelector('#play').onclick=()=>{if(timer){clearInterval(timer);timer=null;document.querySelector('#play').textContent='Abspielen'}else{timer=setInterval(()=>{slider.value=(+slider.value+1)%data.times.length;show()},80);document.querySelector('#play').textContent='Pause'}};document.querySelector('#meet').onclick=()=>{slider.value=data.times.reduce((best,t,k)=>Math.abs(t-19)<Math.abs(data.times[best]-19)?k:best,0);show()};slider.value=data.times.findIndex(t=>Math.abs(t-19)<.0001);show();</script></html>'''
(out/'Flow_Interaktiv.html').write_text(html.replace('__DATA__',json.dumps(payload,separators=(',',':'))))
summary=[{'target':t,'stored_time':float(times[k]),**metrics[k]} for t,k in zip(targets,indices)]
for item in summary:
    centre_step=item['target']*float(d['period'])
    window=a[np.abs(a[:,0]-centre_step)<=20]
    item['Cz_lower_window_mean']=float(window[:,4].mean())
    item['Cz_upper_window_mean']=float(window[:,6].mean())
    item['Cz_total_window_mean']=float((window[:,4]+window[:,6]).mean())
    item['force_window_steps']=len(window)
(out/'Begegnungsphasen.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
