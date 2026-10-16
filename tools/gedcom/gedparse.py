"""Minimální parser GEDCOM 5.5.1 bez závislostí (stromová struktura, CONC/CONT sloučené)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

LINE_RE = re.compile(r"^\s*(\d+)\s+(@[^@]+@\s+)?(\S+)(?:\s(.*))?$")


@dataclass
class Node:
    tag: str
    value: str = ""
    xref: str | None = None
    children: list["Node"] = field(default_factory=list)

    def first(self, tag: str) -> "Node | None":
        return next((c for c in self.children if c.tag == tag), None)

    def all(self, tag: str) -> list["Node"]:
        return [c for c in self.children if c.tag == tag]

    def val(self, *path: str) -> str:
        node: Node | None = self
        for tag in path:
            node = node.first(tag) if node else None
        return node.value if node else ""


def parse(path: str | Path) -> dict[str, Node]:
    """Vrátí záznamy nejvyšší úrovně podle xref (@I1@ …); HEAD pod klíčem 'HEAD'."""
    records: dict[str, Node] = {}
    stack: list[Node] = []
    for raw in Path(path).read_text(encoding="utf-8-sig").splitlines():
        m = LINE_RE.match(raw)
        if not m:
            continue
        level, xref, tag, value = int(m[1]), (m[2] or "").strip() or None, m[3], m[4] or ""
        if tag in ("CONC", "CONT") and stack:
            parent = stack[level - 1]
            parent.value += ("\n" if tag == "CONT" else "") + value
            continue
        node = Node(tag, value, xref)
        del stack[level:]
        if level == 0:
            records[xref or tag] = node
        else:
            stack[level - 1].children.append(node)
        stack.append(node)
    return records


def year(date: str) -> int | None:
    m = re.search(r"(\d{4})", date or "")
    return int(m[1]) if m else None


def name(indi: Node) -> tuple[str, str]:
    n = indi.first("NAME")
    if not n:
        return "", ""
    given = n.val("GIVN") or n.value.split("/")[0].strip()
    surname = n.val("SURN") or (n.value.split("/")[1] if "/" in n.value else "")
    return given.strip(), surname.strip()
