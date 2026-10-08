"""Pin data images to their generated commit so GitHub cannot reuse stale images."""
from pathlib import Path
import re,subprocess

root=Path(__file__).resolve().parents[1]
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
readme=root/'README.md'
text=readme.read_text(encoding='utf-8')
for name in ['contrib-heatmap.svg','stats.svg']:
    url=f'https://raw.githubusercontent.com/kashifhussa1n/kashifhussa1n/{sha}/{name}'
    text,count=re.subn(r'src="[^"\n]*'+re.escape(name)+r'(?:\?[^"\n]*)?"',f'src="{url}"',text)
    if count!=1: raise ValueError(f'Expected one README image for {name}, got {count}')
readme.write_text(text,encoding='utf-8')
print('Pinned both contribution images to their actual commit')
