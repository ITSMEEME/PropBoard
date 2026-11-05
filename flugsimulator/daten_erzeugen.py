"""Erzeugt modelle.js fuer den globalen Flugsimulator aus den D14-Ausgaben.

Quellen (unveraendert gelesen):
  ../multirotor_d14/Ausgabe/Auslegung.json   Geometrie, Statik, Ausruestung
  ../multirotor_d14/Ausgabe/Pruefung.json    CAD-Massen, Kollisionsstatus
  ../quad_r380_d13/Ausgabe/Antrieb_Annahmen.json  CT/CP-Referenz (NS52x20, ungeprueft fuer HEP-S)
  ../kreis_r04/mn1330_p14/Motor_Daten.json   MN1330-Pruefstandstabelle (19 Punkte)
Die Motorkonstanten (Kt, R, I0) werden hier gegen die 19 Pruefpunkte angepasst.
"""
import json, math, hashlib, os, re

H = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(H)
def lade(p): return json.load(open(os.path.join(R, p), encoding='utf-8'))

AUS = lade('multirotor_d14/Ausgabe/Auslegung.json')
PRU = lade('multirotor_d14/Ausgabe/Pruefung.json')
PAR = lade('multirotor_d14/parameter.json')
ANT = lade('quad_r380_d13/Ausgabe/Antrieb_Annahmen.json')
MOT = lade('kreis_r04/mn1330_p14/Motor_Daten.json')
pru = {c['schluessel']: c for c in PRU['konfigurationen']}

# ---------------------------------------------------------------- Motorfit (Kt, R, I0 gegen Pruefstandspunkte)
ETA_ESC = 0.97
D_MAX = 0.98   # hoechste Aussteuerung des Reglers bei Vollgas
def motorfit(pts, kv, rmin=0.005, voll=(), polpaare=21):
    """pts: (rpm, Drehmoment Nm, elektrische Eingangsleistung W) -> k_t (+-10 % um KV), R (>= Datenblatt), I0 aus der Leistung.
    voll: Vollgaspunkte (U, rpm, Drehmoment) -> Phaseninduktivitaet L aus der Spannungsgrenze
    U_max^2 = (k_t w + R I)^2 + (p w L I)^2 (Blindspannung bei hoher elektrischer Frequenz)."""
    kt0 = 60 / (2 * math.pi * kv)
    def fehler(kt, r, i0):
        return sum((((kt * n * math.pi / 30 + r * (q / kt + i0)) * (q / kt + i0) / ETA_ESC - p) / p) ** 2 for n, q, p in pts)
    best = None
    for kt in [kt0 * (0.90 + 0.0025 * k) for k in range(81)]:
        for r in [rmin + 0.0005 * k for k in range(100)]:
            for i0 in [0.25 * k for k in range(40)]:
                e = fehler(kt, r, i0)
                if best is None or e < best[0]: best = (e, kt, r, i0)
    e, kt, r, i0 = best
    Ls = []
    for u, n, q in voll:
        w = n * math.pi / 30; i = q / kt + i0; ur = kt * w + r * i
        Ls.append(math.sqrt(max((D_MAX * u) ** 2 - ur ** 2, 0)) / (polpaare * w * i))
    L = sum(Ls) / len(Ls) if Ls else 0.0
    fit = [dict(rpm=n, drehmoment_Nm=q, gemessen_W=p, modell_W=round((kt * n * math.pi / 30 + r * (q / kt + i0)) * (q / kt + i0) / ETA_ESC, 1)) for n, q, p in pts]
    rms_p = math.sqrt(sum((f['modell_W'] / f['gemessen_W'] - 1) ** 2 for f in fit) / len(fit))
    return kt, r, i0, rms_p, fit, L

pts = MOT['test']['points']
KT, RPH, I0, rms, fit, LPH = motorfit([(p['rpm'], p['torque_Nm'], p['input_power_W']) for p in pts], MOT['basic']['kv'], MOT['basic']['phase_to_phase_resistance_ohm'],
    [(p['voltage_V'], p['rpm'], p['torque_Nm']) for p in pts if p['throttle_percent'] >= 100])
for f_, p in zip(fit, pts): f_['schub_N'] = round(p['thrust_N'], 1)
ONL = json.load(open(os.path.join(H, 'Quellen/Motoren_Online.json'), encoding='utf-8'))
motoren = {'MN1330_KV40': dict(typ='MN1330 KV40', hersteller='(Bestand D05–D14)', masse_kg=MOT['basic']['mass_including_leads_kg'], kv=MOT['basic']['kv'], kt_fit=KT, r_phase_fit=RPH, i0_fit=I0,
    fit_rms_anteil=round(rms, 4), fit_punkte=fit, L_phase=LPH, polpaare=21, r_datenblatt=MOT['basic']['phase_to_phase_resistance_ohm'], max_strom_A=MOT['basic']['max_current_A'],
    abmessung_mm=[150, 65], max_schub_kg=MOT['basic']['max_thrust_claim_kg'], nennleistung_W=MOT['basic']['max_power_180s_W'], nennleistung_hinweis='3400 W fuer 180 s (Bezugsseite ungeklaert)', quellen=['quad_r380_d05/Quellen/MN1330 (Nutzertabelle)'], datenlage='19 Pruefpunkte NS52x20')}
for key, m in ONL['motoren'].items():
    e = dict(m); e.pop('punkte', None)
    if m['punkte']:
        kt, r, i0, rr, ff, L = motorfit([(p['rpm'], p['drehmoment_Nm'], p['leistung_W']) for p in m['punkte']], m['kv'], m['r_datenblatt'] or 0.005,
            [(p['U'], p['rpm'], p['drehmoment_Nm']) for p in m['punkte'] if p['gas'] >= 100])
        e.update(kt_fit=kt, r_phase_fit=r, i0_fit=i0, fit_rms_anteil=round(rr, 4), fit_punkte=ff, L_phase=L, polpaare=21, datenlage=f"{len(m['punkte'])} Herstellerpunkte ({m['propeller_test']})")
        if e['r_datenblatt'] is None: e['r_datenblatt'] = r / 2
    else:
        rds = 0.015
        e.update(kt_fit=60 / (2 * math.pi * m['kv']), r_phase_fit=rds + (RPH - MOT['basic']['phase_to_phase_resistance_ohm']), i0_fit=round(I0 * 3.6 / 3.4, 2), fit_rms_anteil=None, fit_punkte=[], L_phase=LPH*(21/31), polpaare=31,
                 r_datenblatt=rds, datenlage='keine Messtabelle; R und I0 angenommen')
    motoren[key] = e
    print(f"{key}: Kt={e['kt_fit']:.3f} (KV-Wert {60/(2*math.pi*m['kv']):.3f}) R={e['r_phase_fit']*1000:.1f} mOhm I0={e['i0_fit']:.2f} A L={e['L_phase']*1e6:.1f} uH RMS={e['fit_rms_anteil']}")

# ---------------------------------------------------------------- je Konfiguration
def steigung(label):
    m = re.search(r'(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)', label)
    return float(m.group(1)), float(m.group(2))

def armgrenze(st):
    """Zulaessiger Schub je Ausleger [N] aus dem Screening: Lastfall / hoechste Ausnutzung (linear)."""
    if 'staebe' in st:
        u = max(max(s['cfk_ausnutzung'], s['knick_ausnutzung'], s['alu_strebe_knick_ausnutzung']) for s in st['staebe'])
        art = 'Stabwerk (Knicken/CFK/Alu-Strebe)'
    else:
        u = st['ausnutzung']; art = 'Kragarm Biegung'
    return st['schub_je_ausleger_N'] / max(u, 1e-6), u, art

modelle = {}
for c in AUS['konfigurationen']:
    k = c['schluessel']; q = pru[k]; m = q['massen']; a = c['ausruestung']
    d_in, p_in = steigung(c['propeller_label'])
    bw = c['bauweise']; koax = c['rotor_unten'] is not None
    z_oben = (c['rotor_oben_z_mm'] - c['rotor_huelle_halb_mm']) / 1000
    z_unten = c['rotor_unten']['rotorebene_z_mm'] / 1000 if koax else None
    tlim, u, art = armgrenze(c['statik'])
    arme = []; rotoren = []
    for mo in c['motoren']:
        x, y = mo['xy'][0] / 1000, mo['xy'][1] / 1000
        arme.append(dict(nr=mo['nr'], xy=[x, y], grenze_N=round(tlim, 1)))
        s = 1 if mo['drehrichtung'] == 'CCW' else -1
        rotoren.append(dict(arm=len(arme) - 1, xy=[x, y], z=round(z_oben, 4), dreh=s, lage='oben', nr=mo['nr'], winkel=mo['winkel_grad']))
        if koax:
            rotoren.append(dict(arm=len(arme) - 1, xy=[x, y], z=round(z_unten, 4), dreh=-s, lage='unten', nr=mo['nr'] + len(c['motoren']), winkel=mo['winkel_grad']))
    # Abschattung (Download) je Rotor: Auslegerrohr unter der Scheibe + Motortraeger + Regler
    od = c['arm']['huelse']['od'] / 1000                     # inkl. konfigurationsspezifischer Rohrgroesse
    Rr = c['rotor_d_mm'] / 2000
    reg = a['regler']
    regler_unter = reg['abstand_reglerende_motorachse_mm'] / 1000 < Rr
    A_b = min(Rr, c['arm']['Lr'] / 1000) * od + 0.008 + (0.146 * 0.074 if regler_unter else 0.0)
    f = a['fussschlitten']; lg = a['landegestell']
    st = c['statik_ausruestung']
    modelle[k] = dict(
        schluessel=k, bauweise=bw, bauweise_label=PAR['bauweisen'][bw]['label'], propeller=c['propeller'], propeller_label=c['propeller_label'],
        variante=c['variante'], variante_label=PAR['varianten'][c['variante']]['titel'],
        d_m=c['rotor_d_mm'] / 1000, d_in=d_in, steigung_in=p_in, motorradius_m=c['motorradius_mm'] / 1000,
        rotoren=rotoren, arme=arme, arm_grenze_N=round(tlim, 1), arm_ausnutzung_3g=round(u, 3), arm_nachweis=art,
        abschattung_m2=round(A_b, 5), regler_unter_scheibe=regler_unter,
        rahmen=dict(seiten=c['rahmen']['seiten'], umkreis_m=c['rahmen']['umkreis'] / 1000, apothem_m=c['rahmen']['apothem'] / 1000),
        fuesse=[[p[0] / 1000, p[1] / 1000, p[2] / 1000] for p in lg['fuesse']], boden_z_m=lg['boden_z_mm'] / 1000,
        fuss_grenze_N=st['landung']['fusslast_N'], kippkante_m=lg['kippkante_mm'] / 1000,
        plattform_z_m=(f['schiene_z_mm'] + 18) / 1000, fuss_x_m=max(f['fuss_x_mm'], f['fuss_x_min_mm']) / 1000, schiene_y_m=f['schiene_y_mm'] / 1000,
        bock_x_m=f['bock_x_mm'] / 1000,
        unterer_rotor_boden_m=(lg['unterer_rotor_ueber_boden_mm'] / 1000 if lg['unterer_rotor_ueber_boden_mm'] is not None else None),
        massen=dict(struktur_kg=m['struktur_gesamt_kg'], ausruestung_kg=m['ausruestung']['ausruestung_gesamt_ohne_regler_kg'],
                    regler_kg=m['ausruestung']['regler_katalog_kg'], regler_anzahl=m['ausruestung']['regler_anzahl'],
                    motortraeger_kg=m['motortraeger_je_stueck_kg'] * m['motortraeger_anzahl'], arme_kg=m['auslegerrohre_je_ausleger_kg'] * len(c['motoren'])),
        regler_abstand_m=reg['s_mitte_mm'] / 1000,
        pruefungen=c['pruefungen'], kollisionsfrei=q['kollisionsfrei'],
    )

daten = dict(
    erzeugt_aus=dict(
        auslegung_sha256=hashlib.sha256(open(os.path.join(R, 'multirotor_d14/Ausgabe/Auslegung.json'), 'rb').read()).hexdigest()[:16],
        geometrie_signatur=PRU['geometrie_signatur']),
    standard=PAR['standard'],
    motor=motoren['MN1330_KV40'], motoren=motoren, standard_motor='MN1330_KV40',
    akkus=json.load(open(os.path.join(H, 'Quellen/Akkus_Online.json'), encoding='utf-8')), standard_akku='LIPO_TATTU22',
    regler=dict(typ='V200A 24S', masse_kg=0.748, dauer_A=100, spitze_A=200, wirkungsgrad=ETA_ESC),
    antrieb=dict(ct_ref=ANT['reference_CT'], cp_ref=ANT['reference_CP'], d_ref_in=ANT['reference_diameter_in'], p_ref_in=ANT['reference_pitch_in'],
                 quelle=ANT['method']),
    modelle=modelle,
)
with open(os.path.join(H, 'modelle.js'), 'w', encoding='utf-8') as fh:
    fh.write('/* erzeugt von daten_erzeugen.py – nicht von Hand aendern */\n')
    fh.write('globalThis.SIM_DATEN=' + json.dumps(daten, ensure_ascii=False, separators=(',', ':')) + ';\n')
print(f'{len(modelle)} Modelle; MN1330 Kt={KT:.3f} Nm/A R={RPH*1000:.1f} mOhm I0={I0:.2f} A L={LPH*1e6:.1f} uH, RMS {rms*100:.1f} %')
