#!/usr/bin/env python3
"""Refresh the public profile artwork from Kashif's GitHub contribution calendar."""
from __future__ import annotations
import datetime as dt, html, re, urllib.request
from collections import defaultdict
from pathlib import Path

USER="kashifhussa1n"
ROOT=Path(__file__).resolve().parents[1]
URL=f"https://github.com/users/{USER}/contributions"

def fetch():
    req=urllib.request.Request(URL,headers={"User-Agent":"kashif-profile-readme/1.0"})
    text=urllib.request.urlopen(req,timeout=30).read().decode("utf-8")
    cells=re.findall(r'<td[^>]*class="[^"]*ContributionCalendar-day[^"]*"[^>]*>',text)
    days=[]
    for tag in cells:
        d=re.search(r'data-date="([^"]+)"',tag)
        ident=re.search(r'id="([^"]+)"',tag)
        level=re.search(r'data-level="(\d+)"',tag)
        if not d: continue
        count=0
        if ident:
            tip=re.search(r'<tool-tip[^>]*for="'+re.escape(ident.group(1))+r'"[^>]*>(.*?)</tool-tip>',text,re.S)
            if tip:
                plain=re.sub("<[^>]+>","",tip.group(1)).strip()
                m=re.match(r'([\d,]+) contribution',plain,re.I)
                if m: count=int(m.group(1).replace(",",""))
        days.append({"date":dt.date.fromisoformat(d.group(1)),"count":count,"level":int(level.group(1)) if level else 0})
    if not days: raise RuntimeError("GitHub contribution calendar markup was not recognized")
    return sorted(days,key=lambda x:x["date"])

def esc(s): return html.escape(str(s))

def heatmap(days):
    W,H=860,190; left,top=36,42; cell,gap=11,3; pitch=cell+gap
    by={x["date"]:x for x in days}; end=max(by); start=end-dt.timedelta(days=370)
    start-=dt.timedelta(days=(start.weekday()+1)%7)
    levels=["#161b22","#0e4429","#006d32","#26a641","#39d353"]
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
         '<style>.c{opacity:0;animation:p .28s ease-out forwards}@keyframes p{to{opacity:1}}@media(prefers-reduced-motion:reduce){.c{opacity:1;animation:none}}</style>',
         '<rect width="860" height="190" rx="14" fill="#0d1117"/><rect x=".5" y=".5" width="859" height="189" rx="14" fill="none" stroke="#30363d"/>',
         '<text x="20" y="24" fill="#7d8590" font-size="12">kashif@github: ~$ ./contributions.sh</text>']
    for week in range(53):
        for dow in range(7):
            date=start+dt.timedelta(days=week*7+dow); item=by.get(date,{"count":0,"level":0})
            x=left+week*pitch; y=top+dow*pitch; delay=(week*7+dow)*.006
            out.append(f'<rect class="c" style="animation-delay:{delay:.3f}s" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{levels[min(4,item["level"])]}"><title>{item["count"]} contributions on {date}</title></rect>')
    total=sum(x["count"] for x in days)
    out.append(f'<text x="20" y="174" fill="#7d8590" font-size="12">{total:,} contributions in the displayed calendar · refreshed daily</text></svg>')
    (ROOT/"contrib-heatmap.svg").write_text("".join(out),encoding="utf-8")

def streaks(days):
    cur=0
    seq=days[:-1] if days and days[-1]["count"]==0 else days
    for x in reversed(seq):
        if x["count"]<=0: break
        cur+=1
    longest=run=0
    for x in days:
        run=run+1 if x["count"]>0 else 0; longest=max(longest,run)
    return cur,longest

def stats(days):
    total=sum(x["count"] for x in days); active=sum(x["count"]>0 for x in days); cur,longest=streaks(days)
    best=max(days,key=lambda x:x["count"])
    monthly=defaultdict(int)
    for x in days: monthly[x["date"].strftime("%b")]+=x["count"]
    recent=list(monthly.items())[-12:]; peak=max([v for _,v in recent] or [1])
    W,H=840,880
    cards=[("current streak",cur,"days"),("longest streak",longest,"days"),("contributions",total,"last year"),("active days",active,"days"),("best day",best["count"],best["date"].strftime("%b %d")),("avg / active",round(total/active,1) if active else 0,"contributions")]
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
         '<style>.a{opacity:0;transform:translateY(10px);animation:i .45s ease-out forwards}@keyframes i{to{opacity:1;transform:translateY(0)}}@media(prefers-reduced-motion:reduce){.a{opacity:1;transform:none;animation:none}}</style>',
         '<defs><linearGradient id="g" x2="0" y2="1"><stop stop-color="#111722"/><stop offset="1" stop-color="#0d1117"/></linearGradient></defs><rect width="840" height="880" rx="14" fill="url(#g)"/><rect x=".5" y=".5" width="839" height="879" rx="14" fill="none" stroke="#30363d"/><line y1="30" x2="840" y2="30" stroke="#30363d"/><circle cx="20" cy="15" r="5" fill="#ff5f56"/><circle cx="36" cy="15" r="5" fill="#ffbd2e"/><circle cx="52" cy="15" r="5" fill="#27c93f"/><text x="420" y="19" fill="#7d8590" font-size="12" text-anchor="middle">kashif@github: ~$ ./stats.sh</text>']
    for i,(label,value,caption) in enumerate(cards):
        col=i%2; row=i//2; x=20+col*408; y=54+row*158
        out.append(f'<g class="a" style="animation-delay:{i*.12:.2f}s"><rect x="{x}" y="{y}" width="392" height="142" rx="10" fill="#161b22" stroke="#30363d"/><text x="{x+22}" y="{y+34}" fill="#7d8590" font-size="19">$ {esc(label)}</text><text x="{x+22}" y="{y+91}" fill="#e6edf3" font-size="45" font-weight="700">{esc(value)}</text><text x="{x+22}" y="{y+122}" fill="#7d8590" font-size="17">{esc(caption)}</text></g>')
    chart_y=550; out.append(f'<rect x="20" y="{chart_y}" width="800" height="292" rx="10" fill="#161b22" stroke="#30363d"/><text x="42" y="{chart_y+38}" fill="#7d8590" font-size="19">$ contributions / month</text>')
    for i,(mon,val) in enumerate(recent):
        h=180*val/peak if peak else 0; x=48+i*62; y=chart_y+238-h
        out.append(f'<rect x="{x}" y="{y:.1f}" width="36" height="{max(2,h):.1f}" rx="3" fill="#26a641"/><text x="{x+18}" y="{chart_y+267}" fill="#7d8590" font-size="13" text-anchor="middle">{esc(mon[0])}</text>')
    out.append('</svg>'); (ROOT/"stats.svg").write_text("".join(out),encoding="utf-8")

if __name__=="__main__":
    d=fetch(); heatmap(d); stats(d); print(f"refreshed profile art for {USER}: {len(d)} calendar days")
