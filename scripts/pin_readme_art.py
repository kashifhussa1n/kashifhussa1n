"""Keep generated profile imagery fresh through immutable commit URLs."""
from pathlib import Path
import re, subprocess
root=Path(__file__).resolve().parents[1]
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
path=root/'README.md';text=path.read_text()
for name in ['profile-overview.svg','project-code.svg','project-motion.svg']:
    url=f'https://raw.githubusercontent.com/kashifhussa1n/kashifhussa1n/{sha}/assets/{name}'
    text,n=re.subn(r'src="[^"\n]*'+re.escape(name)+r'"',f'src="{url}"',text)
    if n!=1:raise ValueError(f'Expected one image for {name}; found {n}')
path.write_text(text,encoding='utf-8')

