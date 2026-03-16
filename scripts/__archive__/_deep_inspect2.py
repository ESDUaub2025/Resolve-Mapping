# -*- coding: utf-8 -*-
"""Check ADDITIONAL sheet, original MZSurvey CSV, and Model_Predictions."""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd

EXCEL = 'data/Farmers survey 27-2-2026.xlsx'

# 1. ADDITIONAL sheet
print('=== ADDITIONAL sheet ===')
df_add = pd.read_excel(EXCEL, sheet_name='ADDITIONAL ')
print(f'Rows: {len(df_add)}, Cols: {len(df_add.columns)}')
print(f'Columns: {list(df_add.columns)[:15]}')
if len(df_add) > 0:
    village_col = None
    for c in df_add.columns:
        if 'village' in str(c).lower():
            village_col = c
            break
    if village_col:
        print(f'Villages: {sorted(df_add[village_col].dropna().unique().tolist())}')

# 2. Original MZSurvey CSV (without coords)
print('\n=== MZSurvey farmers ENGLISH.csv ===')
mz = pd.read_csv('data/MZSurvey farmers ENGLISH.csv', encoding='utf-8')
print(f'Rows: {len(mz)}, Cols: {len(mz.columns)}')
print(f'Columns (first 15): {list(mz.columns)[:15]}')
village_col = None
for c in mz.columns:
    if 'village' in c.lower():
        village_col = c
        break
if village_col:
    print(f'Village col: {repr(village_col)}')
    print(f'Villages: {sorted(mz[village_col].dropna().unique().tolist())}')

# 3. REF and CALCUL sheets
for sheet in ['REF', 'CALCUL', 'calcul VILLAGE ']:
    print(f'\n=== {sheet} sheet ===')
    try:
        df = pd.read_excel(EXCEL, sheet_name=sheet)
        print(f'Rows: {len(df)}, Cols: {len(df.columns)}')
        print(f'Columns (first 10): {list(df.columns)[:10]}')
    except Exception as e:
        print(f'Error: {e}')

# 4. Model_Predictions.geojson analysis
print('\n=== Model_Predictions.geojson ===')
mp_file = 'data/geojson/Model_Predictions.geojson'
if os.path.exists(mp_file):
    with open(mp_file, 'r', encoding='utf-8') as f:
        mp = json.load(f)
    feats = mp.get('features', [])
    print(f'Features: {len(feats)}')
    if feats:
        props = feats[0]['properties']
        print(f'Property keys: {list(props.keys())}')
        # Get village names
        vkey = 'Village_Name' if 'Village_Name' in props else None
        if not vkey:
            for k in props:
                if 'village' in k.lower():
                    vkey = k
                    break
        if vkey:
            villages = sorted(set(f['properties'].get(vkey, '') for f in feats if f['properties'].get(vkey)))
            print(f'Villages ({len(villages)}): {villages}')
        print(f'Sample feature props: {feats[0]["properties"]}')
        
        # Check coords
        coords = [f['geometry']['coordinates'] for f in feats if f.get('geometry')]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        print(f'Lon range: {min(lons):.4f} to {max(lons):.4f}')
        print(f'Lat range: {min(lats):.4f} to {max(lats):.4f}')

# 5. Compare Excel dedup villages with original CSV villages (normalized)
print('\n=== Normalized village comparison ===')
import re
def normalize(v):
    v = str(v).strip().lower()
    v = re.sub(r'[^a-z\s]', '', v)
    v = re.sub(r'\s+', ' ', v)
    return v

df_dedup = pd.read_excel(EXCEL, sheet_name='WiTHOUT DUPLICATES FS (2)')
excel_villages = {normalize(v): v for v in df_dedup['Village'].dropna().unique()}

en_water = pd.read_csv('data/layers/English/Water_1.0.en.csv', encoding='utf-8')
water_village_col = [c for c in en_water.columns if 'قرية' in str(c) or 'village' in c.lower()][0]
orig_villages = {normalize(v): v for v in en_water[water_village_col].dropna().unique()}

print(f'Excel (normalized): {len(excel_villages)} villages')
print(f'Original (normalized): {len(orig_villages)} villages')

overlap = set(excel_villages.keys()) & set(orig_villages.keys())
print(f'\nExact match overlap: {len(overlap)}')
for v in sorted(overlap):
    print(f'  {excel_villages[v]} <-> {orig_villages[v]}')

# Fuzzy match the rest
only_excel = set(excel_villages.keys()) - overlap
only_orig = set(orig_villages.keys()) - overlap
print(f'\nOnly in Excel ({len(only_excel)}):')
for v in sorted(only_excel):
    print(f'  {excel_villages[v]}')
print(f'\nOnly in Original ({len(only_orig)}):')
for v in sorted(only_orig):
    print(f'  {orig_villages[v]}')
