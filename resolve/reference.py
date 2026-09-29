"""Adapters for public reference layers: fire detections, protected areas, admin boundaries."""
import hashlib
import json
from datetime import datetime

from shapely.geometry import mapping, shape

from .paths import codab_dir, private_root
from .textnorm import clean


def _q(coords, digits):
    """Quantize nested coordinate arrays."""
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], digits), round(coords[1], digits)]
    return [_q(c, digits) for c in coords]


def _geom(geometry, digits, simplify=None):
    g = shape(geometry)
    if not g.is_valid:
        raise ValueError(f"invalid geometry: {g.geom_type}")
    if simplify:
        g = g.simplify(simplify, preserve_topology=True)
    m = mapping(g)
    return {"type": m["type"], "coordinates": _q(json.loads(json.dumps(m["coordinates"])), digits)}


def fire_detections():
    path = private_root() / "raw" / "fire_detections" / "legacy-2025-02" / "fire.geojson"
    with open(path, encoding="utf-8") as fh:
        fc = json.load(fh)
    features = []
    for f in fc["features"]:
        p = f["properties"]
        when = datetime.strptime(f"{p['ACQ_DATE']} {p['acqtime']}", "%m/%d/%Y %H:%M")
        lon, lat = f["geometry"]["coordinates"][:2]
        digest = hashlib.sha1(f"{when.isoformat()}|{lon:.5f}|{lat:.5f}".encode()).hexdigest()[:10]
        features.append({
            "type": "Feature",
            "id": f"fire:{when:%Y%m%d}:{digest}",
            "geometry": {"type": "Point", "coordinates": [round(lon, 5), round(lat, 5)]},
            "properties": {
                "entity_type": "fire_detection",
                "acq_date": when.date().isoformat(),
                "acq_time_utc": when.strftime("%H:%M"),
                "day_night": clean(p.get("Day\\Night")),
                "geom_origin": "satellite_pixel_centre",
                "spatial_precision": "satellite_pixel",
            },
        })
    features.sort(key=lambda x: x["id"])
    ids = [f["id"] for f in features]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate fire detection ids")
    return features


def _area(text, prefix):
    value = clean(text)
    if value is None:
        return None
    return round(float(value.replace(prefix, "").replace(":", "").strip()), 3)


def protected_areas():
    path = private_root() / "raw" / "protected_areas" / "legacy-unknown" / "Preservations.geojson"
    with open(path, encoding="utf-8") as fh:
        fc = json.load(fh)
    features = []
    for f in fc["features"]:
        p = f["properties"]
        features.append({
            "type": "Feature",
            "id": f"pa:{int(p['fid']):03d}",
            "geometry": _geom(f["geometry"], 5, simplify=0.0001),
            "properties": {
                "entity_type": "protected_area",
                "name": clean(p.get("NAME")),
                "name_original": clean(p.get("ORIG_NAME")),
                "designation": clean(p.get("DESIG")),
                "designation_type": clean(p.get("DESIG_TYPE")),
                "governance": clean(p.get("GOV_TYPE")),
                "reported_area_km2": _area(p.get("REP_AREA"), "Area"),
                "gis_area_km2": _area(p.get("GIS_AREA"), "GIS"),
                "verification": clean(p.get("VERIF")),
                "geom_origin": "source_gis_polygon",
                "spatial_precision": "source_polygon",
            },
        })
    features.sort(key=lambda x: x["id"])
    return features


def admin_units(level, pcodes, simplify):
    with open(codab_dir() / f"lbn_admin{level}.geojson", encoding="utf-8") as fh:
        fc = json.load(fh)
    out = {}
    for f in fc["features"]:
        p = f["properties"]
        code = p[f"adm{level}_pcode"]
        if code in pcodes:
            out[code] = {"geometry": _geom(f["geometry"], 5, simplify=simplify), "properties": p}
    missing = set(pcodes) - set(out)
    if missing:
        raise ValueError(f"admin{level} units not found: {sorted(missing)}")
    return out
