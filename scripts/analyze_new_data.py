"""
Analyze New Survey Data - Phase 1: Data Inspection
==================================================
Comprehensive analysis of mixed Arabic/English survey data
"""
import pandas as pd
import json
from pathlib import Path

# Load the mixed-language survey data
input_file = Path('data/MZSurvey farmers ENGLISH.csv')
df = pd.read_csv(input_file, encoding='utf-8')

print("="*80)
print("PHASE 1: DATA INSPECTION REPORT")
print("="*80)

# 1. Basic Statistics
print(f"\n📊 DATASET OVERVIEW")
print(f"Total rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")
print(f"Non-empty rows: {df.dropna(how='all').shape[0]}")

# 2. Village Analysis (CRITICAL FOR MAPPING)
print(f"\n🏘️  VILLAGE NAMES (Arabic)")
if '4.القرية:' in df.columns:
    villages_ar = df['4.القرية:'].dropna().unique()
    print(f"Total unique villages: {len(villages_ar)}")
    for i, village in enumerate(sorted(villages_ar), 1):
        count = len(df[df['4.القرية:'] == village])
        print(f"  {i:2d}. {village:20s} ({count} respondents)")
else:
    print("  ❌ ERROR: Arabic village column not found!")

# 3. Coordinate Check (CRITICAL)
print(f"\n📍 COORDINATE DATA CHECK")
coord_keywords = ['latitude', 'longitude', 'lat', 'lon', 'x', 'y', 'coord', 'location']
coord_cols = [c for c in df.columns if any(kw in c.lower() for kw in coord_keywords)]

if coord_cols:
    print(f"  ✓ Found potential coordinate columns:")
    for col in coord_cols:
        non_null = df[col].notna().sum()
        print(f"    - {col}: {non_null}/{len(df)} non-null values")
else:
    print(f"  ❌ CRITICAL ISSUE: No coordinate columns found!")
    print(f"  ⚠️  This data CANNOT be mapped without coordinates (X/Y or Lat/Lon)")
    print(f"  📋 REQUIRED ACTION: Add coordinate columns before proceeding")

# 4. Column Structure Analysis
print(f"\n📋 COLUMN STRUCTURE")
english_cols = [c for c in df.columns if not any(ord(ch) > 127 for ch in c)]
arabic_cols = [c for c in df.columns if any(ord(ch) > 127 for ch in c)]
mixed_cols = [c for c in df.columns if any(ord(ch) > 127 for ch in c) and any(ord(ch) < 128 and ch.isalpha() for ch in c)]

print(f"  English-only columns: {len(english_cols)}")
print(f"  Arabic-only columns: {len(arabic_cols)}")
print(f"  Mixed (both languages): {len(mixed_cols)}")

# 5. Sample paired columns
print(f"\n🔗 SAMPLE PAIRED COLUMNS (English | Arabic)")
paired_cols = [
    ('4. Village', '4.القرية:'),
    ('10. Main Crops', '10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟'),
    ('13. Water Source', '13.ما هو المصدر الرئيسي للمياه المستخدمة في الري؟'),
    ('14. Energy Source', '14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟'),
]

for en_col, ar_col in paired_cols:
    en_exists = en_col in df.columns
    ar_exists = ar_col in df.columns
    status = "✓" if (en_exists and ar_exists) else "❌"
    print(f"  {status} {en_col[:40]:40s} | {ar_col[:40]}")

# 6. Data Completeness
print(f"\n📊 DATA COMPLETENESS (Critical Fields)")
critical_fields = {
    'Respondent Name (AR)': '1.اسم المُستجيب:',
    'Village (AR)': '4.القرية:',
    'Main Crops (AR)': '10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟',
    'Water Source (AR)': '13.ما هو المصدر الرئيسي للمياه المستخدمة في الري؟',
}

for label, col in critical_fields.items():
    if col in df.columns:
        filled = df[col].notna().sum()
        pct = (filled / len(df)) * 100
        status = "✓" if pct > 80 else "⚠️" if pct > 50 else "❌"
        print(f"  {status} {label:25s}: {filled:2d}/{len(df):2d} ({pct:5.1f}%)")

# 7. Export Summary Report
report = {
    "total_rows": len(df),
    "total_columns": len(df.columns),
    "villages": list(villages_ar) if '4.القرية:' in df.columns else [],
    "has_coordinates": len(coord_cols) > 0,
    "coordinate_columns": coord_cols,
    "english_columns": len(english_cols),
    "arabic_columns": len(arabic_cols),
    "mixed_columns": len(mixed_cols),
}

output_file = Path('data/new_data_inspection_report.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f"\n✓ Report saved to: {output_file}")
print("="*80)
