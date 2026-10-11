# Sunset Gelato — single-page website

Open `index.html` through any static server, for example:

```bash
python -m http.server 8765 --directory site
```

## Editing text
All visible text comes from `source-extracted/website-copy-verbatim.json`. Never edit `site/index.html` directly.

1. Edit the paragraph text in the JSON (or the layout in `src/index.template.html`).
2. Run `python tools/build_site.py` to rebuild `site/index.html`.
3. Run `python tools/verify_copy.py` to confirm every piece of text matches the JSON exactly.

## Editing images or prices
Prices live inside the posters `image5.png` (Starter set) and `image8.png` (Pro set).
1. Replace the file in `source-extracted/` using the same name.
2. Delete the old variants in `site/assets/img/<name>-*`.
3. Run `python tools/build_images.py`, then `python tools/build_site.py`.

`site/assets/image-manifest.json` maps every resized file back to its original.

## Files
- `index.html` — built page (from the template)
- `styles.css` — theme, layout and animations
- `main.js` — reveal, menu, image viewer, card tilt, falling ice cream, drips and sprinkle burst
- `assets/original/` — original images from Word, unchanged
- `assets/img/` — AVIF/WebP at several sizes
