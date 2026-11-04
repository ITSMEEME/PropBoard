"""Create an evidence-based mechanical detail report and merge projected sheets."""
from pathlib import Path
import json,collections
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFontFamily('DejaVu',normal='DejaVu',bold='DejaVu-Bold',italic='DejaVu',boldItalic='DejaVu-Bold')
from pypdf import PdfReader,PdfWriter
H=Path(__file__).resolve().parent;O=H/'Ausgabe'
def read(n):return json.loads((O/n).read_text())
r=read('Pruefung.json');b=read('Instanzen.json');s=read('Bauteile.json');t=read('Tragwerk_Lastscreen.json');a=read('Antriebsanforderungen.json');c=read('Kollisionen.json');m=read('Montage_Pruefung.json');p=read('Bauteilpruefdaten.json')
styles=getSampleStyleSheet()
for style in styles.byName.values():style.fontName='DejaVu-Bold' if style.name.startswith('Heading') or style.name=='Title' else 'DejaVu'
styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
story=[]
def para(x,style='BodyText'):story.append(Paragraph(x,styles[style]));story.append(Spacer(1,6))
def title(x):para(x,'Heading1')
def table(rows,widths):
 z=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT');z.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dce8ef')),('TEXTCOLOR',(0,0),(-1,-1),colors.HexColor('#16394f')),('FONTNAME',(0,0),(-1,-1),'DejaVu'),('FONTSIZE',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#16394f')),('VALIGN',(0,0),(-1,-1),'TOP')]));story.append(z)
def page():story.append(PageBreak())
title('Quad R380 D01');para('Mechanische Detailkonstruktion und geometrische Prüfungen','Heading2')
para('Dieser Stand liefert ein detailliertes Tragwerksmodul mit Deck. Er schließt den Gesamt-Quad noch nicht konstruktiv und ist keine Produktions-, Fertigungs- oder Flugfreigabe. OEM-Baugruppen fehlen, solange ihre belastbaren Unterlagen nicht vorliegen.')
if (H/'Tragwerk_Ansicht.png').exists():story.append(Image(str(H/'Tragwerk_Ansicht.png'),width=480,height=320))
table([['Merkmal','Ergebnis'],['Physische Instanzen / Teiletypen',f'{len(b)} / {len(s)}'],['Native PartDesign-Typen',str(len(p))],['Modellierte Tragwerksmasse',f'{r["mass_modeled_kg"]:.3f} kg'],['Rahmen-Bauraum ohne Rotoren','1008,49 x 1008,49 x 274,48 mm'],['Motorachsen / untersuchter Rotorradius','x/y = +/-425 mm / R = 380 mm']], [230,250])
page();title('1. Konstruktion und Schnittstellen')
para('Die Zentralplatten sind 380 x 380 x 8 mm groß. Vier Ausleger aus 50 x 50 x 3 mm Aluminiumprofil verbinden sie mit den Endträgern. Die Wurzelkanäle laufen offen bis zum Plattenrand. Eingepasste Druckstücke stützen die dünnen Rohrwände gegen Klemmkräfte ab; seitliche M5-Schrauben sichern deren Lage.')
para('Die Druckstücke sind 135 mm lang. Innenflächen der Rohre sind über diese Länge auf 44,00 bis 44,02 mm zu bearbeiten und zu messen; Druckstücke werden nominal 43,97 mm breit ausgeführt. Ein maximaler Flächenspalt von 0,03 mm ist separat durch Paarung und Messung sicherzustellen. Die Einzelmaßtoleranzen allein garantieren diesen Spalt bei exzentrischer Lage nicht.')
para('Vier Stützen stehen bei x = +/-85 mm und y = +/-70 mm. Sie verbinden den Zentralrahmen mit zwei Deckrohren 40 x 30 x 3 mm. Vier eingeschobene Mutternkassetten halten die oberen Stützenschrauben. Angefasste Kassettenunterkanten berücksichtigen die inneren Profilradien. Druckhülsen verhindern das Zusammendrücken der Deckrohre durch die Deckschrauben.')
para('Die Endträger enthalten acht M6-Gewinde auf dem projekteigenen Anschlusskreis IF90. Ein passender OEM-Motor ist damit noch nicht bestätigt. Motoradapter, Welle, Nabe und Rotoranschluss müssen nach der Komponentenauswahl separat konstruiert werden.')
para('Die zwölf Eigenbauteiltypen besitzen editierbare PartDesign-Historien. Normschrauben, Muttern und Scheiben stammen aus der gepinnten FreeCAD-Fasteners-Geometrie; Schrauben und Muttern besitzen geometrisch modellierte Helices. Nominalgeometrie belegt keine Lieferqualität oder Werkstoffklasse.')
para('Gewählte Normteilanforderungen: ISO4762 Schrauben Klasse 10.9; ISO7719 Ganzmetall-Sicherungsmuttern Klasse 10; ISO7089 Scheiben 300HV. Die Lieferantenauswahl und Zertifikate sind noch offen. Aluminium ist als EN AW-6082 T6 modelliert; Dichte 2700 kg/m³ und Materialkennwerte sind Rechenannahmen.')
page();title('2. Geometrie- und Montageprüfungen')
table([['Prüfung','Ergebnis / Geltungsbereich'],['Körpergeometrie',f'{len(b)} gültige platzierte Instanzen'],['Gewindepaarungen','94 nominale Schrauben-/Mutter- bzw. Sacklochpaarungen'],['Kollisionsprüfung',f'{c["candidate_pairs"]} Kandidatenpaare; 0 Überschneidungen >0,1 mm³'],['Werkzeugzugänge',f'{len(m["geometric_access"])} gerade Zugänge, montageabhängig'],['Kassetteneinbau','4 Einschubwege durch gleichförmige Rohrquerschnitte']], [165,315])
para('Die Kollisionsprüfung verwendet echte BRep-Körper und prüft alle über Begrenzungsboxen vorselektierten Paarungen. Keine Teilefamilie ist pauschal ausgeschlossen. Wiederholte nominal identische Gewindepaarungen werden über identische Geometrie und relative Lage wiederverwendet. Gewindephasen sind an die jeweiligen Muttern bzw. Innengewinde angepasst. Das ist eine nominale Geometrieprüfung ohne Toleranz-, Kontakt- oder Vorspannungssimulation.')
para('Der Werkzeugvorcheck verwendet einen Zylinder mit Schlüsselumkreis plus 0,6 mm Radiuszugabe und 35 mm gerader Anfahrstrecke ab Schraubenkopf. Er prüft ausdrücklich benannte Montagestufen, keine beliebige spätere Wartungszugänglichkeit. Werkzeuggriffe, Handhabung, Gegenhalten und OEM-Werkzeuggeometrien sind nicht vollständig geprüft.')
para('Montagefolge: (1) Druckstücke paaren, einschieben und sichern; danach Wurzelklemmung schließen. (2) Endträger ohne Antrieb montieren. (3) Kassetten mit vier Muttern, Deckel und M3-Schrauben außerhalb der Deckrohre vormontieren; links/rechts vom jeweiligen offenen Rohrende einschieben. (4) Stützenfüße und -köpfe verschrauben. (5) Deckhülsen und Deck montieren. Die Kassetten müssen vor querenden Deck- und Stützenschrauben eingebracht werden.')
para('Unterlagen: Ausgabe/Kollisionen.json, Gewindepruefung.json, Montage_Pruefung.json und Schraubstellen.csv. Die nativen Schrauben enthalten Verbundpartner, Montagestufe und vorläufiges Vorspannziel.')
page();title('3. Statischer Vorcheck und Grenzen')
arm=t['arm'];joint=t['root_joint']
table([['Annahme / Ergebnis','Wert'],['Gesamtmasse / Lastfaktor','200 kg / 2'],['Kraft je Ausleger / freie Länge',f'{arm["force_N"]:.0f} N / {arm["unsupported_length_m"]*1000:.2f} mm'],['CAD-Querschnitt / Flächenträgheit',f'{arm["area_mm2"]:.2f} mm² / {arm["exact_section_I_mm4"]:.0f} mm4'],['Wurzelmoment',f'{arm["root_moment_Nm"]:.2f} Nm'],['Nominale Biegespannung / Verformung',f'{arm["nominal_bending_stress_MPa"]:.2f} MPa / {arm["tip_deflection_mm"]:.3f} mm'],['Angenommenes E / Rp0,2','70 GPa / 250 MPa']], [275,205])
para('Ein linearer Kragträgeransatz mit gleichmäßiger Lastverteilung und dem tatsächlichen CAD-Querschnitt ergibt die Werte oben. Der Quotient aus angenommener Streckgrenze und nominaler Spannung beträgt 4,41. Dies ist kein nachgewiesener Sicherheitsfaktor für das Gesamtfahrzeug: Kerben, Kontakt, lokale Plattenbiegung, Lastumlagerung, Ermüdung und dynamische Anregung fehlen.')
para('Wurzelverbindung: vier M6-Schrauben, zwei Reihen im Abstand 60 mm. Vorläufiges Vorspannziel je Schraube 8 kN; rechnerische maximale Zugkraft 11,77 kN gegenüber einem angenommenen Prüfkraftbezug von 16,68 kN. Der Kraftansatz bildet weder die tatsächliche Schrauben-/Bauteilsteifigkeit noch Streuungen vollständig ab. VDI2230-Nachweis und Versuche stehen aus.')
para('Eine frei überbrückende Rohrwand ergäbe im vereinfachten Streifenmodell rund 725 MPa; deshalb sind eingepasste Druckstücke zwingend. Der Lastpfad muss durch Kontaktrechnung und Versuche bestätigt werden. Lose Druckstücke sind unzulässig.')
para('Ein angenommener Drehmomentfaktor K = 0,18 bis 0,24 ergibt für die Wurzelschrauben 8,64 bis 11,52 Nm. Dieser Bereich ist kein freigegebenes Anzugsmoment: Reibwerte, Sicherungsmuttern-Reibmoment, Oberflächen, Wiederverwendung und Anzugstrategie sind ungeklärt.')
page();title('4. Antriebssuche und offene Fahrzeugbilanz')
para('Das bisherige angenommene Dreiblattmodell liefert nur einen Suchkorridor für Herstellerkennfelder. Es verwendet keine validierte reale Rotorpolare. R = 380 mm ist beibehalten; Blätter und Motoren sind noch nicht ausgewählt.')
table([['Masse kg','U/min','Nm/Motor','kW Welle/Motor +30%','kW elektrisch ges.'],*[ [str(x['mass_case_kg']),f'{x["rpm"]:.0f}',f'{x["torque_each_Nm"]:.2f}',f'{x["required_continuous_shaft_plus30pct_kW"]:.2f}',f'{x["electric_total_at_eta082_kW"]:.2f}'] for x in a]], [65,65,80,145,125])
para('Die elektrische Leistung nimmt pauschal 82 % Gesamtwirkungsgrad an. Spannung, Zellenzahl, Packmasse, Flugzeit und Thermik sind nicht geschlossen. Der neue Tragwerksumfang darf nicht ungeprüft mit früheren Konzeptmassen vermischt werden. Kein Lastfall oben ist bereits die bestätigte Gesamtmasse des neuen Fahrzeugs.')
para('Offene Baugruppen: Motoren, bestätigte Motoradapter, Rotoren und Blattanschlüsse, Regler/Elektronik, Batterie/BMS/Kontaktoren/Sicherungen, Kabelbaum, Schutzgitter/Rückhaltung und Landegestell. Diese Teile werden erst anhand belegter Abmessungen und Betriebsdaten modelliert.')
para('Datenbeschaffung: BESCHAFFUNGSAUFTRAG.md enthält die gezielten Domains und Dokumentanforderungen. Herstellerzugriff war mit HTTP CONNECT 403 gesperrt. Der gespeicherte Netzwerkentwurf muss in den Umgebungseinstellungen geprüft und veröffentlicht werden. Weitere Download-Hosts erst anhand konkreter OEM-Verweise ergänzen.')
para('Weitere Freigabeschritte: reale Kennfelder auswählen; Schnittstellen und Kühlsysteme schließen; komplette Masse/Energie neu rechnen; tolerierte Zeichnungen und Lieferzertifikate erstellen; Schraubverbindungen, Kontakt und Ermüdung nachweisen; dynamische und Ausfalllasten prüfen; Baugruppenversuche durchführen. Die 30-%-Leistungsreserve ersetzt keinen dieser Nachweise.')
page();title('5. Stückliste des modellierten Moduls')
counts=collections.Counter(x['id'] for x in b)
rows=[['Teile-ID','Anz.','Bezeichnung','Summe kg']]
for k,n in counts.items():rows.append([k,str(n),Paragraph(s[k]['label'],styles['BodyText']),f'{s[k]["mass_kg"]*n:.3f}'])
table(rows,[105,32,283,60]);para(f'Gesamt: {len(b)} Instanzen; {r["mass_modeled_kg"]:.3f} kg. Massen aus nominalem CAD-Volumen und angenommener Dichte; keine Wägung.')
page();title('6. Dateien, Quellen und Reproduktion')
para('Native Baugruppe: Ausgabe/QuadR380_D01_Mechanik.FCStd. Einzelteile: Ausgabe/Einzelteile/*.FCStd und *.step. Die nativen Einzelteile erhalten ihre editierbare Feature-Historie. STEP ist ein Austauschformat ohne diese Historie. Bauteilpruefblaetter.pdf enthält zwölf A3-Projektionen aus echten BRep-Kanten; vollständige Bohrungskoordinaten stehen in Bauteilpruefdaten.json und den nativen Skizzen.')
para('Die Prüfblätter besitzen Ansichtsmaßstäbe, Außenmaße und Bohrungs-/Gewindeattribute. Sie sind keine vollständigen Fertigungszeichnungen mit allen Passungen, Bezugsflächen und geometrischen Toleranzen. Ihre Kennzeichnung lautet deshalb ausdrücklich Bauteilprüfblatt, keine Fertigungsfreigabe.')
para('Normgeometrien: github.com/shaise/FreeCAD_FastenersWB, Commit fddd07af422b7d3a69098b32333711c5eeae184c. Quellenmanifest, Maßtabellen und Lizenz sind unter Quellen/Normteile abgelegt. Werkstoff-/Festigkeitsanforderungen sind Projektvorgaben und keine Aussagen dieses CAD-Lieferanten.')
para('Reproduktionsfolge und Abhängigkeiten siehe README.md. Nach Änderungen an Geometrie, Lage oder Gewindephasen sind die betroffenen Prüfungen neu auszuführen. Alte Prüfergebnisse dürfen nicht auf veränderte Modelle übertragen werden.')
para('SHA256 der geprüften nativen Baugruppe: '+r['native_sha256'])
para('Diese Dokumentation beschreibt den vorliegenden mechanischen Detailstand. Alle Prüfungen gelten für nominal starre Geometrie bzw. die ausdrücklich genannten Modellannahmen. Eine vollständige Produktionsqualität des Gesamt-Quad ist damit noch nicht erreicht.')
def foot(canvas,doc):canvas.setFont('DejaVu',8);canvas.setFillColor(colors.HexColor('#456273'));canvas.drawString(40,25,'Quad R380 D01 | mechanischer Detailstand | keine Produktionsfreigabe');canvas.drawRightString(555,25,str(doc.page))
SimpleDocTemplate(str(H/'Detailbericht.pdf'),pagesize=(595.28,841.89),leftMargin=40,rightMargin=40,topMargin=35,bottomMargin=43).build(story,onFirstPage=foot,onLaterPages=foot)
w=PdfWriter()
for row in p:
 f=O/'Einzelteile'/(row['id']+'_Pruefblatt.pdf');reader=PdfReader(str(f));assert len(reader.pages)==1,(f,len(reader.pages));w.add_page(reader.pages[0])
with (H/'Bauteilpruefblaetter.pdf').open('wb') as f:w.write(f)
print('Report and',len(p),'part sheets complete')
