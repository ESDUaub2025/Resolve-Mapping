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
    
    # Column normalization: map new-style canonical keys → old-style keys
    # so the rest of the pipeline (which references old-style) works uniformly.
    COLUMN_NORMALIZATION = {
        'water': {
            '4. Village': 'القرية',
            '10. Main Crops': 'المحصول',
            '13. Water Source': '_6',
            '16. Water Availability': '_7',
            '17. Water Scarcity Months': '_8',
            '18. Change in Irrigation Needs': '_5',
        },
        'energy': {
            '4. Village': 'القرية',
            '14. Energy Source': '_3',
            '15. Energy Consumption': '_4',
        },
        'food': {
            '4. Village': 'القرية',
            '19. Food Production Level': '_5',
            '20. Coop Member?': '_6',
            '24. % Village Participation': '_7',
        },
        'general_info': {
            '4. Village': 'القرية',
            '5. Own Farmland?': '_2',
            '8. Land Size': '_3',
            '9. Soil Type': '_4',
            '52. Climate Change Noticed?': '_5a',
            '53. Climate Changes': '_5',
            '54. Impact on Production': '_6',
        },
        'regenerative_agriculture': {
            '4. Village': 'القرية',
            '34. Seed Selection Criteria': '_2',
            '35. Seed Source': '_2a',
            '36. Seed Challenges': '_2b',
            '38. Soil Enhancers': '_4',
            '39. Chem Fertilizer Reliance': '_5',
            '43. Pest Control Method': '_6',
            '44. Pesticide Reliance': '_7',
            '63. Raise Poultry?': '_8',
        },
    }
    
    def __init__(self, data_dir: str = "data/geojson/canonical"):
        self.data_dir = Path(data_dir)
        self.features_df = None
    
    def _normalize_columns(self, record: dict, theme: str) -> dict:
        """Normalize new-style column names to old-style for pipeline compatibility."""
        mapping = self.COLUMN_NORMALIZATION.get(theme, {})
        normalized = {}
        for key, value in record.items():
            if key in mapping:
                normalized[mapping[key]] = value
            else:
                normalized[key] = value
        return normalized
        
    def load_canonical_data(self) -> Dict[str, pd.DataFrame]:
        """Load all canonical GeoJSON files into DataFrames (including new Beqaa data)."""
        themes = ['Water', 'Energy', 'Food', 'General_Info', 'Regenerative_Agriculture']
        data = {}
        
        for theme in themes:
            # Load original data
            filepath = self.data_dir / f"{theme}.canonical.geojson"
            # Load new Beqaa Valley data
            filepath_new = self.data_dir / f"{theme}_new.canonical.geojson"
            
            all_records = []
            
            # Process original file
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    geojson = json.load(f)
                
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
                        'data_source': 'original',
                        **values  # Unpack all English property values
                    }
                    all_records.append(record)
                print(f"✓ Loaded {len(all_records)} records from {theme} (original)")
            else:
                print(f"Warning: {filepath} not found")
            
            # Process new Beqaa data file (if exists)
            if filepath_new.exists():
                with open(filepath_new, 'r', encoding='utf-8') as f:
                    geojson_new = json.load(f)
                
                new_count = 0
                for feature in geojson_new['features']:
                    props = feature['properties']
                    coords = feature['geometry']['coordinates']
                    
                    # Get English values
                    values = props.get('values', {}).get('en', {})
                    
                    record = {
                        'feature_id': props.get('featureId'),
                        'theme': props.get('theme'),
                        'longitude': coords[0],
                        'latitude': coords[1],
                        'data_source': 'beqaa_2026',
                        **values  # Unpack all English property values
                    }
                    # Normalize new-style key names to old-style for pipeline compat
                    record = self._normalize_columns(record, theme.lower())
                    all_records.append(record)
                    new_count += 1
                print(f"✓ Loaded {new_count} records from {theme}_new (Beqaa Valley 2026)")
            
            data[theme.lower()] = pd.DataFrame(all_records)
            print(f"  Total {theme}: {len(all_records)} records")
        
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
    
    # Features that must be EXCLUDED when predicting a specific target
    # to prevent data leakage (feature derived from same column as target).
    CIRCULAR_FEATURES = {
        'target_regen_adoption': ['regen_technique_count'],
        'target_economic_vuln': ['small_farm', 'small_production'],
    }

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create derived features from raw survey data.

        All ordinal maps validated against actual canonical GeoJSON values
        (both original Mount Lebanon + Beqaa Valley 2026 surveys).
        """

        # === Spatial Features ===
        df['coord_hash'] = df['longitude'].astype(str) + '_' + df['latitude'].astype(str)

        # Village frequency (proxy for village size / sampling density)
        village_col = next(
            (c for c in df.columns if 'village' in c.lower() or c == 'water_القرية'),
            None,
        )
        if village_col and village_col in df.columns:
            df['village_sample_size'] = df[village_col].map(df[village_col].value_counts())
        else:
            df['village_sample_size'] = 1

        # === Water Features ===
        # Water sufficiency (ordinal) — actual values from canonical data
        if 'water__7' in df.columns:
            def _map_water_sufficiency(val):
                if pd.isna(val):
                    return np.nan
                v = str(val).lower().strip()
                if v in ('always enough', 'always'):
                    return 4
                if 'sometimes' in v:
                    return 2
                if 'rarely' in v:
                    return 1
                if 'insufficient' in v or 'completely' in v or 'totally' in v:
                    return 0
                return np.nan
            df['water_sufficiency_score'] = df['water__7'].apply(_map_water_sufficiency).fillna(2)

        # Water scarcity months — count month names in free-text field
        # Actual values: "August September July", "July-Aug", "No", etc.
        if 'water__8' in df.columns:
            _MONTH_TOKENS = {
                'jan', 'feb', 'mar', 'apr', 'may', 'jun',
                'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
                'january', 'february', 'march', 'april', 'june',
                'july', 'august', 'september', 'october', 'november', 'december',
                'summer',  # counts as 3 months (jun-aug)
            }
            def _count_scarcity_months(val):
                if pd.isna(val):
                    return 0
                v = str(val).lower().strip()
                if v in ('no', 'none', '', 'n/a'):
                    return 0
                if 'summer' in v:
                    return 3  # June-August
                if 'all year' in v:
                    return 12
                # Tokenize and match month names
                tokens = set()
                for word in v.replace('-', ' ').replace(',', ' ').split():
                    w = word.strip().lower()
                    if w[:3] in ('jan', 'feb', 'mar', 'apr', 'may', 'jun',
                                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'):
                        tokens.add(w[:3])
                return max(len(tokens), 1) if tokens else 0
            df['water_scarcity_months'] = df['water__8'].apply(_count_scarcity_months)

        # === Energy Features ===
        # Manual labor percentage (numeric %)
        if 'energy__5' in df.columns:
            df['manual_labor_pct'] = pd.to_numeric(df['energy__5'], errors='coerce').fillna(50)

        # Solar adoption (binary — has any solar %)
        if 'energy__10' in df.columns:
            df['has_solar'] = (pd.to_numeric(df['energy__10'], errors='coerce') > 0).astype(int)

        # Energy source diversity (count sources separated by / or comma)
        if 'energy__3' in df.columns:
            df['energy_source_count'] = df['energy__3'].fillna('').apply(
                lambda v: max(1, len([s for s in str(v).replace('/', ',').split(',') if s.strip()]))
            )
            df['uses_renewable'] = df['energy__3'].fillna('').str.contains(
                'Solar|solar|renewable', case=False, na=False
            ).astype(int)

        # === Food / Production Features ===
        # Crop diversity (count distinct crops)
        crop_col = next(
            (c for c in ('water_المحصول', 'food__3') if c in df.columns), None
        )
        if crop_col:
            df['crop_diversity'] = df[crop_col].fillna('').str.split(r'[,،]').apply(
                lambda parts: max(1, len([p for p in parts if p.strip()]))
            )
        else:
            df['crop_diversity'] = 1

        # Production level (ordinal) — check highest category mentioned
        # Actual values: "Small production", "Average production", "Great production",
        # "Small (Home use)", "Medium (Local sale)", "Large (Markets)",
        # multi-value: "Small production medium production", etc.
        if 'food__5' in df.columns:
            def _map_production(val):
                if pd.isna(val):
                    return np.nan
                v = str(val).lower()
                if 'great' in v or 'large' in v:
                    return 2
                if 'average' in v or 'medium' in v:
                    return 1
                if 'small' in v:
                    return 0
                return np.nan
            df['production_level_score'] = df['food__5'].apply(_map_production).fillna(1)

        # Animal husbandry (binary)
        if 'food__8' in df.columns:
            df['has_animals'] = df['food__8'].notna().astype(int)

        # Coop membership (binary)
        if 'food__6' in df.columns:
            df['coop_member'] = df['food__6'].fillna('').str.contains(
                'Yes', case=False, na=False
            ).astype(int)

        # === Farm Characteristics ===
        # Farm size (ordinal) — actual values from both datasets
        # Old: "Less than 5 dunums (<5000 m²)", "More than 1 hectare (>10,000 m2)", etc.
        # New: "< 1 Hectare", "> 1 Hectare", "> 2 Hectares", "< 5 Dunums"
        if 'general_info__3' in df.columns:
            def _map_farm_size(val):
                if pd.isna(val):
                    return np.nan
                v = str(val).lower()
                if '2 hectare' in v or '> 2' in v or 'more than 2' in v:
                    return 3
                if '1 hectare' in v or '> 1' in v or 'more than 1' in v:
                    return 2
                if '< 1 hectare' in v or 'less than 1' in v:
                    return 1
                if 'dunum' in v or '< 5' in v or 'less than 5' in v:
                    return 0
                return np.nan
            df['farm_size_score'] = df['general_info__3'].apply(_map_farm_size).fillna(1)

        # Climate impact severity (count of distinct impact categories mentioned)
        # Actual values: "Decrease in production, delay in agricultural seasons,
        #   increase in pests and diseases, difficulties in pollination..."
        if 'general_info__6' in df.columns:
            def _count_climate_impacts(val):
                if pd.isna(val):
                    return 0
                v = str(val).lower()
                if 'no' in v and any(w in v for w in ('significant', 'major', 'big')):
                    return 0
                impacts = 0
                if any(w in v for w in ('decrease', 'low production', 'reduced')):
                    impacts += 1
                if any(w in v for w in ('delay', 'season')):
                    impacts += 1
                if any(w in v for w in ('pest', 'disease')):
                    impacts += 1
                if any(w in v for w in ('pollination', 'fruiting')):
                    impacts += 1
                return impacts
            df['climate_impact_count'] = df['general_info__6'].apply(_count_climate_impacts)

        # Soil quality proxy (loamy > clay > sandy for agriculture)
        if 'general_info__4' in df.columns:
            def _map_soil_quality(val):
                if pd.isna(val):
                    return np.nan
                v = str(val).lower()
                if 'loam' in v:
                    return 2
                if 'clay' in v:
                    return 1
                if 'sand' in v or 'رمل' in v:
                    return 0
                if 'calcareous' in v:
                    return 1
                return np.nan
            df['soil_quality_score'] = df['general_info__4'].apply(_map_soil_quality).fillna(1)

        # === Regenerative Agriculture Features ===
        # Fertilizer reliance (ordinal) — actual values:
        # "Partial"/"Partial credit" → 1,  "Total" → 2,
        # "It is not used"/"Not used" → 0
        if 'regenerative_agriculture__5' in df.columns:
            def _map_fertilizer(val):
                if pd.isna(val):
                    return np.nan
                v = str(val).lower()
                if 'not used' in v:
                    return 0
                if 'partial' in v:
                    return 1
                if 'total' in v:
                    return 2
                return np.nan
            df['fertilizer_reliance_score'] = df['regenerative_agriculture__5'].apply(_map_fertilizer).fillna(1)

        # Pesticide reliance (ordinal) — actual values:
        # "Partial"/"Partial credit" → 1,  "Total"/"Total dependence" → 2,
        # "It is not used" → 0
        if 'regenerative_agriculture__7' in df.columns:
            def _map_pesticide(val):
                if pd.isna(val):
                    return np.nan
                v = str(val).lower()
                if 'not used' in v:
                    return 0
                if 'partial' in v:
                    return 1
                if 'total' in v:
                    return 2
                return np.nan
            df['pesticide_reliance_score'] = df['regenerative_agriculture__7'].apply(_map_pesticide).fillna(1)

        # Chemical input intensity (composite: mean of fertilizer + pesticide)
        fert = df.get('fertilizer_reliance_score', pd.Series(1, index=df.index))
        pest = df.get('pesticide_reliance_score', pd.Series(1, index=df.index))
        df['chemical_input_intensity'] = (fert + pest) / 2

        # Soil enhancement diversity
        if 'regenerative_agriculture__4' in df.columns:
            df['soil_enhancer_diversity'] = df['regenerative_agriculture__4'].fillna('').apply(
                lambda v: max(1, len([s for s in str(v).replace('/', ',').split(',') if s.strip()])) if v else 0
            )
            df['uses_organic_enhancer'] = df['regenerative_agriculture__4'].fillna('').str.contains(
                'Compost|Manure|Bio|organic|compost|manure',
                case=False, na=False,
            ).astype(int)

        # Biological/physical pest control (vs pure chemical)
        if 'regenerative_agriculture__6' in df.columns:
            df['uses_bio_pest_control'] = df['regenerative_agriculture__6'].fillna('').str.contains(
                'Bio|biological|Local|local|Physical|physical',
                case=False, na=False,
            ).astype(int)

        # Regen technique count — kept for descriptive use but EXCLUDED
        # from regen_adoption model (circular: same source column as target)
        if 'regenerative_agriculture__3' in df.columns:
            df['regen_technique_count'] = df['regenerative_agriculture__3'].fillna('').apply(
                lambda v: len([t for t in str(v).replace('|', ',').split(',') if t.strip()]) if v else 0
            )
            df.loc[df['regenerative_agriculture__3'].isna(), 'regen_technique_count'] = 0

        # Resource intensity composite (fertilizer + pesticide + manual_labor)
        manual = df.get('manual_labor_pct', pd.Series(50, index=df.index))
        df['resource_intensity'] = (fert + pest + (manual / 100)) / 3

        engineered = [c for c in df.columns
                      if c.endswith(('_score', '_count', '_pct', '_intensity'))]
        print(f"✓ Engineered {len(engineered)} derived features")
        return df
    
    def create_target_variables(self, df: pd.DataFrame) -> pd.DataFrame:
        """Define target variables for each AI prediction layer.

        Each target is a binary indicator derived from survey responses.
        Targets validated against actual data distributions (84 samples).
        """

        # === Target 1: Regenerative Agriculture Adoption ===
        # Positive: mentions specific high-value regenerative practices
        # Actual data: most responses mention "Organic", "compost", "rotation", etc.
        if 'regenerative_agriculture__3' in df.columns:
            df['target_regen_adoption'] = df['regenerative_agriculture__3'].fillna('').str.contains(
                'Organic|compost|rotation|Biological|Cover crops|organic materials',
                case=False, na=False
            ).astype(int)
        else:
            df['target_regen_adoption'] = 0

        # === Target 2: Water Risk ===
        # Positive: water insufficiency reported
        # Actual values: "It rarely is", "Completely insufficient",
        #   "Rarely enough", "Totally insufficient"
        if 'water__7' in df.columns:
            df['target_water_risk'] = df['water__7'].fillna('').str.contains(
                'rarely|insufficient|totally',
                case=False, na=False
            ).astype(int)
        else:
            df['target_water_risk'] = 0

        # === Target 3: Economic Vulnerability ===
        # Positive: small farm AND small production level
        # Intermediate columns kept for analysis but excluded from this target's model
        if 'general_info__3' in df.columns and 'food__5' in df.columns:
            df['small_farm'] = df['general_info__3'].fillna('').apply(
                lambda v: 1 if any(w in str(v).lower() for w in ('less than', '< 1', '< 5', 'dunum')) else 0
            )
            df['small_production'] = df['food__5'].fillna('').apply(
                lambda v: 1 if 'small' in str(v).lower() else 0
            )
            df['target_economic_vuln'] = (
                (df['small_farm'] == 1) & (df['small_production'] == 1)
            ).astype(int)
        else:
            df['target_economic_vuln'] = 0

        # === Target 4: Labor Shortage ===
        # Positive: high manual labor (>=50%) on medium/large farms
        if 'energy__5' in df.columns:
            manual_pct = pd.to_numeric(df['energy__5'], errors='coerce').fillna(0)
            df['high_manual_labor'] = (manual_pct >= 50).astype(int)
            df['medium_large_farm'] = df.get('general_info__3', pd.Series('', index=df.index)).fillna('').apply(
                lambda v: 1 if any(w in str(v).lower() for w in ('more than 1', 'more than 2', '> 1', '> 2')) else 0
            )
            df['target_labor_shortage'] = (
                (df['high_manual_labor'] == 1) & (df['medium_large_farm'] == 1)
            ).astype(int)
        else:
            df['target_labor_shortage'] = 0

        # === Target 5: Climate Vulnerability ===
        # Positive: climate impacts observed on production
        # Actual values: "Decrease in production", "pests and diseases",
        #   "delay in agricultural seasons", "difficulties in pollination"
        if 'general_info__6' in df.columns:
            df['target_climate_vuln'] = df['general_info__6'].fillna('').str.contains(
                'decrease|decreased|low production|reduced|pest|disease',
                case=False, na=False
            ).astype(int)
        else:
            df['target_climate_vuln'] = 0

        # Report target distributions
        targets = [c for c in df.columns if c.startswith('target_')]
        print("\n=== Target Variable Distributions ===")
        for target in targets:
            pos_count = int(df[target].sum())
            neg_count = len(df) - pos_count
            pos_rate = df[target].mean() * 100
            print(f"  {target}: {pos_count} positive ({pos_rate:.1f}%), {neg_count} negative")

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
        """Complete pipeline: load → merge → engineer → encode.

        Returns (df, feature_cols, target_cols).
        Use get_features_for_target(target, feature_cols) to get non-circular
        feature list for a specific target.
        """

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

        # Step 6: Select feature columns (exclude metadata, targets, and
        #         intermediate target-definition columns)
        intermediate_cols = {'small_farm', 'small_production', 'high_manual_labor', 'medium_large_farm'}
        exclude_cols = {'feature_id', 'theme', 'coord_hash', 'data_source',
                        'water_data_source', 'energy_data_source',
                        'food_data_source', 'general_info_data_source',
                        'regenerative_agriculture_data_source'}
        exclude_cols |= intermediate_cols
        exclude_cols |= {c for c in df.columns if c.startswith('target_')}

        # Only keep village-type columns as identifiers, not features
        village_cols = {c for c in df.columns if 'القرية' in c or 'village' in c.lower()}
        exclude_cols |= village_cols

        # Only include numeric columns
        feature_cols = [c for c in df.columns
                        if c not in exclude_cols
                        and df[c].dtype in ('int64', 'float64', 'int32', 'float32')]
        target_cols = [c for c in df.columns if c.startswith('target_')]

        # Handle missing values in features
        df[feature_cols] = df[feature_cols].fillna(df[feature_cols].median())

        # Report feature variance — warn about constant features
        constant_feats = [c for c in feature_cols if df[c].nunique() <= 1]
        if constant_feats:
            print(f"\n⚠️  {len(constant_feats)} constant features (will be dropped): {constant_feats}")
            feature_cols = [c for c in feature_cols if c not in constant_feats]

        print(f"\n✓ Final dataset: {len(df)} samples, {len(feature_cols)} features, {len(target_cols)} targets")
        print(f"  Features: {feature_cols}")

        self.features_df = df
        self.feature_cols = feature_cols
        self.target_cols = target_cols
        return df, feature_cols, target_cols

    def get_features_for_target(self, target: str, feature_cols: List[str]) -> List[str]:
        """Return feature list with circular features excluded for a target."""
        excluded = set(self.CIRCULAR_FEATURES.get(target, []))
        filtered = [f for f in feature_cols if f not in excluded]
        if excluded & set(feature_cols):
            print(f"  ↳ Excluded circular features for {target}: {excluded & set(feature_cols)}")
        return filtered
    
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
