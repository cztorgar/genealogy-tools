// Workbench dashboard — přehled listin (sources/**/*.yml) a historie domů (research/domy + události s č. p.).
"use strict";

const LF = { typ: store.get("lf-typ", ""), osoba: "", q: "" };
const DF = { obec: store.get("df-obec", ""), q: "", open: store.get("df-open", "") };
let lSig = "", dSig = "";
const ROLE_ORDER = ["vlastník", "chalupník", "výminek", "narození", "bydliště", "sčítání", "povolání", "držba", "úmrtí"];

const pidLink = (id) => id ? `<span class="pid" data-pid="${esc(id)}" title="${esc((S.people[id] || {}).name || "")}">${esc(id)}</span>` : "";
const fileLink = (f, label) => `<a href="${fileUrl(f)}" target="_blank" rel="noopener">${esc(label || f.split("/").pop())}</a>`;
const isImg = (f) => /\.(jpe?g|png|gif|webp|tiff?)$/i.test(f);
const span = (od, d) => od || d ? `${od ?? "?"}–${d ?? ""}` : "";

// ------------------------------------------------------------------ listiny

function listinaCard(l, compact) {
  const thumb = (l.crops[0] || l.files.find(isImg));
  const files = l.files.map((f) => fileLink(f)).concat(l.crops.map((f) => fileLink(f, "výřez")));
  if (l.url) files.push(`<a href="${esc(l.url)}" target="_blank" rel="noopener">portál ↗</a>`);
  files.push(fileLink(l.file, "sidecar"));
  return `<article class="listina" data-lfile="${esc(l.file)}">
    ${thumb && !compact ? `<img class="lthumb" src="${fileUrl(thumb)}" data-full="${esc(thumb)}" alt="" loading="lazy">` : ""}
    <div class="lbody">
      <div class="lhead"><span class="tag">${esc(l.type)}</span> ${l.year ? `<b>${l.year}${l.years.length > 1 ? `–${l.years[l.years.length - 1]}` : ""}</b>` : ""}
        <b>${esc(l.title)}</b></div>
      ${l.entry ? `<div class="lentry">${esc(compact ? l.entry.slice(0, 220) + (l.entry.length > 220 ? "…" : "") : l.entry)}</div>` : ""}
      ${l.persons.length ? `<div class="lpers">${l.persons.map(pidLink).join(" ")}</div>` : ""}
      <div class="links">${files.join(" · ")}</div>
    </div>
  </article>`;
}

function renderListiny(force) {
  if (!S || $("#listinywrap").hidden) return;
  const all = S.listiny || [];
  const sig = JSON.stringify([all.length, S.version, LF]);
  if (!force && sig === lSig) return;
  lSig = sig;
  const types = [...new Set(all.map((l) => l.type))].sort();
  $("#lf-typ").innerHTML = `<option value="">všechny (${all.length})</option>` +
    types.map((t) => `<option value="${esc(t)}">${esc(t)} (${all.filter((l) => l.type === t).length})</option>`).join("");
  $("#lf-typ").value = LF.typ;
  const ids = [...new Set(all.flatMap((l) => l.persons))].sort();
  const cur = $("#lf-osoba").value;
  $("#lf-osoba").innerHTML = `<option value="">všechny</option>` + ids.map((v) => `<option value="${esc(v)}">${esc(v)} ${esc((S.people[v] || {}).name || "")}</option>`).join("");
  $("#lf-osoba").value = ids.includes(cur) ? cur : "";
  LF.osoba = $("#lf-osoba").value;
  const q = foldPlace(LF.q);
  const shown = all.filter((l) => (!LF.typ || l.type === LF.typ) && (!LF.osoba || l.persons.includes(LF.osoba))
    && (!q || foldPlace(`${l.title} ${l.entry} ${l.text} ${l.file}`).includes(q)));
  $("#l-summary").textContent = `zobrazeno ${shown.length} z ${all.length}`;
  $("#l-list").innerHTML = shown.map((l) => listinaCard(l)).join("") || `<p class="empty">Nic neodpovídá filtru.</p>`;
}
window.renderListiny = renderListiny;

// ------------------------------------------------------------------ domy

function houseRow(h) {
  const n = h.persons.length;
  return `<li class="dum ${DF.open === h.key ? "on" : ""}" data-dum="${esc(h.key)}">
    <b>${esc(h.obec)} č. ${esc(h.cp)}</b> <small>${span(h.od, h.do)}</small><br>
    <small>${n} osob · ${h.events.length} událostí${h.drzba.length ? ` · ${h.drzba.length} držba` : ""} · ${h.listiny.length} listin${h.file ? " · ✎" : ""}</small></li>`;
}

function houseDetail(h) {
  const byFile = Object.fromEntries((S.listiny || []).map((l) => [l.file, l]));
  const drz = h.drzba.length ? `<h3>Držba a výminky</h3><table class="dtab"><tr><th>od–do</th><th>role</th><th>kdo</th><th>poznámka · pramen</th></tr>
    ${h.drzba.map((d) => `<tr class="r-${esc(d.role)}"><td>${span(d.od, d.do)}</td><td>${esc(d.role)}</td>
      <td>${d.kdo.map((k) => k.id ? `${pidLink(k.id)} ${esc(k.name)}` : esc(k.name)).join("<br>")}</td>
      <td>${esc(d.pozn)}${d.pramen ? `<br><small>${fileLink(d.pramen, byFile[d.pramen] ? byFile[d.pramen].title : d.pramen)}</small>` : ""}</td></tr>`).join("")}</table>` : "";
  // lidé: kdo se tu narodil, zemřel, žil — souhrn po osobách
  const per = {};
  for (const e of h.events) {
    const p = per[e.id] || (per[e.id] = { id: e.id, name: e.name || (S.people[e.id] || {}).name || "", roles: new Set(), from: null, to: null });
    p.roles.add(e.role);
    const y1 = e.year, y2 = e.year_to || e.year;
    if (y1) { p.from = p.from == null ? y1 : Math.min(p.from, y1); p.to = p.to == null ? y2 : Math.max(p.to, y2); }
  }
  const people = Object.values(per).sort((a, b) => (a.from ?? 9999) - (b.from ?? 9999));
  const lidi = people.length ? `<h3>Kdo tu byl</h3><table class="dtab"><tr><th>osoba</th><th>doloženo</th><th>role</th></tr>
    ${people.map((p) => `<tr><td>${pidLink(p.id)} ${esc(p.name)}</td><td>${span(p.from, p.to !== p.from ? p.to : null) || p.from || ""}</td>
      <td>${[...p.roles].sort((a, b) => ROLE_ORDER.indexOf(a) - ROLE_ORDER.indexOf(b)).map((r) => `<span class="role r-${esc(r)}">${esc(r)}</span>`).join(" ")}</td></tr>`).join("")}</table>` : "";
  const tl = h.events.length ? `<h3>Časová osa</h3><table class="dtab"><tr><th>datum</th><th>osoba</th><th>událost</th><th>popis</th></tr>
    ${h.events.map((e) => `<tr><td>${esc(e.date)}</td><td>${pidLink(e.id)} ${esc(e.name || (S.people[e.id] || {}).name || "")}</td>
      <td><span class="role r-${esc(e.role)}">${esc(e.role)}</span></td><td><small>${esc(e.desc)}</small></td></tr>`).join("")}</table>` : "";
  const ls = h.listiny.length ? `<h3>Listiny (${h.listiny.length})</h3>${h.listiny.map((f) => byFile[f] ? listinaCard(byFile[f], true) : `<p>${fileLink(f)}</p>`).join("")}` : "";
  return `<h2>${esc(h.obec)} č. ${esc(h.cp)}</h2>
    ${h.nazev ? `<p><b>${esc(h.nazev)}</b></p>` : ""}${h.popis ? `<p>${esc(h.popis)}</p>` : ""}
    <p class="frhelp">${h.file ? `Ručně vedená historie: ${fileLink(h.file)}. ` : `Doplnit držbu a výminky: založ <code>research/domy/${esc(h.key)}.yml</code> (vzor v research/domy/README.md). `}Události se berou z patchů automaticky.</p>
    ${drz}${lidi}${tl}${ls}`;
}

function renderDomy(force) {
  if (!S || $("#domywrap").hidden) return;
  const all = S.domy || [];
  const sig = JSON.stringify([S.version, DF]);
  if (!force && sig === dSig) return;
  dSig = sig;
  const obce = [...new Set(all.map((h) => h.obec))].sort((a, b) => a.localeCompare(b, "cs"));
  $("#df-obec").innerHTML = `<option value="">všechny (${all.length})</option>` + obce.map((o) => `<option>${esc(o)}</option>`).join("");
  $("#df-obec").value = obce.includes(DF.obec) ? DF.obec : "";
  const q = foldPlace(DF.q);
  const shown = all.filter((h) => (!DF.obec || h.obec === DF.obec)
    && (!q || foldPlace(`${h.obec} ${h.cp} ${h.nazev} ${h.events.map((e) => e.name).join(" ")}`).includes(q)));
  $("#d-summary").textContent = `${shown.length} domů`;
  $("#d-list").innerHTML = shown.map(houseRow).join("") || `<li class="empty">nic</li>`;
  const h = all.find((x) => x.key === DF.open) || shown[0];
  $("#d-detail").innerHTML = h ? houseDetail(h) : `<p class="empty">Žádný dům.</p>`;
  if (h) $("#d-list").querySelector(`[data-dum="${CSS.escape(h.key)}"]`)?.classList.add("on");
}
window.renderDomy = renderDomy;

// ------------------------------------------------------------------ ovládání

$("#lf-typ").addEventListener("change", () => { LF.typ = $("#lf-typ").value; store.set("lf-typ", LF.typ); renderListiny(true); });
$("#lf-osoba").addEventListener("change", () => { LF.osoba = $("#lf-osoba").value; renderListiny(true); });
$("#lf-q").addEventListener("input", () => { LF.q = $("#lf-q").value; renderListiny(true); });
$("#df-obec").addEventListener("change", () => { DF.obec = $("#df-obec").value; store.set("df-obec", DF.obec); renderDomy(true); });
$("#df-q").addEventListener("input", () => { DF.q = $("#df-q").value; renderDomy(true); });
$("#d-list").addEventListener("click", (ev) => {
  const li = ev.target.closest("[data-dum]"); if (!li) return;
  DF.open = li.dataset.dum; store.set("df-open", DF.open); renderDomy(true);
});
for (const box of ["#l-list", "#d-detail"]) {
  $(box).addEventListener("click", (ev) => {
    const full = ev.target.closest("img[data-full]");
    if (!full) return;
    const lb = $("#lightbox"), f = full.dataset.full;
    lb.querySelector("img").src = fileUrl(f); lb.querySelector("a").href = fileUrl(f); lb.hidden = false;
  });
}

{
  const prev = window.onStateChange;
  window.onStateChange = () => { if (prev) prev(); renderListiny(); renderDomy(); };
  const t0 = store.get("tab", "strom");
  if (t0 === "listiny" || t0 === "domy") setTab(t0);
}
