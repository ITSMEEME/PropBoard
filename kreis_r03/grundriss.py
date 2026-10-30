#!/usr/bin/env python3
"""REKONSTRUKTION (2026-10-30): Grundrissvergleich R02-Umlaufbahn gegen R03-Kreisbahn.

Rein geometrisch. Ueberstrichene Flaechen sind idealisierte Ringflaechen je Ebene,
keine wirksamen Strahlflaechen; beide Ebenen werden nicht addiert.
Erzeugt Vergleich.json/.csv/.md sowie Grundriss_Vergleich.svg (und .png mit matplotlib).
"""
import csv, json, math
from pathlib import Path
HERE = Path(__file__).resolve().parent

R, HALF_SPAN, CHORD, N_WINGS = .45, .30, .12, 16
R_IN, R_OUT = R-HALF_SPAN, R+HALF_SPAN
VARIANTS = {'R02_Umlaufbahn': .50, 'R03_Kreis': 0.}   # Laenge eines geraden Abschnitts [m]


def kennwerte(straight):
    return {'gerader_Abschnitt_m': straight,
            'Bahnlaenge_Mittellinie_m': 2*straight+2*math.pi*R,
            'ueberstrichene_Flaeche_je_Ebene_m2': math.pi*(R_OUT**2-R_IN**2)+2*straight*(R_OUT-R_IN),
            'Fluegelflaeche_gesamt_m2': N_WINGS*2*HALF_SPAN*CHORD,
            'Grundriss_Fluegelbereich_m': [straight+2*R_OUT, 2*R_OUT]}


def outline(straight, r, n=181):
    """Stadionkontur mit Radius r um Kreismitten bei x=+-straight/2."""
    pts = []
    for cx, a0 in ((straight/2, -math.pi/2), (-straight/2, math.pi/2)):
        pts += [(cx+r*math.cos(a0+math.pi*i/(n-1)), r*math.sin(a0+math.pi*i/(n-1))) for i in range(n)]
    return pts+pts[:1]


def svg(path):
    s, w, h = 220, 1200, 520
    def poly(pts, ox, style):
        p = ' '.join(f'{ox+x*s:.1f},{h/2-y*s:.1f}' for x, y in pts)
        return f'<polyline points="{p}" style="{style}"/>'
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="sans-serif">',
           '<rect width="100%" height="100%" fill="white"/>']
    for (name, straight), ox in zip(VARIANTS.items(), (360, 900)):
        out.append(f'<text x="{ox}" y="30" text-anchor="middle" font-size="18">{name.replace("_", " ")}</text>')
        for r, style in ((R_OUT, 'fill:none;stroke:#1f5fa8;stroke-width:2'), (R_IN, 'fill:none;stroke:#1f5fa8;stroke-width:2'),
                         (R, 'fill:none;stroke:#888;stroke-dasharray:6 4'),
                         (.13, 'fill:none;stroke:#c0392b;stroke-width:1.5'), (.77, 'fill:none;stroke:#c0392b;stroke-width:1.5')):
            out.append(poly(outline(straight, r), ox, style))
        k = kennwerte(straight)
        out.append(f'<text x="{ox}" y="{h-40}" text-anchor="middle" font-size="14">Bahn {k["Bahnlaenge_Mittellinie_m"]:.4f} m, '
                   f'Ring je Ebene {k["ueberstrichene_Flaeche_je_Ebene_m2"]:.5f} m²</text>')
    out.append(f'<text x="{w/2}" y="{h-12}" text-anchor="middle" font-size="12" fill="#555">Blau: Flügelbereich r 150–750 mm; '
               'rot: Führungen r 130/770 mm; gestrichelt: Mittellinie r 450 mm. Geometrisch, kein Strömungsnachweis.</text></svg>')
    path.write_text('\n'.join(out), encoding='utf-8')


def png(path):
    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    except ImportError:
        return False
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for ax, (name, straight) in zip(axes, VARIANTS.items()):
        for r, kw in ((R_OUT, dict(c='#1f5fa8')), (R_IN, dict(c='#1f5fa8')), (R, dict(c='#888', ls='--')),
                      (.13, dict(c='#c0392b', lw=1)), (.77, dict(c='#c0392b', lw=1))):
            x, y = zip(*outline(straight, r)); ax.plot(x, y, **kw)
        ax.set_aspect('equal'); ax.set_xlim(-1.3, 1.3); ax.set_ylim(-.9, .9); ax.grid(alpha=.3)
        k = kennwerte(straight)
        ax.set_title(f'{name.replace("_", " ")}\nBahn {k["Bahnlaenge_Mittellinie_m"]:.4f} m, Ring {k["ueberstrichene_Flaeche_je_Ebene_m2"]:.5f} m²')
        ax.set_xlabel('x [m]'); ax.set_ylabel('y [m]')
    fig.suptitle('REKONSTRUKTION – geometrischer Grundrissvergleich, kein Strömungs- oder Tragfähigkeitsnachweis', fontsize=9)
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)
    return True


def main():
    data = {k: kennwerte(v) for k, v in VARIANTS.items()}
    a02, a03 = (data[k]['ueberstrichene_Flaeche_je_Ebene_m2'] for k in VARIANTS)
    report = {'status': 'REKONSTRUKTION_GEOMETRIE', 'varianten': data,
              'Flaechenaenderung_R03_gegen_R02_prozent': 100*(a03-a02)/a02,
              'hinweise': ['Ueberstrichene Flaechen sind idealisierte geometrische Ringflaechen je Ebene, keine wirksamen Strahlflaechen.',
                           'Die beiden uebereinanderliegenden Ebenen sind nicht als unabhaengige Rotorflaechen addierbar.',
                           'Der Kreis beseitigt Zentrifugalkraefte nicht; bei gleichem Radius und gleicher Geschwindigkeit wirken sie jetzt ueber den gesamten Umlauf.']}
    (HERE/'Vergleich.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    with (HERE/'Vergleich.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(['Kennwert', *VARIANTS])
        for key in ('gerader_Abschnitt_m', 'Bahnlaenge_Mittellinie_m', 'ueberstrichene_Flaeche_je_Ebene_m2', 'Fluegelflaeche_gesamt_m2'):
            w.writerow([key, *(round(data[v][key], 6) for v in VARIANTS)])
    svg(HERE/'Grundriss_Vergleich.svg'); has_png = png(HERE/'Grundriss_Vergleich.png')
    print(json.dumps(report, ensure_ascii=False, indent=1)); print('PNG erzeugt:', has_png)


if __name__ == '__main__':
    main()
