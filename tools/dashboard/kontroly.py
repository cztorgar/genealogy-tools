"""Fronta kontrol: `T/research/kontroly/<ID>-<nn>.yml` a `G-<nn>.yml` (formát `docs/metodika/autonomie.md`, kap. 5).

Čtení živě. **Jediný zápis dashboardu** je rozhodnutí: v souboru kontroly se přepíší jen
klíče `stav` a `rozhodnuti` (textovou úpravou řádků, zbytek souboru včetně komentářů zůstane),
výsledek se ověří parserem a zapíše atomicky.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

import yaml

FILE_RE = re.compile(r"^(?:K\d+(?:-[SCP]\d+)*|G)-\d+\.ya?ml$")
OPEN = "otevřeno"
DECIDABLE = {"otevřeno", "rozhodnuto"}
CHANGED_KEYS = {"stav", "rozhodnuti"}


def files(root: Path) -> list[Path]:
    d = root / "research/kontroly"
    return sorted(p for p in d.glob("*.y*ml") if FILE_RE.match(p.name)) if d.is_dir() else []


def _kdy(v) -> str:
    if isinstance(v, dict):
        v = v.get("kdy")
    return str(v or "")


def load(paths: list[Path], cache, load_yaml, root: Path, norm_any) -> list[dict]:
    out = []
    for p in paths:
        data = cache.get(p, "yaml", load_yaml)
        rel = str(p.relative_to(root))
        if not isinstance(data, dict):
            out.append({"id": p.stem, "file": rel, "error": "neplatný YAML", "stav": OPEN, "blokuje": False,
                        "priorita": 1, "typ": "nastroj", "varianty": [], "souvisi": [], "vzniklo_kdy": "", "otazka": f"Soubor {rel} nejde načíst (neplatný YAML)."})
            continue
        k = dict(data)
        k["id"] = str(k.get("id") or p.stem)
        k["file"] = rel
        k["osoba"] = norm_any(k.get("osoba")) if k.get("osoba") else None
        k["stav"] = str(k.get("stav") or OPEN)
        k["blokuje"] = bool(k.get("blokuje"))
        try:
            k["priorita"] = int(k.get("priorita") or 3)
        except (TypeError, ValueError):
            k["priorita"] = 3
        if k["blokuje"]:
            k["priorita"] = 1
        k["vzniklo_kdy"] = _kdy(k.get("vzniklo"))
        k["varianty"] = [v if isinstance(v, dict) else {"volba": str(v)} for v in (k.get("varianty") or [])]
        k["souvisi"] = [str(x) for x in (k.get("souvisi") or [])] if isinstance(k.get("souvisi"), list) \
            else ([str(k["souvisi"])] if k.get("souvisi") else [])
        for f in ("snimek", "vyrez"):
            if k.get(f) and not (root / str(k[f])).is_file():
                k[f + "_chybi"] = True
        out.append(json.loads(json.dumps(k, default=str)))   # data → JSON-bezpečné (datumy z YAML)
    out.sort(key=lambda k: (k["stav"] != OPEN, not k["blokuje"], k["priorita"], k["vzniklo_kdy"] or "9999", k["id"]))
    return out


# ---------------------------------------------------------------- zápis rozhodnutí

def _q(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)   # řetězec v uvozovkách JSON = platný YAML skalár


def _replace_key(lines: list[str], key: str, new_line: str) -> list[str]:
    """Nahradí top-level klíč (řádek `key:` + jeho odsazené pokračování) jedním řádkem; jinak připojí."""
    for i, ln in enumerate(lines):
        if re.match(rf"^{key}\s*:", ln):
            j = i + 1
            while j < len(lines) and (lines[j].startswith((" ", "\t")) or
                                      (not lines[j].strip() and j + 1 < len(lines) and lines[j + 1].startswith((" ", "\t")))):
                j += 1
            return lines[:i] + [new_line] + lines[j:]
    if lines and not lines[-1].endswith("\n"):
        lines = lines[:-1] + [lines[-1] + "\n"]
    return lines + [new_line]


class DecisionError(Exception):
    pass


def decide(root: Path, kid: str, volba: str, poznamka: str) -> dict:
    volba, poznamka = (volba or "").strip(), (poznamka or "").strip()
    if not volba:
        raise DecisionError("chybí volba")
    if len(volba) > 2000 or len(poznamka) > 5000:
        raise DecisionError("text je příliš dlouhý")
    path = next((p for p in files(root) if p.stem == kid), None)
    if path is None:
        raise DecisionError(f"kontrola {kid} neexistuje")
    st = path.stat()
    text = path.read_text(encoding="utf-8")
    try:
        before = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise DecisionError(f"soubor není platný YAML: {e}") from None
    if not isinstance(before, dict):
        raise DecisionError("soubor není mapa YAML")
    if str(before.get("stav") or OPEN) not in DECIDABLE:
        raise DecisionError(f"kontrola je ve stavu „{before.get('stav')}“ — rozhodnutí už nejde měnit")

    kdy = datetime.now().strftime("%Y-%m-%d %H:%M")
    rozh = {"volba": volba, "poznamka": poznamka or None, "kdo": "uzivatel", "kdy": kdy}
    lines = text.splitlines(keepends=True)
    lines = _replace_key(lines, "stav", "stav: rozhodnuto\n")
    lines = _replace_key(lines, "rozhodnuti",
                         f"rozhodnuti: {{volba: {_q(volba)}, poznamka: {_q(poznamka) if poznamka else 'null'}, "
                         f"kdo: uzivatel, kdy: {_q(kdy)}}}\n")
    new = "".join(lines)

    after = yaml.safe_load(new)                # ověření: změnila se jen dvě pole
    if not isinstance(after, dict) or after.get("stav") != "rozhodnuto" or after.get("rozhodnuti") != rozh:
        raise DecisionError("úprava souboru neprošla kontrolou — nic nezapsáno")
    if {k: v for k, v in before.items() if k not in CHANGED_KEYS} != {k: v for k, v in after.items() if k not in CHANGED_KEYS}:
        raise DecisionError("úprava by změnila i jiná pole — nic nezapsáno")

    now = path.stat()
    if (now.st_mtime_ns, now.st_size) != (st.st_mtime_ns, st.st_size):
        raise DecisionError("soubor se mezitím změnil — načti znovu")
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(new)
        os.chmod(tmp, st.st_mode & 0o777)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return {"id": kid, "file": str(path.relative_to(root)), "osoba": before.get("osoba"), "rozhodnuti": rozh}
