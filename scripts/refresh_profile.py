"""Regenerate both data panels from a single, verified GitHub calendar."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
for script in ['fetch_contributions.py','render_heatmap_svg.py','render_stats_svg.py','validate_art.py']:
    subprocess.run([sys.executable,str(ROOT/'scripts'/script)], cwd=ROOT, check=True)
