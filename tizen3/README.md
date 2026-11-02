# Tizen 3.0 build (Samsung 2017 TVs)

`app/` targets recent Samsung TVs. Samsung's 2017 models (for example the
UA50MU6100) run Tizen 3.0, whose web engine is Chromium 47. That engine is
missing several things `app/` relies on, so this build produces a separate
widget source in `dist/tizen3/`:

```
python3 scripts/build-tizen3.py
```

Run it again after any change in `app/`. It needs Python 3.10+ with
`fonttools` and `brotli`.

## What the build changes

| Problem on Chromium 47 | What the build does |
| --- | --- |
| No CSS custom properties (`var(--x)`) | Splits `style.css` into plain chunks and "slots". `compat/cssvars.js` resolves slot values against the live DOM, writes each slot into its own `<style>` in the original rule order, and rewrites a slot only when its text changes. |
| `element.style.setProperty('--x', …)` is ignored | Calls in `main.js` are rewritten to `CFVars.set` / `CFVars.remove`. |
| No flexbox `gap` | The runtime adds the gap as margins between flex items. Element items get inline margins, `::before`/`::after` items get generated rules, and items with `margin: auto` are left alone. |
| No `inset` shorthand | Expanded to `top/right/bottom/left`. |
| No `:focus-visible` | Becomes `:focus`. |
| `font-variant-numeric` unprefixed | Adds `-webkit-font-feature-settings: "tnum"`. |
| No variable fonts, weight ranges, `size-adjust` or metric overrides | Bakes static `.woff2` files for each weight used (Manrope 400–700, Geist 300/400, Newsreader 400 at opsz 36), with size-adjust and metric overrides built into each font. |
| Manifest `required_version="6.5"` | Set to `3.0` in the built `config.xml`. |

Restyling happens on class, `id`, `hidden` and `data-*` selector changes, on
focus changes, on `CFVars` calls, and before layout reads such as
`getBoundingClientRect`, `getComputedStyle` and `offsetWidth`.

## Preview and checks

`python3 scripts/preview.py --public-fonts` serves:

- `/home/`: the original `app/`.
- `/tizen3/`: the built `dist/tizen3/`.

The `/tizen3/` preview in a modern browser exercises the compatibility runtime
itself, because the built stylesheet contains no `var()` or `gap` for the
browser to fall back on.

### Comparison results (Chrome on macOS, 22 Oct 2026)

Both builds were loaded side by side and every element's computed style and
position was compared, including `::before` and `::after`.

- **Identical:** all 19 appearance combinations, and 102 navigation steps
  (home, controls row, All apps, Settings, Appearance, Arrange) across both
  layouts and three backgrounds.
- **Small differences:** Manrope and Geist are within 0.05 px. Newsreader is
  about 2% narrower, because one optical size replaces its per-element sizes.

## Not yet verified on a real TV

- Rendering and speed on the actual Tizen 3.0 engine. A full style refresh
  takes about 1 ms on a Mac; expect it to be many times slower on a 2017 TV.
- App launch IDs. `app/device.js` holds the reference TV's IDs; read this TV's
  installed-app list after connecting with SDB.
- Native Home-button takeover (`scripts/native-home/`) needs .NET on the TV,
  which Tizen 3.0 doesn't have. On this TV, CleanFrame is opened as an app.
