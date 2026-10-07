# Profile artwork

The README uses three custom, committed SVGs and no external stats cards.
The terminal layout and portrait/stats renderers are adapted from
[Avi Vashishta's profile](https://github.com/AVIVASHISHTA29/AVIVASHISHTA29)
and his [tutorial](https://www.avivashishta.com/blog/build-animated-github-profile-readme).
All contribution data and statistics belong to `kashifhussa1n`.

## Portrait

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
values and the portrait grid before the workflow commits anything. Failed
retrieval or verification leaves the last committed assets in place.
The portrait is regenerated only when its source changes, not daily.
