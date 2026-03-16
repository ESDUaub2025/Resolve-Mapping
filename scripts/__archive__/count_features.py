"""
Check if survey data is already integrated by counting features
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CANONICAL_DIR = PROJECT_ROOT / 'data' / 'geojson' / 'canonical'

print("=" * 80)
print("CANONICAL GEOJSON FEATURE COUNT")
print("=" * 80)

total = 0
for geojson_file in sorted(CANONICAL_DIR.glob('*.canonical.geojson')):
    with open(geojson_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        count = len(data.get('features', []))
        total += count
        print(f"{geojson_file.name:40s} {count:4d} features")

print("=" * 80)
print(f"{'TOTAL':40s} {total:4d} features")
print("=" * 80)

print("\n📌 Expected: 287 features (from documentation)")
print(f"📌 Found: {total} features")

if total > 287:
    print(f"\n✅ Survey data appears ALREADY INTEGRATED (+{total - 287} features)")
    print("   The 29 survey responses are already in the canonical GeoJSON files")
elif total == 287:
    print(f"\n❓ Survey data NOT yet integrated (matching documented count)")
else:
    print(f"\n⚠️ Feature count LOWER than expected (missing {287 - total} features)")
