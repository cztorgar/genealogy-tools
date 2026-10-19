// Workbench dashboard — fronta kontrol (research/kontroly/*.yml) a zápis rozhodnutí.
"use strict";

const TOKEN = document.querySelector('meta[name="dashboard-token"]').content;
const KTYP_CS = { cteni: "čtení", totoznost: "totožnost", rozpor: "rozpor", nastroj: "nástroj", vzorek: "vzorek", jine: "jiné" };
const drafts = new Map();   // id → {pick, own, note} — rozepsané rozhodnutí přežije překreslení
let kSig = "";
const justDecided = new Set();   // rozhodnuté v této relaci zůstanou vidět i ve filtru „otevřené“

const kFilters = { stav: store.get("kf-stav", "otevřeno"), osoba: "", typ: "" };

function kStavMatch(k, f) {
  if (!f) return true;
  if (f === "hotovo") return ["zapracováno", "zamítnuto"].includes(k.stav);
  return k.stav === f;
}

function updateKCount() {
  const ks = (S && S.kontroly) || [];
  const open = ks.filter((k) => k.stav === "otevřeno");
  const block = open.filter((k) => k.blokuje).length;
  $("#k-count").innerHTML = open.length
    ? `<b class="kcnt ${block ? "block" : ""}" title="${open.length} otevřených, ${block} blokujících">${open.length}${block ? ` · ${block}!` : ""}</b>`
    : "";
}

function fillKFilters(ks) {
  const sel = (id, values, label) => {
    const box = $(id), cur = box.value;
    box.innerHTML = `<option value="">všechny</option>` + values.map((v) => `<option value="${esc(v)}">${esc(label(v))}</option>`).join("");
    box.value = values.includes(cur) ? cur : "";
  };
  sel("#kf-osoba", [...new Set(ks.map((k) => k.osoba || "G"))].sort(),
      (v) => (v === "G" ? "obecné (G-)" : `${v} ${(S.people[v] || {}).name || ""}`));
  sel("#kf-typ", [...new Set(ks.map((k) => k.typ || "jine"))].sort(), (v) => KTYP_CS[v] || v);
  $("#kf-stav").value = kFilters.stav;
}

function isRecommended(k, v) {
  const d = String(k.doporuceni || "").toLowerCase(), w = String(v.volba || "").toLowerCase().split(" (")[0].trim();
  return w && d.startsWith(w);
}

function renderK(k) {
  const dr = drafts.get(k.id) || {};
  const decided = k.rozhodnuti && typeof k.rozhodnuti === "object" ? k.rozhodnuti : null;
  const editable = ["otevřeno", "rozhodnuto"].includes(k.stav) && !k.error;
  const editing = editable && (k.stav === "otevřeno" || dr.reopen);
  let pick = dr.pick;
  if (pick === undefined && decided) {
    const i = k.varianty.findIndex((v) => v.volba === decided.volba);
    pick = i >= 0 ? String(i) : "own";
  }
  const own = dr.own ?? (decided && pick === "own" ? decided.volba : "");
  const note = dr.note ?? (decided ? decided.poznamka || "" : "");
  const p = k.osoba ? S.people[k.osoba] : null;

  const head = `<header>
    <b>${esc(k.id)}</b>
    ${k.osoba ? `<span class="pid" data-pid="${esc(k.osoba)}">${esc(k.osoba)}</span> ${esc(p ? p.name : "")}` : `<span class="tag">obecná</span>`}
    <span class="tag">${esc(KTYP_CS[k.typ] || k.typ || "?")}</span>
    ${k.blokuje ? `<span class="tag block">blokuje</span>` : ""}
    <span class="tag">priorita ${esc(k.priorita)}</span>
    <span class="kstav ${esc(k.stav)}">${esc(k.stav)}</span>
    <small>${esc([k.vzniklo && k.vzniklo.kdo, k.vzniklo_kdy].filter(Boolean).join(", "))} · <a href="${fileUrl(k.file)}" target="_blank" rel="noopener">${esc(k.file)}</a></small>
  </header>`;

  const img = k.vyrez || k.snimek;
  const portal = k.url ? `<a href="${esc(k.url)}" target="_blank" rel="noopener">portál ↗</a>` : "";
  const shot = img ? `<div class="kshot">
      ${k[(k.vyrez ? "vyrez" : "snimek") + "_chybi"] ? `<div class="miss">soubor ${esc(img)} chybí</div>`
        : `<img src="${fileUrl(img)}" data-full="${esc(img)}" alt="výřez" title="zvětšit">`}
      <div class="links">${[k.vyrez && k.snimek ? `<a href="#" data-full-link="${esc(k.snimek)}">celý snímek</a>` : "",
        portal].filter(Boolean).join(" · ")}</div>
    </div>` : portal ? `<div class="kshot"><div class="miss">snímek není stažený — otevři na portálu</div>
      <div class="links">${portal}</div></div>` : "";

  const vars = k.varianty.map((v, i) => `<label class="var ${isRecommended(k, v) ? "rec" : ""} ${String(i) === pick ? "on" : ""}">
      <input type="radio" name="v-${esc(k.id)}" value="${i}" ${String(i) === pick ? "checked" : ""} ${editing ? "" : "disabled"}>
      <b>${esc(v.volba)}</b>${isRecommended(k, v) ? ` <span class="star" title="doporučení session">★</span>` : ""}
      ${v.opora ? `<small>${esc(v.opora)}</small>` : ""}
      ${v.cteni || v["ctení"] ? `<small class="who">čtení: ${esc(v.cteni || v["ctení"])}</small>` : ""}
    </label>`).join("") + (editing || pick === "own" ? `<label class="var own ${pick === "own" ? "on" : ""}">
      <input type="radio" name="v-${esc(k.id)}" value="own" ${pick === "own" ? "checked" : ""} ${editing ? "" : "disabled"}>
      <b>vlastní</b><textarea data-own rows="2" placeholder="vlastní znění" ${editing ? "" : "disabled"}>${esc(own)}</textarea></label>` : "");

  const form = editing ? `<div class="kform">
      <textarea data-note rows="2" placeholder="poznámka (nepovinná) — proč, co jsem na snímku viděl">${esc(note)}</textarea>
      <div><button data-decide="${esc(k.id)}" class="primary">Zapsat rozhodnutí</button>
      ${dr.reopen ? `<button data-cancel="${esc(k.id)}">zrušit</button>` : ""}
      <span class="kmsg">${esc(dr.msg || "")}</span></div></div>` : "";

  const dec = decided ? `<div class="kdec">Rozhodnuto: <b>${esc(decided.volba)}</b>${decided.poznamka ? ` — ${esc(decided.poznamka)}` : ""}
      <small>(${esc(decided.kdo || "")} ${esc(decided.kdy || "")})</small>
      ${k.zapracovano ? `<br><small>zapracováno: ${esc(typeof k.zapracovano === "object" ? [k.zapracovano.patch, k.zapracovano.kdy].filter(Boolean).join(", ") : k.zapracovano)}</small>`
        : `<br><small>čeká na zapracování (session osoby nebo manager)</small>`}
      ${editable && !editing ? ` <button data-reopen="${esc(k.id)}">změnit</button>` : ""}
      ${dr.msg && !editing ? `<span class="kmsg">${esc(dr.msg)}</span>` : ""}</div>` : "";

  const rel = k.souvisi.length ? `<div class="ksouvisi"><small>souvisí: ${k.souvisi.map((f) =>
      `<a href="${fileUrl(f)}" target="_blank" rel="noopener">${esc(f)}</a>`).join(" · ")}</small></div>` : "";

  return `<article class="kontrola ${k.blokuje ? "blok" : ""} ${esc(k.stav)}" id="k-${esc(k.id)}" data-k="${esc(k.id)}">
    ${head}
    <h3>${esc(k.otazka || "(bez otázky)")}</h3>
    ${k.error ? `<p class="miss">${esc(k.error)}</p>` : ""}
    <div class="kmain">${shot}<div class="kright">
      ${k.kontext ? md(String(k.kontext)) : ""}
      ${k.varianty.length || editing ? `<div class="vars">${vars}</div>` : ""}
      ${k.doporuceni ? `<div class="krec">Doporučení: ${esc(k.doporuceni)}</div>` : ""}
      ${dec}${form}${rel}
    </div></div>
  </article>`;
}

function renderKontroly(force) {
  updateKCount();
  if (!S || $("#kontrolywrap").hidden) return;
  const ks = S.kontroly || [];
  const sig = JSON.stringify([ks, kFilters]);
  if (!force && sig === kSig) return;
  const active = document.activeElement && document.activeElement.closest?.("#k-list") ? document.activeElement : null;
  if (active && !force) return;   // uživatel zrovna píše — překreslí se při dalším pollu
  kSig = sig;
  fillKFilters(ks);
  const shown = ks.filter((k) => (kStavMatch(k, kFilters.stav) || justDecided.has(k.id)) && (!kFilters.osoba || (k.osoba || "G") === kFilters.osoba)
                                   && (!kFilters.typ || (k.typ || "jine") === kFilters.typ));
  const open = ks.filter((k) => k.stav === "otevřeno");
  $("#k-summary").textContent = `${open.length} otevřeno, z toho ${open.filter((k) => k.blokuje).length} blokujících · zobrazeno ${shown.length} z ${ks.length}`;
  $("#k-list").innerHTML = shown.map(renderK).join("")
    || `<p class="empty">${ks.length ? "Filtru nic neodpovídá." : "Fronta je prázdná — research/kontroly/ neobsahuje žádnou kontrolu."}</p>`;
}
window.renderKontroly = renderKontroly;

function draftOf(id) { if (!drafts.has(id)) drafts.set(id, {}); return drafts.get(id); }

$("#k-list").addEventListener("input", (ev) => {
  const art = ev.target.closest("[data-k]"); if (!art) return;
  const d = draftOf(art.dataset.k);
  if (ev.target.matches("[data-own]")) {
    d.own = ev.target.value; d.pick = "own";
    const r = art.querySelector('input[value="own"]'); if (r) r.checked = true;
  }
  if (ev.target.matches("[data-note]")) d.note = ev.target.value;
});
$("#k-list").addEventListener("change", (ev) => {
  const art = ev.target.closest("[data-k]"); if (!art || ev.target.type !== "radio") return;
  draftOf(art.dataset.k).pick = ev.target.value;
  art.querySelectorAll(".var").forEach((l) => l.classList.toggle("on", l.contains(ev.target)));
});
$("#k-list").addEventListener("click", async (ev) => {
  const full = ev.target.closest("img[data-full], [data-full-link]");
  if (full) {
    ev.preventDefault();
    const f = full.dataset.full || full.dataset.fullLink;
    const lb = $("#lightbox");
    lb.querySelector("img").src = fileUrl(f); lb.querySelector("a").href = fileUrl(f); lb.hidden = false;
    return;
  }
  const re = ev.target.closest("[data-reopen]");
  if (re) { draftOf(re.dataset.reopen).reopen = true; renderKontroly(true); return; }
  const ca = ev.target.closest("[data-cancel]");
  if (ca) { drafts.delete(ca.dataset.cancel); renderKontroly(true); return; }
  const btn = ev.target.closest("[data-decide]");
  if (btn) decide(btn.dataset.decide, btn);
});

async function decide(id, btn) {
  const k = (S.kontroly || []).find((x) => x.id === id);
  const d = draftOf(id);
  const art = btn.closest("[data-k]");
  d.note = art.querySelector("[data-note]")?.value ?? d.note;
  const pick = art.querySelector(`input[name="v-${CSS.escape(id)}"]:checked`)?.value;
  let volba = "";
  if (pick === "own") volba = (art.querySelector("[data-own]")?.value || "").trim();
  else if (pick != null && k.varianty[+pick]) volba = k.varianty[+pick].volba;
  const msg = art.querySelector(".kmsg");
  if (!volba) { msg.textContent = "vyber variantu nebo napiš vlastní znění"; return; }
  btn.disabled = true; msg.textContent = "zapisuji…";
  try {
    const r = await fetch(`/api/kontrola/${encodeURIComponent(id)}`, {
      method: "POST", headers: { "Content-Type": "application/json", "X-Dashboard-Token": TOKEN },
      body: JSON.stringify({ volba, poznamka: d.note || "" }),
    });
    const res = await r.json();
    if (!r.ok) { msg.textContent = `nezapsáno: ${res.error || r.status}`; btn.disabled = false; return; }
    justDecided.add(id);
    drafts.set(id, { msg: `zapsáno${res.session ? ` · session ${res.session} dostala zprávu` : " · vyzvedne manager (session neběží)"}` });
    k.stav = "rozhodnuto"; k.rozhodnuti = res.rozhodnuti;   // hned ukázat; poll pak přinese soubor
    if (document.activeElement) document.activeElement.blur();
    renderKontroly(true);
  } catch (e) {
    msg.textContent = "server neodpovídá"; btn.disabled = false;
  }
}

for (const [id, key] of [["#kf-stav", "stav"], ["#kf-osoba", "osoba"], ["#kf-typ", "typ"]]) {
  $(id).addEventListener("change", () => {
    kFilters[key] = $(id).value;
    justDecided.clear();
    if (key === "stav") store.set("kf-stav", kFilters.stav);
    renderKontroly(true);
  });
}

// odkaz na kontrolu z panelu osoby
document.addEventListener("click", (ev) => {
  const a = ev.target.closest?.("[data-kontrola]");
  if (!a) return;
  ev.preventDefault();
  const k = (S.kontroly || []).find((x) => x.id === a.dataset.kontrola);
  if (k && !kStavMatch(k, kFilters.stav)) kFilters.stav = "";
  kFilters.osoba = ""; kFilters.typ = "";
  setTab("kontroly");
  renderKontroly(true);
  const art = document.getElementById("k-" + a.dataset.kontrola);
  if (art) { art.scrollIntoView({ block: "start" }); art.classList.add("flash"); setTimeout(() => art.classList.remove("flash"), 1500); }
});

{
  const prev = window.onStateChange;
  window.onStateChange = () => { if (prev) prev(); renderKontroly(); };
  const t0 = store.get("tab", "strom");
  if (t0 !== "strom") setTab(t0);
}
