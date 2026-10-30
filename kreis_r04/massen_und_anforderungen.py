#!/usr/bin/env python3
"""REKONSTRUKTION (2026-10-30): Massenszenarien und analytische Auftriebsanforderungen R04.

Erfasste Modellmasse aus CAD_Volumen.csv (nur Koerper mit Werkstoffklasse CFK/Aluminium/Stahl;
Referenzbauraeume, Magnete, Elektronik, Batteriezellen u. a. fehlen). Das ist KEINE Fahrzeugmasse.

Auftrieb: L = 1/2 rho CL c (U/R)^2 (r2^3 - r1^3)/3 je Fluegel, 16 Fluegel, CL frei angenommen.
Keine induzierte Stroemung, keine Fluegel-Fluegel-Interferenz, keine Ebenenwechselwirkung -> obere
Schranke-artige Idealisierung, getrennt von CFD zu behandeln. allowable_payload_kg bleibt null.
"""
import csv, json, math, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import profil

G, RHO, PERSON = 9.81, 1.225, 100.
SPEEDS = list(range(10, 75, 5)); CLS = (.5, .8, 1.0, 1.2)
# Frei gewaehlte Zusatzszenarien, keine Auslegung:
SCENARIOS = {'S1_nur_CAD_erfasst': (1.0, 0.), 'S2_CAD_plus_30_Prozent_Struktur': (1.3, 0.),
             'S3_S2_plus_25kg_Akku_Antrieb': (1.3, 25.)}
R1, R2, R = (r/1000 for r in (*profil.R_WING, profil.RADIUS))
C = profil.CHORD/1000; N = 2*profil.WINGS_PER_LEVEL


def lift(u, cl):
    return N*.5*RHO*cl*C*(u/R)**2*(R2**3-R1**3)/3


def cad_masses():
    m = {}
    with (HERE/'CAD_Volumen.csv').open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r['Masse_kg']:m[r['Variante']] = m.get(r['Variante'], 0.)+float(r['Masse_kg'])
    return m


def main():
    cad = cad_masses()
    scen = []
    for var, m in cad.items():
        for s, (factor, extra) in SCENARIOS.items():
            scen.append({'Variante': var, 'Szenario': s, 'CAD_erfasst_kg': round(m, 3), 'Faktor': factor, 'Zuschlag_kg': extra,
                         'Fahrzeug_Szenario_kg': round(m*factor+extra, 3), 'Person_kg': PERSON,
                         'Erforderliche_Vertikalkraft_N': round((m*factor+extra+PERSON)*G, 2)})
    rows = []
    for sc in scen:
        for cl in CLS:
            for u in SPEEDS:
                L = lift(u, cl)
                rows.append({'Variante': sc['Variante'], 'Szenario': sc['Szenario'], 'CL_angenommen': cl, 'U_ref_m_s': u,
                             'Auftrieb_analytisch_N': round(L, 2), 'Kraftaequivalent_kg': round(L/G, 2),
                             'Erforderlich_N': sc['Erforderliche_Vertikalkraft_N'],
                             'Verhaeltnis': round(L/sc['Erforderliche_Vertikalkraft_N'], 4),
                             'Zentripetalbeschleunigung_r450_g': round(u**2/R/G, 1),
                             'allowable_payload_kg': None})
    for sc in scen:
        sc['U_min_m_s_je_CL'] = {cl: round(u, 2) for cl in CLS
                                 for u in [math.sqrt(sc['Erforderliche_Vertikalkraft_N']/lift(1., cl))]}
    out = {'status': 'REKONSTRUKTION_ANALYTISCH_CL_FREI_ANGENOMMEN', 'dichte_luft': RHO, 'person_kg': PERSON,
           'szenarien': scen, 'anzahl_faelle': len(rows), 'cad_erfasste_masse_kg': cad,
           'differenz_mit_minus_ohne_Aussenring_kg': (cad.get('Kreis_R04_Aussenring', 0)-cad.get('Kreis_R04_ohne_Aussenring', 0)) if len(cad) == 2 else None,
           'allowable_payload_kg': None,
           'fehlend': ['tatsaechliche Batterien', 'Teile des Antriebs', 'Magnet-/Spulensysteme', 'Elektronik', 'neue vollstaendige Tragstruktur'],
           'hinweis': 'Keine induzierte Stroemung/Interferenz; nicht mit CFD-Ergebnissen vermischen. Kraftaequivalent ist keine zulaessige Zuladung.'}
    (HERE/'Massen_Szenarien.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    with (HERE/'Massen_Szenarien.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=[k for k in scen[0] if k != 'U_min_m_s_je_CL']+[f'U_min_CL{cl}' for cl in CLS]); w.writeheader()
        for sc in scen:w.writerow({**{k: v for k, v in sc.items() if k != 'U_min_m_s_je_CL'}, **{f'U_min_CL{cl}': v for cl, v in sc['U_min_m_s_je_CL'].items()}})
    with (HERE/'Auftriebsanforderungen.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(json.dumps({k: out[k] for k in ('cad_erfasste_masse_kg', 'differenz_mit_minus_ohne_Aussenring_kg', 'anzahl_faelle')}, indent=1))


if __name__ == '__main__':
    main()
