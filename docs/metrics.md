# Before / after metrics

"Before" was measured during the audit on commit `3f51024` (2026-03-16 release, still live on
2026-09-29). "After" is `python -m resolve metrics` plus the test suite on the refactored release.

| Area | Metric | Before | After |
|---|---|---|---|
| Privacy | Direct identifiers publicly downloadable | names + phones of 29 respondents, names of 204 rows, in 8+ files (HTTP 200) | 0 (files removed; history rewritten; tests block re-adding) |
| Privacy | Respondent-level features on the public map | 145 (29 Beqaa respondents × 5 themes) with village + age/gender-linked answers at fake-precise points | 207 pins by user decision: random ID + practice answers only, placed at their own village (201 at OSM settlement points, median 87 m spread) |
| Privacy | Public "aggregates" of fewer than 5 respondents | up to 29 of ~50 villages had ≤ 2 respondents | 0 (every summary ≥ k = 5; indicators need ≥ 5 answers) |
| Privacy | Identity fields in the public catalog | n/a (no catalog) | 0 |
| Location | Features declaring origin + precision | 0 % | 100 % |
| Location | Baked coordinate displacements | per-theme offsets of 0.5–1.5 km in 4 themes | 0 (cadastral polygons / official points) |
| Location | Villages resolved to official units | 0 (free text; hand-typed gazetteer with errors up to ~40 km) | 59 of 61 localities (2 flagged unverified/unresolved) |
| Data | Canonical field names with meaning | 0 % in legacy themes (`_3` … `_12`) | 100 % (46 dictionary fields, incl. 2 derived) |
| Data | Categorical fields with a controlled vocabulary | ~0 | 36 of 46 fields (the other 10 are free text/date, never published) |
| Data | Missing-value semantics | null / blank / dropped | 5 explicit statuses on every field of every record |
| Data | Datasets with source + licence recorded | 0 of 5 | 4 of 4 published datasets |
| Reproducibility | Published outputs rebuildable from active code | 1 of ~5 families | all; two builds are byte-identical; raw inputs hash-verified |
| Architecture | Dataset-specific literals in frontend code | ~27 explicit branches + ~15 theme-keyed maps | 0 |
| Architecture | Files edited to add a survey wave or answer option | 4 files, ~15 places incl. JS | YAML (dictionary, aliases) only; no frontend change |
| Testing | Automated tests | 0 | 46 test functions (≈ 90 cases) in CI + a browser end-to-end test |
| Performance | Data loaded by the browser | ≈ 1.6 MB (+ 2.4 MB shipped unused) | 1.28 MB raw, ≈ 0.2 MB gzipped as served; nothing unused shipped |
| UX | Popup field set identical in Arabic and English | no (e.g. 8 vs 1 fields) | yes (generated from one dictionary) |
| UX | Layers with legend and source/licence card | 4 legends (one mislabelled), no cards | all layers |
| Honesty | Layers whose claims contradict their own metrics | 2+ AI layers ("~98 % accuracy" vs CV F1 0.0) | 0 |
| Analysis | Validated analytical outputs | 0 (in-sample metrics only) | 4 farmer types (bootstrap ARI 0.70); water stress: 3 findings, grouped-CV AUC 0.67 (0.60–0.75) vs 0.49 baseline; chemical dependence: 3 findings, AUC 0.61 (0.52–0.69) - reported as weak |
