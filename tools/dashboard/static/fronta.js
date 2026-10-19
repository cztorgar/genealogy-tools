// Workbench dashboard — fronta fáze I (server: tools/research/fronta.py → /api/state `fronta`).
"use strict";

const FR_TIER = { 1: "Šedí — ještě nezkoumaní", 2: "Nezelení — rozpracovaní, chybí položky fáze I" };
const FR_OBT = { "nízká": "lo", "střední": "mid", "velká": "hi" };
const frFilters = { anc: store.get("fr-anc", false), tier: store.get("fr-tier", "") };
let frSig = "";

function frTodo(r) {
  if (r.waiting) return `<span class="frwait">čeká na patch (manager)</span>`;
  if (r.blocking) return `<span class="frwait">čeká na tvou kontrolu</span>`;
  const out = [];
  if (r.parents === false && r.open.includes("rodice")) out.push(`<b>rodiče</b> → další úroveň, nebo závora`);
  const rest = r.open.filter((k) => k !== "rodice");
  if (rest.length) out.push(rest.map((k) => `<span class="frkey">${esc(k.replace("scitani", "sč. "))}</span>`).join(" "));
  if (r.zavora_fake) out.push(`<span class="frwarn" title="sekce Závora říká „nehledáno“ — pramen existuje, není to závora">závora = nehledáno</span>`);
  return out.join(" · ") || `<small>zkontrolovat checklist</small>`;
}

function renderFronta(force) {
  if (!S || $("#frontawrap").hidden) return;
  const rows = S.fronta || [];
  const sig = JSON.stringify([rows, frFilters]);
  if (!force && sig === frSig) return;
  frSig = sig;
  const shown = rows.filter((r) => (!frFilters.anc || r.anc) && (!frFilters.tier || String(r.tier) === frFilters.tier));
  const total = Object.keys(S.people).length;
  const green = Object.values(S.people).filter((p) => p.stav === "uzavřeno").length;
  const obt = (lvl) => rows.filter((r) => r.zavora === lvl).length;
  $("#fr-summary").innerHTML = `zelených <b>${green}</b> z ${total} · ve frontě <b>${rows.length}</b>
    (šedí ${rows.filter((r) => r.tier === 1).length}, nezelení ${rows.filter((r) => r.tier === 2).length})
    · závory ve frontě: <span class="obt lo">nízká ${obt("nízká")}</span> <span class="obt mid">střední ${obt("střední")}</span> <span class="obt hi">velká ${obt("velká")}</span>`;
  let html = "", tier = null;
  for (const r of shown) {
    if (r.tier !== tier) {
      if (tier !== null) html += `</tbody></table>`;
      tier = r.tier;
      html += `<h3>${r.tier}. ${esc(FR_TIER[r.tier])} <small>(${shown.filter((x) => x.tier === tier).length})</small></h3>
        <table class="frtab"><thead><tr><th>#</th><th>osoba</th><th>gen.</th><th>stav</th><th>závora</th><th>co udělat</th></tr></thead><tbody>`;
    }
    const p = S.people[r.id] || {};
    html += `<tr class="${r.anc ? "" : "side"}">
      <td class="num">${r.pos}</td>
      <td><span class="sw" style="background:${STATE_COLORS[r.stav || ""] || "#fff"}"></span> <span class="pid" data-pid="${r.id}">${r.id}</span> ${esc(p.name || "")}${r.anc ? "" : ` <small class="muted">vedlejší</small>`}</td>
      <td class="num">${r.gen}</td>
      <td>${esc(r.stav || "bez dossieru")}${p.branch ? ` <small class="frrun">▶ ${esc(p.branch)}</small>` : ""}</td>
      <td>${r.zavora ? `<span class="obt ${FR_OBT[r.zavora]}" title="obtížnost prolomit závoru">${esc(r.zavora)}</span>` : ""}</td>
      <td>${frTodo(r)}</td></tr>`;
  }
  if (tier !== null) html += `</tbody></table>`;
  $("#fr-list").innerHTML = html || `<p class="empty">${rows.length ? "Filtru nic neodpovídá." : "Fronta je prázdná — všichni jsou zelení."}</p>`;
}
window.renderFronta = renderFronta;

$("#fr-anc").checked = frFilters.anc;
$("#fr-tier").value = frFilters.tier;
$("#fr-anc").addEventListener("change", () => { frFilters.anc = $("#fr-anc").checked; store.set("fr-anc", frFilters.anc); renderFronta(true); });
$("#fr-tier").addEventListener("change", () => { frFilters.tier = $("#fr-tier").value; store.set("fr-tier", frFilters.tier); renderFronta(true); });

{
  const prev = window.onStateChange;
  window.onStateChange = () => { if (prev) prev(); renderFronta(); };
  if (store.get("tab", "strom") === "fronta") setTab("fronta");
}
