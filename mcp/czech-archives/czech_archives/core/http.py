"""HTTP klient s rate limitem (i mezi procesy) a diskovou cache.

Zásady (CLAUDE.md workbenche): stahovat jen na vyžádání, rychlostí člověka, přes cache.
- min. interval mezi požadavky na jeden „klíč“ (archiv) — výchozí 2,5 s, hlídá se zámkem
  v souboru, takže ho dodrží i dvě souběžně běžící session,
- žádné paralelní dotazy (zámek se drží po celou dobu požadavku),
- identifikace User-Agentem,
- JSON odpovědi se cachují na disk s TTL, binární soubory (snímky) natrvalo.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import shutil
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path

USER_AGENT = "genealogy-workbench/0.1 (osobní rodinný výzkum)"
CACHE_DIR = Path(
    os.environ.get(
        "CZECH_ARCHIVES_CACHE",
        Path.home() / ".cache" / "genealogy-workbench" / "czech-archives",
    )
)
# Pojistka proti nechtěnému stažení celé matriky jedním souborem.
MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024


class HttpError(RuntimeError):
    def __init__(self, status: int, url: str, body: str = ""):
        super().__init__(f"HTTP {status} pro {url}: {body[:300]}")
        self.status = status
        self.url = url


class RateLimitedClient:
    def __init__(self, key: str, min_interval: float = 2.5, timeout: float = 60.0):
        self.key = key
        self.min_interval = min_interval
        self.timeout = timeout
        self.cache_dir = CACHE_DIR / key
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock_path = CACHE_DIR / f".ratelimit-{key}"

    # --- rate limit -----------------------------------------------------------------------
    @contextmanager
    def _slot(self):
        """Exkluzivní slot pro jeden požadavek; mezi sloty aspoň min_interval sekund."""
        self._lock_path.touch(exist_ok=True)
        with open(self._lock_path, "r+") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                fh.seek(0)
                raw = fh.read().strip()
                last = float(raw) if raw else 0.0
                wait = last + self.min_interval - time.time()
                if wait > 0:
                    time.sleep(wait)
                yield
            finally:
                fh.seek(0)
                fh.truncate()
                fh.write(str(time.time()))
                fh.flush()
                fcntl.flock(fh, fcntl.LOCK_UN)

    def _request(self, url: str, method: str = "GET", body: dict | None = None,
                 accept: str = "application/json"):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"User-Agent": USER_AGENT, "Accept": accept}
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        return urllib.request.urlopen(req, timeout=self.timeout)

    # --- JSON -----------------------------------------------------------------------------
    def _cache_file(self, url: str, method: str, body: dict | None) -> Path:
        h = hashlib.sha256(
            f"{method} {url} {json.dumps(body, sort_keys=True, ensure_ascii=False)}".encode()
        ).hexdigest()[:24]
        return self.cache_dir / "json" / h[:2] / f"{h}.json"

    def json(self, url: str, method: str = "GET", body: dict | None = None,
             ttl: float = 86400.0, accept: str = "application/json"):
        cf = self._cache_file(url, method, body)
        if ttl > 0 and cf.exists() and time.time() - cf.stat().st_mtime < ttl:
            return json.loads(cf.read_text("utf-8"))
        with self._slot():
            try:
                with self._request(url, method, body, accept) as resp:
                    raw = resp.read()
            except urllib.error.HTTPError as e:
                raise HttpError(e.code, url, e.read().decode("utf-8", "replace")) from None
        data = json.loads(raw.decode("utf-8"))
        cf.parent.mkdir(parents=True, exist_ok=True)
        cf.write_text(json.dumps(data, ensure_ascii=False), "utf-8")
        return data

    def text(self, url: str, ttl: float = 86400.0, accept: str = "text/plain") -> str:
        """Textová odpověď (např. OCR) s cache na disku; `accept` jde do hlavičky tak, jak je."""
        h = hashlib.sha256(f"TEXT {url} {accept}".encode()).hexdigest()[:24]
        cf = self.cache_dir / "text" / h[:2] / f"{h}.txt"
        if ttl > 0 and cf.exists() and time.time() - cf.stat().st_mtime < ttl:
            return cf.read_text("utf-8")
        with self._slot():
            try:
                with self._request(url, accept=accept) as resp:
                    raw = resp.read()
            except urllib.error.HTTPError as e:
                raise HttpError(e.code, url, e.read().decode("utf-8", "replace")) from None
        out = raw.decode("utf-8", "replace")
        cf.parent.mkdir(parents=True, exist_ok=True)
        cf.write_text(out, "utf-8")
        return out

    def head(self, url: str) -> dict:
        with self._slot():
            try:
                with self._request(url, "HEAD", accept="*/*") as resp:
                    return {"status": resp.status, **{k.lower(): v for k, v in resp.headers.items()}}
            except urllib.error.HTTPError as e:
                return {"status": e.code}

    # --- binární soubory ------------------------------------------------------------------
    def download(self, url: str, cache_rel: str, max_bytes: int = MAX_DOWNLOAD_BYTES) -> Path:
        """Stáhne soubor do cache (pokud tam už není) a vrátí cestu v cache."""
        target = self.cache_dir / "files" / cache_rel
        if target.exists() and target.stat().st_size > 0:
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".part")
        with self._slot():
            try:
                with self._request(url, accept="*/*") as resp:
                    length = int(resp.headers.get("Content-Length") or 0)
                    if length and length > max_bytes:
                        raise RuntimeError(
                            f"{url}: {length} B > limit {max_bytes} B — nestahuji")
                    got = 0
                    with open(tmp, "wb") as out:
                        while chunk := resp.read(1 << 16):
                            got += len(chunk)
                            if got > max_bytes:
                                raise RuntimeError(f"{url}: překročen limit {max_bytes} B")
                            out.write(chunk)
            except urllib.error.HTTPError as e:
                tmp.unlink(missing_ok=True)
                raise HttpError(e.code, url) from None
            except BaseException:
                tmp.unlink(missing_ok=True)
                raise
        tmp.replace(target)
        return target


def copy_to(src: Path, dest: Path) -> Path:
    """dest může být adresář (zachová se jméno) nebo cesta k souboru."""
    dest = Path(dest).expanduser()
    if dest.is_dir() or str(dest).endswith(os.sep):
        dest.mkdir(parents=True, exist_ok=True)
        dest = dest / src.name
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    return dest
