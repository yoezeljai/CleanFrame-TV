"""Keeps only the named wallpapers (and their materials) in a built asset folder.

Usage: python3 scripts/trim_wallpapers.py <assets dir> [--max-width N] <id> [<id> ...]

--max-width also scales the kept full-screen images down (the CSS sizes stay the same), so
each decoded wallpaper and glass layer takes less GPU memory on a low-RAM device.
"""
import json
import re
import sys
from pathlib import Path

args = sys.argv[2:]
max_width = 0
if args[:1] == ['--max-width']:
    max_width, args = int(args[1]), args[2:]
root, keep = Path(sys.argv[1]), set(args)
cat = root / 'wallpapers/catalog.js'
text = cat.read_text()
walls = json.loads(text[text.index('['):text.rindex(']') + 1])
ids = [w['id'] for w in walls]
assert keep <= set(ids), 'Unknown wallpaper in keep list: %s' % sorted(keep - set(ids))
cat.write_text(text[:text.index('[')] + json.dumps([w for w in walls if w['id'] in keep], indent=2) + ';\n')
for folder in ('wallpapers', 'materials'):
    for f in (root / folder).glob('*.jpg'):
        stem = re.split(r'[-.]', f.name)[0]
        if stem in ids and stem not in keep:
            f.unlink()
        elif max_width:
            from PIL import Image
            im = Image.open(f)
            if im.width > max_width:
                im.convert('RGB').resize((max_width, round(im.height * max_width / im.width)), Image.LANCZOS).save(f, quality=86)
