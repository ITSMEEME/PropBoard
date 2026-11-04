from pathlib import Path
H=Path(__file__).resolve().parent
source=(H.parent/'quad_r380_d05/normteile_erstellen.py').read_text().replace("specs=[('ISO4762','M6',12)]","specs=[('ISO4762','M4',30),('ISO4032','M4',None)]")
exec(compile(source,str(__file__),'exec'))
