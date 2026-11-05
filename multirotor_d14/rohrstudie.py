"""Grundsatzpruefung der CFK-Rohrdurchmesser fuer die D14-Ausleger (reines Python).

Fuer jede Bauweise x Propeller x Variante (V1 Einrohr, V2 Zweigurt, V3 Dreirohr) und jede handelsuebliche
Rohrgroesse werden bewertet:
  1. Festigkeit und Knicken im D14-Lastfall (Schweben x 3 g) mit der realen Abflugmasse aus dem Flugsimulator
  2. Querbiegung durch Motormoment und Kreiselmoment (das vertikale Fachwerk traegt seitlich nur ueber Rohrbiegung)
  3. Eigenfrequenzen des Auslegers (vertikal, seitlich) gegen 1P- und 2P-Anregung im Drehzahlbereich
  4. Masse (Rohre + Alu-Huelsen) und deren Wirkung auf die Schwebeleistung, Abschattung im Abwind
  5. Wandstaerke (D/t, Mindestwand) fuer Klemmung und Handhabung
Die Ausleger-Geometrie wird mit auslegung.arm() fuer die jeweilige Rohrgroesse neu berechnet; die Motorpositionen
bleiben wie in D14. Ergebnis: Ausgabe/Rohrstudie/.
"""
import json, math, csv, copy
from pathlib import Path
import numpy as np
import auslegung as AL

H = Path(__file__).resolve().parent
OUT = H / 'Ausgabe' / 'Rohrstudie'; OUT.mkdir(parents=True, exist_ok=True)
P = AL.P
AUS = {c['schluessel']: c for c in json.loads((H / 'Ausgabe/Auslegung.json').read_text())['konfigurationen']}
PRU = {c['schluessel']: c for c in json.loads((H / 'Ausgabe/Pruefung.json').read_text())['konfigurationen']}
SIM = {c['schluessel']: c for c in json.loads((H.parent / 'flugsimulator/Ergebnisse/Schwebeanalyse_alle.json').read_text())['konfigurationen']}

# Handelsuebliche gewickelte CFK-Rohre (Aussen x Innen, mm)
KATALOG = [(16, 14), (18, 16), (20, 18), (20, 17), (22, 20), (22, 19), (25, 23), (25, 22), (28, 26), (28, 25),
           (30, 28), (30, 27), (32, 30), (32, 29), (35, 33), (35, 32), (40, 38), (40, 37), (45, 42), (50, 47), (50, 46), (60, 57), (60, 56)]
SPREIZUNG_R3 = 60.0                           # halbe seitliche Wurzelspreizung der Obergurte im Raumfachwerk R3 (mm)
F_MIN = 15.0                                  # Mindest-Eigenfrequenz: Abstand zur Flugregelung und Boeenanregung (Hz)
LA = P['lasten']
E_CFK = LA['cfk_e_modul_mpa']; SIG_ZUL = LA['cfk_zulaessig_mpa']; G0 = LA['g_m_s2']; LF = LA['lastfaktor']
RHO_CFK = 1.55e-6; RHO_ALU = 2.81e-6         # kg/mm^3
GAMMA_KNICK = 1.5                             # Abminderung fuer Imperfektion/Kerben bei duennwandigem CFK
M_MOTOR = 2.75; Q_MOTOR_MAX = 46.25           # MN1330: Masse, groesstes gemessenes Drehmoment (Nm)
D_T_MAX = 25.0; T_MIN = 1.0                   # Wandkriterien
ABSTAND = 0.15                                # geforderter Frequenzabstand zu Anregungsbaendern (+-15 %)


def variante(vid, od, di):
    v = copy.deepcopy(P['varianten'][vid]); v['rohr_od_mm'] = od; v['rohr_id_mm'] = di; return v


def arm_fuer(bw, prop, vid, R, od, di):
    """auslegung.arm() mit geaenderter Rohrgroesse; Huelsenmittenabstand am Motortraeger waechst mit der Huelse."""
    P['varianten']['_X'] = variante(vid, od, di)
    alt = P['motortraeger']['huelsen_mittenabstand_mm']
    hu = AL.huelse(P['varianten']['_X'])
    P['motortraeger']['huelsen_mittenabstand_mm'] = max(alt, 2 * hu['r_aussen'] + 3.4)
    try:
        return AL.arm(bw, prop, '_X', R)
    finally:
        P['motortraeger']['huelsen_mittenabstand_mm'] = alt; del P['varianten']['_X']


def querschnitt(od, di):
    A = math.pi / 4 * (od ** 2 - di ** 2); I = math.pi / 64 * (od ** 4 - di ** 4); W = I / (od / 2)
    return A, I, W


def bewerte(bw, prop, vid, od, di):
    raum = vid in ('R3', 'R4'); vbas = 'V3' if raum else vid
    key = f'{bw}_{prop["id"]}_{vbas}'; c = AUS[key]; sim = SIM[key]
    R = c['motorradius_mm']; g = arm_fuer(bw, prop, vbas, R, od, di)
    npos = P['bauweisen'][bw]['rotorpositionen']; koax = bw == 'KOAX'
    A, I, W = querschnitt(od, di); n = len(g['rohre']); hu = g['huelse']
    masse = max(LA['gesamtmasse_kg'], sim['masse_kg'])
    F = masse * G0 * LF / npos                                   # Schub je Ausleger im Lastfall (N)
    Fh = sim['masse_kg'] * G0 / npos                             # Schwebeschub je Ausleger
    # ---- 1. vertikal: Kragarm (V1) bzw. Gelenkstabwerk (V2/V3)
    k_lat = None; spreizung = 0.0
    if raum:
        # Raumfachwerk: Obergurte an der Wurzel um +-b quer gespreizt, Untergurt mittig; alle treffen sich im Systempunkt I
        Ip = np.array(g['I']); W0 = np.array(g['W']); uu = np.array(g['u']); nq = np.array([-uu[1], uu[0], 0.0])
        wz = P['varianten']['V2']['wurzel_z_mm']; Vp = np.array(g['Vp'])
        # baubar: zusaetzliche Gurte enden im benachbarten Rahmeneckknoten (dort sitzen bereits die Laschen des Dreiecksverbinders)
        wurzeln = [W0 + [0, 0, wz[0]], Vp + [0, 0, wz[0]], W0 + [0, 0, wz[1]]] + ([Vp + [0, 0, wz[1]]] if vid == 'R4' else [])
        K3 = np.zeros((3, 3)); st = []
        for w_ in wurzeln:
            d = w_ - Ip; L = np.linalg.norm(d); e = d / L; K3 += E_CFK * A / L * np.outer(e, e); st.append((e, L))
        u = np.linalg.solve(K3, [0, 0, F]); sig_v = 0.0; knick = 0.0
        for e, L in st:
            N = -E_CFK * A / L * float(e @ u); sig_v = max(sig_v, abs(N) / A)
            Lf = L - g['d0'] - g['ce'] - 2 * hu['L']; Pcr = math.pi ** 2 * E_CFK * I / Lf ** 2; knick = max(knick, max(0.0, -N) * GAMMA_KNICK / Pcr)
        kv = 1.0 / np.linalg.inv(K3)[2, 2]
        lat = np.cross([0, 0, 1.0], uu); k_lat = 1.0 / float(lat @ np.linalg.inv(K3) @ lat)
        n = len(st); g = dict(g, rohre=[dict(systemlaenge_mm=L) for e, L in st])
        spreizung = float(abs((Vp - W0) @ nq))
    elif n == 1:
        L = g['Lr']; sig_v = F * L / W; knick = 0.0; kv = 3 * E_CFK * I / L ** 3
    else:
        K = [[0.0, 0.0], [0.0, 0.0]]; st = []
        for t in g['rohre']:
            d3 = AL.sub(t['wurzel'], t['systempunkt']); L = AL.norm(d3)
            d = [-math.hypot(d3[0], d3[1]) / L, d3[2] / L]; k = E_CFK * A / L
            for i in range(2):
                for j in range(2): K[i][j] += k * d[i] * d[j]
            st.append((t, d, k))
        det = K[0][0] * K[1][1] - K[0][1] * K[1][0]
        u = [-K[0][1] * F / det, K[0][0] * F / det]
        sig_v = 0.0; knick = 0.0
        for t, d, k in st:
            N = -k * (d[0] * u[0] + d[1] * u[1]); sig_v = max(sig_v, abs(N) / A)
            Lf = t['laenge_mm'] - 2 * hu['L']; Pcr = math.pi ** 2 * E_CFK * I / (LA['knickfaktor_k'] * Lf) ** 2
            knick = max(knick, max(0.0, -N) * GAMMA_KNICK / Pcr)
        kv = det / K[0][0]                                        # vertikale Federsteifigkeit am Systempunkt: 1/(K^-1)_zz (N/mm)
    # ---- 2. seitlich: Motormoment + Kreiselmoment, Rohre als parallele Kragtraeger
    J = 0.0425 * (prop['d_mm'] / 1066.8) ** 4.5 + 0.004
    n_max = sim['schwebe_rpm'] * math.sqrt(max(sim['schub_gewicht'], 1.0)) if sim['schwebefaehig'] else None
    Om = (n_max or 3000) * math.pi / 30
    M_gyro = J * Om * 2.0 * 1000                                  # 2 rad/s Nick-/Rollrate (Nmm)
    M_lat = (Q_MOTOR_MAX * 1000) + M_gyro                         # Koax: Motoren gegenlaeufig, Differenz bis Q_max
    sig_lat = M_lat / (n * W)
    Ls = sum(t['systemlaenge_mm'] for t in g['rohre']) / n
    if k_lat is None: k_lat = n * 3 * E_CFK * I / Ls ** 3        # vertikales Fachwerk/Einrohr: seitlich nur Rohrbiegung
    # ---- 3. Eigenfrequenzen (Ein-Massen-Schwinger am Auslegerende)
    m_rohre = n * A * Ls * RHO_CFK
    m_huelse = 2 * n * RHO_ALU * math.pi * (hu['r_aussen'] ** 2 - hu['r_bohr'] ** 2) * hu['L'] * 1.6
    m_mt = PRU[key]['massen']['motortraeger_je_stueck_kg']
    m_spitze = (2 if koax else 1) * (M_MOTOR + 0.56 * (prop['d_mm'] / 1066.8) ** 2.5) + m_mt + 0.3
    m_eff = m_spitze + 0.24 * m_rohre
    f_v = math.sqrt(kv * 1000 / m_eff) / (2 * math.pi); f_l = math.sqrt(k_lat * 1000 / m_eff) / (2 * math.pi)
    anr = None; frei = None
    if sim['schwebefaehig']:
        n_lo = 0.85 * sim['schwebe_rpm']; b1 = (n_lo / 60, n_max / 60); b2 = (2 * n_lo / 60, 2 * n_max / 60)
        def trifft(f, b): return b[0] * (1 - ABSTAND) <= f <= b[1] * (1 + ABSTAND)
        anr = dict(P1_Hz=[round(x, 1) for x in b1], P2_Hz=[round(x, 1) for x in b2])
        frei = not any(trifft(f, b) for f in (f_v, f_l) for b in (b1, b2))
    # ---- 4. Masse, Abschattung
    t = (od - di) / 2
    m_ausleger = m_rohre + m_huelse
    dl = 1.2 * (od / 1000) * min(prop['d_mm'] / 2000, g['Lr'] / 1000) / (math.pi * (prop['d_mm'] / 2000) ** 2)
    ok = dict(festigkeit=(sig_v + sig_lat) <= SIG_ZUL, knicken=knick <= 1.0, wand=(od / t) <= D_T_MAX and t >= T_MIN,
              frequenz=frei if frei is not None else True, mindestfrequenz=min(f_v, f_l) >= F_MIN)
    return dict(schluessel=key if not raum else key.replace('_V3', '_' + vid), spreizung_mm=round(spreizung, 1), bauweise=bw, propeller=prop['id'], variante=vid, od=od, id=di, wand_mm=t,
                rohre=n, Lr_mm=round(g['Lr'], 1), schub_lastfall_N=round(F, 0), sigma_vertikal_MPa=round(sig_v, 1),
                sigma_quer_MPa=round(sig_lat, 1), ausnutzung_festigkeit=round((sig_v + sig_lat) / SIG_ZUL, 3),
                knick_ausnutzung_gamma15=round(knick, 3), f_vertikal_Hz=round(f_v, 1), f_seitlich_Hz=round(f_l, 1),
                anregung=anr, frequenz_frei=frei, durchbiegung_schweben_mm=round(Fh / kv, 2) if kv else None,
                masse_rohre_kg=round(m_rohre, 3), masse_huelsen_kg=round(m_huelse, 3), masse_ausleger_kg=round(m_ausleger, 3),
                abschattung_anteil=round(dl, 4), schwebefaehig=sim['schwebefaehig'], kriterien=ok, alle_ok=all(ok.values()))


def main():
    rows = []
    for bw in P['bauweisen']:
        for prop in P['propeller']:
            for vid in list(P['varianten']) + ['R3', 'R4']:
                for od, di in KATALOG:
                    if vid != 'V1' and od > 40: continue
                    rows.append(bewerte(bw, prop, vid, od, di))
    # Empfehlung je Konfiguration: leichtester Ausleger, der alle Kriterien erfuellt; Vergleich mit dem D14-Stand
    emp = {}
    for r in rows:
        k = r['schluessel']; e = emp.setdefault(k, dict(schluessel=k, bauweise=r['bauweise'], propeller=r['propeller'], variante=r['variante'],
                                                       schwebefaehig=r['schwebefaehig'], bester=None, d14=None))
        d14 = (P['varianten'][r['variante'] if r['variante'] not in ('R3', 'R4') else 'V2']['rohr_od_mm'], P['varianten'][r['variante'] if r['variante'] not in ('R3', 'R4') else 'V2']['rohr_id_mm'])
        if (r['od'], r['id']) == d14: e['d14'] = r
        if r['alle_ok'] and (e['bester'] is None or r['masse_ausleger_kg'] < e['bester']['masse_ausleger_kg']): e['bester'] = r
    for e in emp.values():
        npos = P['bauweisen'][e['bauweise']]['rotorpositionen']
        if e['bester'] and e['d14']:
            e['masse_delta_kg_gesamt'] = round(npos * (e['bester']['masse_ausleger_kg'] - e['d14']['masse_ausleger_kg']), 2)
    (OUT / 'Rohrstudie.json').write_text(json.dumps(dict(
        annahmen=dict(lastfall=f'Schweben x {LF} g mit max(160 kg, Simulator-Abflugmasse); Knicken mit Abminderung {GAMMA_KNICK}',
                      quer=f'Motormoment {Q_MOTOR_MAX} Nm + Kreiselmoment bei 2 rad/s und Maximaldrehzahl, Rohre als parallele Kragtraeger',
                      frequenz='Ein-Massen-Schwinger am Auslegerende (Motor, Propeller, Motortraeger, Regleranteil); Anregung 1P/2P von 0,85 x Schwebedrehzahl bis Maximaldrehzahl, Abstand +-15 %',
                      material=f'E_CFK {E_CFK} MPa, zulaessig {SIG_ZUL} MPa (Parameter D14), Dichte 1,55 g/cm3; Huelsen Alu wie D14 skaliert',
                      wand=f'D/t <= {D_T_MAX}, t >= {T_MIN} mm', katalog=KATALOG),
        empfehlungen=list(emp.values()), alle=rows), ensure_ascii=False, indent=1, default=lambda o: o.item()))
    with open(OUT / 'Rohrstudie.csv', 'w', newline='') as fh:
        w = csv.writer(fh, delimiter=';'); sp = [k for k in rows[0] if k not in ('anregung', 'kriterien')]
        w.writerow(sp + ['krit_festigkeit', 'krit_knicken', 'krit_wand', 'krit_frequenz', 'krit_mindestfrequenz'])
        for r in rows: w.writerow([r[k] for k in sp] + [r['kriterien'][k] for k in ('festigkeit', 'knicken', 'wand', 'frequenz', 'mindestfrequenz')])
    return rows, emp


if __name__ == '__main__':
    rows, emp = main()
    print(len(rows), 'Bewertungen')
