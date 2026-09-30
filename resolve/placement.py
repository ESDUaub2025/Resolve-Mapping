"""Where each respondent's pin goes.

Evidence, most precise first:
  1. gps_area            the respondent wrote GPS coordinates for their land: the pin goes to the
                         cadastral area containing that point (the exact point stays private).
  2. farm_area_reported  the land-location answer names another cadastral area; reviewed
                         assignments live in <private>/registry/farm_area_overrides.csv.
  3. residence_village   the village the respondent reported, resolved via ref/locality_aliases.csv.

The anchor is the area's settlement point (ref/settlement_points.csv: OpenStreetMap place nodes,
not polygon centroids), or the OSM/legacy point of special places. Pins sharing an anchor are laid
out on a small sunflower pattern (about 55 m between rings) and pulled back toward the anchor if
they would leave the cadastral area. The anchor, the evidence and the offset are recorded on every
pin, so the displayed position is never presented as a farm location.
"""
import csv
import json
import math

from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform

from .gazetteer import localities
from .paths import REF, codab_dir, private_root

STEP_M = 55
GOLDEN = math.pi * (3 - math.sqrt(5))
_TO_M = Transformer.from_crs("EPSG:4326", "EPSG:32636", always_xy=True).transform
_TO_DEG = Transformer.from_crs("EPSG:32636", "EPSG:4326", always_xy=True).transform


def _read(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def settlement_points():
    return {r["adm3_pcode"]: r for r in _read(REF / "settlement_points.csv")}


def farm_overrides():
    return {r["respondent_id"]: r["adm3_pcode"] for r in _read(private_root() / "registry" / "farm_area_overrides.csv")}


def _cadastral_polygons():
    with open(codab_dir() / "lbn_admin3.geojson", encoding="utf-8") as fh:
        return {f["properties"]["adm3_pcode"]: shape(f["geometry"]) for f in json.load(fh)["features"]}


class Placer:
    def __init__(self):
        self.locs = localities()
        self.by_adm3 = {r["adm3_pcode"]: r for r in self.locs.values() if r["kind"] == "cadastral"}
        self.points = settlement_points()
        self.overrides = farm_overrides()
        self.polys = _cadastral_polygons()

    def _cadastral_of(self, lon, lat):
        pt = Point(lon, lat)
        return next((code for code, poly in self.polys.items() if poly.contains(pt)), None)

    def _area(self, adm3):
        loc, pt = self.by_adm3.get(adm3), self.points.get(adm3)
        if loc is None or pt is None:
            return None
        origin = "osm_settlement_point" if pt["osm_ref"] else "point_inside_cadastral_area"
        return {"lon": float(pt["lon"]), "lat": float(pt["lat"]), "adm3_pcode": adm3, "geom_origin": origin,
                "spatial_precision": "locality", "area_name_en": loc["adm3_name_en"], "area_name_ar": loc["adm3_name_ar"],
                "district_en": loc["adm2_name_en"], "district_ar": loc["adm2_name_ar"], "anchor_source": pt["source"]}

    def anchor(self, record):
        """Anchor for a record, or None if its location cannot be resolved."""
        loc = record["location"]
        if record["holding"]:
            adm3 = self._cadastral_of(record["holding"]["lon"], record["holding"]["lat"])
            area = self._area(adm3) if adm3 else None
            if area:
                return {**area, "location_basis": "gps_area"}
        adm3 = self.overrides.get(record["respondent_id"])
        if adm3 and self._area(adm3):
            return {**self._area(adm3), "location_basis": "farm_area_reported"}
        special = self.locs.get(loc["locality_id"]) if loc["locality_id"] else None
        if special and special["kind"] in ("place", "unverified_place") and special["lon"]:
            return {"lon": float(special["lon"]), "lat": float(special["lat"]), "adm3_pcode": special["adm3_pcode"] or None,
                    "geom_origin": "osm_place_point" if special["kind"] == "place" else "legacy_manual_point",
                    "spatial_precision": "locality" if special["kind"] == "place" else "unverified_locality",
                    "area_name_en": special["name_en"], "area_name_ar": special["name_ar"],
                    "district_en": special["adm2_name_en"], "district_ar": special["adm2_name_ar"],
                    "anchor_source": special["point_source"], "location_basis": "residence_village"}
        if loc["adm3_pcode"] and self._area(loc["adm3_pcode"]):
            return {**self._area(loc["adm3_pcode"]), "location_basis": "residence_village"}
        return None

    def layout(self, placed):
        """placed: list of (record, anchor). Returns {response_id: (lon, lat, offset_m)}."""
        groups = {}
        for record, a in placed:
            groups.setdefault((a["lon"], a["lat"]), []).append((record, a))
        out = {}
        for (lon, lat), members in groups.items():
            members.sort(key=lambda m: m[0]["respondent_id"])
            cx, cy = _TO_M(lon, lat)
            poly = self.polys.get(members[0][1]["adm3_pcode"])
            poly_m = transform(_TO_M, poly) if poly is not None else None
            for i, (record, _) in enumerate(members):
                r = 0.0 if len(members) == 1 else STEP_M * math.sqrt(i + 0.5)
                angle = i * GOLDEN
                x, y = cx + r * math.cos(angle), cy + r * math.sin(angle)
                shrink = 0
                while poly_m is not None and not poly_m.contains(Point(x, y)) and shrink < 8:
                    r *= 0.7
                    x, y = cx + r * math.cos(angle), cy + r * math.sin(angle)
                    shrink += 1
                plon, plat = _TO_DEG(x, y)
                out[record["response_id"]] = (round(plon, 5), round(plat, 5), int(round(r)))
        return out
