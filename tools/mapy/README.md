# tools/mapy — historické mapy jako skládatelné vrstvy

Stáhne mapové vrstvy pro oblast (hranice k. ú. + okraj), složí je do georeferencované mozaiky
a vygeneruje XYZ dlaždice ve **společné mřížce EPSG:3857 / 256 px**. Díky tomu se všechny
vrstvy přesně skládají na sebe (Leaflet, MapLibre, QGIS).

```sh
python3 -m venv .venv && .venv/bin/pip install rasterio pyproj pillow requests pyyaml   # jednou
.venv/bin/python tools/mapy/stahni.py zizelice --odhad          # počet požadavků
.venv/bin/python tools/mapy/stahni.py zizelice vm2 orto1950     # vybrané vrstvy
.venv/bin/python tools/mapy/stahni.py zizelice --bez-stahovani  # přegenerovat z cache
```

- `oblasti/<oblast>.geojson` — hranice k. ú. z RÚIAN (určují obálku).
- `vrstvy.yml` — zdroje: `wmts` (nativní dlaždice, mřížka se ověřuje proti GetCapabilities),
  `wms` a `arcgis_export` (metadlaždice zarovnané na globální mřížku, volitelný okraj proti
  ořezaným popiskům).
- Výstup: `cache/mapy/<oblast>/<vrstva>/` → `src/` (surové odpovědi), `<vrstva>.tif`
  (RGBA GeoTIFF v nativním CRS, overviews), `xyz/`, `manifest.json`, `tilejson.json`.

Šetrnost: odstup požadavků ≥ 1 s (`--interval`), při 429/5xx couvá, navazuje z cache, stahuje
jen obálku oblasti. Licence a citace každé vrstvy jsou v `vrstvy.yml` a v manifestu. Vrstvy bez
otevřené licence (Chartae Antiquae) jsou jen pro osobní výzkum.

Katalog map a jejich zdroje: [docs/mistopis/zizelice/mapy.md](../../docs/mistopis/zizelice/mapy.md).
