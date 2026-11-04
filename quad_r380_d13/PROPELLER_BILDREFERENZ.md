# Zweiblattpropeller aus den bereitgestellten Bildern

Die [Projektansicht](Projekt.html) enthält jetzt ausgeformte Zweiblattpropeller in zwei gespiegelten Drehrichtungen. Im nativen [FreeCAD-Modell](Ausgabe/Quad_Flachrippen_Mensch.FCStd) liegen zwanzig Propellervarianten und je vier größenabhängig geschaltete Einbauten. [STEP-Einzelteile](Ausgabe/Propeller_STEP/) sind für jede Größe und Drehrichtung vorhanden.

Mit **„Propeller einzeln“** wird der gewählte Propeller isoliert angezeigt. Die Größenwahl bleibt aktiv; **„Gesamtansicht“** führt zurück zum vollständigen Modell. Die Rotorstellung lässt sich separat verstellen. [42-Zoll-Detailbild](Ausgabe/Propeller_42_Detail.png), [CW-STEP](Ausgabe/Propeller_STEP/HEP_S_42_16_CW.step) und [CCW-STEP](Ausgabe/Propeller_STEP/HEP_S_42_16_CCW.step) zeigen den größten Aufbau.

Die drei Bilder liefern den charakteristischen Zweiblattumriss mit schmaler Mitte, breiterem innerem Blattbereich, auslaufender Blattspitze und geringer seitlicher Krümmung. Sie liefern **keine vollständige Maßzeichnung**. Die modellierten Volumenkörper sind eine Bildreferenz mit offengelegten Annahmen, keine bestätigten T-Motor-Fertigungsdaten.

## Größenanpassung

Es werden die zehn vorgegebenen Größen von HEP-S 18×6.7 bis 42×16 verwendet. Der jeweilige nominelle Außendurchmesser begrenzt die Geometrie durch einen exakten CAD-Zylinder. Blattlänge, Blattbreite und Rückpfeilung werden angepasst; die Nabenmaße bleiben als gemeinsame Projektschnittstelle konstant. Eine rein gleichförmige Skalierung würde sonst die Motor-Lochkreise mitverändern.

Die Blätter entstehen aus räumlich verwundenen Profilquerschnitten als geschlossene Loft-Volumenkörper. Beide Blätter und die mittlere Nabe bilden **einen zusammenhängenden Körper**. Die zentrale Bohrung und vier Befestigungsbohrungen sind reale Durchgänge. Die schwarze Gewebedarstellung in der Ansicht ist eine Oberflächendarstellung und enthält keine Aussage zum Laminataufbau.

Für den Blattbereich wird der geometrische Helixwinkel aus der gewählten Steigung P und dem Radius r angenähert: β = atan(P / (2πr)). Am inneren Übergang wird die Verwindung zwischen 75 und 105 mm Radius weich eingeblendet. Die inneren Querschnitte bis 75 mm bleiben flach, damit das Blatt nicht in den 150-mm-Motorkörper hineinläuft. Ober- und Unterseite verwenden ein angenommenes NACA-artiges Profil mit bis zu 2,5 % Wölbung und von 18 auf 8 % abnehmender relativer Dicke. Diese Werte sind **nicht aus den Fotos messbar** und nicht als OEM-Profil zu verwenden.

## Gemeinsame Nabe – unbestätigte Projektmaße

| Merkmal | Modellannahme |
|---|---:|
| Nabenunterseite | z = 154 mm, bisherige Motor-Oberseite |
| Nabendicke | 9 mm |
| Elliptischer Nabenumriss | 140 × 44 mm |
| Zentralbohrung | Ø15 mm |
| Befestigung | 4 × Ø5,5 mm auf Ø30 mm, 45° versetzt |

Diese Schnittstelle ist eine Projektannahme passend zur bisherigen Motorreferenz. Das Foto allein bestätigt weder Lochkreis noch Bohrungsdurchmesser. Schraubenlänge, Gewindetiefe, Zentrierung, Vorspannung und zulässige Befestigung am MN1330 sind offen. Es werden deshalb keine vermeintlich freigegebenen Befestigungsschrauben ergänzt.

CW/CCW bezeichnet die Drehrichtung von oben auf den Rotor gesehen. Zwei Rotoren je Richtung sind eingebaut. Die Gegenrichtung ist eine geometrische Spiegelung mit gleichbleibender Wölbung nach oben. Daraus folgt keine Bestätigung der Drehrichtungsmarkierung eines konkreten Herstellerartikels.

## Umlauf- und Einbauprüfung

[Propeller-Prüfdaten](Ausgabe/Propeller_Pruefung.json) dokumentieren die gespeicherte native Geometrie. Ein innerer Zylinder bis 75 mm Radius oberhalb z = 154 mm und ein äußerer Ringraum von 75 mm bis zum jeweiligen Außenradius umfassen den Propeller über **jede Rotorstellung**. Der äußere Ringraum verwendet die konservativen axialen Grenzen des nativen Propellerkörpers. Die vollständige Aufnahme des Propellers in diese rotationssymmetrischen Räume wird durch eine native Volumendifferenz geprüft.

Diese Hüllräume werden an allen vier Motorachsen in allen 50 Größen-/Rohrkombinationen gegen die Montagepartner und die Größenfigur geprüft. Die Rotorabstände werden zusätzlich anhand der vollständigen Umlaufkreise geprüft. Der zugeschnittene NURBS-Körper kann einen konservativen CAD-Begrenzungskasten besitzen, der radial etwas über das nominelle Maß hinausweist; maßgeblich sind die geprüfte native Zylinderbegrenzung und die tatsächlichen Oberflächen, nicht dieser lose Begrenzungskasten.

Die Hüllprüfung betrifft **starre nominale Bildreferenzgeometrie**. Sie enthält keine Blattdurchbiegung, Fertigungstoleranzen, Flatter-, Festigkeits-, Drehzahl- oder Nabenfreigabe. Die [Antriebsanzeige](ANTRIEB_UND_KNOTEN.md) bleibt ein getrenntes Koeffizientenmodell. Das neue 3D-Blatt ist dadurch weder aerodynamisch validiert noch ein nachgewiesenes HEP-S-Kennfeld.

Die Propellermasse bleibt aus der Fahrzeug-Teilmasse ausgeschlossen: Ein gefüllter CAD-Körper ergibt ohne reale Schalen-, Kern- und Laminatdaten keine belastbare CFK-Propellermasse.
