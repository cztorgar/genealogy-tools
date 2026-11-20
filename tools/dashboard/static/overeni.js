// Workbench dashboard — seznam k ověření proti snímku (research/todo-overeni.md) a verdikt „sedí / nesedí“.
"use strict";

const ovFilters = { stav: store.get("ov-stav", "otevřeno"), osoba: "" };
const ovDrafts = new Map();   // id → {note, msg}
const ovJust = new Set();     // zapsané v této relaci zůstanou vidět i ve filtru „otevřené“
let ovSig = "";

function ovStav(s) {
  if (s.verdikt === "sedí") return "potvrzeno";
  if (s.verdikt === "nesedí") return "nesedí";
  return s.open ? "otevřeno" : "hotovo";
}

function updateOvCount() {
  const n = ((S && S.overeni) || []).filter((s) => s.open).length;
  $("#ov-count").innerHTML = n ? `<b class="kcnt" title="${n} zápisů čeká na porovnání se snímkem">${n}</b>` : "";
}

function fillOvFilters(list) {
  const box = $("#ovf-osoba"), cur = box.value;
  const ids = [...new Set(list.flatMap((s) => s.osoby))].sort();
  box.innerHTML = `<option value="">všechny</option>` +
    ids.map((v) => `<option value="${esc(v)}">${esc(v)} ${esc((S.people[v] || {}).name || "")}</option>`).join("");
  box.value = ids.includes(cur) ? cur : "";
  $("#ovf-stav").value = ovFilters.stav;
}

function renderOv(s) {
  const dr = ovDrafts.get(s.id) || {};
  const st = ovStav(s);
  const img = s.vyrez;
  const links = [s.snimek && s.snimek !== s.vyrez ? `<a href="#" data-full-link="${esc(s.snimek)}">celý snímek</a>` : "",
    s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">portál ↗</a>` : ""].filter(Boolean).join(" · ");
  const shot = img ? `<div class="kshot"><img src="${fileUrl(img)}" data-full="${esc(img)}" alt="výřez" title="zvětšit">
      <div class="links">${links}</div></div>`
    : `<div class="kshot"><div class="miss">snímek není uložený</div><div class="links">${links}</div></div>`;
  const people = s.osoby.map((id) => `<span class="pid" data-pid="${esc(id)}" title="${esc((S.people[id] || {}).name || "")}">${esc(id)}</span>`).join(" ");
  const form = s.open || dr.reopen ? `<div class="kform">
      <textarea data-ovnote rows="2" placeholder="poznámka — u „nesedí“ napiš, co je na snímku jinak">${esc(dr.note || "")}</textarea>
      <div><button data-ov="sedí" class="primary">Sedí</button> <button data-ov="nesedí">Nesedí</button>
      <span class="kmsg">${esc(dr.msg || "")}</span></div></div>`
    : `<div class="kdec">${s.verdikt ? `Tvůj verdikt: <b>${esc(s.verdikt)}</b>${s.poznamka ? ` — ${esc(s.poznamka)}` : ""}
        <br><small>${esc(s.stav)}</small> <button data-ovreopen>změnit</button>` : `<small>${esc(s.stav)}</small>`}
        ${dr.msg ? `<span class="kmsg">${esc(dr.msg)}</span>` : ""}</div>`;
  return `<article class="kontrola overeni ${s.verdikt ? "rozhodnuto" : s.open ? "otevřeno" : "zapracováno"}" id="ov-${esc(s.id)}" data-ov-id="${esc(s.id)}">
    <header><span class="kstav ${st === "potvrzeno" ? "rozhodnuto" : st === "nesedí" ? "zamítnuto" : st === "hotovo" ? "zapracováno" : "otevřeno"}">${esc(st)}</span> ${people}</header>
    <h3>${esc(s.title)}</h3>
    <div class="kmain">${shot}<div class="kright">
      <ul class="ovlist">${s.overit.map((o) => `<li>${esc(o)}</li>`).join("")}</ul>
      ${form}
    </div></div>
  </article>`;
}

function renderOverovani(force) {
  updateOvCount();
  if (!S || $("#overeniwrap").hidden) return;
  const list = S.overeni || [];
  const sig = JSON.stringify([list, ovFilters]);
  if (!force && sig === ovSig) return;
  const active = document.activeElement && document.activeElement.closest?.("#ov-list") ? document.activeElement : null;
  if (active && !force) return;
  ovSig = sig;
  fillOvFilters(list);
  const shown = list.filter((s) => (!ovFilters.stav || ovStav(s) === ovFilters.stav || ovJust.has(s.id))
                                   && (!ovFilters.osoba || s.osoby.includes(ovFilters.osoba)));
  const open = list.filter((s) => s.open).length;
  const conf = list.filter((s) => s.verdikt === "sedí").length, bad = list.filter((s) => s.verdikt === "nesedí").length;
  $("#ov-summary").textContent = `${open} k porovnání · ${conf} sedí · ${bad} nesedí (obojí čeká na managera) · zobrazeno ${shown.length} z ${list.length}`;
  $("#ov-list").innerHTML = shown.slice().reverse().map(renderOv).join("")
    || `<p class="empty">${list.length ? "Filtru nic neodpovídá." : "Seznam research/todo-overeni.md je prázdný."}</p>`;
}
window.renderOverovani = renderOverovani;

$("#ov-list").addEventListener("input", (ev) => {
  const art = ev.target.closest("[data-ov-id]");
  if (art && ev.target.matches("[data-ovnote]")) {
    const d = ovDrafts.get(art.dataset.ovId) || {}; d.note = ev.target.value; ovDrafts.set(art.dataset.ovId, d);
  }
});

$("#ov-list").addEventListener("click", async (ev) => {
  const full = ev.target.closest("img[data-full], [data-full-link]");
  if (full) {
    ev.preventDefault();
    const f = full.dataset.full || full.dataset.fullLink, lb = $("#lightbox");
    lb.querySelector("img").src = fileUrl(f); lb.querySelector("a").href = fileUrl(f); lb.hidden = false;
    return;
  }
  const art = ev.target.closest("[data-ov-id]"); if (!art) return;
  const id = art.dataset.ovId;
  if (ev.target.closest("[data-ovreopen]")) { ovDrafts.set(id, { ...(ovDrafts.get(id) || {}), reopen: true }); renderOverovani(true); return; }
  const btn = ev.target.closest("[data-ov]"); if (!btn) return;
  const note = art.querySelector("[data-ovnote]")?.value || "";
  const msg = art.querySelector(".kmsg");
  if (btn.dataset.ov === "nesedí" && !note.trim()) { msg.textContent = "napiš do poznámky, co nesedí"; return; }
  art.querySelectorAll("[data-ov]").forEach((b) => (b.disabled = true)); msg.textContent = "zapisuji…";
  try {
    const r = await fetch(`/api/overeni/${encodeURIComponent(id)}`, {
      method: "POST", headers: { "Content-Type": "application/json", "X-Dashboard-Token": TOKEN },
      body: JSON.stringify({ verdikt: btn.dataset.ov, poznamka: note }),
    });
    const res = await r.json();
    if (!r.ok) { msg.textContent = `nezapsáno: ${res.error || r.status}`; art.querySelectorAll("[data-ov]").forEach((b) => (b.disabled = false)); return; }
    ovJust.add(id);
    ovDrafts.set(id, { msg: "zapsáno · manager zvedne jistotu" });
    const s = S.overeni.find((x) => x.id === id);
    if (s) { s.verdikt = res.verdikt; s.stav = res.stav; s.open = false; s.poznamka = note.trim(); }
    if (document.activeElement) document.activeElement.blur();
    renderOverovani(true);
  } catch (e) {
    msg.textContent = "server neodpovídá"; art.querySelectorAll("[data-ov]").forEach((b) => (b.disabled = false));
  }
});

for (const [id, key] of [["#ovf-stav", "stav"], ["#ovf-osoba", "osoba"]]) {
  $(id).addEventListener("change", () => {
    ovFilters[key] = $(id).value;
    ovJust.clear();
    if (key === "stav") store.set("ov-stav", ovFilters.stav);
    renderOverovani(true);
  });
}

{
  const prev = window.onStateChange;
  window.onStateChange = () => { if (prev) prev(); renderOverovani(); };
  if (store.get("tab", "strom") === "overeni") setTab("overeni");
}
