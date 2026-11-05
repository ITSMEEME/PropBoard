"""DRRF-K01: analytische Konzeptauslegung eines Dual-Rotor-Radialfluss-Motors (reines Python).

Drei Topologien werden mit demselben Modell im selben Bauraum (D14-Motorhuelle Ø150 x 66 mm) bewertet:
  DR-NS  Dual-Rotor, Fluss geht radial durch jochlose Statorzaehne (Zahnspulen), aussen und innen je ein Magnetring
  DR-NN  Dual-Rotor, Statorjoch mit Ringwicklung (toroidal): jede Windung ist im aeusseren UND inneren Luftspalt aktiv
  REF    konventioneller Aussenlaeufer mit Zahnspulen (Bauart MN1330) als Vergleich
Modell: Magnetkreis mit Luftspalt, Carterfaktor und Streuung; Grundwelle der Luftspaltinduktion; Drehmomentkonstante aus
Flussverkettung; Zahn-, Joch- und Rueckschlussbreiten aus zulaessiger Induktion; Nutflaeche, Fuellfaktor, Windungslaenge,
Kupfer- und Eisenverluste; Massen aller aktiven und tragenden Teile. Optimiert wird die Masse unter Strom-, Spannungs-,
Bauraum- und Wirkungsgradgrenzen. Ergebnis: Ausgabe/Auslegung.json
"""
import json, math, itertools
from pathlib import Path

H = Path(__file__).resolve().parent
P = json.loads((H / 'parameter.json').read_text())
AN, MA, GF, TH, OP = P['anforderung'], P['material'], P['geometrie_fest'], P['thermik'], P['optimierung']
PI = math.pi


def br():
    return MA['Br_20_T'] * (1 + MA['Br_tk_proK'] * (MA['magnet_temp_C'] - 20))


def b_luftspalt(hm, magnete_in_reihe=1):
    """Luftspaltinduktion (Mittelwert unter dem Pol): Magnete und Luftspalte im Kreis in Reihe."""
    g = GF['luftspalt_mm'] * GF['carter_faktor']
    return br() * hm / (hm + MA['mu_r_magnet'] * g) * GF['streufaktor']


def grundwelle(b):
    return 4 / PI * b * math.sin(GF['polbedeckung'] * PI / 2)


def rho_cu():
    return MA['kupfer_rho_ohm_m_20C'] * (1 + MA['kupfer_tk'] * (MA['kupfer_temp_C'] - 20))


def hoehe(L):
    return GF['boden_mm'] + GF['spalt_boden_mm'] + L + 2 * GF['wickelkopf_mm'] + 2.0 + GF['deckel_mm'] + GF['nabe_aufbau_mm']


def nut(r_aussen, r_innen, w_t, schuhe):
    """Nutflaeche zwischen zwei Zaehnen im Ring r_innen..r_aussen; schuhe: Anzahl Zahnschuhseiten (1 oder 2)."""
    Ns = GF['nuten']; hs = r_aussen - r_innen; h_sh = GF['zahnschuh_hoehe_mm']
    ring = PI * (r_aussen ** 2 - r_innen ** 2) / Ns
    zahn = w_t * (hs - schuhe * h_sh)
    schuh = 0.0
    for r in ([r_aussen, r_innen] if schuhe == 2 else [r_aussen]):
        schuh += max(2 * PI * r / Ns - w_t - GF['nutschlitz_mm'], 0) * h_sh
    b_min = 2 * PI * r_innen / Ns - w_t
    return ring - zahn - schuh, b_min


def bewerte(topo, L, hs, hm):
    """Geometrie, Massen und Motorkonstanten einer Topologie (ohne Windungszahl). None bei ungueltiger Geometrie."""
    Ns, p = GF['nuten'], GF['pole'] // 2
    g, a_p = GF['luftspalt_mm'], GF['polbedeckung']
    r0 = AN['bauraum_d_mm'] / 2
    B = b_luftspalt(hm)
    def rueck(r, Bg):                       # Rueckschluss traegt den halben Polfluss
        return max(GF['rueckschluss_min_mm'], Bg * (PI * r / p) * a_p / (2 * MA['B_rueckschluss_max_T']))
    d = dict(topologie=topo, L=L, hs=hs, hm=hm, B_luftspalt_T=B)
    if topo == 'REF':
        t_bo = rueck(r0, B); r_m_o = r0 - t_bo; r_m_i = r_m_o - hm; r_so = r_m_i - g
        w_t = B * (2 * PI * r_so / Ns) / MA['B_zahn_max_T']
        t_y = B * (PI * r_so / p) * a_p / (2 * MA['B_joch_max_T'])
        r_nut_i = r_so - hs; r_si = r_nut_i - t_y
        if r_si < GF['innen_freiraum_r_mm']: return None
        A_s, b_min = nut(r_so, r_nut_i, w_t, 1)
        if A_s <= 5 or b_min < 1.5: return None
        A_cu_spule = MA['fuellfaktor'] * A_s / 2
        c = A_s / (2 * hs)
        l_w = 2 * L + 2 * w_t + PI * c
        psi = B * 1.0; Kt_je_N = 3 * GF['wicklungsfaktor'] * grundwelle(B) * (r_so + g / 2) * L * 1e-6
        eisen = (Ns * w_t * (hs - GF['zahnschuh_hoehe_mm']) + PI * (r_nut_i ** 2 - r_si ** 2) + Ns * (2 * PI * r_so / Ns - GF['nutschlitz_mm']) * GF['zahnschuh_hoehe_mm']) * L
        m_mag = 2 * PI * (r_m_o - hm / 2) * hm * a_p * (L + 2 * GF['magnet_ueberstand_mm']) * MA['rho_magnet']
        m_rs = 2 * PI * (r0 - t_bo / 2) * t_bo * (L + 2 * GF['magnet_ueberstand_mm']) * MA['rho_stahl']
        traeger = PI * (r_si ** 2 - 12 ** 2) * 5 * 0.5 * MA['rho_alu']          # Statornabe (Speichenscheibe)
        d.update(r=dict(rueckschluss_aussen=[r0 - t_bo, r0], magnet_aussen=[r_m_i, r_m_o], stator=[r_si, r_so], nutgrund=r_nut_i),
                 w_t=w_t, t_y=t_y, t_bo=t_bo, nut_mm2=A_s, f_eisen_B=max(MA['B_zahn_max_T'], MA['B_joch_max_T']))
        r_stat_m = (r_so + r_si) / 2
    elif topo == 'DR-NS':
        t_bo = rueck(r0, B); r_mo_o = r0 - t_bo; r_mo_i = r_mo_o - hm; r_so = r_mo_i - g
        r_si = r_so - hs; r_mi_o = r_si - g; r_mi_i = r_mi_o - hm
        B_i = B * r_so / r_si                                     # Flusskontinuitaet im Zahn
        t_bi = rueck(r_mi_i, B_i); r_bi_i = r_mi_i - t_bi
        if r_bi_i < GF['innen_freiraum_r_mm']: return None
        r_m = (r_so + r_si) / 2
        w_t = B * (2 * PI * r_so / Ns) / MA['B_zahn_max_T']       # Zahn fuehrt den ganzen Polfluss radial durch
        A_s, b_min = nut(r_so, r_si, w_t, 2)
        if A_s <= 5 or b_min < 1.5: return None
        A_cu_spule = MA['fuellfaktor'] * A_s / 2
        c = A_s / (2 * hs)
        l_w = 2 * L + 2 * w_t + PI * c
        Kt_je_N = 3 * GF['wicklungsfaktor'] * grundwelle(B) * (r_so + g / 2) * L * 1e-6
        eisen = (Ns * w_t * (hs - 2 * GF['zahnschuh_hoehe_mm']) + sum(Ns * max(2 * PI * r / Ns - GF['nutschlitz_mm'], 0) * GF['zahnschuh_hoehe_mm'] for r in (r_so, r_si))) * L
        m_mag = (2 * PI * (r_mo_o - hm / 2) + 2 * PI * (r_mi_o - hm / 2)) * hm * a_p * (L + 2 * GF['magnet_ueberstand_mm']) * MA['rho_magnet']
        m_rs = (2 * PI * (r0 - t_bo / 2) * t_bo + 2 * PI * (r_mi_i - t_bi / 2) * t_bi) * (L + 2 * GF['magnet_ueberstand_mm']) * MA['rho_stahl']
        traeger = 2 * PI * r_m * 2.5 * 6 * MA['rho_alu']                           # Tragring unter dem Stator
        d.update(r=dict(rueckschluss_aussen=[r0 - t_bo, r0], magnet_aussen=[r_mo_i, r_mo_o], stator=[r_si, r_so],
                        magnet_innen=[r_mi_i, r_mi_o], rueckschluss_innen=[r_bi_i, r_mi_i]),
                 w_t=w_t, t_y=0.0, t_bo=t_bo, t_bi=t_bi, nut_mm2=A_s, B_innen_T=B_i, f_eisen_B=MA['B_zahn_max_T'])
        r_stat_m = r_m
    elif topo == 'DR-NN':
        t_bo = rueck(r0, B); r_mo_o = r0 - t_bo; r_mo_i = r_mo_o - hm; r_so = r_mo_i - g
        hso = hsi = hs / 2
        w_to = B * (2 * PI * r_so / Ns) / MA['B_zahn_max_T']
        t_y_vor = None
        # Joch traegt die Polfluesse beider Rotoren (gleichsinnig, N-N)
        r_no = r_so - hso
        for _ in range(3):
            r_ji = r_no - (t_y_vor or 6.0); r_si = r_ji - hsi
            t_y = B * ((PI * r_so / p) + (PI * r_si / p)) * a_p / (2 * MA['B_joch_max_T'])
            t_y_vor = t_y
        r_ji = r_no - t_y; r_si = r_ji - hsi
        w_ti = B * (2 * PI * r_si / Ns) / MA['B_zahn_max_T']
        r_mi_o = r_si - g; r_mi_i = r_mi_o - hm; t_bi = rueck(r_mi_i, B); r_bi_i = r_mi_i - t_bi
        if r_bi_i < GF['innen_freiraum_r_mm']: return None
        A_so, b1 = nut(r_so, r_no, w_to, 1)
        # innere Nuten oeffnen nach innen: Zahnschuh an r_si
        Ns_ = GF['nuten']; ring_i = PI * (r_ji ** 2 - r_si ** 2) / Ns_
        A_si = ring_i - w_ti * (hsi - GF['zahnschuh_hoehe_mm']) - max(2 * PI * r_si / Ns_ - w_ti - GF['nutschlitz_mm'], 0) * GF['zahnschuh_hoehe_mm']
        b2 = 2 * PI * r_si / Ns_ - w_ti
        A_s = min(A_so, A_si)
        if A_s <= 5 or b1 < 1.5 or b2 < 1.5: return None
        A_cu_spule = MA['fuellfaktor'] * A_s            # Ringspule fuellt je eine Aussen- und eine Innennut
        l_w = 2 * L + 2 * (t_y + hso / 2 + hsi / 2) + 6.0
        Kt_je_N = 3 * GF['wicklungsfaktor'] * grundwelle(B) * ((r_so + g / 2) + (r_si - g / 2)) * L * 1e-6
        eisen = (Ns * (w_to * (hso - GF['zahnschuh_hoehe_mm']) + w_ti * (hsi - GF['zahnschuh_hoehe_mm'])) + PI * (r_no ** 2 - r_ji ** 2)) * L
        m_mag = (2 * PI * (r_mo_o - hm / 2) + 2 * PI * (r_mi_o - hm / 2)) * hm * a_p * (L + 2 * GF['magnet_ueberstand_mm']) * MA['rho_magnet']
        m_rs = (2 * PI * (r0 - t_bo / 2) * t_bo + 2 * PI * (r_mi_i - t_bi / 2) * t_bi) * (L + 2 * GF['magnet_ueberstand_mm']) * MA['rho_stahl']
        r_m = (r_so + r_si) / 2
        traeger = 2 * PI * r_m * 2.5 * 6 * MA['rho_alu']
        d.update(r=dict(rueckschluss_aussen=[r0 - t_bo, r0], magnet_aussen=[r_mo_i, r_mo_o], stator=[r_si, r_so], joch=[r_ji, r_no],
                        magnet_innen=[r_mi_i, r_mi_o], rueckschluss_innen=[r_bi_i, r_mi_i]),
                 w_t=w_to, w_t_innen=w_ti, t_y=t_y, t_bo=t_bo, t_bi=t_bi, nut_mm2=A_s, f_eisen_B=max(MA['B_zahn_max_T'], MA['B_joch_max_T']))
        r_stat_m = r_m
    if hoehe(L) > AN['bauraum_h_mm'] + 1e-6:
        return None
    m_eisen = eisen * MA['rho_blech']
    m_cu = Ns * A_cu_spule * l_w * MA['rho_kupfer']
    m_verguss = Ns * (1 - MA['fuellfaktor']) * (A_s if topo != 'DR-NN' else 2 * A_s) * (L + 2 * GF['wickelkopf_mm']) * MA['rho_verguss'] * 0.8
    deckel = PI * (r0 ** 2 - 22 ** 2) * GF['deckel_mm'] * 0.55 * MA['rho_alu']        # Rotordeckel mit Lueftungsfenstern
    huelse = 2 * PI * r0 * 1.2 * (hoehe(L) - L - GF['deckel_mm'] - GF['boden_mm']) * MA['rho_alu']   # Aussenhuelse ausserhalb der Aktivzone
    boden = PI * (r0 ** 2) * GF['boden_mm'] * 0.5 * MA['rho_alu']                     # Statortraeger-Boden mit Kuehlfenstern
    fest = 0.14 + 0.08 + 0.06 + 0.08          # 2 x 6004, Achse (hohl), Rotornabe, Schrauben/Leitungen
    massen = dict(eisen=m_eisen, magnete=m_mag, rueckschluss=m_rs, kupfer=m_cu, verguss=m_verguss, rotordeckel=deckel,
                  aussenhuelse=huelse, statortraeger=boden + traeger, lager_achse_nabe=fest)
    d.update(massen_kg={k: round(v, 4) for k, v in massen.items()}, masse_kg=sum(massen.values()),
             A_cu_spule_mm2=A_cu_spule, l_windung_mm=l_w, Kt_je_windung=Kt_je_N, m_eisen_kg=m_eisen, r_stat_m=r_stat_m,
             hoehe_mm=hoehe(L))
    return d


def wicklung(d, a, Nc):
    """Elektrische Kennwerte fuer a parallele Zweige und Nc Windungen je Spule."""
    Ns = GF['nuten']
    N_ph = Ns / 3 / a * Nc                              # Reihenwindungen je Phase und Zweig
    Kt = d['Kt_je_windung'] * N_ph                       # Nm je A (Phasenscheitelwert)
    a_w = d['A_cu_spule_mm2'] / Nc                       # Leiterquerschnitt je Windung
    R_ph = rho_cu() * (N_ph * d['l_windung_mm'] * 1e-3) / (a_w * 1e-6) / a
    return dict(N_ph=N_ph, Kt=Kt, a_w=a_w, R_ph=R_ph, a=a, Nc=Nc)


def betriebspunkt(d, w, T, n):
    om = n * PI / 30
    I_pk = T / w['Kt']; I_rms = I_pk / math.sqrt(2)
    J = I_rms / w['a'] / w['a_w']
    P_cu = 3 * I_rms ** 2 * w['R_ph']
    f = GF['pole'] / 2 * n / 60
    P_fe = MA['eisenverlust_W_kg_1T_1kHz'] * d['m_eisen_kg'] * (f / 1000) ** 1.5 * d['f_eisen_B'] ** 2
    P_mech = T * om
    E_ph = 2 / 3 * w['Kt'] * om                          # Phasenscheitel der Gegen-EMK
    U_ll = math.sqrt(3) * math.hypot(E_ph + I_pk * w['R_ph'], 0.0)
    return dict(I_pk=I_pk, I_rms=I_rms, J=J, P_cu=P_cu, P_fe=P_fe, P_mech=P_mech, eta=P_mech / (P_mech + P_cu + P_fe),
                U_ll_pk=U_ll, f_el=f)


def optimiere():
    ergebnisse = {}
    for topo in ('DR-NS', 'DR-NN', 'REF'):
        best = None; alle = 0; naechst = None
        for L, hs, hm in itertools.product(OP['aktive_laenge_mm'], OP['nut_tiefe_mm'], OP['magnet_dicke_mm']):
            d = bewerte(topo, L, hs, hm)
            if not d: continue
            for a in OP['parallelzweige']:
                if (GF['nuten'] // 3) % a: continue
                for Nc in range(60, 0, -1):
                    w = wicklung(d, a, Nc)
                    sp = betriebspunkt(d, w, AN['spitze_drehmoment_Nm'], AN['spitze_drehzahl_min'])
                    if sp['U_ll_pk'] > AN['aussteuerung_max'] * AN['busspannung_min_V']: continue
                    da = betriebspunkt(d, w, AN['dauer_drehmoment_Nm'], AN['dauer_drehzahl_min'])
                    alle += 1
                    naechst_kand = (da['J'], d, w, da, sp)
                    if naechst is None or naechst_kand[0] < naechst[0]: naechst = naechst_kand
                    if (da['J'] > TH['J_dauer_max_A_mm2'] or sp['J'] > TH['J_spitze_max_A_mm2'] or da['eta'] < 0.93
                            or da['I_rms'] > AN['regler_dauer_A_eff'] or sp['I_rms'] > AN['regler_spitze_A_eff']):
                        break
                    # Ziel: Masse; bei gleicher Masse (1 g) hoeherer Wirkungsgrad
                    kand = (round(d['masse_kg'], 3) - 1e-4 * da['eta'], d, w, da, sp)
                    if best is None or kand[0] < best[0]: best = kand
                    break                                    # groesste zulaessige Windungszahl je (L, hs, hm, a)
        ergebnisse[topo] = (best, alle, naechst)
    return ergebnisse


def bericht(best):
    m, d, w, da, sp = best
    A_th = 2 * (2 * PI * d['r_stat_m'] * (d['L'] + 2 * GF['wickelkopf_mm'])) * 1e-6
    dT = (da['P_cu'] + da['P_fe']) / (TH['waermeleitwert_W_K_je_m2'] * A_th)
    kv = 60 / (2 * PI) / (w['Kt'] / 1.5 * math.sqrt(3))        # U/min je Volt (Strang-Strang-Scheitel)
    return dict(topologie=d['topologie'], aktive_laenge_mm=d['L'], nut_tiefe_mm=d['hs'], magnet_dicke_mm=d['hm'],
                radien_mm={k: [round(x, 2) for x in v] if isinstance(v, list) else round(v, 2) for k, v in d['r'].items()},
                zahnbreite_mm=round(d['w_t'], 2), zahnbreite_innen_mm=round(d.get('w_t_innen', d['w_t']), 2), jochdicke_mm=round(d['t_y'], 2), nutflaeche_mm2=round(d['nut_mm2'], 1),
                luftspaltinduktion_T=round(d['B_luftspalt_T'], 3), hoehe_mm=round(d['hoehe_mm'], 1),
                masse_kg=round(d['masse_kg'], 3), massen_kg=d['massen_kg'],
                wicklung=dict(nuten=GF['nuten'], pole=GF['pole'], parallelzweige=w['a'], windungen_je_spule=w['Nc'],
                              leiterquerschnitt_mm2=round(w['a_w'], 3), R_phase_mOhm=round(w['R_ph'] * 1000, 2),
                              Kt_Nm_je_A_scheitel=round(w['Kt'], 4), kv_U_min_V=round(kv, 1), windungslaenge_mm=round(d['l_windung_mm'], 1)),
                dauerpunkt=dict(drehmoment_Nm=AN['dauer_drehmoment_Nm'], drehzahl=AN['dauer_drehzahl_min'], **{k: round(v, 3) for k, v in da.items()},
                                waermeabgabe_dT_K=round(dT, 1)),
                spitzenpunkt=dict(drehmoment_Nm=AN['spitze_drehmoment_Nm'], drehzahl=AN['spitze_drehzahl_min'], **{k: round(v, 3) for k, v in sp.items()}),
                drehmomentdichte_Nm_kg=round(AN['dauer_drehmoment_Nm'] / d['masse_kg'], 2))


if __name__ == '__main__':
    erg = optimiere()
    out = dict(revision=P['revision'], anforderung=AN, topologien={})
    for topo, (best, n, naechst) in erg.items():
        if best is None:
            nb = bericht(naechst) if naechst else None
            out['topologien'][topo] = dict(gefunden=False, gepruefte_wicklungen=n, naechste_loesung=nb)
            print(topo, 'keine zulaessige Loesung; beste Stromdichte im Dauerpunkt', nb and nb['dauerpunkt']['J'], 'A/mm2 bei', nb and nb['masse_kg'], 'kg'); continue
        b = bericht(best); b['gepruefte_wicklungen'] = n; out['topologien'][topo] = b
        print(f"{topo:6s} {b['masse_kg']:.3f} kg  L={b['aktive_laenge_mm']} hs={b['nut_tiefe_mm']} hm={b['magnet_dicke_mm']}  "
              f"B={b['luftspaltinduktion_T']} T  Kt={b['wicklung']['Kt_Nm_je_A_scheitel']}  R={b['wicklung']['R_phase_mOhm']} mOhm  "
              f"Dauer: J={b['dauerpunkt']['J']:.1f} eta={b['dauerpunkt']['eta']:.3f} Pcu={b['dauerpunkt']['P_cu']:.0f} Pfe={b['dauerpunkt']['P_fe']:.0f} W  "
              f"Spitze J={b['spitzenpunkt']['J']:.1f}  {b['drehmomentdichte_Nm_kg']} Nm/kg")
    dr = {k: v for k, v in out['topologien'].items() if k != 'REF' and v.get('masse_kg')}
    for k, v in out['topologien'].items(): v['gefunden'] = bool(v.get('masse_kg'))
    out['gewaehlt'] = min(dr, key=lambda k: dr[k]['masse_kg']) if dr else None
    (H / 'Ausgabe').mkdir(exist_ok=True)
    (H / 'Ausgabe' / 'Auslegung.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
    (H / 'Ausgabe' / 'auslegung.js').write_text('window.DRRF_VERGLEICH=' + json.dumps(out['topologien'], ensure_ascii=False) + ';\n')
    print('gewaehlt:', out['gewaehlt'])
