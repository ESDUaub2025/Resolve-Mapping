"""
Spatial Interpolation & Grid Generation
=========================================
Convert point predictions to grid-based probability heatmaps.

Input: Trained models + survey point locations
Output: AI_Grid_Predictions.geojson with regular grid and interpolated probabilities
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import joblib
import warnings
warnings.filterwarnings('ignore')

from scipy.interpolate import griddata
from scipy.spatial import distance_matrix


class GridInterpolator:
    """Generate prediction grids for heatmap visualization."""
    
    def __init__(
        self,
        data_path: str = "data/ml_prepared_data.csv",
        models_dir: str = "data/models"
    ):
        self.data_path = Path(data_path)
        self.models_dir = Path(models_dir)
        self.df = None
        self.models = {}
        self.features = []
        
    def load_data_and_models(self):
        """Load prepared data and trained models."""
        
        # Load data
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data not found: {self.data_path}")
        
        self.df = pd.read_csv(self.data_path)
        print(f"✓ Loaded {len(self.df)} survey points")
        
        # Load feature list
        features_file = self.models_dir / "feature_list.json"
        if features_file.exists():
            with open(features_file, 'r') as f:
                feature_data = json.load(f)
                self.features = feature_data['features']
        else:
            raise FileNotFoundError(f"Feature list not found: {features_file}")
        
        # Load models
        target_mapping = {
            'target_regen_adoption': 'Regen',
            'target_water_risk': 'Water',
            'target_economic_vuln': 'Econ',
            'target_labor_shortage': 'Labor',
            'target_climate_vuln': 'Climate'
        }
        
        for target, short_name in target_mapping.items():
            model_file = self.models_dir / f"{target}_model.joblib"
            if model_file.exists():
                self.models[short_name] = joblib.load(model_file)
                print(f"✓ Loaded model: {short_name}")
            else:
                print(f"⚠️  Model not found: {model_file.name}")
        
        if not self.models:
            raise ValueError("No models loaded")
    
    def predict_survey_points(self) -> pd.DataFrame:
        """Generate predictions for all survey points."""
        
        X = self.df[self.features]
        coords = self.df[['longitude', 'latitude']].values
        
        predictions = pd.DataFrame({
            'longitude': coords[:, 0],
            'latitude': coords[:, 1]
        })
        
        for name, model in self.models.items():
            proba = model.predict_proba(X)[:, 1]
            predictions[f'Prob_{name}'] = proba
            print(f"✓ Predicted {name}: mean={proba.mean():.3f}, std={proba.std():.3f}")
        
        return predictions
    
    def generate_grid(
        self,
        lon_range: Tuple[float, float] = (35.40, 35.70),
        lat_range: Tuple[float, float] = (33.58, 33.80),
        resolution: float = 0.005  # ~500m at this latitude
    ) -> np.ndarray:
        """Generate regular grid covering study area."""
        
        lon_grid = np.arange(lon_range[0], lon_range[1], resolution)
        lat_grid = np.arange(lat_range[0], lat_range[1], resolution)
        
        lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
        grid_points = np.column_stack([lon_mesh.ravel(), lat_mesh.ravel()])
        
        print(f"✓ Generated grid: {len(grid_points)} points ({len(lon_grid)}x{len(lat_grid)})")
        return grid_points
    
    def interpolate_to_grid(
        self,
        survey_predictions: pd.DataFrame,
        grid_points: np.ndarray,
        method: str = 'linear',
        max_distance: float = 0.05  # ~5km
    ) -> pd.DataFrame:
        """Interpolate survey point predictions to grid using spatial interpolation."""
        
        survey_coords = survey_predictions[['longitude', 'latitude']].values
        prob_columns = [c for c in survey_predictions.columns if c.startswith('Prob_')]
        
        grid_df = pd.DataFrame({
            'longitude': grid_points[:, 0],
            'latitude': grid_points[:, 1]
        })
        
        print(f"\nInterpolating {len(prob_columns)} probability fields to grid...")
        
        for prob_col in prob_columns:
            print(f"  {prob_col}...", end=' ')
            
            values = survey_predictions[prob_col].values
            
            # Interpolate using griddata
            if method == 'nearest':
                grid_values = griddata(survey_coords, values, grid_points, method='nearest')
            else:
                # Linear interpolation with fallback to nearest for points outside convex hull
                grid_values = griddata(survey_coords, values, grid_points, method='linear')
                nan_mask = np.isnan(grid_values)
                if nan_mask.any():
                    grid_values[nan_mask] = griddata(
                        survey_coords, values, grid_points[nan_mask], method='nearest'
                    )
            
            # Distance-based weighting: reduce confidence for points far from survey data
            distances = distance_matrix(grid_points, survey_coords)
            min_distances = distances.min(axis=1)
            
            # Apply distance penalty (exponential decay)
            distance_weight = np.exp(-min_distances / (max_distance / 3))
            
            # Clip to [0, 1] and apply weighting
            grid_values = np.clip(grid_values, 0, 1)
            grid_values = grid_values * distance_weight + 0.5 * (1 - distance_weight)
            
            grid_df[prob_col] = grid_values
            print(f"✓ (mean={grid_values.mean():.3f})")
        
        return grid_df
    
    def smooth_probabilities(self, grid_df: pd.DataFrame, window_size: int = 3) -> pd.DataFrame:
        """Apply spatial smoothing to reduce noise."""
        
        prob_columns = [c for c in grid_df.columns if c.startswith('Prob_')]
        
        print(f"\nApplying spatial smoothing (window={window_size})...")
        
        for prob_col in prob_columns:
            values = grid_df[prob_col].values
            
            # Simple moving average smoothing
            smoothed = np.copy(values)
            for i in range(len(values)):
                # Find nearby points (simple distance-based)
                coords_i = grid_df.iloc[i][['longitude', 'latitude']].values
                
                # Use vectorized distance calculation
                all_coords = grid_df[['longitude', 'latitude']].values
                dists = np.sqrt(((all_coords - coords_i) ** 2).sum(axis=1))
                
                nearby_idx = dists < 0.01  # ~1km radius
                if nearby_idx.sum() > 1:
                    smoothed[i] = values[nearby_idx].mean()
            
            grid_df[prob_col] = smoothed
            print(f"  {prob_col}: ✓")
        
        return grid_df
    
    def export_geojson(
        self,
        grid_df: pd.DataFrame,
        output_file: str = "data/geojson/AI_Grid_Predictions.geojson"
    ):
        """Export grid predictions as GeoJSON."""
        
        features = []
        
        for _, row in grid_df.iterrows():
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row['longitude'], row['latitude']]
                },
                "properties": {
                    col: float(row[col]) 
                    for col in grid_df.columns 
                    if col.startswith('Prob_')
                }
            }
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(geojson, f)
        
        print(f"\n✓ Exported {len(features)} grid points to {output_path}")
        print(f"  File size: {output_path.stat().st_size / 1024:.1f} KB")
    
    def run_pipeline(
        self,
        resolution: float = 0.005,
        interpolation_method: str = 'linear',
        apply_smoothing: bool = True
    ):
        """Complete interpolation pipeline."""
        
        print("\n=== Starting Grid Interpolation Pipeline ===\n")
        
        # Step 1: Load data and models
        self.load_data_and_models()
        
        # Step 2: Predict at survey points
        survey_predictions = self.predict_survey_points()
        
        # Step 3: Generate grid
        grid_points = self.generate_grid(resolution=resolution)
        
        # Step 4: Interpolate to grid
        grid_df = self.interpolate_to_grid(
            survey_predictions,
            grid_points,
            method=interpolation_method
        )
        
        # Step 5: Optional smoothing
        if apply_smoothing:
            grid_df = self.smooth_probabilities(grid_df)
        
        # Step 6: Export GeoJSON
        self.export_geojson(grid_df)
        
        print("\n=== Grid Interpolation Complete ===")
        
        # Summary statistics
        prob_cols = [c for c in grid_df.columns if c.startswith('Prob_')]
        print("\n=== Grid Statistics ===")
        for col in prob_cols:
            print(f"{col}:")
            print(f"  Mean: {grid_df[col].mean():.3f}")
            print(f"  Std:  {grid_df[col].std():.3f}")
            print(f"  Min:  {grid_df[col].min():.3f}")
            print(f"  Max:  {grid_df[col].max():.3f}")


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    resolution = float(sys.argv[1]) if len(sys.argv) > 1 else 0.005
    
    print(f"Grid resolution: {resolution}° (~{resolution * 111:.1f}km)")
    
    interpolator = GridInterpolator()
    interpolator.run_pipeline(resolution=resolution)
