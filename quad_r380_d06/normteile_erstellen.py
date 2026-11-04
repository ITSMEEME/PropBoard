"""Generate the single additional nominal helical fastener, using D05 provenance."""
from pathlib import Path
H=Path(__file__).resolve().parent
source=(H.parent/'quad_r380_d05/normteile_erstellen.py').read_text()
source=source.replace("specs=[('ISO4762','M6',12)]","specs=[('ISO4762','M5',35)]")
exec(compile(source,str(H/'normteile_erstellen.py'),'exec'))
