"""Render the reference's slim pop-in calendar from our verified local snapshot."""
from pathlib import Path
import datetime as dt
import json
from html import escape

ROOT = Path(__file__).resolve().parents[1]
PALETTE = ['#161b22','#0e4429','#006d32','#26a641','#39d353']

def render(data):
    days = data['days']
    first = dt.date.fromisoformat(days[0]['date'])
    sunday = first-dt.timedelta(days=(first.weekday()+1)%7)
    last = dt.date.fromisoformat(days[-1]['date'])
    weeks = (last-sunday).days//7+1
    w,h = 34+weeks*16+6,158
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif" role="img">',
             f'<title>{escape(data["username"])} — {data["total_contributions"]} real GitHub contributions</title>',
             '<style>text.lbl{fill:#7d8590;font-size:13px;font-weight:600}text.total{fill:#e6edf3;font-size:15px;font-weight:700}.c{transform-box:fill-box;transform-origin:center;opacity:0;animation:pop .55s ease-out both}.g{animation:pop .55s ease-out both,flash .7s ease-out both}@keyframes pop{0%{opacity:0;transform:scale(.2)}60%{opacity:1;transform:scale(1.1)}100%{opacity:1;transform:scale(1)}}@keyframes flash{0%,45%{filter:brightness(2.4)}100%{filter:brightness(1)}}@media(prefers-reduced-motion:reduce){.c{opacity:1!important;animation:none!important;transform:none!important}}</style>']
    last_month = None
    for week in range(weeks):
        day = max(first,sunday+dt.timedelta(days=week*7))
        month = day.strftime('%Y-%m')
        if month != last_month:
            parts.append(f'<text class="lbl" x="{34+week*16}" y="16">{day.strftime("%b")}</text>')
            last_month = month
    for name,row in [('Mon',1),('Wed',3),('Fri',5)]:
        parts.append(f'<text class="lbl" x="2" y="{24+row*16+11}">{name}</text>')
    maxorder = weeks-1+6*.55
    for day in days:
        offset = (dt.date.fromisoformat(day['date'])-sunday).days
        week,row = divmod(offset,7)
        delay = (week+row*.55)/maxorder*3.6
        level = day['level']
        parts.append(f'<rect class="c {"g" if level else "e"}" x="{34+week*16}" y="{24+row*16}" width="13" height="13" rx="2.5" fill="{PALETTE[level]}" data-date="{day["date"]}" data-count="{day["count"]}" style="animation-delay:{delay:.3f}s"><title>{day["date"]}: {day["count"]} contributions</title></rect>')
    parts.append(f'<text class="total" x="34" y="152">{data["total_contributions"]:,} contributions in the last year</text></svg>')
    return ''.join(parts)

if __name__ == '__main__':
    data = json.loads((ROOT/'data/contributions.json').read_text(encoding='utf-8'))
    (ROOT/'contrib-heatmap.svg').write_text(render(data),encoding='utf-8')
    print(f'Heatmap: {len(data["days"])} dates, {data["total_contributions"]} contributions')
