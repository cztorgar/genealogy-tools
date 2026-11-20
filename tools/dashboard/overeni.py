"""Seznam k ověření proti snímku: `T/research/todo-overeni.md` (vede manager, formát viz hlavička souboru).

Sekce `## <zápis>` s řádky `- online:`, `- soubor:` / `soubory:`, `- osoby:`, `- ověřit:` a `- stav:`.
Čtení živě. Zápis z dashboardu je jen **verdikt uživatele**: v jedné sekci se přepíše řádek `- stav:`
na `sedí` / `nesedí` (+ datum) a za něj se vloží `- poznámka uživatele:`. Zbytek souboru zůstane, zápis
je atomický a ověřený parserem. Jistotu citací pak zvedá manager (`update_citation`) a nastaví `hotovo`.
"""
from __future__ import annotations

import hashlib
import os
import re
import tempfile
import threading
from datetime import datetime
from pathlib import Path

REL = "research/todo-overeni.md"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".tif", ".tiff"}
VERDICTS = {"sedí", "nesedí"}
CLOSED = ("hotovo", "uzavřeno", "vyřízeno")
CROP_HINT = ("_radek", "_radky", "_vyrez", "_detail", "_osoby", "_tabulka")


_LOCK = threading.Lock()   # verdikty z více záložek najednou: čtení–kontrola–zápis jako jeden krok


def _sid(title: str, body: str, n: int) -> str:
    """ID sekce z obsahu, který se verdiktem nemění (nadpis, odkaz, body „ověřit“) — nová sekce se stejným
    nadpisem jinde v souboru tak nepřevezme ID té, kterou má uživatel otevřenou."""
    keep = "\n".join(m.group(0) for m in re.finditer(r"^- (?:online|ověřit):.*$", body, re.M))
    return hashlib.sha1(f"{title}\0{keep}\0{n}".encode()).hexdigest()[:10]


def _spans(text: str) -> dict[str, tuple[str, int, int]]:
    """ID → (nadpis, začátek, konec); `n` rozliší jen úplně shodné sekce."""
    seen: dict[str, int] = {}
    out = {}
    for title, a, b in _sections(text):
        sid0 = _sid(title, text[a:b], 0)
        seen[sid0] = seen.get(sid0, -1) + 1
        out[_sid(title, text[a:b], seen[sid0])] = (title, a, b)
    return out


def _sections(text: str) -> list[tuple[str, int, int]]:
    """(nadpis, začátek, konec) každé sekce `## ` — v pořadí souboru."""
    heads = [m for m in re.finditer(r"^## (.+)$", text, re.M)]
    return [(m.group(1).strip(), m.start(), heads[i + 1].start() if i + 1 < len(heads) else len(text))
            for i, m in enumerate(heads)]


def _files(line: str, root: Path) -> list[str]:
    """Cesty v backtickách; holý název souboru se bere ze složky předchozí cesty."""
    out, last_dir = [], ""
    for raw in re.findall(r"`([^`]+)`", line):
        raw = raw.strip()
        if "{" in raw:            # sources/scitani/{1890,1900}-lhota/… — rozbalit
            m = re.match(r"(.*)\{([^}]+)\}(.*)", raw)
            cands = [m.group(1) + x + m.group(3) for x in m.group(2).split(",")] if m else []
        elif "/" not in raw and last_dir:
            cands = [f"{last_dir}/{raw}"]
        else:
            cands = [raw]
        for c in cands:
            p = root / c
            if p.is_dir():
                out += [str(f.relative_to(root)) for f in sorted(p.iterdir()) if f.suffix.lower() in IMAGE_EXT]
                last_dir = c.rstrip("/")
            elif p.is_file():
                out.append(c)
                last_dir = str(Path(c).parent)
    return list(dict.fromkeys(out))


def parse(path: Path, root: Path, ids_in) -> list[dict]:
    return parse_text(path.read_text(encoding="utf-8", errors="replace"), root, ids_in)


def parse_text(text: str, root: Path, ids_in) -> list[dict]:
    out = []
    for sid, (title, a, b) in _spans(text).items():
        body = text[a:b]
        line = lambda key: next((m.group(1).strip() for m in re.finditer(rf"^- {key}:\s*(.+)$", body, re.M)), "")
        online = line("online")
        files = _files(online + " " + line(r"soubory?"), root)
        imgs = [f for f in files if Path(f).suffix.lower() in IMAGE_EXT]
        crops = [f for f in imgs if any(h in Path(f).name for h in CROP_HINT)]
        stav = line("stav") or "otevřeno"
        out.append({
            "id": sid, "title": title,
            "url": (re.search(r"https?://\S+", online) or [None])[0] if online else None,
            "files": imgs,
            "vyrez": crops[0] if crops else (imgs[0] if imgs else None),
            "snimek": next((f for f in imgs if f not in crops), None),
            "osoby": ids_in(line("osoby")),
            "overit": [m.group(1).strip() for m in re.finditer(r"^- ověřit:\s*(.+)$", body, re.M)],
            "poznamka": line("poznámka uživatele"),
            "stav": stav,
            "verdikt": next((v for v in VERDICTS if stav.lower().startswith(v)), None),
            "open": not stav.lower().startswith(CLOSED) and not any(stav.lower().startswith(v) for v in VERDICTS),
        })
    return out


class VerdictError(Exception):
    pass


def decide(root: Path, sid: str, verdikt: str, poznamka: str, ids_in) -> dict:
    with _LOCK:
        return _decide(root, sid, verdikt, poznamka, ids_in)


def _decide(root: Path, sid: str, verdikt: str, poznamka: str, ids_in) -> dict:
    verdikt, poznamka = (verdikt or "").strip(), " ".join((poznamka or "").split())
    if verdikt not in VERDICTS:
        raise VerdictError("verdikt musí být „sedí“ nebo „nesedí“")
    if verdikt == "nesedí" and not poznamka:
        raise VerdictError("u „nesedí“ napiš, co je jinak")
    if len(poznamka) > 3000:
        raise VerdictError("poznámka je příliš dlouhá")
    path = root / REL
    if not path.is_file():
        raise VerdictError(f"{REL} neexistuje — načti stránku znovu")
    st = path.stat()
    text = path.read_text(encoding="utf-8")
    before = parse_text(text, root, ids_in)
    target = next((s for s in before if s["id"] == sid), None)
    if target is None:
        raise VerdictError("sekce nenalezena — soubor se mezitím změnil, načti znovu")
    if target["stav"].lower().startswith(CLOSED):
        raise VerdictError("sekce je už uzavřená (hotovo)")
    _, a, b = _spans(text)[sid]
    body = text[a:b]
    body = re.sub(r"^- poznámka uživatele:.*\n?", "", body, flags=re.M)
    kdy = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_stav = f"- stav: {verdikt} (uživatel {kdy}) — čeká na managera\n"
    if poznamka:
        new_stav += f"- poznámka uživatele: {poznamka}\n"
    body, n = re.subn(r"^- stav:.*\n?", new_stav, body, count=1, flags=re.M)
    if not n:
        body = body.rstrip("\n") + "\n" + new_stav + ("\n" if b < len(text) else "")
    new = text[:a] + body + text[b:]

    after = parse_text(new, root, ids_in)
    changed = [(x["id"], x["stav"]) for x, y in zip(before, after) if (x["title"], x["overit"]) != (y["title"], y["overit"])]
    got = next((s for s in after if s["id"] == sid), None)
    if len(after) != len(before) or changed or not got or got["verdikt"] != verdikt:
        raise VerdictError("úprava souboru neprošla kontrolou — nic nezapsáno")

    now = path.stat()
    if (now.st_mtime_ns, now.st_size) != (st.st_mtime_ns, st.st_size):
        raise VerdictError("soubor se mezitím změnil — načti znovu")
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
    return {"id": sid, "title": got["title"], "stav": got["stav"], "verdikt": verdikt, "osoby": got["osoby"]}
