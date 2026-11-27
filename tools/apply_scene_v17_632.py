"""V17.632: remove only the agreed west shower partitions and obsolete hall slab."""
import json
from pathlib import Path

MOSAIC = ('aqua', 'turquoise', 'deep_teal', 'gold')
GEOMETRY = 'geometry/v623-glass-mosaic.json'
WEST = 'Interieur/Vestiaires et douches ouest/'
EXPECTED = {
    'v17_001771': (WEST+'Murs', 'unit_box', [-40,2.15,-45], [17,3.25,.24]),
    'v17_001773': (WEST+'Murs', 'unit_box', [-48.38,2.15,-36], [.25,3.25,18]),
    'v7_close_obsolete_hall_stairwell': ('Interieur/Galeries/V7 fermeture tremie ancien escalier', 'unit_box', [-15,4.5,-11.15], [6.3,.3,5.1]),
}
for j in range(5):
    x = -44.5+1.75*j
    EXPECTED[f'v17_{1805+2*j:06d}'] = (WEST+'Douches/Colonnes', 'unit_box', [x,2,-43.6], [.09,2.8,.09])
    EXPECTED[f'v17_{1806+2*j:06d}'] = (WEST+'Douches/Pommeaux', 'unit_sphere', [x,3.1,-43.5], [.42,.14,.35])
for name in MOSAIC:
    ident = 'v623_mosaic_'+name
    EXPECTED[ident] = (WEST+'Mosaique de verre', 'geo_'+ident, [0,0,0], [1,1,1])

def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def apply_patch(scene):
    scene=Path(scene); root=scene.parent; doc=load(scene)
    assert doc['revision'] in ('V17.629','V17.631'), 'Unexpected source revision'
    path=root/'instances/v442-corrections.json'; data=load(path); old=data['instances']
    by={x['id']:x for x in old}; assert len(by)==len(old)
    for ident, expected in EXPECTED.items():
        obj=by[ident]; actual=tuple(obj[k] for k in ('parent','geometry','position','size'))
        assert actual==expected, (ident,actual,expected)
    geom=load(root/GEOMETRY); meshes=geom['meshes']
    assert {m['id'] for m in meshes}=={'geo_v623_mosaic_'+n for n in MOSAIC}
    assert sum(len(m['faces']) for m in meshes)==25608
    new=[x for x in old if x['id'] not in EXPECTED]
    assert len(old)-len(new)==17
    assert all(x['geometry'] not in {m['id'] for m in meshes} for x in new)
    for sector in doc['sectors']:
        for rel in sector['instances']:
            if rel!='instances/v442-corrections.json':
                assert all(x['geometry'] not in {m['id'] for m in meshes} for x in load(root/rel)['instances'])
    assert sum(s['geometry'].count(GEOMETRY) for s in doc['sectors'])==1
    for sector in doc['sectors']:
        if GEOMETRY in sector['geometry']: sector['geometry'].remove(GEOMETRY)
    data['instances']=new
    dump(path,data); dump(scene,doc); (root/GEOMETRY).unlink()
    report={'revision':'V17.632','removedInstances':[by[i] for i in EXPECTED], 'removedMosaicTriangles':25608, 'retainedInstances':len(new), 'removedGeometry':GEOMETRY, 'notes':['Both glass substrates belong to the deleted L mosaic partitions; structural walls and access walls remain.','Five shower columns and five heads removed.','Only former hall stairwell closure removed; level-two gallery slabs remain.']}
    dump(root/'reports/west-cleanup-v632.json',report)
    print('V17.632 cleanup: 17 instances removed, 25608 mosaic triangles removed; other instances preserved')
