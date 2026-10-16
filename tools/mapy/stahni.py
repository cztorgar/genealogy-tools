#!/usr/bin/env python3
"""Stáhne mapové vrstvy pro oblast, složí je do georeferencované mozaiky a vygeneruje XYZ dlaždice.

Všechny vrstvy končí ve **stejné mřížce** — XYZ / EPSG:3857, 256 px — takže se ve webové mapě
skládají přesně na sebe. Mezikrokem je mozaika GeoTIFF v nativním CRS zdroje (S-JTSK nebo
Web Mercator) s přesnou geotransformací z mřížky služby; ta je „master“ pro QGIS i pro
pozdější přegenerování. Ke každé vrstvě se zapíše manifest.json (zdroj, mřížka, licence,
počty, hashe) a tilejson.json.

Šetrně: jeden požadavek za ~1 s (nastavitelné), stažené odpovědi se cachují (navazuje se),
stahuje se jen obálka oblasti.

Použití:
  .venv/bin/python tools/mapy/stahni.py <oblast> [vrstva …] [--odhad] [--bez-stahovani] [--bez-dlazdic]
  oblast = tools/mapy/oblasti/<oblast>.geojson; výstup cache/mapy/<oblast>/<vrstva>/
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import math
import re
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
import requests
import yaml
from PIL import Image
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject, transform_bounds
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
UA = "genealogy-workbench/0.1 (soukromy rodopisny vyzkum; tools/mapy)"
MERC = 20037508.342789244          # polovina obvodu Web Mercatoru
TILE = 256
VERZE = 1


# ---------- oblast ----------

def nacti_oblast(nazev: str, buffer_m: float) -> dict:
    gj = json.loads((HERE / "oblasti" / f"{nazev}.geojson").read_text())
    xs, ys = [], []
    for f in gj["features"]:
        g = f["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for p in polys:
            for ring in p:
                for x, y in ring:
                    xs.append(x)
                    ys.append(y)
    lat = (min(ys) + max(ys)) / 2
    dlat = buffer_m / 111_320
    dlon = buffer_m / (111_320 * math.cos(math.radians(lat)))
    return {"nazev": nazev, "bbox_wgs84": [min(xs) - dlon, min(ys) - dlat, max(xs) + dlon, max(ys) + dlat],
            "buffer_m": buffer_m, "ku": [f["properties"] for f in gj["features"]]}


# ---------- šetrné stahování ----------

class Fetcher:
    def __init__(self, interval: float):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = UA
        self.interval = interval
        self.last = 0.0
        self.pocet = 0

    def get(self, url: str, params: dict | None = None) -> requests.Response:
        for pokus in range(5):
            wait = self.interval - (time.monotonic() - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.monotonic()
            try:
                r = self.s.get(url, params=params, timeout=90)
                self.pocet += 1
            except requests.RequestException as e:
                print(f"  ! {e} — zkusím znovu", file=sys.stderr)
                time.sleep(10 * (pokus + 1))
                continue
            if r.status_code in (429, 500, 502, 503, 504):
                print(f"  ! HTTP {r.status_code} — zpomaluji", file=sys.stderr)
                time.sleep(30 * (pokus + 1))
                continue
            return r
        raise RuntimeError(f"nepodařilo se stáhnout {url}")


def obrazek(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    img.load()
    return img.convert("RGBA")


# ---------- mřížky ----------

def plan_wmts(v: dict, bb: tuple) -> list[dict]:
    ox, oy = v["origin"]
    step = v["res"] * v["tile"]
    c0, c1 = math.floor((bb[0] - ox) / step), math.floor((bb[2] - ox) / step)
    r0, r1 = math.floor((oy - bb[3]) / step), math.floor((oy - bb[1]) / step)
    kusy = []
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            kusy.append({"soubor": f"{v['level']}/{r}/{c}", "radek": r - r0, "sloupec": c - c0,
                         "url": v["url"].format(z=v["level"], row=r, col=c), "params": None})
    sirka, vyska = (c1 - c0 + 1) * v["tile"], (r1 - r0 + 1) * v["tile"]
    transform = from_origin(ox + c0 * step, oy - r0 * step, v["res"], v["res"])
    return kusy, sirka, vyska, transform, v["tile"], 0


def plan_wms(v: dict, bb: tuple) -> list[dict]:
    res, meta, g = v["res"], v["meta"], v.get("gutter", 0)
    step = res * meta
    # zarovnání na globální mřížku (násobky step od 0) → opakované běhy dávají stejné kusy
    c0, c1 = math.floor(bb[0] / step), math.floor(bb[2] / step)
    r0, r1 = math.floor(-bb[3] / step), math.floor(-bb[1] / step)
    kusy = []
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            minx, maxy = c * step - g * res, -r * step + g * res
            maxx, miny = (c + 1) * step + g * res, -(r + 1) * step - g * res
            box = f"{minx:.6f},{miny:.6f},{maxx:.6f},{maxy:.6f}"
            n = meta + 2 * g
            if v["typ"] == "wms":
                p = {"SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap", "SRS": v["crs"],
                     "BBOX": box, "WIDTH": n, "HEIGHT": n, **v["params"]}
            else:
                code = v["crs"].split(":")[1]
                p = {"bbox": box, "bboxSR": code, "imageSR": code, "size": f"{n},{n}", **v["params"]}
            kusy.append({"soubor": f"{r}_{c}", "radek": r - r0, "sloupec": c - c0, "url": v["url"], "params": p})
    sirka, vyska = (c1 - c0 + 1) * meta, (r1 - r0 + 1) * meta
    transform = from_origin(c0 * step, -r0 * step, res, res)
    return kusy, sirka, vyska, transform, meta, g


def over_wmts(v: dict, f: Fetcher) -> dict | None:
    """Ověří res/origin proti GetCapabilities a vrátí popis TileMatrix do manifestu."""
    if "capabilities" not in v or v["typ"] != "wmts":
        return None
    x = f.get(v["capabilities"]).text
    for m in re.findall(r"<TileMatrix>(.*?)</TileMatrix>", x, re.S):
        ident = re.search(r"<ows:Identifier>(.*?)</ows:Identifier>", m).group(1)
        if ident == str(v["level"]):
            sd = float(re.search(r"<ScaleDenominator>(.*?)</ScaleDenominator>", m).group(1))
            tl = [float(t) for t in re.search(r"<TopLeftCorner>(.*?)</TopLeftCorner>", m).group(1).split()]
            ts = int(re.search(r"<TileWidth>(.*?)</TileWidth>", m).group(1))
            res = sd * 0.00028
            if abs(res - v["res"]) > 1e-6 or tl != v["origin"] or ts != v["tile"]:
                raise SystemExit(f"mřížka {v['url']} nesedí s capabilities: res {res}, origin {tl}, tile {ts}")
            return {"identifier": ident, "scale_denominator": sd, "top_left": tl, "tile": ts, "res": res}
    raise SystemExit(f"úroveň {v['level']} v capabilities nenalezena")


# ---------- vrstva ----------

def stahni_vrstvu(klic: str, v: dict, oblast: dict, out: Path, f: Fetcher, odhad: bool, stahovat: bool) -> dict:
    bb = transform_bounds("EPSG:4326", v["crs"], *oblast["bbox_wgs84"], densify_pts=50)
    kusy, sirka, vyska, transform, krok, gutter = (plan_wmts if v["typ"] == "wmts" else plan_wms)(v, bb)
    print(f"[{klic}] {v['nazev']}: {len(kusy)} požadavků, mozaika {sirka}×{vyska} px ({v['crs']}, {v['res']:.4f} m/px)")
    if odhad:
        return {}
    matrix = over_wmts(v, f) if stahovat else None
    src = out / "src"
    tif = out / f"{klic}.tif"
    ext = "png" if v["typ"] != "wmts" and "png" in str(v.get("params", {})).lower() else "img"
    with rasterio.open(tif, "w", driver="GTiff", width=sirka, height=vyska, count=4, dtype="uint8",
                       crs=v["crs"], transform=transform, tiled=True, blockxsize=512, blockysize=512,
                       compress="deflate", predictor=2, photometric="RGB", BIGTIFF="IF_SAFER") as ds:
        ds.colorinterp = [rasterio.enums.ColorInterp.red, rasterio.enums.ColorInterp.green,
                          rasterio.enums.ColorInterp.blue, rasterio.enums.ColorInterp.alpha]
        prazdne = 0
        for i, k in enumerate(kusy, 1):
            p = src / f"{k['soubor']}.{ext}"
            if not p.exists():
                if not stahovat:
                    continue
                r = f.get(k["url"], k["params"])
                ct = r.headers.get("content-type", "")
                if r.status_code == 404 or (r.status_code == 200 and not ct.startswith("image")):
                    if r.status_code == 404 or "xml" in ct or "text" in ct:
                        # mimo pokrytí / chyba služby — uložit text pro kontrolu, kus vynechat
                        p.parent.mkdir(parents=True, exist_ok=True)
                        p.with_suffix(".err").write_bytes(r.content[:4000])
                        prazdne += 1
                        continue
                r.raise_for_status()
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(r.content)
                if i % 25 == 0 or i == len(kusy):
                    print(f"  {i}/{len(kusy)}")
            img = np.asarray(obrazek(p.read_bytes()))
            if gutter:
                img = img[gutter:gutter + krok, gutter:gutter + krok]
            win = Window(k["sloupec"] * krok, k["radek"] * krok, krok, krok)
            ds.write(np.moveaxis(img, 2, 0), window=win)
        ds.build_overviews([2, 4, 8, 16, 32], Resampling.average)
        ds.update_tags(zdroj=v["url"], licence=v["licence"], citace=v["citace"])
    return {"pozadavku": len(kusy), "mimo_pokryti": prazdne, "mozaika_px": [sirka, vyska],
            "bbox_nativni": list(bb), "geotransform": list(transform)[:6], "tile_matrix": matrix}


# ---------- XYZ ----------

def xyz_rozsah(bb4326: list, z: int) -> tuple:
    def x(lon):
        return int((lon + 180) / 360 * 2 ** z)

    def y(lat):
        la = math.radians(lat)
        return int((1 - math.log(math.tan(la) + 1 / math.cos(la)) / math.pi) / 2 * 2 ** z)
    return x(bb4326[0]), y(bb4326[3]), x(bb4326[2]), y(bb4326[1])


def dlazdice(klic: str, v: dict, oblast: dict, out: Path) -> dict:
    tif = out / f"{klic}.tif"
    rs = getattr(Resampling, v.get("resampling", "bilinear"))
    fmt = v.get("format", "webp")
    pocet, bajtu = 0, 0
    z0, z1 = v["zoom"]
    with rasterio.open(tif) as src:
        for z in range(z0, z1 + 1):
            x0, y0, x1, y1 = xyz_rozsah(oblast["bbox_wgs84"], z)
            size = 2 * MERC / 2 ** z
            for tx in range(x0, x1 + 1):
                for ty in range(y0, y1 + 1):
                    dst = np.zeros((4, TILE, TILE), dtype="uint8")
                    tr = from_origin(-MERC + tx * size, MERC - ty * size, size / TILE, size / TILE)
                    reproject(rasterio.band(src, [1, 2, 3, 4]), dst, dst_transform=tr, dst_crs="EPSG:3857",
                              resampling=rs, src_nodata=None, dst_nodata=None)
                    if not dst[3].any():
                        continue
                    img = Image.fromarray(np.moveaxis(dst, 0, 2), "RGBA")
                    p = out / "xyz" / str(z) / str(tx) / f"{ty}.{fmt}"
                    p.parent.mkdir(parents=True, exist_ok=True)
                    if fmt == "webp":
                        img.save(p, "WEBP", quality=85, method=4)
                    else:
                        img.save(p, "PNG", optimize=True)
                    pocet += 1
                    bajtu += p.stat().st_size
            print(f"  [{klic}] z{z}: hotovo ({pocet} dlaždic celkem)")
    return {"scheme": "xyz", "crs": "EPSG:3857", "tile": TILE, "zoom": [z0, z1], "format": fmt,
            "dlazdic": pocet, "bajtu": bajtu, "sablona": "xyz/{z}/{x}/{y}." + fmt}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("oblast")
    ap.add_argument("vrstvy", nargs="*")
    ap.add_argument("--buffer", type=float, default=300, help="okraj kolem hranic k. ú. v metrech")
    ap.add_argument("--interval", type=float, default=1.0, help="min. odstup požadavků v s")
    ap.add_argument("--odhad", action="store_true", help="jen vypsat počet požadavků")
    ap.add_argument("--bez-stahovani", action="store_true", help="jen z cache")
    ap.add_argument("--bez-dlazdic", action="store_true")
    a = ap.parse_args()

    cfg = yaml.safe_load((HERE / "vrstvy.yml").read_text())["vrstvy"]
    oblast = nacti_oblast(a.oblast, a.buffer)
    f = Fetcher(a.interval)
    for klic in a.vrstvy or list(cfg):
        v = cfg[klic]
        out = ROOT / "cache" / "mapy" / a.oblast / klic
        out.mkdir(parents=True, exist_ok=True)
        info = stahni_vrstvu(klic, v, oblast, out, f, a.odhad, not a.bez_stahovani)
        if a.odhad:
            continue
        xyz = None if a.bez_dlazdic else dlazdice(klic, v, oblast, out)
        mf_path = out / "manifest.json"
        stary = json.loads(mf_path.read_text()) if mf_path.exists() else {}
        mf = {
            "verze_nastroje": VERZE, "vrstva": klic, "nazev": v["nazev"], "oblast": oblast,
            "zdroj": {k: v[k] for k in ("typ", "url", "capabilities", "params", "crs", "res", "level",
                                        "origin", "tile", "meta", "gutter") if k in v},
            "licence": v["licence"], "citace": v["citace"],
            "stazeno": stary.get("stazeno") if a.bez_stahovani else dt.date.today().isoformat(),
            "mozaika": {"soubor": f"{klic}.tif", "sha256": sha256(out / f"{klic}.tif"), **info},
            "xyz": xyz or stary.get("xyz"),
        }
        mf_path.write_text(json.dumps(mf, ensure_ascii=False, indent=2))
        if mf["xyz"]:
            (out / "tilejson.json").write_text(json.dumps({
                "tilejson": "3.0.0", "name": v["nazev"], "attribution": v["citace"],
                "tiles": [mf["xyz"]["sablona"]], "minzoom": mf["xyz"]["zoom"][0], "maxzoom": mf["xyz"]["zoom"][1],
                "bounds": oblast["bbox_wgs84"], "scheme": "xyz"}, ensure_ascii=False, indent=2))
        print(f"[{klic}] manifest: {mf_path.relative_to(ROOT)}")
    print(f"požadavků celkem: {f.pocet}")


if __name__ == "__main__":
    main()
