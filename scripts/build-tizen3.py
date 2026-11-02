"""Build a Samsung 2017 (Tizen 3.0, Chromium 47) variant of app/ into dist/tizen3/.

style.css is split into plain chunks and runtime "slots" (rules using var(),
defining --properties or setting flex gap); tizen3/cssvars.js resolves the
slots on the TV. Other differences from app/ are listed in tizen3/README.md.
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'app'
OUT = ROOT / 'dist/tizen3'


def matching(text, start):
    """Index just past the brace block that opens at text[start] == '{'."""
    depth, i, quote = 0, start, None
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == '\\':
                i += 1
            elif ch == quote:
                quote = None
        elif ch in '"\'':
            quote = ch
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError('Unbalanced braces in style.css')


def split_top(text, sep):
    parts, depth, quote, cur = [], 0, None, ''
    for ch in text:
        if quote:
            if ch == quote:
                quote = None
        elif ch in '"\'':
            quote = ch
        elif ch in '([':
            depth += 1
        elif ch in ')]':
            depth -= 1
        elif ch == sep and depth == 0:
            parts.append(cur)
            cur = ''
            continue
        cur += ch
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def parse(text):
    nodes, i = [], 0
    while True:
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text):
            return nodes
        brace = text.find('{', i)
        semi = text.find(';', i)
        if text[i] == '@' and semi >= 0 and (brace < 0 or semi < brace):
            nodes.append(('raw', text[i:semi + 1]))
            i = semi + 1
            continue
        end = matching(text, brace)
        prelude, body = text[i:brace].strip(), text[brace + 1:end - 1]
        if prelude.startswith('@media'):
            nodes.append(('media', prelude[6:].strip(), parse(body)))
        elif prelude.startswith('@'):
            if 'var(' in body:
                raise ValueError('var() inside ' + prelude + ' is not supported')
            nodes.append(('raw', text[i:end]))
        else:
            nodes.append(('rule', prelude, body))
        i = end


def declarations(body):
    out = []
    for d in split_top(body, ';'):
        prop, _, value = d.partition(':')
        prop, value = prop.strip(), value.strip()
        imp = value.endswith('!important')
        if imp:
            value = value[:-len('!important')].strip()
        out.append([prop, value, imp])
    return out


def expand(decls):
    """Static rewrites for properties Chromium 47 lacks or names differently."""
    out = []
    for prop, value, imp in decls:
        if prop == 'inset':
            v = split_top(value, ' ')
            v = (v * 4)[:4] if len(v) == 1 else v + v[:4 - len(v)] if len(v) == 2 else v + [v[1]] if len(v) == 3 else v
            out += [[side, val, imp] for side, val in zip(['top', 'right', 'bottom', 'left'], v)]
            continue
        out.append([prop, value, imp])
        if prop == 'font-variant-numeric' and 'tabular-nums' in value:
            out.append(['-webkit-font-feature-settings', '"tnum"', imp])
        elif prop == 'font-feature-settings':
            out.append(['-webkit-font-feature-settings', value, imp])
    return out


PSEUDO_ELEMENT = re.compile(r'(::?(?:before|after|placeholder|selection))$')


def specificity(sel):
    s = re.sub(r'"[^"]*"|\'[^\']*\'', '', sel)
    s = re.sub(r':not\(([^)]*)\)', r' \1', s)
    ids = len(re.findall(r'#[\w-]+', s))
    s = re.sub(r'#[\w-]+', '', s)
    attrs = len(re.findall(r'\[[^\]]*\]', s))
    s = re.sub(r'\[[^\]]*\]', '', s)
    pe = len(re.findall(r'::[\w-]+|:(?:before|after)\b', s))
    s = re.sub(r'::[\w-]+|:(?:before|after)\b', '', s)
    classes = len(re.findall(r'\.[\w-]+', s)) + len(re.findall(r':[\w-]+', s)) + attrs
    s = re.sub(r'\.[\w-]+|:[\w-]+', '', s)
    types = len(re.findall(r'(?:^|[\s>+~])([a-zA-Z][\w-]*)', s)) + pe
    return [ids, classes, types]


def selector_info(sel):
    m = PSEUDO_ELEMENT.search(sel)
    base, pe = (sel[:m.start()], m.group(1)) if m else (sel, '')
    return {'s': base or '*', 'pe': pe, 'full': sel, 'spec': specificity(sel)}


def auto_sides(decls):
    """Margin sides set to auto; gap emulation must leave those margins alone."""
    sides = {}
    for prop, value, _ in decls:
        if prop == 'margin':
            v = split_top(value, ' ')
            v = (v * 4)[:4] if len(v) == 1 else v + v[:4 - len(v)] if len(v) == 2 else v + [v[1]] if len(v) == 3 else v
            for side, val in zip(['marginTop', 'marginRight', 'marginBottom', 'marginLeft'], v):
                sides[side] = val == 'auto'
        elif prop.startswith('margin-'):
            side = 'margin' + prop[7:].capitalize()
            sides[side] = value == 'auto'
    return [side for side, auto in sides.items() if auto]


def fix_selector(sel):
    return sel.replace(':focus-visible', ':focus')


def serialise(sel, decls):
    return sel + '{' + ';'.join(p + ':' + v + ('!important' if i else '') for p, v, i in decls) + '}'


def build_css(text):
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    chunks, slots, buf, attrs, autos = [], [], [], {'class', 'id', 'hidden'}, []

    def flush():
        if buf:
            chunks.append(''.join(buf))
            buf.clear()

    def rule(prelude, body, media):
        sels = split_top(fix_selector(prelude), ',')
        for s in sels:
            attrs.update(re.findall(r'\[([\w-]+)', s))
        decls = expand(declarations(body))
        static = [d for d in decls if not (d[0].startswith('--') or 'var(' in d[1] or d[0] == 'gap')]
        if static:
            css = serialise(','.join(sels), static)
            buf.append('@media ' + media + '{' + css + '}' if media else css)
        auto = auto_sides(decls)
        if auto:
            autos.append({'sels': [selector_info(s)['s'] for s in sels], 'media': media, 'sides': auto})
        defs = [d for d in decls if d[0].startswith('--')]
        uses = [d for d in decls if not d[0].startswith('--') and 'var(' in d[1] and d[0] != 'gap']
        gap = [d for d in decls if d[0] == 'gap']
        if not (defs or uses or gap):
            return
        slot = {'sels': [selector_info(s) for s in sels], 'media': media}
        if defs:
            slot['defs'] = defs
        if gap:
            slot['gap'] = [gap[-1][1], gap[-1][2]]
        if uses:
            slot['vars'] = uses
            flush()
            chunks.append(len(slots))
        slots.append(slot)

    for node in parse(text):
        if node[0] == 'raw':
            buf.append(node[1])
        elif node[0] == 'rule':
            rule(node[1], node[2], None)
        else:
            for child in node[2]:
                if child[0] != 'rule':
                    raise ValueError('Nested at-rule inside @media is not supported')
                rule(child[1], child[2], node[1])
    flush()
    return {'chunks': chunks, 'slots': slots, 'attrs': sorted(attrs), 'autoMargins': autos}


# Chromium 47 predates variable fonts (it would draw each file's default instance,
# Manrope's being ExtraLight 200) and weight ranges in @font-face. Bake one static
# file per weight the UI asks for. size-adjust and the *-override descriptors are
# also unsupported there, so Geist and Newsreader sit slightly differently.
STATIC_FONTS = [
    ('Manrope', 'manrope.woff2', 'fonts.css', {}, [400, 500, 600, 700]),
    ('Study Geist', 'fonts/geist/Geist-Variable.ttf', 'typefaces.css', {}, [300, 400]),
    ('Study Newsreader', 'fonts/newsreader/Newsreader-Variable.ttf', 'typefaces.css', {'opsz': 36}, [400]),
]


def face_metrics(family):
    """size-adjust and *-override descriptors from app/assets/typefaces.css."""
    for face in re.findall(r'@font-face\{([^}]*)\}', (APP / 'assets/typefaces.css').read_text()):
        if "'" + family + "'" in face:
            return {k: float(v) / 100 for k, v in re.findall(r'(size-adjust|ascent-override|descent-override|line-gap-override):([\d.]+)%', face)}
    return {}


def bake_metrics(font, family):
    """Applies the face's size-adjust and metric overrides inside the font file."""
    m = face_metrics(family)
    if not m:
        return
    head, hhea, os2 = font['head'], font['hhea'], font['OS/2']
    upm = round(head.unitsPerEm / m.get('size-adjust', 1))
    head.unitsPerEm = upm
    asc, desc, gap = round(m['ascent-override'] * upm), round(m['descent-override'] * upm), round(m.get('line-gap-override', 0) * upm)
    hhea.ascent, hhea.descent, hhea.lineGap = asc, -desc, gap
    os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = asc, -desc, gap
    os2.usWinAscent, os2.usWinDescent = asc, desc


def build_fonts():
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    css = {}
    for family, src, sheet, axes, weights in STATIC_FONTS:
        for weight in weights:
            font = instantiateVariableFont(TTFont(APP / 'assets' / src), dict(axes, wght=weight))
            bake_metrics(font, family)
            font.flavor = 'woff2'
            name = 'static/%s-%d.woff2' % (family.lower().replace(' ', '-'), weight)
            (OUT / 'assets/static').mkdir(exist_ok=True)
            font.save(OUT / 'assets' / name)
            css.setdefault(sheet, []).append("@font-face{font-family:'%s';font-style:normal;font-weight:%d;src:url('%s') format('woff2')}" % (family, weight, name))
    for sheet, faces in css.items():
        (OUT / 'assets' / sheet).write_text('/* Static instances for Tizen 3.0; see scripts/build-tizen3.py. */\n' + '\n'.join(faces) + '\n')
    for _, src, _, _, _ in STATIC_FONTS:
        (OUT / 'assets' / src).unlink()  # Licences beside them stay.


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(APP, OUT, ignore=shutil.ignore_patterns('style.css', '.DS_Store'))
    (OUT / 'compat').mkdir()
    data = build_css((APP / 'style.css').read_text())
    (OUT / 'compat/css-data.js').write_text('window.CF_CSS=' + json.dumps(data, separators=(',', ':')) + ';\n')
    shutil.copy(ROOT / 'tizen3/cssvars.js', OUT / 'compat/cssvars.js')
    build_fonts()

    html = (OUT / 'index.html').read_text()
    link = '<link rel="stylesheet" href="style.css">'
    assert link in html, 'index.html no longer links style.css'
    html = html.replace(link, '<script src="compat/css-data.js"></script>\n<script src="compat/cssvars.js"></script>')
    (OUT / 'index.html').write_text(html)

    js = (OUT / 'main.js').read_text()
    js, n_set = re.subn(r'([\w.]+)\.style\.setProperty\(', r'CFVars.set(\1, ', js)
    js, n_rm = re.subn(r'([\w.]+)\.style\.removeProperty\(', r'CFVars.remove(\1, ', js)
    (OUT / 'main.js').write_text(js)

    config = (OUT / 'config.xml').read_text()
    config, n = re.subn(r'required_version="[^"]*"', 'required_version="3.0"', config)
    assert n == 1, 'config.xml has no required_version'
    (OUT / 'config.xml').write_text(config)

    n_vars = sum(1 for s in data['slots'] if 'vars' in s)
    print('dist/tizen3: %d CSS chunks, %d slots (%d var, %d def, %d gap), %d setProperty / %d removeProperty calls rewired'
          % (sum(1 for c in data['chunks'] if isinstance(c, str)), len(data['slots']), n_vars,
             sum(1 for s in data['slots'] if 'defs' in s), sum(1 for s in data['slots'] if 'gap' in s), n_set, n_rm))


if __name__ == '__main__':
    main()
