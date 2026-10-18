#!/usr/bin/env python3
"""Sestaví frontu přímých předků (čísla podle Kekuleho) a dossier ke každému z GEDCOM exportu.

Údaje z exportu jsou v dossieru jen jako **nápovědy** (jistota 0). Existující dossiery se
nepřepisují (jsou rozpracované) — jen se doplní nové; přehled fronty se generuje vždy znovu.

Vedlejší linie: `--family-of <ID>` (opakovatelně) přidá manžele/ky (`<ID>-S<n>`) a děti (`<ID>-C<n>`)
dané osoby; `--parents-of <ID>[:hloubka]` přidá předky (`<ID>-P1` otec, `<ID>-P2` matka, rekurzivně).
ID se uchovávají v `ids.json` a nemění se.

Použití: build_queue.py <export.ged> <root_xref, např. @I500003@> <research/people> [--family-of K0001 …]
"""
from __future__ import annotations

import html
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gedcom"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import checklist as cl  # noqa: E402
from gedparse import Node, name, parse, year  # noqa: E402

EVENT_LABELS = {"BIRT": "narození", "CHR": "křest", "BAPM": "křest", "DEAT": "úmrtí", "BURI": "pohřeb",
                "MARR": "sňatek", "DIV": "rozvod", "RESI": "bydliště", "OCCU": "povolání",
                "EVEN": "událost", "EDUC": "vzdělání", "RELI": "náboženství"}
URL_RE = re.compile(r"https?://[^\s<>\"']+")
STATE_FILE_RE = re.compile(r"^stav:\s*(.+)$", re.M)
STATES = ["zmínka", "převzato", "rozpracováno", "pozastaveno", "dokončeno", "zapsáno"]
STATES_HINT = "zmínka | převzato → rozpracováno ⇄ pozastaveno → dokončeno → zapsáno"
DOCS_HEADING = "## Doklady k dohledání"
DOCS_HINT = ("*Formát: `- [ ] <doklad> | potvrdí: <co> | kde: <doma / rodiče / matriční úřad …>`; "
             "`[x]` = máme (cesta k souboru v `sources/`), `[-]` = nesehnatelné. Agreguje se do "
             "`research/doklady.md`.*")
DEFERRED_HEADING = "## Odloženo (vědomě neřešeno)"
DEFERRED_HINT = ("*Co jsme se rozhodli teď nedělat — aby se na to nezapomnělo a nehledalo se to omylem znovu. "
                 "Formát: `- YYYY-MM-DD · **co** — proč / kde · kdo rozhodl`.*")
DOC_LINE_RE = re.compile(r"^- \[([ x~-])\] (.+)$")


def clean(text: str) -> str:
    """HTML z MyHeritage → prostý text (entity bývají escapované i dvakrát)."""
    for _ in range(3):
        text = html.unescape(text)
    text = re.sub(r"<br\s*/?>|</p>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", text)).strip()


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def relation(k: int) -> str:
    if k == 1:
        return "výchozí osoba"
    path = []
    while k > 1:
        path.append("otec" if k % 2 == 0 else "matka")
        k //= 2
    return " → ".join(reversed(path))


def describe_event(ev: Node) -> str:
    # hodnota "Y" = MyHeritage příznak „událost nastala, bez data“
    parts = [ev.val("TYPE"), ev.val("DATE"), ev.val("PLAC"), ev.val("ADDR"), "" if ev.value == "Y" else ev.value]
    if ev.val("AGE"):
        parts.append(f"věk {ev.val('AGE')}")
    if ev.val("CAUS"):
        parts.append(f"příčina: {ev.val('CAUS')}")
    return ", ".join(p for p in parts if p)


class Tree:
    def __init__(self, path: str):
        self.rec = parse(path)

    def indi(self, xref: str | None) -> Node | None:
        return self.rec.get(xref) if xref else None

    def parents(self, indi: Node) -> tuple[Node | None, Node | None, Node | None]:
        fam = self.indi(indi.val("FAMC"))
        if not fam:
            return None, None, None
        return self.indi(fam.val("HUSB")), self.indi(fam.val("WIFE")), fam

    def families(self, indi: Node) -> list[Node]:
        return [f for f in (self.indi(n.value) for n in indi.all("FAMS")) if f]

    def label(self, indi: Node | None) -> str:
        if not indi:
            return "?"
        g, s = name(indi)
        b, d = year(indi.val("BIRT", "DATE")), year(indi.val("DEAT", "DATE"))
        life = f" ({b or '?'}–{d or ''})" if b or d else ""
        return f"{g} {s}{life}".strip()

    def source_title(self, xref: str) -> str:
        src = self.indi(xref)
        if not src:
            return xref
        kind = src.val("_TYPE")
        return f"{src.val('TITL')}{' — ' + src.val('AUTH') if src.val('AUTH') else ''}{f' [{kind}]' if kind else ''}"


def ancestors(tree: Tree, root: str) -> dict[int, Node]:
    out, todo = {}, [(1, tree.indi(root))]
    while todo:
        k, indi = todo.pop(0)
        if not indi:
            continue
        out[k] = indi
        father, mother, _ = tree.parents(indi)
        todo += [(2 * k, father), (2 * k + 1, mother)]
    return out


def collect_texts(node: Node, tree: Tree, ctx: str = "") -> tuple[list[str], list[str]]:
    """Poznámky a citace (s kontextem události) rekurzivně."""
    notes, cites = [], []
    for c in node.children:
        here = EVENT_LABELS.get(c.tag, ctx)
        if c.tag == "NOTE" and c.value and not c.value.startswith("@"):
            notes.append(f"{f'[{ctx}] ' if ctx else ''}{clean(c.value)}")
        elif c.tag == "SOUR":
            page, text = c.val("PAGE"), clean(c.val("DATA", "TEXT"))
            cites.append(f"{f'[{ctx}] ' if ctx else ''}{tree.source_title(c.value)}"
                         f"{' — ' + page if page else ''}{' — „' + text + '“' if text else ''}")
            continue
        n, s = collect_texts(c, tree, here)
        notes += n
        cites += s
    return notes, cites


def dossier(tree: Tree, pid: str, rel: str, indi: Node, idmap: dict[str, str]) -> str:
    g, s = name(indi)
    sex = indi.val("SEX")
    birth, death = year(indi.val("BIRT", "DATE")) or year(indi.val("CHR", "DATE")), year(indi.val("DEAT", "DATE"))
    fams = tree.families(indi)
    father, mother, pfam = tree.parents(indi)

    def ref(p: Node | None) -> str:
        if not p:
            return "—"
        kk = idmap.get(p.xref)
        return f"{tree.label(p)}" + (f" ({kk})" if kk else "")

    est = ""
    if birth is None:
        kids = [year(tree.indi(c.value).val("BIRT", "DATE")) for f in fams for c in f.all("CHIL")
                if tree.indi(c.value)]
        kids = [y for y in kids if y]
        if kids:
            birth, est = min(kids) - 28, f"odhad z narození nejstaršího dítěte ({min(kids)} − 28)"
    facts = cl.finish(cl.Facts(birth=birth, death=death, birth_est=bool(est),
                               male=(sex == "M") if sex in ("M", "F") else None, married=bool(fams),
                               dead=bool(indi.first("DEAT") or indi.first("BURI"))), pid, None)

    lines = [
        "---",
        f"id: {pid}",
        *([f"kekule: {int(pid[1:])}"] if re.fullmatch(r"K\d+", pid) else []),
        "původ: myheritage       # myheritage | pramen | ústně",
        f"myheritage: {{id: {indi.xref.strip('@')}, uid: {indi.val('_UID')}}}",
        "gramps_id: null",
        f"stav: převzato          # {STATES_HINT}",
        "---",
        "",
        f"# {g} {s} ({pid})",
        "",
        f"*{rel}*" + (f" · odhad roku narození: {est}" if est else ""),
        "",
        "## Nápovědy z MyHeritage (jistota 0 — neověřeno)",
        "",
    ]
    for ev in indi.children:
        if ev.tag in EVENT_LABELS:
            d = describe_event(ev)
            if d:
                lines.append(f"- **{EVENT_LABELS[ev.tag]}:** {d}")
    lines += [f"- **otec:** {ref(father)}", f"- **matka:** {ref(mother)}"]
    if pfam and pfam.first("MARR"):
        lines.append(f"- **sňatek rodičů:** {describe_event(pfam.first('MARR'))}")
    for f in fams:
        spouse = tree.indi(f.val("WIFE") if indi.xref == f.val("HUSB") else f.val("HUSB"))
        marr = describe_event(f.first("MARR")) if f.first("MARR") else ""
        lines.append(f"- **manžel/ka:** {ref(spouse)}{' — sňatek ' + marr if marr else ''}")
        kids = [tree.label(tree.indi(c.value)) for c in f.all("CHIL") if tree.indi(c.value)]
        if kids:
            lines.append(f"  - děti: {'; '.join(kids)}")
    alt = [n.value.replace("/", "") for n in indi.all("NAME")[1:]] + [n.val("_MARNM") for n in indi.all("NAME")
                                                                       if n.val("_MARNM")]
    if alt:
        lines.append(f"- **další jména:** {', '.join(a for a in alt if a)}")

    notes, cites = collect_texts(indi, tree)
    for f in fams:
        n, c = collect_texts(f, tree, "rodina")
        notes += n
        cites += c
    links = sorted({u.rstrip(".,)") for t in notes + cites for u in URL_RE.findall(t)
                    if "myheritage" not in u and "mhcache" not in u})
    if links:
        lines += ["", "### Odkazy do archivů (z poznámek — ověřit jako první)", ""]
        lines += [f"- {u}" for u in links]
    if notes:
        lines += ["", "### Poznámky", ""] + [f"- {n}" for n in notes if n]
    if cites:
        lines += ["", "### Citace v MyHeritage", ""] + [f"- {c}" for c in cites]
    media = [o.val("FILE").rsplit("/", 1)[-1] for o in indi.all("OBJE") if o.val("FILE")]
    if media:
        lines += ["", "### Média (v `media/`)", ""] + [f"- {m} — {o}" for m, o in
                                                       zip(media, [o.val("TITL") for o in indi.all("OBJE")])]

    lines += ["", "## Checklist", "", cl.render(cl.evaluate(facts, {}), facts).rstrip()]
    lines += ["", DOCS_HEADING, "", DOCS_HINT, ""]
    lines += ["", DEFERRED_HEADING, "", DEFERRED_HINT, ""]
    lines += ["", "## Log hledání", "",
              "*Formát: `- YYYY-MM-DD | pramen (archiv, svazek, roky, snímky; hledané jméno + varianty) | výsledek | odkaz`. Zapisovat i „nenalezeno“ — u nenalezeného navíc `| proč na absenci záleží | příště zkusit`.*", "",
              "## Výzkum", "", "*(zjištění, rozbor rozporů, závěry — odkazy na přepisy a patche)*", ""]
    return "\n".join(lines)


def ensure_docs_section(path: Path) -> None:
    """Do staršího dossieru vloží chybějící sekce (doklady, odloženo) před log — nic jiného nemění."""
    text = path.read_text(encoding="utf-8")
    if "## Log hledání" not in text:
        return
    changed = False
    for heading, hint in ((DOCS_HEADING, DOCS_HINT), (DEFERRED_HEADING, DEFERRED_HINT)):
        if heading.split(" (")[0] not in text:
            text = text.replace("## Log hledání", f"{heading}\n\n{hint}\n\n## Log hledání", 1)
            changed = True
    if changed:
        path.write_text(text, encoding="utf-8")


def collect_docs(path: Path, pid: str) -> list[dict]:
    out, inside = [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            inside = line.strip() == DOCS_HEADING
            continue
        m = DOC_LINE_RE.match(line) if inside else None
        if not m:
            continue
        parts = [p.strip() for p in m[2].split("|")]
        fields = {"doc": parts[0], "potvrdí": "", "kde": "neurčeno"}
        for part in parts[1:]:
            key, _, val = part.partition(":")
            if key.strip() in ("potvrdí", "kde") and val.strip():
                fields[key.strip()] = val.strip()
        out.append({**fields, "state": m[1], "pid": pid, "file": path.name})
    return out


def write_docs_index(out: Path, docs: list[dict]) -> None:
    merged: dict[tuple, dict] = {}
    for d in docs:
        key = (d["doc"].lower(), d["state"] == "x")
        if key in merged:
            merged[key]["pids"].append((d["pid"], d["file"]))
            if d["potvrdí"] and d["potvrdí"] not in merged[key]["potvrdí"]:
                merged[key]["potvrdí"] += "; " + d["potvrdí"]
        else:
            merged[key] = {**d, "pids": [(d["pid"], d["file"])]}
    items = list(merged.values())
    open_ = [d for d in items if d["state"] in (" ", "~")]
    done = [d for d in items if d["state"] == "x"]
    gone = [d for d in items if d["state"] == "-"]

    def line(d: dict) -> str:
        who = ", ".join(f"[{p}]({f})" for p, f in d["pids"])
        return f"- [{d['state']}] **{d['doc']}**{' — ' + d['potvrdí'] if d['potvrdí'] else ''} — pro: {who}"

    lines = ["# Doklady k dohledání", "",
             "Generováno `tools/research/build_queue.py` ze sekcí *Doklady k dohledání* v dossierech — "
             "**sem nezapisuj ručně**. Když doklad máš, dej sken do `../doklady/` a řekni to kterékoli "
             "session nebo managerovi; stav se změní v dossieru.", "",
             f"## Chybí ({len(open_)})", ""]
    for kde in sorted({d["kde"] for d in open_}):
        lines += [f"### {kde}", "", *[line(d) for d in open_ if d["kde"] == kde], ""]
    if done:
        lines += [f"## Máme ({len(done)})", "", *[line(d) for d in done], ""]
    if gone:
        lines += [f"## Nesehnatelné ({len(gone)})", "", *[line(d) for d in gone], ""]
    (out.parent / "doklady.md").write_text("\n".join(lines), encoding="utf-8")


def kid(k: int) -> str:
    return f"K{k:04d}"


def load_ids(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def add_family(tree: Tree, anchor_id: str, ids: dict[str, str]) -> list[str]:
    """Přidá ID manželům/kám (S<n>) a dětem (C<n>) osoby anchor_id; vrací nově přidaná ID."""
    rev = {v: x for x, v in ids.items()}
    indi = tree.indi(rev.get(anchor_id))
    if not indi:
        sys.exit(f"osoba {anchor_id} v ids.json není")
    used = set(ids.values())

    def nxt(kind: str) -> str:
        n = 1
        while f"{anchor_id}-{kind}{n}" in used:
            n += 1
        used.add(f"{anchor_id}-{kind}{n}")
        return f"{anchor_id}-{kind}{n}"

    new = []
    fams = tree.families(indi)
    for f in fams:
        sp = f.val("WIFE") if indi.xref == f.val("HUSB") else f.val("HUSB")
        if sp and sp not in ids:
            ids[sp] = nxt("S")
            new.append(ids[sp])
    kids = [c.value for f in fams for c in f.all("CHIL") if tree.indi(c.value)]
    kids.sort(key=lambda x: (year(tree.indi(x).val("BIRT", "DATE")) or 9999))
    for c in kids:
        if c not in ids:
            ids[c] = nxt("C")
            new.append(ids[c])
    return new


def add_parents(tree: Tree, anchor_id: str, ids: dict[str, str], depth: int) -> list[str]:
    """Přidá ID předkům osoby anchor_id: otec <ID>-P1, matka <ID>-P2, rekurzivně do hloubky depth."""
    rev = {v: x for x, v in ids.items()}
    indi = tree.indi(rev.get(anchor_id))
    if not indi:
        sys.exit(f"osoba {anchor_id} v ids.json není")
    new = []
    father, mother, _ = tree.parents(indi)
    for n, p in ((1, father), (2, mother)):
        if not p:
            continue
        if p.xref not in ids:
            ids[p.xref] = f"{anchor_id}-P{n}"
            new.append(ids[p.xref])
        if depth > 1:
            new += add_parents(tree, ids[p.xref], ids, depth - 1)
    return new


def collateral_relation(pid: str, ids_rev: dict[str, str], tree: Tree) -> str:
    anchor, _, last = pid.rpartition("-")
    a = tree.indi(ids_rev.get(anchor))
    who = tree.label(a) if a else anchor
    me = tree.indi(ids_rev.get(pid))
    male = me is not None and me.val("SEX") == "M"
    if last.startswith("S"):
        return f"{'manžel' if male else 'manželka'} — {who} ({anchor})"
    if last.startswith("P"):
        return f"{'otec' if male else 'matka'} — {who} ({anchor})"
    return f"{'syn' if male else 'dcera'} — {who} ({anchor})"


def main(ged: str, root: str, out_dir: str, family_of: list[str], parents_of: list[tuple[str, int]]) -> int:
    tree = Tree(ged)
    if root not in tree.rec:
        sys.exit(f"výchozí osoba {root} v exportu není")
    anc = ancestors(tree, root)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ids_path = out / "ids.json"
    ids = load_ids(ids_path)
    for k, indi in anc.items():
        ids.setdefault(indi.xref, kid(k))
    added = [pid for a in family_of for pid in add_family(tree, a, ids)]
    added += [pid for a, d in parents_of for pid in add_parents(tree, a, ids, d)]
    ids_path.write_text(json.dumps(ids, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    ids_rev = {v: x for x, v in ids.items()}
    # osoby mimo export MyHeritage (nalezené v pramenech / ústně) — zakládá tools/research/add_person.py
    manual_path = out / "manual.json"
    manual = json.loads(manual_path.read_text(encoding="utf-8")) if manual_path.exists() else {}

    def ensure(pid: str, rel: str) -> tuple[Path, str]:
        if pid in manual:
            hits = sorted(p for p in out.glob(f"{pid}-*.md") if re.match(rf"{re.escape(pid)}-[a-z]", p.name))
            if not hits:
                sys.exit(f"dossier ručně založené osoby {pid} chybí")
            ensure_docs_section(hits[0])
            ensure.docs += collect_docs(hits[0], pid)
            m = STATE_FILE_RE.search(hits[0].read_text(encoding="utf-8"))
            return hits[0], (m[1].split("#")[0].strip() if m else "?")
        indi = tree.indi(ids_rev[pid])
        g, s = name(indi)
        existing = sorted(p for p in out.glob(f"{pid}-*.md") if re.match(rf"{re.escape(pid)}-[a-z]", p.name))
        path = existing[0] if existing else out / f"{pid}-{slug(f'{g} {s}') or 'bez-jmena'}.md"
        if not path.exists():
            path.write_text(dossier(tree, pid, rel, indi, ids), encoding="utf-8")
            ensure.created += 1
        ensure_docs_section(path)
        ensure.docs += collect_docs(path, pid)
        m = STATE_FILE_RE.search(path.read_text(encoding="utf-8"))
        return path, (m[1].split("#")[0].strip() if m else "?")
    ensure.created = 0
    ensure.docs = []

    rows = []
    for k in sorted(anc):
        path, state = ensure(kid(k), relation(k))
        rows.append(f"| {k.bit_length()} | K{k} | [{tree.label(anc[k])}]({path.name}) | {relation(k)} | {state} |")
    coll = []
    for pid in sorted(p for p in ids_rev if not re.fullmatch(r"K\d+", p)):
        rel = collateral_relation(pid, ids_rev, tree)
        path, state = ensure(pid, rel)
        coll.append(f"| {pid} | [{tree.label(tree.indi(ids_rev[pid]))}]({path.name}) | {rel} | {state} |")
    for pid in sorted(manual):
        m = manual[pid]
        path, state = ensure(pid, m["rel"])
        life = f" ({m['birth']}–)" if m.get("birth") else ""
        coll.append(f"| {pid} | [{m['name']}{life}]({path.name}) | {m['rel']} · původ: {m['původ']} | {state} |")
    coll.sort(key=lambda r: r.split("|")[1].strip())
    states = [r.rsplit("|", 2)[-2].strip() for r in rows + coll]
    summary = " · ".join(f"{s}: {states.count(s)}" for s in STATES if states.count(s))
    index = ["# Fronta osob", "",
             "Generováno `tools/research/build_queue.py` z exportu MyHeritage. Stav se čte z dossierů, "
             "ID osob jsou stabilní (`ids.json`). Stavy: `docs/metodika/workflow-sessions.md`.", "",
             f"**Souhrn:** {summary}", "",
             "## Přímí předci (čísla podle Kekuleho)", "",
             "| Gen. | K | Osoba (podle MyHeritage) | Vztah | Stav |", "|---|---|---|---|---|", *rows, ""]
    if coll:
        index += ["## Vedlejší linie", "",
                  "ID = kotva + `S<n>` (manžel/ka) / `C<n>` (dítě), např. `K0002-C1` = dítě K2.", "",
                  "| ID | Osoba (podle MyHeritage) | Vztah | Stav |", "|---|---|---|---|", *coll, ""]
    (out / "README.md").write_text("\n".join(index), encoding="utf-8")
    write_docs_index(out, ensure.docs)
    print(f"předků: {len(anc)}, vedlejších: {len(coll)}, nově přidaná ID: {', '.join(added) or '—'}, "
          f"nových dossierů: {ensure.created}")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    fam = []
    while "--family-of" in args:
        i = args.index("--family-of")
        fam.append(args[i + 1])
        del args[i:i + 2]
    par = []
    while "--parents-of" in args:
        i = args.index("--parents-of")
        anchor, _, depth = args[i + 1].partition(":")
        par.append((anchor, int(depth or 1)))
        del args[i:i + 2]
    if len(args) != 3:
        sys.exit(__doc__)
    sys.exit(main(*args, family_of=fam, parents_of=par))
