"""
Check Village Coordinate Availability
======================================
Cross-reference new villages with existing coordinate data
"""
import pandas as pd
import json
from pathlib import Path

# New villages from survey
new_villages = [
    'ماسما', 'تربل', 'دلهامية', 'الفاكهة', 'رياق', 
    'علي النهري', 'حارة الفيكاني', 'نبي شيت', 'مشغرة', 'اللبوة', 'زحلة'
]

# Load existing canonical data to find matching villages
canonical_dir = Path('data/geojson/canonical')
coords_by_village = {}

themes = ['Water', 'Energy', 'Food', 'General_Info', 'Regenerative_Agriculture']
for theme in themes:
    geojson_path = canonical_dir / f'{theme}.canonical.geojson'
    if geojson_path.exists():
        with open(geojson_path, encoding='utf-8') as f:
            data = json.load(f)
        
        for feature in data['features']:
            props = feature['properties']['values']['ar']
            village = props.get('القرية', '')
            coords = feature['geometry']['coordinates']
            
            if village:
                if village not in coords_by_village:
                    coords_by_village[village] = []
                coords_by_village[village].append({
                    'lon': coords[0],
                    'lat': coords[1],
                    'theme': theme
                })

print("="*80)
print("VILLAGE COORDINATE AVAILABILITY CHECK")
print("="*80)

print(f"\nExisting villages in database: {len(coords_by_village)}")
print(f"New villages from survey: {len(new_villages)}\n")

found_villages = []
missing_villages = []

for village in sorted(new_villages):
    if village in coords_by_village:
        coords_list = coords_by_village[village]
        avg_lon = sum(c['lon'] for c in coords_list) / len(coords_list)
        avg_lat = sum(c['lat'] for c in coords_list) / len(coords_list)
        found_villages.append({
            'name': village,
            'lon': avg_lon,
            'lat': avg_lat,
            'sample_count': len(coords_list)
        })
        print(f"✓ {village:20s} FOUND (Lon: {avg_lon:.6f}, Lat: {avg_lat:.6f}, {len(coords_list)} existing points)")
    else:
        missing_villages.append(village)
        print(f"✗ {village:20s} NEW - NEEDS COORDINATES")

print(f"\n{'='*80}")
print(f"SUMMARY:")
print(f"  ✓ Villages with existing coordinates: {len(found_villages)}/{len(new_villages)}")
print(f"  ✗ Villages needing coordinates: {len(missing_villages)}/{len(new_villages)}")

if missing_villages:
    print(f"\n⚠️  CRITICAL: {len(missing_villages)} villages have NO coordinate data")
    print(f"Missing villages: {', '.join(missing_villages)}")
    print(f"\n📋 REQUIRED ACTION:")
    print(f"   1. Obtain GPS coordinates for new villages")
    print(f"   2. OR use approximate village center coordinates from maps")
    print(f"   3. OR skip these villages until coordinates are available")

# Save results
output = {
    'found_villages': found_villages,
    'missing_villages': missing_villages,
    'total_new_villages': len(new_villages),
    'matched_count': len(found_villages),
    'missing_count': len(missing_villages)
}

with open('data/village_coordinate_check.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n✓ Results saved to: data/village_coordinate_check.json")
print("="*80)
