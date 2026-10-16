#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6"]
# ///
"""Workbench dashboard — živý přehled stavu výzkumu nad stromem.

Čte **živé soubory stromu** při každém požadavku (jen paměťová cache podle mtime), nic negeneruje,
nic nezapisuje. Poslouchá jen na 127.0.0.1.

    uv run tools/dashboard/server.py [--tree berescak] [--port 5056]

API:
    GET /api/state[?v=<verze>]   souhrn (osoby, session, patche, todo, log); při stejné verzi {"unchanged": true}
    GET /api/person/<ID>         vše k osobě (dossier, nápovědy, patche, todo, prameny)
    GET /api/file?p=<cesta>      soubor stromu (snímky, přepisy) — jen čtení, jen uvnitř stromu
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import subprocess
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import yaml

WORKBENCH = Path(__file__).resolve().parents[2]
STATIC = Path(__file__).resolve().parent / "static"

# ID osoby: Kekule K%04d + přípony -S<n> (manžel/ka), -C<n> (dítě), -P1/-P2 (otec/matka)
ID_RE = re.compile(r"\bK(\d{1,5})((?:-[SCP]\d+)*)\b")
ID_FULL_RE = re.compile(r"^K\d+(?:-[SCP]\d+)*$")
HINT_ID_RE = re.compile(r"^(K\d+(?:-[SCP]\d+)*)-")
SESSION_NAME_RE = re.compile(r"^k\d+(?:-[scp]\d+)*$")

STATES = ["zmínka", "převzato", "rozpracováno", "pozastaveno", "dokončeno", "zapsáno"]
PATCH_WAITING = {"navrženo", "schváleno"}
TODO_CLOSED = ("nalezeno", "nenalezeno", "zodpovězeno", "neví", "hotovo", "vyřízeno", "uzavřeno")
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".tif", ".tiff"}
TEXT_EXT = {".md", ".yml", ".yaml", ".json", ".txt", ".xml"}


def norm_id(num: str, suffix: str = "") -> str:
    return f"K{int(num):04d}{suffix}"


def ids_in(text: str) -> list[str]:
    seen: dict[str, None] = {}
    for m in ID_RE.finditer(text):
        seen[norm_id(m.group(1), m.group(2))] = None
    return list(seen)


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

    checklist = {"x": 0, "~": 0, "-": 0, "n": 0, " ": 0}
    for m in re.finditer(r"^\s*- \[(.)\]", section(secs, "Checklist"), re.M):
        mark = m.group(1)
        checklist[mark if mark in checklist else " "] += 1

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
        "checklist": checklist, "docs": docs, "deferred": deferred, "log": log_n,
        "birth": birth, "death": death,
    }


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
        self._herdr = (0.0, [])
        self._herdr_lock = threading.Lock()

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
            "research": [p for p in (r / "research/log.md", r / "research/doklady.md") if p.exists()],
            "sidecars": [y for d in source_dirs for y in sorted(d.glob("*.yml"))],
            "source_dirs": source_dirs,
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
                for a in agents:
                    name = a.get("name") or ""
                    cwd = a.get("cwd") or ""
                    if not SESSION_NAME_RE.match(name):
                        continue
                    if not (cwd.startswith(str(WORKBENCH)) or cwd.startswith(str(self.root))):
                        continue
                    out.append({"id": name.upper(), "name": name, "status": a.get("agent_status"),
                                "title": a.get("terminal_title_stripped") or ""})
            except (OSError, subprocess.SubprocessError, json.JSONDecodeError, AttributeError):
                out = []
            self._herdr = (time.time(), out)
            return out

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
                               "checklist": None, "docs": None, "deferred": 0, "log": 0,
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

        for pid, d in people.items():
            d["hints"] = len(hints.get(pid, []))
            d["patches"] = {}
            d["todo"] = 0
            d["todo_open"] = 0
            d["sources"] = pid in src_ids
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
        # osoby jen s nápovědou / patchem bez dossieru — ať jsou ve stromu vidět
        for pid in list(hints) + [p["id"] for p in patches if p["id"]]:
            if pid not in people and ID_FULL_RE.match(pid):
                people[pid] = {"id": pid, "name": "", "rel": "", "stav": None, "file": None,
                               "hints": len(hints.get(pid, [])), "patches": {}, "todo": 0, "todo_open": 0,
                               "checklist": None, "docs": None, "sources": pid in src_ids, "orphan": True}

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
            "counts": counts,
            "states": STATES,
        }

    # --- detail osoby
    def person(self, pid: str) -> dict | None:
        files = self.files()
        people = self.people(files)
        d = people.get(pid, {"id": pid, "name": "", "file": None})
        out = dict(d)
        out["dossier"] = read_text(self.root / d["file"]) if d.get("file") else None
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
        out["session"] = next((s for s in self.sessions() if s["id"] == pid), None)
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

    def send_file(self, path: Path, ctype: str | None = None):
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", ctype or mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        path = unquote(url.path)
        q = parse_qs(url.query)
        try:
            if path in ("/", "/index.html"):
                return self.send_file(STATIC / "index.html", "text/html; charset=utf-8")
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
