"""Render site/index.html from src/index.template.html.

Every visible string comes from source-extracted/website-copy-verbatim.json,
inserted exactly (only HTML-escaped). Placeholders:

  {{p:N}}      paragraph N as escaped text
  {{a:N}}      paragraph N escaped for an attribute value
  {{head:N}}   paragraph N split at the first " | " into number + title spans
               (textContent stays identical to the source string)
  {{pic:FILE;sizes=...;alt=N;eager}}
               <picture> with AVIF/WebP srcset from assets/image-manifest.json
  {{zoom:FILE}} data attributes for the full-size lightbox

Run after editing the JSON or the template:  python tools/build_site.py
"""
import html
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COPY = ROOT / "source-extracted" / "website-copy-verbatim.json"
EXTRA = ROOT / "source-extracted" / "website-copy-extra.json"
TEMPLATE = ROOT / "src" / "index.template.html"
MANIFEST = ROOT / "site" / "assets" / "image-manifest.json"
OUT = ROOT / "site" / "index.html"

paras = {p["paragraph"]: p["text"] for p in json.loads(COPY.read_text(encoding="utf-8"))["paragraphs"]}
extra = {e["key"]: e for e in json.loads(EXTRA.read_text(encoding="utf-8"))["entries"]}
images = {m["source"]: m for m in json.loads(MANIFEST.read_text(encoding="utf-8")) if "widths" in m}
used_images = set()


def esc(s):
    return html.escape(s, quote=False)


def attr(s):
    return html.escape(s, quote=True)


def head(n):
    text = paras[n]
    num, sep, rest = text.partition(" | ")
    if not sep:
        return esc(text)
    return f'<span class="sec-num">{esc(num)}</span><span class="sec-title">{esc(sep + rest)}</span>'


def pic(spec):
    parts = spec.split(";")
    name = parts[0]
    opts = dict(p.split("=", 1) if "=" in p else (p, True) for p in parts[1:])
    m = images[name]
    used_images.add(name)
    stem = Path(name).stem
    sizes = opts.get("sizes", "100vw")
    srcset = lambda ext: ", ".join(f"assets/img/{stem}-{w}.{ext} {w}w" for w in m["widths"])
    alt = attr(paras[int(opts["alt"])]) if "alt" in opts else ""
    eager = "eager" in opts
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    fallback = f"assets/img/{stem}-{m['widths'][min(1, len(m['widths']) - 1)]}.webp"
    return (
        f'<picture>'
        f'<source type="image/avif" srcset="{srcset("avif")}" sizes="{sizes}">'
        f'<source type="image/webp" srcset="{srcset("webp")}" sizes="{sizes}">'
        f'<img src="{fallback}" alt="{alt}" width="{m["width"]}" height="{m["height"]}" '
        f'{load} decoding="async" data-src-name="{name}">'
        f'</picture>'
    )


def zoom(name):
    m = images[name]
    return f'data-full="assets/{m["original"]}" data-w="{m["width"]}" data-h="{m["height"]}"'


def drip(spec):
    """Melting-ice-cream edge: an icing band with drips of varying length."""
    color, seed = spec.split(";")
    rng = random.Random(int(seed))
    parts = [f'<svg class="drip-edge" viewBox="0 0 1440 140" preserveAspectRatio="xMidYMin slice" aria-hidden="true" focusable="false">',
             f'<g fill="{color}">',
             '<rect x="0" y="0" width="1440" height="26"/>']
    # scalloped lower edge of the band
    for x in range(0, 1441, 48):
        parts.append(f'<circle cx="{x}" cy="24" r="{rng.randint(14, 20)}"/>')
    x = rng.randint(10, 40)
    while x < 1420:
        w = rng.randint(16, 30)
        length = rng.randint(30, 96)
        r = w / 2
        delay = rng.uniform(0, 4)
        dur = rng.uniform(4, 7)
        parts.append(
            f'<path class="drip-line" style="animation-delay:-{delay:.1f}s;animation-duration:{dur:.1f}s" '
            f'd="M{x} 20 V{20 + length} a{r:.1f} {r:.1f} 0 0 0 {w} 0 V20 Z"/>')
        x += w + rng.randint(30, 110)
    parts.append('</g></svg>')
    return "".join(parts)


def strip(_):
    """Endless photo strip: every image twice, decorative (alt empty)."""
    items = []
    for name in list(images) * 2:
        m = images[name]
        stem = Path(name).stem
        w = m["widths"][0]
        h = round(m["height"] * w / m["width"])
        items.append(
            f'<li><picture><source type="image/avif" srcset="assets/img/{stem}-{w}.avif">'
            f'<img src="assets/img/{stem}-{w}.webp" alt="" width="{w}" height="{h}" loading="lazy" decoding="async"></picture></li>')
    return "".join(items)


def render(tpl):
    def sub(match):
        kind, arg = match.group(1), match.group(2)
        if kind == "p":
            return esc(paras[int(arg)])
        if kind == "a":
            return attr(paras[int(arg)])
        if kind == "head":
            return head(int(arg))
        if kind == "pic":
            return pic(arg)
        if kind == "zoom":
            return zoom(arg)
        if kind == "x":
            return esc(extra[arg]["text"])
        if kind == "xhref":
            return attr(extra[arg]["href"])
        if kind == "drip":
            return drip(arg)
        if kind == "strip":
            return strip(arg)
        raise ValueError(kind)

    return re.sub(r"\{\{(p|a|head|pic|zoom|drip|strip|x|xhref):([^}]+)\}\}", sub, tpl)


def main():
    out = render(TEMPLATE.read_text(encoding="utf-8"))
    missing = set(images) - used_images
    if missing:
        raise SystemExit(f"images not used: {sorted(missing)}")
    shown = {int(n) for n in re.findall(r'data-p="(\d+)"', out)}
    missing_p = set(paras) - shown
    if missing_p:
        raise SystemExit(f"paragraphs not shown: {sorted(missing_p)}")
    OUT.write_text(out, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(shown)} paragraphs, {len(used_images)} images")


if __name__ == "__main__":
    main()
