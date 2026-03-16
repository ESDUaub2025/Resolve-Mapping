"""Audit current data state for the project."""
import pandas as pd
import json
import os
import sys
import io
from pathlib import Path

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

# 1. Check the new Excel file
print("=== NEW EXCEL FILE ===")
xl_path = ROOT / "data" / "Farmers survey 27-2-2026.xlsx"
if xl_path.exists():
    xl = pd.ExcelFile(str(xl_path))
    for s in xl.sheet_names:
        df = pd.read_excel(str(xl_path), sheet_name=s)
        print(f"  Sheet: {s} -> {len(df)} rows x {len(df.columns)} cols")
    # Use largest sheet
    primary = max(xl.sheet_names, key=lambda s: len(pd.read_excel(str(xl_path), sheet_name=s)))
    df_xl = pd.read_excel(str(xl_path), sheet_name=primary)
    print(f"  Primary sheet: {primary}")
    # List column names
    print(f"  Columns ({len(df_xl.columns)}):")
    for c in df_xl.columns:
        print(f"    - {c}")
else:
    print("  NOT FOUND")

# 2. Check existing master CSV
print("\n=== MASTER CSV (with coords) ===")
master_path = ROOT / "data" / "MZSurvey farmers ENGLISH_with_coords.csv"
if master_path.exists():
    df_master = pd.read_csv(str(master_path), encoding='utf-8')
    print(f"  Rows: {len(df_master)}, Cols: {len(df_master.columns)}")
    has_x = df_master['X'].notna().sum() if 'X' in df_master.columns else 0
    has_y = df_master['Y'].notna().sum() if 'Y' in df_master.columns else 0
    print(f"  Rows with coordinates: X={has_x}, Y={has_y}")
    # Village column
    for vcol in df_master.columns:
        if 'القرية' in str(vcol) or 'Village' in str(vcol):
            villages = df_master[vcol].dropna().unique()
            print(f"  Village column '{vcol}': {len(villages)} unique")
            for v in sorted(str(x) for x in villages):
                print(f"    - {v}")
            break
else:
    print("  NOT FOUND")

# 3. Check canonical files
print("\n=== CANONICAL GEOJSON FILES ===")
canon_dir = ROOT / "data" / "geojson" / "canonical"
for f in sorted(canon_dir.glob("*.geojson")):
    with open(f, 'r', encoding='utf-8') as fh:
        gj = json.load(fh)
    features = gj.get('features', [])
    count = len(features)
    # Check if EN values exist and are not just Arabic copies
    en_sample = ""
    ar_sample = ""
    if count > 0:
        vals = features[0].get('properties', {}).get('values', {})
        ar_keys = list(vals.get('ar', {}).keys())[:3]
        en_keys = list(vals.get('en', {}).keys())[:3]
        ar_sample = str(ar_keys)
        en_sample = str(en_keys)
    print(f"  {f.name}: {count} features | AR keys: {ar_sample} | EN keys: {en_sample}")

# 4. Check source CSV layer files
print("\n=== ARABIC LAYER CSVs ===")
ar_dir = ROOT / "data" / "layers" / "Arabic"
for f in sorted(ar_dir.glob("*.csv")):
    try:
        df = pd.read_csv(str(f), encoding='utf-8-sig')
        print(f"  {f.name}: {len(df)} rows x {len(df.columns)} cols")
    except Exception as e:
        print(f"  {f.name}: ERROR - {e}")

print("\n=== ENGLISH LAYER CSVs ===")
en_dir = ROOT / "data" / "layers" / "English"
for f in sorted(en_dir.glob("*.csv")):
    if '.pre_transliterate' in f.name:
        continue
    try:
        df = pd.read_csv(str(f), encoding='utf-8-sig')
        print(f"  {f.name}: {len(df)} rows x {len(df.columns)} cols")
    except Exception as e:
        print(f"  {f.name}: ERROR - {e}")

# 5. Check verified village coordinates
print("\n=== VERIFIED VILLAGE COORDINATES ===")
coord_file = ROOT / "data" / "verified_village_coordinates.json"
if coord_file.exists():
    with open(coord_file, 'r', encoding='utf-8') as fh:
        coord_data = json.load(fh)
    villages = coord_data.get('villages', {})
    print(f"  {len(villages)} villages with coordinates:")
    for name, info in sorted(villages.items()):
        en_name = info.get('name_en', '???')
        lat = info.get('lat', '?')
        lon = info.get('lon', '?')
        print(f"    {name} -> {en_name} ({lat}, {lon})")
else:
    print("  NOT FOUND")

# 6. Check Model_Predictions.geojson
print("\n=== MODEL PREDICTIONS ===")
pred_path = ROOT / "data" / "geojson" / "Model_Predictions.geojson"
if pred_path.exists():
    with open(pred_path, 'r', encoding='utf-8') as fh:
        gj = json.load(fh)
    features = gj.get('features', [])
    print(f"  {len(features)} prediction features")
    if features:
        props = features[0].get('properties', {})
        print(f"  Sample properties: {list(props.keys())}")
else:
    print("  NOT FOUND")

# 7. Check survey_by_theme
print("\n=== SURVEY BY THEME ===")
theme_dir = ROOT / "data" / "survey_by_theme"
if theme_dir.exists():
    for f in sorted(theme_dir.glob("*.csv")):
        df = pd.read_csv(str(f), encoding='utf-8')
        print(f"  {f.name}: {len(df)} rows")
