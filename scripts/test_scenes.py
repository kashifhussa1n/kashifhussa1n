"""Behavioral tests for glyph population changes and the jump camera framing."""
import unittest
import numpy as np
from render_scenes import Morph,ronaldo,ROWS,CH

class Transitions(unittest.TestCase):
    def assert_cloud(self,actual,expected):
        xy,g,rgb,alpha=actual
        visible=alpha>.999
        # Every input glyph survives at the endpoint, with no extra particles.
        self.assertEqual(np.count_nonzero(visible),len(expected[0]))
        result=sorted(tuple(np.r_[p,gg,c].round(6)) for p,gg,c in zip(xy[visible],g[visible],rgb[visible]))
        target=sorted(tuple(np.r_[p,gg,c].round(6)) for p,gg,c in zip(*expected))
        self.assertEqual(result,target)

    def test_population_changes_preserve_endpoints(self):
        rng=np.random.default_rng(21)
        for na,nb in [(30,70),(70,30),(40,40)]:
            a=(rng.uniform(100,700,(na,2)),rng.integers(1,11,na),rng.uniform(40,240,(na,3)))
            b=(rng.uniform(100,700,(nb,2)),rng.integers(1,11,nb),rng.uniform(40,240,(nb,3)))
            morph=Morph(a,b)
            self.assert_cloud(morph.frame(0),a); self.assert_cloud(morph.frame(1),b)
            mid=morph.frame(.5)
            self.assertTrue(np.all(np.isfinite(mid[0])))
            self.assertEqual(len(mid[0]),max(na,nb))
            # Motion eases into and out of the morph with zero endpoint velocity.
            self.assertLess(np.max(np.linalg.norm(morph.frame(.001)[0]-morph.frame(0)[0],axis=1)),.01)

    def test_celebration_stays_inside_camera(self):
        for t in np.linspace(0,4.8,49):
            p,_,_=ronaldo(float(t))
            projected_y=p[:,1]*190*5.8/(5.8-p[:,2])
            self.assertLess(np.max(np.abs(projected_y)),ROWS*CH/2-6)

if __name__=='__main__': unittest.main()
