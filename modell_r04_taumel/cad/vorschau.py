#!/usr/bin/env python3
"""Rendert Vorschaubilder aus den STL-Dateien von erstellen.py (matplotlib). Entwurf F01."""
import struct, sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
HERE = Path(__file__).resolve().parent


def read_stl(path):
    data = path.read_bytes()
    if data[:5] == b'solid' and b'facet' in data[:300]:
        v = [list(map(float, l.split()[1:4])) for l in data.decode().splitlines() if l.strip().startswith('vertex')]
        return np.array(v).reshape(-1, 3, 3)
    n = struct.unpack('<I', data[80:84])[0]
    arr = np.frombuffer(data[84:84 + n * 50], dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
    return arr['v'].reshape(-1, 3, 3).astype(float)


def shade(tris, color, light=np.array([0.4, -0.5, 0.8])):
    nrm = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    k = 0.45 + 0.55 * np.abs(nrm @ (light / np.linalg.norm(light)))
    return np.clip(np.array(color)[None, :] * k[:, None], 0, 1)


def view(ax, groups, elev, azim, lim):
    for tris, color in groups:
        pc = Poly3DCollection(tris, facecolors=shade(tris, color), edgecolor='none', linewidth=0); ax.add_collection3d(pc)
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_zlim(-lim, lim); ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim); ax.set_axis_off()


def color(stem):
    if stem.endswith('_Kauf'): return (0.45, 0.45, 0.45)
    if stem.startswith('Rotor_oben'): return (0.16, 0.47, 0.84)
    if stem.startswith('Rotor_unten'): return (0.92, 0.41, 0.20)
    return (0.11, 0.69, 0.48)
groups = [(read_stl(p), color(p.stem)) for p in sorted((HERE / 'vorschau').glob('*.stl'))]
fig = plt.figure(figsize=(14, 7))
view(fig.add_subplot(1, 2, 1, projection='3d'), groups, 22, -60, 205)
view(fig.add_subplot(1, 2, 2, projection='3d'), groups, 0, -90, 205)
fig.suptitle('R04-Taumelmodell 1:4 – Entwurf F01 (blau: Rotor oben, orange: Rotor unten, grün: feststehende Druckteile inkl. Taumelscheiben-Innenring, grau: Kaufteile)', fontsize=10)
fig.tight_layout(); fig.savefig(HERE / 'Vorschau_Baugruppe.png', dpi=110); plt.close(fig)
hub = read_stl(HERE / 'stl' / 'Nabe.stl'); hub -= hub.reshape(-1, 3).mean(0)
fig = plt.figure(figsize=(14, 7))
view(fig.add_subplot(1, 2, 1, projection='3d'), [(hub, (0.16, 0.47, 0.84))], 55, -60, 48)
view(fig.add_subplot(1, 2, 2, projection='3d'), [(hub, (0.16, 0.47, 0.84))], -55, -60, 48)
fig.suptitle('Nabe als Topf: links Oberseite (Hebelraum), rechts Unterseite', fontsize=10)
fig.tight_layout(); fig.savefig(HERE / 'Vorschau_Nabe.png', dpi=110); plt.close(fig)
print('ok')
