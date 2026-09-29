"""Check if feature IDs have common patterns"""
import sys
sys.path.insert(0, 'scripts/ml_pipeline')
from feature_engineering import FeatureEngineer

engineer = FeatureEngineer()
data = engineer.load_canonical_data()

for theme_name, df in data.items():
    print(f"\n{theme_name} sample feature_ids:")
    print(df['feature_id'].head(5).tolist())
    
print("\n=== Checking row numbers in feature IDs ===")
# Feature IDs format: {theme}_{row}_{hash}
# Different themes might have same row numbers

water_rows = set([fid.split('_')[1] for fid in data['water']['feature_id']])
energy_rows = set([fid.split('_')[1] for fid in data['energy']['feature_id']])
regen_rows = set([fid.split('_')[1] for fid in data['regenerative_agriculture']['feature_id']])

print(f"Water row numbers: {sorted(water_rows)[:10]}")
print(f"Energy row numbers: {sorted(energy_rows)[:10]}")
print(f"Regen row numbers: {sorted(regen_rows)[:10]}")

common_rows = water_rows & energy_rows & regen_rows
print(f"\nRow numbers in ALL themes: {len(common_rows)}")
print(f"Common rows: {sorted(common_rows)[:20]}")
