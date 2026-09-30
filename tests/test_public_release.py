"""Invariants of the committed public release (public/data), i.e. exactly what Pages serves."""
import hashlib
import json
import re

import pytest
from shapely.geometry import shape

from resolve.dictionary import load
from resolve.paths import PUBLIC, PUBLIC_DATA
from resolve.validate import check_public_catalog, in_lebanon

ENTITY_GEOMETRIES = {
    "village_survey_summary": {"Polygon", "MultiPolygon"},
    "district_survey_summary": {"Polygon", "MultiPolygon"},
    "fire_detection": {"Point"},
    "protected_area": {"Polygon", "MultiPolygon"},
    "survey_respondent_public": {"Point"},
}
PIN_FILE = "survey_respondents."
RESPONDENT_ID = re.compile(r"\b(CH|BQ)-[2-9A-HJ-NP-Z]{6}\b")


@pytest.fixture(scope="module")
def catalog():
    return json.loads((PUBLIC_DATA / "catalog.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def collections(catalog):
    out = {}
    for layer in catalog["layers"]:
        out[layer["id"]] = json.loads((PUBLIC / layer["file"]).read_text(encoding="utf-8"))
    return out


def _coords(geometry):
    stack = [geometry["coordinates"]]
    while stack:
        c = stack.pop()
        if isinstance(c[0], (int, float)):
            yield c
        else:
            stack.extend(c)


def test_catalog_is_public_tier(catalog):
    assert catalog["tier"] == "public"
    assert catalog["k_min_respondents"] >= 5


def test_catalog_only_describes_public_fields(catalog):
    d = load()
    public = {f.code for f in d.fields if f.is_public}
    assert set(catalog["fields"]) <= public


def test_validator_accepts_release(catalog, collections):
    assert check_public_catalog(catalog, collections, catalog["k_min_respondents"]) == []


def test_files_are_content_hashed(catalog):
    for layer in catalog["layers"]:
        path = PUBLIC / layer["file"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:10]
        assert path.name.split(".")[-2] == digest, f"{path.name} does not match its content hash"


def test_no_unreferenced_data_files(catalog):
    referenced = {PUBLIC / l["file"] for l in catalog["layers"]} | {PUBLIC_DATA / "catalog.json"}
    assert set(PUBLIC_DATA.iterdir()) == referenced


def test_geometry_valid_typed_and_inside_lebanon(collections):
    for name, fc in collections.items():
        for f in fc["features"]:
            etype = f["properties"]["entity_type"]
            assert f["geometry"]["type"] in ENTITY_GEOMETRIES[etype], f"{name}/{f['id']}"
            assert shape(f["geometry"]).is_valid, f"{name}/{f['id']} invalid geometry"
            for lon, lat in _coords(f["geometry"]):
                assert in_lebanon(lon, lat), f"{name}/{f['id']} outside Lebanon"
                assert round(lon, 5) == lon and round(lat, 5) == lat, f"{name}/{f['id']} over-precise coordinates"


def test_every_feature_declares_location_provenance(collections):
    for fc in collections.values():
        for f in fc["features"]:
            assert f["properties"].get("geom_origin") and f["properties"].get("spatial_precision")


def test_survey_summaries_respect_k(catalog, collections):
    k = catalog["k_min_respondents"]
    for layer in catalog["layers"]:
        if layer["renderer"] != "survey_summary":
            continue
        for f in collections[layer["id"]]["features"]:
            p = f["properties"]
            assert p["n_respondents"] >= k
            for summaries in (p.get("indicators", {}), p.get("remainder_indicators", {})):
                for s in summaries.values():
                    if s["counts"] is not None:
                        assert s["n_answered"] >= k


def test_respondent_ids_only_on_pins():
    for path in PUBLIC_DATA.iterdir():
        if path.name.startswith(PIN_FILE):
            continue
        assert not RESPONDENT_ID.search(path.read_text(encoding="utf-8")), f"respondent ID in {path.name}"


def test_pins_carry_only_public_village_answers(collections):
    d = load()
    allowed = {f.code for f in d.fields if f.privacy == "public_village"}
    identity = {f.code for f in d.fields if f.privacy == "identity"}
    pins = [f for fc in collections.values() for f in fc["features"] if f["properties"]["entity_type"] == "survey_respondent_public"]
    assert pins, "public pins layer is empty"
    for f in pins:
        p = f["properties"]
        assert set(p["values"]) <= allowed and set(p["status"]) <= allowed, f["id"]
        assert not identity & set(p), f["id"]
        assert p["spatial_precision"] in ("locality", "unverified_locality")


def test_pins_sit_near_their_village_settlement(collections):
    pins = [f for fc in collections.values() for f in fc["features"] if f["properties"]["entity_type"] == "survey_respondent_public"]
    for f in pins:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        alon, alat = p["anchor"]
        assert ((lon - alon) * 92.5) ** 2 + ((lat - alat) * 111.0) ** 2 <= 1.0, f["id"]
        assert p["location_basis"] in ("gps_area", "farm_area_reported", "residence_village")
        assert p["spatial_precision"] in ("locality", "unverified_locality")
