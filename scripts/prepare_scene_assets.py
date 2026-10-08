"""Fetch the pinned, openly licensed typeface used for reproducible rendering."""
from pathlib import Path
import hashlib
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
FONT=ROOT/'assets/JetBrainsMono-Regular.ttf'
SHA='e6fd0d7e91550b3ed2b735d4312474362c4716edc4fc0577a0f61ed782d5aed1'
URL='https://raw.githubusercontent.com/JetBrains/JetBrainsMono/19371302b95d218af43299bce79ddbddd0bc364d/fonts/ttf/JetBrainsMono-Regular.ttf'
FONT.parent.mkdir(exist_ok=True)
if not FONT.exists():
    with urllib.request.urlopen(URL,timeout=30) as response: content=response.read()
    if hashlib.sha256(content).hexdigest()!=SHA: raise ValueError('Typeface checksum mismatch')
    FONT.write_bytes(content)
assert hashlib.sha256(FONT.read_bytes()).hexdigest()==SHA
print('Verified pinned JetBrains Mono typeface (OFL-1.1)')
