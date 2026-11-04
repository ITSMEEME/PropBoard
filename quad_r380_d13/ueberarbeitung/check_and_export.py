from pathlib import Path
import runpy
H=Path(__file__).parent
for file in ['fast_pruefen.py','propeller_pruefen.py','viewer_export.py']:runpy.run_path(str(H/file))
