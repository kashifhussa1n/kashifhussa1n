"""Script-free SVG: real calendar cells lift into an automatically orbiting skyline."""
from pathlib import Path
import math, json, datetime as dt, html, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
COLORS = ['#121c18','#0e4429','#006d32','#26a641','#39d353']
TIMES = [0,.12] + [i/100 for i in range(14,91,2)] + [1]
DURATION = 18

def ease(v):
    v = min(1,max(0,v))
    return v*v*v*(10+v*(-15+6*v))

def pose(t):
    lift = ease((t-.12)/.18) * (1-ease((t-.72)/.18))
    orbit = ease((t-.30)/.42)
    yaw = lift * (.38 + .22*math.sin(math.pi*orbit))
    tilt = math.pi/2 - lift*.99
    return lift, yaw, tilt

def matrix(t):
    lift,yaw,tilt = pose(t)
    return (math.cos(yaw),math.sin(yaw)*math.sin(tilt),-math.sin(yaw),math.cos(yaw)*math.sin(tilt),430,163+lift*96)

def project(x,y,z,t):
    a,b,c,d,e,f = matrix(t)
    return (a*x+c*y+e,b*x+d*y+f-z*math.cos(pose(t)[2]))

def geometry(index,count,maximum,t,nweeks):
    col,row = divmod(index,7)
    pitch = 730/nweeks
    x,y = (col-nweeks/2)*pitch, (row-3.5)*pitch
    side = pitch-2.7
    height = (10+90*count/maximum)*pose(t)[0] if count else 0
    corners = [(x,y),(x+side,y),(x+side,y+side),(x,y+side)]
    base = [project(a,b,0,t) for a,b in corners]
    top = [project(a,b,height,t) for a,b in corners]
    return [ [base[1],base[2],top[2],top[1]], [base[2],base[3],top[3],top[2]], top ]

def shade(color,factor):
    return '#'+''.join(f'{int(int(color[i:i+2],16)*factor):02x}' for i in (1,3,5))

def fmt(points):
    return ' '.join(f'{x:.1f},{y:.1f}' for x,y in points)

def anim(attr,values):
    return f'<animate attributeName="{attr}" dur="{DURATION}s" repeatCount="indefinite" keyTimes="'+ ';'.join(str(t) for t in TIMES)+'" values="'+';'.join(values)+'"/>'

def text(x,y,value,size=13,color='#8b949e',weight=400):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}">{html.escape(str(value))}</text>'

def short_date(value):
    return dt.date.fromisoformat(value).strftime('%b %d').replace(' 0',' ') if value else '—'

def render(data,animated=True,t=.48):
    days=data['days']; nweeks=math.ceil(len(days)/7); pitch=730/nweeks
    total=data['total_contributions']; maximum=max(1,max(d['count'] for d in days))
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="860" height="490" viewBox="0 0 860 490" role="img" aria-labelledby="title desc">',
         f'<title id="title">{total:,} contributions in the last year · Kashif Hussain</title>',
         '<desc id="desc">Real GitHub contribution calendar. Each green square rises into a tower proportional to its contribution count, rotates gently, then returns to the calendar.</desc>',
         '<style>text{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif}</style>',
         '<rect x=".5" y=".5" width="859" height="489" rx="14" fill="#090c0b" stroke="#26322c"/>',
         text(30,39,f'{total:,} contributions in the last year',18,'#e6edf3',600),
         text(830,39,'',12),'<path d="M30 59H830" stroke="#1d2922"/>']
    if animated:
        out.append('<g class="motion">')
    initial=0 if animated else t
    # One affine transform moves the entire calendar floor; SMIL interpolates at display refresh rate.
    for kind,values in [('translate',lambda t:f'430 {matrix(t)[5]:.4f}'),('scale',lambda t:f'1 {math.sin(pose(t)[2]):.5f}'),('rotate',lambda t:f'{math.degrees(pose(t)[1]):.5f}')]:
        out.append(f'<g transform="{kind}({values(initial)})">')
        if animated:
            out.append(f'<animateTransform attributeName="transform" type="{kind}" dur="18s" repeatCount="indefinite" keyTimes="'+';'.join(str(t) for t in TIMES)+'" values="'+';'.join(values(t) for t in TIMES)+'"/>')
    for i,day in enumerate(days):
        col,row=divmod(i,7); x=(col-nweeks/2)*pitch; y=(row-3.5)*pitch
        out.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{pitch-2.7:.2f}" height="{pitch-2.7:.2f}" rx="1.4" fill="{COLORS[day["level"]]}"/>')
    out.append('</g></g></g>')
    # Back-to-front ordering; only nonzero days need three moving solid faces.
    for i in sorted(range(len(days)),key=lambda i:(i//7)*.48+(i%7)*.88):
        day=days[i]
        if not day['count']: continue
        out.append(f'<g data-date="{day["date"]}" data-count="{day["count"]}">')
        for face,factor in enumerate([.58,.78,1]):
            points=geometry(i,day['count'],maximum,initial,nweeks)[face]
            out.append(f'<polygon points="{fmt(points)}" fill="{shade(COLORS[day["level"]],factor)}" stroke="#080e0a" stroke-width=".25" stroke-linejoin="round">')
            if animated: out.append(anim('points',[fmt(geometry(i,day['count'],maximum,t,nweeks)[face]) for t in TIMES]))
            out.append('</polygon>')
        out.append('</g>')
    # Calendar labels fade as the grid changes perspective.
    out.append(f'<g opacity="{1-pose(initial)[0]:.2f}">')
    if animated: out.append(anim('opacity',[f'{1-pose(t)[0]:.3f}' for t in TIMES]))
    previous=None
    for i,day in enumerate(days):
        month=day['date'][:7]
        if month!=previous:
            if i//7< nweeks-2:
                out.append(text(65+(i//7)*pitch,98,dt.date.fromisoformat(day['date']).strftime('%b'),11))
            previous=month
    for row,label in [(1,'Mon'),(3,'Wed'),(5,'Fri')]: out.append(text(27,163+(row-3.5)*pitch+8,label,10))
    out.append('</g>')
    stats=[('1 year total',f'{total:,}','contributions',short_date(data['range']['start'])+' – '+short_date(data['range']['end']), (64,271),(616,104)),
           ('Busiest day',str(maximum if total else 0),'contributions',short_date(data['best_day']['date']), (450,271),(616,185)),
           ('Longest streak',str(data['longest_streak']['length']),'days',short_date(data['longest_streak']['start'])+' – '+short_date(data['longest_streak']['end']), (64,362),(45,347)),
           ('Current streak',str(data['current_streak']['length']),'days',short_date(data['current_streak']['start'])+' – '+short_date(data['current_streak']['end']), (450,362),(254,390))]
    for label,value,unit,date,flat,raised in stats:
        def pos(t):
            q=pose(t)[0]; return (flat[0]+(raised[0]-flat[0])*q,flat[1]+(raised[1]-flat[1])*q)
        x,y=pos(initial); out.append(f'<g transform="translate({x:.1f} {y:.1f})">')
        if animated: out.append('<animateTransform attributeName="transform" type="translate" dur="18s" repeatCount="indefinite" keyTimes="'+';'.join(str(t) for t in TIMES)+'" values="'+';'.join(f'{pos(t)[0]:.1f} {pos(t)[1]:.1f}' for t in TIMES)+'"/>')
        out.extend([text(0,0,label,12),text(0,31,value,30,'#39d353',600),text(len(value)*18+10,30,unit,12,'#c9d1d9'),text(0,51,date,11,'#67766d'),'</g>'])
    if animated: out.append('</g>')
    out.append('<path d="M30 447H830" stroke="#1d2922"/>')
    out.append(text(30,471,'kashifhussa1n · GitHub contributions',11,'#67766d'))
    out.append(text(682,471,'Less',10))
    for i,color in enumerate(COLORS): out.append(f'<rect x="{713+i*15}" y="461" width="11" height="11" rx="2" fill="{color}"/>')
    out.append(text(793,471,'More',10))
    out.append('</svg>')
    return '\n'.join(out)

def main():
    data=json.loads((ROOT/'data/contributions.json').read_text())
    assert sum(day['count'] for day in data['days'])==data['total_contributions']
    for animated,name,t in [(True,'contribution-skyline.svg',0),(False,'contribution-skyline-static.svg',.48)]:
        svg=render(data,animated,t); ET.fromstring(svg); (ROOT/name).write_text(svg,encoding='utf-8')
    # Every moving face returns to exactly its first coordinates at the loop boundary.
    for i,day in enumerate(data['days']):
        assert geometry(i,day['count'],max(1,data['best_day']['count']),0,math.ceil(len(data['days'])/7))==geometry(i,day['count'],max(1,data['best_day']['count']),1,math.ceil(len(data['days'])/7))
    print(f'Built skyline: {data["total_contributions"]} contributions; {len(data["days"])} days; seamless 18-second loop')

if __name__=='__main__': main()

