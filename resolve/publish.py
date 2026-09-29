"""Build releases.

public    -> public/data/ (committed, deployed to GitHub Pages): disclosure-controlled survey
             summaries plus public reference layers. Allow-list driven by the field dictionary.
research  -> <private store>/build/research/data/ (local only): standardized respondent
             records with ID, name and phone, all villages, research fields.
Both are described by a catalog.json that the web map reads to register layers, popups,
legends and filters; the frontend has no dataset-specific code.
"""
import hashlib
import json
import shutil

from . import SCHEMA_VERSION, rawstore, reference, sdc, survey
from .dictionary import STATUSES, load
from .gazetteer import localities
from .paths import PUBLIC_DATA, private_root
from .validate import ValidationError, check_public_catalog, check_records

DEFAULT_K = 5
DEFAULT_INDICATOR = "water_availability"


def _dump(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=False)


def _write_hashed(directory, stem, obj):
    body = _dump(obj).encode("utf-8")
    name = f"{stem}.{hashlib.sha256(body).hexdigest()[:10]}.geojson"
    (directory / name).write_bytes(body)
    return name, body


def _fc(features):
    return {"type": "FeatureCollection", "features": features}


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


def _modes(indicators, prefix="mode__"):
    return {prefix + code: s["mode"] for code, s in indicators.items() if s.get("mode")}


def _survey_features(villages, districts):
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


REFERENCE_PROPERTY_LABELS = {
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
    "locality_name_en": {"en": "Locality", "ar": "المنطقة"},
    "spatial_precision": {"en": "Location precision", "ar": "دقة الموقع"},
    "uncertainty_m": {"en": "Location uncertainty (m)", "ar": "هامش خطأ الموقع (م)"},
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


def _base_catalog(d, tier, k, field_codes, datasets):
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
        "property_labels": REFERENCE_PROPERTY_LABELS,
        "datasets": {name: d.datasets[name] for name in datasets},
        "instruments": {n: {"title": i["title"], "collected": i["collected"]} for n, i in d.instruments.items()},
        "layers": [],
    }


def _reference_layers(out_dir, files):
    fire = reference.fire_detections()
    areas = reference.protected_areas()
    fire_file, fire_body = _write_hashed(out_dir, "fire_detections", _fc(fire))
    pa_file, pa_body = _write_hashed(out_dir, "protected_areas", _fc(areas))
    files.update({fire_file: fire_body, pa_file: pa_body})
    layers = [
        {"id": "protected-areas", "dataset": "protected_areas", "file": f"data/{pa_file}", "renderer": "polygons",
         "title": {"en": "Protected areas", "ar": "المحميات"}, "color": "#2e8b57", "visible": True,
         "label_property": "name", "popup_properties": ["name", "name_original", "designation", "designation_type",
                                                         "governance", "reported_area_km2", "gis_area_km2", "verification"]},
        {"id": "fire", "dataset": "fire_detections", "file": f"data/{fire_file}", "renderer": "points",
         "title": {"en": "Fire detections", "ar": "رصد الحرائق"}, "color": "#d7301f", "cluster": True, "visible": False,
         "heatmap": True, "popup_properties": ["acq_date", "acq_time_utc", "day_night"],
         "filters": [{"property": "acq_date", "type": "date_range"}, {"property": "day_night", "type": "choice"}]},
    ]
    return layers, {"fire_detections": fire, "protected_areas": areas}


def build_public(records, k=DEFAULT_K):
    d = load()
    villages, districts, log = sdc.summarize(records, k)
    village_feats, district_feats = _survey_features(villages, districts)

    tmp = PUBLIC_DATA.parent / "data.tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    files = {}
    v_file, body = _write_hashed(tmp, "survey_villages", _fc(village_feats)); files[v_file] = body
    d_file, body = _write_hashed(tmp, "survey_districts", _fc(district_feats)); files[d_file] = body
    ref_layers, ref_fcs = _reference_layers(tmp, files)

    village_codes = [f.code for f in d.fields if f.privacy == "public_village"]
    district_codes = [f.code for f in d.fields if f.privacy == "public_district"]
    catalog = _base_catalog(d, "public", k, set(village_codes + district_codes),
                            ["farmer_survey", "fire_detections", "protected_areas", "admin_districts"])
    protected = [l for l in ref_layers if l["id"] == "protected-areas"]
    others = [l for l in ref_layers if l["id"] != "protected-areas"]
    # Draw order (bottom -> top): context polygons, district summaries, village summaries, points.
    catalog["layers"] = protected + [
        {"id": "survey-districts", "dataset": "farmer_survey", "file": f"data/{d_file}", "renderer": "survey_summary",
         "title": {"en": "Survey – district summaries", "ar": "الاستبيان – ملخصات الأقضية"}, "visible": True,
         "indicators": village_codes, "sensitive_indicators": district_codes, "summary_key": "remainder_indicators",
         "default_indicator": DEFAULT_INDICATOR},
        {"id": "survey-villages", "dataset": "farmer_survey", "file": f"data/{v_file}", "renderer": "survey_summary",
         "title": {"en": "Survey – village summaries", "ar": "الاستبيان – ملخصات القرى"}, "visible": True,
         "indicators": village_codes, "summary_key": "indicators", "default_indicator": DEFAULT_INDICATOR},
    ] + others
    catalog["release"] = {
        "id": hashlib.sha256(b"".join(files[n] for n in sorted(files))).hexdigest()[:12],
        "villages_published": len(village_feats), "districts_published": len(district_feats),
        "respondents_in_summaries": sum(x["n_respondents"] for x in districts),
        "respondents_excluded_no_location": len(log["excluded_no_location"]),
    }

    fcs = {"survey_villages": _fc(village_feats), "survey_districts": _fc(district_feats), **{n: _fc(f) for n, f in ref_fcs.items()}}
    problems = check_public_catalog(catalog, fcs, k)
    if problems:
        shutil.rmtree(tmp)
        raise ValidationError(problems)

    (tmp / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    _replace_dir(tmp, PUBLIC_DATA)
    return catalog, log


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


def build_research(records, identity):
    """Local research release with identifiers. Written only inside the private store."""
    d = load()
    out_dir = private_root() / "build" / "research" / "data"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    ident = {i["respondent_id"]: i for i in identity}
    locs = localities()
    features, holdings = [], []
    for r in records:
        loc = r["location"]
        locality = locs.get(loc["locality_id"]) if loc["locality_id"] else None
        props = {
            "entity_type": "survey_respondent",
            "respondent_id": r["respondent_id"],
            "instrument": r["instrument"],
            **{k: ident[r["respondent_id"]].get(k) for k in ("name_latin", "name_arabic", "phone")},
            "locality_name_en": locality["name_en"] if locality else None,
            "locality_name_ar": locality["name_ar"] if locality else None,
            "geom_origin": loc["geom_origin"], "spatial_precision": loc["spatial_precision"],
            "uncertainty_m": loc["uncertainty_m"], "point_source": loc["point_source"],
            "values": r["values"], "status": r["status"], "source": r["source"],
        }
        geometry = {"type": "Point", "coordinates": [loc["lon"], loc["lat"]]} if loc["lon"] is not None else None
        features.append({"type": "Feature", "id": r["response_id"], "geometry": geometry, "properties": props})
        if r["holding"]:
            h = r["holding"]
            holdings.append({"type": "Feature", "id": f"holding:{r['respondent_id']}",
                             "geometry": {"type": "Point", "coordinates": [h["lon"], h["lat"]]},
                             "properties": {"entity_type": "holding", "respondent_id": r["respondent_id"],
                                            "name_latin": props["name_latin"], "name_arabic": props["name_arabic"],
                                            "geom_origin": h["geom_origin"], "spatial_precision": h["spatial_precision"],
                                            "uncertainty_m": h["uncertainty_m"]}})
    villages, districts, _ = sdc.summarize(records, 1)
    village_feats, district_feats = _survey_features(villages, districts)
    files = {}
    names = {}
    for stem, fc in (("respondents", _fc([f for f in features if f["geometry"]])), ("holdings", _fc(holdings)),
                     ("survey_villages", _fc(village_feats)), ("survey_districts", _fc(district_feats))):
        names[stem], files[stem] = _write_hashed(out_dir, stem, fc)
    ref_layers, _ = _reference_layers(out_dir, files)

    all_codes = {f.code for f in d.fields}
    catalog = _base_catalog(d, "research", 1, all_codes, ["farmer_survey", "fire_detections", "protected_areas", "admin_districts"])
    village_codes = [f.code for f in d.fields if f.privacy == "public_village"]
    district_codes = [f.code for f in d.fields if f.privacy == "public_district"]
    catalog["layers"] = [l for l in ref_layers if l["id"] == "protected-areas"] + [
        {"id": "survey-villages", "dataset": "farmer_survey", "file": f"data/{names['survey_villages']}",
         "renderer": "survey_summary", "title": {"en": "Survey – all villages", "ar": "الاستبيان – كل القرى"},
         "visible": False, "indicators": village_codes, "summary_key": "indicators", "default_indicator": DEFAULT_INDICATOR},
        {"id": "respondents", "dataset": "farmer_survey", "file": f"data/{names['respondents']}", "renderer": "respondents",
         "title": {"en": "Respondents (research, identifiable)", "ar": "المستجيبون (بحثي، يتضمن الهوية)"},
         "color": "#6a3d9a", "cluster": True, "visible": True,
         "identity_properties": ["respondent_id", "name_latin", "name_arabic", "phone"]},
        {"id": "holdings", "dataset": "farmer_survey", "file": f"data/{names['holdings']}", "renderer": "points",
         "title": {"en": "Farm locations reported by GPS", "ar": "مواقع مزارع بإحداثيات"}, "color": "#b15928",
         "visible": True, "popup_properties": ["respondent_id", "spatial_precision", "uncertainty_m"]},
    ] + [l for l in ref_layers if l["id"] != "protected-areas"]
    catalog["district_sensitive_indicators"] = district_codes
    (out_dir / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out_dir, sum(1 for f in features if f["geometry"]), len(holdings)


def build(tier="all", k=DEFAULT_K):
    """Adapters -> validation -> canonical -> releases. Returns a summary dict."""
    root = private_root()
    raw_files = rawstore.verify()
    records, identity, issues, new_ids = survey.build_staging()
    for sub in ("staging", "canonical"):
        (root / sub).mkdir(exist_ok=True)
    _json_write(root / "staging" / "survey_responses.json", records)
    _json_write(root / "staging" / "survey_identity.json", identity)
    _json_write(root / "staging" / "review_issues.json", issues)

    problems = check_records(records, identity)
    errors = [i for i in issues if i["severity"] == "error"]
    if problems or errors:
        raise ValidationError(problems + [f"{e['rule']} {e['instrument']} row {e['source_row']}: {e['message']}" for e in errors])
    _json_write(root / "canonical" / "survey_responses.json", records)
    _json_write(root / "canonical" / "survey_identity.json", identity)

    summary = {"raw_files_verified": raw_files, "records": len(records), "new_ids": new_ids, "review_issues": len(issues)}
    if tier in ("public", "all"):
        catalog, log = build_public(records, k)
        _json_write(root / "build" / "public_sdc_log.json", log)
        summary["public"] = catalog["release"]
    if tier in ("research", "all"):
        out_dir, n, h = build_research(records, identity)
        summary["research"] = {"dir": str(out_dir), "respondent_points": n, "holding_points": h}
    return summary


def _json_write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
