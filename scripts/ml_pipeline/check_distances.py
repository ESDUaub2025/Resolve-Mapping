"""Check actual distances between nearest points across themes"""
import sys
sys.path.insert(0, 'scripts/ml_pipeline')
from feature_engineering import FeatureEngineer
from scipy.spatial import cKDTree
import numpy as np

engineer = FeatureEngineer()
data = engineer.load_canonical_data()

water_coords = data['water'][['longitude', 'latitude']].values
energy_coords = data['energy'][['longitude', 'latitude']].values

# Build KDTree for energy
tree = cKDTree(energy_coords)

# Find nearest energy point for each water point
distances, indices = tree.query(water_coords, k=1)

print("=== Distance Statistics (degrees) ===")
print(f"Min distance: {distances.min():.6f}")
print(f"Max distance: {distances.max():.6f}")
print(f"Mean distance: {distances.mean():.6f}")
print(f"Median distance: {np.median(distances):.6f}")

# Convert to approximate meters (1 degree ≈ 111km at this latitude)
print("\n=== Distance Statistics (approximate meters) ===")
print(f"Min: {distances.min() * 111000:.1f}m")
print(f"Max: {distances.max() * 111000:.1f}m")
print(f"Mean: {distances.mean() * 111000:.1f}m")
print(f"Median: {np.median(distances) * 111000:.1f}m")

# Show distribution
print("\n=== Distance Distribution ===")
thresholds = [0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05]
for thresh in thresholds:
    count = (distances < thresh).sum()
    print(f"Within {thresh} degrees ({thresh * 111000:.0f}m): {count}/{len(distances)} ({count/len(distances)*100:.1f}%)")
