# scripts/__archive__/

One-time and superseded scripts moved here during the June 2025 cleanup.
These files are **safe to delete** once you're satisfied everything works.

None of these scripts are called by the map app or any active pipeline step.

## Origin

All files were previously in `scripts/` and served these historical purposes:

| File | Purpose |
|------|---------|
| `add_coordinates_to_survey.py` | One-off: added X/Y coords to 30-row original survey |
| `audit_village_transliterations.py` | One-off audit of phonetic transliteration quality |
| `audit_villages.py` | One-off village name audit vs GeoJSON |
| `check_property_schemas.py` | Debug tool: compared PropertySchemas vs actual GeoJSON keys |
| `check_village_coords.py` | One-off: verified village coordinate lookup file |
| `combine_original_data.py` | One-off: merged multiple early CSV exports |
| `count_features.py` | Debug tool: printed feature counts across GeoJSON files |
| `csv_to_geojson_immutable.py` | Superseded by `generate_canonical_geojson.py` |
| `csvs_to_geojson_complete.py` | Legacy dual-file (Arabic + English) GeoJSON generator |
| `find_missing_schemas.py` | Debug tool: found properties with no PropertySchemas entry |
| `fix_theme_coordinates.py` | One-off coordinate patch for theme GeoJSONs |
| `fix_village_names.py` | One-off village name normalisation patch |
| `generate_canonical_new_data.py` | Superseded by `integrate_new_survey_27_2_2026.py` |
| `inspect_new_survey.py` | One-off: inspected new Excel structure |
| `inspect_to_json.py` | One-off: dumped Excel schema to JSON |
| `integrate_survey_data.py` | Superseded by `integrate_new_survey_27_2_2026.py` |
| `list_csv_columns.py` | Debug tool |
| `map_actual_geojson_keys.py` | Debug tool |
| `map_column_translations.py` | One-off: mapped Arabic column headers to English |
| `map_survey_columns.py` | One-off: mapped survey question numbers to column names |
| `regenerate_comprehensive_canonical.py` | Superseded by `integrate_new_survey_27_2_2026.py` step 7 |
| `research_village_coordinates.py` | One-off: looked up GPS coords for new villages |
| `survey_inspect.ipynb` | Broken Jupyter notebook (QGIS kernel conflict) |
| `test_column_names.py` | One-off test |
| `test_write.py` | One-off test |
| `translate_csv_gold_standard.py` | One-off: AR→EN translation pass on CSV data |
| `validate_bilingual_translation.py` | One-off validation of AR/EN data alignment |
| `validate_survey_data.py` | One-off validation of survey completeness |
| `verify_transliterations.py` | One-off: verified village name transliterations |
