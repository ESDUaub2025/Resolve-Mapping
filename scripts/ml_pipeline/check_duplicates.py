"""Check for duplicate coordinates in themes"""
import sys
sys.path.insert(0, 'scripts/ml_pipeline')
from feature_engineering import FeatureEngineer

engineer = FeatureEngineer()
data = engineer.load_canonical_data()

for theme_name, df in data.items():
    df['coord_key'] = df['longitude'].astype(str) + '_' + df['latitude'].astype(str)
    duplicates = df['coord_key'].duplicated().sum()
    unique_coords = df['coord_key'].nunique()
    total = len(df)
    print(f"\n{theme_name}:")
    print(f"  Total features: {total}")
    print(f"  Unique coordinates: {unique_coords}")
    print(f"  Duplicate coordinates: {duplicates}")
    
    if unique_coords < total:
        print(f"  ⚠️  {total - unique_coords} features will be lost in coordinate merge!")
