"""Build releases.

public    -> public/data/ (committed, deployed to GitHub Pages): disclosure-controlled survey
             summaries, approximate respondent pins identified only by ID, analysis insights
             and public reference layers. Allow-list driven by the field dictionary.
research  -> <private store>/build/research/data/ (local only): standardized respondent
             records with ID, name and phone, all villages, research fields.
Both are described by a catalog.json that the web map reads to register layers, popups,
legends, filters and the insights panel; the frontend has no dataset-specific code.
"""
import hashlib
import json
import shutil

from . import SCHEMA_VERSION, analysis, placement, rawstore, reference, sdc, survey
from .dictionary import CODED_TYPES, STATUSES, load
from .gazetteer import localities
from .paths import PUBLIC_DATA, private_root
from .validate import ValidationError, check_public_catalog, check_records

DEFAULT_K = 5
DEFAULT_INDICATOR = "farmer_type"
PIN_FILTER_FIELDS = ["farmer_type", "water_availability", "water_sources", "energy_sources", "crop_groups",
                     "chem_fertilizer_reliance", "pesticide_reliance", "low_input_practices", "land_size_band",
                     "production_level", "coop_member"]


def _dump(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=False)


def _write_hashed(directory, stem, obj):
    body = _dump(obj).encode("utf-8")
    name = f"{stem}.{hashlib.sha256(body).hexdigest()[:10]}.geojson"
    (directory / name).write_bytes(body)
    return name, body


def _fc(features):
    return {"type": "FeatureCollection", "features": features}


def _json_write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def _fresh_dir(path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def _replace_dir(src, dst):
    """Make dst contain exactly src's files (file-level; avoids Windows directory-rename locks)."""
    dst.mkdir(parents=True, exist_ok=True)
    new = {p.name for p in src.iterdir()}
    for old in dst.iterdir():
        if old.name not in new:
            old.unlink()
    for p in src.iterdir():
        shutil.copyfile(p, dst / p.name)
    shutil.rmtree(src, ignore_errors=True)


# ── catalog pieces ─────────────────────────────────────────────────────────

def _field_catalog(d, codes):
    fields, vocabs = {}, {}
    for f in d.fields:
        if f.code not in codes:
            continue
        entry = {"label": f.label, "type": f.type, "group": f.group, "privacy": f.privacy}
        if f.vocab:
            entry["vocab"] = f.vocab
            v = d.vocabularies[f.vocab]
            vocabs[f.vocab] = {"kind": v.kind, "codes": [{"code": c.code, "label": c.label} for c in v.codes]}
        if f.note:
            entry["note"] = f.note
        fields[f.code] = entry
    return fields, vocabs


PROPERTY_LABELS = {
    "acq_date": {"en": "Detection date", "ar": "تاريخ الرصد"},
    "acq_time_utc": {"en": "Time (UTC)", "ar": "الوقت (UTC)"},
    "day_night": {"en": "Day / night pass", "ar": "نهار / ليل"},
    "name": {"en": "Name", "ar": "الاسم"},
    "name_original": {"en": "Original name", "ar": "الاسم الأصلي"},
    "designation": {"en": "Designation", "ar": "التصنيف"},
    "designation_type": {"en": "Designation level", "ar": "مستوى التصنيف"},
    "governance": {"en": "Governance", "ar": "الإدارة"},
    "reported_area_km2": {"en": "Reported area (km²)", "ar": "المساحة المعلنة (كم²)"},
    "gis_area_km2": {"en": "GIS area (km²)", "ar": "المساحة المحسوبة (كم²)"},
    "verification": {"en": "Verification", "ar": "التحقق"},
    "respondent_id": {"en": "ID", "ar": "المعرّف"},
    "instrument": {"en": "Survey", "ar": "الاستبيان"},
    "area_name_en": {"en": "Area", "ar": "المنطقة"},
    "spatial_precision": {"en": "Location precision", "ar": "دقة الموقع"},
    "uncertainty_m": {"en": "Location uncertainty (m)", "ar": "هامش خطأ الموقع (م)"},
    "fire_detections_5km": {"en": "Satellite fire detections within 5 km (Jun 2024 – Feb 2025)",
                            "ar": "حرائق مرصودة ضمن 5 كم (حزيران 2024 – شباط 2025)"},
    "protected_area_km": {"en": "Distance to nearest protected area (km)", "ar": "المسافة إلى أقرب محمية (كم)"},
}

PRECISION_LABELS = {
    "exact": {"en": "Exact (GPS reported by respondent)", "ar": "دقيق (إحداثيات من المستجيب)"},
    "cadastral_unit": {"en": "Cadastral area (not a farm location)", "ar": "منطقة عقارية (ليست موقع المزرعة)"},
    "locality": {"en": "Locality point (approximate)", "ar": "نقطة المنطقة (تقريبية)"},
    "unverified_locality": {"en": "Unverified locality point", "ar": "نقطة منطقة غير مؤكدة"},
    "district": {"en": "District (caza)", "ar": "القضاء"},
    "satellite_pixel": {"en": "Satellite pixel centre (≈375 m–1 km)", "ar": "مركز بكسل القمر الصناعي"},
    "source_polygon": {"en": "Source polygon", "ar": "مضلع المصدر"},
    "unknown": {"en": "Unknown", "ar": "غير معروف"},
}


def _base_catalog(d, tier, k, field_codes, insights):
    fields, vocabs = _field_catalog(d, field_codes)
    return {
        "schema_version": SCHEMA_VERSION,
        "tier": tier,
        "k_min_respondents": k,
        "statuses": STATUSES,
        "precisions": PRECISION_LABELS,
        "groups": d.groups,
        "fields": fields,
        "vocabularies": vocabs,
        "property_labels": PROPERTY_LABELS,
        "datasets": {n: d.datasets[n] for n in ("farmer_survey", "fire_detections", "protected_areas", "admin_districts")},
        "instruments": {n: {"title": i["title"], "collected": i["collected"]} for n, i in d.instruments.items()},
        "insights": insights,
        "layers": [],
    }


def _public_insights(report):
    """Aggregate-only view of the analysis (every figure rests on >= 5 respondents per cell)."""
    t = report["typology"]
    return {
        "typology": {k: t[k] for k in ("published", "method", "n", "k", "stability_ari", "candidates")} | {
            "types": [{k: p[k] for k in ("code", "letter", "name", "size", "regions", "traits")} for p in t["profiles"]]
                     if t["published"] else []},
        "drivers": {name: {k: v for k, v in r.items() if k != "tests_run"} | {"tests_run": r["tests_run"],
                    "findings": [{k: f[k] for k in ("field", "code", "label", "n_with", "n_without", "rate_with",
                                                     "rate_without", "or", "ci", "q")} for f in r["findings"]]}
                    for name, r in report["drivers"].items()},
    }


# ── features ───────────────────────────────────────────────────────────────

def _modes(indicators, prefix="mode__"):
    return {prefix + code: s["mode"] for code, s in indicators.items() if s.get("mode")}


def _survey_features(villages, districts, context):
    locs = {r["adm3_pcode"]: r for r in localities().values() if r["kind"] == "cadastral"}
    adm2_names = {r["adm2_pcode"]: (r["adm2_name_en"], r["adm2_name_ar"]) for r in localities().values() if r["adm2_pcode"]}
    adm3_geo = reference.admin_units(3, {v["adm3_pcode"] for v in villages}, simplify=0.0003)
    adm2_geo = reference.admin_units(2, {x["adm2_pcode"] for x in districts}, simplify=0.001)
    village_features = []
    for v in villages:
        loc = locs[v["adm3_pcode"]]
        village_features.append({
            "type": "Feature", "id": f"village:{v['adm3_pcode']}",
            "geometry": adm3_geo[v["adm3_pcode"]]["geometry"],
            "properties": {
                "entity_type": "village_survey_summary",
                "name_en": loc["adm3_name_en"], "name_ar": loc["adm3_name_ar"],
                "district_en": loc["adm2_name_en"], "district_ar": loc["adm2_name_ar"],
                "adm3_pcode": v["adm3_pcode"], "adm2_pcode": v["adm2_pcode"],
                "n_respondents": v["n_respondents"], "instruments": v["instruments"],
                "geom_origin": "cadastral_unit_polygon", "spatial_precision": "cadastral_unit",
                "context": context.get(v["adm3_pcode"], {}),
                **_modes(v["indicators"]),
                "indicators": v["indicators"],
            },
        })
    district_features = []
    for x in districts:
        name_en, name_ar = adm2_names[x["adm2_pcode"]]
        district_features.append({
            "type": "Feature", "id": f"district:{x['adm2_pcode']}",
            "geometry": adm2_geo[x["adm2_pcode"]]["geometry"],
            "properties": {
                "entity_type": "district_survey_summary",
                "name_en": name_en, "name_ar": name_ar, "adm2_pcode": x["adm2_pcode"],
                "n_respondents": x["n_respondents"], "n_remainder": x["n_remainder"],
                "remainder_villages": x["remainder_villages"], "instruments": x["instruments"],
                "geom_origin": "district_polygon", "spatial_precision": "district",
                **_modes(x["remainder_indicators"]),
                "indicators": x["indicators"],
                "remainder_indicators": x["remainder_indicators"],
            },
        })
    return village_features, district_features


def _primary(value):
    return value[0] if isinstance(value, list) else value


def _pins(records, codes, placer, extra=None):
    """One pin per respondent, placed by resolve.placement (best location evidence available).

    The geometry is the display position: the area's settlement point plus a small spread so pins
    do not overlap. The anchor, the evidence used and the offset are recorded on every pin.
    """
    d = load()
    coded = {f.code for f in d.fields if f.type in CODED_TYPES}
    placed = [(r, a) for r in records if (a := placer.anchor(r)) is not None]
    positions = placer.layout(placed)
    features = []
    for r, a in placed:
        lon, lat, offset = positions[r["response_id"]]
        props = {
            "entity_type": "survey_respondent_public" if extra is None else "survey_respondent",
            "respondent_id": r["respondent_id"], "instrument": r["instrument"],
            "area_name_en": a["area_name_en"], "area_name_ar": a["area_name_ar"],
            "district_en": a["district_en"], "district_ar": a["district_ar"],
            "location_basis": a["location_basis"], "geom_origin": a["geom_origin"],
            "spatial_precision": a["spatial_precision"], "anchor": [round(a["lon"], 5), round(a["lat"], 5)],
            "display_offset_m": offset,
            **{f"c__{c}": _primary(r["values"][c]) for c in codes if c in coded and r["status"][c] == "reported"},
            "values": {c: r["values"][c] for c in codes},
            "status": {c: r["status"][c] for c in codes},
        }
        if extra:
            props.update(extra(r))
        features.append({"type": "Feature", "id": r["response_id"],
                         "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": props})
    features.sort(key=lambda f: f["id"])
    return features


def _layers_for_pins(file_name, codes, research):
    title = ({"en": "Respondents (research, identifiable)", "ar": "المستجيبون (بحثي، يتضمن الهوية)"} if research
             else {"en": "Survey respondents (approximate pins)", "ar": "المستجيبون (مواقع تقريبية)"})
    layer = {"id": "survey-respondents", "dataset": "farmer_survey", "file": f"data/{file_name}", "renderer": "pins",
             "title": title, "color": "#4a4a4a", "cluster": True, "visible": True,
             "indicators": [c for c in codes if load().field(c).type in CODED_TYPES],
             "filter_fields": [c for c in PIN_FILTER_FIELDS if c in codes], "id_search": True,
             "default_indicator": DEFAULT_INDICATOR}
    if research:
        layer["identity_properties"] = ["respondent_id", "name_latin", "name_arabic", "phone"]
    return layer


def _reference(out_dir, files, fire, areas):
    fire_file, body = _write_hashed(out_dir, "fire_detections", _fc(fire)); files[fire_file] = body
    pa_file, body = _write_hashed(out_dir, "protected_areas", _fc(areas)); files[pa_file] = body
    protected = {"id": "protected-areas", "dataset": "protected_areas", "file": f"data/{pa_file}", "renderer": "polygons",
                 "title": {"en": "Protected areas", "ar": "المحميات"}, "color": "#0b6e4f", "outline": "strong",
                 "visible": True, "label_property": "name",
                 "popup_properties": ["name", "name_original", "designation", "designation_type", "governance",
                                      "reported_area_km2", "gis_area_km2", "verification"]}
    fire_layer = {"id": "fire", "dataset": "fire_detections", "file": f"data/{fire_file}", "renderer": "points",
                  "title": {"en": "Fire detections", "ar": "رصد الحرائق"}, "color": "#d7301f", "cluster": True,
                  "visible": False, "heatmap": True, "popup_properties": ["acq_date", "acq_time_utc", "day_night"],
                  "filters": [{"property": "acq_date", "type": "date_range"}, {"property": "day_night", "type": "choice"}]}
    return protected, fire_layer


# ── releases ───────────────────────────────────────────────────────────────

def build_public(records, report, fire, areas, context, k=DEFAULT_K):
    d = load()
    villages, districts, log = sdc.summarize(records, k)
    village_feats, district_feats = _survey_features(villages, districts, context)

    # Pins: every respondent in their best-evidenced village area (user decision 2026-09-30).
    pin_codes = [f.code for f in d.fields if f.privacy == "public_village"]
    pins = _pins(records, pin_codes, placement.Placer())

    tmp = _fresh_dir(PUBLIC_DATA.parent / "data.tmp")
    files = {}
    names = {}
    for stem, feats in (("survey_villages", village_feats), ("survey_districts", district_feats), ("survey_respondents", pins)):
        names[stem], files[stem] = _write_hashed(tmp, stem, _fc(feats))
    protected, fire_layer = _reference(tmp, files, fire, areas)

    district_codes = [f.code for f in d.fields if f.privacy == "public_district"]
    catalog = _base_catalog(d, "public", k, set(pin_codes + district_codes), _public_insights(report))
    catalog["layers"] = [
        protected,
        {"id": "survey-districts", "dataset": "farmer_survey", "file": f"data/{names['survey_districts']}",
         "renderer": "survey_summary", "title": {"en": "Survey – district summaries", "ar": "الاستبيان – ملخصات الأقضية"},
         "visible": False, "indicators": pin_codes, "sensitive_indicators": district_codes,
         "summary_key": "remainder_indicators", "default_indicator": DEFAULT_INDICATOR},
        {"id": "survey-villages", "dataset": "farmer_survey", "file": f"data/{names['survey_villages']}",
         "renderer": "survey_summary", "title": {"en": "Survey – village summaries", "ar": "الاستبيان – ملخصات القرى"},
         "visible": True, "indicators": pin_codes, "summary_key": "indicators", "default_indicator": DEFAULT_INDICATOR},
        fire_layer,
        _layers_for_pins(names["survey_respondents"], pin_codes, research=False),
    ]
    catalog["release"] = {
        "id": hashlib.sha256(b"".join(files[n] for n in sorted(files))).hexdigest()[:12],
        "villages_published": len(village_feats), "districts_published": len(district_feats),
        "respondent_pins": len(pins),
        "respondent_pins_by_location_basis": {b: sum(1 for p in pins if p["properties"]["location_basis"] == b)
                                              for b in ("gps_area", "farm_area_reported", "residence_village")},
        "respondents_in_summaries": sum(x["n_respondents"] for x in districts),
        "respondents_excluded_no_location": len(log["excluded_no_location"]),
    }
    fcs = {"survey_villages": _fc(village_feats), "survey_districts": _fc(district_feats),
           "survey_respondents": _fc(pins), "fire_detections": _fc(fire), "protected_areas": _fc(areas)}
    problems = check_public_catalog(catalog, fcs, k)
    if problems:
        shutil.rmtree(tmp)
        raise ValidationError(problems)
    (tmp / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    _replace_dir(tmp, PUBLIC_DATA)
    return catalog, log


def build_research(records, identity, report, fire, areas, context):
    """Local research release with identifiers. Written only inside the private store."""
    d = load()
    out_dir = _fresh_dir(private_root() / "build" / "research" / "data")
    ident = {i["respondent_id"]: i for i in identity}
    locs = localities()

    def extra(r):
        loc = r["location"]
        return {**{k: ident[r["respondent_id"]].get(k) for k in ("name_latin", "name_arabic", "phone")},
                "uncertainty_m": loc["uncertainty_m"], "point_source": loc["point_source"], "source": r["source"]}

    all_codes = [f.code for f in d.fields if f.privacy != "identity"]
    pins = _pins(records, all_codes, placement.Placer(), extra)
    holdings = [{"type": "Feature", "id": f"holding:{r['respondent_id']}",
                 "geometry": {"type": "Point", "coordinates": [r["holding"]["lon"], r["holding"]["lat"]]},
                 "properties": {"entity_type": "holding", "respondent_id": r["respondent_id"],
                                "geom_origin": r["holding"]["geom_origin"], "spatial_precision": r["holding"]["spatial_precision"],
                                "uncertainty_m": r["holding"]["uncertainty_m"]}}
                for r in records if r["holding"]]
    villages, districts, _ = sdc.summarize(records, 1)
    village_feats, _ = _survey_features(villages, districts, context)
    files, names = {}, {}
    for stem, feats in (("respondents", pins), ("holdings", holdings), ("survey_villages", village_feats)):
        names[stem], files[stem] = _write_hashed(out_dir, stem, _fc(feats))
    protected, fire_layer = _reference(out_dir, files, fire, areas)

    village_codes = [f.code for f in d.fields if f.privacy == "public_village"]
    catalog = _base_catalog(d, "research", 1, {f.code for f in d.fields}, _public_insights(report))
    catalog["layers"] = [
        protected,
        {"id": "survey-villages", "dataset": "farmer_survey", "file": f"data/{names['survey_villages']}",
         "renderer": "survey_summary", "title": {"en": "Survey – all villages", "ar": "الاستبيان – كل القرى"},
         "visible": False, "indicators": village_codes, "summary_key": "indicators", "default_indicator": DEFAULT_INDICATOR},
        fire_layer,
        {"id": "holdings", "dataset": "farmer_survey", "file": f"data/{names['holdings']}", "renderer": "points",
         "title": {"en": "Farm locations reported by GPS", "ar": "مواقع مزارع بإحداثيات"}, "color": "#b15928",
         "visible": True, "popup_properties": ["respondent_id", "spatial_precision", "uncertainty_m"]},
        _layers_for_pins(names["respondents"], all_codes, research=True),
    ]
    _json_write(out_dir / "catalog.json", catalog)
    return out_dir, len(pins), len(holdings)


def build(tier="all", k=DEFAULT_K):
    """Adapters -> analysis -> validation -> canonical -> releases. Returns a summary dict."""
    root = private_root()
    raw_files = rawstore.verify()
    records, identity, issues, new_ids = survey.build_staging()
    _json_write(root / "staging" / "survey_responses.json", records)
    _json_write(root / "staging" / "survey_identity.json", identity)
    _json_write(root / "staging" / "review_issues.json", issues)

    report = analysis.derive(records)  # adds farmer_type / low_input_practices to every record
    problems = check_records(records, identity)
    errors = [i for i in issues if i["severity"] == "error"]
    if problems or errors:
        raise ValidationError(problems + [f"{e['rule']} {e['instrument']} row {e['source_row']}: {e['message']}" for e in errors])
    _json_write(root / "canonical" / "survey_responses.json", records)
    _json_write(root / "canonical" / "survey_identity.json", identity)
    _json_write(root / "build" / "analysis_report.json", report)

    fire, areas = reference.fire_detections(), reference.protected_areas()
    units = reference.admin_units(3, {r["location"]["adm3_pcode"] for r in records if r["location"]["adm3_pcode"]}, simplify=None)
    context = analysis.spatial_context(units, fire, areas)

    summary = {"raw_files_verified": raw_files, "records": len(records), "new_ids": new_ids, "review_issues": len(issues),
               "typology": {"published": report["typology"]["published"], "k": report["typology"]["k"],
                            "stability_ari": report["typology"]["stability_ari"]},
               "drivers": {n: {"findings": len(r["findings"]), **r["model"]} for n, r in report["drivers"].items()}}
    if tier in ("public", "all"):
        catalog, log = build_public(records, report, fire, areas, context, k)
        _json_write(root / "build" / "public_sdc_log.json", log)
        summary["public"] = catalog["release"]
    if tier in ("research", "all"):
        out_dir, n, h = build_research(records, identity, report, fire, areas, context)
        summary["research"] = {"dir": str(out_dir), "respondent_points": n, "holding_points": h}
    return summary
