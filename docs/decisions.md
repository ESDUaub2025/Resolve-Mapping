# Decisions

Short records of decisions taken in the 2026-09-29 refactor (full reasoning in the audit plan).

| # | Decision | Why | Alternatives rejected |
|---|---|---|---|
| D1 | Survey data only in a private store outside the repo; Pages deploys only `public/` | raw files with names/phones were publicly served; consent is research-only | ignore rules in the same repo (one `git add -A` re-publishes); private repo + auth (static-only constraint) |
| D2 | Public survey layer = disclosure-controlled summaries, k = 5 | research-only consent excludes any individual record | jittered points, k-anonymised microdata |
| D3 | Sensitive indicators (income, age, gender, cost shares) at district level only, with small-cell suppression | attribute disclosure risk in small villages | village-level with cell suppression only |
| D4 | District "remainder" excludes published villages | prevents recovering small villages by subtracting villages from district totals | full district totals |
| D5 | Official cadastral units (OCHA COD-AB admin 3) as the locality spine | stable P-codes, bilingual names, polygons that honestly show "an area", not a farm | geocoding each village string; the legacy hand-typed gazetteer (had points ~40 km off and outside Lebanon) |
| D6 | Explicit value statuses per field (`not_asked`, `not_applicable`, …) | missing answers had been dropped or shown as blanks; instruments differ | nulls; sentinel strings |
| D7 | Random stable respondent IDs from a private registry | replaces names everywhere; stable across row re-ordering | row-number or coordinate-hash IDs (unstable, three schemes before) |
| D8 | One dictionary (YAML) drives adapters, validation, docs and the public catalog | semantics had drifted across 5+ hand-kept maps | keeping `property-schemas.js` + `config.py` in sync |
| D9 | JSON (not Parquet) for staging/canonical files | < 1 MB, no extra dependency, human-auditable diffs | Parquet/GeoParquet (revisit if data grows) |
| D10 | De-duplicated Chouf sheet is the source of truth; individual crop answers joined from the full sheet by respondent name | user decision; only the full sheet has individual crops | legacy `_1.0` CSVs (undocumented village aggregates with per-theme coordinate offsets) |
| D11 | Contradictory multi-answers (e.g. all impacts + "no significant impact") keep the substantive answers and log a review item | not silently repaired: raw answer kept, issue reported | treating the whole answer as invalid |
| D12 | ML/AI layers withdrawn from the public map; code kept in `research/` | in-sample metrics, leakage, inverted colours | relabelling as experimental |
| D13 | Neutral viridis ramp for ordinal scales, Okabe–Ito for categories | colour-blind safe; avoids implying good/bad for neutral scales like farm size | red–green ramps |
| D15 | Public pins, one per respondent, identified only by the random ID (user decision) | the map should show each respondent while keeping personal data local | pins in the local view only; pins with all answers |
| D16 | Pin safeguards: farming-practice answers only; anchor = cadastral centre if ≥ k respondents, else district centre; no pin in districts below k; positions spread only at display time | a pin is still an individual record: small villages, sensitive answers and exact positions would allow re-identification | village anchor for everyone; baked jitter in the data |
| D17 | Farmer typology by k-means on one-hot practice answers; k by bootstrap stability; publish only if ARI ≥ 0.6 and every type ≥ 20 | only k-means gave acceptable stability (ARI 0.70 at k = 4); Ward and Jaccard-average linkage were unstable or produced singletons | hierarchical clustering; picking k by silhouette alone (≈ 0.1 for every method) |
| D18 | Drivers: Mantel–Haenszel odds ratios stratified by region, Benjamini–Hochberg q < 0.10, all cells ≥ 5; predictive check with village-grouped CV vs a region-only baseline | ~200 respondents from two different surveys: region confounds almost everything, and villages must not leak between train and test | random forests (the withdrawn models overfit: CV F1 0.0); unadjusted chi-square tests |
| D19 | Crop groups coded from free text with an AI-assisted vocabulary (13 groups); the text itself stays research-only | crops were unusable free text; coded groups make crops filterable and analysable | publishing the free text; ignoring crops |
| D20 | Spatial context per village: fire detections within 5 km, distance to the nearest protected area | cheap, reproducible context from layers already in the release | climate rasters (new data sources, licences) - possible later |
| D14 | Default basemap Esri Light Gray; OSM and Esri imagery optional | the CARTO tiles used before now require an API key; a quiet basemap suits choropleths | CARTO (key), OSM as default (tile policy discourages heavy use) |

## Open items

- **Fire detections**: evidence points to NASA FIRMS VIIRS NOAA-20 (an earlier export is named
  `fire_archive_J1V-C2_647822.csv`). Re-download from FIRMS with confidence and FRP and filter
  low-confidence detections.
- **Protected areas**: confirm WDPA version and whether serving the polygons as GeoJSON is
  acceptable under the WDPA terms (non-commercial, attribution, no downloadable redistribution
  without permission); otherwise request permission or switch to a tile service.
- **Basemap terms**: confirm Esri basemap usage terms for this site, or move to OpenFreeMap vector tiles.
- **Unresolved places**: Masma (ماسما) and Haret El-Fikani (حارة الفيكاني) need confirmation from the survey team.
- **Chouf interview dates**: not recorded in the source; ask the survey team.
- **Older local copies**: `D:\Programing\ResolveMaping_final` contains respondent names and
  coordinates (`data/CLEANED_Farmers*.csv`); decide whether to delete it or move it into the private store.
- **Legal**: data owner to check notification duties for the earlier public exposure (e.g. Lebanese Law No. 81/2018).
