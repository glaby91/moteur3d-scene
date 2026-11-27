"""V17.633: nine approved changes, on top of the V17.632 cleanup.
No change to engine or unrelated instances. Procedural artwork is original,
based on the approved two-panel swimming mosaic concept.
"""
import json
import math
from pathlib import Path

GEO='geometry/v633-west-interior.json'
IP='instances/v442-corrections.json'
MP='materials/v442-corrections.json'
PP='pbr/v440-audit.json'
LP='lighting/v8-nine-anomalies.json'
PALETTE={
    'aqua':([.35,.76,.77],.66), 'teal':([.06,.40,.47],.57),
    'cobalt':([.045,.19,.53],.52), 'clear':([.80,.91,.91],.82),
    'gold':([.95,.62,.17],.59), 'red':([.82,.16,.075],.52),
    'ivory':([.94,.83,.62],.48), 'outline':([.29,.21,.13],.44),
}
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def need(ok,msg): 
    if not ok: raise ValueError(msg)
def near(a,b): return abs(a-b)<1e-6
def mesh(ident): return {'id':ident,'type':'triangle_mesh','vertices':[],'faces':[],'uv':[]}
def quad(m,points,uv):
    i=len(m['vertices']);m['vertices'].extend(points);m['uv'].extend(uv)
    m['faces'].extend([[i,i+1,i+2],[i,i+2,i+3]])
def polygon_contains(x,y,poly):
    inside=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]: inside=not inside
    return inside
def swimmer(x,y,ox,oy,scale):
    # Normalized silhouette: head, cap, streamlined torso, two arms, legs.
    u=(x-ox)/scale;v=(y-oy)/scale
    parts=[
        [(-.10,.0),(.02,.045),(.19,.035),(.30,.085),(.38,.115),(.39,.10),(.29,.052),(.17,-.015),(.06,-.04),(-.10,-.055)],
        [(-.10,-.02),(-.29,-.055),(-.43,-.02),(-.45,-.045),(-.29,-.105),(-.05,-.06)],
        [(-.07,-.04),(-.23,-.11),(-.40,-.095),(-.42,-.12),(-.22,-.145),(.02,-.07)],
        [(.03,.02),(.16,-.015),(.31,.01),(.35,.04),(.36,.025),(.32,-.018),(.15,-.06),(.02,-.03)]
    ]
    if ((u-.14)/.058)**2+((v-.061)/.047)**2<1:
        return 'outline' if v>.078 else 'ivory'
    if any(polygon_contains(u,v,p) for p in parts): return 'ivory'
    return None
def artwork(x,y,which):
    # x,y in [0,1], y points upward. Broad water bands, solar disc, red
    # ribbons and two different athletic compositions; no baked background.
    starx,stary=.84,.79
    dx=(x-starx)*2.15;dy=y-stary
    angle=math.atan2(dy,dx);radius=math.hypot(dx,dy)
    if radius<.035+.18*max(0,math.cos(4*angle))**12: return 'gold'
    sun=math.hypot((x-(.22 if which==0 else .18))*2.15,y-.92)
    if .12<sun<.23: return 'gold'
    for args in ([(.49,.35,.92),(.26,.60,.52)] if which==0 else [(.56,.48,1.02)]):
        c=swimmer(x,y,*args)
        if c:return c
    ribbon=.30+.68*x+.08*math.sin(x*math.pi)
    if abs(y-ribbon)<.045:return 'red'
    if abs(y-ribbon+.085)<.028:return 'gold'
    if which==1 and abs(y-(.78-.83*x))<.035:return 'red'
    wave=y+.13*math.sin(2*math.pi*x+which*.8)
    if wave<.16:return 'cobalt'
    if wave<.29:return 'teal'
    if wave<.43:return 'aqua'
    if wave<.51:return 'clear'
    if which==1 and x>.63 and y>.62:return 'cobalt'
    return 'aqua' if (int(x*9)+int(y*6))%5==0 else 'clear'

def apply_patch(scene):
    scene=Path(scene);root=scene.parent;doc=load(scene)
    need(doc['revision'] in ('V17.629','V17.632'),'Unexpected base')
    data=load(root/IP);old=data['instances'];by={o['id']:o for o in old}
    need(len(by)==len(old),'Duplicate source IDs')
    need('v623_mosaic_aqua' not in by and 'v17_001771' not in by,'Apply V17.632 cleanup first')
    meshes=[]; added=[]; changed=set(); removed=set()
    def add(ident,parent,material,pos,size,geometry='unit_box',yaw=0):
        need(ident not in by and not any(o['id']==ident for o in added),'Duplicate new ID '+ident)
        added.append(dict(id=ident,parent=parent,geometry=geometry,material=material,position=pos,size=size,rotationY=yaw))
    def remove(ident):
        need(ident in by,'Missing '+ident);removed.add(ident)
    def change(ident):
        need(ident in by,'Missing '+ident);changed.add(ident);return by[ident]
    # 1,2,3,5: retain 300mm structural slab and 26.5mm finish as a single
    # continuous upper skin. Three west structural decks and two thin links
    # are replaced, plus front gallery slab/finish. The lift opening is exact.
    floors=['v8_side_gallery_floor_90_0','v8_side_gallery_floor_90_1','v8_side_gallery_floor_90_2',
            'v439_floor_deck_9','v439_floor_deck_10','v439_floor_deck_11',
            'v613_landing_link_north','v613_landing_link_south','v17_000029','v439_floor_deck_3']
    need(by[floors[0]]['size']==[8.95,.3,49.0] and by[floors[1]]['size']==[9.95,.3,49.0],'Unexpected gallery geometry')
    for i in floors:remove(i)
    parent='Interieur/Galeries/V633 dalle continue niveau 2'
    # Non-overlapping rectangles: west full footprint and central front
    # gallery. Opening exactly x[-41.55,-38.45], z[-35.28,-32.72].
    # Keep the original 3.1 x 2.56 m shaft void and its door bridges.
    rects=[(-50.5,-41.55,-54.5,-4.175),(-38.45,-28.5,-54.5,-4.175),
           (-41.55,-38.45,-54.5,-35.28),(-41.55,-38.45,-32.72,-4.175),
           (-28.5,28.5,-13.7,-4.175)]
    # Split skin at every shared boundary (T-junction free). Each cell uses
    # world-aligned UV, no overlapping surfaces, no grout or seam geometry.
    xs=sorted({v for a,b,c,d in rects for v in (a,b)})
    zs=sorted({v for a,b,c,d in rects for v in (c,d)})
    def covered(x,z):return any(a<x<b and c<z<d for a,b,c,d in rects)
    cells=[(a,b,c,d) for a,b in zip(xs,xs[1:]) for c,d in zip(zs,zs[1:]) if covered((a+b)/2,(c+d)/2)]
    area=sum((b-a)*(d-c) for a,b,c,d in cells)
    need(near(area,22*50.325-3.1*2.56+57*9.525),'Unexpected floor area')
    top=9.1765;bottom=8.85
    skin=mesh('geo_v633_floor_surface')
    for i,(a,b,c,d) in enumerate(rects):
        # Solid source boxes retain existing walkable geometry and BVH behavior.
        add('v633_floor_structure_%02d'%i,parent,'prp_concrete_raw',[(a+b)/2,(bottom+top-.025)/2,(c+d)/2],[b-a,top-.025-bottom,d-c])
    for a,b,c,d in cells:
        points=[[a,top,c],[a,top,d],[b,top,d],[b,top,c]]
        quad(skin,points,[[p[0]*.5,p[2]*.5] for p in points])
        # Finish edge only on exterior boundaries, never between cells.
        for p,q,ox,oz in [([a,top,c],[b,top,c],0,-1),([b,top,c],[b,top,d],1,0),([b,top,d],[a,top,d],0,1),([a,top,d],[a,top,c],-1,0)]:
            if not covered((p[0]+q[0])/2+ox*.001,(p[2]+q[2])/2+oz*.001):
                quad(skin,[q,p,[p[0],top-.025,p[2]],[q[0],top-.025,q[2]]],[[0,1],[1,1],[1,0],[0,0]])
    meshes.append(skin)
    add('v633_floor_surface',parent,'v439_gallery_warm',[0,0,0],[1,1,1],skin['id'])
    # 4: extend the shaft's fixed envelope, not the mobile cabin nor doors.
    roof=by['v17_000148'];ceiling=roof['position'][1]-roof['size'][1]/2
    need(near(ceiling,19.275),'Unexpected roof height')
    shaft_parent=by['v613_shaft_post_01']['parent']
    for o in old:
        ident=o['id']
        if ident.startswith(('v613_shaft_post_','v613_shaft_glass_')):
            b=o['position'][1]-o['size'][1]/2;limit=ceiling-(.09 if '_post_' in ident else .18)
            change(ident)['position'][1]=(b+limit)/2;o['size'][1]=limit-b
        elif ident.startswith('v613_shaft_crown_'):
            change(ident)['position'][1]=ceiling-.09
    def point(i):
        a=math.tau*i/12;return -40+1.30*math.cos(a),-34+1.28*math.sin(a)
    # Close the formerly open portal facets ONLY above existing portal height.
    for i in (0,5,6,11):
        x,z=point(i);xx,zz=point((i+1)%12);dx=xx-x;dz=zz-z
        pos=[(x+xx)/2,(11.35+ceiling-.18)/2,(z+zz)/2]
        yaw=math.degrees(math.atan2(-dz,dx))
        add('v633_upper_glass_%02d'%i,shaft_parent,'v614_lift_blue_glass',pos,[math.hypot(dx,dz)-.10,ceiling-.18-11.35,.045],yaw=yaw)
        add('v633_upper_crown_%02d'%i,shaft_parent,'v439_gallery_warm',[pos[0],ceiling-.09,pos[2]],[math.hypot(dx,dz)+.03,.18,.12],yaw=yaw)
    for i in (0,6):
        x,z=point(i);add('v633_upper_post_%02d'%i,shaft_parent,'v439_gallery_warm',[x,(11.35+ceiling-.09)/2,z],[.11,ceiling-.09-11.35,.11])
    # 6,7,8: one floating bar removed, two pilaster-mounted luminaires.
    for ident in ('v623_l_wallwash_01','v623_l_wallwash_02','v623_l_wallwash_03'):remove(ident)
    mats=load(root/MP);pbr=load(root/PP)
    def material(ident,color,rough,trans=0,metal=0,emission=None):
        need(ident not in {m['id'] for m in mats['materials']},'Material exists '+ident)
        m=dict(id=ident,baseColor=color,roughness=rough,metallic=metal,transmission=trans,ior=1.5,textureSet='tex_'+ident)
        if emission:m['emission']={'color':emission[0],'intensity':emission[1]}
        mats['materials'].append(m)
        pbr['sets'].append(dict(id='tex_'+ident,material=ident,pattern='solid',resolution=64,channels=['albedo'],baseColor=color,roughness=rough))
    material('v633_opal_rib',[.94,.87,.73],.24,0,0,([1,.76,.50],.65))
    material('v633_opal_groove',[.77,.68,.54],.32,0,0,([1,.76,.50],.30))
    lights=load(root/LP);orig_lights=len(lights['lights'])
    lamp_parent='Interieur/Vestiaires ouest/V633 appliques verticales opalines'
    for n,pid in enumerate(('v17_000897','v17_000903'),1):
        pillar=by[pid];x,y,z=pillar['position'];sx,sy,sz=pillar['size']
        need(near(x,-49.15) and near(sy,13.8),'Unexpected pilaster')
        face=x+sx/2
        # The existing pilaster ends at 14m, below the 19.275m roof. Avoid
        # a floating upper extension; stop just below its cap and split at deck.
        for j,(lo,hi) in enumerate(((.75,8.70),(9.22,13.90))):
            h=hi-lo;mid=(hi+lo)/2;prefix='v633_lamp_%d_%d_'%(n,j)
            add(prefix+'back',lamp_parent,'v614_lift_brass',[face+.025,mid,z],[.05,h,.38])
            for side in (-1,1):
                add(prefix+'rail_'+str(side),lamp_parent,'v614_lift_brass',[face+.075,mid,z+side*.177],[.10,h,.026])
            for side in (-1,1):
                add(prefix+'cap_'+str(side),lamp_parent,'v614_lift_brass',[face+.065,mid+side*(h/2-.035),z],[.12,.07,.38])
            add(prefix+'diffuser',lamp_parent,'v633_opal_groove',[face+.072,mid,z],[.038,h-.14,.326])
            for k in range(9):
                zz=z+(k-4)*.036
                add(prefix+'rib_%02d'%k,lamp_parent,'v633_opal_rib',[face+.103,mid,zz],[.034,h-.14,.026])
            for q in range(max(2,math.ceil(h/2.2))):
                yy=lo+(q+.5)*h/max(2,math.ceil(h/2.2))
                lights['lights'].append(dict(id=prefix+'source_%02d'%q,position=[face+.24,yy,z],radius=4.4,intensity=.45,color=[255,208,164],group='interior'))
    # 9: the two existing access-wall footprints become independent artistic
    # glass screens. Open air beneath; 3 brass feet and perimeter frame.
    for name,(color,trans) in PALETTE.items():material('v633_mosaic_'+name,color,.20,trans)
    panel_parent='Interieur/Piscine olympique/V633 vitraux sportifs sur pieds'
    panel_stats=[]
    for idx,ident in enumerate(('v17_001774','v17_001775')):
        wall=by[ident];need(wall['size']==[.25,3.25,7] and wall['material']=='prp_tile_ceramic','Unexpected access wall')
        remove(ident);x,y,z=wall['position'];width=7.;lo=.84;hi=3.775;mid=(lo+hi)/2
        prefix='v633_screen_%d_'%(idx+1)
        for side in (-1,1):
            add(prefix+'side_'+str(side),panel_parent,'v614_lift_brass',[x,mid,z+side*(width/2-.035)],[.12,hi-lo,.07])
            add(prefix+'rail_'+str(side),panel_parent,'v614_lift_brass',[x,mid+side*((hi-lo)/2-.035),z],[.12,.07,width-.14])
        for k,offset in enumerate((-2.65,0,2.65)):
            add(prefix+'foot_%d'%k,panel_parent,'v614_lift_brass',[x,.585,z+offset],[.62,.07,.28])
            add(prefix+'leg_%d'%k,panel_parent,'v614_lift_brass',[x,.725,z+offset],[.12,.28,.12])
        groups={name:mesh('geo_'+prefix+name) for name in PALETTE}
        cols,rows=96,40;w=width-.14;h=hi-lo-.14
        for col in range(cols):
            for row in range(rows):
                u=(col+.5)/cols;v=(row+.5)/rows;name=artwork(u,v,idx)
                m=groups[name]
                # Narrow joints are open air; one two-sided raster sheet per
                # tile, no opaque substrate and no redundant stacked layers.
                a=z-w/2+col*w/cols+.0015;b=z-w/2+(col+1)*w/cols-.0015
                c=lo+.07+row*h/rows+.0015;d=lo+.07+(row+1)*h/rows-.0015
                quad(m,[[x,c,a],[x,d,a],[x,d,b],[x,c,b]],[[0,0],[0,1],[1,1],[1,0]])
        for name,m in groups.items():
            if not m['faces']:continue
            meshes.append(m);add(prefix+name,panel_parent,'v633_mosaic_'+name,[0,0,0],[1,1,1],m['id'])
        panel_stats.append({'replaced':ident,'centerXZ':[x,z],'height':[lo,hi],'tiles':cols*rows,'paletteCounts':{n:len(m['faces'])//2 for n,m in groups.items()}})
    # Verify scope, IDs, bounds and mesh integrity before writing anything.
    new=[o for o in old if o['id'] not in removed]+added
    need(len({o['id'] for o in new})==len(new),'Duplicate final instance ID')
    need(len(removed)==15,'Unexpected removals')
    need(len(changed)==26,'Unexpected shaft modifications')
    for m in meshes:
        need(len(m['vertices'])==len(m['uv']) and len(m['faces'])<=80000 and len(m['vertices'])<=200000,'Mesh limit')
        need(all(len(f)==3 and len(set(f))==3 and min(f)>=0 and max(f)<len(m['vertices']) for f in m['faces']),'Invalid index')
    need(all(not covered(x,z) for x,z in [(-40,-34),(-40,-33),(-40,-35)]),'Lift opening blocked')
    need(all(covered(x,z) for x,z in [(-40,-36),(-40,-32),(-40,-4.2),(-31,-4.2),(0,-4.2)]),'Missing floor fill')
    need(all(p['tiles']==3840 for p in panel_stats),'Mosaic incomplete')
    need(len(mats['materials'])<256,'DX11 material limit')
    doc['sectors'][0]['geometry'].append(GEO)
    data['instances']=new
    dump(root/IP,data);dump(root/MP,mats);dump(root/PP,pbr);dump(root/LP,lights)
    dump(root/GEO,{'format':'m3d-geometry-v1','units':'m','meshes':meshes})
    dump(scene,doc)
    dump(root/'reports/west-interior-v633.json',{'revision':'V17.633','removed':sorted(removed),'modified':sorted(changed),'added':[o['id'] for o in added],'floorAreaM2':area,'floorTopY':top,'floorBottomY':bottom,'shaftTopY':ceiling,'lightSourcesAdded':len(lights['lights'])-orig_lights,'panels':panel_stats,'limitations':['Lamps terminate at existing pilaster caps (13.9m), not unsupported roof at 19.275m; continuous aligned segments either side of slab.','Mosaic is procedural geometry following approved concept, not a photographic texture; colored transmitted shadows not implemented by engine.']})
    print('V17.633: nine corrections;',len(removed),'removed;',len(changed),'shaft parts modified;',len(added),'added;',len(meshes),'meshes')
