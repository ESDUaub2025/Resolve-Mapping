"""
Validate survey data structure and check for duplicates with existing features
"""

import pandas as pd
import json
import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
SURVEY_CSV = PROJECT_ROOT / 'data' / 'MZSurvey farmers ENGLISH_with_coords.csv'
CANONICAL_DIR = PROJECT_ROOT / 'data' / 'geojson' / 'canonical'

def load_survey_data():
    """Load and analyze survey CSV"""
    df = pd.read_csv(SURVEY_CSV)
    
    print("=" * 80)
    print("SURVEY DATA VALIDATION")
    print("=" * 80)
    
    print(f"\n📊 Total survey responses: {len(df)}")
    print(f"📊 Total columns: {len(df.columns)}")
    
    # Village distribution
    village_col = '4.القرية:'
    print(f"\n🏘️ Villages distribution:")
    village_counts = df[village_col].value_counts()
    for village, count in village_counts.items():
        print(f"   {village}: {count} responses")
    
    # Coordinate check
    has_coords = df[['X', 'Y']].notna().all(axis=1).sum()
    print(f"\n📍 Responses with coordinates: {has_coords}/{len(df)}")
    
    # Bekaa vs Mount Lebanon split
    bekaa_villages = ['رياق', 'تربل', 'زحلة']
    bekaa_df = df[df[village_col].isin(bekaa_villages)]
    mount_lebanon_df = df[~df[village_col].isin(bekaa_villages)]
    
    print(f"\n🗺️ Geographic split:")
    print(f"   Bekaa Valley: {len(bekaa_df)} responses")
    print(f"   Mount Lebanon: {len(mount_lebanon_df)} responses")
    
    return df, bekaa_df, mount_lebanon_df, village_col

def check_duplicate_coordinates(df):
    """Check if any survey coordinates match existing canonical GeoJSON features"""
    print(f"\n🔍 Checking for duplicate coordinates with existing data...")
    
    # Load existing canonical GeoJSON files
    existing_coords = []
    if CANONICAL_DIR.exists():
        for geojson_file in CANONICAL_DIR.glob('*.canonical.geojson'):
            with open(geojson_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for feature in data.get('features', []):
                    coords = feature['geometry']['coordinates']
                    existing_coords.append((round(coords[0], 6), round(coords[1], 6)))
    
    print(f"   Existing features: {len(existing_coords)}")
    
    # Check survey coordinates
    survey_coords = []
    duplicates = []
    for idx, row in df.iterrows():
        if pd.notna(row['X']) and pd.notna(row['Y']):
            coord = (round(row['X'], 6), round(row['Y'], 6))
            survey_coords.append(coord)
            if coord in existing_coords:
                village = row.get('4.القرية:', 'Unknown')
                duplicates.append((coord, village))
    
    print(f"   Survey coordinates: {len(survey_coords)}")
    print(f"   ⚠️ Duplicates found: {len(duplicates)}")
    
    if duplicates:
        print(f"\n   Duplicate coordinates:")
        for coord, village in duplicates[:5]:  # Show first 5
            print(f"      {coord} - {village}")
        if len(duplicates) > 5:
            print(f"      ... and {len(duplicates) - 5} more")
    else:
        print(f"   ✅ No duplicates - survey data is NEW")
    
    return len(duplicates) == 0

def analyze_survey_structure(df):
    """Analyze survey columns and identify theme-relevant properties"""
    print(f"\n📋 Column Analysis:")
    
    # Key column patterns for each theme
    theme_patterns = {
        'Water': ['water', 'irrigation', 'rain', 'well', 'مياه', 'ري', 'scarcity', 'شح'],
        'Energy': ['energy', 'diesel', 'solar', 'electric', 'طاقة', 'ديزل', 'شمسية'],
        'Food': ['crops', 'production', 'yield', 'محاصيل', 'إنتاج', 'غذاء'],
        'General Info': ['age', 'gender', 'village', 'land', 'عمر', 'جنس', 'قرية', 'أرض'],
        'Regenerative Agriculture': ['organic', 'compost', 'regenerative', 'عضوي', 'كمبوست', 'تجديد']
    }
    
    for theme, patterns in theme_patterns.items():
        matching_cols = [col for col in df.columns 
                        if any(pattern.lower() in col.lower() for pattern in patterns)]
        print(f"\n   {theme}: {len(matching_cols)} relevant columns")
        if matching_cols and len(matching_cols) <= 10:
            for col in matching_cols[:5]:
                print(f"      - {col}")
    
    return True

def main():
    # Load data
    df, bekaa_df, mount_lebanon_df, village_col = load_survey_data()
    
    # Check for duplicates
    is_new_data = check_duplicate_coordinates(df)
    
    # Analyze structure
    analyze_survey_structure(df)
    
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    if is_new_data:
        print("✅ Survey data is NEW (no duplicate coordinates)")
        print(f"✅ Ready to integrate {len(df)} responses:")
        print(f"   - {len(bekaa_df)} Bekaa Valley responses")
        print(f"   - {len(mount_lebanon_df)} Mount Lebanon responses")
    else:
        print("⚠️ DUPLICATES FOUND - Manual review required")
    
    print("\n📦 Next step: Split survey data by theme and generate CSVs")
    print("=" * 80)

if __name__ == '__main__':
    main()
