"""Locality spine: survey village strings -> official cadastral units (OCHA COD-AB admin 3).

ref/locality_aliases.csv     every reported spelling -> locality_id (+ how it was resolved)
ref/special_localities.csv   places that are not whole cadastral units (OSM or legacy points)
ref/localities.csv           generated: one row per referenced locality with admin codes and a
                             representative point with its source and uncertainty
"""
import csv
import json
import math
from functools import lru_cache

from shapely.geometry import Point, shape

from .paths import REF, codab_dir
from .textnorm import clean, key

LOCALITY_COLUMNS = [
    "locality_id", "kind", "name_en", "name_ar",
    "adm3_pcode", "adm3_name_en", "adm3_name_ar",
    "adm2_pcode", "adm2_name_en", "adm2_name_ar",
    "adm1_pcode", "adm1_name_en", "adm1_name_ar",
    "lon", "lat", "point_source", "uncertainty_m",
]


def _read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def read_aliases():
    return _read_csv(REF / "locality_aliases.csv")


@lru_cache(maxsize=1)
def localities():
    return {row["locality_id"]: row for row in _read_csv(REF / "localities.csv")}


@lru_cache(maxsize=1)
def _alias_index():
    index = {}
    for row in read_aliases():
        k = (row["instrument"], key(row["alias"]))
        if k in index:
            raise ValueError(f"duplicate alias {row['alias']!r} for {row['instrument']}")
        index[k] = row
    return index


def resolve(instrument, reported):
    """Return (locality row or None, alias row or None) for a reported village string."""
    text = clean(reported)
    if text is None:
        return None, None
    alias = _alias_index().get((instrument, key(text)))
    if alias is None or not alias["locality_id"]:
        return None, alias
    return localities()[alias["locality_id"]], alias


def _codab(level):
    with open(codab_dir() / f"lbn_admin{level}.geojson", encoding="utf-8") as fh:
        return json.load(fh)["features"]


def build_localities():
    """Regenerate ref/localities.csv from the alias tables and COD-AB (needs the private store)."""
    adm3 = {f["properties"]["adm3_pcode"]: f for f in _codab(3)}
    adm2 = [(shape(f["geometry"]), f["properties"]) for f in _codab(2)]

    def adm2_of(lon, lat):
        pt = Point(lon, lat)
        for geom, props in adm2:
            if geom.contains(pt):
                return props
        return None

    def admin_cols(p2):
        return {
            "adm2_pcode": p2["adm2_pcode"], "adm2_name_en": p2["adm2_name"], "adm2_name_ar": p2["adm2_name1"],
            "adm1_pcode": p2["adm1_pcode"], "adm1_name_en": p2["adm1_name"], "adm1_name_ar": p2["adm1_name1"],
        }

    rows = {}
    for alias in read_aliases():
        loc_id = alias["locality_id"]
        if not loc_id or loc_id in rows or not loc_id.startswith("adm3:"):
            continue
        props = adm3[loc_id.split(":", 1)[1]]["properties"]
        radius = math.sqrt(props["area_sqkm"] / math.pi) * 1000
        rows[loc_id] = {
            "locality_id": loc_id, "kind": "cadastral",
            "name_en": props["adm3_name"], "name_ar": props["adm3_name1"],
            "adm3_pcode": props["adm3_pcode"], "adm3_name_en": props["adm3_name"], "adm3_name_ar": props["adm3_name1"],
            "adm2_pcode": props["adm2_pcode"], "adm2_name_en": props["adm2_name"], "adm2_name_ar": props["adm2_name1"],
            "adm1_pcode": props["adm1_pcode"], "adm1_name_en": props["adm1_name"], "adm1_name_ar": props["adm1_name1"],
            "lon": f"{props['center_lon']:.5f}", "lat": f"{props['center_lat']:.5f}",
            "point_source": "COD-AB cadastral unit centre",
            "uncertainty_m": str(int(round(radius, -2))),
        }

    for special in _read_csv(REF / "special_localities.csv"):
        lon, lat = float(special["lon"]), float(special["lat"])
        row = {
            "locality_id": special["locality_id"],
            "kind": "place" if special["adm3_pcode"] else "unverified_place",
            "name_en": special["name_en"], "name_ar": special["name_ar"],
            "adm3_pcode": "", "adm3_name_en": "", "adm3_name_ar": "",
            "lon": f"{lon:.5f}", "lat": f"{lat:.5f}",
            "point_source": special["point_source"], "uncertainty_m": special["uncertainty_m"],
        }
        if special["adm3_pcode"]:
            p3 = adm3[special["adm3_pcode"]]["properties"]
            if not shape(adm3[special["adm3_pcode"]]["geometry"]).contains(Point(lon, lat)):
                raise ValueError(f"{special['locality_id']} point is not inside cadastral {special['adm3_pcode']}")
            row.update({"adm3_pcode": p3["adm3_pcode"], "adm3_name_en": p3["adm3_name"], "adm3_name_ar": p3["adm3_name1"]})
        district = adm2_of(lon, lat)
        if district is None:
            if special["adm3_pcode"]:
                raise ValueError(f"{special['locality_id']} lies outside every district")
            # Unverifiable point outside Lebanon: keep the place but assign no admin unit.
            row["kind"] = "unresolved"
            row.update({k: "" for k in ("adm2_pcode", "adm2_name_en", "adm2_name_ar",
                                         "adm1_pcode", "adm1_name_en", "adm1_name_ar")})
        else:
            row.update(admin_cols(district))
        rows[row["locality_id"]] = row

    missing = {a["locality_id"] for a in read_aliases() if a["locality_id"]} - set(rows)
    if missing:
        raise ValueError(f"aliases reference undefined localities: {sorted(missing)}")

    with open(REF / "localities.csv", "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=LOCALITY_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for loc_id in sorted(rows):
            writer.writerow(rows[loc_id])
    localities.cache_clear()
    return len(rows)
