# Cohexial Study – R04-Taumelmodell 1:4

Das native FreeCAD-Modell enthält zwei gegenläufige Rotoren mit je acht pitchverstellbaren Flügeln und eigener Taumelscheibe. Maßstab 1:4, Flügelkreis Ø375 mm, Ebenenabstand 60 mm. **Entwurf; keine Fertigungs- oder Betriebsfreigabe.**

Der [Fertigungsordner](Fertigung/) enthält Einzelteilmodelle, STEP/STL, TechDraw-Zeichnungen und Nennmaßtabellen, Stücklisten und Prüfprotokolle. Einstieg: [Fertigungshinweise](Fertigung/Fertigungshinweise.md). Dort sind insbesondere noch fehlende Servobefestigungen, Kugelanschlüsse, Klemmungen und Passungen einzeln benannt.

- [Baugruppe FreeCAD](R04_Taumelmodell_1zu4.FCStd) / [STEP](R04_Taumelmodell_1zu4.step)
- [Zeichnungssatz PDF](Fertigung/Fertigungszeichnungen_F01.pdf)
- [Eigenfertigung / Zuschnitt](Fertigung/Fertigungsstueckliste.csv) / [Kaufteile](Fertigung/Kaufteilliste.csv)
- [Geometrie- und Austauschprüfung](Fertigung/Geometriepruefung.json)
- [Baugruppenprüfung](Pruefbericht.json)

`Fertigung_oeffnen.FCMacro` importiert die mitgelieferten Python-Features. Danach lassen sich die Einzelteile über ihre native FreeCAD-Tabelle **Parameter** ändern und neu berechnen. Dies ist ein skriptparametrischer Aufbau; die Baugruppe wird über `erstellen.py` aus `parameter.json` neu erzeugt. Die Einzelteilparameter ändern die Baugruppe nicht automatisch.

Die Erzeugung und Prüfung stehen in den Fertigungshinweisen. Verwendet wurde die offizielle FreeCAD-Version 1.0.2 mit geprüfter SHA-256-Prüfsumme. Die örtliche FreeCAD-1.0.0-Python-Bibliothek stürzte bei der Verbundkörpererzeugung ab.
