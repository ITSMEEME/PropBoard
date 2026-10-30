"""Editable P03 plate input; build revised hole pattern without altering F01 defaults."""
import importlib.util
from pathlib import Path
_C=None

def templates():
    global _C
    if _C is None:
        p=Path(__file__).resolve().parent.parent/'cad/erstellen.py'
        spec=importlib.util.spec_from_file_location('_p03_cad_templates',p);_C=importlib.util.module_from_spec(spec);spec.loader.exec_module(_C)
    return _C

def shape(dx,dy):
    c=templates();old=dict(c.MO)
    try:
        c.MO['mount_pattern']='rectangular';c.MO['mount_pitch_mm']=[dx,dy]
        return c.plate_shape()[0]
    finally:c.MO.clear();c.MO.update(old)

class Plate:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):obj.Shape=shape(obj.MotorRasterX_mm.Value,obj.MotorRasterY_mm.Value)
    def dumps(self):return None
    def loads(self,state):pass
