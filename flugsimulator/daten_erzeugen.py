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

# ---------------------------------------------------------------- Motorfit
ETA_ESC = 0.97
pts = MOT['test']['points']
def fehler(kt, r, i0):
    s = 0.0
    for p in pts:
        w = p['rpm'] * math.pi / 30; i = p['torque_Nm'] / kt + i0
        pin = (kt * w + r * i) * i / ETA_ESC
        s += ((pin - p['input_power_W']) / p['input_power_W']) ** 2
    return s
best = None
for kt in [0.200 + 0.002 * k for k in range(30)]:
    for r in [0.010 + 0.001 * k for k in range(40)]:
        for i0 in [1.0 * k for k in range(12)]:
            e = fehler(kt, r, i0)
            if best is None or e < best[0]: best = (e, kt, r, i0)
e, KT, RPH, I0 = best
rms = math.sqrt(e / len(pts))
fit = []
for p in pts:
    w = p['rpm'] * math.pi / 30; i = p['torque_Nm'] / KT + I0
    fit.append(dict(rpm=p['rpm'], drehmoment_Nm=p['torque_Nm'], gemessen_W=p['input_power_W'], modell_W=round((KT * w + RPH * i) * i / ETA_ESC, 1),
                    schub_N=round(p['thrust_N'], 1)))

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
    od = PAR['varianten'][c['variante']]['rohr_od_mm'] / 1000
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
    motor=dict(typ='MN1330 KV40', masse_kg=MOT['basic']['mass_including_leads_kg'], kv=MOT['basic']['kv'], kt_fit=KT, r_phase_fit=RPH, i0_fit=I0,
               fit_rms_anteil=round(rms, 4), fit_punkte=fit, r_datenblatt=MOT['basic']['phase_to_phase_resistance_ohm'],
               max_strom_A=MOT['basic']['max_current_A'], max_drehmoment_gemessen_Nm=MOT['maxima']['recorded_torque_Nm'],
               max_drehzahl_gemessen=MOT['maxima']['recorded_rpm'], leistung_180s_W=MOT['basic']['max_power_180s_W']),
    regler=dict(typ='V200A 24S', masse_kg=0.748, dauer_A=100, spitze_A=200, wirkungsgrad=ETA_ESC),
    antrieb=dict(ct_ref=ANT['reference_CT'], cp_ref=ANT['reference_CP'], d_ref_in=ANT['reference_diameter_in'], p_ref_in=ANT['reference_pitch_in'],
                 quelle=ANT['method']),
    modelle=modelle,
)
with open(os.path.join(H, 'modelle.js'), 'w', encoding='utf-8') as fh:
    fh.write('/* erzeugt von daten_erzeugen.py – nicht von Hand aendern */\n')
    fh.write('globalThis.SIM_DATEN=' + json.dumps(daten, ensure_ascii=False, separators=(',', ':')) + ';\n')
print(f'{len(modelle)} Modelle; Motorfit Kt={KT:.3f} Nm/A R={RPH*1000:.1f} mOhm I0={I0:.1f} A, RMS {rms*100:.1f} %')
