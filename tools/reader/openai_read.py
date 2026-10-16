#!/usr/bin/env python3
"""Druhé nezávislé čtení snímku matriky / dokladu přes OpenAI (model s viděním).

Použití:
    openai_read.py read <snímek.jpg> --type N|O|Z|scitani|doklad \
        [--crop x,y,w,h] [--hint "obec, rok, hledaná osoba"] [--model auto|<id>] \
        [--effort low|medium|high] [--max-side 3200] [--detail original|high|auto] \
        [--enhance] --out <soubor.json>
    openai_read.py models          # vypíše kandidáty na vision model a co by zvolil `auto`

Výstup je JSON se strukturovaným čtením podle rubrik (každé pole {raw, value, confidence}),
názvem modelu, parametry a spotřebou. Spotřeba a odhad ceny se připisují do
~/.cache/genealogy-workbench/reader/usage.jsonl (bez klíče).

Klíč: proměnná OPENAI_API_KEY, jinak ~/.config/openai/genealogie.json (pole .api_key.value).
Klíč se nikdy nevypisuje ani neukládá.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

API = "https://api.openai.com/v1"
KEY_FILE = Path.home() / ".config/openai/genealogie.json"
CACHE_DIR = Path.home() / ".cache/genealogy-workbench/reader"
USAGE_LOG = CACHE_DIR / "usage.jsonl"
MODELS_CACHE = CACHE_DIR / "models.json"

# Ceník USD za 1M tokenů (vstup, vstup z cache, výstup). ODHAD — ověřit na
# https://developers.openai.com/api/docs/pricing ; neznámý model → cena se neuvede.
PRICES = {
    "gpt-6.1-sol": (2.00, 0.20, 10.00),
    "gpt-6-sol": (2.00, 0.20, 10.00),
    "gpt-6-luna": (0.10, 0.01, 0.50),
    "gpt-5.5": (5.00, 0.50, 30.00),
    "gpt-5.4": (2.50, 0.25, 15.00),
    "gpt-5.4-mini": (0.75, 0.075, 4.50),
    "gpt-5.2": (1.75, 0.175, 14.00),
    "gpt-5.1": (1.25, 0.125, 10.00),
    "gpt-5": (1.25, 0.125, 10.00),
    "gpt-5-mini": (0.25, 0.025, 2.00),
    "gpt-4.1": (2.00, 0.50, 8.00),
    "gpt-4o": (2.50, 1.25, 10.00),
}


# ---------------------------------------------------------------- klíč a HTTP

def api_key() -> str:
    k = os.environ.get("OPENAI_API_KEY")
    if k:
        return k.strip()
    try:
        return json.loads(KEY_FILE.read_text())["api_key"]["value"].strip()
    except Exception as e:  # nikdy nevypisovat obsah souboru
        sys.exit(f"Chybí API klíč (OPENAI_API_KEY ani {KEY_FILE}): {type(e).__name__}")


def http(method: str, path: str, body: dict | None = None, timeout: int = 600) -> dict:
    req = urllib.request.Request(
        API + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": "Bearer " + api_key(), "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:2000]
        if e.code == 429 and ("insufficient_quota" in detail or "credit_balance" in detail):
            sys.exit("OpenAI: účet nemá kredit (insufficient_quota) — dobít na "
                     "https://platform.openai.com/settings/organization/billing/")
        raise RuntimeError(f"HTTP {e.code} {path}: {detail}") from None


# ---------------------------------------------------------------- volba modelu

_EXCLUDE = re.compile(r"(mini|nano|pro|codex|chat|audio|realtime|image|search|transcribe|tts|"
                      r"embedding|moderation|live|instruct|turbo|whisper|translate)")


def list_models(refresh: bool = False) -> list[str]:
    if not refresh and MODELS_CACHE.exists() and time.time() - MODELS_CACHE.stat().st_mtime < 86400:
        return json.loads(MODELS_CACHE.read_text())
    ids = sorted(m["id"] for m in http("GET", "/models")["data"])
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_CACHE.write_text(json.dumps(ids))
    return ids


def vision_candidates(ids: list[str]) -> list[tuple[tuple, str]]:
    """Vlajkové GPT modely (všechny řady gpt-4o+ umí obraz), seřazené od nejlepšího.
    Pořadí: verze ↓, u stejné verze `-sol` (vlajková řada 6.x) před základním názvem;
    datované snapshoty a menší řady (luna, terra, astra, mini…) se přeskakují."""
    out = []
    for m in ids:
        mm = re.fullmatch(r"gpt-(\d+)(?:\.(\d+))?(o)?(-sol)?", m)
        if not mm or _EXCLUDE.search(m):
            continue
        ver = (int(mm.group(1)), int(mm.group(2) or 0), 1 if mm.group(4) else 0)
        out.append((ver, m))
    return sorted(out, reverse=True)


def pick_model(requested: str) -> str:
    if requested and requested != "auto":
        return requested
    cands = vision_candidates(list_models())
    if not cands:
        sys.exit("V nabídce API není žádný vhodný vision model.")
    return cands[0][1]


def price_for(model: str):
    base = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", model)
    return PRICES.get(base)


# ---------------------------------------------------------------- schémata

def F(desc: str) -> dict:
    """Pole záznamu: doslovné čtení, normalizace, jistota."""
    return {
        "type": "object",
        "description": desc,
        "additionalProperties": False,
        "required": ["raw", "value", "confidence"],
        "properties": {
            "raw": {"type": ["string", "null"]},
            "value": {"type": ["string", "null"]},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        },
    }


def obj(props: dict, desc: str = "") -> dict:
    return {"type": "object", "description": desc, "additionalProperties": False,
            "required": list(props), "properties": props}


def arr(item: dict, desc: str = "") -> dict:
    return {"type": "array", "description": desc, "items": item}


def person(desc: str) -> dict:
    return obj({
        "jmeno": F("jméno a příjmení osoby"),
        "povolani_stav": F("povolání / stav / vyznání u osoby"),
        "bydliste": F("obec a č. p. bydliště / původu"),
    }, desc)


SCHEMA_N = obj({
    "datum_narozeni": F("den a měsíc (a rok) narození"),
    "datum_krtu": F("den a měsíc (a rok) křtu"),
    "cislo_domu": F("číslo domu, kde se dítě narodilo"),
    "misto": F("obec / místo narození, pokud uvedeno"),
    "jmeno_ditete": F("křestní jméno(a) dítěte, jak stojí v rubrice"),
    "nabozenstvi": F("náboženství"),
    "pohlavi": F("pohlaví (mužské / ženské)"),
    "manzelske": F("manželské / nemanželské"),
    "otec": person("otec dítěte"),
    "otec_otec": person("otec otce (děd z otcovy strany)"),
    "otec_matka": person("matka otce (babička z otcovy strany), včetně rodného příjmení"),
    "matka": person("matka dítěte (rodné příjmení, je-li uvedeno)"),
    "matka_otec": person("otec matky"),
    "matka_matka": person("matka matky, včetně rodného příjmení"),
    "kmotri": arr(person("kmotr / kmotra / svědek"), "kmotři a svědkové v pořadí zápisu"),
    "porodni_baba": person("porodní bába"),
    "krtitel": F("kdo křtil (jméno a funkce)"),
    "poznamky": arr(F("přípisek / poznámka"), "pozdější přípisky, marginálie, poznámky"),
})

SCHEMA_O = obj({
    "datum_snatku": F("datum oddavek"),
    "oddavajici": F("kdo oddával"),
    "cislo_domu": F("číslo domu (obvykle nevěsty)"),
    "misto": F("obec"),
    "zenich": person("ženich"),
    "zenich_vek": F("věk nebo datum narození ženicha"),
    "zenich_stav": F("svobodný / vdovec"),
    "zenich_otec": person("otec ženicha"),
    "zenich_matka": person("matka ženicha"),
    "nevesta": person("nevěsta"),
    "nevesta_vek": F("věk nebo datum narození nevěsty"),
    "nevesta_stav": F("svobodná / vdova"),
    "nevesta_otec": person("otec nevěsty"),
    "nevesta_matka": person("matka nevěsty"),
    "nabozenstvi": F("náboženství snoubenců"),
    "svedci": arr(person("svědek"), "svědkové v pořadí zápisu"),
    "poznamky": arr(F("přípisek / poznámka"), "ohlášky, dispenze, přípisky"),
})

SCHEMA_Z = obj({
    "datum_umrti": F("datum úmrtí"),
    "datum_pohrbu": F("datum pohřbu"),
    "cislo_domu": F("číslo domu"),
    "misto": F("obec"),
    "zemrely": person("zemřelý / zemřelá"),
    "nabozenstvi": F("náboženství"),
    "pohlavi": F("pohlaví"),
    "vek": F("věk"),
    "pricina_smrti": F("nemoc / příčina smrti"),
    "rodice_manzel": arr(person("rodič nebo manžel/ka"), "u dětí rodiče, u dospělých manžel/ka"),
    "ohledac": F("ohledač mrtvých"),
    "pohrbil": F("kdo pohřbil"),
    "poznamky": arr(F("přípisek / poznámka"), "přípisky, marginálie"),
})

SCHEMA_SCITANI = obj({
    "obec": F("obec"),
    "cislo_domu": F("číslo domu"),
    "osoby": arr(obj({
        "poradi": F("pořadové číslo osoby"),
        "jmeno": F("příjmení a jméno"),
        "vztah": F("vztah k přednostovi domácnosti"),
        "pohlavi": F("pohlaví"),
        "datum_narozeni": F("den, měsíc, rok narození"),
        "misto_narozeni": F("rodiště (obec, okres)"),
        "domovska_obec": F("domovská obec / příslušnost"),
        "nabozenstvi": F("náboženství"),
        "rodinny_stav": F("rodinný stav"),
        "povolani": F("povolání"),
        "jazyk": F("obcovací / mateřský jazyk"),
        "poznamka": F("ostatní údaje k osobě"),
    }), "osoby domácnosti v pořadí archu"),
    "poznamky": arr(F("poznámka"), "ostatní údaje archu"),
})

SCHEMA_DOKLAD = obj({
    "druh_dokladu": F("druh dokladu (rodný list, křestní list, domovský list…)"),
    "vydavatel": F("úřad / farnost, která doklad vydala"),
    "datum_vystaveni": F("datum vystavení"),
    "osoby": arr(obj({"jmeno": F("jméno"), "role": F("role v dokladu (dítě, otec, matka…)"),
                      "udaje": F("ostatní údaje u osoby (narození, bydliště, povolání)")}), "osoby"),
    "rubriky": arr(obj({"rubrika": {"type": "string"}, "raw": {"type": ["string", "null"]},
                        "value": {"type": ["string", "null"]},
                        "confidence": {"type": "string", "enum": ["high", "medium", "low"]}},
                       "rubrika formuláře"), "všechny rubriky dokladu v pořadí"),
    "poznamky": arr(F("poznámka / razítko / podpis"), "razítka, podpisy, přípisky"),
})

SCHEMAS = {"N": SCHEMA_N, "O": SCHEMA_O, "Z": SCHEMA_Z, "scitani": SCHEMA_SCITANI, "doklad": SCHEMA_DOKLAD}

TYPE_NAMES = {
    "N": "zápis z matriky narozených / pokřtěných (jozefínské rubriky)",
    "O": "zápis z matriky oddaných",
    "Z": "zápis z matriky zemřelých",
    "scitani": "sčítací arch (domácnost po osobách)",
    "doklad": "úřední doklad (rodný/křestní/oddací list, výpis…)",
}


def wrap_schema(typ: str) -> dict:
    return obj({
        "zapis_nalezen": {"type": "boolean",
                          "description": "true, pokud je na snímku zápis odpovídající nápovědě (nebo je-li výřez)"},
        "umisteni": {"type": "string",
                     "description": "kde na snímku zápis je (strana, pořadí zápisu, pořadové číslo)"},
        "jazyk_pismo": {"type": "string", "description": "jazyk a písmo zápisu"},
        "zapis": SCHEMAS[typ],
        "nejista_mista": arr({"type": "string"}, "rubriky/slova, která má člověk ověřit proti snímku"),
    })


PROMPT = """Jsi paleograf, který doslovně čte české matriky a úřední doklady 18.–20. století
(kurent i latinka, česky, německy, latinsky). Tvé čtení je NEZÁVISLÉ druhé čtení pro kontrolu.

Pravidla:
- `raw` = DOSLOVNÝ přepis: zachovej pravopis zápisu (w, ss, g=j, ň…), zkratky, číslice, koncovky jako
  „Novotný-ho“. Nenormalizuj jména na běžnější tvar, neopravuj pravopis.
- Nečitelné znaky/slova piš `[?]`, nejisté čtení `[Wáclaw?]`. Prázdná rubrika → raw null.
- NIKDY nevymýšlej: žádná data, jména ani čísla, která na snímku nejsou. Nedovozuj příjmení dítěte
  z otce do `raw`. Pokud si nejsi jistý, sniž `confidence` a uveď místo v `nejista_mista`.
- `value` = normalizace jen pro strojové zpracování: datum ISO (RRRR-MM-DD, rok z hlavičky stránky/
  ročníku, pokud je jednoznačný), číslo domu jen číslo, jméno současným pravopisem (Wáclaw → Václav),
  příjmení ženy může být v ženském tvaru. Jiné jméno, než stojí na snímku, do value nepiš.
- Rubriky čti v rámci JEDNOHO řádku/zápisu tabulky — nepřebírej údaje ze sousedních zápisů.
  Vpisky nad řádkem, marginálie a pozdější přípisky dej do `poznamky` (u daného pole jen když
  k němu zjevně patří).
- Každé pole má `raw` (doslovně), `value` (normalizace) a `confidence`; prázdná rubrika → raw i value null.
- confidence: high = čteno jistě, medium = drobná nejistota, low = odhad.
"""


def user_text(typ: str, hint: str | None, cropped: bool) -> str:
    t = [f"Typ záznamu: {TYPE_NAMES[typ]}."]
    if cropped:
        t.append("Snímek je výřez obsahující hledaný zápis (případně okraje sousedních zápisů — ty ignoruj).")
    else:
        t.append("Na snímku je celá stránka/dvojstrana s více zápisy. Přečti JEN zápis odpovídající nápovědě; "
                 "pokud žádný neodpovídá, nastav zapis_nalezen=false a pole nech prázdná (null).")
    if hint:
        t.append(f"Nápověda (jen k NALEZENÍ zápisu, ne k doplňování obsahu): {hint}")
    t.append("Vrať strukturované čtení podle schématu.")
    return "\n".join(t)


# ---------------------------------------------------------------- obrázek

def prepare_image(path: Path, crop: str | None, max_side: int, enhance: bool) -> tuple[bytes, dict]:
    im = Image.open(path)
    im = ImageOps.exif_transpose(im).convert("RGB")
    info = {"original": list(im.size)}
    if crop:
        x, y, w, h = (int(v) for v in crop.split(","))
        im = im.crop((x, y, x + w, y + h))
        info["crop"] = [x, y, w, h]
    if max(im.size) > max_side:
        s = max_side / max(im.size)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    if enhance:
        im = ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=1).convert("RGB")
    info["sent"] = list(im.size)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    info["bytes"] = buf.tell()
    return buf.getvalue(), info


# ---------------------------------------------------------------- volání

def call(model: str, typ: str, img: bytes, hint: str | None, cropped: bool,
         effort: str | None, detail: str) -> dict:
    body = {
        "model": model,
        "input": [
            {"role": "developer", "content": [{"type": "input_text", "text": PROMPT}]},
            {"role": "user", "content": [
                {"type": "input_text", "text": user_text(typ, hint, cropped)},
                {"type": "input_image", "detail": detail,
                 "image_url": "data:image/jpeg;base64," + base64.b64encode(img).decode()},
            ]},
        ],
        "text": {"format": {"type": "json_schema", "name": f"zapis_{typ}", "strict": True,
                            "schema": wrap_schema(typ)}},
        "store": False,
    }
    if effort:
        body["reasoning"] = {"effort": effort}
    try:
        return http("POST", "/responses", body)
    except RuntimeError as e:
        msg = str(e)
        # starší / jiné modely: bez reasoning, příp. bez detail=original
        if effort and "reasoning" in msg:
            body.pop("reasoning")
        elif detail == "original" and "detail" in msg:
            body["input"][1]["content"][1]["detail"] = "high"
        else:
            raise
        print("Pozn.: model odmítl parametr, opakuji bez něj.", file=sys.stderr)
        return http("POST", "/responses", body)


def output_text(resp: dict) -> str:
    for item in resp.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    return c["text"]
                if c.get("type") == "refusal":
                    raise RuntimeError("Model odmítl: " + c.get("refusal", ""))
    raise RuntimeError(f"Odpověď bez textu (status {resp.get('status')})")


def usage_of(resp: dict, model: str) -> dict:
    u = resp.get("usage") or {}
    inp = u.get("input_tokens", 0)
    cached = (u.get("input_tokens_details") or {}).get("cached_tokens", 0)
    out = u.get("output_tokens", 0)
    reasoning = (u.get("output_tokens_details") or {}).get("reasoning_tokens", 0)
    res = {"input_tokens": inp, "cached_tokens": cached, "output_tokens": out, "reasoning_tokens": reasoning}
    p = price_for(resp.get("model") or model) or price_for(model)
    if p:
        res["cost_usd_est"] = round(((inp - cached) * p[0] + cached * p[1] + out * p[2]) / 1e6, 5)
        res["price_per_1m"] = {"input": p[0], "cached": p[1], "output": p[2]}
    else:
        res["cost_usd_est"] = None
    return res


def cmd_read(a) -> None:
    path = Path(a.image)
    typ = a.type
    model = pick_model(a.model)
    img, info = prepare_image(path, a.crop, a.max_side, a.enhance)
    if a.dry_run:  # bez volání API: uloží odesílaný obrázek ke kontrole výřezu
        prev = Path(a.out).with_suffix(".sent.jpg")
        prev.parent.mkdir(parents=True, exist_ok=True)
        prev.write_bytes(img)
        patches = -(-info["sent"][0] // 32) * -(-info["sent"][1] // 32)
        print(f"dry-run: model {model}, obrázek {info['sent']} ({info['bytes']} B, ~{patches} dlaždic 32×32) → {prev}")
        return
    t0 = time.time()
    resp = call(model, typ, img, a.hint, bool(a.crop), a.effort, a.detail)
    secs = round(time.time() - t0, 1)
    reading = json.loads(output_text(resp))
    usage = usage_of(resp, model)
    result = {
        "nastroj": "openai_read",
        "model": resp.get("model", model),
        "model_pozadovany": a.model,
        "typ": typ,
        "snimek": str(path),
        "snimek_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "obrazek": info,
        "detail": a.detail,
        "effort": a.effort,
        "hint": a.hint,
        "cas": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "trvani_s": secs,
        "usage": usage,
        "cteni": reading,
    }
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with USAGE_LOG.open("a") as f:
        f.write(json.dumps({"cas": result["cas"], "model": result["model"], "typ": typ,
                            "snimek": path.name, "crop": a.crop, "sent": info["sent"],
                            "detail": a.detail, "effort": a.effort, "trvani_s": secs,
                            "out": str(out), **usage}, ensure_ascii=False) + "\n")
    c = usage.get("cost_usd_est")
    print(f"{out}: model {result['model']}, zápis nalezen={reading.get('zapis_nalezen')}, "
          f"tokeny in {usage['input_tokens']} / out {usage['output_tokens']} "
          f"(z toho reasoning {usage['reasoning_tokens']}), "
          f"cena ≈ {'$%.4f' % c if c is not None else 'neznámá'}, {secs} s")


def cmd_models(a) -> None:
    ids = list_models(refresh=a.refresh)
    cands = vision_candidates(ids)
    for _, m in cands:
        p = price_for(m)
        print(f"{m:20s} {'cena %s/%s USD za 1M' % (p[0], p[2]) if p else 'cena neznámá'}")
    print(f"\nauto → {cands[0][1] if cands else '—'}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("read", help="přečíst snímek")
    r.add_argument("image")
    r.add_argument("--type", required=True, choices=list(SCHEMAS))
    r.add_argument("--crop", help="výřez x,y,w,h v pixelech originálu")
    r.add_argument("--hint", help="obec, rok, hledaná osoba — jen k nalezení zápisu")
    r.add_argument("--model", default="auto")
    r.add_argument("--effort", default="medium", help="reasoning effort (low|medium|high); '' = nevyplňovat")
    r.add_argument("--detail", default="original", choices=["original", "high", "auto", "low"])
    r.add_argument("--max-side", type=int, default=3200, help="max. delší strana odeslaného obrázku")
    r.add_argument("--enhance", action="store_true", help="šedotón + autokontrast")
    r.add_argument("--dry-run", action="store_true", help="nevolat API, jen uložit odesílaný obrázek")
    r.add_argument("--out", required=True)
    m = sub.add_parser("models", help="vypsat kandidáty na vision model")
    m.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    if a.cmd == "read":
        a.effort = a.effort or None
        cmd_read(a)
    else:
        cmd_models(a)


if __name__ == "__main__":
    main()
