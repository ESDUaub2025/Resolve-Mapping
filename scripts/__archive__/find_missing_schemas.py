"""
Find missing property mappings by comparing canonical GeoJSON keys with PropertySchemas
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CANONICAL_DIR = PROJECT_ROOT / 'data' / 'geojson' / 'canonical'
SCHEMA_FILE = PROJECT_ROOT / 'app' / 'modules' / 'i18n' / 'property-schemas.js'

print("=" * 80)
print("FINDING MISSING PROPERTY SCHEMA MAPPINGS")
print("=" * 80)

# Extract all property keys from canonical GeoJSON files
canonical_keys = {}

for theme_key in ['Water', 'Energy', 'Food', 'General_Info', 'Regenerative_Agriculture']:
    new_file = CANONICAL_DIR / f'{theme_key}_new.canonical.geojson'
    
    if new_file.exists():
        with open(new_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data['features']:
                # Collect all unique keys from all features
                all_keys = set()
                for feature in data['features']:
                    if 'values' in feature['properties']:
                        ar_props = feature['properties']['values'].get('ar', {})
                        en_props = feature['properties']['values'].get('en', {})
                        all_keys.update(ar_props.keys())
                        all_keys.update(en_props.keys())
                
                canonical_keys[theme_key] = sorted(all_keys)

# Read schema file content
with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
    schema_content = f.read()

# Check which keys are missing from schemas
print("\n📋 MISSING PROPERTY MAPPINGS:\n")

missing_mappings = {}
for theme, keys in canonical_keys.items():
    theme_display = theme.replace('_', ' ')
    missing = []
    
    for key in keys:
        # Check if key appears in schema file (case-sensitive)
        if f"'{key}'" not in schema_content and f'"{key}"' not in schema_content:
            missing.append(key)
    
    if missing:
        missing_mappings[theme] = missing
        print(f"{theme_display}:")
        print(f"  Missing {len(missing)} mappings:")
        for key in missing[:10]:  # Show first 10
            display_key = key if len(key) <= 70 else key[:67] + "..."
            print(f"    - {display_key}")
        if len(missing) > 10:
            print(f"    ... and {len(missing) - 10} more")
        print()
    else:
        print(f"{theme_display}: ✅ All keys mapped ({len(keys)} total)")

if not missing_mappings:
    print("\n✅ NO MISSING MAPPINGS - All survey properties are already mapped!")
else:
    print(f"\n⚠️ Total themes with missing mappings: {len(missing_mappings)}")
    print(f"⚠️ Total missing keys: {sum(len(v) for v in missing_mappings.values())}")
    
    print("\n" + "=" * 80)
    print("RECOMMENDED ADDITIONS TO PropertySchemas")
    print("=" * 80)
    
    for theme, keys in missing_mappings.items():
        theme_key = theme.lower().replace('_', '').replace(' ', '')
        if theme_key == 'generalinfo':
            theme_key = 'general'
        elif theme_key == 'regenerativeagriculture':
            theme_key = 'regen'
        
        print(f"\n// Add to {theme_key} schema:")
        for key in keys[:5]:  # Show first 5
            print(f"            '{key}': {{ en: 'TODO', ar: 'TODO' }},")

print("\n" + "=" * 80)
