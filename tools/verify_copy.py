"""Check that every [data-p] element in site/index.html has textContent exactly
equal to its paragraph in website-copy-verbatim.json (no trim, no normalize)."""
import html.parser
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
paras = {p["paragraph"]: p["text"] for p in
         json.loads((ROOT / "source-extracted" / "website-copy-verbatim.json").read_text(encoding="utf-8"))["paragraphs"]}

extra = {e["key"]: e["text"] for e in
         json.loads((ROOT / "source-extracted" / "website-copy-extra.json").read_text(encoding="utf-8"))["entries"]}

VOID = {"img", "source", "meta", "link", "br", "input", "path", "rect"}


class P(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []      # open elements: [tag, data-p or None, collected text]
        self.found = []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        a = dict(attrs)
        self.stack.append([tag, a.get("data-p") or ("x:" + a["data-x"] if "data-x" in a else None), []])

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        while self.stack:
            t, p, buf = self.stack.pop()
            text = "".join(buf)
            if self.stack:
                self.stack[-1][2].append(text)
            if p is not None:
                self.found.append((p if p.startswith("x:") else int(p), text))
            if t == tag:
                break

    def handle_data(self, data):
        if self.stack:
            self.stack[-1][2].append(data)


parser = P()
parser.feed((ROOT / "site" / "index.html").read_text(encoding="utf-8"))
expected = lambda n: extra[n[2:]] if isinstance(n, str) else paras[n]
errors = [(n, t) for n, t in parser.found if t != expected(n)]
shown = {n for n, _ in parser.found if not isinstance(n, str)}
print(f"checked {len(parser.found)} elements, {len(shown)}/{len(paras)} paragraphs shown")
for n, t in errors:
    print(f"MISMATCH {n}: {t!r} != {expected(n)!r}")
missing = set(paras) - shown
if missing:
    print("MISSING:", sorted(missing))
raise SystemExit(1 if errors or missing else 0)
