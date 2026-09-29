# Architecture

## Data flow

```
<private store>/raw/<source>/<version>/          immutable inputs (checksummed in manifest.sha256)
   │  resolve/survey.py      survey adapters: dictionary-driven column mapping, vocabulary coding,
   │                         value statuses, skip logic, locality resolution, respondent IDs
   │  resolve/reference.py   fire detections, protected areas, admin boundaries
   ▼
<private store>/staging/     survey_responses.json, survey_identity.json, review_issues.json
   │  resolve/validate.py    critical invariants -> build stops; review items -> report
   ▼
<private store>/canonical/   validated standardized records + identity table
   │  resolve/analysis.py    typology, driver analysis, spatial context -> derived fields + insights
   │  resolve/sdc.py         disclosure control (k, district pooling, small-cell suppression)
   │  resolve/publish.py     releases + catalog.json
   ├──────────────► public/data/              public release (committed, deployed)
   └──────────────► <private store>/build/research/data/   research release (local only)
                          │
                   public/js (MapLibre)       one generic app reads catalog.json for either tier
```

## Canonical survey record

```json
{
  "response_id": "CH-0EXAMP:chouf_2026",
  "respondent_id": "CH-0EXAMP",
  "instrument": "chouf_2026",
  "source": {"file": "raw/chouf_survey/2026-02-27/...xlsx", "sheet": "WiTHOUT DUPLICATES FS (2)", "row": 14},
  "location": {"village_reported": "Mresti", "locality_id": "adm3:23659", "resolution": "cadastral_name_match",
               "confidence": "high", "adm3_pcode": "23659", "adm2_pcode": "LB33", "adm1_pcode": "LB3",
               "lon": 35.64, "lat": 33.62, "geom_origin": "cadastral_unit_centre",
               "spatial_precision": "cadastral_unit", "uncertainty_m": 1600, "point_source": "COD-AB cadastral unit centre"},
  "holding": null,
  "values": {"water_availability": "sometimes", "water_sources": ["well", "tanker"], "gender": null, "...": "..."},
  "status": {"water_availability": "reported", "gender": "not_asked", "poultry_purpose": "not_applicable", "...": "..."},
  "raw":    {"water_availability": "Sometimes enough", "...": "..."}
}
```

- **Values** are codes from `dictionary/vocabularies.yaml`; free text stays text and is never published.
- **Status** is explicit for every field: `reported`, `not_provided`, `not_asked` (question not in
  that instrument), `not_applicable` (skip logic), `invalid` (unreadable/ambiguous; logged for review).
- **Raw** keeps the original answer so every normalization is auditable.
- **Location** never pretends to be a farm location: survey villages resolve to official cadastral
  units (OCHA COD-AB admin 3) and carry origin, precision and uncertainty. A respondent's own GPS
  point, when written in the land-location answer, becomes a separate `holding` (research only).
- **Identity** (names, phone) is split into a separate table keyed by `respondent_id`.

## Public products

| Layer | Entity | Geometry | Rule |
|---|---|---|---|
| Survey – village summaries | `village_survey_summary` | cadastral polygon | ≥ k respondents in the cadastral unit |
| Survey – district summaries | `district_survey_summary` | district polygon | sensitive indicators for all district respondents (≥ k); other indicators for respondents *outside* published villages (≥ k) |
| Survey respondents (pins) | `survey_respondent_public` | point at the cadastral centre (≥ k respondents) or district centre | random ID + farming-practice answers only; spread around the anchor at display time |
| Protected areas | `protected_area` | WDPA polygons, simplified | attribution; licence terms in the dataset card |
| Fire detections | `fire_detection` | satellite pixel centre | caveats in the dataset card |

Each indicator distribution is published only if at least k respondents answered it; for
sensitive indicators counts of 1–2 are hidden (plus a complementary cell for single-choice).

## Analysis (resolve/analysis.py)

- **Farmer typology**: k-means on the one-hot matrix of 12 practice fields; k in 3–6 chosen by
  mean adjusted Rand index over 100 bootstrap resamples; published only if ARI ≥ 0.6 and each type
  has ≥ 20 respondents. Types are lettered by size and named from their two most distinctive answers.
- **Drivers** of water stress (water rarely/never enough) and high chemical dependence (total
  reliance on fertilizers or pesticides): Mantel–Haenszel odds ratio per answer option, stratified by
  region, Robins–Breslow–Greenland 95% CI, Benjamini–Hochberg q; published if q < 0.10, the CI
  excludes 1 and every 2×2 cell ≥ 5. A ridge logistic model is scored with 5-fold cross-validation
  grouped by village against a region-only baseline.
- **Spatial context** per cadastral unit: FIRMS detections within 5 km and distance to the nearest
  protected area (EPSG:32636).
- Results go to `catalog.json → insights` (aggregates only) and `<private>/build/analysis_report.json`.

## Frontend

`public/js` is a registry-driven MapLibre app with no dataset-specific code: `catalog.json`
lists layers with a `renderer` (`survey_summary`, `polygons`, `points`, `respondents`), their
fields, vocabularies, colours, filters and dataset cards. Popups, legends, filters, the
indicator selector and the accessible feature lists are all generated from it. All data is
inserted as text (no `innerHTML`). Arabic/English switching flips the page direction.

## Why no database

The whole private store is a few MB and there are no server-side queries: a deterministic file
pipeline with JSON outputs and static hosting is simpler, cheaper and easier to audit. PMTiles
remains the option if a reference layer grows beyond ~5–10 MB.
