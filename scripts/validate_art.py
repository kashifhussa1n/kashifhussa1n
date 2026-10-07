"""Verify identity, calendar values, SVG dimensions and all six final stats."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SVG = '{http://www.w3.org/2000/svg}'

def validate(root=ROOT):
    data = json.loads((root/'data/contributions.json').read_text(encoding='utf-8'))
    assert data['username'] == 'kashifhussa1n', 'Wrong profile identity'
    assert data['total_contributions'] == sum(d['count'] for d in data['days'])
    assert data['active_days'] == sum(d['count'] > 0 for d in data['days'])
    assert data['total_contributions'] == sum(m['total'] for m in data['monthly'])
    docs = {}
    for name in ['kashif-ascii.svg','contrib-heatmap.svg','stats.svg']:
        source = (root/name).read_text(encoding='utf-8')
        assert 'AVIVASHISHTA29' not in source and 'avi@github' not in source and 'Avi Vashishta' not in source
        doc = ET.fromstring(source)
        assert doc.tag == SVG+'svg'
        assert not doc.findall('.//'+SVG+'script')
        docs[name] = doc
    for name in ['kashif-ascii.svg','stats.svg']:
        doc = docs[name]
        assert float(doc.attrib['width']) == 840 and float(doc.attrib['height']) == 880
        assert list(map(float,doc.attrib['viewBox'].split())) == [0,0,840,880]
    cells = docs['contrib-heatmap.svg'].findall('.//'+SVG+'rect')
    parsed = [{'date':c.attrib['data-date'],'count':int(c.attrib['data-count'])} for c in cells if 'data-date' in c.attrib]
    assert parsed == [{'date':d['date'],'count':d['count']} for d in data['days']], 'Calendar mismatch'
    final = [t.text for t in docs['stats.svg'].iter(SVG+'text') if t.attrib.get('class') == 'count-final']
    expected = [str(data['current_streak']['length']),str(data['longest_streak']['length']),f'{data["total_contributions"]:,}',str(data['active_days']),str(data['best_day']['count']),f'{data["avg_per_active_day"]:.1f}']
    assert final == expected, f'Stats mismatch: {final} vs {expected}'
    rows = [g.find(SVG+'text').text for g in docs['kashif-ascii.svg'].iter(SVG+'g') if g.attrib.get('class') == 'portrait-row']
    assert len(rows) == 96 and all(len(row) == 180 for row in rows), 'Malformed portrait grid'
    assert any('@' in row for row in rows) and any(' ' in row for row in rows)
    print('Verified: 3 valid SVGs; equal 840 x 880 panels; all calendar dates/counts and 6 stats agree; 180 x 96 image-derived portrait')

if __name__ == '__main__':
    validate()
