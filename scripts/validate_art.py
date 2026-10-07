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
    for name in ['ascii-motion.svg','contrib-heatmap.svg','stats.svg']:
        source = (root/name).read_text(encoding='utf-8')
        assert 'AVIVASHISHTA29' not in source and 'avi@github' not in source and 'Avi Vashishta' not in source
        doc = ET.fromstring(source)
        assert doc.tag == SVG+'svg'
        assert not doc.findall('.//'+SVG+'script')
        docs[name] = doc
    for name in ['ascii-motion.svg','stats.svg']:
        doc = docs[name]
        assert float(doc.attrib['width']) == 840 and float(doc.attrib['height']) == 880
        assert list(map(float,doc.attrib['viewBox'].split())) == [0,0,840,880]
    cells = docs['contrib-heatmap.svg'].findall('.//'+SVG+'rect')
    parsed = [{'date':c.attrib['data-date'],'count':int(c.attrib['data-count'])} for c in cells if 'data-date' in c.attrib]
    assert parsed == [{'date':d['date'],'count':d['count']} for d in data['days']], 'Calendar mismatch'
    final = [t.text for t in docs['stats.svg'].iter(SVG+'text') if t.attrib.get('class') == 'count-final']
    expected = [str(data['current_streak']['length']),str(data['longest_streak']['length']),f'{data["total_contributions"]:,}',str(data['active_days']),str(data['best_day']['count']),f'{data["avg_per_active_day"]:.1f}']
    assert final == expected, f'Stats mismatch: {final} vs {expected}'
    gallery = docs['ascii-motion.svg']
    frames = [g for g in gallery.iter(SVG+'g') if 'frame' in g.attrib.get('class','').split()]
    assert len(frames) == 256, 'Missing rotation frames'
    assert {int(g.attrib['data-object']) for g in frames} == set(range(16))
    assert [g.attrib['id'] for g in frames] == [f'frame-{i}' for i in range(256)]
    objects = [g for g in gallery.iter(SVG+'g') if g.attrib.get('class') == 'object']
    assert len(objects) == 16
    for obj in objects:
        assert len([t for t in obj.iter(SVG+'text') if t.attrib.get('class') == 'phase']) == 3
    for frame in frames:
        rows = list(frame.iter(SVG+'text'))
        assert len(rows) >= 10, 'Empty sculpture'
        assert all(row.text and set(row.text) <= set(' .,:;+=*#%@') for row in rows)
        assert all(32 <= float(row.attrib['x']) and float(row.attrib['x'])+len(row.text)*9.6 <= 808 for row in rows)
        assert all(194 <= float(row.attrib['y']) <= 746 for row in rows)
        assert all(row.tag == SVG+'text' for row in rows)
    style = gallery.find(SVG+'style').text
    assert all(s in style for s in ('infinite','prefers-reduced-motion','#frame-0','@keyframes assemble','@keyframes building','@keyframes dissolving'))
    print('Verified: matching panels; real calendar and 6 stats; 16 sculptures / 256 shaded views; build and dissolve phases')

if __name__ == '__main__':
    validate()
