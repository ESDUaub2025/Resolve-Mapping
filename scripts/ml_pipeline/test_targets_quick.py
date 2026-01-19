#!/usr/bin/env python3
"""Quick test of target calibrations."""

import sys
sys.path.insert(0, 'd:/Programing/ResolveMaping_final2/scripts/ml_pipeline')

from feature_engineering import FeatureEngineer

# Initialize and load data
fe = FeatureEngineer()
data_dict = fe.load_canonical_data()

# Merge themes
df = fe.merge_themes(data_dict)

# Create targets
df = fe.create_target_variables(df)

# Print distributions
print("\n=== CALIBRATED TARGET DISTRIBUTIONS ===\n")
for col in [c for c in df.columns if c.startswith('target_')]:
    pos_count = df[col].sum()
    total = len(df)
    pos_rate = df[col].mean() * 100
    print(f"{col}:")
    print(f"  Positive: {pos_count}/{total} ({pos_rate:.1f}%)")
    print(f"  Negative: {total - pos_count}/{total} ({100-pos_rate:.1f}%)")
    print()
