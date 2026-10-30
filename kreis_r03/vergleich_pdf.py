#!/usr/bin/env python3
"""Vergleich.md -> Vergleich.pdf (Python-Markdown + Chrome headless). REKONSTRUKTION 2026-10-30."""
import subprocess, sys, tempfile
from pathlib import Path
import markdown
HERE = Path(__file__).resolve().parent
CSS = 'body{font-family:sans-serif;max-width:46em;margin:2em auto;line-height:1.45}table{border-collapse:collapse}td,th{border:1px solid #999;padding:.3em .6em}td:not(:first-child){text-align:right}blockquote{background:#fff4e0;border-left:4px solid #e08a00;margin:0;padding:.5em 1em}img{max-width:100%}'
html = f'<!doctype html><meta charset="utf-8"><title>Kreis R03 Vergleich</title><style>{CSS}</style>' + \
       markdown.markdown((HERE/'Vergleich.md').read_text(encoding='utf-8'), extensions=['tables'])
with tempfile.TemporaryDirectory() as tmp:
    page = HERE/'_vergleich_tmp.html'; page.write_text(html, encoding='utf-8')
    try:
        subprocess.run([sys.argv[1] if len(sys.argv) > 1 else 'google-chrome', '--headless', '--disable-gpu', '--no-pdf-header-footer',
                        f'--user-data-dir={tmp}', f'--print-to-pdf={HERE/"Vergleich.pdf"}', page.as_uri()], check=True, capture_output=True)
    finally:
        page.unlink()
print(HERE/'Vergleich.pdf')
