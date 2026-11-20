// Workbench dashboard — zajímavosti k rozluštění (research/todo-zajimavosti.md), jen čtení.
"use strict";

const ZF = { stav: store.get("zf-stav", "open") };
let zSig = "";

function zCard(z) {
  const pers = z.osoby.map((id) => `<span class="pid" data-pid="${esc(id)}">${esc(id)}</span> <small>${esc((S.people[id] || {}).name || "")}</small>`).join(" · ");
  return `<article class="zaj ${z.open ? "" : "done"}">
    <h3>${z.n}. ${esc(z.title)}</h3>
    ${z.proc ? `<div class="zrow"><b>proč</b>${md(z.proc)}</div>` : ""}
    ${z.kde ? `<div class="zrow"><b>kde hledat</b>${md(z.kde)}</div>` : ""}
    ${pers ? `<div class="zrow zpers"><b>osoby</b>${pers}</div>` : (z.osoby_text ? `<div class="zrow"><b>osoby</b>${esc(z.osoby_text)}</div>` : "")}
    <div class="zrow"><b>stav</b><span class="kstav ${z.open ? "otevřeno" : "zapracováno"}">${esc(z.stav)}</span></div>
  </article>`;
}

function renderZajimavosti(force) {
  const all = (S && S.zajimavosti) || [];
  const open = all.filter((z) => z.open).length;
  $("#z-count").innerHTML = open ? `<b class="kcnt" title="${open} otevřených otázek">${open}</b>` : "";
  if (!S || $("#zajimavostiwrap").hidden) return;
  const sig = JSON.stringify([all, ZF]);
  if (!force && sig === zSig) return;
  zSig = sig;
  $("#zf-stav").value = ZF.stav;
  const shown = all.filter((z) => !ZF.stav || (ZF.stav === "open" ? z.open : !z.open));
  $("#z-summary").textContent = `${open} otevřených · ${all.length - open} vyřešených · zobrazeno ${shown.length}`;
  $("#z-list").innerHTML = shown.map(zCard).join("") || `<p class="empty">Nic.</p>`;
}
window.renderZajimavosti = renderZajimavosti;

$("#zf-stav").addEventListener("change", () => { ZF.stav = $("#zf-stav").value; store.set("zf-stav", ZF.stav); renderZajimavosti(true); });
$("#z-file").addEventListener("click", (ev) => { ev.preventDefault(); window.open(fileUrl("research/todo-zajimavosti.md"), "_blank"); });
$("#z-list").addEventListener("click", (ev) => {
  const a = ev.target.closest("a[href^='/api/file']");
  if (a) { ev.preventDefault(); window.open(a.getAttribute("href"), "_blank"); }
});

{
  const prev = window.onStateChange;
  window.onStateChange = () => { if (prev) prev(); renderZajimavosti(); };
  if (store.get("tab", "strom") === "zajimavosti") setTab("zajimavosti");
}
