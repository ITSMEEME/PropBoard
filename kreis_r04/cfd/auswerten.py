#!/usr/bin/env python3
"""REKONSTRUKTION (2026-10-30): numerische Akzeptanzpruefung und Kraft-/Leistungsauswertung der Sektorfaelle.

Akzeptanz (alle erforderlich): Netzpruefung bestanden (Gmsh-Bericht und, falls vorhanden, checkMesh
'Mesh OK.'), Solver regulaer beendet, >= 200 Kraftausgabepunkte, Kraftdrift im letzten Fenster < 3 %,
relative Kraftstreuung < 5 %, relative Massenbilanzabweichung < 1 %, Impuls-Anfangsresiduen < 1e-4.

Vertikale Sektorkraft wird mit 8 auf den Vollkreis hochgerechnet; horizontale Sektorkomponenten
werden wegen der gedrehten Sektoren NICHT als globale Komponenten hochgerechnet. Leistung aus
Drehmoment Mz und Drehrichtung je Zone. Kraftverlaeufe ueber SIMPLE-Iterationen sind numerische
Konvergenz, keine physikalischen Zeitverlaeufe. F/g ist ein Brutto-Kraftaequivalent, keine zulaessige
Personenzuladung; allowable_payload_kg bleibt null.
"""
import csv, json, re, statistics, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import profil

G, N_SECTORS, WINDOW = 9.81, 8, 200
LIMITS = {'kraftpunkte_min': 200, 'drift_max': .03, 'streuung_max': .05, 'massenbilanz_max': .01, 'residuum_U_max': 1e-4}
NUM = re.compile(r'[-+]?\d+\.?\d*(?:[eE][-+]?\d+)?')


def table(path):
    rows = []
    for line in path.read_text().splitlines():
        if line.startswith('#') or not line.strip():continue
        rows.append([float(x) for x in NUM.findall(line)])
    return rows


def latest(folder, filename):
    hits = sorted(folder.glob(f'*/{filename}'), key=lambda p: float(p.parent.name)) if folder.exists() else []
    return hits[-1] if hits else None


def evaluate(case):
    meta = json.loads((case/'case.json').read_text()) if (case/'case.json').exists() else {}
    res = {'fall': case.name, 'U_ref_m_s': meta.get('U_ref_m_s'), 'gruende': [], 'allowable_payload_kg': None}
    mesh = HERE/'results'/f'Netzpruefung_{case.name}.json'
    mesh_ok = mesh.exists() and json.loads(mesh.read_text()).get('netzpruefung_bestanden', False)
    cm = case/'log.checkMesh'
    if cm.exists():mesh_ok &= 'Mesh OK.' in cm.read_text(errors='ignore')
    res['netz_ok'] = bool(mesh_ok)
    if not mesh_ok:res['gruende'].append('Netzpruefung nicht bestanden oder fehlt')
    log = case/'log.simpleFoam'; text = log.read_text(errors='ignore') if log.exists() else ''
    res['solver_regulaer'] = bool(text) and 'FOAM FATAL' not in text and re.search(r'^End\s*$', text, re.M) is not None
    if not res['solver_regulaer']:res['gruende'].append('Solver nicht regulaer beendet oder nicht gelaufen')
    ux = [float(m) for m in re.findall(r'Solving for Ux, Initial residual = ([^,]+)', text)]
    uy = [float(m) for m in re.findall(r'Solving for Uy, Initial residual = ([^,]+)', text)]
    uz = [float(m) for m in re.findall(r'Solving for Uz, Initial residual = ([^,]+)', text)]
    res['residuum_U'] = max(r[-1] for r in (ux, uy, uz)) if ux and uy and uz else None
    om = meta.get('omega_rad_s')
    fz_total, power, series = 0., 0., None
    for patch, sign in (('wing_lower', 1), ('wing_upper', -1)):
        f = latest(case/'postProcessing'/f'forces_{patch}', 'force.dat'); m = latest(case/'postProcessing'/f'forces_{patch}', 'moment.dat')
        if not f or not m:
            res['gruende'].append(f'Kraftausgabe {patch} fehlt'); series = None; break
        F, M = table(f), table(m)
        fz = [r[3] for r in F]; mz = [r[3] for r in M]
        series = fz if series is None else [a+b for a, b in zip(series, fz)]
        fz_total += statistics.fmean(fz[-WINDOW:])
        # Leistung, die die Zone an das Fluid abgibt: -Mz_Fluid_auf_Fluegel * omega_zone
        power += -statistics.fmean(mz[-WINDOW:])*sign*om
    if series:
        res['kraftpunkte'] = len(series); last = series[-WINDOW:]; mean = statistics.fmean(last)
        half = len(last)//2
        res['drift'] = abs(statistics.fmean(last[half:])-statistics.fmean(last[:half]))/abs(mean) if mean else None
        res['streuung'] = (max(last)-min(last))/abs(mean) if mean else None
        res['Fz_Sektor_N'] = fz_total; res['Fz_Vollkreis_N'] = N_SECTORS*fz_total
        res['Brutto_Kraftaequivalent_kg'] = N_SECTORS*fz_total/G
        res['P_aero_mech_Vollkreis_W'] = N_SECTORS*power
    fluxes = {}
    for p in ('outer', 'top', 'bottom', 'inner'):
        s = latest(case/'postProcessing'/f'flux_{p}', 'surfaceFieldValue.dat')
        if s:fluxes[p] = statistics.fmean(r[1] for r in table(s)[-WINDOW:])
    res['massenbilanz'] = abs(sum(fluxes.values()))/sum(abs(v) for v in fluxes.values()) if fluxes and any(fluxes.values()) else None
    checks = {'netz': res['netz_ok'], 'solver': res['solver_regulaer'],
              'kraftpunkte': res.get('kraftpunkte', 0) >= LIMITS['kraftpunkte_min'],
              'drift': res.get('drift') is not None and res['drift'] < LIMITS['drift_max'],
              'streuung': res.get('streuung') is not None and res['streuung'] < LIMITS['streuung_max'],
              'massenbilanz': res['massenbilanz'] is not None and res['massenbilanz'] < LIMITS['massenbilanz_max'],
              'residuum': res['residuum_U'] is not None and res['residuum_U'] < LIMITS['residuum_U_max']}
    res['pruefungen'] = checks; res['akzeptiert'] = all(checks.values())
    return res


def main():
    cases = sorted(p for p in (HERE/'cases').glob('*') if p.is_dir()) if (HERE/'cases').exists() else []
    results = [evaluate(c) for c in cases]
    meshes = sorted(p.stem.removeprefix('Netzpruefung_') for p in (HERE/'results').glob('Netzpruefung_*.json'))
    out = {'status': 'REKONSTRUKTION', 'grenzwerte': LIMITS, 'faelle': results,
           'netzberichte': meshes, 'akzeptierte_faelle': [r['fall'] for r in results if r['akzeptiert']],
           'allowable_payload_kg': None,
           'hinweis': 'Ohne akzeptierte Faelle liegen keine freigegebenen CFD-Kraefte vor. Schwebefall, kein Vorwaertsflug, keine Validierung.'}
    (HERE/'results').mkdir(exist_ok=True)
    (HERE/'results'/'Auswertung.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    cols = ['fall', 'U_ref_m_s', 'akzeptiert', 'netz_ok', 'solver_regulaer', 'kraftpunkte', 'drift', 'streuung', 'massenbilanz',
            'residuum_U', 'Fz_Vollkreis_N', 'Brutto_Kraftaequivalent_kg', 'P_aero_mech_Vollkreis_W', 'allowable_payload_kg', 'gruende']
    with (HERE/'results'/'CFD_Ergebnisse.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); w.writeheader()
        for r in results:w.writerow({**r, 'gruende': '; '.join(r['gruende'])})
    print(json.dumps({k: out[k] for k in ('akzeptierte_faelle', 'netzberichte')}, indent=1))
    for r in results:print(r['fall'], 'akzeptiert' if r['akzeptiert'] else 'NICHT akzeptiert:', '; '.join(r['gruende']))


if __name__ == '__main__':
    main()
