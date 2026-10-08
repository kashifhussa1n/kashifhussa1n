"""Offline 3D ASCII cinema. Deterministic geometry, z-buffer and glyph transport.

python scripts/render_scenes.py --stills
python scripts/render_scenes.py
All art is geometry, not image-to-text copies of the user's references.
"""
from pathlib import Path
import argparse, functools, json, math, os, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont, _webp
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from skimage.measure import marching_cubes

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
W,H = 840,880
CW,CH = 7,11
COLS,ROWS = 108,56
OX,OY = (W-COLS*CW)//2,157
FPS = 25
BG = (13,17,23)
INK = (218,233,242)
MUTED = (119,140,157)
CYAN = (140,211,229)
GOLD = (233,206,162)
GLYPHS = np.array(list(' .,:;-=+*#%@'))
FONT_PATH = str(OUT/'JetBrainsMono-Regular.ttf')
FONT = ImageFont.truetype(FONT_PATH,13)
SMALL = ImageFont.truetype(FONT_PATH,16)
TITLE = ImageFont.truetype(FONT_PATH,31)
SUB = ImageFont.truetype(FONT_PATH,18)
TAU = 2*math.pi

def unit(v):
    return v / np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-9)

def rot(a,axis='y'):
    c,s = math.cos(a),math.sin(a)
    if axis=='y': return np.array([[c,0,s],[0,1,0],[-s,0,c]],np.float32)
    if axis=='x': return np.array([[1,0,0],[0,c,-s],[0,s,c]],np.float32)
    return np.array([[c,-s,0],[s,c,0],[0,0,1]],np.float32)

def shape(p,n,col=INK):
    p,n = np.asarray(p,np.float32),np.asarray(n,np.float32)
    c = np.broadcast_to(np.asarray(col,np.float32),p.shape).copy()
    return p,n,c

def move(s,offset=(0,0,0),r=None,scale=1):
    p,n,c = s
    if r is None: r = np.eye(3)
    return p@r.T*scale+np.array(offset),n@r.T,c

def join(*ss):
    return tuple(np.concatenate([s[i] for s in ss]) for i in range(3))

@functools.lru_cache(maxsize=64)
def ellipsoid(rx,ry,rz,count=14000,col=INK):
    i=np.arange(count,dtype=np.float32)+.5
    y=1-2*i/count; a=i*2.399963229728653
    v=np.stack([np.sqrt(1-y*y)*np.cos(a),y,np.sqrt(1-y*y)*np.sin(a)],1)
    radii=np.array([rx,ry,rz]); return shape(v*radii,unit(v/radii),col)

def ell(c,r,col=INK,count=14000):
    return move(ellipsoid(*r,count,tuple(col)),c)

def tube(path,radius,col=INK,sides=12):
    p=np.asarray(path,np.float32)
    t=unit(np.gradient(p,axis=0))
    ref=np.broadcast_to([0,1,0],t.shape).copy(); ref[np.abs(t[:,1])>.93]=[1,0,0]
    b=unit(np.cross(t,ref)); c=unit(np.cross(t,b))
    a=np.arange(sides)*TAU/sides
    n=b[:,None,:]*np.cos(a)[None,:,None]+c[:,None,:]*np.sin(a)[None,:,None]
    xyz=p[:,None,:]+radius*n
    return shape(xyz.reshape(-1,3),n.reshape(-1,3),col)

def limb(a,b,r,col=INK):
    a,b=np.array(a),np.array(b); vec=b-a; length=np.linalg.norm(vec)
    y=vec/length; x=unit(np.cross(y,[0,0,1.])); z=np.cross(x,y)
    return move(ellipsoid(r,length/2+r*.25,r,5000,tuple(col)),(a+b)/2,np.stack([x,y,z],1))

def box(size,col=INK,texture=None):
    size=np.array(size); points=[]; normals=[]
    for ax in range(3):
        other=[v for v in range(3) if v!=ax]
        u=np.linspace(-size[other[0]]/2,size[other[0]]/2,max(3,int(size[other[0]]/.009)))
        v=np.linspace(-size[other[1]]/2,size[other[1]]/2,max(3,int(size[other[1]]/.009)))
        uv=np.stack(np.meshgrid(u,v,indexing='ij'),-1).reshape(-1,2)
        for sign in [-1,1]:
            p=np.zeros((len(uv),3)); p[:,ax]=sign*size[ax]/2; p[:,other]=uv
            n=np.zeros_like(p); n[:,ax]=sign
            points.append(p); normals.append(n)
    p,n=np.concatenate(points),np.concatenate(normals)
    result=shape(p,n,col)
    if texture: result=(p,n,texture(p,n,result[2]))
    return result

def smoothmin(a,b,k=.12):
    h=np.clip(.5+.5*(b-a)/k,0,1)
    return b*(1-h)+a*h-k*h*(1-h)

def sdfell(p,c,r):
    q=(p-np.array(c))/np.array(r)
    return (np.linalg.norm(q,axis=-1)-1)*min(r)

def implicit(name,fn,col=INK,bounds=1.55,n=170):
    cache=OUT/(name+'-mesh.npz')
    if cache.exists():
        z=np.load(cache); return z['p'],z['n'],z['c']
    axis=np.linspace(-bounds,bounds,n,dtype=np.float32)
    p=np.stack(np.meshgrid(axis,axis,axis,indexing='ij'),-1)
    volume=fn(p)
    verts,faces,_,_=marching_cubes(volume,0,spacing=(axis[1]-axis[0],)*3)
    verts-=bounds
    # Densify mesh with triangle centroids to prevent pinholes on ASCII cells.
    verts=np.concatenate([verts,verts[faces].mean(1)])
    eps=.0015; normals=[]
    for ax in range(3):
        step=np.eye(3)[ax]*eps
        normals.append((fn(verts+step)-fn(verts-step))/(2*eps))
    result=shape(verts,unit(np.stack(normals,1)),col)
    np.savez_compressed(cache,p=result[0],n=result[1],c=result[2])
    return result

@functools.lru_cache(None)
def brain():
    def field(p):
        x,y,z=np.moveaxis(p,-1,0)
        left=sdfell(p,(-.42,.15,0),(.65,.83,.83)); right=sdfell(p,(.42,.15,0),(.65,.83,.83))
        base=np.minimum(left,right)
        # Meandering cortical sulci, with a deep longitudinal fissure.
        a=np.sin(19*x+2.5*np.sin(8*y)+1.4*np.sin(7*z))
        b=np.sin(18*z+2.5*np.sin(7*x)-1.6*np.sin(9*y))
        folds=.042*np.tanh(3*(a*b+.12))
        cortex=base+folds
        stem=sdfell(p,(.16,-.90,-.30),(.21,.39,.23))
        cerebellum=sdfell(p,(0,-.59,-.43),(.55,.39,.42))+.015*np.cos(y*90)
        return smoothmin(smoothmin(cortex,cerebellum,.09),stem,.08)
    return implicit('brain-v2',field,(190,210,231))

@functools.lru_cache(None)
def skull():
    def field(p):
        x,y,z=np.moveaxis(p,-1,0)
        d=sdfell(p,(0,.36,-.10),(.83,.90,.70))
        d=smoothmin(d,sdfell(p,(0,-.25,.04),(.64,.56,.58)),.15)
        for s in [-1,1]:
            d=smoothmin(d,sdfell(p,(s*.57,-.19,.19),(.24,.32,.38)),.08)
        # Eye sockets and nasal opening are subtracted solids, with interior walls.
        for s in [-1,1]: d=np.maximum(d,-sdfell(p,(s*.34,.10,.64),(.28,.29,.43)))
        nose=np.maximum(np.abs(x)-(.075+.16*np.clip(-y+.02,0,.5)),np.maximum(y-.04,-y-.43))
        nose=np.maximum(nose,np.abs(z-.67)-.43)
        d=np.maximum(d,-nose)
        # Hollow mouth, separated mandible, and eight individually modeled teeth.
        d=np.maximum(d,-sdfell(p,(0,-.64,.48),(.47,.22,.35)))
        jaw=np.maximum(sdfell(p,(0,-.77,.06),(.61,.43,.48)),-sdfell(p,(0,-.66,.09),(.45,.33,.44)))
        d=np.minimum(d,jaw)
        for xx in np.linspace(-.40,.40,9):
            for yy in [-.48,-.78]:
                d=np.minimum(d,sdfell(p,(xx,yy,.52-.13*(xx/.45)**2),(.041,.095,.07)))
        return d
    return implicit('skull-v3',field,(231,226,211))

@functools.lru_cache(None)
def cat():
    def field(p):
        x,y,z=np.moveaxis(p,-1,0)
        d=sdfell(p,(0,-.13,-.05),(.90,.80,.64))
        for s in [-1,1]:
            # A tapered solid ear, rising from each side of the head.
            yy=np.clip((y-.35)/.95,0,1)
            ear=np.maximum(np.abs(x-s*(.69+.05*yy))-(.34*(1-yy)+.025),np.abs(z+.03)-(.25*(1-yy)+.045))
            ear=np.maximum(ear,np.maximum(.30-y,y-1.22))
            d=smoothmin(d,ear,.12)
            d=smoothmin(d,sdfell(p,(s*.23,-.42,.53),(.33,.26,.30)),.08)
        return d
    body=implicit('cat-v3',field,(201,212,213))
    p,n,c=body; c=c.copy()
    stripes=np.sin(p[:,0]*17+2*np.sin(p[:,1]*13))>.63
    stripezone=(p[:,1]>.15)|(np.abs(p[:,0])>.56)
    c[stripes&stripezone]*=.48
    ears=(p[:,1]>.55)&(p[:,2]>.03); c[ears]=[182,152,156]
    parts=[(p,n,c)]
    for s in [-1,1]:
        parts.extend([ell((s*.36,.04,.55),(.24,.22,.15),(216,224,211)),
                      ell((s*.36,.045,.69),(.135,.15,.04),(122,183,169)),
                      ell((s*.36,.045,.726),(.056,.13,.02),(42,56,68)),
                      ell((s*.32,.10,.744),(.034,.037,.015),(251,251,239))])
        a=np.linspace(0,TAU,320)
        # Rounded rectangular glasses rims, deliberately substantial at README size.
        xx=np.sign(np.cos(a))*np.abs(np.cos(a))**.60*.33+s*.37
        yy=np.sign(np.sin(a))*np.abs(np.sin(a))**.70*.255+.045
        parts.append(tube(np.stack([xx,yy,.79-.06*(xx**2)],1),.030,(110,158,189),16))
        for k in range(3):
            t=np.linspace(0,1,100)
            parts.append(tube(np.stack([s*(.34+.84*t),-.40+(k-1)*.15*t,.78-.18*t],1),.006,(193,214,223),6))
    parts.append(tube([[-.07,.11,.80],[0,.15,.84],[.07,.11,.80]],.025,(110,158,189)))
    parts.append(ell((0,-.32,.84),(.12,.077,.08),(172,136,153)))
    for s in [-1,1]:
        t=np.linspace(0,1,100)
        parts.append(tube(np.stack([s*.20*t,-.45-.08*np.sin(t*math.pi),.803-.04*t],1),.014,(50,68,81)))
    return join(*parts)

@functools.lru_cache(None)
def earth():
    land=Image.new('L',(1440,720)); draw=ImageDraw.Draw(land)
    geo=json.loads((OUT/'earth-land.geojson').read_text())
    for feature in geo['features']:
        g=feature['geometry']; polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
        for poly in polys:
            for idx,ring in enumerate(poly):
                draw.polygon([((lon+180)*4,(90-lat)*4) for lon,lat in ring],fill=255 if idx==0 else 0)
    p,n,c=ellipsoid(1.06,1.06,1.06,100000)
    lon=np.arctan2(p[:,0],p[:,2]); lat=np.arcsin(p[:,1]/1.06)
    ix=np.clip(((lon/math.pi+1)*720).astype(int),0,1439); iy=np.clip(((.5-lat/math.pi)*720).astype(int),0,719)
    mask=np.asarray(land)[iy,ix]>0
    c[:]=[54,101,139]; c[mask]=[194,225,210]
    c[np.abs(lat)>1.30]=[224,238,240]
    return p,n,c

@functools.lru_cache(None)
def steve_parts():
    def skin(p,n,c):
        # Stable pixel shading, not temporally randomized noise.
        q=np.floor((p+1)*20)
        noise=(np.sin(q[:,0]*7+q[:,1]*13+q[:,2]*17)>0)*.17+.83
        return c*noise[:,None]
    def face(p,n,c):
        c=skin(p,n,c); front=n[:,2]>.5
        x,y=p[:,0],p[:,1]
        hair=(y>.20)|((n[:,2]<.5)&(y>-.1)); c[hair]=[79,67,54]
        eyes=front&(abs(y-.02)<.041)&(abs(abs(x)-.16)<.09); c[eyes]=[216,231,225]
        pupils=eyes&(abs(abs(x)-.14)<.041); c[pupils]=[117,134,208]
        beard=front&(y<-.13)&(abs(x)<.21); c[beard]=[100,72,57]
        mouth=front&(y<-.17)&(y>-.22)&(abs(x)<.09); c[mouth]=[191,133,104]
        return c
    return {
        'head':box((.62,.62,.62),(191,149,116),face),
        'torso':box((.62,.87,.32),(76,190,194),skin),
        'arm':join(move(box((.28,.29,.32),(70,181,190),skin),(0,.29,0)),move(box((.28,.59,.32),(190,149,117),skin),(0,-.15,0))),
        'leg':join(move(box((.29,.79,.32),(109,111,184),skin),(0,.055,0)),move(box((.29,.14,.38),(86,98,105)),(0,-.41,.025)))
    }

def steve(t):
    parts=steve_parts(); a=math.sin(t*TAU*1.25)*.58; bob=.018*math.cos(t*TAU*2.5)
    shapes=[move(parts['head'],(0,.95+bob,0),rot(.06*math.sin(t*TAU/4))), move(parts['torso'],(0,.205+bob,0))]
    for s in [-1,1]:
        # Rotation about shoulder/hip rather than about limb center.
        shapes.append(move(move(parts['arm'],(0,-.39,0)),(s*.46,.62+bob,0),rot(s*a,'x')))
        shapes.append(move(move(parts['leg'],(0,-.44,0)),(s*.16,-.23+bob,0),rot(-s*a,'x')))
    return move(join(*shapes),r=rot(-.38+.32*math.sin(t*TAU/4)))

def ronaldo(t):
    # Stylized CR7: athletic proportions, sculpted face, number 7, jump-turn-land.
    u=(t%4.8)/4.8
    jump=math.sin(math.pi*np.clip((u-.12)/.47,0,1))*.30 if .12<u<.59 else 0
    turn=TAU*(3*(np.clip((u-.10)/.49,0,1)**2)-2*(np.clip((u-.10)/.49,0,1)**3))
    spread=.15+.46*(.5-.5*math.cos(math.pi*np.clip((u-.40)/.20,0,1)))
    # Return gradually to starting pose after celebration hold.
    reset=np.clip((u-.79)/.21,0,1); reset=reset*reset*(3-2*reset)
    spread=spread*(1-reset)+.15*reset
    raise_arm=math.sin(math.pi*np.clip(u/.55,0,1)) if u<.55 else 0
    raise_arm*=1-reset
    skin=(211,178,148); shirt=(218,229,235); shorts=(177,198,217)
    parts=[ell((0,.24,0),(.34,.48,.18),shirt),ell((0,.76,0),(.10,.15,.10),skin),ell((0,1.02,.015),(.18,.245,.18),skin)]
    head=ell((0,1.13,-.025),(.185,.15,.18),(58,64,70)); parts.append(head)
    parts.extend([ell((0,1.01,.197),(.038,.062,.046),skin),ell((0,.924,.18),(.08,.013,.022),(104,80,73))])
    for s in [-1,1]:
        parts.extend([ell((s*.078,1.056,.173),(.033,.016,.019),(39,48,57)),ell((s*.08,1.084,.16),(.051,.016,.018),(62,64,68))])
        shoulder=(s*.30,.58,0); elbow=(s*(.55-.10*raise_arm),.20+.70*raise_arm,.02); hand=(s*(.78-.35*raise_arm),-.11+1.28*raise_arm,.10)
        parts.extend([limb(shoulder,elbow,.09,shirt),limb(elbow,hand,.066,skin),ell(hand,(.068,.085,.059),skin)])
        hip=(s*.15,-.19,0); knee=(s*(.18+spread*.50),-.67,.02); foot=(s*(.19+spread),-1.10,.12)
        parts.extend([limb(hip,knee,.125,shorts),limb(knee,foot,.072,shirt),ell((foot[0],foot[1]-.02,.19),(.10,.075,.21),(165,195,208))])
    # Front and rear number 7, actually attached to torso geometry.
    for z in [.191,-.191]:
        parts.append(tube([[-.09,.48,z],[.09,.48,z],[.01,.25,z],[-.025,.17,z]],.018,(54,116,160),8))
    return move(join(*parts),(0,jump-.10,0),rot(turn-.16))

@functools.lru_cache(None)
def asterisk():
    return join(*[move(box((.32,2.15,.37),(196,223,233)),r=rot(k*math.pi/3,'z')) for k in range(3)])

@functools.lru_cache(None)
def star():
    def field(p):
        x,y,z=np.moveaxis(p,-1,0)
        a=np.arctan2(y,x); radius=np.hypot(x,y)
        target=.76+.24*np.cos(5*a)
        return np.sqrt((radius/target)**2+(z/.30)**2)-1
    return implicit('star-v1',field,(215,203,239),n=150)

@functools.lru_cache(None)
def eye():
    t=np.linspace(0,TAU,900); x=1.2*np.cos(t); y=.62*np.sin(t)*np.abs(np.sin(t))**.35
    rim=tube(np.stack([x,y,np.zeros_like(x)],1),.085,(161,211,220),18)
    p,n,c=ellipsoid(.47,.47,.47,26000)
    c[:]=[159,202,210]; c[p[:,2]>.35]=[106,155,187]; c[p[:,2]>.44]=[32,54,77]
    return join(rim,(p,n,c))

@functools.lru_cache(None)
def knot():
    t=np.linspace(0,TAU,2000)
    p=np.stack([np.sin(t)+2*np.sin(2*t),np.cos(t)-2*np.cos(2*t),-np.sin(3*t)],1)*.34
    return tube(p,.13,(170,216,220),24)

def solar(t):
    shapes=[ell((0,0,0),(.28,.28,.28),(246,204,135),16000)]
    for i,(r,size) in enumerate(zip([.43,.60,.79,.96,1.22,1.51,1.77,1.99],[.039,.060,.065,.047,.128,.10,.070,.068])):
        phase=t*(1.8/(1+i*.40))+i*1.7
        a=np.linspace(0,TAU,1000)
        orbit=np.stack([r*np.cos(a),np.zeros_like(a),r*np.sin(a)],1)
        shapes.append(tube(orbit,.004,(69,92,115),5))
        pos=(r*math.cos(phase),0,r*math.sin(phase))
        colors=[(171,168,164),(217,193,159),(135,201,219),(218,160,133),(212,191,163),(207,196,171),(150,215,216),(130,156,226)]
        planet=ell(pos,(size,size,size),colors[i],6000)
        shapes.append(planet)
        if i==5:
            ring=np.stack([.18*np.cos(a),.045*np.sin(a),.18*np.sin(a)],1)+np.array(pos)
            shapes.append(tube(ring,.014,(171,159,147),8))
    return move(join(*shapes),r=rot(.48,'x')@rot(-.2,'z'))

SCENES=[
    ('NEURAL / 01','The architecture of thought','brain',4.8),
    ('OVERWORLD / 02','Steve, one step at a time','steve',4.8),
    ('MEMENTO / 03','A study in light and bone','skull',4.8),
    ('PALE BLUE DOT / 04','One planet. Endless possibilities.','earth',6.4),
    ('SIUUU / 05','CR7 / jump, turn, land','ronaldo',4.8),
    ('CURIOUS / 06','A familiar face. A different dimension.','cat',5.2),
    ('ASTERISK / 07','A small symbol with a lot of depth','asterisk',4.0),
    ('ORBITAL / 08','Everything is in motion','solar',5.2),
    ('STARFORM / 09','Soft surfaces. Sharp ideas.','star',4.0),
    ('PERSPECTIVE / 10','There is always another way to look','eye',4.0),
    ('CONTINUUM / 11','Follow the thread','knot',4.0),
]

def model(key,t,duration):
    if key in ['steve','ronaldo','solar']: return globals()[key](t)
    obj=globals()[key]()
    if key=='earth': r=rot(-t/duration*TAU-.20)@rot(.15,'z')
    elif key=='cat': r=rot(.60*math.sin(t/duration*TAU))@rot(.10*math.sin(t/duration*TAU),'z')
    elif key=='skull': r=rot(.85*math.sin(t/duration*TAU))@rot(.11,'x')
    else: r=rot(t/duration*TAU+.30)@rot(.18+.19*math.sin(t/duration*TAU),'x')
    return move(obj,r=r)

def project(obj,scale=245):
    p,n,c=obj
    # Perspective camera with the same scale for x and y in physical pixels.
    perspective=5.8/(5.8-p[:,2])
    px=COLS/2+p[:,0]*scale*perspective/CW
    py=ROWS/2-p[:,1]*scale*perspective/CH
    ix=np.rint(px).astype(int); iy=np.rint(py).astype(int)
    valid=(ix>=1)&(ix<COLS-1)&(iy>=1)&(iy<ROWS-1)
    # Normal backface tests relative to the camera, not merely to world +z.
    view=unit(np.array([0,0,5.8])-p)
    valid &= np.sum(n*view,axis=1)>-.05
    ids=np.flatnonzero(valid); flat=iy[ids]*COLS+ix[ids]
    # Sort primarily by pixel, then nearest depth. One opaque surface per cell.
    order=np.lexsort((-p[ids,2],flat)); sortedflat=flat[order]
    first=np.r_[True,np.diff(sortedflat)!=0]; indices=ids[order[first]]
    key=unit(np.array([-.55,.65,1.])); fill=unit(np.array([.8,.1,.5]))
    light=.22+.70*np.maximum(n[indices]@key,0)+.18*np.maximum(n[indices]@fill,0)
    rim=.10*(1-np.clip(np.sum(n[indices]*view[indices],1),0,1))**2
    rgb=np.clip(c[indices]*(light+rim)[:,None],0,255)
    luma=rgb@np.array([.2126,.7152,.0722])/255
    glyph=np.clip((luma*12+1).astype(int),1,10)
    # Continuous shading in addition to glyph coverage makes cavities readable.
    rgb=np.clip(c[indices]*(.50+.50*np.clip(light+rim,0,1))[:,None],0,255)
    xy=np.stack([OX+ix[indices]*CW,OY+iy[indices]*CH],1).astype(float)
    return xy,glyph,rgb

def smooth(u): return np.clip(u,0,1)**3*(10-15*np.clip(u,0,1)+6*np.clip(u,0,1)**2)

class Morph:
    def __init__(self,a,b):
        self.a,self.b=a,b
        # Minimum-cost bipartite glyph matching preserves local neighborhoods.
        dist=cdist(a[0]/[756,616],b[0]/[756,616],'sqeuclidean')
        ia,ib=linear_sum_assignment(dist)
        self.ia,self.ib=ia,ib
        self.drop=np.setdiff1d(np.arange(len(a[0])),ia)
        self.add=np.setdiff1d(np.arange(len(b[0])),ib)
        self.drop_to=np.argmin(dist[self.drop],axis=1) if len(self.drop) else []
        self.add_from=np.argmin(dist[:,self.add],axis=0) if len(self.add) else []

    def frame(self,u):
        a,b=self.a,self.b; s=smooth(u)
        pa,pb=a[0][self.ia],b[0][self.ib]
        delta=pb-pa
        bend=np.stack([-delta[:,1],delta[:,0]],1)*(.10*np.sin(math.pi*s))
        xy=pa+(pb-pa)*s+bend
        rgb=a[2][self.ia]*(1-s)+b[2][self.ib]*s
        # Each matched character crossfades its glyph while following one path.
        g=a[1][self.ia]*(1-s)+b[1][self.ib]*s
        if len(self.drop):
            p=a[0][self.drop]*(1-s)+b[0][self.drop_to]*s
            xy=np.concatenate([xy,p]); g=np.r_[g,a[1][self.drop]]
            rgb=np.concatenate([rgb,BG+(a[2][self.drop]-BG)*(1-s)**1.7])
        if len(self.add):
            p=a[0][self.add_from]*(1-s)+b[0][self.add]*s
            xy=np.concatenate([xy,p]); g=np.r_[g,b[1][self.add]]
            rgb=np.concatenate([rgb,BG+(b[2][self.add]-BG)*s**1.7])
        return xy,g,rgb

@functools.lru_cache(None)
def glyph_mask(g):
    m=Image.new('L',(CW+2,CH+2)); ImageDraw.Draw(m).text((0,-1),str(GLYPHS[g]),font=FONT,fill=255)
    return m

def canvas(scene,phase,progress):
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    d.rounded_rectangle((0,0,W-1,H-1),radius=12,outline=(48,54,61))
    d.line((0,30,W,30),fill=(48,54,61))
    for i,col in enumerate([(255,95,86),(255,189,46),(39,201,63)]): d.ellipse((15+i*16,10,25+i*16,20),fill=col)
    d.text((420,15),'kashif@github: ~$ ./ascii-cinema',font=ImageFont.truetype(FONT_PATH,12),fill=MUTED,anchor='mm')
    d.text((42,65),'A S C I I   /   S T U D I E S',font=SMALL,fill=CYAN)
    d.text((42,99),scene[0],font=TITLE,fill=INK)
    d.text((42,785),scene[1],font=SUB,fill=MUTED)
    d.line((42,829,798,829),fill=(37,48,62),width=2)
    d.line((42,829,42+int(756*progress),829),fill=(101,168,191),width=2)
    d.text((42,851),phase,font=SMALL,fill=CYAN)
    d.text((798,851),'LOOP / 11 SCENES',font=SMALL,fill=MUTED,anchor='ra')
    return im

def draw_cloud(im,cloud,alpha=1):
    xy,g,colors=cloud
    # Cached glyph bitmaps avoid repeated font layout for thousands of particles.
    for pos,gi,color in zip(xy,g,colors):
        x,y=np.rint(pos).astype(int)
        if not (8<x<W-10 and 150<y<774): continue
        lo=int(math.floor(gi)); hi=min(10,lo+1); mix=gi-lo
        mask=glyph_mask(max(1,lo))
        if mix>.025: mask=Image.blend(mask,glyph_mask(hi),float(mix))
        rgb=tuple(np.clip(BG+(color-BG)*alpha,0,255).astype(int))
        im.paste(rgb,(x,y),mask)
    return im

def stills():
    thumbs=[]
    for i,scene in enumerate(SCENES):
        t=.15 if scene[2] in ['star','asterisk','eye','cat'] else .6 if scene[2]!='ronaldo' else 3.0
        cloud=project(model(scene[2],t,scene[3]),170 if scene[2]=='solar' else 205 if scene[2]=='ronaldo' else 225 if scene[2]=='steve' else 245)
        im=draw_cloud(canvas(scene,'FORM / MOTION',.5),cloud)
        im.save(OUT/(scene[2]+'-preview.png'))
        if scene[2]=='cat': im.save(OUT/'cinema-poster.png')
        thumbs.append(im.resize((420,440),Image.Resampling.LANCZOS))
        print(scene[2],len(cloud[0]),flush=True)
    contact=Image.new('RGB',(420*4,440*3),BG)
    for i,im in enumerate(thumbs): contact.paste(im,(i%4*420,i//4*440))
    contact.save(OUT/'scene-contact-sheet.jpg',quality=94)

def palette():
    # Uniform palette shared by all frames prevents quantization flicker.
    colors=[BG]
    for base in [INK,CYAN,GOLD,(157,160,226),(99,195,173),(229,166,149)]:
        for f in np.linspace(.08,1,40): colors.append(tuple(int(v) for v in np.array(BG)+(np.array(base)-BG)*f))
    colors.extend([(255,95,86),(255,189,46),(39,201,63),(48,54,61),(37,48,62),MUTED])
    colors=(colors+[BG]*256)[:256]
    p=Image.new('P',(1,1));p.putpalette([v for c in colors for v in c]);return p

def render():
    manifest={'fps':FPS,'width':W,'height':H,'scenes':[],'transitions':[]}
    fullpath=ROOT/'ascii-cinema.webp'; started=time.time(); frameidx=0
    # Pillow's streaming libwebp binding avoids retaining 1,890 raw RGB frames.
    encoder=_webp.WebPAnimEncoder((W,H),0xff0d1117,0,True,9,17,False,False)
    def emit(im):
        nonlocal frameidx
        encoder.add(im.convert('RGBA').getim(),frameidx*40,False,82,100,3)
        frameidx+=1
    clouds=[]
    for i,scene in enumerate(SCENES):
        n=round(scene[3]*FPS)
        print('Rendering',scene[2],n,'frames',flush=True)
        cloudlist=[project(model(scene[2],k/FPS,scene[3]),170 if scene[2]=='solar' else 205 if scene[2]=='ronaldo' else 225 if scene[2]=='steve' else 245) for k in range(n+1)]
        clouds.append(cloudlist)
    # Particle assembly is the opening; final transition returns directly to it.
    first=clouds[0][0]; rng=np.random.default_rng(7)
    last=clouds[-1][-1]
    seedxy=last[0]+rng.normal(0,26,last[0].shape)
    seedxy[:,0]=np.clip(seedxy[:,0],60,775);seedxy[:,1]=np.clip(seedxy[:,1],175,745)
    seed=(seedxy,last[1],np.array(BG)+(last[2]-BG)*.70)
    intro=Morph(seed,first)
    for k in range(40): emit(draw_cloud(canvas(SCENES[0],'ASSEMBLING',0),intro.frame(k/40)))
    for i,scene in enumerate(SCENES):
        start=frameidx
        for k,cloud in enumerate(clouds[i][:-1]):
            emit(draw_cloud(canvas(scene,'FORM / MOTION',k/(len(clouds[i])-1)),cloud))
        manifest['scenes'].append({'id':scene[2],'start':start,'frames':frameidx-start,'glyphs':len(clouds[i][0][0])})
        # Last-to-first morph uses the first sculpture, then loops through a held
        # matching first frame rather than scattering the whole subject again.
        j=(i+1)%len(SCENES); target=clouds[j][0] if j else seed
        morph=Morph(clouds[i][-1],target); start=frameidx
        for k in range(50):
            u=k/50
            phase='ASSEMBLING' if j==0 and u>.5 else 'REFORMING / '+SCENES[j][2].upper()
            frame=draw_cloud(canvas(scene if u<.5 else SCENES[j],phase,u if j else 0),morph.frame(u))
            emit(frame)
        manifest['transitions'].append({'from':scene[2],'to':SCENES[j][2],'start':start,'frames':50,'matched':len(morph.ia),'added':len(morph.add),'retired':len(morph.drop)})
        print('Encoded',scene[2],frameidx,'frames',flush=True)
    encoder.add(None,frameidx*40,False,82,100,0)
    fullpath.write_bytes(encoder.assemble('','',''))
    manifest.update(frames=frameidx,duration=frameidx/FPS,bytes=fullpath.stat().st_size)
    (OUT/'animation-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Done',frameidx,'frames',round(time.time()-started,1),'seconds',flush=True)

if __name__=='__main__':
    OUT.mkdir(exist_ok=True)
    parser=argparse.ArgumentParser(); parser.add_argument('--stills',action='store_true')
    args=parser.parse_args()
    if args.stills: stills()
    else: render()
