#!/usr/bin/env python3
"""REKONSTRUKTION (2026-10-30): Euler-Bernoulli-Balkenmodell der Pitchwelle, R04 mit/ohne Aussenring.

Modell: Stahlwelle D8, L 640 mm (r 130..770 mm), E 200 GPa; nur die Welle traegt.
- mit Aussenring: vertikal einfach abgestuetzt bei r 130 und r 770,
- ohne Aussenring: bei r 130 eingespannter Kragarm.
Aerodynamische Last proportional r**2 auf dem Fluegelbereich r 150..750 mm, Gesamtauftrieb
vorgeschrieben (nicht aus CFD). Eigengewicht wirkt nach unten. Zentrifugale Zugversteifung
optional ueber geometrische Steifigkeit; die axiale Fliehkraft wird innen abgesetzt, die
aeussere Lagerung ist axial schwimmend. Kein Festigkeitsnachweis des realen Fahrzeugs.
"""
import csv, json, math, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import profil

G = 9.81
E, D, L = 200e9, .008, .64
R0 = profil.R_GUIDE[0]/1000
WING = tuple(r/1000 for r in profil.R_WING)
RHO_STEEL, RHO_CFK = 7850., 1600.
A, I = math.pi*D**2/4, math.pi*D**4/64
EI = E*I
SHELL_A = profil.shell_area_mm2()*1e-6        # Fluegelschale aus Profilpolygon, gleiche Definition wie CAD
S355_ANNAHME_MPA = 355.                        # Vergleichswert, Wellenwerkstoff NICHT ausgewaehlt
N_WINGS = 2*profil.WINGS_PER_LEVEL


def element_matrices(le, n_axial):
    k = EI/le**3*np.array([[12, 6*le, -12, 6*le], [6*le, 4*le**2, -6*le, 2*le**2],
                           [-12, -6*le, 12, -6*le], [6*le, 2*le**2, -6*le, 4*le**2]])
    kg = n_axial/(30*le)*np.array([[36, 3*le, -36, 3*le], [3*le, 4*le**2, -3*le, -le**2],
                                   [-36, -3*le, 36, -3*le], [3*le, -le**2, -3*le, 4*le**2]])
    return k, kg


def solve(variant, n_el, q_fun, n_fun=lambda x: 0., point=None, tip_moment=0.):
    """Linear mit vorgegebener Normalkraft. q_fun(x) [N/m] nach oben, x ab Innenlager."""
    nodes = np.linspace(0, L, n_el+1); ndof = 2*(n_el+1)
    K = np.zeros((ndof, ndof)); F = np.zeros(ndof)
    gp, gw = np.polynomial.legendre.leggauss(6)
    for e in range(n_el):
        a, b = nodes[e], nodes[e+1]; le = b-a
        k, kg = element_matrices(le, n_fun((a+b)/2))
        idx = [2*e, 2*e+1, 2*e+2, 2*e+3]
        K[np.ix_(idx, idx)] += k+kg
        for s, w in zip(gp, gw):
            xi = (s+1)/2; x = a+xi*le
            Nshape = np.array([1-3*xi**2+2*xi**3, le*(xi-2*xi**2+xi**3), 3*xi**2-2*xi**3, le*(-xi**2+xi**3)])
            F[idx] += Nshape*q_fun(x)*w*le/2
    if point:
        x, P = point; j = int(round(x/L*n_el)); F[2*j] += P
    F[-1] += tip_moment
    fixed = [0, 1] if variant == 'ohne_Aussenring' else [0, ndof-2]
    free = [i for i in range(ndof) if i not in fixed]
    u = np.zeros(ndof); u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
    w = u[0::2]
    # Biegemoment an Elementenden aus Hermite-Kruemmung
    M = np.zeros(n_el+1)
    for e in range(n_el):
        le = nodes[e+1]-nodes[e]; ue = u[2*e:2*e+4]
        for xi, j in ((0., e), (1., e+1)):
            B = np.array([-6+12*xi, le*(-4+6*xi), 6-12*xi, le*(-2+6*xi)])/le**2
            M[j] = max(M[j], abs(EI*B@ue), key=abs)
    return nodes, w, M


def loads(lift_total_n, u_ref, stiffening):
    r_of = lambda x: R0+x
    on_wing = lambda r: WING[0] <= r <= WING[1]
    lift_wing = lift_total_n/N_WINGS
    c = lift_wing/((WING[1]**3-WING[0]**3)/3)
    mprime = lambda r: RHO_STEEL*A+(RHO_CFK*SHELL_A if on_wing(r) else 0.)
    q = lambda x: (c*r_of(x)**2 if on_wing(r_of(x)) else 0.)-mprime(r_of(x))*G
    om = profil.omega(u_ref)
    xs = np.linspace(0, L, 2001); rs = R0+xs
    dens = np.array([mprime(r)*om**2*r for r in rs])
    tail = np.concatenate([[0.], np.cumsum((dens[1:]+dens[:-1])/2*np.diff(xs))]); tail = tail[-1]-tail
    n_fun = (lambda x: float(np.interp(x, xs, tail))) if stiffening else (lambda x: 0.)
    return q, n_fun, float(tail[0])


def case(variant, u_ref, mass_equiv_kg, stiffening=True, n_el=64):
    q, n_fun, n_root = loads(mass_equiv_kg*G, u_ref, stiffening)
    nodes, w, M = solve(variant, n_el, q, n_fun)
    n_nodes = np.array([n_fun(x) for x in nodes])
    sigma = (np.abs(M)*D/2/I+n_nodes/A)/1e6
    return {'Variante': variant, 'U_ref_m_s': u_ref, 'Auftrieb_Kraftaequivalent_kg': mass_equiv_kg,
            'Zugversteifung': stiffening, 'Elemente': n_el,
            'max_Durchbiegung_mm': float(np.max(np.abs(w))*1000), 'max_Biegemoment_Nm': float(np.max(np.abs(M))),
            'Fliehkraft_innen_N': n_root, 'max_nominelle_Spannung_MPa': float(np.max(sigma)),
            'Verhaeltnis_zu_S355_Annahme': float(np.max(sigma)/S355_ANNAHME_MPA)}


def verification():
    q0, P, M0, n = 100., 50., 5., 64
    checks = []
    def add(name, numeric, analytic):
        numeric = float(numeric)
        checks.append({'Fall': name, 'numerisch': numeric, 'analytisch': analytic,
                       'rel_Abweichung': abs(numeric-analytic)/abs(analytic)})
    _, w, _ = solve('mit_Aussenring', n, lambda x: q0); add('einfach_gestuetzt_Gleichlast_Mitte', w[n//2], 5*q0*L**4/(384*EI))
    _, w, _ = solve('mit_Aussenring', n, lambda x: 0., point=(L/2, P)); add('einfach_gestuetzt_Einzellast_Mitte', w[n//2], P*L**3/(48*EI))
    _, w, M = solve('mit_Aussenring', n, lambda x: q0); add('einfach_gestuetzt_Gleichlast_Moment_Mitte', abs(M[n//2]), q0*L**2/8)
    _, w, _ = solve('ohne_Aussenring', n, lambda x: q0); add('Kragarm_Gleichlast_Spitze', w[-1], q0*L**4/(8*EI))
    _, w, _ = solve('ohne_Aussenring', n, lambda x: 0., point=(L, P)); add('Kragarm_Einzellast_Spitze', w[-1], P*L**3/(3*EI))
    _, w, _ = solve('ohne_Aussenring', n, lambda x: 0., tip_moment=M0); add('Kragarm_Endmoment_Spitze', w[-1], M0*L**2/(2*EI))
    for c in checks:c['bestanden'] = c['rel_Abweichung'] < 1e-3
    return checks


def main():
    ref = {v: case(v, 50., 200.) for v in ('mit_Aussenring', 'ohne_Aussenring')}
    disc = [case(v, 50., 200., True, n) for v in ref for n in (16, 32, 64, 128)]
    sweep = [case(v, u, m, s) for v in ref for s in (True, False) for m in (100., 150., 200., 250.) for u in range(10, 75, 5)]
    checks = verification()
    with (HERE/'Struktur_Sweep.csv').open('w', newline='', encoding='utf-8-sig') as f:
        wr = csv.DictWriter(f, fieldnames=list(sweep[0])); wr.writeheader(); wr.writerows(sweep)
    report = {'status': 'REKONSTRUKTION_BEDINGTES_MODELL_KEIN_FESTIGKEITSNACHWEIS',
              'annahmen': {'Welle': 'Stahl D8 mm, L 640 mm, E 200 GPa (Werkstoff nicht ausgewaehlt)',
                           'Fluegelschale_Querschnitt_mm2': SHELL_A*1e6, 'Dichte_CFK': RHO_CFK, 'Dichte_Stahl': RHO_STEEL,
                           'Fluegelmasse_kg': RHO_CFK*SHELL_A*(WING[1]-WING[0]), 'Wellenmasse_kg': RHO_STEEL*A*L,
                           'Lastverteilung': 'proportional r^2 auf r 150..750 mm, Gesamtauftrieb vorgeschrieben',
                           'Lagerung_mit_Aussenring': 'vertikal einfach abgestuetzt r 130/770',
                           'Lagerung_ohne_Aussenring': 'Kragarm, eingespannt r 130',
                           'Axiallast': 'aeussere Lagerung axial schwimmend; Fliehkraft innen abgesetzt',
                           'S355_MPa': 'nur angenommener Vergleichswert'},
              'referenzfall_50m_s_200kg': ref, 'diskretisierung': disc, 'verifikation_Euler_Bernoulli': checks,
              'parameterfaelle': len(sweep),
              'nicht_abgedeckt': ['tatsaechliche CFK-Tragwirkung', 'Fuegestellen', 'Torsion', 'Ermuedung', 'Magnetfuehrung',
                                  'vollstaendige Dynamik/Eigenfrequenzen', 'gekoppelte Stroemungs-Struktur-Rechnung',
                                  'neu auszulegende Fluegelwurzel/Drehmomentuebertragung ohne Aussenring']}
    (HERE/'Struktur_Referenz.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    for v, r in ref.items():
        print(v, {k: round(x, 3) if isinstance(x, float) else x for k, x in r.items()})
    print('Verifikation bestanden:', all(c['bestanden'] for c in checks), max(c['rel_Abweichung'] for c in checks))
    print('Diskretisierung:', [(d['Variante'][:4], d['Elemente'], round(d['max_Durchbiegung_mm'], 4), round(d['max_nominelle_Spannung_MPa'], 2)) for d in disc])


if __name__ == '__main__':
    main()
