# Rahmen aus CBU20171005TG

Übernommene Nutzerangaben: High Performance Rundrohr20×17×1000mm,45,02€ inklusive MwSt., Prepreg-Carbon/Epoxid,0°/90°-Kernlagen, PU-Außenbeschichtung, Außendurchmessertoleranz±0,2mm. Innendurchmessertoleranz, Laminatkennwerte und erlaubte Klemmpressung fehlen. Es werden keine E-Module oder Festigkeiten aus der Produktbezeichnung erfunden.

## Geometrie und Lastpfad

Lange Aluminiumquerträger werden durch schräge CFK-Streben ersetzt. Vier Streben je Motor verbinden die verschraubte Motorplatte mit dem Außenrahmen. Drei polygonale Rahmen liegen im Mittelraum sowie axial außerhalb der Rotoren; vertikale CFK-Rohre verbinden ihre Knoten. Weitere Streben stützen die kurze metallische Mittelbrücke ab. Die polygonalen Seiten bestehen aus geraden Zuschnitten; ein Rundrohr wird nicht in einen Ring gebogen.

Die drei festen Rollen je Rotor bleiben bestehen. Ihre Gabeln werden mit zweigeteilten Sätteln an durchgehenden vertikalen Rahmenrohren befestigt. Die Sättel besitzen separate Anschlussgewinde und benötigen keine Bohrung im CFK-Rohr. Der Rotor hat weiterhin8 Blätter je Ebene,1500mm nominalen Durchmesser und240mm Ebenenabstand, solange die entsprechenden Parameter nicht verändert werden.

Die Hauptrohre tragen über geteilte Sockelklemmen in metallische Mehrportknoten ein. Die Knoten sind als einzelne CNC-Körper mit Anschlussachsen und Gewindekernbohrungen modelliert. Klemmen sind in zwei tatsächlich getrennte Hälften aufgeteilt. M4-Flanschbohrungen sowie M4-Queranzug sind geometrisch getrennt; die Guide-Sättel besitzen M5-Klemmanschlüsse und frontseitige M6-Anschlüsse. Die Schrauben selbst sind noch nicht vollständig modelliert und nicht zur Bestellung freigegeben.

Die Knoten sind ein vorläufiger, geometrisch durchgearbeiteter Anschlussentwurf. Ihre Wandstärken, Klemmkräfte, Schraubenlängen und Festigkeit sind nicht abschließend bemessen. Werkstoffannahme der Knoten: EN AW-7075 T6. Kein Kleben oder Schweißen am CFK-Rohr wird vorausgesetzt. Lokale Aluminiumbrücken benötigen weiterhin einen eigenen Fügenachweis.

## Außendurchmesser und Klemmung

Nominal beträgt die Wanddicke1,5mm. Das tatsächliche Außenmaß wird als `cfk_actual_od` im Bereich19,8..20,2mm erfasst. Der Klemmbohrungsdurchmesser ist zunächst20,6mm; daraus ergibt sich eine radiale Isolierlage von0,2..0,4mm. Sie wird auf das gemessene Rohr zugeschnitten. Als Material ist GFK-/Isolierfilm vorgesehen, die genaue Paarung jedoch noch nicht ausgewählt.

Die Zwischenlage trennt CFK elektrisch vom Aluminium. Sie ersetzt keine Ermittlung der zulässigen Flächenpressung, Reibung, Kriechneigung und Schlupfsicherheit. Insbesondere ist die PU-Beschichtung noch keine qualifizierte Klemmoberfläche. Keine Querbohrungen und keine Metallgewinde direkt im1,5mm-CFK-Laminat vorsehen.

Die Rohrkontur im CAD verwendet den eingegebenen Ist-OD und nominal17mm innen. Eine Aussage über die reale Innenwandtoleranz oder tatsächliche Laminateigenschaften folgt daraus nicht.

## Zuschnitt und Bestellung

`CFK_Zuschnitt.csv` ordnet jedes Rohr einem1000mm-Rohling und seinen beiden Knoten zu. Eingriffslänge in die Sockelklemme ist derzeit30mm je Ende. Sägefuge2mm und Endbeschnitt5mm je Rohlingende sind als änderbare Annahmen erfasst. Der Endbeschnitt umfasst dabei den Bereich für den jeweiligen Absetzschnitt. Die Planung rundet Schnittlängen konservativ auf0,1mm auf; Fertigungstoleranzen sind separat festzulegen.

Die Packung verwendet First-Fit-Decreasing. Sie ist nachvollziehbar und innerhalb der Rohlinglänge, aber nicht als global minimaler Materialbedarf bewiesen. Der Preis in `CFK_Beschaffung.json` gilt nur für die CFK-Rohlinge: ohne Knoten, Klemmen, Schrauben, Zwischenlagen, Bearbeitung und Versand. Der Artikelpreis stammt aus der Nutzerangabe, nicht aus einem aktuellen Warenkorb.

## Was geprüft wird

Parameterbereiche, notwendige Eingriffslängen, freie Abstände zwischen Klemmen, Portwinkel, gültige Einzelkörper, Zuschnittlängen und exakte BRep-Überschneidungen im neutralen Aufbau werden geprüft. Die gespeicherten Anschlussachsen stehen zusätzlich in `CFK_Knotenanschluesse.json`.

150kg Gesamtmasse und850min⁻¹ sind Nutzer-Auslegungswerte; Lastfaktor2 bleibt eine vorläufige Rechenannahme. Eine Überdrehzahl wurde noch nicht festgelegt. Es fehlen vor allem orthotrope Steifigkeits-/Festigkeitsdaten, Knick-/Biegungs-/Torsionsnachweise, Knotennachweise, Klemmpressung, Vorspannung und das vollständige Lastkollektiv. Der Rahmen ist deshalb ein CAD-Fertigungsentwurf, keine Fertigungs- oder Belastungsfreigabe. Akku wird vorerst nicht als Auslegungsgrenze behandelt.
