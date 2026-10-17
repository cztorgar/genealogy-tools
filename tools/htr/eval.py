#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml", "pillow"]
# ///
"""Hodnocení HTR/OCR nástrojů nad trvalou testovací sadou `evals/htr/`.

  eval.py prepare                      # vyřízne výřezy z manifestu do <cache>/crops/<id>.jpg
  eval.py score <dir> [--tool NAME] [--md FILE] [--group G]
                                       # <dir>/<id>.txt = výstup nástroje pro výřez <id>

Vstup `score`: jeden textový soubor na výřez, pojmenovaný podle `id` z manifestu (řádky libovolně zalomené;
za tabulátorem na řádku může být confidence — ignoruje se). Referenční přepis `evals/htr/ref/<id>.txt`
a klíčové tokeny `evals/htr/ref/<id>.json` ({"tokens": [{"t": "Vrbický", "typ": "prijmeni"}, …]},
typ: jmeno | prijmeni | letopocet | cp | misto). Položky bez ref/klíče se přeskočí a vypíšou.

Metriky po skupinách písma (a celkem):
  CER, WER   — Levenshtein nad normalizovaným textem (casefold, bílé znaky sloučeny; diakritika ZACHOVÁNA),
               počítáno jako součet chyb / součet délek reference (ne průměr podílů).
  recall     — podíl klíčových tokenů nalezených ve výstupu: `přesně` (po normalizaci, bez ohledu na diakritiku
               a y/i·w/v není sjednocováno) a `±1` (tolerance 1 záměny/vynechání písmene u tokenů ≥ 5 znaků,
               hledá se v okně slov výstupu). Letopočty a č. p. se musí shodovat přesně.
Matrikové výřezy (`typ: matrika-vyrez`) mají referenci jen pokud existuje evals/htr/ref/<id>.txt.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
EVAL_DIR = HERE.parents[1] / "evals" / "htr"


def load_manifest() -> dict:
    m = yaml.safe_load((EVAL_DIR / "manifest.yml").read_text("utf-8"))
    m["cache"] = Path(m["cache"]).expanduser()
    return m


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s).casefold()
    return re.sub(r"\s+", " ", s).strip()


def strip_diacritics(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))


def lev(a, b) -> int:
    """Levenshtein vzdálenost dvou posloupností (řetězců nebo seznamů slov)."""
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def clean_hyp(text: str) -> str:
    """Vypustí confidence za tabulátorem; řádky spojí mezerou."""
    return " ".join(line.split("\t")[0] for line in text.splitlines())


def token_found(tok: str, hyp: str, typ: str, fuzzy: bool) -> bool:
    t = strip_diacritics(norm(tok))
    h = strip_diacritics(norm(hyp))
    if typ in ("letopocet", "cp"):
        return re.search(rf"(?<!\d){re.escape(t)}(?!\d)", h) is not None
    if not fuzzy:
        return t in h
    if t in h:
        return True
    if len(t) < 5:
        return False
    words = re.findall(r"\w+", h)
    n = len(t.split())
    for i in range(len(words)):
        cand = " ".join(words[i:i + n])
        if lev(t, cand) <= 1:
            return True
    return False


def cmd_prepare(_: argparse.Namespace) -> int:
    from PIL import Image

    m = load_manifest()
    out = m["cache"] / "crops"
    out.mkdir(parents=True, exist_ok=True)
    missing = []
    for it in m["polozky"]:
        if it["typ"] != "archivalie":
            continue
        src = m["cache"] / it["obrazek"]
        if not src.exists():
            missing.append(it)
            continue
        x, y, w, h = it["vyrez"]
        Image.open(src).crop((x, y, x + w, y + h)).save(out / f"{it['id']}.jpg", quality=92)
    for it in missing:
        print(f"chybí {it['obrazek']} → fetch_archivalie_page(archivalie_id={it['archivalie_id']}, "
              f"image={it['snimek']}, dest_dir={m['cache'] / Path(it['obrazek']).parent})", file=sys.stderr)
    print(f"výřezy: {out} ({len(m['polozky']) - len(missing)} z {len(m['polozky'])}; matriky se berou ze stromu)")
    return 1 if missing else 0


def cmd_score(a: argparse.Namespace) -> int:
    m = load_manifest()
    res = Path(a.dir)
    acc = defaultdict(lambda: {"n": 0, "cerE": 0, "cerN": 0, "werE": 0, "werN": 0,
                               "kt": 0, "k_ex": 0, "k_f": 0, "typ": defaultdict(lambda: [0, 0, 0])})
    skipped, rows = [], []
    for it in m["polozky"]:
        if a.group and it["skupina"] != a.group:
            continue
        hyp_f = res / f"{it['id']}.txt"
        ref_f = EVAL_DIR / "ref" / f"{it['id']}.txt"
        key_f = EVAL_DIR / "ref" / f"{it['id']}.json"
        if not hyp_f.exists():
            skipped.append((it["id"], "chybí výstup nástroje"))
            continue
        hyp = clean_hyp(hyp_f.read_text("utf-8"))
        row = {"id": it["id"], "skupina": it["skupina"]}
        for grp in (it["skupina"], "CELKEM"):
            g = acc[grp]
            if ref_f.exists():
                r, h = norm(ref_f.read_text("utf-8")), norm(hyp)
                ce, we = lev(r, h), lev(r.split(), h.split())
                g["cerE"] += ce; g["cerN"] += len(r); g["werE"] += we; g["werN"] += len(r.split())
                row["cer"] = ce / max(len(r), 1); row["wer"] = we / max(len(r.split()), 1)
            if key_f.exists():
                toks = json.loads(key_f.read_text("utf-8"))["tokens"]
                for t in toks:
                    ex = token_found(t["t"], hyp, t["typ"], False)
                    fz = ex or token_found(t["t"], hyp, t["typ"], True)
                    g["kt"] += 1; g["k_ex"] += ex; g["k_f"] += fz
                    tt = g["typ"][t["typ"]]; tt[0] += 1; tt[1] += ex; tt[2] += fz
            g["n"] += 1
        if not ref_f.exists():
            skipped.append((it["id"], "bez ref/*.txt (CER/WER vynecháno)"))
        if not key_f.exists():
            skipped.append((it["id"], "bez ref/*.json (recall vynechán)"))
        rows.append(row)

    def pct(x, n):
        return f"{100 * x / n:.1f} %" if n else "—"

    lines = [f"### {a.tool or res.name}", "",
             "| skupina | stran | CER | WER | recall přesně | recall ±1 | jména | příjmení | letopočty | č. p. |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    order = [g for g in ("latinka20", "kurent19", "kurent18", "matrika-kurent") if g in acc] + ["CELKEM"]
    for grp in order:
        if grp not in acc:
            continue
        g = acc[grp]
        t = g["typ"]
        cell = lambda k: pct(t[k][1], t[k][0]) + f" ({t[k][1]}/{t[k][0]})" if t[k][0] else "—"
        lines.append(f"| {grp} | {g['n']} | {pct(g['cerE'], g['cerN'])} | {pct(g['werE'], g['werN'])} | "
                     f"{pct(g['k_ex'], g['kt'])} | {pct(g['k_f'], g['kt'])} | "
                     f"{cell('jmeno')} | {cell('prijmeni')} | {cell('letopocet')} | {cell('cp')} |")
    if skipped:
        lines += ["", "Přeskočeno: " + "; ".join(f"{i} ({why})" for i, why in skipped)]
    text = "\n".join(lines)
    print(text)
    if a.md:
        with open(a.md, "a", encoding="utf-8") as f:
            f.write("\n" + text + "\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prepare", help="vyřízne výřezy z manifestu").set_defaults(fn=cmd_prepare)
    s = sub.add_parser("score", help="CER/WER a recall klíčových tokenů")
    s.add_argument("dir", help="složka s <id>.txt z hodnoceného nástroje")
    s.add_argument("--tool", help="název nástroje do nadpisu")
    s.add_argument("--group", help="jen jedna skupina písma")
    s.add_argument("--md", help="připsat tabulku na konec markdown souboru")
    s.set_defaults(fn=cmd_score)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
