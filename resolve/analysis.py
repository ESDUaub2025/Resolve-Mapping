"""Stage 8 analysis on the standardized records (runs inside the private build).

Methods were chosen for ~200 respondents from two different surveys, and every result is
checked before it is published:

1. Farmer typology - k-means on the one-hot matrix of farming-practice answers. k (3–6) is
   chosen by bootstrap stability (adjusted Rand index); the typology is published only if the
   chosen k has mean ARI >= 0.6 and every type has >= 20 respondents.
2. Drivers of water stress and chemical dependence - for every answer option, a Mantel–Haenszel
   odds ratio stratified by survey region (Chouf vs Beqaa), with Robins–Breslow–Greenland 95%
   confidence intervals and Benjamini–Hochberg false-discovery control. A finding is published
   only if q < 0.10, the interval excludes 1 and every 2×2 cell has >= 5 respondents.
   A penalised logistic model is evaluated with cross-validation grouped by village; it is
   reported as predictive only if its out-of-fold AUC beats the region-only baseline by >= 0.05
   and the lower 95% bound is above 0.5.
3. Spatial context per village - satellite fire detections within 5 km and distance to the
   nearest protected area.

Nothing here is causal: associations describe respondents, who were not randomly sampled.
"""
from collections import Counter

import numpy as np
from pyproj import Transformer
from scipy.stats import chi2
from shapely.geometry import Point, shape
from shapely.ops import transform
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import adjusted_rand_score, roc_auc_score
from sklearn.model_selection import GroupKFold

from .dictionary import Code, Vocabulary, load

SEED = 20260929
MIN_PREVALENCE = 0.03
TYPOLOGY_FIELDS = ["water_sources", "energy_sources", "soil_enhancers", "chem_fertilizer_reliance",
                   "pesticide_reliance", "pest_control", "seed_sources", "production_level",
                   "land_size_band", "crop_groups", "coop_member", "raises_poultry"]
PREDICTORS = ["water_sources", "energy_sources", "land_size_band", "soil_types", "crop_groups",
              "production_level", "coop_member", "seed_sources", "raises_poultry"]
LOW_INPUT = {"soil_enhancers": {"compost", "manure", "biofertilizer"},
             "pest_control": {"biological", "physical", "local"}}
TYPE_LETTERS = "ABCDEF"


# ── helpers ────────────────────────────────────────────────────────────────

def _has(value, code):
    return code in value if isinstance(value, list) else value == code


def indicator_matrix(records, fields, min_prevalence=MIN_PREVALENCE):
    """Binary matrix (respondent × answer option). Unanswered = all zeros for that field."""
    d = load()
    cols = [(f, c) for f in fields for c in d.vocab_for(d.field(f)).code_names]
    X = np.array([[1.0 if r["status"][f] == "reported" and _has(r["values"][f], c) else 0.0
                   for f, c in cols] for r in records])
    prev = X.mean(axis=0) if len(X) else np.array([])
    keep = (prev >= min_prevalence) & (prev <= 1 - min_prevalence)
    return X[:, keep], [c for c, k in zip(cols, keep) if k]


def _labels(field, code):
    d = load()
    f = d.field(field)
    v = d.vocab_for(f)
    return {lang: f"{f.label[lang]}: {v.label(code, lang)}" for lang in ("en", "ar")}


def bh_qvalues(pvalues):
    p = np.asarray(pvalues, dtype=float)
    if not len(p):
        return p
    order = np.argsort(p)
    ranked = p[order] * len(p) / (np.arange(len(p)) + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty_like(q)
    out[order] = np.minimum(q, 1.0)
    return out


def mantel_haenszel(x, y, strata):
    """Stratified odds ratio for binary exposure x and outcome y.

    Returns (or, ci_low, ci_high, p) with the Robins–Breslow–Greenland variance and the
    continuity-corrected Mantel–Haenszel chi-square; None if the ratio is undefined.
    """
    sum_r = sum_s = sum_pr = sum_ps_qr = sum_qs = 0.0
    sum_a = sum_ea = sum_va = 0.0
    for s in np.unique(strata):
        m = strata == s
        a = float(np.sum((x[m] == 1) & (y[m] == 1)))
        b = float(np.sum((x[m] == 1) & (y[m] == 0)))
        c = float(np.sum((x[m] == 0) & (y[m] == 1)))
        dd = float(np.sum((x[m] == 0) & (y[m] == 0)))
        n = a + b + c + dd
        if n < 2:
            continue
        r, s_ = a * dd / n, b * c / n
        p_, q_ = (a + dd) / n, (b + c) / n
        sum_r += r; sum_s += s_
        sum_pr += p_ * r; sum_ps_qr += p_ * s_ + q_ * r; sum_qs += q_ * s_
        sum_a += a
        sum_ea += (a + b) * (a + c) / n
        sum_va += (a + b) * (c + dd) * (a + c) * (b + dd) / (n * n * (n - 1))
    if sum_r == 0 or sum_s == 0 or sum_va == 0:
        return None
    odds = sum_r / sum_s
    var = sum_pr / (2 * sum_r ** 2) + sum_ps_qr / (2 * sum_r * sum_s) + sum_qs / (2 * sum_s ** 2)
    se = np.sqrt(var)
    stat = (abs(sum_a - sum_ea) - 0.5) ** 2 / sum_va
    return odds, float(np.exp(np.log(odds) - 1.96 * se)), float(np.exp(np.log(odds) + 1.96 * se)), float(chi2.sf(stat, 1))


def _bootstrap_auc(y, p, rng, n=2000):
    stats = []
    for _ in range(n):
        idx = rng.integers(0, len(y), len(y))
        if len(np.unique(y[idx])) == 2:
            stats.append(roc_auc_score(y[idx], p[idx]))
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


# ── 1. typology ────────────────────────────────────────────────────────────

def typology(records):
    X, cols = indicator_matrix(records, TYPOLOGY_FIELDS)
    rng = np.random.default_rng(SEED)
    candidates = []
    for k in range(3, 7):
        labels = KMeans(k, n_init=50, random_state=SEED).fit_predict(X)
        aris = []
        for _ in range(100):
            idx = np.unique(rng.integers(0, len(X), len(X)))
            boot = KMeans(k, n_init=10, random_state=SEED).fit_predict(X[idx])
            aris.append(adjusted_rand_score(labels[idx], boot))
        candidates.append({"k": k, "stability_ari": round(float(np.mean(aris)), 3),
                           "stability_sd": round(float(np.std(aris)), 3),
                           "min_size": int(min(Counter(labels).values())), "labels": labels})
    best = max(candidates, key=lambda c: (c["stability_ari"], -c["k"]))
    published = best["stability_ari"] >= 0.6 and best["min_size"] >= 20
    # Name types A, B, C… by size so the lettering is stable across runs.
    order = [lab for lab, _ in Counter(best["labels"]).most_common()]
    letter = {lab: TYPE_LETTERS[i] for i, lab in enumerate(order)}
    assignments = {r["response_id"]: f"type_{letter[lab].lower()}" for r, lab in zip(records, best["labels"])}

    overall = X.mean(axis=0)
    profiles = []
    for lab in order:
        members = best["labels"] == lab
        prev = X[members].mean(axis=0)
        ranked = sorted(range(len(cols)), key=lambda j: prev[j] - overall[j], reverse=True)
        traits = [{"field": cols[j][0], "code": cols[j][1], "label": _labels(*cols[j]),
                   "share_in_type": round(float(prev[j]), 2), "share_overall": round(float(overall[j]), 2)}
                  for j in ranked if prev[j] >= 0.4 and prev[j] - overall[j] >= 0.15][:5]
        regions = Counter(r["instrument"] for r, m in zip(records, members) if m)
        profiles.append({"code": f"type_{letter[lab].lower()}", "letter": letter[lab], "size": int(members.sum()),
                         "regions": dict(regions), "traits": traits})
    return {
        "published": published,
        "method": "k-means on one-hot farming-practice answers; k chosen by bootstrap stability (100 resamples)",
        "fields": TYPOLOGY_FIELDS,
        "n": len(records),
        "k": best["k"],
        "candidates": [{k: v for k, v in c.items() if k != "labels"} for c in candidates],
        "stability_ari": best["stability_ari"],
        "profiles": profiles,
    }, assignments


def _short(field, code, lang):
    d = load()
    f = d.field(field)
    name = (f.short_label or f.label)[lang]
    return f"{name}: {d.vocab_for(f).label(code, lang).lower() if lang == 'en' else d.vocab_for(f).label(code, lang)}"


def typology_vocabulary(result):
    codes = []
    for p in result["profiles"]:
        label = {}
        for lang, word in (("en", "Type"), ("ar", "النمط")):
            traits = "; ".join(_short(t["field"], t["code"], lang) for t in p["traits"][:2]) or ("mixed" if lang == "en" else "متنوع")
            label[lang] = f"{word} {p['letter']} – {traits}"
        p["name"] = label
        codes.append(Code(code=p["code"], label=label, patterns=[]))
    return Vocabulary("farmer_type", "categorical", codes,
                      "Derived by clustering; see the Insights panel for each type's profile.")


# ── 2. drivers ─────────────────────────────────────────────────────────────

OUTCOMES = {
    "water_stress": {
        "label": {"en": "Water stress", "ar": "الإجهاد المائي"},
        "definition": {"en": "Water in the growing season is rarely or never enough",
                       "ar": "المياه نادراً ما تكون كافية أو غير كافية تماماً خلال موسم الزراعة"},
        "caveat": {"en": "Tanker delivery and storage tanks are often a response to scarcity, so they mark where water stress is felt rather than cause it.",
                   "ar": "غالباً ما يكون نقل المياه بالصهاريج والتخزين استجابةً للشح، فهي تدل على أماكن الإجهاد المائي ولا تسببه بالضرورة."},
    },
    "chemical_dependence": {
        "label": {"en": "High chemical dependence", "ar": "اعتماد مرتفع على الكيماويات"},
        "definition": {"en": "Total reliance on chemical fertilizers or on chemical pesticides",
                       "ar": "اعتماد كامل على الأسمدة الكيميائية أو على المبيدات الكيميائية"},
        "caveat": {"en": "Wells, diesel pumps and tropical fruit go together with more intensive irrigated farming; the association may reflect the type of farm rather than any single factor.",
                   "ar": "ترتبط الآبار ومضخات الديزل والفواكه الاستوائية بزراعة مروية أكثر كثافة؛ قد يعكس الارتباط نوع المزرعة لا عاملاً واحداً بعينه."},
    },
}


def _outcome(name, r):
    s, v = r["status"], r["values"]
    if name == "water_stress":
        if s["water_availability"] != "reported":
            return None
        return 1 if v["water_availability"] in ("rarely", "never") else 0
    rel = [v[f] for f in ("chem_fertilizer_reliance", "pesticide_reliance") if s[f] == "reported"]
    if not rel:
        return None
    return 1 if "total" in rel else 0


def drivers(records, groups_of):
    rng = np.random.default_rng(SEED)
    results = {}
    for name, meta in OUTCOMES.items():
        rows = [(r, _outcome(name, r)) for r in records]
        rows = [(r, y) for r, y in rows if y is not None]
        recs = [r for r, _ in rows]
        y = np.array([y for _, y in rows])
        strata = np.array([r["instrument"] for r in recs])
        X, cols = indicator_matrix(recs, PREDICTORS)
        tests = []
        for j, (field, code) in enumerate(cols):
            x = X[:, j]
            cells = [np.sum((x == 1) & (y == 1)), np.sum((x == 1) & (y == 0)), np.sum((x == 0) & (y == 1)), np.sum((x == 0) & (y == 0))]
            mh = mantel_haenszel(x, y, strata)
            if mh is None:
                continue
            tests.append({"field": field, "code": code, "label": _labels(field, code),
                          "n_with": int(x.sum()), "n_without": int(len(x) - x.sum()),
                          "rate_with": round(float(y[x == 1].mean()), 3), "rate_without": round(float(y[x == 0].mean()), 3),
                          "or": round(mh[0], 2), "ci": [round(mh[1], 2), round(mh[2], 2)], "p": mh[3],
                          "min_cell": int(min(cells))})
        for t, q in zip(tests, bh_qvalues([t["p"] for t in tests])):
            t["q"] = round(float(q), 4)
        findings = [t for t in tests if t["q"] < 0.10 and (t["ci"][0] > 1 or t["ci"][1] < 1) and t["min_cell"] >= 5]
        findings.sort(key=lambda t: t["q"])

        # Predictive check, cross-validated by village so a village is never in train and test.
        region = (strata == "beqaa_2026").astype(float)[:, None]
        groups = np.array([groups_of(r) for r in recs])
        folds = GroupKFold(n_splits=5)
        oof_full, oof_base = np.zeros(len(y)), np.zeros(len(y))
        full = np.hstack([X, region])
        for train, test in folds.split(full, y, groups):
            m = LogisticRegression(C=0.5, max_iter=2000).fit(full[train], y[train])
            oof_full[test] = m.predict_proba(full[test])[:, 1]
            b = LogisticRegression(max_iter=2000).fit(region[train], y[train])
            oof_base[test] = b.predict_proba(region[test])[:, 1]
        auc, auc_base = roc_auc_score(y, oof_full), roc_auc_score(y, oof_base)
        lo, hi = _bootstrap_auc(y, oof_full, rng)
        predictive = auc - auc_base >= 0.05 and lo > 0.5
        results[name] = {
            **meta, "n": int(len(y)), "prevalence": round(float(y.mean()), 3),
            "prevalence_by_region": {str(s): round(float(y[strata == s].mean()), 3) for s in np.unique(strata)},
            "tests_run": len(tests), "findings": findings,
            "model": {"auc": round(float(auc), 3), "auc_ci": [round(lo, 3), round(hi, 3)],
                      "baseline_auc": round(float(auc_base), 3), "predictive": bool(predictive),
                      "validation": "5-fold cross-validation grouped by village; baseline = region only"},
        }
    return results


# ── 3. spatial context ─────────────────────────────────────────────────────

def spatial_context(units, fire_features, protected_features):
    """units: {adm3_pcode: {'geometry':..., 'properties':{center_lon, center_lat}}}"""
    to_m = Transformer.from_crs("EPSG:4326", "EPSG:32636", always_xy=True).transform
    fires = [transform(to_m, Point(f["geometry"]["coordinates"])) for f in fire_features]
    parks = [transform(to_m, shape(f["geometry"])) for f in protected_features]
    out = {}
    for code, u in units.items():
        centre = transform(to_m, Point(u["properties"]["center_lon"], u["properties"]["center_lat"]))
        poly = transform(to_m, shape(u["geometry"]))
        out[code] = {
            "fire_detections_5km": sum(1 for p in fires if centre.distance(p) <= 5000),
            "protected_area_km": round(min(poly.distance(p) for p in parks) / 1000, 1),
        }
    return out


# ── orchestration ──────────────────────────────────────────────────────────

def derive(records):
    """Add derived per-respondent fields (farmer_type, low_input_practices) and run all analyses.

    Returns the analysis report (aggregates only) and registers the derived fields in the
    dictionary so that validation, disclosure control and the catalog treat them like others.
    """
    d = load()
    report, assignments = typology(records)
    d.vocabularies["farmer_type"].codes = typology_vocabulary(report).codes
    if not report["published"]:
        d.field("farmer_type").privacy = "research"  # unstable grouping: keep it out of public outputs
    for r in records:
        r["values"]["farmer_type"] = assignments[r["response_id"]]
        r["status"]["farmer_type"] = "reported"
        answered = [f for f in LOW_INPUT if r["status"][f] == "reported"]
        if answered:
            uses = any(set(r["values"][f] if isinstance(r["values"][f], list) else [r["values"][f]]) & codes
                       for f, codes in LOW_INPUT.items() if f in answered)
            r["values"]["low_input_practices"], r["status"]["low_input_practices"] = ("yes" if uses else "no"), "reported"
        else:
            r["values"]["low_input_practices"], r["status"]["low_input_practices"] = None, "not_provided"
        r["raw"]["farmer_type"] = r["raw"]["low_input_practices"] = None

    groups = lambda r: r["location"]["adm3_pcode"] or r["location"]["locality_id"] or r["location"]["adm2_pcode"] or "none"
    return {"typology": report, "drivers": drivers(records, groups)}

