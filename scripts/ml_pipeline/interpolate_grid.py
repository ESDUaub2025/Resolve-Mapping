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
        self._model_features = {}  # per-model feature lists
        
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
                self._model_features = feature_data.get('model_features', {})
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
        
        coords = self.df[['longitude', 'latitude']].values
        
        predictions = pd.DataFrame({
            'longitude': coords[:, 0],
            'latitude': coords[:, 1]
        })
        
        # Map short model names to target names for feature lookup
        short_to_target = {
            'Regen': 'target_regen_adoption',
            'Water': 'target_water_risk',
            'Econ': 'target_economic_vuln',
            'Labor': 'target_labor_shortage',
            'Climate': 'target_climate_vuln',
        }
        
        for name, model in self.models.items():
            # Use per-model features if available, else global
            target = short_to_target.get(name, '')
            model_feats = self._model_features.get(target, self.features)
            # Filter to features present in data
            available_feats = [f for f in model_feats if f in self.df.columns]
            X = self.df[available_feats]
            
            proba = model.predict_proba(X)[:, 1]
            predictions[f'Prob_{name}'] = proba
            print(f"✓ Predicted {name}: mean={proba.mean():.3f}, std={proba.std():.3f}")
        
        return predictions
    
    def generate_grid(
        self,
        lon_range: Tuple[float, float] = None,
        lat_range: Tuple[float, float] = None,
        resolution: float = 0.005  # ~500m at this latitude
    ) -> np.ndarray:
        """Generate regular grid covering study area.
        
        If lon/lat ranges not specified, computes from data with padding.
        """
        if lon_range is None or lat_range is None:
            # Dynamically compute bounds from survey data
            pad = 0.02  # ~2km padding
            lon_range = (
                self.df['longitude'].min() - pad,
                self.df['longitude'].max() + pad
            )
            lat_range = (
                self.df['latitude'].min() - pad,
                self.df['latitude'].max() + pad
            )
            print(f"  Dynamic bounds: lon [{lon_range[0]:.4f}, {lon_range[1]:.4f}], lat [{lat_range[0]:.4f}, {lat_range[1]:.4f}]")
        
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
    
    def export_model_predictions(
        self,
        survey_predictions: pd.DataFrame,
        output_file: str = "data/geojson/Model_Predictions.geojson"
    ):
        """Export discrete predictions at survey points for app.js AI layers.
        
        Generates Model_Predictions.geojson with property names matching
        what addAiHeatmapLayer() expects: Pred_Regen_Adoption, Pred_Water_Risk,
        Pred_Production_Level (discrete string values "0", "1", "2").
        
        Also includes composite indices (idx_*), PCA scores (pca_*),
        and cluster assignment (farmer_cluster) if available in source data.
        """
        
        # Map probability column names to app.js property names
        prob_to_pred = {
            'Prob_Regen': 'Pred_Regen_Adoption',
            'Prob_Water': 'Pred_Water_Risk',
            'Prob_Econ': 'Pred_Production_Level',
            'Prob_Climate': 'Pred_Climate_Vuln',
        }
        
        # Columns from unsupervised analysis to include
        index_cols = [c for c in self.df.columns if c.startswith('idx_')]
        pca_cols = [c for c in self.df.columns if c.startswith('pca_')]
        cluster_col = 'farmer_cluster' if 'farmer_cluster' in self.df.columns else None
        
        # Get village names from source data if available
        village_col = None
        for c in self.df.columns:
            if c == 'water_القرية' or c == 'water_4. Village':
                village_col = c
                break
        if village_col is None:
            for c in self.df.columns:
                if 'village' in c.lower() or c.endswith('_القرية'):
                    village_col = c
                    break
        
        features = []
        for idx, row in survey_predictions.iterrows():
            props = {
                'source_row': str(idx + 1),
            }
            
            # Add village name if available
            if village_col and idx < len(self.df):
                v = self.df.iloc[idx].get(village_col)
                if pd.notna(v):
                    props['Village_Name'] = str(v)
            
            # Add data source
            if 'data_source' in self.df.columns and idx < len(self.df):
                props['data_source'] = str(self.df.iloc[idx].get('data_source', ''))
            
            # Convert probabilities to discrete predictions
            for prob_col, pred_name in prob_to_pred.items():
                if prob_col in survey_predictions.columns:
                    prob = row[prob_col]
                    # Binary: threshold at 0.5
                    if pred_name in ('Pred_Regen_Adoption', 'Pred_Water_Risk'):
                        props[pred_name] = str(int(prob >= 0.5))
                    else:
                        # Ternary: <0.33 → "0", 0.33-0.66 → "1", >0.66 → "2"
                        if prob < 0.33:
                            props[pred_name] = "0"
                        elif prob < 0.66:
                            props[pred_name] = "1"
                        else:
                            props[pred_name] = "2"
            
            # Add composite indices (0-100 scale)
            if idx < len(self.df):
                for col in index_cols:
                    v = self.df.iloc[idx].get(col)
                    if pd.notna(v):
                        props[col] = round(float(v), 1)
                
                for col in pca_cols:
                    v = self.df.iloc[idx].get(col)
                    if pd.notna(v):
                        props[col] = round(float(v), 1)
                
                if cluster_col:
                    v = self.df.iloc[idx].get(cluster_col)
                    if pd.notna(v):
                        props['farmer_cluster'] = str(int(v))
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row['longitude']), float(row['latitude'])]
                },
                "properties": props
            }
            features.append(feature)
        
        geojson = {"type": "FeatureCollection", "features": features}
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(geojson, f, ensure_ascii=False)
        
        print(f"\n✓ Exported {len(features)} predictions to {output_path}")
        print(f"  File size: {output_path.stat().st_size / 1024:.1f} KB")
        
        # Summary
        for pred_name in prob_to_pred.values():
            vals = [f['properties'].get(pred_name) for f in features if pred_name in f['properties']]
            if vals:
                from collections import Counter
                dist = Counter(vals)
                print(f"  {pred_name}: {dict(dist)}")
        
        if index_cols:
            print(f"  Composite indices: {', '.join(index_cols)}")
        if cluster_col:
            cluster_vals = [f['properties'].get('farmer_cluster') for f in features 
                           if 'farmer_cluster' in f['properties']]
            from collections import Counter
            print(f"  Clusters: {dict(Counter(cluster_vals))}")
    
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
        
        # Step 6: Export GeoJSON (grid)
        self.export_geojson(grid_df)
        
        # Step 7: Generate Model_Predictions.geojson (discrete predictions at survey points)
        self.export_model_predictions(survey_predictions)
        
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
