# Tragfähigkeits-Nachweisversuch

Start: **Nachweisversuch.pdf** oder **Nachweisversuch.html**. Der Nachweis für 100 kg Person plus Ausrüstung wurde **nicht erbracht**. Das ist kein Beleg, dass die maximal mögliche Tragfähigkeit null sei oder jeder geänderte Entwurf unmöglich sei.

Enthalten sind eine bedingte Materialmassenrechnung aus realen CAD-Instanzvolumina, quasistationäre Auftriebsanforderungen, Umlenk-/Magnetkraftreferenzen, ein Aktuatorscheiben-Leistungsvergleich mit Akku-Massenrückkopplung, ein konkreter Einbaucheck des früher beschriebenen Akkupacks und ein Einzelbalken-Steifigkeitsscreening. Alle Polaren, Wirkungsgrade, Dichten, Batterieparameter und Lagerungsannahmen sind als Annahmen ausgewiesen. Keine neue realmaßstäbliche 3D-CFD und keine neuen Hardwaremessungen.

Besonders wichtig: Die 3,57 m² Vergleichsfläche sind **keine nachgewiesene wirksame Strahlfläche** des Umlaufs. Die damit errechnete Leistung ist keine strenge universelle Mindestleistung des tatsächlichen Antriebs. Die Akku-Rasterwerte sind keine verfügbare Produktauswahl oder technologischen Obergrenzen. Die Materialsumme ist kein bestätigtes Leergewicht und kein allgemeiner unterer Massenwert für einen später optimierten Entwurf.

Die Prüfung der 712 Instanzvolumina gegen die native CAD-Datei ist in `CAD_Volumenpruefung.json` dokumentiert. Sie bestätigt nur die Geometrieübernahme. Die zulässige Nutzlast bleibt in `Ergebnisse.json` ausdrücklich `null`.

Reproduktion im Repository-Verzeichnis:

```sh
/usr/bin/python3 tragfaehigkeit/cad_volumen_pruefen.py
python tragfaehigkeit/rechnen.py
python tragfaehigkeit/visualisieren.py
python tragfaehigkeit/bericht_erstellen.py
```

Die erste Zeile benötigt das FreeCAD-Python-Modul der Umgebung. Die analytische Rechnung benötigt nur Python-Standardbibliotheken; Grafiken benötigen NumPy/Matplotlib. PDF/HTML werden mit Pandoc und XeLaTeX erzeugt. Die benötigten Quellen sind im Archiv in ihren ursprünglichen Unterordnern enthalten.

CSV-Tabellen sind Rechenfälle, keine freigegebenen Kennwerte oder Bestellanforderungen. Die „0 kg“ in der Akku-Sensitivität bezeichnet ausschließlich eine untersuchte Ausrüstungsannahme beziehungsweise das bewusste Weglassen zusätzlicher unbekannter Systemmassen. Sie ist kein positiver Nutzlastnachweis.
