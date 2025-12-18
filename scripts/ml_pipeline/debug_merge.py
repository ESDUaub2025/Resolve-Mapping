"""Debug merge to see which features don't match"""
import sys
sys.path.insert(0, 'scripts/ml_pipeline')
from feature_engineering import FeatureEngineer
import pandas as pd

engineer = FeatureEngineer()
data = engineer.load_canonical_data()

# Add merge keys to each theme
for theme_name, df in data.items():
    df['merge_key'] = df['longitude'].round(6).astype(str) + '_' + df['latitude'].round(6).astype(str)

# Get unique merge keys from each theme
water_keys = set(data['water']['merge_key'])
energy_keys = set(data['energy']['merge_key'])
food_keys = set(data['food']['merge_key'])
general_keys = set(data['general_info']['merge_key'])
regen_keys = set(data['regenerative_agriculture']['merge_key'])

print("=== Coordinate Overlap Analysis ===")
print(f"Water unique coords: {len(water_keys)}")
print(f"Energy unique coords: {len(energy_keys)}")
print(f"Food unique coords: {len(food_keys)}")
print(f"General unique coords: {len(general_keys)}")
print(f"Regen unique coords: {len(regen_keys)}")

# Find intersection
all_themes = water_keys & energy_keys & food_keys & general_keys & regen_keys
print(f"\n✓ Coords present in ALL themes: {len(all_themes)}")

# Find what's missing
print(f"\n⚠️  Energy coords NOT in water: {len(energy_keys - water_keys)}")
print(f"⚠️  Food coords NOT in water: {len(food_keys - water_keys)}")
print(f"⚠️  General coords NOT in water: {len(general_keys - water_keys)}")
print(f"⚠️  Regen coords NOT in water: {len(regen_keys - water_keys)}")

print(f"\n⚠️  Water coords NOT in regen: {len(water_keys - regen_keys)}")

# Show sample mismatches
if energy_keys - water_keys:
    print("\nSample energy coords not in water:")
    for coord in list(energy_keys - water_keys)[:3]:
        print(f"  {coord}")
