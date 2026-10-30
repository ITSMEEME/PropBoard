#!/usr/bin/env python3
"""Pin imported standard CAD assets, preserve license and provenance; no OEM claims."""
from pathlib import Path
import subprocess,json,hashlib,shutil,urllib.parse
H=Path(__file__).resolve().parent;R=H.parents[1]/'.cfd-tools/vendor/FreeCAD-library'
REV='f5ca01cdcaa2f69b9295a6382719c2d90628780c'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==REV
allpaths=subprocess.check_output(['git','ls-tree','-r','--name-only','HEAD'],cwd=R,text=True).splitlines()
terms={'N01_M3x10':'Screw M3x10 ISO4762','N02_M3x12':'Screw M3x12 ISO4762','N03_M3x40':'Screw M3x40 ISO4762','N04_Mutter_M3':'ISO4032_Hex_Nut_M3.step'}
items=[]
for key,term in terms.items():
    src=next(p for p in allpaths if term in p and p.endswith('.step'));p=R/src;dest=H/'Quellen'/(key+'.step');shutil.copyfile(p,dest)
    items.append(dict(id=key,filename=dest.name,source_repository='https://github.com/FreeCAD/FreeCAD-library',source_revision=REV,source_path=src,source_url='https://github.com/FreeCAD/FreeCAD-library/blob/'+REV+'/'+urllib.parse.quote(src,safe='/'),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),license='CC-BY-3.0 per repository LICENSE-Assets',attribution='FreeCAD Parts Library contributors; ISO4762 family source history includes Peta-T (2015) and WladIMirG (2019). Nut author not identified in the checked metadata.',model_status='COMMUNITY_STANDARD_PART_MODEL_NOT_OEM_CERTIFICATE',thread_detail='Nominal thread interface; no verified helical flank geometry or supplier material certificate'))
for item in items:
    if item['id']=='N04_Mutter_M3':
        item['attribution']='FreeCAD Parts Library contributors; recorded file-history authors: WladIMirG, Obijuan'
        item['history_authors']=['WladIMirG','Obijuan']
shutil.copyfile(R/'LICENSE-Assets',H/'Quellen/LICENSE-FreeCAD-Assets.txt')
(H/'Quellen/Quellenmanifest.json').write_text(json.dumps(dict(assets=items,license_metadata_note='Legacy FCStd defaults say All rights reserved with empty author fields; repository asset policy explicitly covers all CAD as CC-BY-3.0. Unmodified STEP sources and upstream policy retained.'),indent=2))
print('Pinned',len(items),'STEP models at',REV)
