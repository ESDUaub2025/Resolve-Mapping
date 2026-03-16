"""Move all obsolete scripts into scripts/__archive__/"""
import shutil
from pathlib import Path

ROOT    = Path(__file__).resolve().parent  # project root (file is at root level)
SCRIPTS = ROOT / "scripts"
ARCHIVE = SCRIPTS / "__archive__"
ARCHIVE.mkdir(exist_ok=True)

TO_MOVE = [
    "add_coordinates_to_survey.py",
    "audit_villages.py",
    "audit_village_transliterations.py",
    "check_property_schemas.py",
    "check_village_coords.py",
    "combine_original_data.py",
    "count_features.py",
    "csvs_to_geojson_complete.py",
    "csv_to_geojson_immutable.py",
    "find_missing_schemas.py",
    "fix_theme_coordinates.py",
    "fix_village_names.py",
    "fix_new_canonical.py",
    "generate_canonical_new_data.py",
    "inspect_new_survey.py",
    "inspect_to_json.py",
    "integrate_survey_data.py",
    "list_csv_columns.py",
    "map_actual_geojson_keys.py",
    "map_column_translations.py",
    "map_survey_columns.py",
    "regenerate_comprehensive_canonical.py",
    "research_village_coordinates.py",
    "survey_inspect.ipynb",
    "test_column_names.py",
    "test_write.py",
    "translate_csv_gold_standard.py",
    "validate_bilingual_translation.py",
    "validate_survey_data.py",
    "verify_transliterations.py",
]

moved, skipped = [], []
for fname in TO_MOVE:
    src = SCRIPTS / fname
    if src.exists():
        shutil.move(str(src), str(ARCHIVE / fname))
        moved.append(fname)
    else:
        skipped.append(fname)

print(f"Moved   ({len(moved)}): " + ", ".join(moved))
print(f"Skipped ({len(skipped)}): " + ", ".join(skipped))
print("Archive complete.")
