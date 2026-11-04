"""Additional M4x20 helical nominal ISO fastener, same pinned source as D05."""
from pathlib import Path
H=Path(__file__).resolve().parent
source=(H.parent/'quad_r380_d05/normteile_erstellen.py').read_text()
source=source.replace("specs=[('ISO4762','M6',12)]","specs=[('ISO4762','M4',20)]")
exec(compile(source,str(H/'normteile_erstellen.py'),'exec'))
