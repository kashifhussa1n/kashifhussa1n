"""Check real-date mapping, SVG integrity, camera bounds and loop continuity."""
import json, math, unittest, datetime as dt
import xml.etree.ElementTree as ET
from render_skyline import ROOT, geometry, render

class SkylineTests(unittest.TestCase):
    def test_calendar_and_encoded_counts(self):
        data=json.loads((ROOT/'data/contributions.json').read_text())
        days=data['days']
        self.assertEqual(dt.date.fromisoformat(days[0]['date']).weekday(),6)
        self.assertEqual(sum(d['count'] for d in days),data['total_contributions'])
        root=ET.fromstring(render(data))
        encoded={e.attrib['data-date']:int(e.attrib['data-count']) for e in root.iter() if 'data-date' in e.attrib}
        self.assertEqual(encoded,{d['date']:d['count'] for d in days if d['count']})
        for e in root.iter():
            self.assertFalse(e.tag.endswith('script'))
            if 'values' in e.attrib:
                values=e.attrib['values'].split(';')
                self.assertEqual(len(values),len(e.attrib['keyTimes'].split(';')))
                self.assertEqual(values[0],values[-1])

    def test_camera_extremes_and_linear_height(self):
        for i in range(371):
            for step in range(51):
                for face in geometry(i,30,30,step/50,53):
                    for x,y in face:
                        self.assertTrue(25<x<835 and 65<y<430,(i,step,x,y))
        # A day with twice the contributions has exactly twice the tower height.
        a=geometry(120,10,30,.5,53)
        b=geometry(120,20,30,.5,53)
        self.assertAlmostEqual((a[0][0][1]-a[0][3][1])*2,b[0][0][1]-b[0][3][1])

if __name__=='__main__': unittest.main()

