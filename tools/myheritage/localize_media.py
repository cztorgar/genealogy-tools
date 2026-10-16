#!/usr/bin/env python3
"""Přepíše odkazy na média v GEDCOM exportu z MyHeritage na lokální soubory.

MyHeritage exportuje média jako podepsané URL na CDN (sites-cf.mhcache.com), které po pár dnech
expirují. Média se stáhnou do media/ stromu (download_media.py) a tento skript nahradí
`FILE https://…/<jméno>.jpg` za `FILE <jméno>.jpg` (relativně k media/ = base path v Gramps).

Použití: localize_media.py <vstup.ged> <výstup.ged> <media_dir>
"""
import re
import sys
from pathlib import Path

URL_RE = re.compile(r"^(\d+ FILE )(https?://\S*mhcache\.com/\S+)$")


def main(src: str, dst: str, media_dir: str) -> int:
    media = Path(media_dir)
    text = Path(src).read_text(encoding="utf-8-sig")
    out, replaced, missing = [], 0, []
    for line in text.splitlines():
        m = URL_RE.match(line)
        if m:
            name = m.group(2).rsplit("/", 1)[-1]
            if (media / name).is_file():
                line = m.group(1) + name
                replaced += 1
            else:
                missing.append(name)
        out.append(line)
    Path(dst).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"nahrazeno {replaced}, chybí lokálně {len(missing)}")
    for name in missing:
        print("  chybí:", name)
    return 1 if missing else 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    sys.exit(main(*sys.argv[1:]))
