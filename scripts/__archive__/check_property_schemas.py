"""
Compare survey CSV columns with PropertySchema mappings to find gaps
"""

import pandas as pd
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SURVEY_CSV = PROJECT_ROOT / 'data' / 'MZSurvey farmers ENGLISH_with_coords.csv'

# Load survey data
df = pd.read_csv(SURVEY_CSV)

print("=" * 80)
print("PROPERTY SCHEMA COMPLETENESS CHECK")
print("=" * 80)

# Extract relevant columns per theme (Arabic column names used in canonical GeoJSON)
theme_columns = {
    'Water': [col for col in df.columns if any(keyword in col for keyword in ['مياه', 'ري', 'Water', 'irrigation', 'rain', 'well', 'scarcity', 'شح'])],
    'Energy': [col for col in df.columns if any(keyword in col for keyword in ['طاقة', 'Energy', 'diesel', 'solar', 'ديزل', 'شمسية', 'كهرباء'])],
    'Food': [col for col in df.columns if any(keyword in col for keyword in ['محاصيل', 'إنتاج', 'Crops', 'production', 'منتج', 'غذاء'])],
    'General Info': [col for col in df.columns if any(keyword in col for keyword in ['القرية', 'العمر', 'الجنس', 'Village', 'Age', 'Gender', 'أرض', 'Land'])],
    'Regenerative Agriculture': [col for col in df.columns if any(keyword in col for keyword in ['تجديد', 'عضوي', 'كمبوست', 'regenerative', 'organic', 'compost', 'Soil', 'تربة', 'pesticide', 'مبيد'])]
}

print("\n📋 Survey Columns by Theme:\n")
for theme, cols in theme_columns.items():
    print(f"{theme}:")
    print(f"  Total relevant columns: {len(cols)}")
    if cols:
        print(f"  Sample columns:")
        for col in cols[:5]:  # Show first 5
            # Shorten long column names
            display_col = col if len(col) <= 60 else col[:57] + "..."
            print(f"    - {display_col}")
    print()

# Check which properties appear in canonical GeoJSON files
print("=" * 80)
print("CHECKING CANONICAL GEOJSON PROPERTIES")
print("=" * 80)

CANONICAL_DIR = PROJECT_ROOT / 'data' / 'geojson' / 'canonical'

for theme_key, theme_name in [('Water', 'Water'), ('Energy', 'Energy'), ('Food', 'Food'), ('General_Info', 'General Info'), ('Regenerative_Agriculture', 'Regenerative Agriculture')]:
    new_file = CANONICAL_DIR / f'{theme_key}_new.canonical.geojson'
    
    if new_file.exists():
        with open(new_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data['features']:
                # Get properties from first feature
                sample_feature = data['features'][0]
                if 'values' in sample_feature['properties']:
                    ar_props = sample_feature['properties']['values'].get('ar', {})
                    en_props = sample_feature['properties']['values'].get('en', {})
                    
                    print(f"\n{theme_name} (_new file):")
                    print(f"  Features: {len(data['features'])}")
                    print(f"  Arabic properties: {len(ar_props)} keys")
                    print(f"  English properties: {len(en_props)} keys")
                    
                    # Show first few property keys
                    print(f"  Sample Arabic keys:")
                    for key in list(ar_props.keys())[:5]:
                        print(f"    - {key}")

print("\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)
print("1. Verify PropertySchemas in app/modules/i18n/property-schemas.js")
print("2. Add missing property mappings if any")
print("3. Test details panel displays all survey properties")
print("=" * 80)
