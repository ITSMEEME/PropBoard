#!/usr/bin/env python3
"""Review report from actual CAD verification, user specifications and calculated polars."""
import json,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
H=Path(__file__).resolve().parent
load=lambda p:json.loads((H/p).read_text())
V=load('bewegung/Ausgabe/Validierung_M01.json');L=load('messdaten/Servolasten_Savox.json');P=load('aerodynamik/Ausgabe/Polaren.json');B=load('aerodynamik/Ausgabe/Betriebspunkte_Savox.json');F=load('simulation/Ergebnisse/Testbericht.json')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.grid':True,'grid.alpha':.25})
fig,axs=plt.subplots(1,3,figsize=(12,3.6))
for n in (4,9):
    t=next(t for t in P['tables'] if t['re']==100000 and t['ncrit']==n);data={r['alpha']:r for r in t['rows']};x=list(range(-6,17))
    for ax,key in zip(axs,('cl','cd','cm')):ax.plot(x,[data[a][key] if a in data else np.nan for a in x],'.-',label=f'Ncrit {n}');ax.set_xlabel('α [°]');ax.set_ylabel(key.upper());ax.legend()
fig.suptitle('Tatsächliches CAD-Profil · XFOIL Re=100.000 · berechnet, nicht gemessen');fig.tight_layout();fig.savefig(H/'aerodynamik/Ausgabe/CAD_Polaren.png',dpi=160);plt.close(fig)
fig,ax=plt.subplots(figsize=(8,4))
for name in ('SIMPLIFIED_HISTORICAL','CAD_XFOIL_N4','CAD_XFOIL_N9'):
    rows=[r for r in L['results'] if r['aero_model']==name and r['stage']=='tw2'];ax.plot([r['mu_assumed'] for r in rows],[r['required_kgcm_with_factor2'] for r in rows],'.-',label=name)
ax.axhline(20,color='black',linestyle='--',label='Angabe 7,4 V: 20 kg·cm');ax.axhline(15,color='grey',linestyle=':',label='Angabe 6 V: 15 kg·cm');ax.set_xlabel('angenommener effektiver Reibwert µ');ax.set_ylabel('Moment je Servo mit Faktor 2 [kg·cm]');ax.set_title('Lastscreen TW2 · 69-g-Servos · keine Dauerlastfreigabe');ax.legend(fontsize=8);fig.tight_layout();fig.savefig(H/'messdaten/Reibung_Lastscreen.png',dpi=160);plt.close(fig)
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'));styles=getSampleStyleSheet()
for k in ('BodyText','Heading1','Heading2','Title'):styles[k].fontName='DejaVu'
styles['BodyText'].fontSize=9;styles['BodyText'].leading=13;story=[]
def para(t,kind='BodyText'):story.append(Paragraph(t,styles[kind]));story.append(Spacer(1,7))
def table(rows,widths):
    rows=[[Paragraph(str(x),styles['BodyText']) for x in row] for row in rows];t=Table(rows,colWidths=widths,repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dbe9f0')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]));story.append(t);story.append(Spacer(1,9))
para('Cohexial Study · M01','Title');para('Bewegung, Servodaten, Reibung und Aerodynamik','Heading1')
para('Native FreeCAD-Bewegungsbaugruppe und nachvollziehbare Berechnungen. Hardwaremessungen wurden nicht durchgeführt. Lager-/Motorinneres ist schematisch. Reale Servohalter, Spline-/Kugelaufnahmen, Axialsicherungen und Festigkeitsfreigaben bleiben offen.')
para('Übernommene Daten aus deinen Bildern und der Tabelle','Heading2')
table([['Eigenschaft','Savöx SB-2271SG(+)'],['Spannung','6,0–7,4 V; 8,4 V durch diese Angabe nicht gedeckt'],['Masse / Motor / Getriebe','69 g / Brushless / Stahl'],['Momentangabe','15 kg·cm bei 6 V; 20 kg·cm ≈ 1,961 Nm bei 7,4 V'],['Stellzeitangabe','0,08 / 0,06 s pro 60° bei 6 / 7,4 V; Lastbedingungen nicht genannt'],['Gehäuse / Abtrieb','40,3×20,2×38,7 mm, 25T; Verzahnungsdurchmesser/-form fehlen'],['Befestigung aus Zeichnung','54 mm über Laschen; 48×10 mm Raster; Achse 10,3 mm ab Gehäuseende']], [145,340])
para('Der gezeichnete Savöx-Typ ist SB-2271SG(+), nicht der zuvor genannte SB-2270SG. Die Tabellenzuordnung erfolgt anhand der mitgelieferten Zeichnung; Plus-Suffix am Artikel bestätigen. Keine unabhängig abgerufene Herstellerpublikation. „Dynamic Torque“ ist kein nachgewiesenes Stall-/Dauermoment. Stromaufnahme, PWM-Pulsbereich/Frame-Rate und Signalkompatibilität fehlen.')
para('KST X15-755X: nominales Gehäuse 35,5×15×31,6 mm, Gesamtmaß über Abtrieb 36,6 mm, 41,5×7,5 mm Befestigungsraster. Auf dem Bild steht 760 µs. Ohne passende Ansteuerungs- und Lastdaten bleibt er nur CAD-Vergleich; kein ungeprüftes 1500-µs-Setup verwenden.')
para(f"Massenbudget mit sechs Savöx-Servos: {B['mass_kg']:.6f} kg. Neue Halter und BEC-Masse fehlen weiterhin. Die Servo-Trägheiten stammen aus nominalen CAD-Hüllen bei angenommener homogener interner Dichte; sonstiges H01-Budget bleibt erhalten.")
story.append(PageBreak());para('Native Bewegung und Prüfung','Heading1')
story.append(Image(str(H/'bewegung/Ausgabe/Vorschau_M01.png'),width=485,height=261))
para('348 sichtbare Körper: u. a. 16 Flügel/Pitchhebel/Blattgestänge, sechs Servo-Hörner/Abtriebe/Gestänge, zwei kippende und zwei rotierende Taumelscheibenringe, zwei Ritzel/Motorwellen/Glocken und sechs Lager mit getrennten Laufringen, Käfigen und 120 schematischen Kugeln. Die internen Servo-Getriebestufen sind mangels Herstellerzeichnung nicht modelliert.')
para('Feste Servo-Gestängelängen bestimmen die Taumelscheibenlage; feste 15-mm-Blattgestänge bestimmen die tatsächlichen Blattwinkel. Die native Baugruppe lässt sich mit dem Makro per Zeitleiste bewegen. Flugkanäle geben die separat berechnete 69-g-Savöx-Flugdynamik wieder; FreeCAD löst dabei Kinematik, keine neue Kontakt-/Flugkraftdynamik.')
para(f"Prüfung: {V['states_per_variant']} Zustände je Gehäusevariante, zwei Varianten. Maximaler Gestängeschlussfehler {V['max_fixed_link_error_mm']:.2g} mm. {V['pair_checks']} gezielte BRep-Schnittstellenprüfungen, davon {V['gear_checks']} Verzahnungsprüfungen; {len(V['collisions'])} Überschneidungen über der dokumentierten Schwelle. Native Wiederöffnung bestanden. Kein vollständiger All-Pairs-/Festigkeitsnachweis.")
para('Die FreeCAD-GUI-Steuerung wurde im tatsächlichen 1.0.2-Prozess mit Qt-Offscreen auf Zeitleiste, Savöx-Wiedergabe und KST-Beschränkung geprüft. Der Offscreen-OpenGL-Viewport war nicht renderfähig; diese Vorschau stammt separat aus der triangulierten nativen BRep-Geometrie.')
para('Öffnen: bewegung/Bewegung_oeffnen.FCMacro. Das Makro lädt das native FCStd und die zugehörigen Python-Module. Neutralstellung zusätzlich als STEP. Laschendicke, Savöx-Bohrungsdurchmesser und Spline-Geometrie sind teilweise Darstellungsannahmen; die 8-mm-Hörner sind keine freigegebenen Kaufhorn-Schnittstellen.')
story.append(PageBreak());para('Berechnete Aerodynamik des CAD-Profils','Heading1')
para('Export aus dem echten Flügel-BRep: 121 Profilpunkte bei r=110 mm, 30 mm Sehne, 0,6 mm dicke Hinterkante (2 % Sehne). XFOIL 6.99: Re 20.000…180.000, α −6…16°, Ncrit 4/9, Mach 0,08. 317 von 322 Punkten konvergiert. Fehlende Punkte bleiben Lücken. Keine Messung von Druckrauheit, Transition oder dynamischem Stall; keine vollständige 3D-Koaxial-CFD.')
story.append(Image(str(H/'aerodynamik/Ausgabe/CAD_Polaren.png'),width=485,height=146))
rows=[['Polare','Schweben rpm','Busleistung*','TW2 rpm','TW2 Ersatzanteil']]
for s in B['scenarios']:rows.append([s['name'],f"{s['hover']['rpm']:.0f}",f"{s['hover']['bus_power_W']:.0f} W",f"{s['tw2']['rpm']:.0f}",f"{100*s['tw2']['final_section_fallback_fraction']:.2f} %"])
table(rows,[142,79,79,73,112])
para('*Unvalidiertes Motor-/Akku-Ersatzmodell, pauschale Nebenverbraucher; tatsächliche Servo-/BEC-Ströme nicht bestimmt. Die finalen stationären Schwebepunkt-Abschnitte liegen vollständig in den jeweiligen konvergierten Tabellen. Beim Ncrit-4-TW2-Punkt benötigen 23,75 % der finalen Abschnitte die bisherige Ersatzpolare. Internen numerischen Suchschritten können weitere Ersatzwerte zugrunde liegen.')
para('Der optionale XFOIL-Flugfall verwendet uniformen dynamischen Zustrom und benötigt rund 20 % Ersatzmodell-Auswertungen. Der Anteil wird protokolliert. Der Vergleich ist eine gekennzeichnete Hybridrechnung; die stationäre radiale BEMT- und die dynamische uniforme Inflow-Näherung sind unterschiedliche Modellordnungen. CM wird berechnet, aber noch nicht vollständig in zyklische Servo-Luftlasten übersetzt.')
para('Numerische Kontrolle: NACA-Referenz bei α=0 sowie Panelverfeinerung 160→240 am tatsächlichen Profil. CL-/CD-Ausgabe ist gerundet; diese Prüfungen belegen numerische Plausibilität, keine reale Genauigkeit. Solver-/Quell-/Profil-SHA256 und Rohlogs sind enthalten. Der Debian-Binärsolver wurde wegen SIGFPE am Referenzprofil durch einen geprüften lokalen Double-Precision-Releasebuild ersetzt.')
story.append(PageBreak());para('Reibung und erforderliche Servoreserve','Heading1')
story.append(Image(str(H/'messdaten/Reibung_Lastscreen.png'),width=475,height=238))
rows=[['µ angenommen','TW2-Bedarf je Servo mit Faktor 2','Quotient 20 kg·cm / Bedarf']]
for r in L['results']:
    if r['aero_model']=='SIMPLIFIED_HISTORICAL' and r['stage']=='tw2':rows.append([r['mu_assumed'],f"{r['required_kgcm_with_factor2']:.2f} kg·cm",f"{r['advertised_7_4V_ratio']:.2f}"])
table(rows,[93,240,152])
para('728 geschlossene Gestängezustände mit vollem Acht-Blatt-/Drei-Servo-Jacobian. Enthalten: Fliehkraft-Torsion, zyklische Pitch-Trägheit, Viertelsehnen-Luftlastarm und angenommene Nut-Gleitreibung. Ausgeschlossen: Losbrechen, Vorspannung, vollständige CM-/zyklische Luftlasten, Lagerreibung und Struktur-/Temperatureffekte. Die Momentangabe ist keine Dauerlast; deshalb sind die Quotienten keine bestätigten Sicherheitsreserven.')
para('Bei µ=0,2 liegt der Bedarf des vereinfachten Lastscreens mit 20,89 kg·cm knapp über der Angabe bei 7,4 V. Bei µ=0,1 beträgt er 12,97 kg·cm. Der reale µ-Wert wurde nicht ermittelt: Ohne Messungen am tatsächlichen Wurzel-/Nut-/Stiftpaar lässt er sich aus CAD oder Materialnamen nicht belastbar ableiten.')
para('Messvorlagen und Auswerter sind enthalten: Reibung aus Vorlast/Pitchgeschwindigkeit/Moment; effektive Servototzeit/Zeitkonstante aus Kommandos und extern gemessenem Winkel; lokale Aerokorrektur aus Schub und separat gemessenen Rotordrehmomenten. Leere Vorlagen werden zurückgewiesen. Synthetische Wiederherstellungstests sind ausdrücklich keine Messdaten. Gefittete Werte werden nicht automatisch als Flugfreigabe übernommen.')
para('Ergebnis: Die Bewegungsbaugruppe und die Kennwertrechnung sind prüfbar. Alle vier neuen Savöx-Flugvarianten bleiben im unvalidierten Modell stabil. Reale Flugfähigkeit, Strom-/BEC-Auslegung und Dauerlast hängen weiterhin von den genannten Messungen und den offenen mechanischen Schnittstellen ab.')
def footer(c,d):c.setFont('DejaVu',8);c.drawString(42,22,'M01 · Nutzerangaben + Berechnung · keine empirische Flugvalidierung');c.drawRightString(A4[0]-42,22,str(d.page))
SimpleDocTemplate(str(H/'Datenbericht_M01.pdf'),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=35,bottomMargin=38).build(story,onFirstPage=footer,onLaterPages=footer)
print('M01 data report generated')
