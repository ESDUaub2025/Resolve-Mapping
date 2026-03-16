"""
Inspection script for the new Farmers Survey Excel file.
Compares with existing CSV data to identify differences.
"""
import pandas as pd
import json
import os
import sys

BASE = r"d:\Programing\ResolveMaping_final2\data"
NEW_EXCEL = os.path.join(BASE, "Farmers survey 27-2-2026.xlsx")
OLD_EXCEL = os.path.join(BASE, "Original_Survey_Data_Complete.xlsx")

print("=" * 60)
print("NEW EXCEL FILE INSPECTION")
print("=" * 60)

# Read all sheets from new Excel
xl_new = pd.ExcelFile(NEW_EXCEL)
print(f"\nSheets in NEW file: {xl_new.sheet_names}")

new_sheets = {}
for sheet in xl_new.sheet_names:
    df = pd.read_excel(NEW_EXCEL, sheet_name=sheet)
    new_sheets[sheet] = df
    print(f"\n--- Sheet: '{sheet}' ---")
    print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
    print(f"  Columns: {list(df.columns)}")
    # Show first 2 rows of data
    print(f"  First 2 rows sample:")
    print(df.head(2).to_string())

print("\n" + "=" * 60)
print("OLD EXCEL FILE INSPECTION")
print("=" * 60)

xl_old = pd.ExcelFile(OLD_EXCEL)
print(f"\nSheets in OLD file: {xl_old.sheet_names}")

old_sheets = {}
for sheet in xl_old.sheet_names:
    df = pd.read_excel(OLD_EXCEL, sheet_name=sheet)
    old_sheets[sheet] = df
    print(f"\n--- Sheet: '{sheet}' ---")
    print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
    print(f"  Columns: {list(df.columns)}")

print("\n" + "=" * 60)
print("EXISTING CSV STRUCTURE")
print("=" * 60)

arabic_dir = os.path.join(BASE, "layers", "Arabic")
english_dir = os.path.join(BASE, "layers", "English")

print("\nArabic CSVs:")
for f in sorted(os.listdir(arabic_dir)):
    if f.endswith('.csv'):
        df = pd.read_csv(os.path.join(arabic_dir, f), encoding='utf-8-sig')
        print(f"  {f}: {len(df)} rows, cols: {list(df.columns)}")

print("\nEnglish CSVs:")
for f in sorted(os.listdir(english_dir)):
    if f.endswith('.csv'):
        df = pd.read_csv(os.path.join(english_dir, f), encoding='utf-8-sig')
        print(f"  {f}: {len(df)} rows, cols: {list(df.columns)}")

print("\n" + "=" * 60)
print("ROW COUNT COMPARISON (NEW vs OLD vs EXISTING CSVs)")
print("=" * 60)
new_total = sum(len(v) for v in new_sheets.values())
old_total = sum(len(v) for v in old_sheets.values())
print(f"  New Excel total rows (all sheets): {new_total}")
print(f"  Old Excel total rows (all sheets): {old_total}")
print(f"  Difference: {new_total - old_total} rows")

print("\nDone.")
