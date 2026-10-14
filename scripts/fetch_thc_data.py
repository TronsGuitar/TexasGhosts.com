#!/usr/bin/env python3
"""Fetch haunted/death-related markers and pioneer cemeteries from the THC ArcGIS REST API."""
import json
import os
import urllib.parse
import urllib.request

MARKERS_URL = "https://gis.thc.texas.gov/arcgis/rest/services/Historical/FeatureServer/0/query"
CEMETERIES_URL = "https://gis.thc.texas.gov/arcgis/rest/services/Atlas/FeatureServer/3/query"
KEYWORDS = ["died in", "killed in", "massacre", "shot and killed", "haunted"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "thc_markers.json")
PAGE = 1000


def query(url, where):
    records, offset = [], 0
    while True:
        params = {
            "where": where, "outFields": "*", "returnGeometry": "true",
            "outSR": "4326", "f": "json",
            "resultOffset": offset, "resultRecordCount": PAGE,
        }
        req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params),
                                     headers={"User-Agent": "TexasGhosts-sync/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
        feats = data.get("features", [])
        records.extend(feats)
        if not feats or not data.get("exceededTransferLimit"):
            return records
        offset += len(feats)


def point(feat):
    g = feat.get("geometry") or {}
    if "x" in g and "y" in g:
        return g["y"], g["x"]
    if g.get("rings"):
        pts = [p for ring in g["rings"] for p in ring]
        return sum(p[1] for p in pts) / len(pts), sum(p[0] for p in pts) / len(pts)
    return None, None


def pick(attrs, *names):
    low = {k.lower(): v for k, v in attrs.items()}
    for n in names:
        if low.get(n.lower()):
            return str(low[n.lower()]).strip()
    return ""


def main():
    out = []
    where = " OR ".join("UPPER(MarkerText) LIKE '%{}%'".format(k.upper()) for k in KEYWORDS)
    for f in query(MARKERS_URL, where):
        lat, lon = point(f)
        a = f.get("attributes", {})
        if lat is None:
            continue
        out.append({
            "id": "thc-m-" + pick(a, "AtlasNumber", "OBJECTID"),
            "category": "marker",
            "name": pick(a, "Title", "MarkerTitle", "Name") or "THC Historical Marker",
            "lat": round(lat, 6), "lon": round(lon, 6),
            "description": pick(a, "MarkerText")[:1200],
            "source": "Texas Historical Commission",
        })
    try:
        for f in query(CEMETERIES_URL, "1=1"):
            lat, lon = point(f)
            a = f.get("attributes", {})
            if lat is None:
                continue
            out.append({
                "id": "thc-c-" + pick(a, "AtlasNumber", "OBJECTID"),
                "category": "cemetery",
                "name": pick(a, "Name", "CemeteryName", "Title") or "Texas Cemetery",
                "lat": round(lat, 6), "lon": round(lon, 6),
                "description": pick(a, "Description", "Remarks"),
                "source": "Texas Historical Commission",
            })
    except Exception as e:  # cemetery layer is optional
        print("Cemetery fetch failed:", e)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2)
    print("Wrote", len(out), "records")


if __name__ == "__main__":
    main()
