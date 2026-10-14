# 👻 TexasGhosts.com — Interactive Texas Ghost & Historical Map

🔗 **Live Application (GitHub Pages):** [https://tronsguitar.github.io/TexasGhosts.com/](https://tronsguitar.github.io/TexasGhosts.com/)  
🌐 **Custom Domain:** [https://texasghosts.com](https://texasghosts.com)  
📂 **Repository:** [https://github.com/TronsGuitar/TexasGhosts.com](https://github.com/TronsGuitar/TexasGhosts.com)

---

## Overview
**TexasGhosts.com** is an interactive, pinch-zoomable dark-mode map and spatial community forum covering Texas history and paranormal lore across five distinct layers:
- 📜 **THC "Died In" Historical Markers** — Pulled from the Texas Historical Commission (THC) ArcGIS Atlas API (`MarkerText` queries for `"died in"`, `"killed in"`, and `"massacre"`).
- 🪦 **Remote & Pioneer Cemeteries** — Isolated 19th-century family burial plots and homestead graveyards (such as the 1880s Riley Pioneer Cemetery in Carrollton).
- 🏚️ **Classic Texas Ghost Towns** — Abandoned boomtowns, mining camps, and bypassed railroad settlements.
- 🔮 **Regional Folklore & Ghost Stories** — Documented Texas urban legends, bridges, and historic hotels.
- 🗣️ **Community Experience Pins & Giscus Forum** — User-submitted experiences with built-in 100-block residential privacy fuzzing, automated Haversine proximity radar to nearby cemeteries/markers, and per-pin GitHub Discussions threads powered by [Giscus](https://giscus.app).

## Automated Workflows (Zero-Cost Architecture)
1. **Sync THC Marker Data (`.github/workflows/sync-thc-data.yml`):** Run manually via the **Actions** tab (`workflow_dispatch`) to query the live Texas Historical Commission API and commit `data/thc_markers.json`.
2. **Publish Community Pins (`.github/workflows/add-ghost-pin.yml`):** Users can click **➕ Drop Experience Pin** on the live map to submit a pre-formatted GitHub Issue. Adding the `approved-pin` label to the issue automatically appends the pin to `data/community_ghosts.json` and updates the live map.
