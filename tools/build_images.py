"""Build responsive AVIF/WebP variants from the original Word images.

Originals in source-extracted/ are copied unchanged to site/assets/original/.
Variants go to site/assets/img/<stem>-<width>.<ext> and are listed in
site/assets/image-manifest.json, which maps every variant back to its source.
"""
import json
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-extracted"
OUT = ROOT / "site" / "assets"
ORIG = OUT / "original"
IMG = OUT / "img"

# Posters keep high quality so prices and QR codes stay readable.
POSTERS = {"image5.png", "image8.png"}
WIDTHS = [480, 800, 1200, 1600]


def main():
    ORIG.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    assets = json.loads((SRC / "asset-manifest.json").read_text(encoding="utf-8"))
    manifest = []
    for item in assets:
        name = item["source"]
        src = SRC / name
        shutil.copy2(src, ORIG / name)
        with Image.open(src) as im:
            im = im.convert("RGB")
            w, h = im.size
            stem = Path(name).stem
            q = 90 if name in POSTERS else 78
            widths = sorted({min(x, w) for x in WIDTHS})
            variants = []
            for vw in widths:
                vh = round(h * vw / w)
                resized = im if vw == w else im.resize((vw, vh), Image.LANCZOS)
                for ext, kw in (("avif", {"quality": q - 18}), ("webp", {"quality": q, "method": 6})):
                    out = IMG / f"{stem}-{vw}.{ext}"
                    if not out.exists():
                        resized.save(out, **kw)
                    variants.append(f"img/{out.name}")
            manifest.append({
                **item,
                "original": f"original/{name}",
                "width": w,
                "height": h,
                "widths": widths,
                "variants": variants,
            })
            print(name, w, h, widths)

    with Image.open(ROOT / "images.png") as logo:
        logo.save(OUT / "logo.png", optimize=True)
        logo.convert("RGB").save(OUT / "logo.webp", quality=90)
        logo.resize((64, 64), Image.LANCZOS).save(OUT / "favicon-64.png", optimize=True)
        logo.resize((180, 180), Image.LANCZOS).save(OUT / "apple-touch-icon.png", optimize=True)
        manifest.append({"source": "images.png", "section": "Header / Footer", "description": "โลโก้",
                         "original": "logo.png", "width": logo.width, "height": logo.height})

    (OUT / "image-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("images:", len(manifest) - 1, "+ logo")


if __name__ == "__main__":
    main()
