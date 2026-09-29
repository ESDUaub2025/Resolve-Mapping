"""Survey adapters: raw survey exports -> standardized response records (staging).

One record per respondent and instrument:
    values[field]  coded value (str), list of codes (multi), text or ISO date, or None
    status[field]  reported | not_provided | not_asked | not_applicable | invalid
    raw[field]     the original answer text, kept for audit (never normalized away)
Identifiers (names, phone) are split off into a separate identity table.
"""
import re
from dataclasses import asdict, dataclass

import pandas as pd

from . import gazetteer
from .dictionary import CODED_TYPES, load
from .ids import Registry
from .paths import private_root
from .textnorm import clean, key

LEBANON_BBOX = (35.0, 33.0, 36.7, 34.75)  # lon_min, lat_min, lon_max, lat_max
_PARENS = re.compile(r"\([^)]*\)")
_GPS = re.compile(r"(3[34]\.\d{3,})[\s,]+(3[56]\.\d{3,})(?:[\s,]+(-?\d+(?:\.\d+)?))?(?:[\s,]+(\d+(?:\.\d+)?))?")

GEOM = {
    # locality kind -> (geom_origin, spatial_precision)
    "cadastral": ("cadastral_unit_centre", "cadastral_unit"),
    "place": ("osm_place_point", "locality"),
    "unverified_place": ("legacy_manual_point", "unverified_locality"),
    "unresolved": (None, "unknown"),
}


@dataclass
class Issue:
    severity: str  # error | review
    rule: str
    instrument: str
    source_row: int
    field: str
    message: str


def _apply_strip(text, patterns):
    for p in patterns or []:
        text = re.sub(p, " ", text)
    return text


def _map_codes(fld, vocab, text, strip, issues, ctx):
    """Map free answer text to codes. Returns (value, status)."""
    candidates = vocab.codes_in(_apply_strip(text, strip))
    if fld.type == "multi":
        if not candidates:
            if "other" in vocab.code_names:
                issues.append(Issue("review", "unmapped_to_other", *ctx, fld.code, f"{text!r} coded as 'other'"))
                return ["other"], "reported"
            issues.append(Issue("review", "unmapped_value", *ctx, fld.code, f"{text!r} matches no code"))
            return None, "invalid"
        exclusive = [c for c in candidates if next(x for x in vocab.codes if x.code == c).exclusive]
        if exclusive and len(candidates) > len(exclusive):
            issues.append(Issue("review", "exclusive_with_others", *ctx, fld.code,
                                f"{text!r}: exclusive {exclusive} dropped alongside other answers"))
            candidates = [c for c in candidates if c not in exclusive]
        return vocab.expand(candidates), "reported"
    if len(candidates) == 1:
        return candidates[0], "reported"
    reason = "matches no code" if not candidates else f"is ambiguous between {candidates}"
    issues.append(Issue("review", "unmapped_value", *ctx, fld.code, f"{text!r} {reason}"))
    return None, "invalid"


def _onehot(fld, vocab, row, columns, prefix, issues, ctx):
    """KoBo select_multiple: columns '<prefix>/<option>' holding 0/1. Returns (codes, status, raw) or None."""
    options = [c for c in columns if c.startswith(prefix + "/")]
    if not options:
        raise KeyError(f"{fld.code}: no one-hot columns for prefix {prefix!r}")
    values = {c: pd.to_numeric(row[c], errors="coerce") for c in options}
    if all(pd.isna(v) for v in values.values()):
        return None
    selected = []
    for col, v in values.items():
        if v == 1:
            label = col[len(prefix) + 1:]
            codes = vocab.codes_in(_PARENS.sub(" ", label))
            if len(codes) != 1:
                raise ValueError(f"{fld.code}: option {label!r} maps to {codes}, expected exactly one code")
            selected.append(codes[0])
    if not selected:
        return [], "not_provided", None
    return vocab.expand(selected), "reported", " | ".join(col[len(prefix) + 1:].strip() for col, v in values.items() if v == 1)


def _parse(fld, vocab, src, row, columns, joined, issues, ctx):
    """Returns (value, status or None if missing, raw)."""
    if "onehot" in src:
        result = _onehot(fld, vocab, row, columns, src["onehot"], issues, ctx)
        if result is not None:
            codes, status, raw = result
            return (codes or None), status, raw
    if src.get("join"):
        answers = sorted({a for a in (clean(r.get(src["column"])) for r in joined.get(src["join"], [])) if a})
        if len(answers) > 1:
            issues.append(Issue("review", "conflicting_duplicates", *ctx, fld.code,
                                f"{len(answers)} different answers across duplicate source rows"))
            return None, "invalid", " || ".join(answers)
        raw = answers[0] if answers else None
    else:
        if src["column"] not in columns:
            raise KeyError(f"{fld.code}: column {src['column']!r} missing from source")
        raw = clean(row[src["column"]])
    if raw is None:
        return None, None, None
    if fld.type in CODED_TYPES:
        value, status = _map_codes(fld, vocab, raw, src.get("strip"), issues, ctx)
        return value, status, raw
    if fld.type == "date":
        parsed = pd.to_datetime(raw, errors="coerce")
        if pd.isna(parsed):
            issues.append(Issue("review", "bad_date", *ctx, fld.code, f"{raw!r} is not a date"))
            return None, "invalid", raw
        return parsed.date().isoformat(), "reported", raw
    return raw, "reported", raw


def _condition_holds(cond, values, statuses):
    parent = cond["field"]
    if statuses.get(parent) != "reported":
        return None  # unknown
    value = values.get(parent)
    chosen = value if isinstance(value, list) else [value]
    return any(v in cond["in"] for v in chosen)


def _holding_point(text):
    """Exact holding location if the respondent wrote GPS coordinates in the land-location answer."""
    if not text:
        return None
    m = _GPS.search(text)
    if not m:
        return None
    lat, lon = float(m.group(1)), float(m.group(2))
    lon_min, lat_min, lon_max, lat_max = LEBANON_BBOX
    if not (lon_min <= lon <= lon_max and lat_min <= lat <= lat_max):
        return None
    acc = float(m.group(4)) if m.group(4) else None
    return {"lon": round(lon, 6), "lat": round(lat, 6), "geom_origin": "gps_reported_by_respondent",
            "spatial_precision": "exact", "uncertainty_m": int(acc) if acc else None}


def _location(instrument, reported, issues, ctx):
    loc, alias = gazetteer.resolve(instrument, reported)
    out = {"village_reported": clean(reported), "locality_id": None, "resolution": None, "confidence": None,
           "adm3_pcode": None, "adm2_pcode": None, "adm1_pcode": None, "lon": None, "lat": None,
           "geom_origin": None, "spatial_precision": "unknown", "uncertainty_m": None, "point_source": None}
    if alias is None:
        issues.append(Issue("error", "unknown_village", *ctx, "village_reported",
                            f"village {reported!r} has no entry in ref/locality_aliases.csv"))
        return out
    out.update({"resolution": alias["resolution"], "confidence": alias["confidence"]})
    if loc is None:
        issues.append(Issue("review", "ambiguous_village", *ctx, "village_reported", alias["note"]))
        if alias.get("adm2_fallback"):
            out.update({"adm2_pcode": alias["adm2_fallback"], "spatial_precision": "district"})
        return out
    origin, precision = GEOM[loc["kind"]]
    out.update({
        "locality_id": loc["locality_id"], "adm3_pcode": loc["adm3_pcode"] or None,
        "adm2_pcode": loc["adm2_pcode"] or None, "adm1_pcode": loc["adm1_pcode"] or None,
        "geom_origin": origin, "spatial_precision": precision,
        "uncertainty_m": int(loc["uncertainty_m"]) if loc["uncertainty_m"] else None,
        "point_source": loc["point_source"],
    })
    if origin:
        out.update({"lon": float(loc["lon"]), "lat": float(loc["lat"])})
    if loc["kind"] == "unresolved":
        issues.append(Issue("review", "unresolved_village", *ctx, "village_reported", alias["note"]))
    return out


def _read_instrument(name, spec, root):
    path = root / spec["source_file"]
    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path, encoding="utf-8-sig", dtype=object)
        sheet = None
    else:
        frame = pd.read_excel(path, sheet_name=spec["source_sheet"], dtype=object)
        sheet = spec["source_sheet"]
    joins = {}
    for join_name, j in (spec.get("joins") or {}).items():
        other = pd.read_excel(path, sheet_name=j["sheet"], dtype=object)
        joins[join_name] = (j, other)
    return frame, sheet, joins


def adapt(instrument, registry, issues):
    d = load()
    spec = d.instruments[instrument]
    root = private_root()
    frame, sheet, joins = _read_instrument(instrument, spec, root)
    columns = list(frame.columns)
    fields = [f for f in d.fields if not f.derived]

    # Index joined sheets by the respondent key column of this instrument.
    join_index = {}
    for join_name, (j, other) in joins.items():
        key_field = d.field(j["key"])
        key_col = key_field.sources[instrument]["column"]
        index = {}
        for _, r in other.iterrows():
            index.setdefault(key(r.get(key_col)), []).append(r.to_dict())
        join_index[join_name] = (key_col, index)

    records, identity, seen = [], [], {}
    for idx, row in frame.iterrows():
        source_row = int(idx) + 2  # 1-based, after the header row
        ctx = (instrument, source_row)
        values, status, raw = {}, {}, {}
        joined = {name: index.get(key(row.get(key_col)), []) for name, (key_col, index) in join_index.items()}
        for fld in fields:
            src = fld.sources.get(instrument)
            if src is None:
                values[fld.code], status[fld.code], raw[fld.code] = None, "not_asked", None
                continue
            v, s, r = _parse(fld, d.vocab_for(fld), src, row, columns, joined, issues, ctx)
            values[fld.code], status[fld.code], raw[fld.code] = v, s, r
        for fld in fields:  # skip logic for missing answers
            if status[fld.code] is None:
                holds = _condition_holds(fld.applies_if, values, status) if fld.applies_if else True
                status[fld.code] = "not_applicable" if holds is False else "not_provided"

        key_values = [values[k] for k in spec["respondent_key"]]
        rid = registry.id_for(instrument, spec["id_prefix"], key_values)
        if rid in seen:
            issues.append(Issue("error", "duplicate_respondent", *ctx, "respondent_id",
                                f"same respondent key as source row {seen[rid]}"))
        seen[rid] = source_row

        identity.append({"respondent_id": rid, "instrument": instrument,
                         **{f.code: values.pop(f.code) for f in fields if f.privacy == "identity"}})
        for f in fields:
            if f.privacy == "identity":
                status.pop(f.code)
                raw.pop(f.code)

        records.append({
            "response_id": f"{rid}:{instrument}",
            "respondent_id": rid,
            "instrument": instrument,
            "source": {"file": spec["source_file"], "sheet": sheet, "row": source_row},
            "location": _location(instrument, row.get(d.field("village_reported").sources[instrument]["column"]), issues, ctx),
            "holding": _holding_point(values.get("land_location_text")),
            "values": values,
            "status": status,
            "raw": raw,
        })
    return records, identity


def build_staging():
    """Run all survey adapters; write staging files into the private store. Returns a summary."""
    root = private_root()
    registry = Registry(root / "registry" / "respondent_ids.csv")
    issues, records, identity = [], [], []
    for instrument in load().instruments:
        r, i = adapt(instrument, registry, issues)
        records += r
        identity += i
    registry.save()
    records.sort(key=lambda r: r["response_id"])
    identity.sort(key=lambda r: r["respondent_id"])
    return records, identity, [asdict(i) for i in issues], registry.new
