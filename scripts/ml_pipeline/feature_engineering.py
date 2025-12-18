"""
Feature Engineering Pipeline
=============================
Transforms canonical GeoJSON survey data into ML-ready features.

Input: Canonical GeoJSON files (Water, Energy, Food, General_Info, Regenerative_Agriculture)
Output: Pandas DataFrame with engineered features and target variables
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


class FeatureEngineer:
    """Transform raw survey data into ML-ready features."""
    
    def __init__(self, data_dir: str = "data/geojson/canonical"):
        self.data_dir = Path(data_dir)
        self.features_df = None
        
    def load_canonical_data(self) -> Dict[str, pd.DataFrame]:
        """Load all canonical GeoJSON files into DataFrames."""
        themes = ['Water', 'Energy', 'Food', 'General_Info', 'Regenerative_Agriculture']
        data = {}
        
        for theme in themes:
            filepath = self.data_dir / f"{theme}.canonical.geojson"
            if not filepath.exists():
                print(f"Warning: {filepath} not found, skipping {theme}")
                continue
                
            with open(filepath, 'r', encoding='utf-8') as f:
                geojson = json.load(f)
            
            records = []
            for feature in geojson['features']:
                props = feature['properties']
                coords = feature['geometry']['coordinates']
                
                # Get English values
                values = props.get('values', {}).get('en', {})
                
                record = {
                    'feature_id': props.get('featureId'),
                    'theme': props.get('theme'),
                    'longitude': coords[0],
                    'latitude': coords[1],
                    **values  # Unpack all English property values
                }
                records.append(record)
            
            data[theme.lower()] = pd.DataFrame(records)
            print(f"✓ Loaded {len(records)} records from {theme}")
        
        return data
    
    def merge_themes(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Merge all theme DataFrames using proximity-based coordinate matching."""
        from scipy.spatial import cKDTree
        
        # Use water theme as base (has most complete village coverage)
        base = data.get('water', pd.DataFrame())
        
        if base.empty:
            raise ValueError("Water theme data is required as base")
        
        print("⚠️  Using proximity-based coordinate matching (~1km threshold for drift)")
        
        # Rename columns to include theme prefix (except common ones)
        preserve_cols = ['feature_id', 'theme', 'longitude', 'latitude']
        for col in base.columns:
            if col not in preserve_cols:
                base = base.rename(columns={col: f'water_{col}'})
        
        # Create spatial index for base (water) coordinates
        base_coords = base[['longitude', 'latitude']].values
        
        # Merge other themes using proximity matching
        for theme_name, df in data.items():
            if theme_name == 'water' or df.empty:
                continue
            
            # Build KDTree for this theme's coordinates
            theme_coords = df[['longitude', 'latitude']].values
            tree = cKDTree(theme_coords)
            
            # For each base point, find nearest neighbor in this theme
            # Distance threshold: ~1.1km at this latitude (0.01 degrees ≈ 1110m)
            # This accounts for coordinate drift between themes
            distances, indices = tree.query(base_coords, k=1, distance_upper_bound=0.01)
            
            # Create mapping of base index to theme index
            valid_matches = distances < 0.01  # Only keep matches within threshold
            
            # Initialize theme columns with NaN
            theme_df_copy = df.copy()
            for col in theme_df_copy.columns:
                if col not in preserve_cols:
                    theme_df_copy = theme_df_copy.rename(columns={col: f'{theme_name}_{col}'})
            
            # Map matched rows
            matched_data = {}
            for col in theme_df_copy.columns:
                if col not in preserve_cols:
                    matched_data[col] = [
                        theme_df_copy.iloc[indices[i]][col] if valid_matches[i] else None
                        for i in range(len(base))
                    ]
            
            # Add matched columns to base
            for col, values in matched_data.items():
                base[col] = values
            
            matched_count = valid_matches.sum()
            print(f"✓ Matched {matched_count}/{len(base)} points from {theme_name} theme")
        
        print(f"✓ Merged data: {len(base)} rows, {len(base.columns)} columns")
        return base
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create derived features from raw survey data."""
        
        # === Spatial Features ===
        df['coord_hash'] = df['longitude'].astype(str) + '_' + df['latitude'].astype(str)
        
        # Find village column
        village_col = next((c for c in df.columns if 'village' in c.lower() or c in ['_3', 'merge_key']), 'merge_key')
        
        # Village frequency (proxy for village size/sampling)
        if village_col in df.columns:
            village_counts = df[village_col].value_counts()
            df['village_sample_size'] = df[village_col].map(village_counts)
        else:
            df['village_sample_size'] = 1
        
        # === Water Features ===
        # Water scarcity months (convert to numeric)
        if 'water__8' in df.columns:  # Scarcity months
            df['water_scarcity_months'] = pd.to_numeric(df['water__8'], errors='coerce').fillna(0)
        
        # Water sufficiency encoding (ordinal)
        if 'water__7' in df.columns:
            water_suff_map = {
                'Always sufficient': 4,
                'Usually sufficient': 3,
                'Sometimes sufficient': 2,
                'Rarely sufficient': 1,
                'Never sufficient': 0
            }
            df['water_sufficiency_score'] = df['water__7'].map(water_suff_map).fillna(2)
        
        # === Energy Features ===
        # Energy diversity (count of energy sources used)
        energy_cols = [col for col in df.columns if 'energy_' in col and '%' in str(df[col].name)]
        if energy_cols:
            df['energy_diversity'] = df[energy_cols].notna().sum(axis=1)
        
        # Solar adoption (binary)
        if 'energy__10' in df.columns:  # % Solar
            df['has_solar'] = (pd.to_numeric(df['energy__10'], errors='coerce') > 0).astype(int)
        
        # Manual labor percentage (inverse of mechanization)
        if 'energy__5' in df.columns:
            df['manual_labor_pct'] = pd.to_numeric(df['energy__5'], errors='coerce').fillna(50)
        
        # === Food/Production Features ===
        # Crop diversity (count distinct crops mentioned)
        if 'food__3' in df.columns:  # Main crops
            df['crop_diversity'] = df['food__3'].str.split(',').str.len().fillna(1)
        
        # Production level encoding (ordinal)
        if 'food__5' in df.columns:
            prod_map = {'Small': 0, 'Medium': 1, 'Large': 2}
            df['production_level_score'] = df['food__5'].map(prod_map).fillna(1)
        
        # Animal husbandry (binary)
        if 'food__8' in df.columns:
            df['has_animals'] = df['food__8'].notna().astype(int)
        
        # === Farm Characteristics ===
        # Farm size encoding (ordinal)
        if 'general_info__3' in df.columns:
            size_map = {
                'أقل من 1 دونم': 0,
                '1-5 دونم': 1,
                '5-10 دونم': 2,
                '10-20 دونم': 3,
                'أكثر من 20 دونم': 4
            }
            df['farm_size_score'] = df['general_info__3'].map(size_map).fillna(1)
        
        # Climate change awareness (binary)
        if 'general_info__5' in df.columns:
            df['climate_aware'] = (df['general_info__5'].notna() & (df['general_info__5'] != 'No')).astype(int)
        
        # === Regenerative Agriculture Features ===
        # Technique diversity (count of regen techniques used)
        if 'regenerative_agriculture__3' in df.columns:
            df['regen_technique_count'] = df['regenerative_agriculture__3'].str.split(',').str.len().fillna(0)
        
        # Fertilizer/pesticide reliance scores
        reliance_map = {'Low': 0, 'Medium': 1, 'High': 2}
        if 'regenerative_agriculture__5' in df.columns:
            df['fertilizer_reliance_score'] = df['regenerative_agriculture__5'].map(reliance_map).fillna(1)
        if 'regenerative_agriculture__7' in df.columns:
            df['pesticide_reliance_score'] = df['regenerative_agriculture__7'].map(reliance_map).fillna(1)
        
        # Resource intensity composite (fertilizer + pesticide + manual labor)
        df['resource_intensity'] = (
            df.get('fertilizer_reliance_score', 1) +
            df.get('pesticide_reliance_score', 1) +
            (df.get('manual_labor_pct', 50) / 50)  # Normalize to 0-2
        ) / 3
        
        print(f"✓ Engineered {len([c for c in df.columns if c.endswith('_score') or c.endswith('_count')])} derived features")
        return df
    
    def create_target_variables(self, df: pd.DataFrame) -> pd.DataFrame:
        """Define target variables for each AI prediction layer."""
        
        # === Target 1: Regenerative Agriculture Adoption ===
        # Based on: presence of organic/regenerative practices
        # Data shows: _3 contains regenerative techniques, _5 shows fertilizer use
        if 'regenerative_agriculture__3' in df.columns:
            # Check for regenerative keywords
            df['has_regen_practice'] = df['regenerative_agriculture__3'].fillna('').str.contains(
                'Organic|compost|rotation|Biological|Cover crops|organic materials',
                case=False, na=False
            ).astype(int)
            
            # Low chemical fertilizer use (_5: "It is not used" or minimal)
            df['low_fertilizer'] = df.get('regenerative_agriculture__5', '').str.contains(
                'not used', case=False, na=False
            ).astype(int)
            
            # Target: Has regen practices OR low fertilizer use
            df['target_regen_adoption'] = (
                (df['has_regen_practice'] == 1) |
                (df['low_fertilizer'] == 1)
            ).astype(int)
        else:
            df['target_regen_adoption'] = 0
        
        # === Target 2: Water Risk ===
        # Based on: water scarcity mentions and sufficiency
        # Data shows: _8 contains scarcity months, _7 shows sufficiency level
        if 'water__7' in df.columns:
            # Water insufficiency (_7: ONLY "rarely" or "completely insufficient")
            df['water_insufficient'] = df['water__7'].fillna('').str.contains(
                'rarely|Completely insufficient',
                case=False, na=False
            ).astype(int)
            
            # Target: Severe water stress only (not "sometimes enough")
            df['target_water_risk'] = (df['water_insufficient'] == 1).astype(int)
        else:
            df['target_water_risk'] = 0
        
        # === Target 3: Economic Vulnerability ===
        # Based on: small farm + small production + chemical dependency
        # Data shows: general_info__3 has farm size, food__5 has production level
        if 'general_info__3' in df.columns and 'food__5' in df.columns:
            # Small farm (< 5000 m2 or < 10000 m2)
            df['small_farm'] = df['general_info__3'].fillna('').str.contains(
                'Less than|< 5000|< 10,000',
                case=False, na=False
            ).astype(int)
            
            # Small production
            df['small_production'] = df['food__5'].fillna('').str.contains(
                'Small production',
                case=False, na=False
            ).astype(int)
            
            # High chemical dependency (regenerative_agriculture__5: "Total dependence")
            df['high_chem_depend'] = df.get('regenerative_agriculture__5', '').str.contains(
                'Total dependence',
                case=False, na=False
            ).astype(int)
            
            # Target: Small farm + (Small production OR high chemical dependency)
            df['target_economic_vuln'] = (
                (df['small_farm'] == 1) &
                ((df['small_production'] == 1) | (df['high_chem_depend'] == 1))
            ).astype(int)
        else:
            df['target_economic_vuln'] = 0
        
        # === Target 4: Labor Shortage ===
        # Based on: manual labor percentage (energy__5) and farm size
        # Data shows: energy__5 contains % manual labor
        if 'energy__5' in df.columns:
            # High manual labor (>50%)
            manual_pct = pd.to_numeric(df['energy__5'], errors='coerce').fillna(0)
            df['high_manual_labor'] = (manual_pct >= 50).astype(int)
            
            # Medium/large farm (>10000 m2)
            df['medium_large_farm'] = df.get('general_info__3', '').str.contains(
                'More than 1 hectare|More than 2 hectare|>10,000|>20,000',
                case=False, na=False
            ).astype(int)
            
            # Target: High manual labor + medium/large farm (labor intensive)
            df['target_labor_shortage'] = (
                (df['high_manual_labor'] == 1) &
                (df['medium_large_farm'] == 1)
            ).astype(int)
        else:
            df['target_labor_shortage'] = 0
        
        # === Target 5: Climate Vulnerability ===
        # Based on: climate change awareness + impacts (no adaptation requirement)
        # Data shows: general_info__5 has climate observations, __6 has impacts
        if 'general_info__5' in df.columns:
            # Climate change observed (_5 has any value)
            df['climate_observed'] = df['general_info__5'].notna().astype(int)
            
            # Significant impacts (_6: mentions production decrease or pests)
            df['has_climate_impact'] = df.get('general_info__6', '').str.contains(
                'Decrease in production|decreased production|pests|diseases',
                case=False, na=False
            ).astype(int)
            
            # Target: Climate observed AND has impacts (removed adaptation filter)
            df['target_climate_vuln'] = (
                (df['climate_observed'] == 1) &
                (df['has_climate_impact'] == 1)
            ).astype(int)
        else:
            df['target_climate_vuln'] = 0
        
        # Report target distributions
        targets = [c for c in df.columns if c.startswith('target_')]
        print("\n=== Target Variable Distributions ===")
        for target in targets:
            pos_rate = df[target].mean() * 100
            pos_count = df[target].sum()
            neg_count = len(df) - pos_count
            print(f"{target}:")
            print(f"  Positive: {pos_count} ({pos_rate:.1f}%)")
            print(f"  Negative: {neg_count} ({100-pos_rate:.1f}%)")
        
        return df
    
    def encode_categorical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """One-hot encode categorical variables."""
        
        # Key categorical columns to encode
        categorical_cols = {
            'water__6': 'water_source',  # Water source
            'general_info__4': 'soil_type',  # Soil type
            'energy__3': 'energy_source',  # Primary energy source
        }
        
        encoded_dfs = [df]
        
        for col, prefix in categorical_cols.items():
            if col in df.columns:
                # Get top 5 categories (others become 'other')
                top_cats = df[col].value_counts().head(5).index
                df[col] = df[col].apply(lambda x: x if x in top_cats else 'other')
                
                # One-hot encode
                dummies = pd.get_dummies(df[col], prefix=prefix, drop_first=True)
                encoded_dfs.append(dummies)
                print(f"✓ One-hot encoded {col} into {len(dummies.columns)} features")
        
        result = pd.concat(encoded_dfs, axis=1)
        print(f"✓ Total features after encoding: {len(result.columns)}")
        return result
    
    def prepare_ml_dataset(self) -> Tuple[pd.DataFrame, List[str], List[str]]:
        """Complete pipeline: load → merge → engineer → encode."""
        
        print("\n=== Starting Feature Engineering Pipeline ===\n")
        
        # Step 1: Load data
        data = self.load_canonical_data()
        
        # Step 2: Merge themes
        df = self.merge_themes(data)
        
        # Step 3: Engineer features
        df = self.engineer_features(df)
        
        # Step 4: Create targets
        df = self.create_target_variables(df)
        
        # Step 5: Encode categoricals
        df = self.encode_categorical_features(df)
        
        # Step 6: Select feature columns (exclude metadata and targets)
        village_col = next((c for c in df.columns if 'village' in c.lower() or c in ['_3', 'merge_key']), 'merge_key')
        exclude_cols = ['feature_id', 'theme', 'coord_hash', village_col] + \
                       [c for c in df.columns if c.startswith('target_')]
        
        feature_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in ['int64', 'float64']]
        target_cols = [c for c in df.columns if c.startswith('target_')]
        
        # Handle missing values in features
        df[feature_cols] = df[feature_cols].fillna(df[feature_cols].median())
        
        print(f"\n✓ Final dataset: {len(df)} samples, {len(feature_cols)} features, {len(target_cols)} targets")
        
        self.features_df = df
        return df, feature_cols, target_cols
    
    def save_prepared_data(self, output_path: str = "data/ml_prepared_data.csv"):
        """Save prepared dataset to CSV."""
        if self.features_df is None:
            raise ValueError("No data prepared. Run prepare_ml_dataset() first.")
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        self.features_df.to_csv(output_file, index=False)
        print(f"\n✓ Saved prepared data to {output_file}")
        

if __name__ == "__main__":
    # Run feature engineering pipeline
    engineer = FeatureEngineer()
    df, features, targets = engineer.prepare_ml_dataset()
    engineer.save_prepared_data()
    
    print("\n=== Feature Engineering Complete ===")
    print(f"Dataset shape: {df.shape}")
    print(f"Features: {len(features)}")
    print(f"Targets: {len(targets)}")
