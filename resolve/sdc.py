"""Statistical disclosure control for public survey summaries.

Rules (respondent consent covers research use only; see the plan, decision A2):
  1. Village (cadastral unit) summaries are published only if at least k respondents live there.
  2. Respondents in villages below k are pooled per district into a "remainder" summary, which
     is itself published only if it has at least k respondents. The remainder excludes published
     villages, so district totals cannot be differenced against villages to recover small ones.
  3. Sensitive indicators (privacy class public_district) are published only per whole district.
  4. An indicator's distribution is published only if at least k respondents answered it.
  5. For sensitive indicators, category counts of 1 or 2 are suppressed; for single-choice
     indicators a second (complementary) cell is suppressed so the first cannot be derived.
Research-only and identity fields never enter any summary.
"""
from collections import Counter, defaultdict

from .dictionary import load

SMALL_CELL = 3


def _summarize(records, fld, vocab, k, sensitive):
    statuses = Counter(r["status"][fld.code] for r in records)
    answered = [r["values"][fld.code] for r in records if r["status"][fld.code] == "reported"]
    summary = {
        "n_answered": len(answered),
        "status_counts": {s: n for s, n in sorted(statuses.items()) if s != "reported"},
        "counts": None,
        "suppressed": None,
        "mode": None,
    }
    if len(answered) < k:
        summary["suppressed"] = "fewer_than_k_answers"
        return summary
    counts = Counter()
    for value in answered:
        counts.update(value if isinstance(value, list) else [value])
    ordered = {c: counts.get(c, 0) for c in vocab.code_names}
    mode = max(vocab.code_names, key=lambda c: (ordered[c], -vocab.code_names.index(c)))
    summary["mode"] = mode if ordered[mode] > 0 else None
    if sensitive:
        hidden = [c for c, n in ordered.items() if 0 < n < SMALL_CELL]
        if len(hidden) == 1 and fld.type != "multi":
            others = sorted((n, vocab.code_names.index(c), c) for c, n in ordered.items() if n >= SMALL_CELL)
            if others:
                hidden.append(others[0][2])
        if hidden:
            ordered = {c: (None if c in hidden else n) for c, n in ordered.items()}
            summary["suppressed"] = "small_cells"
            if summary["mode"] in hidden:
                summary["mode"] = None
    summary["counts"] = ordered
    return summary


def _group_summary(records, fields, d, k, sensitive):
    return {f.code: _summarize(records, f, d.vocab_for(f), k, sensitive) for f in fields}


def summarize(records, k):
    """Returns (villages, districts, log). Each summary: unit ids, n_respondents, indicators."""
    d = load()
    village_fields = [f for f in d.fields if f.privacy == "public_village"]
    district_fields = [f for f in d.fields if f.privacy == "public_district"]

    usable = [r for r in records if r["location"]["adm2_pcode"]]
    excluded = [r["response_id"] for r in records if not r["location"]["adm2_pcode"]]
    by_village, by_district = defaultdict(list), defaultdict(list)
    for r in usable:
        by_district[r["location"]["adm2_pcode"]].append(r)
        if r["location"]["adm3_pcode"]:
            by_village[r["location"]["adm3_pcode"]].append(r)

    villages, published = [], set()
    for adm3, group in sorted(by_village.items()):
        if len(group) >= k:
            published.add(adm3)
            villages.append({
                "adm3_pcode": adm3, "adm2_pcode": group[0]["location"]["adm2_pcode"],
                "n_respondents": len(group),
                "instruments": sorted({r["instrument"] for r in group}),
                "indicators": _group_summary(group, village_fields, d, k, sensitive=False),
            })

    districts, log = [], {"k": k, "excluded_no_location": excluded, "suppressed_villages": {}, "suppressed_districts": []}
    for adm2, group in sorted(by_district.items()):
        remainder = [r for r in group if r["location"]["adm3_pcode"] not in published]
        small = Counter(r["location"]["adm3_pcode"] or r["location"]["locality_id"] or "unassigned"
                        for r in remainder)
        log["suppressed_villages"][adm2] = dict(sorted(small.items()))
        summary = {
            "adm2_pcode": adm2,
            "n_respondents": len(group),
            "n_remainder": len(remainder),
            "remainder_villages": len(small),
            "instruments": sorted({r["instrument"] for r in group}),
            "indicators": {},
            "remainder_indicators": {},
        }
        if len(group) >= k:
            summary["indicators"] = _group_summary(group, district_fields, d, k, sensitive=True)
        if len(remainder) >= k:
            summary["remainder_indicators"] = _group_summary(remainder, village_fields, d, k, sensitive=False)
        if len(group) >= k:
            districts.append(summary)
        else:
            log["suppressed_districts"].append({"adm2_pcode": adm2, "n": len(group)})
    return villages, districts, log
