"""Minimální klient Gramps Web API (bez závislostí). Přístupy z infra/gramps-web/.env.

Účty: GRAMPSWEB_ADMIN_* = strom berescak (master), GRAMPSWEB_REF_* = myheritage-ref.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[2] / "infra" / "gramps-web" / ".env"
TOKEN_CACHE = ENV.parent / ".token-cache.json"   # gitignored (.env* ne — viz .gitignore)


def env() -> dict[str, str]:
    out = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
    return out


class GrampsWeb:
    def __init__(self, ref: bool = False):
        e = env()
        self.base = f"http://127.0.0.1:{e.get('GRAMPSWEB_PORT', '5055')}/api"
        user = e["GRAMPSWEB_REF_USER" if ref else "GRAMPSWEB_ADMIN_USER"]
        pwd = e["GRAMPSWEB_REF_PASSWORD" if ref else "GRAMPSWEB_ADMIN_PASSWORD"]
        self.token = self._token(user, pwd)

    def _token(self, user: str, pwd: str) -> str:
        """Token z cache (platí ~15 min), jinak přihlášení; login má rate limit → při 429 počkat."""
        cache = json.loads(TOKEN_CACHE.read_text()) if TOKEN_CACHE.exists() else {}
        hit = cache.get(user)
        if hit and hit["at"] > time.time() - 600:
            return hit["token"]
        for attempt in range(6):
            try:
                tok = self._call("POST", "/token/", {"username": user, "password": pwd}, auth=False)["access_token"]
                break
            except RuntimeError as e:
                if "HTTP 429" not in str(e) or attempt == 5:
                    raise
                time.sleep(10 * (attempt + 1))
        cache[user] = {"token": tok, "at": time.time()}
        TOKEN_CACHE.write_text(json.dumps(cache))
        TOKEN_CACHE.chmod(0o600)
        return tok

    def _call(self, method: str, path: str, body=None, auth: bool = True, raw: bytes | None = None,
              mime: str = "application/json"):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        req = urllib.request.Request(self.base + path, data=data, method=method)
        req.add_header("Content-Type", mime)
        if auth:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"{method} {path}: HTTP {e.code} {e.read().decode(errors='replace')}") from None
        return json.loads(raw) if raw else None

    def get(self, path: str):
        return self._call("GET", path)

    def post(self, path: str, body):
        return self._call("POST", path, body)

    def upload(self, path: str, data: bytes, mime: str):
        return self._call("POST", path, raw=data, mime=mime)

    def delete(self, path: str):
        return self._call("DELETE", path)

    def put(self, path: str, body):
        return self._call("PUT", path, body)

    def person_by_gramps_id(self, gid: str) -> dict | None:
        try:
            res = self.get(f"/people/?gramps_id={urllib.request.quote(gid)}")
        except RuntimeError as e:
            if "HTTP 404" in str(e):
                return None
            raise
        return res[0] if res else None
