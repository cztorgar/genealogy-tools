#!/usr/bin/env python3
"""Uloží snímek stromu z Gramps Web (formát .gramps = gzip XML) do `data/gramps/` stromu.

Slouží k zafixování stavu (git tag nad stromem + export Gramps se stejným datem).
Použití: export_snapshot.py <strom-dir> [--label stav-YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gw import GrampsWeb  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tree", type=Path)
    ap.add_argument("--label", default=f"stav-{dt.date.today().isoformat()}")
    a = ap.parse_args()
    gw = GrampsWeb()
    req = urllib.request.Request(gw.base + "/exporters/gramps/file")
    req.add_header("Authorization", f"Bearer {gw.token}")
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read()
    xml = gzip.decompress(data) if data[:2] == b"\x1f\x8b" else data
    if b"<database" not in xml[:2000]:
        print(f"neočekávaná odpověď exportu ({len(data)} B): {data[:200]!r}", file=sys.stderr)
        return 1
    out = a.tree / "data" / "gramps" / f"{a.label}.gramps"
    out.write_bytes(gzip.compress(xml, mtime=0))
    print(f"{out} ({xml.count(b'<person ')} osob, {len(xml) // 1024} KiB XML)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
