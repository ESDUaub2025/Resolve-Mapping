# scripts/

Active data-processing scripts for the ResolveMaping project.

## Active scripts

| Script | Purpose | When to run |
|--------|---------|-------------|
| **`integrate_new_survey_27_2_2026.py`** | **Primary integration script** — ingests a new survey Excel and rebuilds all downstream data products (master CSVs, theme CSVs, Arabic layer CSVs, canonical GeoJSON, Excel workbook, optional ML features) | Every time a new survey batch arrives |
| `generate_canonical_geojson.py` | Regenerates the original 1.0 canonical GeoJSON from legacy Arabic/English CSV pairs | Only if original 1.0 data changes |
| `transliterate_village_names.py` | Generates phonetic Arabic→English transliterations for new village names | Only when adding new villages |

## ml_pipeline/

Full ML pipeline: feature engineering → model training → spatial interpolation → boundary generation.

```
# Run all 4 stages
.venv/Scripts/python.exe scripts/ml_pipeline/run_pipeline.py

# Or run stages individually
.venv/Scripts/python.exe scripts/ml_pipeline/feature_engineering.py
.venv/Scripts/python.exe scripts/ml_pipeline/train_models.py
.venv/Scripts/python.exe scripts/ml_pipeline/interpolate_grid.py
.venv/Scripts/python.exe scripts/ml_pipeline/generate_boundary.py
```

## Quick start — integrate new survey data

```powershell
# From project root
.venv/Scripts/python.exe scripts/integrate_new_survey_27_2_2026.py
```

The script:
1. Detects truly new rows vs rows already in the master CSV
2. Assigns GPS coordinates from `data/verified_village_coordinates.json`
3. Merges with existing data (preserving coordinates of all previous rows)
4. Rebuilds `data/survey_by_theme/` CSVs
5. Rebuilds `data/layers/Arabic/*_new.csv` layer files
6. Regenerates `data/geojson/canonical/*_new.canonical.geojson`
7. Refreshes `data/Original_Survey_Data_Complete.xlsx`
8. Optionally re-runs ML feature engineering
9. Writes an audit JSON to `data/integration_audit_<timestamp>.json`

All modified files are automatically backed up with a timestamp suffix before overwriting.

## Archive

Obsolete one-off and superseded scripts live in `__archive__/`.
See [`__archive__/README.md`](__archive__/README.md) for details.

## Adding a new village

If a respondent comes from a village not in `data/verified_village_coordinates.json`:

1. Research the GPS coordinates (Google Maps, QGIS, or field GPS)
2. Add an entry to `data/verified_village_coordinates.json`:
   ```json
   "اسم القرية": { "lon": 35.XXXX, "lat": 33.XXXX, "name_en": "VillageName" }
   ```
3. Re-run `integrate_new_survey_27_2_2026.py`
