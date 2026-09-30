"""Validation of canonical survey records and of public release files.

Critical violations raise ValidationError (build fails loudly); nothing is silently repaired.
"""
from .dictionary import CODED_TYPES, STATUSES, load

LEBANON_BBOX = (35.0, 33.0, 36.7, 34.75)
RECORD_STATUSES = set(STATUSES) - {"suppressed"}
GEOM_ORIGINS = {None, "cadastral_unit_centre", "osm_place_point", "legacy_manual_point"}
PRECISIONS = {"cadastral_unit", "locality", "unverified_locality", "district", "unknown"}


class ValidationError(ValueError):
    def __init__(self, problems):
        super().__init__(f"{len(problems)} critical validation problem(s):\n  " + "\n  ".join(problems[:50]))
        self.problems = problems


def in_lebanon(lon, lat):
    lon_min, lat_min, lon_max, lat_max = LEBANON_BBOX
    return lon_min <= lon <= lon_max and lat_min <= lat <= lat_max


def check_records(records, identity):
    """Invariants of canonical survey records. Returns the list of problems (empty = valid)."""
    d = load()
    problems = []
    ids = [r["response_id"] for r in records]
    if len(ids) != len(set(ids)):
        problems.append("response_id values are not unique")
    identity_codes = {f.code for f in d.fields if f.privacy == "identity"}
    by_code = {f.code: f for f in d.fields}
    for r in records:
        rid = r["response_id"]
        leaked = identity_codes & (set(r["values"]) | set(r["status"]) | set(r["raw"]))
        if leaked:
            problems.append(f"{rid}: identity fields {sorted(leaked)} present in the response record")
        expected = {f.code for f in d.fields if f.privacy != "identity"}
        if set(r["status"]) != expected:
            problems.append(f"{rid}: status must cover every dictionary field (missing {sorted(expected - set(r['status']))})")
        for code, status in r["status"].items():
            if status not in RECORD_STATUSES:
                problems.append(f"{rid}.{code}: unknown status {status!r}")
            value = r["values"].get(code)
            if (status == "reported") != (value is not None):
                problems.append(f"{rid}.{code}: status {status} inconsistent with value {value!r}")
            fld = by_code.get(code)
            if fld is None:
                problems.append(f"{rid}: field {code} not in the dictionary")
                continue
            if fld.type in CODED_TYPES and value is not None:
                allowed = set(d.vocabularies[fld.vocab].code_names)
                chosen = value if fld.type == "multi" else [value]
                if not isinstance(chosen, list) or not chosen or set(chosen) - allowed:
                    problems.append(f"{rid}.{code}: {value!r} not in vocabulary {fld.vocab}")
            if not fld.derived and r["instrument"] not in fld.sources and status != "not_asked":
                problems.append(f"{rid}.{code}: field not in instrument but status is {status}")
        loc = r["location"]
        if loc["geom_origin"] not in GEOM_ORIGINS or loc["spatial_precision"] not in PRECISIONS:
            problems.append(f"{rid}: invalid location provenance {loc['geom_origin']}/{loc['spatial_precision']}")
        if (loc["lon"] is None) != (loc["geom_origin"] is None):
            problems.append(f"{rid}: coordinates present without origin (or origin without coordinates)")
        if loc["lon"] is not None and not in_lebanon(loc["lon"], loc["lat"]):
            problems.append(f"{rid}: point {loc['lon']},{loc['lat']} outside Lebanon")
        if r["holding"] and not in_lebanon(r["holding"]["lon"], r["holding"]["lat"]):
            problems.append(f"{rid}: holding point outside Lebanon")
    ident_ids = {i["respondent_id"] for i in identity}
    if ident_ids != {r["respondent_id"] for r in records}:
        problems.append("identity table and responses do not cover the same respondents")
    return problems


def check_public_catalog(catalog, feature_collections, k):
    """Invariants of the public release (also enforced by tests/privacy on committed files)."""
    d = load()
    problems = []
    public_fields = {f.code for f in d.fields if f.is_public}
    non_public = {f.code for f in d.fields} - public_fields
    for name, fc in feature_collections.items():
        seen = set()
        for feat in fc["features"]:
            fid = feat.get("id")
            if not fid or fid in seen:
                problems.append(f"{name}: missing or duplicate feature id {fid!r}")
            seen.add(fid)
            props = feat["properties"]
            for required in ("entity_type", "geom_origin", "spatial_precision"):
                if required not in props:
                    problems.append(f"{name}/{fid}: missing {required}")
            if props.get("entity_type") in ("village_survey_summary", "district_survey_summary"):
                if props.get("n_respondents", 0) < k:
                    problems.append(f"{name}/{fid}: n_respondents {props.get('n_respondents')} < k={k}")
                published = set(props.get("indicators", {})) | set(props.get("remainder_indicators", {}))
                leaked = non_public & published
                if leaked:
                    problems.append(f"{name}/{fid}: non-public fields published {sorted(leaked)}")
                village_level = {f.code for f in d.fields if f.privacy == "public_district"} & set(props.get("indicators", {}))
                if props["entity_type"] == "village_survey_summary" and village_level:
                    problems.append(f"{name}/{fid}: district-only fields published at village level {sorted(village_level)}")
                for summary in list(props.get("indicators", {}).values()) + list(props.get("remainder_indicators", {}).values()):
                    if summary.get("counts") is not None and summary["n_answered"] < k:
                        problems.append(f"{name}/{fid}: distribution published from fewer than k answers")
    # Public respondent pins: ID only, public village-level answers only, placed near a real
    # settlement point of the respondent's village/farm area, with the evidence recorded.
    village_fields = {f.code for f in d.fields if f.privacy == "public_village"}
    identity_keys = {f.code for f in d.fields if f.privacy == "identity"}
    origins = {"osm_settlement_point", "point_inside_cadastral_area", "osm_place_point", "legacy_manual_point"}
    bases = {"gps_area", "farm_area_reported", "residence_village"}
    for name, fc in feature_collections.items():
        for feat in fc["features"]:
            p = feat["properties"]
            if p.get("entity_type") != "survey_respondent_public":
                continue
            fid = feat.get("id")
            if identity_keys & set(p) or identity_keys & set(p.get("values", {})):
                problems.append(f"{name}/{fid}: identity data on a public pin")
            extra = (set(p.get("values", {})) | set(p.get("status", {}))) - village_fields
            if extra:
                problems.append(f"{name}/{fid}: non-village-level fields on a public pin {sorted(extra)}")
            if p.get("geom_origin") not in origins or p.get("location_basis") not in bases:
                problems.append(f"{name}/{fid}: pin placement must record a known origin and evidence")
            if p.get("spatial_precision") not in ("locality", "unverified_locality"):
                problems.append(f"{name}/{fid}: pins are locality-level, never exact")
            alon, alat = p.get("anchor", (None, None))
            lon, lat = feat["geometry"]["coordinates"]
            if alon is None or ((lon - alon) * 92.5) ** 2 + ((lat - alat) * 111.0) ** 2 > 1.0:
                problems.append(f"{name}/{fid}: pin more than 1 km from its settlement anchor")
    for layer in catalog["layers"]:
        for code in layer.get("indicators", []):
            if code not in public_fields:
                problems.append(f"catalog layer {layer['id']}: indicator {code} is not public")
    return problems
