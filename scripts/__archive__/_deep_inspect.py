# -*- coding: utf-8 -*-
"""Deep inspection of ALL data sources to understand relationships."""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd

EXCEL = 'data/Farmers survey 27-2-2026.xlsx'

# 1. All sheet names
xl = pd.ExcelFile(EXCEL)
print(f'=== All sheets in Excel: {xl.sheet_names}')

# 2. WITHOUT DUPLICATES sheet (179 rows - the clean dataset)
df = pd.read_excel(EXCEL, sheet_name='WiTHOUT DUPLICATES FS (2)')
print(f'\n=== WITHOUT DUPLICATES: {len(df)} rows x {len(df.columns)} cols ===')
print(f'Villages ({df["Village"].nunique()} unique): {sorted(df["Village"].dropna().unique().tolist())}')

# Check for coordinate columns
all_cols = list(df.columns)
print(f'\nAll columns: {all_cols}')

# 3. Check original Arabic CSVs
print(f'\n=== Original Arabic Layer CSVs ===')
ar_dir = 'data/layers/Arabic'
for f in sorted(os.listdir(ar_dir)):
    if f.endswith('.csv'):
        try:
            d = pd.read_csv(os.path.join(ar_dir, f), encoding='utf-8')
            village_col = None
            for c in d.columns:
                if 'قرية' in str(c) or 'Village' in str(c).lower():
                    village_col = c
                    break
            villages = sorted(d[village_col].dropna().unique().tolist()) if village_col else []
            print(f'  {f}: {len(d)} rows, {len(d.columns)} cols, village_col={repr(village_col)}, villages={len(villages)}')
        except Exception as e:
            print(f'  {f}: ERROR - {e}')

# 4. Check original English CSVs  
print(f'\n=== Original English Layer CSVs ===')
en_dir = 'data/layers/English'
for f in sorted(os.listdir(en_dir)):
    if f.endswith('.csv'):
        try:
            d = pd.read_csv(os.path.join(en_dir, f), encoding='utf-8')
            village_col = None
            for c in d.columns:
                if 'قرية' in str(c) or 'Village' in str(c).lower():
                    village_col = c
                    break
            villages = sorted(d[village_col].dropna().unique().tolist()) if village_col else []
            print(f'  {f}: {len(d)} rows, {len(d.columns)} cols, village_col={repr(village_col)}, villages={len(villages)}')
            if villages:
                print(f'    Villages: {villages[:10]}...' if len(villages) > 10 else f'    Villages: {villages}')
        except Exception as e:
            print(f'  {f}: ERROR - {e}')

# 5. Check survey_by_theme CSVs
print(f'\n=== Survey by Theme CSVs ===')
st_dir = 'data/survey_by_theme'
if os.path.exists(st_dir):
    for f in sorted(os.listdir(st_dir)):
        if f.endswith('.csv'):
            try:
                d = pd.read_csv(os.path.join(st_dir, f), encoding='utf-8')
                print(f'  {f}: {len(d)} rows, {len(d.columns)} cols')
                print(f'    Columns: {list(d.columns)}')
            except Exception as e:
                print(f'  {f}: ERROR - {e}')

# 6. Check existing canonical GeoJSON feature counts and villages
print(f'\n=== Canonical GeoJSON Files ===')
canon_dir = 'data/geojson/canonical'
for f in sorted(os.listdir(canon_dir)):
    if f.endswith('.geojson'):
        with open(os.path.join(canon_dir, f), 'r', encoding='utf-8') as fh:
            gj = json.load(fh)
        feats = gj.get('features', [])
        if feats:
            # Check structure
            props = feats[0].get('properties', {})
            has_values = 'values' in props
            if has_values:
                vals = props['values']
                en_keys = list(vals.get('en', {}).keys())[:5]
                ar_keys = list(vals.get('ar', {}).keys())[:5]
                # Check if en values are actually Arabic
                en_sample = list(vals.get('en', {}).values())[:3]
                print(f'  {f}: {len(feats)} features, EN keys sample: {en_keys}, EN values sample: {en_sample}')
            else:
                print(f'  {f}: {len(feats)} features, NO values structure, keys: {list(props.keys())[:8]}')

# 7. Check master CSV
print(f'\n=== Master CSV ===')
master = 'data/MZSurvey farmers ENGLISH_with_coords.csv'
if os.path.exists(master):
    d = pd.read_csv(master, encoding='utf-8')
    print(f'  Rows: {len(d)}, Cols: {len(d.columns)}')
    village_col = None
    for c in d.columns:
        if 'village' in c.lower():
            village_col = c
            break
    if village_col:
        print(f'  Village col: {repr(village_col)}, Villages: {sorted(d[village_col].dropna().unique().tolist())}')

# 8. Check verified village coordinates
print(f'\n=== Verified Village Coordinates ===')
vc_file = 'data/verified_village_coordinates.json'
if os.path.exists(vc_file):
    with open(vc_file, 'r', encoding='utf-8') as fh:
        vc = json.load(fh)
    print(f'  {len(vc)} villages: {sorted(vc.keys())}')

# 9. Original CSV content check - see which villages are in original data
print(f'\n=== Village overlap analysis ===')
excel_villages = set(df['Village'].dropna().str.strip().str.lower().unique())
print(f'  Excel (dedup): {len(excel_villages)} villages')

# Load an original English CSV
en_water = os.path.join(en_dir, [f for f in os.listdir(en_dir) if 'Water' in f and '_new' not in f][0])
d_water = pd.read_csv(en_water, encoding='utf-8')
water_village_col = None
for c in d_water.columns:
    if 'قرية' in str(c) or 'village' in c.lower():
        water_village_col = c
        break
if water_village_col:
    orig_villages = set(d_water[water_village_col].dropna().str.strip().str.lower().unique())
    print(f'  Original Water EN CSV: {len(orig_villages)} villages')
    overlap = excel_villages & orig_villages
    only_excel = excel_villages - orig_villages
    only_orig = orig_villages - excel_villages
    print(f'  Overlap: {len(overlap)}, Only in Excel: {len(only_excel)}, Only in original: {len(only_orig)}')
    if only_orig:
        print(f'    Only in original: {sorted(only_orig)}')
