#!/usr/bin/env python3
"""Fetch THC historical markers mentioning death events and write data/thc_markers.json."""
import json
import os
import urllib.parse
import urllib.request

URL = os.environ.get(
    "THC_ARCGIS_URL",
    "https://atlas.thc.texas.gov/arcgis/rest/services/Atlas/Markers/MapServer/0/query",
)
TERMS = ["died in", "killed in", "massacre"]
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "thc_markers.json")


def query(term):
    params = {
        "where": "UPPER(MarkerText) LIKE '%{}%'".format(term.upper()),
        "outFields": "*",
        "outSR": "4326",
        "f": "json",
        "returnGeometry": "true",
    }
    with urllib.request.urlopen(URL + "?" + urllib.parse.urlencode(params), timeout=60) as r:
        return json.load(r).get("features", [])


def main():
    markers = {}
    for term in TERMS:
        for f in query(term):
            a, g = f.get("attributes", {}), f.get("geometry") or {}
            if "x" not in g or "y" not in g:
                continue
            key = a.get("OBJECTID") or (g["x"], g["y"])
            markers[key] = {
                "title": a.get("Title") or a.get("MarkerTitle") or "Historical Marker",
                "text": a.get("MarkerText", ""),
                "lat": g["y"],
                "lng": g["x"],
            }
    with open(OUT, "w") as fh:
        json.dump(list(markers.values()), fh, indent=1)
    print("Wrote %d markers" % len(markers))


if __name__ == "__main__":
    main()
