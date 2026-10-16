#!/usr/bin/env python3
"""Stáhne média z GEDCOM exportu MyHeritage do lokální složky.

Odkazy na CDN MyHeritage jsou podepsané a expirují (parametr e= v base64 části URL) — stahovat hned
po exportu. Už stažené soubory přeskočí. Šetrně: jeden soubor po druhém s krátkou pauzou.

Použití: download_media.py <export.ged> <media_dir>
"""
import re
import sys
import time
import urllib.request
from pathlib import Path

URL_RE = re.compile(r"https://sites-cf\.mhcache\.com/\S+")


def main(ged: str, media_dir: str) -> int:
    dest = Path(media_dir)
    dest.mkdir(parents=True, exist_ok=True)
    urls = sorted(set(URL_RE.findall(Path(ged).read_text(encoding="utf-8-sig"))))
    ok = fail = 0
    for url in urls:
        target = dest / url.rsplit("/", 1)[-1]
        if target.is_file() and target.stat().st_size:
            ok += 1
            continue
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                target.write_bytes(r.read())
            ok += 1
        except Exception as e:  # noqa: BLE001 — chceme pokračovat a vypsat všechny chyby
            fail += 1
            print(f"CHYBA {url}: {e}")
        time.sleep(0.5)
    print(f"celkem {len(urls)}, ok {ok}, chyb {fail}")
    return 1 if fail else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(*sys.argv[1:]))
