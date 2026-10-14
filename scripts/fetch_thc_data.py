import urllib.request
import urllib.parse
import json
import os
import ssl

# Official Texas Historical Commission (THC) ArcGIS REST Endpoints:
# Layer 2 = Historical Markers | Layer 5 = Historic Cemeteries
THC_MARKERS_URL = "https://gis.thc.texas.gov/arcgis/rest/services/Historical/FeatureServer/2/query"
THC_CEMETERIES_URL = "https://gis.thc.texas.gov/arcgis/rest/services/Historical/FeatureServer/5/query"

# Fallback seed data in case Texas.gov WAF blocks GitHub Actions Azure runner IPs
FALLBACK_MARKERS = [
    {
        "id": "thc-fallback-hardin",
        "category": "marker",
        "badge": "📜 THC 'Died In' Marker",
        "color": "#f59e0b",
        "icon": "📜",
        "title": "John Wesley Hardin Death Site (Acme Saloon)",
        "location": "El Paso, El Paso County",
        "year": "1895",
        "lat": 31.7587,
        "lon": -106.4869,
        "story": "Notorious Texas outlaw and gunfighter John Wesley Hardin died in the Acme Saloon on August 19, 1895 after being shot by Constable John Selman."
    },
    {
        "id": "thc-fallback-sambass",
        "category": "marker",
        "badge": "📜 THC 'Died In' Marker",
        "color": "#f59e0b",
        "icon": "📜",
        "title": "Sam Bass Shootout & Death Site",
        "location": "Round Rock, Williamson County",
        "year": "1878",
        "lat": 30.5083,
        "lon": -97.6789,
        "story": "Outlaw Sam Bass was mortally wounded by Texas Rangers during an attempted bank robbery here on July 19, 1878, and died in custody two days later."
    },
    {
        "id": "thc-fallback-killough",
        "category": "marker",
        "badge": "📜 THC 'Died In' Marker",
        "color": "#f59e0b",
        "icon": "📜",
        "title": "Killough Massacre Monument",
        "location": "Jacksonville, Cherokee County",
        "year": "1838",
        "lat": 32.0435,
        "lon": -95.2952,
        "story": "Marks the remote East Texas homestead where eighteen members of the Isaac Killough family died in an October 5, 1838 raid."
    },
    {
        "id": "thc-fallback-ftparker",
        "category": "marker",
        "badge": "📜 THC 'Died In' Marker",
        "color": "#f59e0b",
        "icon": "📜",
        "title": "Fort Parker Massacre Site",
        "location": "Groesbeck, Limestone County",
        "year": "1836",
        "lat": 31.5958,
        "lon": -96.5333,
        "story": "Site where Elder John Parker and four other settlers died in the May 19, 1836 raid during which young Cynthia Ann Parker was captured."
    },
    {
        "id": "thc-fallback-warren",
        "category": "marker",
        "badge": "📜 THC 'Died In' Marker",
        "color": "#f59e0b",
        "icon": "📜",
        "title": "Warren Wagon Train Raid Marker",
        "location": "Graham Vicinity, Young County",
        "year": "1871",
        "lat": 33.1950,
        "lon": -98.4310,
        "story": "Marks the Salt Creek prairie site where seven teamsters died in the May 18, 1871 attack led by Satanta."
    }
]


def arcgis_query(url, where_clause, max_records=250):
    params = urllib.parse.urlencode({
        "where": where_clause,
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "json",
        "resultRecordCount": max_records
    })
    req = urllib.request.Request(
        f"{url}?{params}",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*"
        }
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=25, context=ctx) as resp:
            raw = resp.read().decode("utf-8", errors="replace").strip()
            if not raw.startswith("{"):
                print(f"Warning: Non-JSON response from {url} (first 120 chars): {raw[:120]}")
                return []
            payload = json.loads(raw)
            if "error" in payload:
                print(f"ArcGIS API error on where='{where_clause}': {payload['error']}")
                return []
            return payload.get("features", [])
    except Exception as exc:
        print(f"Network/parse warning querying {url}: {exc}")
        return []


def pick_attr(attrs, *candidates, default=""):
    lower_map = {k.lower(): v for k, v in attrs.items() if v is not None}
    for c in candidates:
        if c.lower() in lower_map:
            return str(lower_map[c.lower()]).strip()
    return default


def main():
    pins_by_id = {}

    # 1. Query Layer 2 (Historical Markers)
    # Try text search clauses first; if the text column name differs, pull a general batch and filter in Python
    clauses = [
        "1=1"
    ]
    keywords = ("died in", "killed", "massacre", "murdered", "shot", "grave", "cemetery", "ghost", "epidemic", "cholera")

    for clause in clauses:
        features = arcgis_query(THC_MARKERS_URL, clause, max_records=1000)
        print(f"Fetched {len(features)} raw marker features from Layer 2...")
        for feat in features:
            attrs = feat.get("attributes") or {}
            geom = feat.get("geometry") or {}
            lat, lon = geom.get("y"), geom.get("x")
            if lat is None or lon is None:
                continue

            title = pick_attr(attrs, "NAME", "MarkerTitle", "TITLE", "INDEX_NAME", default="Texas Historical Marker")
            text = pick_attr(attrs, "MARKER_TEXT", "MarkerText", "TEXT", "DESCRIPTION", "COMMENTS", default="")
            combined_blob = f"{title} {text}".lower()

            # If marker text is available, filter for tragic/death/ghost keywords; otherwise keep notable markers
            if text and not any(k in combined_blob for k in keywords):
                continue

            obj_id = pick_attr(attrs, "ATLAS_NUM", "AtlasNumber", "MARKER_NUM", "OBJECTID", default=f"{lat:.4f}")
            city = pick_attr(attrs, "CITY", "City", "TOWN", default="")
            county = pick_attr(attrs, "COUNTY", "County", default="Texas")
            year = pick_attr(attrs, "YEAR_ERECTED", "YearMarkerErected", "MARKER_YEAR", "YR_ERECTED", default="Historic")

            pin_id = f"thc-marker-{obj_id}"
            story_body = text if text else f"Official Texas Historical Commission Marker: {title} ({city}, {county} County)."

            pins_by_id[pin_id] = {
                "id": pin_id,
                "category": "marker",
                "badge": "📜 THC Historical Marker",
                "color": "#f59e0b",
                "icon": "📜",
                "title": title,
                "location": f"{city}, {county} County".strip(", "),
                "year": year,
                "lat": round(float(lat), 5),
                "lon": round(float(lon), 5),
                "story": story_body[:650] + ("..." if len(story_body) > 650 else "")
            }

    # 2. Query Layer 5 (Historic Texas Cemeteries)
    cem_features = arcgis_query(THC_CEMETERIES_URL, "1=1", max_records=300)
    print(f"Fetched {len(cem_features)} raw cemetery features from Layer 5...")
    for feat in cem_features:
        attrs = feat.get("attributes") or {}
        geom = feat.get("geometry") or {}
        lat, lon = geom.get("y"), geom.get("x")
        # Handle polygon rings if Layer 5 returns polygon centroids
        if (lat is None or lon is None) and "rings" in geom and geom["rings"]:
            ring = geom["rings"][0]
            if ring:
                lon = sum(pt[0] for pt in ring) / len(ring)
                lat = sum(pt[1] for pt in ring) / len(ring)
        if lat is None or lon is None:
            continue

        cem_name = pick_attr(attrs, "CEMNAME", "NAME", "CemeteryName", default="Historic Pioneer Cemetery")
        county = pick_attr(attrs, "COUNTY", "County", default="Texas")
        obj_id = pick_attr(attrs, "ATLAS_NUM", "OBJECTID", default=f"{lat:.4f}")
        pin_id = f"thc-cem-{obj_id}"

        pins_by_id[pin_id] = {
            "id": pin_id,
            "category": "cemetery",
            "badge": "🪦 Historic Texas Cemetery",
            "color": "#94a3b8",
            "icon": "🪦",
            "title": cem_name,
            "location": f"{county} County",
            "year": "Pioneer Era",
            "lat": round(float(lat), 5),
            "lon": round(float(lon), 5),
            "story": f"Recorded in the Texas Historical Commission Atlas as a historic burial ground ({cem_name}) in {county} County."
        }

    # 3. Always include fallback markers so the output JSON is never empty
    for fb in FALLBACK_MARKERS:
        pins_by_id.setdefault(fb["id"], fb)

    os.makedirs("data", exist_ok=True)
    out_path = "data/thc_markers.json"
    final_list = list(pins_by_id.values())

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final_list, f, indent=2)

    print(f"Successfully wrote {len(final_list)} sites to {out_path}!")


if __name__ == "__main__":
    main()
