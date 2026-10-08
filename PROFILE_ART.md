# Profile artwork

The README combines a real GitHub calendar, a custom 3D ASCII animation, and six contribution statistics. The compact terminal layout was originally inspired by [Avi Vashishta](https://github.com/AVIVASHISHTA29/AVIVASHISHTA29).

## ASCII cinema

The animation renders 1,890 frames at 25 FPS over a 75.6-second loop. Its eleven scenes are a folded brain, walking Minecraft Steve, carved skull, rotating Earth, a stylized CR7 Siuuu celebration, glasses cat, extruded asterisk, eight-planet solar system, sculpted star, floating eye, and trefoil knot. Planet sizes and orbit speeds are artistic, not to scale.

These are independently modeled surfaces and articulated figures. A perspective camera, surface normals, directional lighting, and an opaque depth buffer determine each visible character. Steve and the celebration figure have animated limbs. Earth uses actual coastline polygons. The CR7 scene is a stylized character interpretation, not a facial scan or captured performance.

Each transition contains 50 frames. Minimum-distance matching assigns existing characters to positions in the next subject. They follow eased curved paths. Extra characters appear from nearby positions, while excess characters fade away as they approach the new form. The final knot flows into the opening particle field, which assembles the brain, avoiding an abrupt reset.

The animation preserves the stats panel's aspect ratio and displays at 420 x 440. A static glasses-cat poster is available for reduced-motion viewing.

### Rebuild

```sh
pip install -r scripts/requirements-scenes.txt
python scripts/prepare_scene_assets.py
python scripts/test_scenes.py
python scripts/render_scenes.py --stills
python scripts/render_scenes.py
python scripts/check_animation.py
```

The separate Build ASCII cinema workflow regenerates and commits the animation on manual dispatch. It also builds the ascii-cinema-preview branch when its renderer changes. The daily statistics refresh does not rerender the animation. Dependencies and the typeface revision are pinned; the downloaded font is checked by SHA-256. Mesh caches are local and excluded from Git.

### Sources

- [Obinary's reference video](https://www.youtube.com/watch?v=-G-cvUP8JJE): inspiration for the dimensional extruded asterisk and shaded glyph treatment.
- [Natural Earth land polygons](https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_land.geojson): public-domain geography, stored in assets/earth-land.geojson.
- [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono): OFL-1.1, with its license in assets/JetBrainsMono-OFL.txt.
- The original Memoji portrait and previous SVG sculptures remain archived in the repository.

## Contribution data and visibility

The fetcher reads https://github.com/users/kashifhussa1n/contributions without authentication. It parses every date, count, and intensity level, checks date continuity, and compares the sum to GitHub's headline. Both the calendar and stats come from this verified snapshot in data/contributions.json.

GitHub can show a larger total to the account owner than to signed-out visitors. Enabling Contribution settings > Private contributions makes anonymized private counts available to this renderer; repository names and details stay private. The renderer never guesses the difference or hardcodes a screenshot total. Visibility changes are picked up on the next successful refresh.

The scheduled workflow runs at 02:17 UTC (07:17 Pakistan), on renderer changes to main, or on manual dispatch. It validates every calendar cell and all six stats before committing. Failed retrieval preserves the previous assets. README data-image URLs are pinned to the generated commit so cached images cannot obscure an update.
