"""Minimal profile artwork. Public calendar values are verified before rendering."""
from pathlib import Path
import datetime as dt
import html, json, math, xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
BG='#0d1117'; PANEL='#11161d'; BORDER='#252c35'; INK='#e6edf3'; MUTED='#8b949e'; GREEN='#9bd4aa'

def txt(x,y,value,size=14,color=INK,weight=400,extra=''):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" {extra}>{html.escape(str(value))}</text>'

def rect(x,y,w,h,fill=PANEL,r=10,stroke=BORDER):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>'

def start(w,h,title):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img"><title>{html.escape(title)}</title>',
            '<style>text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}</style>',f'<rect width="{w}" height="{h}" fill="{BG}"/>']

def chips(out,x,y,labels):
    for label in labels:
        w=len(label)*6.6+24
        out.extend([rect(x,y,w,26,'#17231e',13,'#294133'),txt(x+12,y+17,label,12,GREEN)])
        x+=w+8

def overview(d):
    out=start(860,650,'Kashif Hussain — development and motion design')
    out.extend([rect(1,1,858,143),txt(27,31,'DEVELOPMENT  /  MOTION DESIGN',11,GREEN,600,'letter-spacing="1.6"'),
                txt(26,78,'Kashif Hussain',35,INK,650),
                txt(27,108,'Computer science student. Building software and creating motion.',15,MUTED),
                '<path d="M760 44l-16 16 16 16m35-32 16 16-16 16m-17-36-11 40" fill="none" stroke="#536e60" stroke-width="2" stroke-linecap="round"/>'])
    metrics=[('CONTRIBUTIONS',d['total_contributions']),('ACTIVE DAYS',d['active_days']),('LONGEST STREAK',str(d['longest_streak']['length'])+' days'),('BUSIEST DAY',d['best_day']['count'])]
    for i,(label,value) in enumerate(metrics):
        x=1+i*218
        out.extend([rect(x,156,204,85),txt(x+18,193,value,25,INK,600),txt(x+18,219,label,10,MUTED,500,'letter-spacing="1"')])
    out.extend([rect(1,253,858,195),txt(25,282,'Contribution activity',15,INK,600),txt(835,281,'Past year · public calendar',11,MUTED,400,'text-anchor="end"')])
    days=d['days']; n=math.ceil(len(days)/7); pitch=764/n; cell=pitch-3
    colors=['#1b222a','#0e4429','#006d32','#26a641','#39d353']
    last=None
    for i,day in enumerate(days):
        col,row=divmod(i,7); x=65+col*pitch; y=316+row*14
        month=day['date'][:7]
        if month!=last and col<n-2:
            out.append(txt(x,307,dt.date.fromisoformat(day['date']).strftime('%b'),10,MUTED));last=month
        out.append(f'<rect data-date="{day["date"]}" data-count="{day["count"]}" x="{x:.2f}" y="{y}" width="{cell:.2f}" height="11" rx="2" fill="{colors[day["level"]]}"/>')
    for row,label in [(1,'Mon'),(3,'Wed'),(5,'Fri')]:out.append(txt(25,325+row*14,label,9,MUTED))
    out.append(txt(25,432,dt.date.fromisoformat(d['range']['start']).strftime('%b %Y')+' – '+dt.date.fromisoformat(d['range']['end']).strftime('%b %Y'),10,MUTED))
    out.append(txt(700,431,'Less',9,MUTED))
    for i,c in enumerate(colors):out.append(rect(727+i*14,422,10,10,c,2,c))
    out.append(txt(802,431,'More',9,MUTED))
    out.extend([rect(1,460,423,189),rect(436,460,423,189),
                txt(25,491,'Development',18,INK,600),txt(460,491,'Motion design',18,INK,600),
                txt(25,516,'Automation, APIs and programming fundamentals.',12,MUTED),
                txt(460,516,'Video editing and visual storytelling.',12,MUTED)])
    chips(out,25,536,['Python','Java','HTML'])
    chips(out,460,536,['Motion graphics','Video editing'])
    out.extend([txt(25,593,'EXPLORING',10,GREEN,600,'letter-spacing="1"'),txt(25,618,'AI / ML · building through practice',13,MUTED),
                txt(460,593,'CREATING',10,GREEN,600,'letter-spacing="1"'),txt(460,618,'Long-form videos · short-form edits',13,MUTED),'</svg>'])
    return '\n'.join(out)

def project(kind):
    out=start(420,177,'CS2 Trade-Up Bot' if kind=='code' else 'Motion and video portfolio')
    out.append(rect(1,1,418,175))
    out.extend([txt(23,29,'DEVELOPMENT' if kind=='code' else 'MOTION & VIDEO',10,GREEN,600,'letter-spacing="1.5"'),txt(385,30,'↗',20,MUTED),
                txt(23,61,'CS2 Trade-Up Bot' if kind=='code' else 'Selected edits',21,INK,600)])
    lines=['A Python tool for trade-up searches,','live listing checks and Discord reports.'] if kind=='code' else ['Long- and short-form video work','for creators and brands.']
    for i,line in enumerate(lines):out.append(txt(23,90+i*19,line,13,MUTED))
    out.extend([txt(23,149,'Python  ·  APIs  ·  Automation' if kind=='code' else 'Motion design  ·  Video editing',11,GREEN),'</svg>'])
    return '\n'.join(out)

def main():
    d=json.loads((ROOT/'data/contributions.json').read_text())
    assert sum(x['count'] for x in d['days'])==d['total_contributions']
    target=ROOT/'assets';target.mkdir(exist_ok=True)
    for name,svg in [('profile-overview.svg',overview(d)),('project-code.svg',project('code')),('project-motion.svg',project('motion'))]:
        root=ET.fromstring(svg)
        assert not any(e.tag.endswith('script') for e in root.iter())
        if name=='profile-overview.svg':
            cells=[e for e in root.iter() if 'data-count' in e.attrib]
            assert len(cells)==len(d['days'])
            assert sum(int(e.attrib['data-count']) for e in cells)==d['total_contributions']
        (target/name).write_text(svg,encoding='utf-8')
    print(f'Profile rendered with {d["total_contributions"]} verified contributions')

if __name__=='__main__':main()

