#!/usr/bin/env python3
"""Exhaustive manufacturing-completeness inventory of the actual P05 assembly.

A valid solid is necessary but never sufficient for manufacturing release.
Unknown part identifiers are errors, not automatically approved parts.
"""
import csv
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, os.environ.get('FREECAD_LIB', str(ROOT / '.cfd-tools/freecad/usr/lib')))
import FreeCAD as App
import Part

OUT = HERE / 'Ausgabe'
OUT.mkdir(exist_ok=True)
SOURCE = HERE.parent / 'fertigung_p05/Ausgabe/P05_Baugruppe_Motoranschluss_GESPERRT.FCStd'
# Every reason describes a specific remaining interface, rather than demanding
# internal production drawings of bought assemblies.
RULES = {
    'TM-FLUEGEL': ('Eigenfertigung', 'Konstruierter Festkoerper', 'Fluegelzapfen/Nut/Stiftsitz: Passungen, Verschleiss und tragfaehige Sicherung; Werkstoff-/Prozess- und Toleranzfestlegung.'),
    'TM-NABE': ('Eigenfertigung', 'Konstruierter Festkoerper', 'Zapfenlagerung und D2-Stiftsitze: Passungen und Sicherung; Lagersitz und axiale Lagerhaltung.'),
    'TM-PITCHHEBEL': ('Eigenfertigung', 'Unvollstaendiger Anschluss', 'Realer Kugelbolzenanschluss fehlt; Vierkantpassung und axiale Hebelsicherung fehlen.'),
    'TM-DECKEL-ZAHNKRANZ-130': ('Eigenfertigung', 'Konstruierter Festkoerper', 'Deckelbefestigung und Mitnehmerstift sichern; Verzahnungs-/Rundlauf- und Fertigungstoleranzen festlegen.'),
    'TM-TAUMEL-DREHRING': ('Eigenfertigung', 'Unvollstaendiger Anschluss', 'Reale Kugelbolzenanschluesse, Lagerpassung und axiale Lagerhaltung festlegen.'),
    'TM-TAUMEL-GLEITKUGEL': ('Eigenfertigung', 'Montage ungeklaert', 'Geschlossene Kugel-/Pfannenpaarung: Montagefolge bzw. Teilung mit Befestigung ausarbeiten; Gleitpassung/Oberflaeche festlegen.'),
    'TM-TAUMEL-INNENRING': ('Eigenfertigung', 'Unvollstaendiger Anschluss', 'Kugelbolzen-/Fuehrungsstiftbefestigung und Kugelmontage fehlen; Gleitpassung festlegen.'),
    'TM-HALTEPLATTE': ('Eigenfertigung', 'Unvollstaendiger Anschluss', 'Motorlochbild PCD16 bestaetigt; Kragen ohne fertige Klemmschraubverbindung; tangentiale Servohalter und deren Lastpfad fehlen.'),
    'TM-KLEMMRING': ('Eigenfertigung', 'Unvollstaendiger Anschluss', 'Klemmschraube und tragfaehige axiale Rotorsicherung fehlen.'),
    'TM-HUELSE-MITTE': ('Eigenfertigung', 'Konstruierter Festkoerper', 'Passung, axiale Festlegung und Montagebezuege festlegen.'),
    'RITZEL-M1-Z20': ('Eigenfertigung', 'P05 Gewinderitzelentwurf', 'M5x0.8-6H ist spezifiziert; Gewindeauslauf, Rundlauf/Zahnqualitaet, Anzug/Vorspannung und Losdrehsicherung nachweisen. Keine glatte Bohrung fertigen.'),
    'H01': ('Eigenfertigung', 'Konstruierter Festkoerper', 'Kappe/Rohr: axiale Sicherung und Sitz-/Klemmtoleranzen festlegen; Stack-Daempfer/Anlagehoehen abstimmen.'),
    'H02': ('Eigenfertigung', 'Konstruierter Festkoerper', 'Zuordnung zu realem Stack und Daempfern; Toleranzen, Material/Prozess und Verschraubung abschliessen.'),
    'H03': ('Eigenfertigung', 'Konstruierter Festkoerper', 'Verschraubung, Toleranzen und Material/Prozess abschliessen.'),
    'H04': ('Eigenfertigung', 'Konstruierter Festkoerper', 'Rohr-/Kappenverbindung und Batteriehalter-Verschraubung abschliessen; Toleranzen und Material/Prozess festlegen.'),
    'H05': ('Eigenfertigung', 'Konstruierter Festkoerper', 'Akku 78x37x52 vorhanden; reale Polster-/Bandfixierung, Schraubenklemmung und Kabelzugang abschliessen.'),
    'H06': ('Zuschnitt', 'Konstruierter Festkoerper', 'Endgueltige Klemmlaenge, Laengentoleranz und Werkstoff mit Batterieverschraubung abstimmen.'),
    'H07': ('Zuschnitt', 'Konstruierter Festkoerper', 'Rohrprodukt/Werkstoff und Toleranzen, Kappen-/Klemmstellen und Kabeldurchfuehrung abschliessen.'),
    'LAGER-6806': ('Kaufteil', 'Nennmassreferenz', 'Konkreten 6806-2RS-Artikel/Spielvariante und Anschlusszeichnung mit Fasen-/Schultergrenzen waehlen; Sitze/axiale Haltung darauf auslegen.'),
    'LAGER-6809': ('Kaufteil', 'Nennmassreferenz', 'Konkreten 6809-2RS-Artikel/Spielvariante und Anschlusszeichnung mit Fasen-/Schultergrenzen waehlen; Sitze/axiale Haltung darauf auslegen.'),
    'MOTOR-ECO2-2306': ('Kaufteil', 'Bemasste Anschluss-/Bauraumreferenz', 'PCD16, M3 max3 und M5 nutzbar9 bestaetigt. Nicht bemasste Fuss-/Pilotkontur pruefen; Schrauben-/Kontermutteranzug und Rundlauf fehlen. Keine OEM-Innenteile erforderlich.'),
    'SERVO-PLATZHALTER': ('Kaufteil', 'Savox Aussenreferenz', 'Savox SB-2271SG(+): genaue Variante, Laschendicke/Schlitzmasse und Hornanschluss fehlen; vollstaendiger tangentialer Halter fehlt.'),
    'KUGELBOLZEN-M2': ('Kaufteil', 'Funktionsschema', 'Konkreten Kugelbolzen mit bemaesstem Gewinde, Sitz, Sicherung und passender Pfanne waehlen.'),
    'STEUERSTANGE': ('Kaufteil oder Eigenfertigung', 'Funktionsschema', 'Reale Pfannen/Gewindestange fuer 15mm Kugelmittenabstand; Gewindeeingriff, Montage und Schwenkraum fehlen.'),
    'SERVOSTANGE': ('Kaufteil oder Eigenfertigung', 'Funktionsschema', 'Reale Pfannen, Einstellbereich, Gewindeeingriff und Schwenkraum fuer jeweilige Einbaulaenge fehlen.'),
    'STIFT-D2x18': ('Kaufteil', 'Nennmassreferenz', 'Konkreten Stiftstandard/Artikel, Enden, Sitzpassung und Sicherung festlegen.'),
    'MITNEHMERSTIFT-D3': ('Kaufteil', 'Nennmassreferenz', 'Stiftartikel, Einbindung und axiale Sicherung festlegen; nominal D3 in D3.1 ist keine Sicherung.'),
    'FUEHRUNGSSTIFT-D3': ('Kaufteil', 'Nennmassreferenz', 'Stiftartikel, Befestigung am Taumelring und Verschleisspaarung festlegen.'),
    'M2x35': ('Kaufteil', 'Funktionsschema', 'Reale Schraube mit Kopf/Mutter/Anlageflaechen und finaler Klemmlaenge festlegen.'),
    'M3x80': ('Kaufteil', 'Funktionsschema', 'Reale Batterieverschraubung mit Kopf, Muttern, Scheiben, Klemmlaenge und Sicherung abschliessen.'),
    'M3x12': ('Kaufteil', 'Importiertes Normteil', 'Nenngeometrie geprueft; Festigkeitsklasse, Bezugsartikel und Anzug/Sicherung festlegen.'),
    'M3x40': ('Kaufteil', 'Importiertes Normteil', 'Stack-Daempfer, obere Muttern und reale Anlagehoehen fehlen; Festigkeitsklasse/Anzug/Sicherung festlegen.'),
    'ISO4032-M3': ('Kaufteil', 'Importiertes Normteil', 'Festigkeitsklasse, Bezugsartikel und Anzug/Sicherung festlegen.'),
    'ISO4035-M5': ('Kaufteil', 'Nennmassreferenz', 'Duennmutter h2.7: realen Artikel/Guete und Anzug/Losdrehsicherung am M5-Ritzel festlegen.'),
    'ISO7089-M3': ('Kaufteil', 'Nennmassreferenz', 'Realen Scheibenartikel und Dickengrenzen im P05-Einschraubbudget bestaetigen.'),
    'M3x7-P05-REFERENZ': ('Kaufteil', 'Abgeleitete Normteilreferenz', 'Realen M3x7-Artikel/Guete beschaffen, Laengengrenzen und Anzug bestaetigen; CAD nur gekuerzte M3x10-Referenz.'),
    'REF_AKKU': ('Kaufteil', 'Bemasste Bauraumreferenz', 'Realen Akkuartikel, Polster/Band und Kabelaustritt/Steckerfreiraum bestaetigen. Keine Zellinnenteile erforderlich.'),
    'REF_FC': ('Kaufteil', 'Bemasste Bauraumreferenz', 'F405-V4: reale Daempfer-/Anlagehoehen und Stecker-/Kabelraeume bestaetigen.'),
    'REF_ESC': ('Kaufteil', 'Bemasste Bauraumreferenz', '55A-ESC: reale Daempfer-/Anlagehoehen, Kuehlung und Kabelraeume bestaetigen.'),
    'REF_POLSTER': ('Zuschnitt', 'Nennmassreferenz', 'Polstermaterial, Dicke/Kompression und Zuschnitt verbindlich festlegen.'),
}

def rule(o):
    if o.BauteilID.startswith('KEEP_'):
        return ('Freiraum', 'Kein Bauteil', 'Zugangsraum; nicht fertigen und nicht als Bauteil bestellen.')
    role = getattr(o, 'MotionRole', '')
    if role in ('servo_horn', 'servo_shaft', 'servo_tip'):
        reasons = {
            'servo_horn': '8mm-Hebel ist Funktionsgeometrie, kein bestaetigtes 25T-Kaufhorn; Aufnahme, Halteschraube und Kugelbolzenanschluss fehlen.',
            'servo_shaft': 'Zylinder ist Funktionsreferenz, keine vermessene 25T-Verzahnung. Gehoert zum kompletten Kaufservo.',
            'servo_tip': 'Kugel ist Funktionsreferenz ohne realen Gewinde-/Sicherungsanschluss; konkreten Kugelbolzen waehlen.',
        }
        return ('Kaufteil-Anschluss', 'Funktionsschema', reasons[role])
    if o.BauteilID not in RULES:
        raise ValueError('Unbewertete Bauteilkennung: ' + o.BauteilID)
    return RULES[o.BauteilID]


def main():
    doc = App.openDocument(str(SOURCE))
    rows = []
    for o in doc.Objects:
        if not hasattr(o, 'BauteilID'):
            continue
        kind, representation, remaining = rule(o)
        physical = kind != 'Freiraum'
        valid = not o.Shape.isNull() and o.Shape.isValid() and len(o.Shape.Solids) > 0
        if not valid:
            raise ValueError('Ungueltige Geometrie: ' + o.Name)
        rows.append(dict(name=o.Name, part_id=o.BauteilID, label=o.Label,
                         category=kind, representation=representation,
                         physical=physical, geometry_valid=valid,
                         manufacturing_ready=False, remaining=remaining))
        for typ, name, value in [
            ('App::PropertyString', 'P06_Darstellung', representation),
            ('App::PropertyString', 'P06_Beschaffung', kind),
            ('App::PropertyString', 'P06_Offen', remaining),
            ('App::PropertyBool', 'P06_Fertigungsbereit', False),
        ]:
            o.addProperty(typ, name, 'P06 Fertigungspruefung')
            setattr(o, name, value)
            o.setEditorMode(name, 1)
        # Correct obsolete category/name without pretending to supply missing geometry.
        if o.BauteilID == 'RITZEL-M1-Z20':
            o.P02_Klasse = 'Eigenfertigung_P05_Gewinderitzelentwurf'
            o.Herstellung = 'Zerspanung_Entwurf'
        if o.BauteilID == 'SERVO-PLATZHALTER':
            o.Label = 'Savox_SB2271SG_Anschlussreferenz__' + o.Name
        if hasattr(o, 'Bewegungsstatus'):
            o.Bewegungsstatus = 'P06: ' + representation + '; ' + remaining
    count = Counter(r['representation'] for r in rows if r['physical'])
    physical_count = sum(r['physical'] for r in rows)
    missing = [
        dict(part='Tangentialer Servo-Montagehalter', quantity=6,
             reason='Noch kein finaler Halter mit passenden Savox-Laschenanschluessen, Schrauben und Lastpfad vorhanden.'),
        dict(part='Klemm-/Axialsicherungsbefestigungen', quantity=None,
             reason='Baugruppe enthaelt noch nicht alle notwendigen Klemmschrauben, Sicherungen und Anschluesse; Anzahl folgt aus fertiger Konstruktion.'),
    ]
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    info = doc.getObject('P02_Fertigungsstatus')
    info.Begruendung = 'P06 Vollinventur: Funktionsgeometrien und unvollstaendige Eigenfertigungsanschluesse vorhanden; siehe P06_Offen an jedem Bauteil. Keine Gesamtfreigabe.'
    info.Gesamt_Fertigungsfreigabe = False
    doc.Label = 'P06 Vollstaendigkeitspruefung – NICHT FERTIGUNGSBEREIT'
    doc.Comment = info.Begruendung
    doc.recompute()
    path = OUT / 'P06_Bauteilpruefung_NICHT_FERTIGUNGSBEREIT.FCStd'
    doc.saveAs(str(path))
    App.closeDocument(doc.Name)
    check = App.openDocument(str(path))
    assert not check.getObject('P02_Fertigungsstatus').Gesamt_Fertigungsfreigabe
    assert len([o for o in check.Objects if hasattr(o, 'P06_Fertigungsbereit')]) == len(rows)
    # Geometry must not change merely because audit metadata was added.
    original = App.openDocument(str(SOURCE))
    for row in rows:
        a, b = original.getObject(row['name']), check.getObject(row['name'])
        # Compare topology, integral quantities, every vertex, and all bounds.
        # Avoid a minimum-distance test: touching surfaces would not prove equality.
        for attr in ('Solids', 'Shells', 'Faces', 'Edges', 'Vertexes'):
            assert len(getattr(a.Shape, attr)) == len(getattr(b.Shape, attr))
        assert abs(a.Shape.Volume-b.Shape.Volume) < 1e-6
        assert abs(a.Shape.Area-b.Shape.Area) < 1e-6
        for attr in ('XMin','XMax','YMin','YMax','ZMin','ZMax'):
            assert abs(getattr(a.Shape.BoundBox, attr)-getattr(b.Shape.BoundBox, attr)) < 1e-7
        av=sorted((v.Point.x,v.Point.y,v.Point.z) for v in a.Shape.Vertexes)
        bv=sorted((v.Point.x,v.Point.y,v.Point.z) for v in b.Shape.Vertexes)
        assert all(abs(x-y)<1e-7 for va,vb in zip(av,bv) for x,y in zip(va,vb))
        assert not b.P06_Fertigungsbereit
    App.closeDocument(original.Name)
    App.closeDocument(check.Name)
    report = dict(source=str(SOURCE.relative_to(ROOT)), source_sha256=source_hash,
                  native_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  overall_manufacturing_ready=False, physical_objects=physical_count,
                  access_spaces=len(rows)-physical_count, representations=dict(count),
                  native_reopen_pass=True, geometry_preserved=True,
                  geometry_comparison="Topology counts, volume, area, all bounds and vertices within numerical tolerance; metadata-only revision",
                  missing_components=missing, parts=rows)
    (OUT / 'Vollstaendigkeitspruefung.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    with (OUT / 'Bauteile_und_offene_Fertigungspunkte.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    lines = ['# P06 – vollständige Bauteilprüfung', '',
             f'Geprüft: {physical_count} modellierte Bauteilobjekte und {len(rows)-physical_count} Zugangs-/Freiräume. Alle Festkörper gültig und native Datei erneut geöffnet. **Gesamtstand nicht fertigungsbereit.**', '',
             'Das Prüfergebnis bewertet Fertigungsvollständigkeit, nicht nur die Gültigkeit der Festkörper. Es verändert keine Geometrie und erteilt keine Freigabe.', '',
             '| Bauteilkennung / Rolle | Anzahl | Darstellung | Noch auszuarbeiten |',
             '|---|---:|---|---|']
    grouped = Counter((r['part_id'] if not r['part_id'].startswith('M01_') else 'M01_Servoanschluss', r['representation'], r['remaining']) for r in rows if r['physical'])
    for (ident, representation, reason), n in sorted(grouped.items()):
        lines.append(f'| {ident} | {n} | {representation} | {reason} |')
    lines += ['', '## Noch nicht vorhandene Bauteile', '']
    lines += ['- '+x['part']+': '+x['reason'] for x in missing]
    lines += ['', '## Bereits bestätigte Motoranschlüsse', '',
              '4×M3 auf Ø16 mm Teilkreis; M3 maximal 3 mm Einschraubtiefe; M5 nutzbar 9 mm. P05 enthält M3×7 plus 0,5-mm-Scheibe bei 4-mm-Platte (2,5 mm Einschraubtiefe), Gewinderitzel 5,5 mm plus dünne Kontermutter 2,7 mm. Diese Maße werden nicht erneut angefordert.', '',
              'M3/M5-Gewinde dürfen in einem Fertigungsmodell normgerecht vereinfacht dargestellt werden, wenn Zeichnung und Prüfmaße sie eindeutig festlegen. Fehlende Anschlüsse werden dadurch nicht vollständig. Kaufmotor-/Servo-/Lagerinnenteile werden gemäß vereinbarter Kaufteilstrategie nicht selbst gefertigt.', '']
    (HERE / 'Bauteilbericht.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['physical_objects','access_spaces','representations','native_reopen_pass','geometry_preserved','overall_manufacturing_ready']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
