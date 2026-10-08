"""Pin each generated image to its commit to avoid stale GitHub image caches."""
from pathlib import Path
import re, subprocess
root=Path(__file__).resolve().parents[1]
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
path=root/'README.md'
text=path.read_text()
for name in ['contribution-skyline.svg','contribution-skyline-static.svg']:
    url=f'https://raw.githubusercontent.com/kashifhussa1n/kashifhussa1n/{sha}/{name}'
    text,n=re.subn(r'(src(?:set)?=")[^"\n]*'+re.escape(name)+r'"',lambda m:m[1]+url+'"',text)
    if n!=1: raise ValueError(f'Expected one reference to {name}, found {n}')
path.write_text(text,encoding='utf-8')

