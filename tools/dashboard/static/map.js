// Workbench dashboard — mapa „kde kdo žil“. Data z /api/map (bydliště z patchů, čp. z RÚIAN, vrstvy z cache/mapy).
"use strict";

const CARRY_YEARS = 10;     // jak dlouho po posledním doložení se bydliště ještě odvozuje
let M = null;               // data z /api/map
let lmap = null;
let baseLayer = null, kmLayer = null, osmLayer = null;
const gHouses = L.layerGroup(), gAll = L.layerGroup();
let housePos = new Map();   // fold(obec) → {obec, cps}
let placePos = new Map();   // fold(obec) → [lat, lon]
let playTimer = null;
let openKey = null;         // dům s otevřeným popupem (obec|cp)

// stejné jako mapdata.fold — čtvrti („Chlumec nad Cidlinou II“) se neslévají; část obce určuje server (mapdata.resolve)
const foldPlace = (s) => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
  .replace(" nad cidlinou", " n. c.").replace(" n.c.", " n. c.").replace(/\s+/g, " ").trim();
const undeterminedOf = (place, cp) => (M.residences.find((r) => r.undetermined &&
  foldPlace(r.place) === foldPlace(place) && String(r.cp) === String(cp)) || {}).undetermined;

// ------------------------------------------------------------------ záložky

function setTab(tab) {
  const isMap = tab === "mapa";
  document.body.classList.toggle("tab-mapa", isMap);
  document.body.classList.toggle("tab-kontroly", tab === "kontroly" || tab === "fronta");
  document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === tab));
  $("#canvas").hidden = tab !== "strom";
  $("#mapwrap").hidden = !isMap;
  $("#kontrolywrap").hidden = tab !== "kontroly";
  $("#frontawrap").hidden = tab !== "fronta";
  store.set("tab", tab);
  if (isMap) { ensureMap(); setTimeout(() => lmap && lmap.invalidateSize(), 0); }
  else if (tab === "kontroly") { if (window.renderKontroly) renderKontroly(true); }
  else if (tab === "fronta") { if (window.renderFronta) renderFronta(true); }
  else if (selected) setTimeout(() => focusNode(selected), 0);
}
document.querySelectorAll("#tabs button").forEach((b) => b.addEventListener("click", () => setTab(b.dataset.tab)));

// ------------------------------------------------------------------ data

let mapSig = "";
async function loadMapData() {
  let data;
  try { data = await (await fetch("/api/map")).json(); } catch { return; }
  const sig = JSON.stringify(data);
  if (M && sig === mapSig) return;   // změnil se jen jiný stav (session…) — nepřekreslovat
  mapSig = sig;
  M = data;
  housePos = new Map(Object.entries(M.houses).map(([obec, cps]) => [foldPlace(obec), { obec, cps }]));
  placePos = new Map(Object.entries(M.places).map(([obec, ll]) => [foldPlace(obec), ll]));
  const ys = M.residences.flatMap((r) => [r.year, r.year_to || r.year]);
  const slider = $("#m-year");
  slider.min = Math.min(1800, ...ys) - 0;
  slider.max = new Date().getFullYear();
  fillAreas();
  fillLayers();
  draw();
}

// poloha: [lat, lon, přesnost] — „dum“ = čp. z RÚIAN, „obec“ = jen střed obce
function locate(place, cp) {
  const h = housePos.get(foldPlace(place));
  if (h && h.cps[cp]) return { ll: h.cps[cp], precision: "dum", obec: h.obec };
  const p = placePos.get(foldPlace(place));
  if (p) return { ll: p, precision: "obec", obec: place };
  return null;
}

// Kdo kde bydlel v roce y: doloženo = záznam z toho roku (nebo rozmezí FROM–TO),
// odvozeno = mezi dvěma doklady téhož domu, nebo do CARRY_YEARS let po posledním (ne po úmrtí).
function presence(y, exactOnly) {
  const byPerson = new Map();
  for (const r of M.residences) {
    if (!byPerson.has(r.id)) byPerson.set(r.id, []);
    byPerson.get(r.id).push(r);
  }
  const out = [];
  for (const [id, obs] of byPerson) {
    obs.sort((a, b) => a.year - b.year);
    const deaths = obs.filter((o) => o.type === "Death").map((o) => o.year);
    const births = obs.filter((o) => o.type === "Birth").map((o) => o.year);
    const death = deaths.length ? Math.max(...deaths) : Infinity;
    const birth = births.length ? Math.min(...births) : -Infinity;
    if (y > death || y < birth) continue;
    const exact = obs.filter((o) => o.year === y || (o.year_to && o.year <= y && y <= o.year_to));
    if (exact.length) {
      const seen = new Set();
      for (const o of exact) {
        const key = `${o.place}|${o.cp}`;
        if (seen.has(key)) continue;
        seen.add(key);
        out.push({ id, key, place: o.place, cp: o.cp, kind: "doloženo", basis: exact.filter((e) => `${e.place}|${e.cp}` === key) });
      }
      continue;
    }
    if (exactOnly) continue;
    const prev = obs.filter((o) => (o.year_to || o.year) < y).pop();
    const next = obs.find((o) => o.year > y);
    if (!prev) continue;
    const pk = `${prev.place}|${prev.cp}`;
    const sameNext = next && `${next.place}|${next.cp}` === pk;
    if (sameNext || y - (prev.year_to || prev.year) <= CARRY_YEARS) {
      out.push({ id, key: pk, place: prev.place, cp: prev.cp, kind: "odvozeno", basis: [prev].concat(sameNext ? [next] : []) });
    }
  }
  return out;
}

// ------------------------------------------------------------------ mapa

function ensureMap() {
  if (lmap) return;
  lmap = L.map("map", { zoomControl: true, preferCanvas: true }).setView([50.13, 15.4], 13);
  osmLayer = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19, opacity: 0.55, attribution: "© OpenStreetMap",
  }).addTo(lmap);
  gAll.addTo(lmap);
  gHouses.addTo(lmap);
  lmap.on("popupclose", () => { openKey = null; });
  new ResizeObserver(() => lmap.invalidateSize()).observe($("#map"));
  loadMapData();
}

function areaList() {
  const out = [];
  const seen = new Set();
  for (const l of M.layers) {
    if (seen.has(l.area) || !l.bounds) continue;
    seen.add(l.area);
    const reg = M.regions.find((r) => r.id === l.area);
    out.push({ id: l.area, title: reg ? reg.title : l.area, bounds: [[l.bounds[1], l.bounds[0]], [l.bounds[3], l.bounds[2]]] });
  }
  for (const r of M.regions) {
    if (seen.has(r.id) || !r.places.length) continue;
    const lls = r.places.map((p) => M.places[p]).filter(Boolean);
    if (!lls.length) continue;
    out.push({ id: r.id, title: r.title, bounds: L.latLngBounds(lls).pad(0.05) });
  }
  const located = M.residences.map((r) => locate(r.place, r.cp)).filter(Boolean).map((x) => x.ll);
  if (located.length) out.push({ id: "_data", title: "všechna místa s daty", bounds: L.latLngBounds(located).pad(0.1) });
  return out;
}

function fillAreas() {
  const sel = $("#m-area");
  const areas = areaList();
  sel.innerHTML = areas.map((a) => `<option value="${esc(a.id)}">${esc(a.title)}</option>`).join("");
  sel.value = store.get("m-area", areas[0] && areas[0].id);
  if (!sel.value && areas[0]) sel.value = areas[0].id;
  sel.onchange = () => {
    store.set("m-area", sel.value);
    const a = areaList().find((x) => x.id === sel.value);
    if (a) lmap.fitBounds(a.bounds);
  };
  if (!fillAreas.done) { fillAreas.done = true; sel.onchange(); }
}

function fillLayers() {
  const sel = $("#m-layer");
  const base = M.layers.filter((l) => !isOverlay(l));
  sel.innerHTML = `<option value="">jen OpenStreetMap (online)</option>` +
    base.map((l) => `<option value="${esc(l.area)}/${esc(l.id)}">${esc(l.name)}</option>`).join("");
  sel.value = store.get("m-layer", base[0] ? `${base[0].area}/${base[0].id}` : "");
  sel.onchange = () => { $("#m-auto").checked = false; store.set("m-auto", false); store.set("m-layer", sel.value); setBase(sel.value); };
  $("#m-auto").checked = store.get("m-auto", true);
  $("#m-km").checked = store.get("m-km", false);
  $("#m-all").checked = store.get("m-all", false);
  $("#m-exact").checked = store.get("m-exact", false);
  $("#m-year").value = store.get("m-year", 1880);
  setBase(sel.value);
  setKm();
}
const isOverlay = (l) => l.id === "km" || /katastráln/i.test(l.name);

function tileLayer(l, opts) {
  return L.tileLayer(`/tiles/${l.area}/${l.id}/{z}/{x}/{y}.${l.ext}`, Object.assign({
    minZoom: 10, maxZoom: 20, minNativeZoom: l.minzoom, maxNativeZoom: l.maxzoom,
    bounds: l.bounds ? [[l.bounds[1], l.bounds[0]], [l.bounds[3], l.bounds[2]]] : undefined,
    attribution: esc(l.attribution),
  }, opts));
}

function setBase(value) {
  if (baseLayer) { lmap.removeLayer(baseLayer); baseLayer = null; }
  const l = M.layers.find((x) => `${x.area}/${x.id}` === value);
  if (l) baseLayer = tileLayer(l).addTo(lmap);
  osmLayer.setOpacity(l ? 0.55 : 1);
  if (kmLayer) kmLayer.bringToFront();
}
function setKm() {
  if (kmLayer) { lmap.removeLayer(kmLayer); kmLayer = null; }
  const l = M.layers.find(isOverlay);
  if (l && $("#m-km").checked) kmLayer = tileLayer(l, { opacity: 0.8 }).addTo(lmap);
}

// podklad nejblíž zvolenému roku (vrstvy s rozsahem let)
function autoBase(y) {
  let best = null, bestD = Infinity;
  for (const l of M.layers) {
    if (isOverlay(l) || !l.years) continue;
    const d = y < l.years[0] ? l.years[0] - y : y > l.years[1] ? y - l.years[1] : 0;
    if (d < bestD) { best = l; bestD = d; }
  }
  if (!best) return;
  const v = `${best.area}/${best.id}`;
  if ($("#m-layer").value !== v) { $("#m-layer").value = v; setBase(v); }
}

function draw() {
  if (!M || !lmap) return;
  const y = parseInt($("#m-year").value, 10);
  $("#m-year-label").textContent = y;
  if ($("#m-auto").checked) autoBase(y);
  const pres = presence(y, $("#m-exact").checked);

  // seskupit podle domu
  const houses = new Map();
  for (const p of pres) {
    if (!houses.has(p.key)) houses.set(p.key, { key: p.key, place: p.place, cp: p.cp, people: [] });
    houses.get(p.key).people.push(p);
  }
  const keep = openKey;
  gHouses.clearLayers();
  openKey = keep;
  const noLoc = [];
  const villageOnly = new Map();
  for (const h of houses.values()) {
    const loc = locate(h.place, h.cp);
    if (!loc) { noLoc.push(h); continue; }
    if (loc.precision === "obec") {
      const k = foldPlace(h.place);
      if (!villageOnly.has(k)) villageOnly.set(k, { ll: loc.ll, place: h.place, houses: [] });
      villageOnly.get(k).houses.push(h);
      continue;
    }
    const exact = h.people.some((p) => p.kind === "doloženo");
    const m = L.circleMarker(loc.ll, {
      radius: 6 + Math.min(6, h.people.length * 1.5), color: "#8a3b00", weight: exact ? 2 : 2.5,
      fillColor: "#ff8c1a", fillOpacity: exact ? 0.9 : 0.05, dashArray: exact ? null : "3 3",
    }).addTo(gHouses);
    m.bindTooltip(String(h.cp), { permanent: true, direction: "right", offset: [8, 0], className: "cp-label" });
    m.bindPopup(() => housePopup(h.place, h.cp, y), { maxWidth: 420 });
    if (keep === h.key) setTimeout(() => m.openPopup(), 0);
  }
  for (const v of villageOnly.values()) {
    const m = L.marker(v.ll, {
      icon: L.divIcon({ className: "", html: `<div style="background:#ff8c1a;border:2px solid #8a3b00;width:14px;height:14px"></div>`, iconSize: [14, 14] }),
    }).addTo(gHouses);
    const und = v.houses.some((h) => undeterminedOf(h.place, h.cp)) ? " (čtvrť neurčena)" : "";
    m.bindTooltip(`${v.place}${und}: čp. ${v.houses.map((h) => h.cp).join(", ")}`, { permanent: true, direction: "right", offset: [8, 0], className: "cp-label" });
    m.bindPopup(() => v.houses.map((h) => housePopup(h.place, h.cp, y, true)).join("<hr>"), { maxWidth: 420 });
  }
  drawAll();
  const persons = new Set(pres.map((p) => p.id)).size;
  $("#m-count").textContent = `${persons} osob · ${houses.size} domů`;
  const legendOpen = store.get("m-legend", true);
  $("#maplegend").innerHTML = `<details ${legendOpen ? "open" : ""}><summary>Legenda</summary>
    <div><svg width="14" height="14"><circle cx="7" cy="7" r="5.5" fill="#ff8c1a" stroke="#8a3b00" stroke-width="2"/></svg> doloženo v tomto roce (záznam v patchi)</div>
    <div><svg width="14" height="14"><circle cx="7" cy="7" r="5.5" fill="none" stroke="#8a3b00" stroke-width="2" stroke-dasharray="3 3"/></svg> odvozeno — mezi doklady téhož domu, nebo do ${CARRY_YEARS} let po posledním</div>
    <div><svg width="14" height="14"><rect x="1" y="1" width="12" height="12" fill="#ff8c1a" stroke="#8a3b00" stroke-width="2"/></svg> jen střed obce — poloha domu neznámá</div>
    <div class="note" style="color:#666">Poloha čp. = dnešní RÚIAN; historicky mohl dům stát jinde (přečíslování, nová čísla).</div>
    ${noLoc.length ? `<div class="nolo">bez polohy: ${noLoc.map((h) => `${esc(h.place)} čp. ${esc(h.cp)}`).join(", ")}</div>` : ""}</details>`;
  $("#maplegend details").addEventListener("toggle", (ev) => store.set("m-legend", ev.target.open));
}

function drawAll() {
  gAll.clearLayers();
  if (!$("#m-all").checked) return;
  for (const { obec, cps } of housePos.values()) {
    for (const [cp, ll] of Object.entries(cps)) {
      L.circleMarker(ll, { radius: 2.5, color: "#555", weight: 1, fillColor: "#fff", fillOpacity: 0.9 })
        .bindTooltip(`${obec} čp. ${cp}`).addTo(gAll);
    }
  }
}

function housePopup(place, cp, y, compact) {
  openKey = `${place}|${cp}`;
  const key = foldPlace(place) + "|" + cp;
  const all = M.residences.filter((r) => foldPlace(r.place) + "|" + r.cp === key).sort((a, b) => a.year - b.year);
  const now = presence(y, $("#m-exact").checked).filter((p) => foldPlace(p.place) + "|" + p.cp === key);
  const loc = locate(place, cp);
  const who = now.length ? `<ul>${now.map((p) => {
    const r = p.basis[0];
    const name = r.name || (S.people[p.id] || {}).name || "";
    const basis = p.basis.map((b) => `${TYPE_CS[b.type] || b.type} ${b.year}${b.year_to ? `–${b.year_to}` : ""}`).join(", ");
    return `<li><span class="pid" data-pid="${p.id}">${esc(name || p.id)}</span> <small>${esc(p.id)}</small><br><small>${p.kind} · ${esc(basis)}</small></li>`;
  }).join("")}</ul>` : `<p class="note">v roce ${y} tu nikdo ze stromu doložen ani odvozen</p>`;
  const nowIds = new Set(now.map((p) => p.id));
  const hist = `<table>${all.map((r) => `<tr class="${nowIds.has(r.id) ? "now" : ""}">
      <td><span class="yr" data-year="${r.year}">${r.year}${r.year_to ? `–${r.year_to}` : ""}</span></td>
      <td><span class="pid" data-pid="${r.id}">${esc(r.name || r.id)}</span></td>
      <td>${esc(TYPE_CS[r.type] || r.type)}</td>
      <td title="${esc(r.description)}"><small>${esc(r.patch)}${r.status !== "aplikováno" ? ` (${esc(r.status)})` : ""}</small></td></tr>`).join("")}</table>`;
  return `<div class="house-pop"><h4>${esc(loc ? loc.obec : place)} čp. ${esc(cp)}</h4>
    <b>Rok ${y}:</b>${who}
    ${compact ? "" : `<b>Všechny záznamy k domu:</b>${hist}`}
    ${compact ? hist : ""}
    <div class="note">${loc && loc.precision === "dum" ? "poloha: dnešní čp. z RÚIAN (historicky mohlo být jinde)"
      : undeterminedOf(place, cp) ? `${esc(undeterminedOf(place, cp))} — poloha domu neurčena, jen střed obce`
      : "poloha domu neznámá — jen střed obce"}</div></div>`;
}

// ------------------------------------------------------------------ ovládání

function setYear(y) {
  $("#m-year").value = y;
  store.set("m-year", y);
  draw();
}
$("#m-year").addEventListener("input", () => setYear(parseInt($("#m-year").value, 10)));
$("#m-auto").addEventListener("change", () => { store.set("m-auto", $("#m-auto").checked); draw(); });
$("#m-km").addEventListener("change", () => { store.set("m-km", $("#m-km").checked); setKm(); });
$("#m-all").addEventListener("change", () => { store.set("m-all", $("#m-all").checked); drawAll(); });
$("#m-exact").addEventListener("change", () => { store.set("m-exact", $("#m-exact").checked); draw(); });
$("#m-play").addEventListener("click", () => {
  if (playTimer) { clearInterval(playTimer); playTimer = null; $("#m-play").textContent = "▶"; return; }
  $("#m-play").textContent = "❚❚";
  playTimer = setInterval(() => {
    const s = $("#m-year");
    let y = parseInt(s.value, 10) + 1;
    if (y > parseInt(s.max, 10)) y = parseInt(s.min, 10);
    setYear(y);
  }, 350);
});
document.addEventListener("keydown", (ev) => {
  if ($("#mapwrap").hidden || ["INPUT", "SELECT"].includes(document.activeElement.tagName)) return;
  if (ev.key === "ArrowLeft" || ev.key === "ArrowRight") {
    ev.preventDefault();
    setYear(parseInt($("#m-year").value, 10) + (ev.key === "ArrowRight" ? 1 : -1) * (ev.shiftKey ? 10 : 1));
  }
});
document.addEventListener("click", (ev) => {
  const yr = ev.target.closest?.("[data-year]");
  if (yr) { setYear(parseInt(yr.dataset.year, 10)); return; }
  const sm = ev.target.closest?.("[data-showmap]");
  if (sm) {
    ev.preventDefault();
    const [place, cp, year] = sm.dataset.showmap.split("|");
    showOnMap(place, cp, parseInt(year, 10));
  }
});

async function showOnMap(place, cp, year) {
  setTab("mapa");
  if (!M) await loadMapData();
  const loc = locate(place, cp);
  if (loc) lmap.setView(loc.ll, Math.max(lmap.getZoom(), loc.precision === "dum" ? 17 : 14), { animate: false });
  openKey = `${place}|${cp}`;
  setYear(year);
}

// živé obnovení — nová verze stavu (patche) → znovu načíst mapová data
window.onStateChange = () => { if (lmap) loadMapData(); };


