"""
Add X, Y, القرية columns to all new theme CSV files
===================================================
Quick fix: Copies coordinates and village names from General_Info_new.csv
to Water_new.csv and Regenerative_Agriculture_new.csv for GeoJSON generation.
"""

import pandas as pd
from pathlib import Path

# Load General_Info with coordinates
print("Loading General_Info_new.csv...")
general_info = pd.read_csv('data/layers/Arabic/General_Info_new.csv', encoding='utf-8')
print(f"  Loaded {len(general_info)} rows with columns: {list(general_info.columns)}")

# Extract coordinates (assuming same order as original survey)
coords_df = general_info[['X', 'Y', 'القرية']].copy()

# Fix Water theme
print("\nFixing Water_new.csv...")
water = pd.read_csv('data/layers/Arabic/Water_new.csv', encoding='utf-8')
print(f"  Original: {len(water)} rows × {len(water.columns)} columns")

# Add coordinates at the beginning
water_fixed = pd.concat([coords_df, water], axis=1)
print(f"  Fixed: {len(water_fixed)} rows × {len(water_fixed.columns)} columns")

# Save
water_fixed.to_csv('data/layers/Arabic/Water_new.csv', index=False, encoding='utf-8')
print(f"  ✓ Saved with coordinates")

# Fix Regenerative Agriculture theme
print("\nFixing Regenerative_Agriculture_new.csv...")
regen = pd.read_csv('data/layers/Arabic/Regenerative_Agriculture_new.csv', encoding='utf-8')
print(f"  Original: {len(regen)} rows × {len(regen.columns)} columns")

# Add coordinates at the beginning
regen_fixed = pd.concat([coords_df, regen], axis=1)
print(f"  Fixed: {len(regen_fixed)} rows × {len(regen_fixed.columns)} columns")

# Save
regen_fixed.to_csv('data/layers/Arabic/Regenerative_Agriculture_new.csv', index=False, encoding='utf-8')
print(f"  ✓ Saved with coordinates")

print("\n" + "="*70)
print("✅ FIX COMPLETE")
print("="*70)
print("All theme CSV files now have X, Y, القرية columns")
print("Ready for canonical GeoJSON generation")
