"""Validate the committed animation without requiring image packages in daily CI."""
from pathlib import Path
import hashlib,json,struct

ROOT=Path(__file__).resolve().parents[1]

def validate(root=ROOT):
    path=root/'ascii-cinema.webp'; content=path.read_bytes()
    assert content[:4]==b'RIFF' and content[8:12]==b'WEBP'
    assert int.from_bytes(content[4:8],'little')+8==len(content), 'Truncated WebP'
    manifest=json.loads((root/'assets/animation-manifest.json').read_text())
    durations=[]; size=None; loop=None; cursor=12
    while cursor<len(content):
        tag=content[cursor:cursor+4]; length=int.from_bytes(content[cursor+4:cursor+8],'little')
        data=content[cursor+8:cursor+8+length]
        if tag==b'VP8X': size=(int.from_bytes(data[4:7],'little')+1,int.from_bytes(data[7:10],'little')+1)
        if tag==b'ANIM': loop=int.from_bytes(data[4:6],'little')
        if tag==b'ANMF': durations.append(int.from_bytes(data[12:15],'little'))
        cursor+=8+length+(length%2)
    assert cursor==len(content)
    assert size==(840,880) and loop==0
    assert len(durations)==manifest['frames']==1890, 'Missing frames'
    assert set(durations)=={40}, 'Playback must remain at 25 FPS'
    assert sum(durations)==round(manifest['duration']*1000)
    assert [s['id'] for s in manifest['scenes']]==['brain','steve','skull','earth','ronaldo','cat','asterisk','solar','star','eye','knot']
    assert len(manifest['transitions'])==11
    assert all(t['frames']==50 and t['matched']>100 for t in manifest['transitions'])
    assert path.stat().st_size==manifest['bytes']
    assert path.stat().st_size<30_000_000, 'Animation exceeds download budget'
    assert (root/'assets/cinema-poster.png').read_bytes()[:8]==b'\x89PNG\r\n\x1a\n'
    print(f'Animation verified: {len(durations)} frames, 25 FPS, 11 scenes, 11 glyph morphs, {len(content)/1e6:.2f} MB')
    return hashlib.sha256(content).hexdigest()

if __name__=='__main__': validate()
