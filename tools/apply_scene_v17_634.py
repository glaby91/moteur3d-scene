"""V17.634: adjust only the 14 V17.633 opal wall-lamp sources."""
import json
from pathlib import Path
def apply_patch(scene):
    root=Path(scene).parent
    path=root/'lighting/v8-nine-anomalies.json'
    doc=json.loads(path.read_text(encoding='utf-8-sig'))
    expected={f'v633_lamp_{n}_{j}_source_{q:02d}' for n in (1,2) for j,count in ((0,4),(1,3)) for q in range(count)}
    selected=[x for x in doc['lights'] if x.get('id','').startswith('v633_lamp_')]
    if len(selected)!=14 or {x['id'] for x in selected}!=expected:
        raise ValueError('Unexpected lamp source IDs')
    if any(x['radius']!=4.4 or x['intensity']!=.45 or x['group']!='interior' for x in selected):
        raise ValueError('Unexpected original lamp properties')
    for x in selected:x.update(radius=8.0,intensity=1.5)
    path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('V17.634: 14 existing sources adjusted; all other lights and geometry preserved')
