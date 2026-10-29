"""Reuse the tested offline WebGL renderer with adaptive framing."""
import ast
from pathlib import Path
HERE=Path(__file__).resolve().parent
tree=ast.parse((HERE.parent/'bericht/viewer_erstellen.py').read_text())
template=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
              and any(isinstance(t,ast.Name) and t.id=='template' for t in n.targets))
template=template.replace('PropBoard: tatsächliche 3D-Modellgeometrien','PropBoard: Horizontal Z – Montage R02')
template=template.replace('beiden nativen FreeCAD-Dateien','fünf nativen FreeCAD-Dateien')
template=template.replace('beide nativen FCStd-Dateien','fünf nativen FCStd-Dateien')
template=template.replace('Vergleichsbericht.html','Konstruktionsbericht.html').replace('Vergleichsbericht','Konstruktionsbericht')
template=template.replace('color:#152336','color:#152336')
template=template.replace('<p class="small">SHA-256:', '<label><input type="checkbox" data-kind="pilot" checked> Personenreferenz</label><p class="small">SHA-256:')
template=template.replace('<p class="small">SHA-256:', '<label><input type="checkbox" data-kind="stator" checked> Stationäre Führung</label><p class="small">SHA-256:')
template=template.replace('uniform mat3 rotation;uniform vec2 scale;', 'uniform mat3 rotation;uniform vec2 scale;uniform vec3 origin;')
template=template.replace('position-vec3(0.,0.,.07)','position-origin')
template=template.replace("const count=model.parts.reduce",'''let min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];for(const p of model.parts)for(const v of p.vertices)for(let i=0;i<3;i++){min[i]=Math.min(min[i],v[i]/1000);max[i]=Math.max(max[i],v[i]/1000)}const origin=min.map((v,i)=>(v+max[i])/2),baseZoom=1.6/Math.max(...min.map((v,i)=>max[i]-v));gl.uniform3fv(gl.getUniformLocation(program,'origin'),new Float32Array(origin));
 const count=model.parts.reduce''')
template=template.replace('zoom=.8;const visible={wing:true,structure:true}', 'zoom=baseZoom;const visible={wing:true,structure:true,pilot:true,stator:true}')
template=template.replace('zoom=.8;draw()', 'zoom=baseZoom;draw()')
template=template.replace('Math.min(4,zoom*Math.exp', 'Math.min(12,zoom*Math.exp')
template=template.replace('Keine Animation', 'Keine Animation')
template=template.replace('keine Bewegungssimulation, kein Strömungsfeld, kein Tragfähigkeitsnachweis.',
    'keine Bewegungssimulation, keine Fertigungsfreigabe, kein Tragfähigkeitsnachweis. Orange: HV-/Statorraum; grün: LV-/Datenraum; blau: Akkubauraum. Die Personen sind unvalidierte Haltungsreferenzen.')
template=template.replace('<p class="small">SHA-256:', '<label><input type="checkbox" data-kind="fastener" checked> Schrauben / Muttern / Scheiben</label><p class="small">SHA-256:')
template=template.replace('pilot:true,stator:true}', 'pilot:true,stator:true,fastener:true}')
template=template.replace('Konstruktionsbericht.html','Montagebericht.pdf')
template=template.replace('Führung und Schlitten sind Bauraumplatzhalter.','Montagevorentwurf mit offenen Funktions- und Lastnachweisen.').replace('Strukturplatzhalter','Rahmen / Anbauteile')
template=template.replace('pilot:true','pilot:false').replace('data-kind="pilot" checked','data-kind="pilot"')
template=template.replace('for(const p of model.parts)for(const v of p.vertices)','for(const p of model.parts.filter(p=>p.kind!=="pilot"))for(const v of p.vertices)')
(HERE/'Modelle_3D.html').write_text(template.replace('__DATA__',(HERE/'Modelldaten.json').read_text()))
print('Konstruktionsviewer erstellt')
