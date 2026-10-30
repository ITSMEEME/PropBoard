"""Recomputable FreeCAD features for the R04 swashplate manufacturing draft.

Keep this module and erstellen.py beside the Fertigung directory. Load the supplied
FCMacro once before editing the FCStd files in a new FreeCAD session.
"""
import copy
import json
import erstellen as model


def configure(parameters):
    model.P = copy.deepcopy(parameters)
    for attr, key in [('BL','blade'), ('HUB','hub'), ('HO','horn'), ('LID','lid'),
                      ('GR','gear'), ('SW','swash'), ('MO','motor'), ('PL','plate')]:
        setattr(model, attr, model.P[key])
    model.N = model.BL['count']
    model.D, model.F = model.P['print']['density'], model.P['print']['fill']
    model.CDIST = model.GR['module'] * (model.GR['z_ring'] + model.GR['z_pinion']) / 2 + model.GR['center_extra']


def shape_for(recipe, parameters):
    configure(parameters)
    if recipe == 'Fluegel': s = model.blade_shape()
    elif recipe == 'Nabe': s = model.hub_shape()
    elif recipe == 'Deckel_oben': s = model.lid_shape(1)[0]
    elif recipe == 'Deckel_unten': s = model.lid_shape(-1)[0]
    elif recipe == 'Pitchhebel': s = model.horn_shape(1)
    elif recipe == 'Taumel_Gleitkugel': s = model.swash_sleeve()
    elif recipe == 'Taumel_Innenring': s = model.swash_stationary()
    elif recipe == 'Taumel_Drehring': s = model.swash_rotating()
    elif recipe == 'Halteplatte': s = model.plate_shape()[0]
    elif recipe == 'Kappe': s = next(x[0] for x in model.world_static() if x[1] == 'TM-KAPPE-STACK-PRUEFSTAND')
    elif recipe == 'Huelse_Mitte': s = next(x[0] for x in model.world_static() if x[1] == 'TM-HUELSE-MITTE')
    elif recipe == 'Klemmring': s = next(x[0] for x in model.static_parts(0) if x[1] == 'TM-KLEMMRING')
    elif recipe == 'Mittelrohr':
        t = model.P['tube']; s = model.ring(t['d']/2-t['wall'], t['d']/2, 0, 2*t['half_len'])
    else: raise ValueError(recipe)
    # Common manufacturing datum: minimum X/Y/Z of the local part, in millimetres.
    s = s.copy()
    s.translate(model.V(-s.BoundBox.XMin, -s.BoundBox.YMin, -s.BoundBox.ZMin))
    return s


class ManufacturingPart:
    def __init__(self, obj):
        obj.Proxy = self

    def execute(self, obj):
        parameters = json.loads(obj.ParameterJSON)
        if obj.ParameterTabelle:
            for row in range(2, obj.ParameterZeilen + 2):
                path = obj.ParameterTabelle.get('A' + str(row)).split('.')
                target = parameters
                for key in path[:-1]: target = target[key]
                value = obj.ParameterTabelle.get('B' + str(row))
                target[path[-1]] = json.loads(value) if isinstance(value, str) else value
        shape = shape_for(obj.Rezept, parameters)
        if not shape.isValid() or len(shape.Solids) != 1:
            raise ValueError('Invalid/non-single-solid manufacturing part: ' + obj.Rezept)
        obj.Shape = shape
        obj.Placement = shape.Placement

    def onDocumentRestored(self, obj):
        # Stored BRep stays usable on opening; spreadsheet dependency edits
        # trigger regeneration when needed.
        pass

    def dumps(self): return None
    def loads(self, state): pass
    # Compatibility with earlier FreeCAD serialization.
    def __getstate__(self): return None
    def __setstate__(self, state): pass


class EnvelopeReferences(ManufacturingPart):
    """Stable associative dimension datums, including vertex-free round faces."""
    def execute(self, obj):
        b=obj.Source.Shape.BoundBox
        obj.Shape=model.Part.makeCompound([
            model.Part.Vertex(model.V(b.XMin,b.YMin,b.ZMin)),
            model.Part.Vertex(model.V(b.XMax,b.YMax,b.ZMax))])
