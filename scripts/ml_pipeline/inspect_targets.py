"""Quick inspection to see why targets are 0%"""
import pandas as pd

df = pd.read_csv('data/ml_prepared_data.csv')

print("=== Regenerative Agriculture Columns ===")
regen_cols = [c for c in df.columns if 'regenerative' in c.lower()]
for col in regen_cols[:10]:
    print(f"\n{col}:")
    print(df[col].value_counts().head(5))

print("\n\n=== Energy Columns (for labor) ===")
energy_cols = [c for c in df.columns if 'energy' in c.lower()]
for col in energy_cols[:10]:
    print(f"\n{col}:")
    print(df[col].value_counts().head(5))

print("\n\n=== Farm Size & Production ===")
if 'general_info__3' in df.columns:
    print("\ngeneral_info__3 (farm size):")
    print(df['general_info__3'].value_counts())

if 'food__5' in df.columns:
    print("\nfood__5 (production):")
    print(df['food__5'].value_counts())
