// Workbench dashboard — frontend. Čte /api/state (polling), kreslí rodokmen v SVG, panel osoby.
"use strict";

const BW = 190, BH = 60, COLW = 270, VGAP = 8, INDENT = 16, MAX_INDENT = 4;
const POLL_MS = 5000;
const STATE_COLORS = {
  "": "var(--s-missing)", "zmínka": "var(--s-zminka)", "převzato": "var(--s-prevzato)",
  "rozpracováno": "var(--s-rozpracovano)", "pozastaveno": "var(--s-pozastaveno)",
  "dokončeno": "var(--s-dokonceno)", "zapsáno": "var(--s-zapsano)", "bez dossieru": "var(--s-missing)",
};
const STATE_HELP = {
  "zmínka": "jen zmínka, nesáhnuto", "převzato": "převzato z MyHeritage, nesáhnuto",
  "rozpracováno": "session na osobě pracuje", "pozastaveno": "rozpracováno, odloženo",
  "dokončeno": "výzkum hotový, čeká na zápis", "zapsáno": "zapsáno do Gramps",
};
const TYPE_CS = { Birth: "narození", Death: "úmrtí", Residence: "bydliště", Census: "sčítání", Occupation: "povolání / bytem",
                  Christening: "křest", Baptism: "křest", Burial: "pohřeb", Marriage: "sňatek", Religion: "vyznání" };
const circled = (n) => (n === 0 ? "⓪" : n <= 20 ? String.fromCharCode(0x2460 + n - 1) : `(${n})`);
const SVGNS = "http://www.w3.org/2000/svg";
const $ = (s) => document.querySelector(s);

let S = null;               // poslední stav z /api/state
let nodes = new Map();      // id → {id, p (osoba|null), x, y, kind}
let selected = null;
let hit = null;
let T = { x: 40, y: 40, k: 0.8 };
let firstRender = true;
let openDetails = new Set();

const store = {
  get(k, d) { try { const v = localStorage.getItem("dash." + k); return v === null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem("dash." + k, JSON.stringify(v)); } catch { /* bez úložiště */ } },
};
let collapsed = new Set(store.get("collapsed", []));

// ------------------------------------------------------------------ ID → struktura

const isKek = (id) => /^K\d+$/.test(id);
const kekNum = (id) => parseInt(id.slice(1), 10);
const kid = (n) => "K" + String(n).padStart(4, "0");

function structParent(id) {
  if (isKek(id)) { const n = kekNum(id); return n > 1 ? kid(Math.floor(n / 2)) : null; }
  return id.replace(/-[SCP]\d+$/, "");
}
function lastPart(id) {
  if (isKek(id)) return kekNum(id) % 2 === 0 ? "P1" : "P2";
  return id.match(/-([SCP]\d+)$/)[1];
}
function relLabel(id) {
  const p = structParent(id); if (!p) return "výchozí osoba";
  const part = lastPart(id);
  const what = part === "P1" ? "otec" : part === "P2" ? "matka" : part[0] === "S" ? `${part.slice(1)}. manžel/ka` : `${part.slice(1)}. dítě`;
  return `${what} ${p}`;
}

function buildNodes() {
  const people = S.people;
  const ids = new Set(Object.keys(people));
  for (const id of Object.keys(people)) {          // chybějící články řetězce (K0113, když je K0226)
    let p = structParent(id);
    while (p && !ids.has(p)) { ids.add(p); p = structParent(p); }
  }
  if ($("#f-empty").checked) {                     // prázdní rodiče přímých předků — kam se dá jít
    for (const id of Object.keys(people)) {
      if (isKek(id)) { const n = kekNum(id); ids.add(kid(2 * n)); ids.add(kid(2 * n + 1)); }
    }
  }
  ids.add("K0001");
  const kids = new Map();
  for (const id of ids) {
    const p = structParent(id);
    if (!p) continue;
    if (!kids.has(p)) kids.set(p, []);
    kids.get(p).push(id);
  }
  return { ids, kids };
}

function partOrder(id) {
  const part = lastPart(id);
  return (part[0] === "P" ? 0 : part[0] === "S" ? 1000 : 2000) + parseInt(part.slice(1), 10);
}

function layout() {
  const { kids } = buildNodes();
  const out = new Map();
  const edges = [];
  const childList = (id) => (kids.get(id) || []).slice().sort((a, b) => partOrder(a) - partOrder(b));
  const hasParents = (id) => childList(id).some((c) => lastPart(c)[0] === "P");
  // „mělký“ kolaterál: v jeho podstromu nejsou žádní rodiče → vejde se do sloupce pod kotvu
  const deepMemo = new Map();
  const isDeep = (id) => {
    if (deepMemo.has(id)) return deepMemo.get(id);
    const r = !collapsed.has(id) && (hasParents(id) || childList(id).some(isDeep));
    deepMemo.set(id, r); return r;
  };

  function lay(id, col, indent, y0, kind) {
    const all = collapsed.has(id) ? [] : childList(id);
    const parents = all.filter((c) => lastPart(c)[0] === "P");
    const cols = all.filter((c) => lastPart(c)[0] !== "P");
    let y = y0;
    const parY = [];
    for (const p of parents) {
      const h = lay(p, col + 1, 0, y, "parent");
      parY.push(out.get(p).y); y += h;
    }
    const parH = y - y0;
    const boxY = parY.length ? (parY[0] + parY[parY.length - 1]) / 2 : y0;
    const x = col * COLW + indent * INDENT;
    out.set(id, { id, x, y: boxY, kind, col, collapsedKids: collapsed.has(id) ? (kids.get(id) || []).length : 0,
                  hasKids: (kids.get(id) || []).length > 0 });
    for (const p of parents) edges.push({ type: "parent", from: id, to: p });

    let flatY = boxY + BH + VGAP;
    let bottom = Math.max(y0 + parH, boxY + BH + VGAP);
    const flat = cols.filter((c) => !isDeep(c));
    const deep = cols.filter((c) => isDeep(c));
    const ci = Math.min(indent + 1, MAX_INDENT);
    for (const c of flat) {
      const h = lay(c, col, ci, flatY, lastPart(c)[0] === "S" ? "spouse" : "child");
      flatY += h;
      edges.push({ type: lastPart(c)[0] === "S" ? "spouse" : "child", from: id, to: c });
    }
    bottom = Math.max(bottom, flatY);
    for (const c of deep) {
      const h = lay(c, col, ci, bottom, lastPart(c)[0] === "S" ? "spouse" : "child");
      bottom += h;
      edges.push({ type: lastPart(c)[0] === "S" ? "spouse" : "child", from: id, to: c });
    }
    return bottom - y0;
  }
  lay("K0001", 0, 0, 0, "root");
  return { pos: out, edges };
}

// ------------------------------------------------------------------ vykreslení stromu

function el(tag, attrs, parent) {
  const e = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs || {})) e.setAttribute(k, v);
  if (parent) parent.appendChild(e);
  return e;
}
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const trunc = (s, n) => (s.length > n ? s.slice(0, n - 1) + "…" : s);

function years(p) {
  if (!p || (!p.birth && !p.death)) return "";
  return `${p.birth || "?"}–${p.death || ""}`;
}

// vlastní session osoby (k<ID>), jinak session větve, pod kterou osoba spadá (server: people[id].branch)
function sessionOf(id) {
  const ss = S.sessions || [];
  const own = ss.find((s) => s.id === id);
  if (own) return own;
  const p = S.people[id];
  return p && p.branch ? ss.find((s) => s.name === p.branch) : undefined;
}
function sessionTip(ses, id) {
  if (ses.kind !== "vetev") return `session ${ses.name}: ${ses.status}`;
  const p = S.people[id];
  return `session větve ${ses.name}: ${ses.status}\nkořen větve ${ses.root} (${ses.root_src})` +
    (p && p.branch_guess ? "\nžádná osoba větve není rozpracovaná — tečka je u naposledy měněného dossieru" : "");
}
function waitingPatches(p) {
  if (!p || !p.patches) return 0;
  return (p.patches["navrženo"] || 0) + (p.patches["schváleno"] || 0);
}
function matchesFilter(id, p) {
  const work = $("#f-work").checked, wait = $("#f-wait").checked;
  if ($("#f-single").checked && !(p && p.events && p.events.single)) return false;
  if ($("#f-nokx").checked && !(p && p.kontext_missing && p.kontext_missing.length)) return false;
  if (!work && !wait) return true;
  const ses = sessionOf(id);
  let ok = false;
  if (work && p && (["rozpracováno", "pozastaveno"].includes(p.stav) || ses)) ok = true;
  if (wait && ((p && p.patches && p.patches["navrženo"]) || (ses && ses.status !== "working"))) ok = true;
  return ok;
}

function render() {
  const { pos, edges } = layout();
  nodes = pos;
  const gE = $("#edges"), gN = $("#nodes");
  gE.replaceChildren(); gN.replaceChildren();

  for (const e of edges) {
    const a = pos.get(e.from), b = pos.get(e.to);
    if (!a || !b) continue;
    if (e.type === "parent") {
      const x1 = a.x + BW, y1 = a.y + BH / 2, x2 = b.x, y2 = b.y + BH / 2, mx = x2 - 28;
      el("path", { class: "edge", d: `M${x1},${y1} H${mx} V${y2} H${x2}` }, gE);
    } else {
      const x1 = a.x + 8, y1 = a.y + BH, y2 = b.y + BH / 2;
      el("path", { class: `edge col ${e.type}`, d: `M${x1},${y1} V${y2} H${b.x}` }, gE);
      const t = el("text", { class: "edge-label", x: x1 + 2, y: y2 - 3 }, gE);
      t.textContent = e.type === "spouse" ? "∞" : "d.";
    }
  }

  for (const [id, n] of pos) {
    const p = S.people[id] || null;
    const missing = !p;
    const cls = ["node", missing ? "missing" : "", n.kind === "spouse" || n.kind === "child" ? "collateral" : "",
                 id === selected ? "sel" : "", id === hit ? "hit" : "", matchesFilter(id, p) ? "" : "dim"].join(" ");
    const g = el("g", { class: cls, transform: `translate(${n.x},${n.y})`, "data-id": id }, gN);
    const stav = p ? (p.stav || "bez dossieru") : "";
    el("rect", { class: "box", width: BW, height: BH, rx: 4, fill: STATE_COLORS[stav] || "#fff" }, g);
    const tip = el("title", {}, g);
    tip.textContent = missing ? `${id} — nesáhnuto (${relLabel(id)})`
      : `${p.name || "(bez jména)"} · ${id}\n${p.rel || relLabel(id)}\nstav: ${stav}` +
        (p.kontext_missing && p.kontext_missing.length ? `\nchybí: ${p.kontext_missing.join(", ")} (docs/metodika/pribehy.md)` : "") +
        (p.zavora ? `\n${zavoraTip(p.zavora)}` : "");

    const name = missing ? "nesáhnuto" : (p.name || "(bez jména)");
    el("text", { class: "name", x: 7, y: 15 }, g).textContent = trunc(name, 25);
    const meta = missing ? `${id} · ${relLabel(id).split(" ")[0]}` : [id, years(p)].filter(Boolean).join(" · ");
    el("text", { class: "meta", x: 7, y: 29 }, g).textContent = trunc(meta, 34);

    if (p) {
      const b = [];
      const wp = waitingPatches(p);
      if (wp) b.push(`✎${wp}`);
      if (p.hints) b.push(`💡${p.hints}`);
      if (p.todo) b.push(`☐${p.todo_open}/${p.todo}`);
      if (p.docs && p.docs.open) b.push(`📄${p.docs.open}`);
      if (p.sources) b.push("🗂");
      if (p.story) b.push("📖");
      const bt = el("text", { class: "badges", x: 7, y: 45 }, g);
      bt.textContent = b.join("  ");
      const k = p.kontroly;
      if (p.kontext_missing && p.kontext_missing.length) {
        el("tspan", { class: "nokx" }, bt).textContent = `${bt.textContent ? "  " : ""}∅📖`;
      }
      if (p.zavora) {
        const zs = el("tspan", { class: p.zavora.prolomeno ? "zav broken" : "zav" }, bt);
        zs.textContent = `${bt.textContent ? "  " : ""}⛔`;
        el("title", {}, zs).textContent = zavoraTip(p.zavora);
      }
      if (k && k.open) {
        const ts = el("tspan", { class: k.blocking ? "kb block" : "kb" }, bt);
        ts.textContent = `${b.length ? "  " : ""}⚑${k.open}`;
      }
      if ($("#f-single").checked && p.events && p.events.single) {
        el("tspan", { class: "single" }, bt).textContent = `  ①×${p.events.single}`;
      }
      if (p.checklist) drawChecklist(g, p.checklist);
    }
    const ses = sessionOf(id);
    if (ses) {
      const c = el("circle", { class: `run ${ses.status} ${ses.kind === "vetev" ? "branch" : ""} ${p && p.branch_guess ? "guess" : ""}`,
                               cx: BW - 10, cy: 10, r: 5.5 }, g);
      el("title", {}, c).textContent = sessionTip(ses, id);
    }
    if (n.hasKids) {
      const tg = el("g", { class: "toggle", transform: `translate(${BW - 16},${BH - 16})`, "data-toggle": id }, g);
      el("rect", { width: 13, height: 13, rx: 2 }, tg);
      el("text", { x: 6.5, y: 10.5, "text-anchor": "middle" }, tg).textContent = collapsed.has(id) ? "+" : "−";
      el("title", {}, tg).textContent = collapsed.has(id) ? `rozbalit (${n.collapsedKids})` : "sbalit větev";
    }
  }
  applyTransform();
}

function drawChecklist(g, c) {
  const total = c.x + c["~"] + c["-"] + c.n + c[" "];
  if (!total) return;
  const w = BW - 30, x0 = 7, y = BH - 9;
  const segs = [["x", "#2d8a3a"], ["~", "#d6a516"], ["-", "#b5655e"], ["n", "#9a9a9a"], [" ", "#ffffff"]];
  let x = x0;
  for (const [k, col] of segs) {
    if (!c[k]) continue;
    const sw = (w * c[k]) / total;
    el("rect", { x, y, width: sw, height: 5, fill: col }, g);
    x += sw;
  }
  el("rect", { x: x0, y, width: w, height: 5, fill: "none", stroke: "#888", "stroke-width": 0.6 }, g);
  el("title", {}, g.lastChild).textContent =
    `checklist: ${c.x} doloženo, ${c["~"]} slabé, ${c["-"]} nenalezeno, ${c.n} neexistuje, ${c[" "]} nehledáno`;
}

// ------------------------------------------------------------------ pan + zoom

function applyTransform() {
  $("#viewport").setAttribute("transform", `translate(${T.x},${T.y}) scale(${T.k})`);
}
function fit() {
  let x1 = Infinity, y1 = Infinity, x2 = -Infinity, y2 = -Infinity;
  for (const n of nodes.values()) {
    x1 = Math.min(x1, n.x); y1 = Math.min(y1, n.y); x2 = Math.max(x2, n.x + BW); y2 = Math.max(y2, n.y + BH);
  }
  const r = $("#svg").getBoundingClientRect();
  T.k = Math.min(r.width / (x2 - x1 + 60), r.height / (y2 - y1 + 60), 1.2);
  T.x = (r.width - (x2 - x1) * T.k) / 2 - x1 * T.k;
  T.y = (r.height - (y2 - y1) * T.k) / 2 - y1 * T.k;
  applyTransform();
}
function focusNode(id, zoom) {
  const n = nodes.get(id);
  if (!n) return;
  const r = $("#svg").getBoundingClientRect();
  if (zoom) T.k = Math.max(T.k, zoom);
  T.x = r.width / 2 - (n.x + BW / 2) * T.k;
  T.y = r.height / 2 - (n.y + BH / 2) * T.k;
  applyTransform();
}

(function panZoom() {
  const svg = $("#svg");
  let drag = null;
  svg.addEventListener("wheel", (ev) => {
    ev.preventDefault();
    const r = svg.getBoundingClientRect();
    const mx = ev.clientX - r.left, my = ev.clientY - r.top;
    const f = Math.exp(-ev.deltaY * (ev.ctrlKey ? 0.01 : 0.0015));
    const k = Math.min(3, Math.max(0.08, T.k * f));
    T.x = mx - ((mx - T.x) * k) / T.k; T.y = my - ((my - T.y) * k) / T.k; T.k = k;
    applyTransform();
  }, { passive: false });
  svg.addEventListener("pointerdown", (ev) => {
    drag = { x: ev.clientX, y: ev.clientY, tx: T.x, ty: T.y, moved: false };
  });
  window.addEventListener("pointermove", (ev) => {
    if (!drag) return;
    const dx = ev.clientX - drag.x, dy = ev.clientY - drag.y;
    if (!drag.moved && Math.hypot(dx, dy) < 4) return;
    if (!drag.moved) { drag.moved = true; svg.classList.add("drag"); svg.setPointerCapture?.(ev.pointerId); }
    T.x = drag.tx + dx; T.y = drag.ty + dy; applyTransform();
  });
  window.addEventListener("pointerup", (ev) => {
    if (!drag) return;
    const wasMoved = drag.moved;
    drag = null; svg.classList.remove("drag");
    if (wasMoved) return;
    const tg = ev.target.closest?.("[data-toggle]");
    if (tg) { toggle(tg.dataset.toggle); return; }
    const g = ev.target.closest?.(".node");
    if (g) openPerson(g.dataset.id);
  });
})();

function toggle(id) {
  if (collapsed.has(id)) collapsed.delete(id); else collapsed.add(id);
  store.set("collapsed", [...collapsed]);
  const before = nodes.get(id);
  render();
  const after = nodes.get(id);
  if (before && after) { T.x += (before.x - after.x) * T.k; T.y += (before.y - after.y) * T.k; applyTransform(); }
}

// ------------------------------------------------------------------ přehled + lišta

function linkIds(text) {
  return esc(text).replace(/\bK(\d{1,5})((?:-[SCP]\d+)*)\b/g, (m, num, suf) => {
    const id = "K" + String(parseInt(num, 10)).padStart(4, "0") + suf;
    return `<span class="pid" data-pid="${id}">${m}</span>`;
  });
}
function zavoraTip(z) {
  return (z.prolomeno ? `závora (prolomeno ${z.prolomeno})` : "závora") +
    `\nkde: ${z.kde || "?"}\nproč: ${z.proc || "?"}` + (z.sance ? `\nšance prolomit: ${z.sance}` : "");
}
const ZAV_SANCE = { "vysoká": "hi", "střední": "mid", "malá": "lo", "žádná": "none", "prakticky žádná": "none" };
function renderZavory() {
  const all = Object.values(S.people).filter((p) => p.zavora);
  if (!all.length) return `<li class="empty">žádná (sekce ## Závora v dossieru)</li>`;
  const types = [...new Set(all.flatMap((p) => p.zavora.typy))].sort();
  const sel = store.get("zav-typ", "");
  const list = all.filter((p) => !sel || p.zavora.typy.includes(sel))
    .sort((a, b) => (!!a.zavora.prolomeno - !!b.zavora.prolomeno) || a.id.localeCompare(b.id));
  const opts = [`<option value="">všechny typy (${all.length})</option>`].concat(types.map((t) =>
    `<option value="${esc(t)}" ${t === sel ? "selected" : ""}>${esc(t)} (${all.filter((p) => p.zavora.typy.includes(t)).length})</option>`)).join("");
  return `<li><select id="zav-typ">${opts}</select></li>` + (list.map((p) => {
    const z = p.zavora;
    return `<li class="zav-item${z.prolomeno ? " broken" : ""}">${personLabel(p.id)} ${z.typy.map((t) => `<span class="zav-typ">${esc(t)}</span>`).join(" ")}
      ${z.prolomeno ? `<small>prolomeno ${esc(z.prolomeno)}</small>` : ""}
      ${z.kde ? `<br><small><b>kde:</b> ${esc(z.kde)}</small>` : ""}
      ${z.prolomit ? `<br><small><b>prolomilo by:</b> ${esc(z.prolomit)}</small>` : ""}
      ${z.sance ? ` <span class="sance ${ZAV_SANCE[z.sance] || ""}" title="nejlepší z uvedených cest">šance ${esc(z.sance)}</span>` : ""}</li>`;
  }).join("") || `<li class="empty">žádná tohoto typu</li>`);
}
document.addEventListener("change", (ev) => {
  if (ev.target.id === "zav-typ") { store.set("zav-typ", ev.target.value); renderOverview(); }
});
function personLabel(id) {
  const p = S.people[id];
  return `<span class="pid" data-pid="${id}">${id}</span> ${esc(p ? p.name : "")}`;
}

function renderOverview() {
  document.title = `Dashboard — ${S.tree}`;
  $("#title").textContent = `Strom ${S.tree}`;
  const order = [...S.states, "bez dossieru"];
  $("#counts").innerHTML = order.filter((k) => S.counts[k]).map((k) =>
    `<span class="chip" style="background:${STATE_COLORS[k]}" title="${esc(STATE_HELP[k] || "")}">${esc(k)} <b>${S.counts[k]}</b></span>`).join("");

  const dot = (s) => `<svg width="10" height="10"><circle class="run ${s.status}" cx="5" cy="5" r="4.5" style="fill:var(--run-${s.status})"/></svg>`;
  const ses = S.sessions.length ? S.sessions.map((s) => {
    if (s.kind !== "vetev") return `<li>${dot(s)} ${personLabel(s.id)} <small>${esc(s.status)}</small></li>`;
    const on = Object.values(S.people).filter((p) => p.branch === s.name);
    return `<li>${dot(s)} <b>${esc(s.name)}</b> <small>${esc(s.status)}</small><br>
      <small>kořen ${s.root ? `${personLabel(s.root)} <i title="odkud je kořen">(${esc(s.root_src)})</i>` : "neznámý — doplň research/vetve.yml"}</small>
      ${on.length ? `<br><small>${on[0].branch_guess ? "naposledy" : "teď"}: ${on.map((p) => personLabel(p.id)).join(", ")}</small>` : ""}</li>`;
  }).join("")
    : `<li class="empty">žádná osobní session</li>`;
  const waiting = S.patches.filter((p) => ["navrženo", "schváleno"].includes(p.status));
  const pat = waiting.length ? waiting.map((p) =>
    `<li><span class="status ${esc(p.status)}">${esc(p.status)}</span> ${p.id ? `<span class="pid" data-pid="${p.id}">${esc(p.file)}</span>` : esc(p.file)}<br><small>${esc(p.summary)}</small></li>`).join("")
    : `<li class="empty">nic nečeká (${S.patches.length} patchů celkem)</li>`;
  const todos = S.todos.map((t) =>
    `<li title="${esc(t.file)}">${esc(t.title)} <small>— ${t.kind === "sections" ? `${t.open} otevřeno / ${t.entries}` : `${t.entries} záznamů`}</small></li>`).join("")
    || `<li class="empty">žádné</li>`;
  const dok = S.doklady ? `<li>${S.doklady.open} chybí · ${S.doklady.done} máme <small>(research/doklady.md)</small></li>` : `<li class="empty">—</li>`;
  const log = S.log.slice(0, 25).map((l) => `<li>${linkIds(l)}</li>`).join("") || `<li class="empty">prázdný</li>`;
  $("#overview").innerHTML = `
    <h3>Běžící session</h3><ul>${ses}</ul>
    <h3>Patche čekající</h3><ul>${pat}</ul>
    <h3>Závory</h3><ul class="zavory">${renderZavory()}</ul>
    <h3>Sdílené seznamy</h3><ul>${todos}</ul>
    <h3>Doklady k dohledání</h3><ul>${dok}</ul>
    <h3>Výzkumný log (posledních 25)</h3><ul class="log">${log}</ul>`;
}

function renderLegend() {
  const st = [...S.states].map((k) =>
    `<span title="${esc(STATE_HELP[k] || "")}"><i class="sw" style="background:${STATE_COLORS[k]}"></i>${esc(k)}</span>`).join("");
  $("#legend").innerHTML = `
    <div class="row">${st}<span><i class="sw" style="background:#fff;border-style:dashed"></i>nesáhnuto (bez dossieru)</span></div>
    <div class="row"><span>session (kroužek = větev): <b style="color:var(--run-working)">●</b> pracuje <b style="color:var(--run-idle)">●</b> čeká na vstup <b style="color:var(--run-done)">●</b> hotovo</span>
    <span>✎ patch čeká · 💡 nápovědy · ☐ todo otevřeno/celkem · 📄 doklady chybí · 🗂 prameny · 📖 příběh · <span class="nokx">∅📖</span> chybí kontext/příběh · <span class="zav">⛔</span> závora · <b class="kb">⚑</b> kontroly <b class="kb block">⚑</b> blokující</span></div>
    <div class="row"><span>pruh = checklist: <i class="sw" style="background:#2d8a3a"></i>doloženo <i class="sw" style="background:#d6a516"></i>slabé <i class="sw" style="background:#b5655e"></i>nenalezeno <i class="sw" style="background:#9a9a9a"></i>neexistuje <i class="sw"></i>nehledáno</span>
    <span>čárkovaně: <span style="color:#c27b4a">∞ manžel/ka</span>, <span style="color:#5b8f63">d. dítě</span></span></div>`;
}

document.addEventListener("click", (ev) => {
  const t = ev.target.closest?.("[data-pid]");
  if (t) { ev.preventDefault(); openPerson(t.dataset.pid, true); }
});

// ------------------------------------------------------------------ hledání

const fold = (s) => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
let resultIdx = 0;
function search() {
  const q = fold($("#q").value.trim());
  const ul = $("#results");
  if (!q) { ul.hidden = true; return; }
  const res = Object.values(S.people).filter((p) => fold(p.name).includes(q) || fold(p.id).includes(q)).slice(0, 40);
  resultIdx = 0;
  ul.innerHTML = res.map((p, i) => `<li data-id="${p.id}" class="${i === 0 ? "sel" : ""}">${esc(p.name || "(bez jména)")} <small>${p.id} ${esc(years(p))} · ${esc(p.stav || "")}</small></li>`).join("")
    || `<li><small>nic</small></li>`;
  ul.hidden = false;
}
$("#q").addEventListener("input", search);
$("#q").addEventListener("keydown", (ev) => {
  const items = [...$("#results").querySelectorAll("li[data-id]")];
  if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
    ev.preventDefault();
    resultIdx = Math.max(0, Math.min(items.length - 1, resultIdx + (ev.key === "ArrowDown" ? 1 : -1)));
    items.forEach((li, i) => li.classList.toggle("sel", i === resultIdx));
  } else if (ev.key === "Enter" && items[resultIdx]) {
    pick(items[resultIdx].dataset.id);
  } else if (ev.key === "Escape") { $("#results").hidden = true; }
});
$("#results").addEventListener("mousedown", (ev) => {
  const li = ev.target.closest("li[data-id]");
  if (li) { ev.preventDefault(); pick(li.dataset.id); }
});
$("#q").addEventListener("blur", () => setTimeout(() => ($("#results").hidden = true), 150));
function pick(id) {
  $("#results").hidden = true;
  openPerson(id, true);
}

// ------------------------------------------------------------------ panel osoby

function md(text, breaks) {
  if (!text) return "";
  // jednoduchá vlnovka = „přibližně“ (~1783), ne přeškrtnutí GFM — escapovat, `~~…~~` zůstává
  const src = text.replace(/(^|[^~\\])~(?!~)/g, "$1\\~");
  if (window.marked && window.DOMPurify) return `<div class="md">${DOMPurify.sanitize(marked.parse(src, { breaks: !!breaks }))}</div>`;
  return `<pre>${esc(text)}</pre>`;
}
const stripFm = (t) => (t && t.startsWith("---") ? t.replace(/^---[\s\S]*?\n---\s*\n/, "") : t);
const fileUrl = (p) => `/api/file?p=${encodeURIComponent(p)}`;
function det(key, summary, body, open) {
  const isOpen = openDetails.has(key) || (open && !openDetails.has("!" + key));
  return `<details data-key="${esc(key)}" ${isOpen ? "open" : ""}><summary>${summary}</summary>${body}</details>`;
}

async function openPerson(id, center) {
  selected = id;
  try { history.replaceState(null, "", "#" + id); } catch { /* nic */ }
  hit = null;
  if (center) {
    // rozbal sbalené předky, ať je osoba ve stromu vidět
    let p = structParent(id), changed = false;
    while (p) { if (collapsed.delete(p)) changed = true; p = structParent(p); }
    if (changed) store.set("collapsed", [...collapsed]);
    hit = id;
  }
  $("#panel").hidden = false;
  render();
  if (center) focusNode(id, 0.9);
  await loadPanel(id);
}

async function loadPanel(id) {
  const panel = $("#panel");
  let d;
  try { d = await (await fetch(`/api/person/${encodeURIComponent(id)}`)).json(); }
  catch { return; }
  if (selected !== id) return;
  const body = $("#panel-body");
  const scroll = panel.scrollTop;
  body.innerHTML = renderPerson(d);
  panel.hidden = false;
  panel.scrollTop = scroll;
  body.querySelectorAll("details[data-key]").forEach((dt) => dt.addEventListener("toggle", () => {
    const k = dt.dataset.key;
    if (dt.open) { openDetails.add(k); openDetails.delete("!" + k); } else { openDetails.delete(k); openDetails.add("!" + k); }
    if (dt.open && dt.dataset.lazy && !dt.dataset.loaded) loadLazy(dt);
  }));
  body.querySelectorAll("details[data-lazy][open]").forEach(loadLazy);
}

async function loadLazy(dt) {
  dt.dataset.loaded = "1";
  try {
    const t = await (await fetch(fileUrl(dt.dataset.lazy))).text();
    dt.querySelector(".lazy").innerHTML = dt.dataset.lazy.endsWith(".md") ? md(stripFm(t)) : `<pre>${esc(t)}</pre>`;
  } catch { dt.querySelector(".lazy").textContent = "nelze načíst"; }
}

function renderPerson(d) {
  const p = S.people[d.id];
  const id = d.id;
  const stav = p ? (p.stav || "bez dossieru") : "nesáhnuto";
  const ses = sessionOf(id) || d.session;
  const c = p && p.checklist;
  const facts = [
    `<span class="chip" style="background:${STATE_COLORS[p ? stav : ""] || "#fff"}">${esc(stav)}</span>`,
    `<span class="tag">${esc(id)}</span>`,
    p && years(p) ? `<span class="tag">${esc(years(p))}</span>` : "",
    p && p["původ"] ? `<span class="tag">původ: ${esc(p["původ"])}</span>` : "",
    ses ? `<span class="chip" title="${esc(sessionTip(ses, id))}"><b style="color:var(--run-${ses.status})">●</b> ${ses.kind === "vetev" ? "session větve" : "session"} ${esc(ses.name)}: ${esc(ses.status)}</span>` : "",
    d.gramps ? `<a href="${esc(d.gramps)}" target="_blank" rel="noopener">Gramps ↗</a>` : "",
  ].join(" ");
  const struct = [];
  const sp = structParent(id);
  if (sp) struct.push(`${esc(relLabel(id).split(" ")[0])} <span class="pid" data-pid="${sp}">${sp}</span>`);
  const chk = c ? `checklist: ${c.x} doloženo · ${c["~"]} slabé · ${c["-"]} nenalezeno · ${c.n} neexistuje · ${c[" "]} nehledáno` : "";
  const docs = p && p.docs ? `doklady: ${p.docs.open} chybí · ${p.docs.done} máme` : "";
  let h = `<h1>${esc(d.name || (p ? "(bez jména)" : "nesáhnuto"))}</h1>
    <div class="rel">${esc(d.rel || relLabel(id))}</div>
    <div class="facts">${facts}</div>
    <div class="facts"><small>${[chk, docs, p ? `odloženo: ${p.deferred || 0}` : "", p ? `log: ${p.log || 0}` : ""].filter(Boolean).join(" · ")}</small></div>
    <div class="facts"><small>${struct.join(" · ")}</small></div>`;
  if (d.abs_path) {
    h += `<div class="facts"><span class="path" id="abs">${esc(d.abs_path)}</span>
      <button onclick="navigator.clipboard.writeText(document.getElementById('abs').textContent).then(()=>this.textContent='zkopírováno')">kopírovat</button></div>`;
  } else {
    h += `<p><i>Osoba zatím nemá dossier — plyne ze struktury ID (${esc(relLabel(id))}).</i></p>`;
  }

  if (p && p.kontext_missing && p.kontext_missing.length) {
    h += `<div class="nokx-box">Chybí ${esc(p.kontext_missing.join(" a "))} — doplnit podle docs/metodika/pribehy.md (<code>kontext: chybí</code> v dossieru).</div>`;
  }
  if (d.zavora_text) {
    const z = p && p.zavora;
    h += `<h2 class="sec">Závora <small>${z ? esc(z.typy.join(" + ")) + (z.sance ? ` · šance ${esc(z.sance)}` : "") + (z.prolomeno ? ` · prolomeno ${esc(z.prolomeno)}` : "") : ""}</small></h2>`;
    h += `<div class="zavora${z && z.prolomeno ? " broken" : ""}">${md(d.zavora_text)}</div>`;
  }
  if (d.story) {
    const when = new Date(d.story.mtime * 1000).toLocaleDateString("cs-CZ");
    h += `<h2 class="sec">Příběh <small class="path">${esc(d.story.file)} · ${esc(when)}</small></h2>`;
    h += `<div class="story">${md(d.story.text, true)}</div>`;
  }
  if (d.kontext) {
    h += `<h2 class="sec">Kontext <small>(z dossieru — surové poznámky sessions)</small></h2><div class="kontext">${md(d.kontext)}</div>`;
  }
  if (d.kontroly && d.kontroly.length) {
    const rows = d.kontroly.map((k) => `<li><a href="#" data-kontrola="${esc(k.id)}">${esc(k.id)}</a>
      ${k.blokuje ? `<span class="tag block">blokuje</span>` : ""} <span class="tag">${esc(k.typ || "")}</span>
      <span class="kstav ${esc(k.stav)}">${esc(k.stav)}</span><br><small>${esc(k.otazka || "")}</small></li>`).join("");
    h += `<h2 class="sec">Kontroly (${d.kontroly.filter((k) => k.stav === "otevřeno").length} otevřeno)</h2><ul class="klist">${rows}</ul>`;
  }
  if (d.events && d.events.length) {
    const yr = (e) => { const m = String(e.date || "").match(/\d{4}/); return m ? +m[0] : 9999; };
    const rows = d.events.slice().sort((a, b) => yr(a) - yr(b)).map((e) => {
      const recs = e.records.map((r) => `${r.label}${r.confidence != null ? ` (jistota ${r.confidence})` : ""}${r.patch ? ` — ${r.patch}` : ""}`).join("\n");
      return `<tr class="${e.sources <= 1 ? "one" : ""}">
        <td>${esc(TYPE_CS[e.type] || e.type || "?")}${e.family ? " <small>(rodina)</small>" : ""}</td>
        <td>${esc(e.date)}</td><td>${esc(e.place)}</td>
        <td class="n" title="${esc(recs)}">${circled(e.sources)}${e.support ? ` <small title="rejstřík — podpůrně, nepočítá se">+R${e.support}</small>` : ""}</td>
        <td class="n">${e.confidence ?? "—"}</td>
        <td><small>${esc(trunc(e.description || "", 70))}</small></td></tr>`;
    }).join("");
    const one = d.events.filter((e) => e.sources <= 1).length;
    h += det("events", `Doložení údajů <small>(${d.events.length} událostí, ${one} s jediným pramenem; z aplikovaných patchů)</small>`,
      `<table class="evt"><thead><tr><th>událost</th><th>datum</th><th>místo</th><th title="počet nezávislých zápisů v citacích">pramenů</th><th title="nejvyšší jistota citace">jist.</th><th>popis</th></tr></thead><tbody>${rows}</tbody></table>
       <p><small>Pramen = různý zápis (dvě fotky téhož zápisu = jeden, rejstřík se nepočítá). Najetím na počet se ukážou zápisy.</small></p>`, true);
  }
  if (d.residences && d.residences.length) {
    const rows = d.residences.slice().sort((a, b) => a.year - b.year).map((r) =>
      `<li>${r.year}${r.year_to ? `–${r.year_to}` : ""} · ${esc(r.place)} čp. ${esc(r.cp)}${r.undetermined ? ` <small class="warn">${esc(r.undetermined)}</small>` : ""} <small>(${esc(TYPE_CS[r.type] || r.type)}, ${esc(r.patch)})</small>
       <a href="#" data-showmap="${esc(r.place)}|${esc(r.cp)}|${r.year}">na mapě</a></li>`).join("");
    h += `<h2 class="sec">Bydliště (z patchů)</h2><ul>${rows}</ul>`;
  }
  if (d.patches.length) {
    h += `<h2 class="sec">Patche (${d.patches.length})</h2>`;
    for (const pt of d.patches) {
      const waiting = ["navrženo", "schváleno"].includes(pt.status);
      h += det(`patch:${pt.file}`, `<span class="status ${esc(pt.status)}">${esc(pt.status)}</span> ${esc(pt.file)}<br><small>${esc(pt.summary)}</small>`,
        `<div class="path">${esc(pt.path)}</div><pre>${esc(pt.text)}</pre>`, waiting);
    }
  }
  if (d.hints.length) {
    h += `<h2 class="sec">Nápovědy (${d.hints.length})</h2>`;
    for (const x of d.hints) h += det(`hint:${x.file}`, `${esc(x.file.split("/").pop())}`, md(x.text), false);
  }
  if (d.todos.length) {
    h += `<h2 class="sec">Sdílené seznamy (${d.todos.length})</h2>`;
    for (const t of d.todos) {
      const st = t.state ? ` <small>— ${esc(t.state)}</small>` : "";
      h += det(`todo:${t.list}:${t.title}`, `${esc(t.list_title)}: ${esc(trunc(t.title, 90))}${st}`, md(t.text), t.open);
    }
  }
  if (d.dossier) {
    h += `<h2 class="sec">Dossier</h2>`;
    h += det("dossier", `${esc(d.file)}`, md(stripFm(d.dossier)), true);
  }
  const s = d.sources;
  if (s && (s.sidecars.length || s.images.length || s.texts.length)) {
    h += `<h2 class="sec">Prameny${s.dir ? ` <small class="path">${esc(s.dir)}/</small>` : ""}</h2>`;
    if (s.sidecars.length) {
      const items = s.sidecars.map((x) => {
        const img = x.image ? `<img loading="lazy" src="${fileUrl(x.image)}" data-full="${esc(x.image)}" alt="">` : "";
        const links = [x.url ? `<a href="${esc(x.url)}" target="_blank" rel="noopener">snímek ↗</a>` : "",
                       x.volume_url ? `<a href="${esc(x.volume_url)}" target="_blank" rel="noopener">svazek ↗</a>` : "",
                       x.transcription ? `<a href="${fileUrl(x.transcription)}" target="_blank" rel="noopener">přepis</a>` : "",
                       `<a href="${fileUrl(x.path)}" target="_blank" rel="noopener">sidecar</a>`].filter(Boolean).join(" · ");
        const other = !x.own ? `<span class="tag">ze složky ${esc(x.path.split("/")[1])}</span> ` : "";
        return `<div class="src">${img}<div class="info">
          <div>${other}<b>${esc(x.type || "")}</b> ${x.confidence != null ? `<span class="tag">jistota ${esc(x.confidence)}</span>` : ""}</div>
          ${x.entry ? `<div>${esc(x.entry)}</div>` : ""}
          ${x.document ? `<div>${esc(x.document)}</div>` : ""}
          <div><small>${esc([x.archive, x.volume, x.folio].filter(Boolean).join(", "))}</small></div>
          ${x.persons.length ? `<div><small>osoby: ${x.persons.map((q) => `<span class="pid" data-pid="${q}">${q}</span>`).join(" ")}</small></div>` : ""}
          <div>${links}</div></div></div>`;
      }).join("");
      h += det("src:sidecars", `Záznamy se sidecarem <small>(${s.sidecars.length})</small>`, items, true);
    }
    if (s.images.length) {
      h += det("src:images", `Snímky bez sidecaru <small>(${s.images.length})</small>`,
        `<div class="thumbs">${s.images.map((i) => `<img loading="lazy" src="${fileUrl(i)}" data-full="${esc(i)}" title="${esc(i)}" alt="">`).join("")}</div>`, false);
    }
    for (const t of s.texts) {
      const key = `txt:${t}`;
      const isOpen = openDetails.has(key);
      h += `<details data-key="${esc(key)}" data-lazy="${esc(t)}" ${isOpen ? "open" : ""}><summary>${esc(t.split("/").pop())} <small>${esc(t)}</small></summary><div class="lazy">načítám…</div></details>`;
    }
  }
  return h;
}

$("#close").addEventListener("click", closePanel);
function closePanel() { $("#panel").hidden = true; selected = null; hit = null; render(); }
document.addEventListener("keydown", (ev) => {
  if (ev.key !== "Escape") return;
  if (!$("#lightbox").hidden) { $("#lightbox").hidden = true; return; }
  if (document.activeElement !== $("#q")) closePanel();
});
$("#panel").addEventListener("click", (ev) => {
  const img = ev.target.closest("img[data-full]");
  if (!img) return;
  const lb = $("#lightbox");
  lb.querySelector("img").src = fileUrl(img.dataset.full);
  lb.querySelector("a").href = fileUrl(img.dataset.full);
  lb.hidden = false;
});
$("#lightbox").addEventListener("click", (ev) => { if (ev.target.tagName !== "A") $("#lightbox").hidden = true; });

// ------------------------------------------------------------------ filtry, polling

for (const f of ["f-work", "f-wait", "f-empty", "f-single", "f-nokx"]) {
  const box = $("#" + f);
  box.checked = store.get(f, box.checked);
  box.addEventListener("change", () => { store.set(f, box.checked); render(); });
}
$("#fit").addEventListener("click", fit);

async function poll() {
  try {
    const r = await fetch(`/api/state${S ? `?v=${S.version}` : ""}`);
    const st = await r.json();
    $("#live").classList.remove("stale");
    $("#live").title = `živě — naposledy ${new Date().toLocaleTimeString("cs-CZ")}`;
    if (!st.unchanged) {
      S = st;
      if (window.onStateChange) window.onStateChange();
      renderOverview();
      renderLegend();
      render();
      if (firstRender) {
        firstRender = false;
        const r0 = $("#svg").getBoundingClientRect();
        const root = nodes.get("K0001");
        if (root) { T.k = 0.8; T.x = 30 - root.x * T.k; T.y = r0.height / 2 - (root.y + BH / 2) * T.k; applyTransform(); }
        const want = location.hash.slice(1);
        if (want && /^K\d+/.test(want)) openPerson(want, true);
      } else if (selected && !$("#panel").hidden) {
        loadPanel(selected);
      }
    }
  } catch {
    $("#live").classList.add("stale");
    $("#live").title = "server neodpovídá";
  }
  setTimeout(poll, POLL_MS);
}
poll();
window.addEventListener("hashchange", () => {
  const want = location.hash.slice(1);
  if (S && /^K\d+/.test(want) && want !== selected) openPerson(want, true);
});
