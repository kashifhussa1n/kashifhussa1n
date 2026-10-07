"""Render a deterministic, script-free rotating ASCII sculpture gallery."""
from pathlib import Path
from math import sin, cos, pi, sqrt
from html import escape

ROOT = Path(__file__).resolve().parents[1]
COLS, ROWS, FRAMES = 62, 28, 16
HOLD = 6.0
BUILD, SPIN, DISSOLVE = .6, 4.8, .6

def unit(p):
    size=sqrt(sum(v*v for v in p))
    return tuple(v/size for v in p) if size else (0,0,1)

def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])

def sculpture(lines,name):
    """Give curves real thickness and surface normals before projecting them."""
    radius={'TREFOIL KNOT':.10,'GYROSCOPE':.055,'DOUBLE HELIX':.05,
            'ORBITAL ATOM':.035,'MOBIUS STRIP':.025,'UV SPHERE':.025,
            'TORUS':.028,'GEAR':.035}.get(name,.035)
    points=[]
    for a,b in lines:
        axis=unit(tuple(y-x for x,y in zip(a,b)))
        u=unit(cross(axis,(0,0,1) if abs(axis[2])<.9 else (1,0,0)))
        v=cross(axis,u)
        steps=max(1,int(sqrt(sum((x-y)**2 for x,y in zip(a,b)))/.025))
        for j in range(steps+1):
            p=tuple(x+(y-x)*j/steps for x,y in zip(a,b))
            for k in range(10):
                t=2*pi*k/10
                normal=tuple(x*cos(t)+y*sin(t) for x,y in zip(u,v))
                points.append((tuple(x+radius*n for x,n in zip(p,normal)),normal))
    return points

def curve(fn, n=150, closed=True):
    p = [fn(2*pi*i/n) for i in range(n + int(closed))]
    return list(zip(p, p[1:]))

def edges(vertices, pairs):
    return [(vertices[a], vertices[b]) for a,b in pairs]

def ring(r=1, z=0):
    return curve(lambda t:(r*cos(t),r*sin(t),z))

def gallery():
    cube = [(x,y,z) for x in (-.8,.8) for y in (-.8,.8) for z in (-.8,.8)]
    cube_edges = edges(cube, [(i,j) for i in range(8) for j in range(i) if sum(a!=b for a,b in zip(cube[i],cube[j]))==1])
    sphere = []
    for a in (-pi/3,-pi/6,0,pi/6,pi/3): sphere += ring(cos(a), sin(a))
    for a in [i*pi/6 for i in range(6)]: sphere += curve(lambda t,a=a:(cos(t)*cos(a),cos(t)*sin(a),sin(t)))
    pyramid=edges([(-.9,-.9,-.6),(.9,-.9,-.6),(.9,.9,-.6),(-.9,.9,-.6),(0,0,1.1)],[(0,1),(1,2),(2,3),(3,0),(0,4),(1,4),(2,4),(3,4)])
    torus=[]
    for v in [i*pi/4 for i in range(8)]: torus += curve(lambda u,v=v:((.78+.3*cos(v))*cos(u),(.78+.3*cos(v))*sin(u),.3*sin(v)))
    for u in [i*pi/8 for i in range(16)]: torus += curve(lambda v,u=u:((.78+.3*cos(v))*cos(u),(.78+.3*cos(v))*sin(u),.3*sin(v)))
    def knot(t): return ((.75+.28*cos(3*t))*cos(2*t),(.75+.28*cos(3*t))*sin(2*t),.38*sin(3*t))
    trefoil = curve(knot,300)
    mobius=[]
    for s in (-.35,-.17,0,.17,.35): mobius += curve(lambda t,s=s:((.8+s*cos(t/2))*cos(t),(.8+s*cos(t/2))*sin(t),s*sin(t/2)),200)
    for t in [i*pi/18 for i in range(36)]: mobius += [(((.8-.35*cos(t/2))*cos(t),(.8-.35*cos(t/2))*sin(t),-.35*sin(t/2)),((.8+.35*cos(t/2))*cos(t),(.8+.35*cos(t/2))*sin(t),.35*sin(t/2)))]
    gyro = ring(1.1)+curve(lambda t:(.92*cos(t),0,.92*sin(t)))+curve(lambda t:(0,.72*cos(t),.72*sin(t)))+edges([(0,0,-1.2),(0,0,1.2)],[(0,1)])
    atom=[]
    for a in [0,pi/3,2*pi/3]: atom += curve(lambda t,a=a:(1.15*cos(t),.45*sin(t)*cos(a),.95*sin(t)*sin(a)))
    atom+=curve(lambda t:(.18*cos(t),.18*sin(t),0))
    helix=[]
    for a in (0,pi): helix+=curve(lambda t,a=a:(.48*cos(2*t+a),.48*sin(2*t+a),(t/pi-1)*1.1),180,False)
    for i in range(22):
        t=2*pi*i/21; z=(t/pi-1)*1.1
        helix+=[((.48*cos(2*t),.48*sin(2*t),z),(-.48*cos(2*t),-.48*sin(2*t),z))]
    phi=(1+sqrt(5))/2
    ico=[(0,a,b*phi) for a in (-1,1) for b in (-1,1)]+[(a,b*phi,0) for a in (-1,1) for b in (-1,1)]+[(a*phi,0,b) for a in (-1,1) for b in (-1,1)]
    ico_edges=[(i,j) for i in range(12) for j in range(i) if abs(sum((a-b)**2 for a,b in zip(ico[i],ico[j]))-4)<.001]
    ico=edges([tuple(q*.61 for q in p) for p in ico],ico_edges)
    crystal=[]
    vertices=[(.6*cos(i*pi/3),.6*sin(i*pi/3),z) for z in (-.6,.6) for i in range(6)]+[(0,0,-1.2),(0,0,1.2)]
    for i in range(6): crystal+=edges(vertices,[(i,(i+1)%6),(i+6,(i+1)%6+6),(i,i+6),(i,12),(i+6,13)])
    ship=edges([(0,1.25,0),(-.25,-.8,.2),(.25,-.8,.2),(0,-.8,-.2),(-1.2,-.9,0),(1.2,-.9,0),(0,-.2,.6),(0,-.65,0)],[(0,1),(0,2),(0,3),(1,2),(2,3),(3,1),(0,4),(4,1),(0,5),(5,2),(0,6),(6,1),(6,2),(1,7),(2,7)])
    gear=[]
    for z in (-.2,.2):
        gear+=curve(lambda t,z=z:((.93+.15*(1 if cos(12*t)>0 else -1))*cos(t),(.93+.15*(1 if cos(12*t)>0 else -1))*sin(t),z),240)+ring(.35,z)
    for i in range(48):
        t=2*pi*i/48; r=.93+.15*(1 if cos(12*t)>0 else -1)
        gear+=[((r*cos(t),r*sin(t),-.2),(r*cos(t),r*sin(t),.2))]
    wave=[]
    for j in range(11):
        y=(j-5)/5
        wave+=curve(lambda t,y=y:((t/pi-1),y,.28*sin(4*(t/pi-1)+3*y)),80,False)
        x=y
        wave+=curve(lambda t,x=x:(x,(t/pi-1),.28*sin(4*x+3*(t/pi-1))),80,False)
    star=[]
    v=[(0,0,1.2),(0,0,-1.2),(1.2,0,0),(-1.2,0,0),(0,1.2,0),(0,-1.2,0)]
    star=edges(v,[(i,j) for i in range(6) for j in range(i) if i//2 != j//2])
    small=[tuple(q*.5 for q in p) for p in cube]
    tesseract=cube_edges+edges(small,[(i,j) for i in range(8) for j in range(i) if sum(a!=b for a,b in zip(small[i],small[j]))==1])+list(zip(cube,small))
    return [('CUBE','the starting point',cube_edges),('UV SPHERE','latitude / longitude',sphere),('PYRAMID','four faces / one apex',pyramid),('TORUS','a loop with depth',torus),('TREFOIL KNOT','one curve / three crossings',trefoil),('MOBIUS STRIP','one surface / one edge',mobius),('GYROSCOPE','three axes in balance',gyro),('ORBITAL ATOM','paths around a core',atom),('DOUBLE HELIX','two strands / one rhythm',helix),('ICOSAHEDRON','twenty triangular faces',ico),('HEX CRYSTAL','symmetry in six directions',crystal),('SPACECRAFT','built for the next orbit',ship),('GEAR','twelve teeth in motion',gear),('WAVE FIELD','a surface made of signals',wave),('OCTAHEDRON','eight faces / six vertices',star),('NESTED CUBES','a tesseract-inspired projection',tesseract)]

def render(points, angle):
    grid=[[' ']*COLS for _ in range(ROWS)]
    depth=[[-100.]*COLS for _ in range(ROWS)]
    def rotate(p):
        x,y,z=p
        x,z=x*cos(angle)+z*sin(angle),-x*sin(angle)+z*cos(angle)
        tilt=.42+.18*sin(angle); y,z=y*cos(tilt)-z*sin(tilt),y*sin(tilt)+z*cos(tilt)
        roll=.12*sin(angle*.5); x,y=x*cos(roll)-y*sin(roll),x*sin(roll)+y*cos(roll)
        return x,y,z
    palette='.,:;+=*#%@'
    for p,normal in points:
        x,y,z=rotate(p); nx,ny,nz=rotate(normal)
        if nz<-.2: continue
        scale=5/(5-z)
        ix,iy=int(COLS/2+x*18*scale),int(ROWS/2-y*8.5*scale)
        if 0<=ix<COLS and 0<=iy<ROWS and z>=depth[iy][ix]:
            light=max(0,-.4*nx+.5*ny+.76*nz)
            brightness=.15+.7*light+.15*(z+1.4)/2.8
            grid[iy][ix]=palette[max(0,min(9,int(brightness*9)))]
            depth[iy][ix]=z
    return [''.join(row).rstrip() for row in grid]

def main():
    collection=gallery()
    objects=[collection[i] for i in (4,5,6,8,9,10,11,12,13,15,7,3,14,0,1,2)]
    total=len(objects)*FRAMES; duration=len(objects)*HOLD
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="840" height="880" viewBox="0 0 840 880" role="img" aria-labelledby="title desc">', '<title id="title">Kashif\'s rotating ASCII object gallery</title>','<desc id="desc">Sixteen depth-shaded ASCII sculptures assemble from scattered characters, rotate through sixteen 3D views, dissolve, and repeat. Cube, sphere, pyramid, torus, trefoil knot, Mobius strip, gyroscope, orbital atom, double helix, icosahedron, crystal, spacecraft, gear, wave field, octahedron and nested cubes.</desc>','<defs><linearGradient id="bg" x2="0" y2="1"><stop stop-color="#0d1117"/><stop offset="1" stop-color="#111722"/></linearGradient></defs>']
    pct=lambda seconds: f'{100*seconds/duration:.6f}%'
    css=f'.object{{opacity:0;animation:object {duration}s steps(1,end) infinite}}.frame{{opacity:0;animation:frame {duration}s steps(1,end) infinite}}.edge-view{{animation-name:edge}}.frame text{{white-space:pre;animation:assemble {duration}s ease-in-out infinite;animation-delay:var(--delay)}}.phase{{opacity:0;animation-duration:{duration}s;animation-timing-function:steps(1,end);animation-iteration-count:infinite}}'
    for row in range(ROWS):
        dx=(row*31)%181-90; dy=(row*19)%101-50
        css+=f'.frame text:nth-child({row+1}){{--dx:{dx}px;--dy:{dy}px;--ex:{-dx*1.5:g}px;--ey:{dy*1.5:g}px}}'
    for key,seconds in [('object',HOLD),('frame',SPIN/FRAMES),('edge',BUILD+SPIN/FRAMES),('building',BUILD),('rotating',SPIN),('dissolving',DISSOLVE)]:
        css+=f'@keyframes {key}{{0%,{pct(seconds-.00001)}{{opacity:1}}{pct(seconds)},100%{{opacity:0}}}}'
    css+=f'@keyframes assemble{{0%{{opacity:0;transform:translate(var(--dx),var(--dy))}}{pct(BUILD)}{{opacity:1;transform:translate(0px,0px)}}{pct(HOLD-DISSOLVE)}{{opacity:1;transform:translate(0px,0px)}}{pct(HOLD)},100%{{opacity:0;transform:translate(var(--ex),var(--ey))}}}}'
    css+='@media(prefers-reduced-motion:reduce){.object,.frame,.frame text,.phase{animation:none;opacity:0;transform:none}#object-0,#frame-0,#frame-0 text{opacity:1}}'
    out += ['<defs><linearGradient id="ink" x1="0" y1="0" x2=".8" y2="1"><stop stop-color="#e3f6ff"/><stop offset=".5" stop-color="#79c0ff"/><stop offset="1" stop-color="#287ab8"/></linearGradient><clipPath id="art-area"><rect x="32" y="160" width="776" height="602"/></clipPath></defs>',f'<style>{css}</style>','<rect x="1" y="1" width="838" height="878" rx="14" fill="url(#bg)" stroke="#30363d"/>','<path d="M1 31H839" stroke="#30363d"/>','<circle cx="20" cy="16" r="4" fill="#ff5f57"/><circle cx="36" cy="16" r="4" fill="#febc2e"/><circle cx="52" cy="16" r="4" fill="#28c840"/>','<g font-family="ui-monospace,SFMono-Regular,Consolas,monospace"><text x="420" y="20" text-anchor="middle" font-size="12" fill="#8b949e">kashif@github: ~$ ./objects.py</text>','<text x="32" y="66" font-size="13" fill="#8b949e">GEOMETRY LAB <tspan fill="#484f58">/</tspan> ASCII SCULPTURES</text>','<path d="M32 794H808" stroke="#30363d"/>','<text x="32" y="827" font-size="14" fill="#8b949e">BUILD <tspan fill="#484f58">/</tspan> ROTATE <tspan fill="#484f58">/</tspan> DISSOLVE <tspan fill="#484f58">/</tspan> REPEAT</text>','<text x="32" y="852" font-size="12" fill="#58a6ff">learning by building. one dimension at a time.</text>']
    for i,(name,subtitle,lines) in enumerate(objects):
        object_delay=i*HOLD-duration
        points=sculpture(lines,name)
        out += [f'<g id="object-{i}" class="object" style="animation-delay:{object_delay:g}s;--delay:{object_delay:g}s">',f'<text x="32" y="110" fill="#e6edf3" font-size="25" font-weight="600">{name}</text>',f'<text x="32" y="136" fill="#8b949e" font-size="13">{subtitle}</text>',f'<text x="808" y="109" fill="#58a6ff" font-size="14" text-anchor="end">{i+1:02d} / {len(objects):02d}</text>']
        for phase,start in [('building',0),('rotating',BUILD),('dissolving',HOLD-DISSOLVE)]:
            out.append(f'<text x="808" y="781" text-anchor="end" font-size="12" fill="#58a6ff" class="phase" style="animation-name:{phase};animation-delay:{object_delay+start:g}s">{phase.upper()}...</text>')
        out.append('<g clip-path="url(#art-area)" fill="url(#ink)" font-family="monospace" font-size="16" xml:space="preserve">')
        for f in range(FRAMES):
            n=i*FRAMES+f; start=0 if f==0 else BUILD+f*SPIN/FRAMES
            delay=object_delay+start
            edge=' edge-view' if f in (0,FRAMES-1) else ''
            out += [f'<g id="frame-{n}" class="frame{edge}" data-object="{i}" style="animation-delay:{delay:g}s">']
            for row,line in enumerate(render(points, f*2*pi/FRAMES+.35)):
                if line:
                    lead=len(line)-len(line.lstrip())
                    out.append(f'<text x="{122+lead*9.6:g}" y="{194+row*20:g}">{escape(line.lstrip())}</text>')
            out += ['</g>']
        out += ['</g></g>']
    out += ['</g></svg>']
    path=ROOT/'ascii-objects.svg'; path.write_text(''.join(out),encoding='utf-8')
    print(f'{len(objects)} objects; {total} perspective frames; {duration:g}s loop; {path.stat().st_size:,} bytes')

if __name__ == '__main__': main()
