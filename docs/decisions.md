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
| D14 | Default basemap Esri Light Gray; OSM and Esri imagery optional | the CARTO tiles used before now require an API key; a quiet basemap suits choropleths | CARTO (key), OSM as default (tile policy discourages heavy use) |

## Open items

- **Fire detections**: re-acquire from NASA FIRMS with sensor, confidence and FRP, then filter
  low-confidence detections; current file has no provenance.
- **Protected areas**: confirm WDPA version and whether serving the polygons as GeoJSON is
  acceptable under the WDPA terms (non-commercial, attribution, no downloadable redistribution
  without permission); otherwise request permission or switch to a tile service.
- **Basemap terms**: confirm Esri basemap usage terms for this site, or move to OpenFreeMap vector tiles.
- **Unresolved places**: Masma (ماسما) and Haret El-Fikani (حارة الفيكاني) need confirmation from the survey team.
- **Chouf interview dates**: not recorded in the source; ask the survey team.
- **Legal**: data owner to check notification duties for the earlier public exposure (e.g. Lebanese Law No. 81/2018).
