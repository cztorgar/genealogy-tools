#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6"]
# ///
"""Workbench dashboard — živý přehled stavu výzkumu nad stromem.

Čte **živé soubory stromu** při každém požadavku (jen paměťová cache podle mtime), nic negeneruje.
Jediný zápis: rozhodnutí kontroly do `research/kontroly/<id>.yml` (POST z této stránky, token proti CSRF).
Poslouchá jen na 127.0.0.1.

    uv run tools/dashboard/server.py [--tree berescak] [--port 5056]

API:
    GET /api/state[?v=<verze>]   souhrn (osoby, session, patche, todo, log); při stejné verzi {"unchanged": true}
    GET /api/person/<ID>         vše k osobě (dossier, nápovědy, patche, todo, prameny)
    GET /api/file?p=<cesta>      soubor stromu (snímky, přepisy) — jen čtení, jen uvnitř stromu
    POST /api/kontrola/<id>      rozhodnutí kontroly {volba, poznamka}; hlavička X-Dashboard-Token
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import json
import mimetypes
import os
import re
import secrets
import subprocess
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import yaml

import evidence
import gramps_links
import kontroly
import mapdata

WORKBENCH = Path(__file__).resolve().parents[2]
STATIC = Path(__file__).resolve().parent / "static"
sys.path.insert(0, str(WORKBENCH / "tools/research"))
import checklist as cl  # noqa: E402 — šablona checklistu (základní / rozšířený), sdílená s checklist_sync.py
import fronta  # noqa: E402 — pořadí osob fáze I

# ID osoby: Kekule K%04d + přípony -S<n> (manžel/ka), -C<n> (dítě), -P1/-P2 (otec/matka)
ID_RE = re.compile(r"\bK(\d{1,5})((?:-[SCP]\d+)*)\b")
ID_FULL_RE = re.compile(r"^K\d+(?:-[SCP]\d+)*$")
HINT_ID_RE = re.compile(r"^(K\d+(?:-[SCP]\d+)*)-")
SESSION_NAME_RE = re.compile(r"^k\d+(?:-[scp]\d+)*$")
BRANCH_NAME_RE = re.compile(r"^vetev-[\w-]+$")      # session větve (docs/metodika/workflow-sessions.md)
CLAUDE_PROJECTS = Path.home() / ".claude/projects"

# uzavřeno = fáze I hotová (základní checklist celý nalezen / nenalezen s důvodem) — počítá se, v dossieru se nepíše
STATES = ["zmínka", "převzato", "rozpracováno", "pozastaveno", "dokončeno", "zapsáno", "uzavřeno"]
PATCH_WAITING = {"navrženo", "schváleno"}
TODO_CLOSED = ("nalezeno", "nenalezeno", "zodpovězeno", "neví", "hotovo", "vyřízeno", "uzavřeno")
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".tif", ".tiff"}
TEXT_EXT = {".md", ".yml", ".yaml", ".json", ".txt", ".xml"}
CSRF_TOKEN = secrets.token_urlsafe(24)   # nový při každém startu; vkládá se do stránky


def norm_id(num: str, suffix: str = "") -> str:
    return f"K{int(num):04d}{suffix}"


def ids_in(text: str) -> list[str]:
    seen: dict[str, None] = {}
    for m in ID_RE.finditer(text):
        seen[norm_id(m.group(1), m.group(2))] = None
    return list(seen)


def struct_parent(pid: str) -> str | None:
    """Strukturní rodič ID: Kekule n → n//2, jinak bez poslední přípony."""
    m = re.match(r"^K(\d+)$", pid)
    if m:
        n = int(m.group(1))
        return norm_id(str(n // 2)) if n > 1 else None
    return re.sub(r"-[SCP]\d+$", "", pid)


def depth_under(pid: str, root: str) -> int | None:
    """Kolik kroků je `pid` pod `root` (0 = sám kořen), nebo None, když pod ním není."""
    d, cur = 0, pid
    while cur:
        if cur == root:
            return d
        cur, d = struct_parent(cur), d + 1
    return None


def first_prompt_root(cwd: str, session_id: str) -> str | None:
    """První ID osoby v prvním promptu session (Claude transkript) — záložní kořen větve.

    Čte jen začátek souboru; obsah promptu je data (hledá se v něm jen ID)."""
    if not session_id or not re.match(r"^[\w-]+$", session_id):
        return None
    path = CLAUDE_PROJECTS / re.sub(r"[^\w-]", "-", cwd) / f"{session_id}.jsonl"
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                if i > 200:
                    break
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if o.get("type") != "user":
                    continue
                c = (o.get("message") or {}).get("content")
                text = c if isinstance(c, str) else " ".join(x.get("text", "") for x in c or [] if isinstance(x, dict))
                ids = ids_in(text)
                return ids[0] if ids else None
    except OSError:
        return None
    return None


def norm_any(value) -> str | None:
    """`K56`, `56`, `K0056-S1` → kanonické ID."""
    if value is None:
        return None
    s = str(value).strip()
    if s.isdigit():
        return norm_id(s)
    m = ID_RE.match(s)
    return norm_id(m.group(1), m.group(2)) if m else None


# ---------------------------------------------------------------- cache podle mtime

class FileCache:
    def __init__(self):
        self._data: dict[tuple[str, str], tuple[float, int, object]] = {}
        self._lock = threading.Lock()

    def get(self, path: Path, kind: str, parse):
        try:
            st = path.stat()
        except FileNotFoundError:
            return None
        key = (str(path), kind)
        with self._lock:
            hit = self._data.get(key)
            if hit and hit[0] == st.st_mtime and hit[1] == st.st_size:
                return hit[2]
        value = parse(path)
        with self._lock:
            self._data[key] = (st.st_mtime, st.st_size, value)
        return value


CACHE = FileCache()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_yaml(path: Path):
    try:
        return yaml.safe_load(read_text(path))
    except yaml.YAMLError:
        return None


def load_json(path: Path):
    try:
        return json.loads(read_text(path))
    except (json.JSONDecodeError, OSError):
        return None


# ---------------------------------------------------------------- dossier

def split_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    raw, body = text[3:end], text[end + 4:].lstrip("\n")
    try:
        fm = yaml.safe_load(raw)
        if isinstance(fm, dict):
            return fm, body
    except yaml.YAMLError:
        pass
    fm = {}  # tolerantní záloha: key: value po řádcích
    for line in raw.splitlines():
        m = re.match(r"^([^\s:#]+):\s*(.*?)\s*(?:#.*)?$", line)
        if m:
            fm[m.group(1)] = m.group(2) or None
    return fm, body


def sections(body: str) -> dict[str, str]:
    out: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if current is not None:
                out[current] = "\n".join(buf)
            current, buf = line[3:].strip(), []
        elif current is not None:
            buf.append(line)
    if current is not None:
        out[current] = "\n".join(buf)
    return out


def section(secs: dict[str, str], prefix: str) -> str:
    for name, text in secs.items():
        if name.lower().startswith(prefix.lower()):
            return text
    return ""


def first_year(text: str) -> int | None:
    m = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", text)
    return int(m.group(1)) if m else None


# Závora (docs/metodika/workflow-sessions.md, oddíl „Závora“): pevné odrážky `- **klíč:** hodnota`
ZAVORA_KEYS = {"kde": "kde", "proč": "proc", "prohledáno": "prohledano", "co by": "prolomit", "obtížnost": "obtiznost_text",
               "datum": "datum"}
ZAVORA_TYPES = [("nezachov", "matriky nezachovány"), ("nedigital", "nedigitalizováno"), ("nenalez", "nenalezeno"),
                ("nečiteln", "nečitelné"), ("totožnost", "nejistá totožnost"), ("mimo dosah", "mimo dosah"),
                ("rozpočet", "rozpočet/kontext"), ("nezkoum", "nezkoumáno")]
ZAVORA_CHANCES = ["prakticky žádná", "žádná", "malá", "střední", "vysoká"]   # vzestupně
ZAVORA_CHANCE_RE = re.compile(r"(prakticky žádná|žádná|vysoká|střední|malá)", re.I)


def parse_zavora(text: str) -> dict | None:
    if not text.strip():
        return None
    z: dict = {}
    key = None
    for ln in text.splitlines():
        m = re.match(r"^\s*[-*]\s+\*\*([^*:]+):?\*\*:?\s*(.*)$", ln)
        if m:
            label = m.group(1).strip().lower()
            key = next((v for k, v in ZAVORA_KEYS.items() if label.startswith(k)), None)
            if key:
                z[key] = m.group(2).strip()
            continue
        if key and ln.startswith((" ", "\t")) and ln.strip():
            z[key] += " " + ln.strip()
        elif not ln.strip():
            key = None
    proc = z.get("proc", "").lower()
    # typ = klíčová slova podle pořadí v textu („rozpočet/kontext + nedigitalizováno“ → oba, první je hlavní)
    hits = sorted((proc.find(k), t) for k, t in ZAVORA_TYPES if k in proc)
    z["typy"] = list(dict.fromkeys(t for _, t in hits)) or (["jiné"] if proc else ["neuvedeno"])
    z["typ"] = z["typy"][0]
    # šance = nejlepší z uvedených cest („křest — šance vysoká; sňatek — šance malá“ → vysoká)
    chances = [c.lower() for c in ZAVORA_CHANCE_RE.findall(z.get("prolomit", ""))]
    z["sance"] = max(chances, key=ZAVORA_CHANCES.index) if chances else None
    br = re.findall(r"prolomeno\s+(\d{4}-\d{2}-\d{2})", text, re.I)
    z["prolomeno"] = br[-1] if br else None
    m = cl.OBTIZNOST_RE.search(text)
    z["obtiznost"] = m.group(1).lower() if m else None
    z["nehledano"] = not cl.zavora_valid(text)
    return z


def parse_dossier(path: Path) -> dict:
    text = read_text(path)
    fm, body = split_front_matter(text)
    pid = norm_any(fm.get("id")) or norm_any(fm.get("kekule"))
    if not pid:
        m = HINT_ID_RE.match(path.name)
        pid = m.group(1) if m else path.stem
    name, rel = "", ""
    lines = [ln for ln in body.splitlines()]
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            name = re.sub(r"\s*\((?:K[\w-]+)\)\s*$", "", ln[2:].strip())
            for nxt in lines[i + 1:i + 4]:
                if nxt.strip().startswith("*") and not nxt.strip().startswith("**"):
                    rel = nxt.strip().strip("*").strip()
                    break
                if nxt.strip():
                    break
            break
    secs = sections(body)

    marks = cl.parse_marks(section(secs, "Checklist"))

    docs = {"open": 0, "done": 0, "na": 0}
    for m in re.finditer(r"^\s*- \[(.)\]", section(secs, "Doklady k dohledání"), re.M):
        docs[{"x": "done", "-": "na"}.get(m.group(1), "open")] += 1

    deferred = len(re.findall(r"^\s*- ", section(secs, "Odloženo"), re.M))
    log_n = len(re.findall(r"^\s*- \d{4}-", section(secs, "Log hledání"), re.M))

    birth = death = None
    for name_sec, txt in secs.items():
        if name_sec.lower().startswith("nápověd"):
            m = re.search(r"\*\*narození:\*\*([^\n]*)", txt)
            birth = birth or (first_year(m.group(1)) if m else None)
            m = re.search(r"\*\*úmrtí:\*\*([^\n]*)", txt)
            death = death or (first_year(m.group(1)) if m else None)

    stav = str(fm.get("stav") or "").strip() or None
    return {
        "id": pid, "name": name, "rel": rel, "stav": stav,
        "původ": fm.get("původ"), "gramps_id": fm.get("gramps_id"),
        "myheritage": fm.get("myheritage"),
        "marks": marks, "has_zavora": cl.zavora_valid(section(secs, "Závora")), "docs": docs, "deferred": deferred, "log": log_n,
        "birth": birth, "death": death,
        # `kontext: chybí` (tools/research/kontext_flags.py) + zda má dossier vyplněnou sekci Kontext
        "kontext_flag": str(fm.get("kontext") or "").strip() == "chybí",
        "has_kontext": bool(section(secs, "Kontext").strip()),
        "zavora": parse_zavora(section(secs, "Závora")),
    }


# ---------------------------------------------------------------- checklist (fáze I)

class GrampsFacts:
    """Údaje osob z Gramps pro checklist (tools/research/gramps_facts.py); cache v paměti, Gramps jen čte."""

    def __init__(self, ttl: int = 300):
        self.ttl, self.at, self.data, self.error = ttl, 0.0, {}, None
        self.lock = threading.Lock()

    def get(self) -> dict:
        with self.lock:
            if time.time() - self.at < self.ttl:
                return self.data
            self.at = time.time()
            try:
                import gramps_facts
                self.data, self.error = gramps_facts.load(), None
            except Exception as e:  # noqa: BLE001 — Gramps neběží: checklist jen z dossierů
                self.error = f"{type(e).__name__}: {e}"[:300]
                self.at = time.time() - self.ttl + 60
            return self.data


def person_checklist(d: dict, gf: dict, root_birth: int | None) -> list:
    g = gf.get(d["id"]) or cl.Facts()
    f = cl.Facts(**{k: getattr(g, k) for k in g.__dataclass_fields__})
    f.birth = f.birth or d.get("birth")
    f.death = f.death or d.get("death")
    if f.male is None and d.get("sex") in ("M", "F"):
        f.male = d["sex"] == "M"
    f = cl.finish(f, d["id"], root_birth)
    return cl.evaluate(f, d.get("marks") or {}), f


# ---------------------------------------------------------------- todo seznamy

def parse_todo(path: Path) -> dict:
    text = read_text(path)
    clean = re.sub(r"^```.*?^```[^\n]*$", "", text, flags=re.S | re.M)
    title = next((ln[2:].strip() for ln in clean.splitlines() if ln.startswith("# ")), path.stem)
    entries = []
    blocks = re.split(r"^## ", clean, flags=re.M)
    if len(blocks) > 1:
        for block in blocks[1:]:
            head, _, rest = block.partition("\n")
            body = rest.split("\n---", 1)[0].strip()
            m = re.search(r"^\s*- (?:\*\*)?stav(?:\*\*)?:\s*(.+)$", body, re.M | re.I)
            state = m.group(1).strip() if m else None
            entries.append({
                "title": head.strip(), "text": f"## {head.strip()}\n{body}", "state": state,
                "open": state is None or not state.lower().startswith(TODO_CLOSED),
                "ids": ids_in(block),
            })
    else:
        for m in re.finditer(r"^- (\d{4}-\d\d-\d\d.*)$", clean, re.M):
            line = m.group(1)
            parts = [p.strip() for p in line.split("|")]
            entries.append({
                "title": " | ".join(parts[2:4]) if len(parts) > 3 else line[:120],
                "text": "- " + line, "state": None, "open": False, "ids": ids_in(line),
            })
    return {"file": path.name, "title": title, "entries": entries,
            "kind": "sections" if len(blocks) > 1 else "lines"}


# ---------------------------------------------------------------- strom

class Tree:
    def __init__(self, root: Path, gramps_url: str):
        self.root = root
        self.name = root.name
        self.gramps_url = gramps_url.rstrip("/")
        self.links = gramps_links.Links(WORKBENCH)   # propojení větví z Gramps (jen čtení, cache v paměti)
        self.facts = GrampsFacts()                    # údaje osob z Gramps pro checklist
        self._herdr = (0.0, [])
        self._herdr_lock = threading.Lock()
        self._prompt_roots: dict[tuple[str, str], str | None] = {}

    # --- výčet souborů (levný: jen stat)
    def files(self) -> dict[str, list[Path]]:
        r = self.root
        def ls(d: Path, pattern: str) -> list[Path]:
            return sorted(d.glob(pattern)) if d.is_dir() else []
        source_dirs = [d for d in ls(r / "sources", "*") if d.is_dir()]
        return {
            "people": [p for p in ls(r / "research/people", "*.md") if p.name != "README.md"],
            "people_json": [p for p in (r / "research/people/manual.json", r / "research/people/ids.json") if p.exists()],
            "hints": ls(r / "research/hints", "*.md"),
            "patches": ls(r / "patches", "P-*.yml") + ls(r / "patches", "P-*.yaml"),
            "todos": ls(r / "research", "todo-*.md"),
            "research": [p for p in (r / "research/log.md", r / "research/doklady.md", r / "research/vetve.yml") if p.exists()],
            "sidecars": [y for d in source_dirs for y in sorted(d.glob("*.yml"))],
            "source_dirs": source_dirs,
            "kontroly": kontroly.files(r),
            "pribehy": [p for p in ls(r / "research/pribehy", "*.md") if p.name != "README.md"],
        }

    def version(self, files: dict[str, list[Path]], sessions: list[dict]) -> str:
        h = hashlib.sha1()
        for group in files.values():
            for p in group:
                try:
                    st = p.stat()
                except FileNotFoundError:
                    continue
                h.update(f"{p}:{st.st_mtime_ns}:{st.st_size}\n".encode())
        h.update(json.dumps(sessions, sort_keys=True).encode())
        h.update(json.dumps(self.links.get(), sort_keys=True).encode())
        h.update(str(self.facts.at if not self.facts.error else 0).encode())
        return h.hexdigest()[:16]

    # --- herdr session
    def sessions(self) -> list[dict]:
        with self._herdr_lock:
            ts, cached = self._herdr
            if time.time() - ts < 3:
                return cached
            out = []
            try:
                res = subprocess.run(["herdr", "agent", "list"], capture_output=True, text=True, timeout=3)
                agents = json.loads(res.stdout).get("result", {}).get("agents", [])
                config = self.branch_config()
                for a in agents:
                    name = a.get("name") or ""
                    cwd = a.get("cwd") or ""
                    if not (cwd.startswith(str(WORKBENCH)) or cwd.startswith(str(self.root))):
                        continue
                    base = {"name": name, "status": a.get("agent_status"),
                            "title": a.get("terminal_title_stripped") or ""}
                    if SESSION_NAME_RE.match(name):
                        out.append({"id": name.upper(), "kind": "osoba", **base})
                    elif BRANCH_NAME_RE.match(name):
                        root, src = config.get(name), "research/vetve.yml"
                        if not root:
                            sid = str((a.get("agent_session") or {}).get("value") or "")
                            key = (cwd, sid)
                            if key not in self._prompt_roots:
                                self._prompt_roots[key] = first_prompt_root(cwd, sid)
                            root, src = self._prompt_roots[key], "první prompt"
                        out.append({"id": None, "kind": "vetev", "root": root,
                                    "root_src": src if root else None, **base})
            except (OSError, subprocess.SubprocessError, json.JSONDecodeError, AttributeError):
                out = []
            self._herdr = (time.time(), out)
            return out

    def branch_config(self) -> dict[str, str]:
        """`T/research/vetve.yml`: `vetev-x: <kořen>` nebo `vetev-x: {koren: <ID>}` — přebíjí první prompt."""
        data = CACHE.get(self.root / "research/vetve.yml", "yaml", load_yaml)
        out = {}
        for name, v in (data or {}).items() if isinstance(data, dict) else []:
            root = norm_any(v.get("koren") if isinstance(v, dict) else v)
            if root:
                out[str(name)] = root
        return out

    def session_of(self, pid: str, sessions: list[dict] | None = None, people: dict | None = None) -> dict | None:
        """Vlastní session osoby (k<ID>), jinak session větve s nejbližším kořenem nad ní.

        Větev se osobě přiřadí jen u stavu rozpracováno (people), nebo vždy, když people není dáno."""
        sessions = self.sessions() if sessions is None else sessions
        own = next((s for s in sessions if s["id"] == pid), None)
        if own:
            return own
        if people is not None and (people.get(pid) or {}).get("stav") != "rozpracováno":
            return None
        best = None
        for s in sessions:
            if s.get("kind") == "vetev" and s.get("root"):
                d = depth_under(pid, s["root"])
                if d is not None and (best is None or d < best[0]):
                    best = (d, s)
        return best[1] if best else None

    # --- souhrn
    def people(self, files) -> dict[str, dict]:
        people: dict[str, dict] = {}
        for p in files["people"]:
            d = CACHE.get(p, "dossier", parse_dossier)
            if not d or not ID_FULL_RE.match(d["id"]):
                continue
            d = dict(d, file=str(p.relative_to(self.root)))
            prev = people.get(d["id"])
            if prev is None or p.stat().st_mtime > (self.root / prev["file"]).stat().st_mtime:
                people[d["id"]] = d
        manual = CACHE.get(self.root / "research/people/manual.json", "json", load_json) or {}
        for pid, m in manual.items():
            pid = norm_any(pid)
            if not pid or not isinstance(m, dict):
                continue
            if pid in people:
                people[pid].setdefault("sex", m.get("sex"))
                if not people[pid].get("birth") and isinstance(m.get("birth"), int):
                    people[pid]["birth"] = m["birth"]
            else:
                people[pid] = {"id": pid, "name": m.get("name") or "", "rel": m.get("rel") or "",
                               "stav": None, "file": None, "birth": m.get("birth"), "death": None,
                               "marks": {}, "docs": None, "deferred": 0, "log": 0,
                               "sex": m.get("sex"), "manual_only": True}
        return people

    def hints(self, files) -> dict[str, list[Path]]:
        out: dict[str, list[Path]] = {}
        for p in files["hints"]:
            m = HINT_ID_RE.match(p.name)
            if m:
                out.setdefault(m.group(1), []).append(p)
        return out

    def patches(self, files) -> list[dict]:
        out = []
        for p in files["patches"]:
            data = CACHE.get(p, "yaml", load_yaml)
            m = re.match(r"^P-(K\d+(?:-[SCP]\d+)*)-(\d+)\.ya?ml$", p.name)
            pid = m.group(1) if m else norm_any((data or {}).get("person"))
            data = data if isinstance(data, dict) else {}
            out.append({"file": p.name, "id": pid, "status": str(data.get("status") or "?"),
                        "summary": data.get("summary") or "", "mtime": p.stat().st_mtime})
        return out

    def todos(self, files) -> list[dict]:
        return [CACHE.get(p, "todo", parse_todo) for p in files["todos"]]

    def log_tail(self, n: int = 40) -> list[str]:
        p = self.root / "research/log.md"
        lines = CACHE.get(p, "loglines", lambda q: [ln[2:] for ln in read_text(q).splitlines()
                                                     if re.match(r"^- \d{4}-", ln)]) or []
        return list(reversed(lines[-n:]))

    def doklady_summary(self) -> dict | None:
        p = self.root / "research/doklady.md"
        def parse(q: Path):
            t = read_text(q)
            return {"open": len(re.findall(r"^- \[ \]", t, re.M)),
                    "done": len(re.findall(r"^- \[x\]", t, re.M))}
        return CACHE.get(p, "doklady", parse)

    def state(self) -> dict:
        files = self.files()
        sessions = self.sessions()
        version = self.version(files, sessions)
        people = self.people(files)
        hints = self.hints(files)
        patches = self.patches(files)
        todos = self.todos(files)
        src_ids = {d.name for d in files["source_dirs"]}
        stories = {p.stem for p in files["pribehy"]}
        checks = self.kontroly(files)
        events = self.events(files)

        for pid, d in people.items():
            d["hints"] = len(hints.get(pid, []))
            d["patches"] = {}
            d["todo"] = 0
            d["todo_open"] = 0
            d["sources"] = pid in src_ids
            d["story"] = pid in stories
            d["kontext_missing"] = [x for x, ok in (("Kontext", d.get("has_kontext")), ("příběh", d["story"])) if not ok] \
                if d.get("kontext_flag") else []
        for pt in patches:
            if pt["id"] in people:
                st = people[pt["id"]]["patches"]
                st[pt["status"]] = st.get(pt["status"], 0) + 1
        for t in todos:
            for e in t["entries"]:
                for pid in e["ids"]:
                    if pid in people:
                        people[pid]["todo"] += 1
                        people[pid]["todo_open"] += int(e["open"])
        # osoby jen s nápovědou / patchem / kontrolou bez dossieru — ať jsou ve stromu vidět
        for pid in list(hints) + [p["id"] for p in patches if p["id"]] + [k["osoba"] for k in checks if k["osoba"]] + sorted(stories):
            if pid not in people and ID_FULL_RE.match(pid):
                people[pid] = {"id": pid, "name": "", "rel": "", "stav": None, "file": None,
                               "hints": len(hints.get(pid, [])), "patches": {}, "todo": 0, "todo_open": 0,
                               "marks": None, "docs": None, "sources": pid in src_ids, "orphan": True}

        for pid, d in people.items():
            ses = self.session_of(pid, sessions, people)
            d["branch"] = ses["name"] if ses and ses.get("kind") == "vetev" else None
            d["branch_guess"] = False
        # větev bez osoby „rozpracováno“ (session je mezi osobami) → odznak na naposledy měněném dossieru větve
        busy = {d["branch"] for d in people.values() if d.get("branch")}
        for s in sessions:
            if s.get("kind") != "vetev" or not s.get("root") or s["name"] in busy:
                continue
            best = None
            for pid, d in people.items():
                if not d.get("file") or self.session_of(pid, sessions) is not s:
                    continue
                mt = (self.root / d["file"]).stat().st_mtime
                if best is None or mt > best[0]:
                    best = (mt, pid)
            if best:
                people[best[1]]["branch"] = s["name"]
                people[best[1]]["branch_guess"] = True
        gf = self.facts.get()
        root_birth = (gf.get("K0001") or cl.Facts()).birth or 1985
        for pid, d in people.items():
            mine = [k for k in checks if k["osoba"] == pid and k["stav"] == kontroly.OPEN]
            d["kontroly"] = {"open": len(mine), "blocking": sum(k["blokuje"] for k in mine)}
            evs = events.get(pid, [])
            d["events"] = {"total": len(evs), "single": sum(e["sources"] == 1 for e in evs),
                           "none": sum(e["sources"] == 0 for e in evs)}
            self.apply_checklist(d, gf, root_birth)

        queue = fronta.build(people)
        counts: dict[str, int] = {}
        for d in people.values():
            k = d.get("stav") or "bez dossieru"
            counts[k] = counts.get(k, 0) + 1

        return {
            "version": version,
            "tree": self.name,
            "gramps_url": self.gramps_url,
            "people": people,
            "sessions": sessions,
            "patches": sorted(patches, key=lambda p: -p["mtime"]),
            "todos": [{"file": t["file"], "title": t["title"], "kind": t["kind"],
                       "entries": len(t["entries"]), "open": sum(e["open"] for e in t["entries"])}
                      for t in todos],
            "log": self.log_tail(),
            "doklady": self.doklady_summary(),
            "kontroly": checks,
            "fronta": queue,
            "counts": counts,
            "links": self.links.get(),
            "states": STATES,
        }

    def kontroly(self, files) -> list[dict]:
        return kontroly.load(files["kontroly"], CACHE, load_yaml, self.root, norm_any)

    @staticmethod
    def apply_checklist(d: dict, gf: dict, root_birth: int | None) -> None:
        """Souhrn checklistu + stav `uzavřeno` (fáze I hotová, nikdo na osobě nepracuje, žádný patch ani blokující kontrola nečeká)."""
        if d.get("marks") is None:
            d["checklist"] = None
            return
        entries, facts = person_checklist(d, gf, root_birth)
        d["checklist"] = cl.summary(entries)
        d["faze1"] = cl.phase1_done(entries, d.get("has_zavora", False))
        d["open_items"] = [e.item.key for e in entries
                           if e.item.tier == cl.ZAKLADNI and not cl.closed(e, d.get("has_zavora", False))]
        d["parents_in_tree"] = all(facts.parents)
        d["birth_est"] = facts.birth if facts.birth_est else None
        waiting = any(k in PATCH_WAITING for k in (d.get("patches") or {}))
        d["stav_dossier"] = d.get("stav")
        blocked = bool((d.get("kontroly") or {}).get("blocking"))     # otevřená blokující kontrola
        if d["faze1"] and d.get("stav") != "rozpracováno" and not waiting and not blocked:
            d["stav"] = "uzavřeno"
        d.pop("marks", None)

    def events(self, files) -> dict[str, list[dict]]:
        return evidence.events(files["patches"], CACHE, load_yaml, self.root, norm_any)

    def notify_session(self, pid: str | None, text: str) -> str | None:
        """Pošle zprávu běžící session osoby (herdr). → jméno session, nebo None."""
        if not pid:
            return None
        self._herdr = (0.0, [])
        ses = self.session_of(pid.upper())
        if not ses:
            return None
        try:
            subprocess.run(["herdr", "agent", "prompt", ses["name"], text], capture_output=True, timeout=10, check=True)
        except (OSError, subprocess.SubprocessError):
            return None
        return ses["name"]

    # --- mapa
    def houses(self) -> dict[str, dict]:
        houses: dict[str, dict] = {}
        for csvp in sorted((WORKBENCH / "mcp/czech-archives/gazetteer").glob("*-cp.csv")):
            for obec, cps in (CACHE.get(csvp, "houses", mapdata.load_houses) or {}).items():
                houses.setdefault(obec, {}).update(cps)
        return houses

    def residences(self, files, houses=None) -> list[dict]:
        res = mapdata.residences(files["patches"], CACHE, load_yaml, self.root)
        return mapdata.resolve(res, houses if houses is not None else self.houses())

    def map(self) -> dict:
        files = self.files()
        people = self.people(files)
        houses = self.houses()
        places: dict[str, list] = {}
        regions = []
        for d in sorted(p for p in (WORKBENCH / "docs/mistopis").glob("*") if p.is_dir()):
            readme = d / "README.md"
            title = d.name
            if readme.exists():
                head = next((ln[2:] for ln in read_text(readme).splitlines() if ln.startswith("# ")), d.name)
                title = re.split(r"\s+[—–-]\s+", head)[0].strip()
            pl = CACHE.get(d / "obce.md", "places", mapdata.load_places) if (d / "obce.md").exists() else None
            places.update(pl or {})
            regions.append({"id": d.name, "title": title, "places": sorted(pl) if pl else []})
        vrstvy = CACHE.get(WORKBENCH / "tools/mapy/vrstvy.yml", "yaml", load_yaml)
        res = self.residences(files, houses)
        for r in res:
            r["name"] = (people.get(r["id"]) or {}).get("name") or ""
        return {"residences": res, "houses": houses, "places": places, "regions": regions,
                "layers": mapdata.layers(WORKBENCH / "cache/mapy", vrstvy)}

    # --- detail osoby
    def person(self, pid: str) -> dict | None:
        files = self.files()
        people = self.people(files)
        d = people.get(pid, {"id": pid, "name": "", "file": None})
        out = dict(d)
        out["dossier"] = read_text(self.root / d["file"]) if d.get("file") else None
        secs = sections(split_front_matter(out["dossier"])[1]) if out["dossier"] else {}
        out["kontext"] = section(secs, "Kontext").strip()
        out["zavora_text"] = section(secs, "Závora").strip()
        story = self.root / "research/pribehy" / f"{pid}.md"
        out["story"] = {"file": str(story.relative_to(self.root)), "text": read_text(story),
                        "mtime": story.stat().st_mtime} if story.is_file() else None
        out["hints"] = [{"file": str(p.relative_to(self.root)), "text": read_text(p)}
                        for p in self.hints(files).get(pid, [])]
        out["patches"] = []
        for pt in self.patches(files):
            if pt["id"] == pid:
                p = self.root / "patches" / pt["file"]
                out["patches"].append(dict(pt, path=str(p.relative_to(self.root)), text=read_text(p)))
        out["todos"] = []
        for t in self.todos(files):
            for e in t["entries"]:
                if pid in e["ids"]:
                    out["todos"].append({"list": t["file"], "list_title": t["title"], **e})
        out["sources"] = self.sources(pid, files)
        gid = d.get("gramps_id")
        out["gramps"] = f"{self.gramps_url}/person/{gid}" if gid else None
        out["abs_path"] = str(self.root / d["file"]) if d.get("file") else None
        out["session"] = self.session_of(pid, people=people)
        out["residences"] = [r for r in self.residences(files) if r["id"] == pid]
        out["events"] = self.events(files).get(pid, [])
        out["kontroly"] = [k for k in self.kontroly(files) if k["osoba"] == pid]
        gf = self.facts.get()
        if d.get("marks") is not None:
            entries, _ = person_checklist(d, gf, (gf.get("K0001") or cl.Facts()).birth or 1985)
            out["checklist_items"] = [{"key": e.item.key, "label": e.item.label, "tier": e.item.tier,
                                       "state": e.state, "note": e.note, "auto": e.auto, "hint": e.item.hint,
                                       "closed": cl.closed(e, d.get("has_zavora", False))}
                                      for e in entries]
        st = self.state()["people"].get(pid) or {}
        for k in ("stav", "stav_dossier", "checklist", "faze1", "birth_est"):
            if k in st:
                out[k] = st[k]
        out.pop("marks", None)
        return out

    def sources(self, pid: str, files) -> dict:
        own_dir = self.root / "sources" / pid
        sidecars, used = [], set()
        for y in files["sidecars"]:
            data = CACHE.get(y, "yaml", load_yaml)
            if not isinstance(data, dict):
                continue
            persons = {norm_any(x) for x in (data.get("persons") or []) if norm_any(x)}
            own = y.parent == own_dir
            if not own and pid not in persons:
                continue
            img = None
            if data.get("file") and (y.parent / str(data["file"])).exists():
                img = str((y.parent / str(data["file"])).relative_to(self.root))
            else:
                for ext in (".jpg", ".jpeg", ".png"):
                    if y.with_suffix(ext).exists():
                        img = str(y.with_suffix(ext).relative_to(self.root))
                        break
            tr = None
            if data.get("transcription") and (y.parent / str(data["transcription"])).exists():
                tr = str((y.parent / str(data["transcription"])).relative_to(self.root))
            if img:
                used.add(img)
            sidecars.append({
                "path": str(y.relative_to(self.root)), "own": own,
                "type": data.get("type"), "archive": data.get("archive"), "volume": data.get("volume"),
                "document": data.get("document"), "entry": data.get("entry"), "folio": data.get("folio"),
                "url": data.get("url"), "volume_url": data.get("volume_url"), "text": data.get("text"),
                "confidence": data.get("confidence"), "image": img, "transcription": tr,
                "persons": sorted(persons),
            })
        sidecars.sort(key=lambda s: (not s["own"], s["path"]))
        other_images, texts = [], []
        if own_dir.is_dir():
            for f in sorted(own_dir.iterdir()):
                rel = str(f.relative_to(self.root))
                if f.suffix.lower() in IMAGE_EXT and ".crop-" not in f.name and rel not in used:
                    other_images.append(rel)
                elif f.suffix.lower() == ".md":
                    texts.append(rel)
        trans_dir = self.root / "transcriptions"
        if trans_dir.is_dir():
            texts += [str(f.relative_to(self.root)) for f in sorted(trans_dir.glob(f"{pid}-*.md"))]
        return {"dir": str(own_dir.relative_to(self.root)) if own_dir.is_dir() else None,
                "sidecars": sidecars, "images": other_images, "texts": texts}


# ---------------------------------------------------------------- HTTP

class Handler(BaseHTTPRequestHandler):
    tree: Tree

    def log_message(self, fmt, *args):  # tiché
        pass

    def send_json(self, obj, status=HTTPStatus.OK):
        body = json.dumps(obj, ensure_ascii=False, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path, ctype: str | None = None, cache: str = "no-cache"):
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", ctype or mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", cache)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        path = unquote(url.path)
        q = parse_qs(url.query)
        try:
            if path in ("/", "/index.html"):
                html = read_text(STATIC / "index.html").replace("__CSRF_TOKEN__", CSRF_TOKEN).encode()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(html)
                return
            if path.startswith("/static/"):
                f = (STATIC / path[len("/static/"):]).resolve()
                if f.is_file() and f.is_relative_to(STATIC):
                    return self.send_file(f)
                return self.send_error(HTTPStatus.NOT_FOUND)
            if path == "/api/state":
                st = self.tree.state()
                if q.get("v", [None])[0] == st["version"]:
                    return self.send_json({"unchanged": True, "version": st["version"]})
                return self.send_json(st)
            if path.startswith("/api/person/"):
                pid = path[len("/api/person/"):]
                if not ID_FULL_RE.match(pid):
                    return self.send_error(HTTPStatus.BAD_REQUEST)
                return self.send_json(self.tree.person(pid))
            if path == "/api/map":
                return self.send_json(self.tree.map())
            m = re.match(r"^/tiles/([\w-]+)/([\w-]+)/(\d+)/(\d+)/(\d+)\.(webp|png|jpg)$", path)
            if m:
                f = WORKBENCH / "cache/mapy" / m[1] / m[2] / "xyz" / m[3] / m[4] / f"{m[5]}.{m[6]}"
                if f.is_file():
                    return self.send_file(f, cache="max-age=86400")
                self.send_response(HTTPStatus.NO_CONTENT)  # mimo stažené území — prázdno, ne chyba
                self.end_headers()
                return
            if path == "/api/file":
                rel = q.get("p", [""])[0]
                f = (self.tree.root / rel).resolve()
                if not f.is_file() or not f.is_relative_to(self.tree.root.resolve()):
                    return self.send_error(HTTPStatus.NOT_FOUND)
                ext = f.suffix.lower()
                if ext in IMAGE_EXT or ext == ".pdf":
                    return self.send_file(f)
                if ext in TEXT_EXT:
                    return self.send_file(f, "text/plain; charset=utf-8")
                return self.send_error(HTTPStatus.FORBIDDEN)
            return self.send_error(HTTPStatus.NOT_FOUND)
        except (BrokenPipeError, ConnectionResetError):
            pass


    def do_POST(self):
        """Jediný zápis: rozhodnutí kontroly. Jen z 127.0.0.1, s tokenem ze stránky a stejným původem."""
        path = unquote(urlparse(self.path).path)
        try:
            m = re.match(r"^/api/kontrola/((?:K\d+(?:-[SCP]\d+)*|G)-\d+)$", path)
            if not m:
                return self.send_error(HTTPStatus.NOT_FOUND)
            if self.client_address[0] != "127.0.0.1":
                return self.send_json({"error": "jen z 127.0.0.1"}, HTTPStatus.FORBIDDEN)
            if not secrets.compare_digest(self.headers.get("X-Dashboard-Token", ""), CSRF_TOKEN):
                return self.send_json({"error": "neplatný token — obnov stránku"}, HTTPStatus.FORBIDDEN)
            port = self.server.server_address[1]
            allowed = {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}
            origin = self.headers.get("Origin")
            if (origin and origin not in allowed) or self.headers.get("Host") not in {a[7:] for a in allowed}:
                return self.send_json({"error": "cizí původ požadavku"}, HTTPStatus.FORBIDDEN)
            if not (self.headers.get("Content-Type") or "").startswith("application/json"):
                return self.send_json({"error": "očekávám JSON"}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
            n = int(self.headers.get("Content-Length") or 0)
            if n > 20000:
                return self.send_json({"error": "příliš velké"}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
            except json.JSONDecodeError:
                return self.send_json({"error": "neplatný JSON"}, HTTPStatus.BAD_REQUEST)
            if not isinstance(body, dict):
                return self.send_json({"error": "neplatný JSON"}, HTTPStatus.BAD_REQUEST)
            try:
                res = kontroly.decide(self.tree.root, m.group(1), str(body.get("volba") or ""),
                                      str(body.get("poznamka") or ""))
            except kontroly.DecisionError as e:
                return self.send_json({"error": str(e)}, HTTPStatus.CONFLICT)
            volba = res["rozhodnuti"]["volba"].replace("\n", " ")
            res["session"] = self.tree.notify_session(norm_any(res["osoba"]),
                                                      f"kontrola {res['id']}: rozhodnuto — {volba[:300]}")
            return self.send_json(res)
        except (BrokenPipeError, ConnectionResetError):
            pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tree", default="berescak", help="název stromu v ../genealogy-trees/")
    ap.add_argument("--tree-dir", help="cesta ke stromu (místo --tree)")
    ap.add_argument("--port", type=int, default=5056)
    ap.add_argument("--gramps-url", default="http://localhost:5055")
    args = ap.parse_args()
    root = Path(args.tree_dir).resolve() if args.tree_dir else (WORKBENCH.parent / "genealogy-trees" / args.tree)
    if not root.is_dir():
        raise SystemExit(f"strom nenalezen: {root}")
    Handler.tree = Tree(root, args.gramps_url)
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"dashboard: http://127.0.0.1:{args.port}/  (strom {root})", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
