"""Settlement points: where each village actually is, as opposed to its cadastral polygon centre.

Cadastral polygons can be large and mountainous, so their centre is often far from the village.
`python -m resolve settlements` looks up each cadastral unit's place node in OpenStreetMap
(Nominatim, 1 request/second, results must fall inside the cadastral polygon) and writes
ref/settlement_points.csv. Where OSM has no place inside the polygon, a point guaranteed to lie
inside the polygon (shapely representative_point) is used and flagged. Pipeline builds read the CSV
only; they never call the network.
"""
import csv
import json
import time
import urllib.parse
import urllib.request

from shapely.geometry import Point, shape

from .gazetteer import localities, read_aliases
from .paths import REF, codab_dir

COLUMNS = ["locality_id", "adm3_pcode", "name_en", "name_ar", "lon", "lat", "source", "osm_ref"]
PLACE_TYPES = {"city", "town", "village", "hamlet", "suburb", "neighbourhood", "quarter", "locality", "isolated_dwelling"}
PREFERRED = ["city", "town", "village", "suburb", "hamlet", "quarter", "neighbourhood", "locality", "isolated_dwelling"]
USER_AGENT = "RESOLVE-map-gazetteer/1.0 (research use; contact via repository)"


_cache = None


def _cache_path():
    from .paths import private_root
    path = private_root() / "cache" / "nominatim.json"
    path.parent.mkdir(exist_ok=True)
    return path


def _search(query, bbox):
    """Nominatim search with a local cache and retries (transient disconnects happen)."""
    global _cache
    if _cache is None:
        path = _cache_path()
        _cache = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    key = f"{query}|{','.join(f'{b:.3f}' for b in bbox)}"
    if key in _cache:
        return _cache[key]
    params = {"q": query, "countrycodes": "lb", "format": "jsonv2", "limit": 10,
              "viewbox": f"{bbox[0]},{bbox[3]},{bbox[2]},{bbox[1]}", "bounded": 1}
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as fh:
                result = json.load(fh)
            break
        except OSError:
            time.sleep(5 * (attempt + 1))
    else:
        raise RuntimeError(f"Nominatim unavailable for {query!r}")
    time.sleep(1.1)  # Nominatim usage policy: at most one request per second
    _cache[key] = result
    _cache_path().write_text(json.dumps(_cache, ensure_ascii=False), encoding="utf-8")
    return result


def build_settlements():
    units = {}
    with open(codab_dir() / "lbn_admin3.geojson", encoding="utf-8") as fh:
        for f in json.load(fh)["features"]:
            units[f["properties"]["adm3_pcode"]] = shape(f["geometry"])
    rows = []
    for loc in sorted(localities().values(), key=lambda r: r["locality_id"]):
        if loc["kind"] != "cadastral":
            continue  # special places already carry their own OSM or legacy point
        poly = units[loc["adm3_pcode"]]
        # Buffer the search box slightly: the village node may sit near the polygon edge.
        bbox = poly.buffer(0.01).bounds
        found = None
        spellings = [loc["adm3_name_ar"], loc["adm3_name_en"], loc["name_ar"]]
        spellings += [a["alias"] for a in read_aliases() if a["locality_id"] == loc["locality_id"]]
        spellings += [q[:-1] + ("ه" if q.endswith("ة") else "ة") for q in spellings if q and q[-1] in "ةه"]
        candidates = []
        for query in dict.fromkeys(q for q in spellings if q):
            for h in _search(query, bbox):
                if not poly.contains(Point(float(h["lon"]), float(h["lat"]))):
                    continue
                if h.get("category") == "place" and h.get("type") in PLACE_TYPES:
                    candidates.append((PREFERRED.index(h["type"]), -float(h.get("importance") or 0), h))
                elif h.get("category") == "boundary" and h.get("type") == "administrative":
                    candidates.append((len(PREFERRED), -float(h.get("importance") or 0), h))  # municipality point
            if any(c[0] < len(PREFERRED) for c in candidates):
                break
        if candidates:
            found = min(candidates, key=lambda c: (c[0], c[1]))[2]
        if found:
            lon, lat = float(found["lon"]), float(found["lat"])
            kind = f"place={found['type']}" if found["category"] == "place" else "municipality boundary point"
            source, ref = f"OpenStreetMap {kind} (ODbL)", f"{found['osm_type']}/{found['osm_id']}"
        else:
            p = poly.representative_point()
            lon, lat, source, ref = p.x, p.y, "Point inside cadastral polygon (no OSM place found)", ""
        rows.append({"locality_id": loc["locality_id"], "adm3_pcode": loc["adm3_pcode"], "name_en": loc["name_en"],
                     "name_ar": loc["name_ar"], "lon": f"{lon:.5f}", "lat": f"{lat:.5f}", "source": source, "osm_ref": ref})
    with open(REF / "settlement_points.csv", "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return rows
