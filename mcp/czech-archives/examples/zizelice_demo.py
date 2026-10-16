"""Ukázka / kouřový test modulu aron_zamrsk (bez MCP).

    uv run --directory mcp/czech-archives python examples/zizelice_demo.py [cílový_adresář]

1. vypíše matriky narozených 1840–1860, kde se vyskytuje Žiželice,
2. vypíše všechny matriky 18.–19. století pro Žiželice (všechny druhy),
3. vypíše sčítací operáty Žiželice,
4. stáhne 1 snímek (svazek a snímek viz níže) do cílového adresáře + sidecar .yml.

Každý požadavek na portál čeká ~2,5 s; druhé spuštění jede z cache.
"""

from __future__ import annotations

import sys
from pathlib import Path

from czech_archives.modules import get

# Chlumec n. C., N 1855–1859, sign. 55-8 — obsahuje fol. 259–260 narozené mimo farnost
# (Loukonosy, Převýšov, Hradišťko), tj. i místní části dnešní obce Žiželice.
DEMO_REGISTER = "d55af1cf-2d6c-4600-94eb-fcb6c89db2cb"
DEMO_IMAGE = 5


def show(title, regs):
    print(f"\n== {title}: {len(regs)}")
    for r in regs:
        print(f"  {r.id}  {''.join(r.kinds) or '?':4} {r.years_text or '':>16}  "
              f"{r.confession or '':5} sign. {r.signature}  | {(r.places or '')[:70]}")


def main():
    dest = Path(sys.argv[1] if len(sys.argv) > 1 else "./demo-out")
    aron = get("aron_zamrsk")
    show("Žiželice, N 1840–1860", aron.find_registers("Žiželice", 1840, 1860, "N"))
    show("Žiželice, matriky 1700–1900", aron.find_registers("Žiželice", 1700, 1900))
    show("Žiželice, sčítací operáty", aron.find_registers("Žiželice", kind="S"))

    reg = aron.register_info(DEMO_REGISTER)
    print(f"\n== register_info {reg.id}\n  {reg.title}\n  farnost: {reg.parish}; původce: {reg.originator}"
          f"\n  snímků: {reg.image_count}; sada: {reg.set_id}; ZIP: {reg.zip_url}"
          f"\n  oficiální citace: {reg.official_citation}")
    out = aron.fetch_page(DEMO_REGISTER, DEMO_IMAGE, dest)
    print(f"\n== staženo: {out} ({out.stat().st_size} B)\n--- {out.with_suffix('.yml')}")
    print(out.with_suffix(".yml").read_text("utf-8"))


if __name__ == "__main__":
    main()
