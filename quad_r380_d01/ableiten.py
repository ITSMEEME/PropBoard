"""Export editable individual parts, actual CAD mesh instances and check drawings."""
import sys,json,math,html,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,TechDraw,MeshPart
V=A.Vector;doc=A.openDocument(str(O/'QuadR380_D01_Mechanik.FCStd'));bom=json.loads((O/'Instanzen.json').read_text());spec=json.loads((O/'Bauteile.json').read_text());meshes={};partdata=[]
for key in dict.fromkeys(r['id'] for r in bom):
    row=next(r for r in bom if r['id']==key);master=doc.getObject(row['instance']).LinkedObject;s=master.Shape;mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.15,AngularDeflection=.6 if key.startswith("ISO") else .35,Relative=False);v,f=mesh.Topology
    meshes[key]=dict(vertices_mm=[[round(x,5) for x in p] for p in v],faces=f,material=spec[key]['material'],label=master.Label)
    if key.startswith('ISO'):continue
    out=A.newDocument('Teil_'+key);copied=out.copyObject(master,True);out.recompute();copied.Visibility=True
    for q in copied.Group:
        if hasattr(q,'Visibility'):q.Visibility=q==copied.Tip
    out.saveAs(str(O/'Einzelteile'/(key+'.FCStd')));A.closeDocument(out.Name)
    sketches=[];hole_groups=[]
    for q in master.Group:
        if q.TypeId=='Sketcher::SketchObject':sketches.append(dict(name=q.Name,fully_constrained=bool(q.FullyConstrained)))
        if q.TypeId not in ['PartDesign::Pocket','PartDesign::Hole']:continue
        try:profile=q.Profile[0] if isinstance(q.Profile,tuple) else q.Profile
        except:continue
        if not profile or not hasattr(profile,'Geometry'):continue
        circles=[]
        for g in profile.Geometry:
            if type(g).__name__=='Circle':circles.append(dict(centre_mm=list(profile.Placement.multVec(g.Center)),profile_diameter_mm=2*g.Radius))
        if circles:hole_groups.append(dict(feature=q.Name,type=q.TypeId,holes=circles,depth_mm=float(q.Depth if q.TypeId=='PartDesign::Hole' else q.Length),thread=str(q.ThreadSize) if q.TypeId=='PartDesign::Hole' else None,thread_class=str(q.ThreadClass) if q.TypeId=='PartDesign::Hole' else None,model_thread=bool(q.ModelThread) if q.TypeId=='PartDesign::Hole' else False))
    bb=s.BoundBox;d=dict(id=key,label=master.Label,bounds_mm=[bb.XLength,bb.YLength,bb.ZLength],sketches=sketches,hole_groups=hole_groups,feature_count=len(master.Group),mass_kg=spec[key]['mass_kg']);partdata.append(d)
    # Actual projected edges from BRep, each view explicitly scaled.
    views=[]
    for label,axis,angle in [('Draufsicht',V(1,0,0),0),('Vorderansicht',V(1,0,0),90),('Seitenansicht',V(0,1,0),90)]:
        copy=s.copy();copy.rotate(V(),axis,angle);b=copy.BoundBox;max_scale=min(112/max(b.XLength,1),135/max(b.YLength,1));scale=next((v for v in [2,1,.5,.2,.1] if v<=max_scale),.1)
        proj=TechDraw.projectToSVG(copy,V(0,0,1)).replace('stroke-width="1.0"','stroke-width="0.25"');views.append((label,b,scale,proj))
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297"><style>text{font-family:DejaVu Sans,sans-serif;fill:#17384b}.d{font-size:3.2px}.n{font-size:3px}.l{stroke:#416275;stroke-width:.2;fill:none}</style><rect x="7" y="7" width="406" height="283" fill="white" stroke="#17384b" stroke-width=".3"/>',f'<text x="15" y="18" font-size="6">{html.escape(key+" · "+master.Label)}</text><text x="15" y="26" font-size="3.8">D01 · Bauteilprüfblatt · Maße in mm · keine Fertigungsfreigabe</text>']
    for i,(label,b,scale,proj) in enumerate(views):
        x=18+i*132;y=45;w=b.XLength*scale;h=b.YLength*scale;tx=x-b.XMin*scale;ty=y+b.YMax*scale
        svg.extend([f'<text x="{x}" y="38" font-size="3.8">{label} · Skalierung {scale:g}</text>',f'<g transform="translate({tx},{ty}) scale({scale})">{proj}</g>',f'<path class="l" d="M {x} {y+h+3} v 6 M {x+w} {y+h+3} v 6 M {x} {y+h+7} H {x+w}"/>',f'<text class="d" x="{x+w/2}" y="{y+h+12}" text-anchor="middle">{b.XLength:.3f}</text>'])
    notes=[f'Werkstoff: {spec[key]["material"]}; EN10204-3.1 erforderlich.',f'CAD-Masse: {spec[key]["mass_kg"]:.4f} kg bei angenommener Dichte 2700 kg/m³.',f'Native Historie: {len(master.Group)} Features; {sum(p["fully_constrained"] for p in sketches)}/{len(sketches)} Skizzen vollständig festgelegt.','Entgraten 0.2–0.5 mm; Ra3.2, Kontaktflächen Ra1.6 als Vorschlag; Freigabe offen.']
    if key=='QD_E01':notes.append('Einpassmaß 43.97 ±0.01; Wurzelinnenweite 44.00–44.02 auf L135 prüfen; Flächenspalt max0.03.')
    if key=='QD_M01':notes.append('IF90 ist ein Projekteigenes Lochbild; OEM-Motoradapter und Freiräume sind noch nicht bestätigt.')
    for j,n in enumerate(notes):svg.append(f'<text class="n" x="15" y="{211+j*5}">{html.escape(n)}</text>')
    y=246
    for group in hole_groups[:6]:
        tag=f'{len(group["holes"])}× '+(str(group['thread'])+'–'+str(group['thread_class']) if group['thread'] else 'Ø'+str(round(group['holes'][0]['profile_diameter_mm'],3)))+f' · Tiefe {group["depth_mm"]:g}';svg.append(f'<text class="n" x="15" y="{y}">{html.escape(tag+" / "+group["feature"])}</text>');y+=5
    svg.append('<text class="n" x="15" y="285">Vollständige Bohrungskoordinaten und Gewindeattribute: Bauteilpruefdaten.json / native Skizzen.</text></svg>');(O/'Einzelteile'/(key+'_Pruefblatt.svg')).write_text(''.join(svg))
    print('Abgeleitet',key,'faces',len(f),flush=True)
(O/'Bauteilpruefdaten.json').write_text(json.dumps(partdata,indent=2,ensure_ascii=False));payload=dict(scope='Actual native CAD surfaces; only modeled mechanical module, no OEM replacement bodies',meshes=meshes,instances=bom,report=json.loads((O/'Pruefung.json').read_text()));(O/'mesh.js').write_text('globalThis.QD_MODEL='+json.dumps(payload,separators=(',',':'),ensure_ascii=False)+';\n');(O/'Renderdaten.json').write_text(json.dumps(payload,separators=(',',':'),ensure_ascii=False))
print('Ableitungen abgeschlossen',flush=True)
