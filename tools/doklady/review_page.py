#!/usr/bin/env python3
"""Vygeneruje lokální HTML stránku pro ruční kontrolu přepisů: fotka + očíslovaná nejistá místa.

Čte `prepisy/*.md` (sekce „K ručnímu přečtení“), fotky z `jpg/`. Odpovědi uživatel posílá do session
ve tvaru `<fotka>-<číslo>: <čtení>` (např. `4147-2: Šárová`).

Použití: review_page.py <složka dávky, např. doklady/2026-10-16-fotky>  → <složka>/kontrola.html
"""
import html
import re
import sys
from pathlib import Path

TITLE_RE = re.compile(r"^# (.+)$", re.M)
FIELD_RE = re.compile(r"^(typ|forma|čitelnost|souvislost):\s*(.+)$", re.M)


def section(text: str, name: str) -> str:
    m = re.search(rf"^## {re.escape(name)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m[1].strip() if m else ""


def main(batch: str) -> int:
    root = Path(batch)
    cards = []
    total = 0
    for md in sorted((root / "prepisy").glob("*.md")):
        text = md.read_text(encoding="utf-8")
        stem = md.stem
        short = stem.replace("IMG_", "")
        fields = dict(FIELD_RE.findall(text))
        title = TITLE_RE.search(text.split("---", 2)[-1])
        items = [ln[2:].strip() for ln in section(text, "K ručnímu přečtení").splitlines() if ln.startswith("- ")]
        items = [i for i in items if i and not i.lower().startswith(("žádn", "nic"))]
        total += len(items)
        lis = "".join(f'<li><b>{short}-{n}</b> {html.escape(i)}</li>' for n, i in enumerate(items, 1))
        meta = " · ".join(html.escape(fields[k]) for k in ("typ", "forma", "čitelnost") if k in fields)
        rel = html.escape(fields.get("souvislost", ""))
        cards.append(f"""
<section id="{stem}" class="{'' if items else 'ok'}">
  <a href="jpg/{stem}.jpg" target="_blank"><img src="jpg/{stem}.jpg" loading="lazy" alt="{stem}"></a>
  <div>
    <h2>{stem} <small>{html.escape(title[1]) if title else ''}</small></h2>
    <p class="meta">{meta}</p>{f'<p class="meta">souvislost: {rel}</p>' if rel and rel != 'null' else ''}
    {f'<ol>{lis}</ol>' if items else '<p class="meta">nic k přečtení</p>'}
    <p class="meta"><a href="prepisy/{stem}.md">přepis (.md)</a></p>
  </div>
</section>""")
    page = f"""<!doctype html><html lang="cs"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Kontrola přepisů</title>
<style>
:root{{--bg:#fbfaf7;--fg:#222;--muted:#6b6b6b;--card:#fff;--line:#e4e0d8;--acc:#7a4b1f}}
@media (prefers-color-scheme:dark){{:root{{--bg:#1b1a18;--fg:#eee;--muted:#a3a09a;--card:#252421;--line:#3a3833;--acc:#e0a96d}}}}
body{{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}}
h1{{font-size:20px}} h2{{font-size:16px;margin:0 0 4px}} h2 small{{color:var(--muted);font-weight:400}}
section{{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px;background:var(--card);
 border:1px solid var(--line);border-radius:8px;padding:12px;margin:0 0 14px}}
section.ok{{opacity:.6}} img{{width:100%;border-radius:4px}}
.meta{{color:var(--muted);font-size:13px;margin:2px 0}} li{{margin:4px 0}} li b{{color:var(--acc)}}
@media (max-width:760px){{section{{grid-template-columns:1fr}}}}
</style></head><body>
<h1>Kontrola přepisů — {html.escape(root.name)} ({total} míst k přečtení)</h1>
<p class="meta">Odpovídej do session ve tvaru <code>4147-2: čtení</code>. Kliknutím na fotku ji otevřeš v plné velikosti.</p>
{''.join(cards)}
</body></html>"""
    out = root / "kontrola.html"
    out.write_text(page, encoding="utf-8")
    print(f"{out} — {len(cards)} fotek, {total} míst k přečtení")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
