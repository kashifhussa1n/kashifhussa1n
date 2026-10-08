"""Fetch GitHub's public calendar, fail closed on unknown markup, save real data.

Architecture adapted from AVIVASHISHTA29/AVIVASHISHTA29; standard library only.
No token, third-party service, copied snapshot or guessed contribution counts.
"""
from html.parser import HTMLParser
from pathlib import Path
import datetime as dt
import json
import os
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
USERNAME = os.environ.get('GH_PROFILE_USER', 'kashifhussa1n')
URL = f'https://github.com/users/{USERNAME}/contributions'

class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells, self.tips = [], {}
        self.tip = None
        self.text = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'td' and 'ContributionCalendar-day' in attrs.get('class', '').split() and attrs.get('data-date'):
            self.cells.append(attrs)
        if tag == 'tool-tip':
            self.tip, self.text = attrs.get('for'), []
    def handle_data(self, text):
        if self.tip:
            self.text.append(text)
    def handle_endtag(self, tag):
        if tag == 'tool-tip' and self.tip:
            self.tips[self.tip] = ''.join(self.text).strip()
            self.tip = None

def parse(text):
    parser = CalendarParser()
    parser.feed(text)
    days = []
    for cell in parser.cells:
        tip = parser.tips.get(cell.get('id'))
        if not tip:
            raise ValueError(f'Missing count tooltip for {cell["data-date"]}')
        if re.match(r'No contributions\b', tip, re.I):
            count = 0
        else:
            match = re.match(r'([\d,]+) contributions?\b', tip, re.I)
            if not match:
                raise ValueError(f'Unrecognized contribution count: {tip}')
            count = int(match[1].replace(',', ''))
        level = int(cell['data-level'])
        if not 0 <= level <= 4 or (count == 0) != (level == 0):
            raise ValueError('Invalid count or GitHub intensity level')
        days.append({'date':cell['data-date'], 'count':count, 'level':level})
    days.sort(key=lambda d:d['date'])
    if not 365 <= len(days) <= 372:
        raise ValueError(f'Expected a full calendar; received {len(days)} days')
    for a,b in zip(days,days[1:]):
        if dt.date.fromisoformat(b['date'])-dt.date.fromisoformat(a['date']) != dt.timedelta(days=1):
            raise ValueError('Calendar contains duplicate or missing dates')
    # Compare parsed counts to GitHub's own headline, not only our arithmetic.
    headline = re.search(r'([\d,]+)\s+contributions?\s+in the last year', text)
    if not headline or int(headline[1].replace(',','')) != sum(d['count'] for d in days):
        raise ValueError('Parsed counts do not agree with GitHub calendar headline')
    return days

def summarize(days):
    total = sum(d['count'] for d in days)
    active = sum(d['count'] > 0 for d in days)
    longest = run = 0
    longest_start = longest_end = run_start = None
    monthly = {}
    for day in days:
        key = day['date'][:7]
        monthly[key] = monthly.get(key, 0) + day['count']
        if day['count']:
            if not run:
                run_start = day['date']
            run += 1
            if run > longest:
                longest, longest_start, longest_end = run, run_start, day['date']
        else:
            run = 0
    idx = len(days)-1
    if not days[idx]['count']:
        idx -= 1
    end = idx
    current = 0
    while idx >= 0 and days[idx]['count']:
        current += 1
        idx -= 1
    return {'username':USERNAME, 'source_url':URL,
            'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),
            'range':{'start':days[0]['date'], 'end':days[-1]['date']},
            'total_contributions':total, 'active_days':active,
            'avg_per_active_day':round(total/active,1) if active else 0,
            'current_streak':{'length':current, 'start':days[idx+1]['date'] if current else None, 'end':days[end]['date'] if current else None},
            'longest_streak':{'length':longest,'start':longest_start,'end':longest_end},
            'best_day':max(days,key=lambda d:d['count']),
            'monthly':[{'month':k,'total':v} for k,v in monthly.items()], 'days':days}

def fetch():
    request = urllib.request.Request(URL, headers={'User-Agent':'kashif-profile-art/1.0'})
    with urllib.request.urlopen(request, timeout=30) as response:
        text = response.read().decode('utf-8')
    data = summarize(parse(text))
    target = ROOT / 'data/contributions.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(data,indent=2)+'\n', encoding='utf-8')
    print(f'{USERNAME}: {data["total_contributions"]} contributions, {data["active_days"]} active days, {len(data["days"])} verified dates')
    return data

if __name__ == '__main__':
    fetch()


