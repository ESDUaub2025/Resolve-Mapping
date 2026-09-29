"""Objective measures of the public release, comparable with the audit baseline (docs/metrics.md)."""
import json
import re

from .dictionary import load
from .paths import PUBLIC, PUBLIC_DATA, REPO

INDIVIDUAL_ENTITY_TYPES = {"survey_respondent", "holding"}


def measure():
    catalog = json.loads((PUBLIC_DATA / "catalog.json").read_text(encoding="utf-8"))
    d = load()
    payload = (PUBLIC_DATA / "catalog.json").stat().st_size
    features = individual = with_provenance = 0
    per_layer = {}
    for layer in catalog["layers"]:
        path = PUBLIC / layer["file"]
        payload += path.stat().st_size
        fc = json.loads(path.read_text(encoding="utf-8"))
        per_layer[layer["id"]] = len(fc["features"])
        for f in fc["features"]:
            features += 1
            p = f["properties"]
            individual += p.get("entity_type") in INDIVIDUAL_ENTITY_TYPES
            with_provenance += bool(p.get("geom_origin") and p.get("spatial_precision"))
    cards = catalog["datasets"].values()
    js = list((PUBLIC / "js").glob("*.js"))
    # Dataset-specific code = any catalog layer id or dataset name hard-coded in the frontend.
    names = {l["id"] for l in catalog["layers"]} | set(catalog["datasets"])
    pattern = re.compile(r"['\"`](" + "|".join(map(re.escape, sorted(names))) + r")['\"`]")
    branches = sum(len(pattern.findall(p.read_text(encoding="utf-8"))) for p in js)
    tests = sum(len(re.findall(r"^def test_", p.read_text(encoding="utf-8"), re.M)) for p in (REPO / "tests").rglob("test_*.py"))
    coded = [f for f in d.fields if f.privacy != "identity"]
    return {
        "public_payload_bytes": payload,
        "public_features": features,
        "features_per_layer": per_layer,
        "respondent_level_public_features": individual,
        "identity_fields_in_public_catalog": sum(1 for f in d.fields if f.privacy == "identity" and f.code in catalog["fields"]),
        "features_with_location_provenance_pct": round(100 * with_provenance / max(1, features), 1),
        "datasets_with_source_and_licence": f"{sum(1 for c in cards if c.get('source') and c.get('licence'))}/{len(catalog['datasets'])}",
        "dictionary_fields": len(coded),
        "dictionary_fields_with_controlled_vocab": sum(1 for f in coded if f.vocab),
        "public_fields": len(catalog["fields"]),
        "k_min_respondents": catalog["k_min_respondents"],
        "frontend_js_files": len(js),
        "frontend_dataset_specific_literals": branches,
        "automated_test_functions": tests,
    }
