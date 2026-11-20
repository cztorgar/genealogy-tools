#!/usr/bin/env python3
"""Pomocník skillu precti-zapis: snímek z odkazu DigiArchivu v plném rozlišení a výřezy bez zmenšení.

Spouštět přes projekt czech-archives (kvůli modulům a Pillow):
  uv run --project mcp/czech-archives python skills/precti-zapis/zapis.py fetch <url> --dest <dir> --preview <jpg>
  uv run --project mcp/czech-archives python skills/precti-zapis/zapis.py crop <snímek> x0 y0 x1 y1 <výstup>
  uv run --project mcp/czech-archives python skills/precti-zapis/zapis.py read <snímek> x0 y0 x1 y1 <výstup> [--scale 2] [--contrast]

`fetch` a `crop` ukládají do stromu (plné rozlišení). `read` dělá jen pracovní kopii ke čtení (zvětšení,
kontrast) — ta patří do scratchpadu, ne do `sources/`.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# digi.ceskearchivy.cz/<id>/<snímek>[/<x>/<y>/<zoom>/<rotace>] — x, y = střed výhledu v pixelech
# plného snímku (ověřeno: bod leží v řádku, na který se uživatel díval)
URL_RE = re.compile(r"digi\.ceskearchivy\.cz/(\d+)/(\d+)(?:/(\d+)/(\d+)(?:/(\d+))?)?")


def parse_url(url: str) -> dict:
    m = URL_RE.search(url)
    if not m:
        sys.exit(f"Neznámý tvar odkazu: {url} (podporuje se digi.ceskearchivy.cz/<id>/<snímek>/…)")
    rid, img, x, y, zoom = m.groups()
    return {"register_id": rid, "image": int(img),
            "view_x": int(x) if x else None, "view_y": int(y) if y else None,
            "zoom": int(zoom) if zoom else None}


def _fallback_fetch(mod, rid: str, img: int, dest: Path) -> Path:
    """Archiválie, které nejsou matrikou (sčítání, fascikly): register_info je nepřečte,
    snímek se ale skládá stejně. Sidecar doplní agent ručně."""
    base, ref = mod._page_token(rid, img)
    out = dest / f"{rid}_{img:04d}.jpg"
    mod._compose(base, ref).save(out, "JPEG", quality=92)
    return out


def cmd_fetch(a) -> None:
    from czech_archives import modules
    from PIL import Image, ImageDraw

    info = parse_url(a.url)
    dest = Path(a.dest).expanduser()
    dest.mkdir(parents=True, exist_ok=True)
    mod = modules.get("digi_trebon")
    fallback = False
    try:
        path = mod.fetch_page(info["register_id"], info["image"], dest, sidecar=True, entry=a.entry)
    except (ValueError, RuntimeError, KeyError, AttributeError) as e:
        print(f"fetch_page selhal ({e}); skládám snímek přímo, sidecar je třeba napsat ručně", file=sys.stderr)
        path = _fallback_fetch(mod, info["register_id"], info["image"], dest)
        fallback = True
    im = Image.open(path)
    w, h = im.size
    out = {**info, "path": str(path), "width": w, "height": h,
           "sidecar": str(path.with_suffix(".yml")) if path.with_suffix(".yml").exists() else None,
           "sidecar_rucne": fallback}
    if a.preview:
        # náhled jen k orientaci: mřížka v souřadnicích PLNÉHO snímku + křížek ve středu výhledu
        pw = a.preview_width
        s = pw / w
        pv = im.convert("RGB").resize((pw, int(h * s)))
        d = ImageDraw.Draw(pv)
        for gx in range(0, w, a.grid):
            d.line([(gx * s, 0), (gx * s, pv.height)], fill=(255, 0, 0), width=1)
            d.text((gx * s + 2, 2), str(gx), fill=(255, 0, 0))
        for gy in range(0, h, a.grid):
            d.line([(0, gy * s), (pw, gy * s)], fill=(0, 0, 255), width=1)
            d.text((2, gy * s + 2), str(gy), fill=(0, 0, 255))
        if info["view_x"] is not None:
            cx, cy = info["view_x"] * s, info["view_y"] * s
            d.line([(cx - 25, cy), (cx + 25, cy)], fill=(0, 160, 0), width=4)
            d.line([(cx, cy - 25), (cx, cy + 25)], fill=(0, 160, 0), width=4)
        Path(a.preview).parent.mkdir(parents=True, exist_ok=True)
        pv.save(a.preview, quality=85)
        out["preview"] = a.preview
    print(json.dumps(out, ensure_ascii=False, indent=1))


def _box(a, im):
    w, h = im.size
    x0, y0, x1, y1 = max(0, a.x0), max(0, a.y0), min(w, a.x1), min(h, a.y1)
    if x1 <= x0 or y1 <= y0:
        sys.exit(f"prázdný výřez ({x0},{y0})–({x1},{y1}) na snímku {w}×{h}")
    return x0, y0, x1, y1


def cmd_crop(a) -> None:
    from PIL import Image
    im = Image.open(a.src)
    c = im.crop(_box(a, im))          # žádné zmenšení — ukládá se plné rozlišení
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    c.save(a.out, quality=95)
    print(f"{a.out} {c.size[0]}×{c.size[1]}")


def cmd_read(a) -> None:
    from PIL import Image, ImageOps
    im = Image.open(a.src)
    c = im.crop(_box(a, im))
    if a.contrast:                    # tužka, vybledlý inkoust
        c = ImageOps.autocontrast(c.convert("L"), cutoff=1)
    if a.scale != 1:
        c = c.resize((int(c.width * a.scale), int(c.height * a.scale)))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    c.save(a.out, quality=95)
    print(f"{a.out} {c.size[0]}×{c.size[1]} (pracovní kopie, neukládat do sources/)")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="stáhnout snímek z odkazu (plné rozlišení) + sidecar")
    f.add_argument("url")
    f.add_argument("--dest", required=True, help="adresář v sources/ stromu")
    f.add_argument("--entry", help="popis zápisu do sidecaru")
    f.add_argument("--preview", help="cesta k náhledu s mřížkou (scratchpad)")
    f.add_argument("--preview-width", type=int, default=1600)
    f.add_argument("--grid", type=int, default=250, help="krok mřížky v pixelech plného snímku")
    f.set_defaults(func=cmd_fetch)

    for name, fn, hlp in (("crop", cmd_crop, "výřez v plném rozlišení (do stromu)"),
                          ("read", cmd_read, "pracovní kopie ke čtení (zvětšení/kontrast)")):
        c = sub.add_parser(name, help=hlp)
        c.add_argument("src")
        for k in ("x0", "y0", "x1", "y1"):
            c.add_argument(k, type=int)
        c.add_argument("out")
        if name == "read":
            c.add_argument("--scale", type=float, default=1.0)
            c.add_argument("--contrast", action="store_true")
        c.set_defaults(func=fn)

    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
