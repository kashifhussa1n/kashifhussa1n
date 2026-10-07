# Profile artwork

The README uses three custom, committed SVGs and no external stats cards.
The terminal layout and portrait/stats renderers are adapted from
[Avi Vashishta's profile](https://github.com/AVIVASHISHTA29/AVIVASHISHTA29)
and his [tutorial](https://www.avivashishta.com/blog/build-animated-github-profile-readme).
All contribution data and statistics belong to `kashifhussa1n`.

## Rotating ASCII gallery

`ascii-motion.svg` contains sixteen depth-shaded sculptures: trefoil knot,
Mobius strip, gyroscope, double helix, icosahedron, hex crystal, spacecraft,
gear, wave field, nested cubes, orbital atom, torus, octahedron, cube,
sphere and pyramid. Geometry is projected in 3D, depth-shaded with ASCII
characters, and rendered into sixteen views per object. Each six-second cycle assembles the character rows
for 0.6 seconds, rotates for 4.8 seconds, then scatters the rows for 0.6 seconds.
The full 96-second sequence repeats indefinitely.

The shapes come entirely from mathematical geometry in the renderer, not
from GitHub data or an external animation feed. Curves are thickened into
small tubes with surface normals, lit from one direction, rotated around
three axes, and perspective-projected into a depth buffer. Character density
represents the lighting. CSS transforms animate character rows between views;
this animation runs locally in the browser while viewing the SVG.

The panel is 840 x 880 pixels, matching the contribution stats. Its CSS
animation runs inside a self-contained SVG image with no JavaScript,
external fonts, services or runtime dependencies. Reduced-motion viewers
see a static first sculpture. Generate it using the Python standard library:

```sh
python scripts/render_objects_svg.py
```

## Archived portrait

`source-photo.jpg` is Kashif's supplied Memoji. Its white background allows
deterministic isolation without a downloaded background-removal model.
`prep_photo.py` crops the subject, smooths texture, stretches luminance and
enhances dark ridges around the glasses, eyes, nose and lips. The grayscale
`source-prepped.png` is sampled into a 180 × 96 character grid by
`make_ascii_svg.py`, preserving the character aspect ratio. Each row prints
with an SVG clip wipe and cursor, then holds. The result is 840 × 880 pixels.

Install `scripts/requirements-portrait.txt` only when regenerating the portrait:

```sh
python scripts/prep_photo.py
python scripts/make_ascii_svg.py
```

## Real contribution data

`fetch_contributions.py` reads GitHub's own public calendar HTML and parses
every day's date, count tooltip and GitHub intensity level. It rejects missing
tooltips, incomplete calendars and a sum that differs from GitHub's headline.
It never falls back to another account or a guessed count. The snapshot is
saved in `data/contributions.json` with the account, source URL, retrieval time
and date range. Both data panels use that snapshot.

The slim heatmap positions dates by Sunday-based weeks and reveals cells
diagonally once. The 840 × 880 stats panel uses six count-up tiles and monthly
bars. Zero months have zero-height bars. Stats describe the publicly displayed
rolling calendar, including any private contribution counts GitHub chooses to
show. They are not repository commit counts. Current streak permits an
unfinished, empty last day, as in the reference.

## Daily refresh

The workflow runs daily at 02:17 UTC (07:17 Asia/Karachi), after renderer
changes on `main`, or on manual dispatch. The daily pipeline needs only the
Python standard library, no token or additional secret:

```sh
python scripts/refresh_profile.py
```

`validate_art.py` checks dimensions, identity, all calendar cells, final stat
values and all 256 shaded gallery frames and transition phases before the workflow commits anything. Failed
retrieval or verification leaves the last committed assets in place.
The object gallery is regenerated when its renderer changes, not daily.
The original portrait assets remain available for a future switch back.
