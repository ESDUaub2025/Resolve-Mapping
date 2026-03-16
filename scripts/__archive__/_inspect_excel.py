# -*- coding: utf-8 -*-
"""Inspect the new survey Excel file in detail."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd

EXCEL = 'data/Farmers survey 27-2-2026.xlsx'

# Sheet 1: English FS (full dataset)
df_en = pd.read_excel(EXCEL, sheet_name='English FS')
print(f'=== English FS ===')
print(f'Rows: {len(df_en)}, Cols: {len(df_en.columns)}')
print(f'\nColumn names:')
for i, c in enumerate(df_en.columns):
    print(f'  {i}: {repr(c)}')

print(f'\nVillages ({df_en["Village"].nunique()} unique):')
for v in sorted(df_en['Village'].dropna().unique()):
    count = len(df_en[df_en['Village'] == v])
    print(f'  {v} ({count})')

# Sheet: WITHOUT DUPLICATES
df_dedup = pd.read_excel(EXCEL, sheet_name='WiTHOUT DUPLICATES FS (2)')
print(f'\n=== WITHOUT DUPLICATES FS (2) ===')
print(f'Rows: {len(df_dedup)}, Cols: {len(df_dedup.columns)}')
print(f'\nColumn names:')
for i, c in enumerate(df_dedup.columns):
    print(f'  {i}: {repr(c)}')

# Sheet: Arabic FS
df_ar = pd.read_excel(EXCEL, sheet_name='Arabic FS')
print(f'\n=== Arabic FS ===')
print(f'Rows: {len(df_ar)}, Cols: {len(df_ar.columns)}')
print(f'\nColumn names (first 15):')
for i, c in enumerate(df_ar.columns[:15]):
    print(f'  {i}: {repr(c)}')

# Check coordinates
coord_cols_en = [c for c in df_en.columns if any(x in c.lower() for x in ['lat', 'lon', 'x', 'y', 'coord', 'gps'])]
print(f'\nCoordinate-like columns in English FS: {coord_cols_en}')

coord_cols_dedup = [c for c in df_dedup.columns if any(x in c.lower() for x in ['lat', 'lon', 'x', 'y', 'coord', 'gps'])]
print(f'Coordinate-like columns in Dedup: {coord_cols_dedup}')

# Check for X/Y columns
for sheet_name, df in [('English FS', df_en), ('Dedup', df_dedup)]:
    xy = [c for c in df.columns if c.strip() in ('X', 'Y', 'x', 'y')]
    print(f'\nX/Y columns in {sheet_name}: {xy}')
    if xy:
        non_null = df[xy].notna().sum()
        print(f'  Non-null counts: {dict(non_null)}')
        
# All sheet names
xl = pd.ExcelFile(EXCEL)
print(f'\nAll sheets: {xl.sheet_names}')
