"""Propojení větví: (1) zhroucení předků — rodiče podle Gramps ≠ rodiče podle ID;
(2) sňatky mezi větvemi — manželé v Gramps, kteří podle ID patří do různých větví (ne X × X-S<n>, ne X-P1 × X-P2, ne Kekule 2n × 2n+1).

Strom dashboardu je postavený z ID (`K%04d` Kekule, přípony `-S/-C/-P`). Skutečné rodinné vazby jsou
v Gramps; když má osoba v Gramps za rodiče někoho z jiné větve ID, je to propojení — typicky zhroucení
předků (sňatek příbuzných). Čte se jen Gramps Web API (`tools/gramps/gw.py`: .env + token cache),
výsledek drží `Links` v paměti a obnovuje po `TTL` sekundách. Do Gramps se nic nezapisuje.

Gramps ID osoby = ID ve workbenchi (`K0001-S2-P2`), takže se páruje přímo.
"""
from __future__ import annotations

import re
import sys
import threading
import time
from pathlib import Path

KEK_RE = re.compile(r"^K(\d+)$")
TTL = 300


def _kek(gid: str) -> int | None:
    m = KEK_RE.match(gid)
    return int(m.group(1)) if m else None


def _struct_parent(gid: str) -> str | None:
    n = _kek(gid)
    if n is not None:
        return f"K{n // 2:04d}" if n > 1 else None
    return re.sub(r"-[SCP]\d+$", "", gid) if "-" in gid else None


def id_parents(gid: str) -> set[str]:
    """Rodiče, které plynou z ID: Kekule 2n/2n+1, jinak `<ID>-P1/-P2`."""
    n = _kek(gid)
    if n is not None:
        return {f"K{2 * n:04d}", f"K{2 * n + 1:04d}"}
    return {f"{gid}-P1", f"{gid}-P2"}


def chain(gid: str) -> list[str]:
    """ID → cesta od K0001: Kekule hlava se rozvine na -P1/-P2 (bit 0 = otec, 1 = matka)."""
    head, *rest = gid.split("-")
    n = _kek(head)
    if n is None:
        return gid.split("-")
    bits = bin(n)[3:]
    return ["K0001"] + ["P1" if b == "0" else "P2" for b in bits] + rest


def kinship(g1: int, g2: int) -> str:
    """Vztah dvou osob podle počtu generací ke společným předkům (g ≥ 1)."""
    lo, hi = sorted((g1, g2))
    deg = g1 + g2
    if lo == 1 and hi == 1:
        rel = "sourozenci"
    elif lo == 1:
        rel = "strýc/teta ↔ synovec/neteř" + (f" ({hi - 2}× pra-)" if hi > 2 else "")
    else:
        rel = f"bratranci/sestřenice z {lo - 1}. kolene" + (f", posun o {hi - lo} gen." if hi != lo else "")
    return f"{rel} — příbuzenství v {deg}. stupni (§ 772 OZ)"


def relation(parent_id: str, child_id: str) -> dict | None:
    """Kde se v ID stromu potkají dvě cesty ke společnému předku a kdo z toho je příbuzný s kým.

    Cesta A = umístění rodiče v ID (`parent_id`), cesta B = dítě (`child_id`) + 1 generace.
    Spočítá se jen tehdy, když za rozcestím vedou obě cesty jen přes -P (předci).
    """
    a, b = chain(parent_id), chain(child_id)
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    if i == 0 or i >= len(a) or i >= len(b):
        return None
    x = "-".join(a[:i])
    ta, tb = a[i:], b[i:]
    ga, gb = len(ta), len(tb) + 1          # generace od rozcestí ke společnému předku
    if not all(t[0] == "P" for t in ta[1:] + tb[1:]):
        return None
    if ta[0][0] == "P" and tb[0][0] == "P":       # otec × matka osoby X
        pa, pb = f"{x}-{ta[0]}", f"{x}-{tb[0]}"
        ga, gb = ga - 1, gb - 1
    elif ta[0][0] == "S" and tb[0][0] == "P":      # X × její/jeho manžel/ka
        pa, pb = f"{x}-{ta[0]}", x
        ga -= 1
    elif ta[0][0] == "P" and tb[0][0] == "S":
        pa, pb = x, f"{x}-{tb[0]}"
        gb -= 1
    else:
        return None
    if ga < 1 or gb < 1:
        return None
    return {"a": pa, "b": pb, "ga": ga, "gb": gb, "text": kinship(ga, gb)}


def compute(people: list[dict], families: list[dict]) -> list[dict]:
    gid = {p["handle"]: p["gramps_id"] for p in people}
    out = []
    for f in families:
        fa, mo = gid.get(f.get("father_handle") or ""), gid.get(f.get("mother_handle") or "")
        parents = [p for p in (fa, mo) if p]
        if not parents:
            continue
        for cr in f.get("child_ref_list") or []:
            c = gid.get(cr.get("ref"))
            if not c:
                continue
            if _struct_parent(c) in parents and re.search(r"-C\d+$", c):
                continue                     # dítě kotvy (X-C1 rodičů X × X-S1)
            wrong = [p for p in parents if p not in id_parents(c)]
            if not wrong:
                continue
            rel = relation(wrong[0], c)
            out.append({"child": c, "parents": parents, "family": f.get("gramps_id"),
                        "id_parents": sorted(id_parents(c)), "relation": rel})
    out.sort(key=lambda r: r["child"])
    return out


def marriages(people: list[dict], families: list[dict]) -> list[dict]:
    """Rodiny, kde manžel a manželka podle ID nejsou pár (X × X-S<n>, Kekule 2n × 2n+1) → sňatek spojuje dvě větve."""
    gid = {p["handle"]: p["gramps_id"] for p in people}
    out = []
    for f in families:
        fa, mo = gid.get(f.get("father_handle") or ""), gid.get(f.get("mother_handle") or "")
        if not fa or not mo:
            continue
        if re.fullmatch(re.escape(fa) + r"-S\d+", mo) or re.fullmatch(re.escape(mo) + r"-S\d+", fa):
            continue
        if fa.endswith("-P1") and mo == fa[:-3] + "-P2":   # rodiče osoby X: X-P1 × X-P2
            continue
        a, b = _kek(fa), _kek(mo)
        if a is not None and b is not None and b == a + 1 and a % 2 == 0:
            continue
        out.append({"a": fa, "b": mo, "family": f.get("gramps_id")})
    out.sort(key=lambda r: (r["a"], r["b"]))
    return out


class Links:
    """Cache vazeb z Gramps v paměti; obnova nejdřív po TTL, chyba se drží jen 60 s."""

    def __init__(self, workbench: Path):
        self.workbench = workbench
        self.lock = threading.Lock()
        self.at = 0.0
        self.ttl = TTL
        self.data: dict = {"links": [], "error": None, "at": None}

    def get(self) -> dict:
        with self.lock:
            if time.time() - self.at < self.ttl:
                return self.data
            self.at = time.time()
            try:
                sys.path.insert(0, str(self.workbench / "tools/gramps"))
                from gw import GrampsWeb   # noqa: E402 — klient workbenche, jen GET
                g = GrampsWeb()
                ps = g.get("/people/?keys=handle,gramps_id&pagesize=100000")
                fs = g.get("/families/?keys=handle,gramps_id,father_handle,mother_handle,child_ref_list&pagesize=100000")
                self.data = {"links": compute(ps, fs), "marriages": marriages(ps, fs), "error": None,
                             "at": time.strftime("%Y-%m-%d %H:%M"), "families": len(fs)}
                self.ttl = TTL
            except Exception as e:  # noqa: BLE001 — Gramps neběží apod.; dashboard jede dál bez propojení
                self.data = dict(self.data, error=f"{type(e).__name__}: {e}"[:300])
                self.ttl = 60
            return self.data
