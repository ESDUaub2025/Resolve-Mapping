# Machine Learning Pipeline for Agricultural AI Layers

Complete ML pipeline for generating AI prediction heatmap layers from farmer survey data.

## Overview

This pipeline transforms raw survey data (287 farmer responses across 5 themes) into AI-powered prediction layers for:

- **Regenerative Agriculture Adoption** - Likelihood of farmers adopting sustainable practices
- **Water Risk** - Water scarcity and shortage vulnerability
- **Economic Vulnerability** - Economic resilience indicators
- **Labor Shortage** - Agricultural labor availability
- **Climate Vulnerability** - Climate change impact susceptibility

## Pipeline Architecture

```
Raw Data (CSV/GeoJSON) 
    ↓
Feature Engineering → ML-Ready Features (48+ properties)
    ↓
Model Training → 5 Trained Models (RandomForest/XGBoost)
    ↓
Spatial Interpolation → Regular Grid (~1000-2000 points)
    ↓
Output: AI_Grid_Predictions.geojson + Farmers_Boundary.geojson
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- pandas, numpy, scikit-learn
- xgboost (optional, RandomForest used as fallback)
- scipy (spatial interpolation)
- shapely (boundary generation)

### 2. Run Complete Pipeline

```bash
# From project root
cd scripts/ml_pipeline

# Run full pipeline (feature engineering → training → interpolation → boundary)
python run_pipeline.py
```

**Output files:**
- `data/ml_prepared_data.csv` - Engineered features dataset
- `data/models/*.joblib` - 5 trained model files
- `data/models/training_report.txt` - Model performance metrics
- `data/geojson/AI_Grid_Predictions.geojson` - Grid heatmap data
- `data/geojson/Farmers_Boundary.geojson` - Survey area boundary

### 3. View Results

Refresh the browser at `http://localhost:8000/` - AI layer checkboxes in sidebar will now be functional.

## Pipeline Modules

### Module 1: Feature Engineering (`feature_engineering.py`)

**Input:** Canonical GeoJSON files (Water, Energy, Food, General_Info, Regenerative_Agriculture)

**Process:**
- Loads 287 survey responses with 48 properties
- Merges themes on village name
- Engineers derived features:
  - Water scarcity score (0-12 months)
  - Energy diversity index
  - Crop diversity count
  - Farm size ordinal encoding
  - Resource intensity composite score
- Creates 5 target variables (binary classification)
- One-hot encodes categoricals (water source, soil type, energy source)

**Output:** `data/ml_prepared_data.csv` (~60 features, 287 rows)

**Run standalone:**
```bash
python feature_engineering.py
```

### Module 2: Model Training (`train_models.py`)

**Input:** Prepared dataset from feature engineering

**Process:**
- Trains 5 binary classifiers (one per prediction target)
- Uses RandomForest (default) or XGBoost
- Spatial cross-validation (leave-one-village-out)
- Hyperparameters optimized for small dataset (n=287)
- Handles class imbalance with `class_weight='balanced'`
- Generates feature importance rankings

**Validation Strategy:**
- **Spatial CV** prevents overfitting due to geographic clustering
- **F1-score** primary metric (handles imbalanced classes)
- **ROC-AUC** for probability calibration

**Output:** 
- `data/models/target_*_model.joblib` - 5 model files
- `data/models/training_report.txt` - Performance report
- `data/models/training_metrics.json` - Machine-readable metrics

**Run standalone:**
```bash
# RandomForest (default)
python train_models.py

# XGBoost
python train_models.py xgboost

# Logistic Regression
python train_models.py logistic
```

### Module 3: Spatial Interpolation (`interpolate_grid.py`)

**Input:** Trained models + prepared dataset

**Process:**
- Predicts probabilities at 287 survey point locations
- Generates regular grid covering study area (35.40-35.70°E, 33.58-33.80°N)
- Interpolates point predictions to grid using:
  - **Linear interpolation** for smooth gradients
  - **Distance-based weighting** reduces confidence far from survey points
  - **Spatial smoothing** reduces noise
- Exports 5 probability fields (Prob_Regen, Prob_Water, Prob_Econ, Prob_Labor, Prob_Climate)

**Grid Resolution:**
- Default: `0.005°` ≈ 500m spacing → ~1500 grid points
- Fine: `0.002°` ≈ 200m spacing → ~9000 grid points (slower, larger file)
- Coarse: `0.01°` ≈ 1km spacing → ~400 grid points (faster, less detail)

**Output:** `data/geojson/AI_Grid_Predictions.geojson` (50-500KB depending on resolution)

**Run standalone:**
```bash
# Default resolution (500m)
python interpolate_grid.py

# Fine resolution (200m)
python interpolate_grid.py 0.002

# Coarse resolution (1km)
python interpolate_grid.py 0.01
```

### Module 4: Boundary Generation (`generate_boundary.py`)

**Input:** Survey point coordinates

**Process:**
- Computes geographic boundary from 287 survey points
- **Convex hull** (default) - Simple bounding polygon
- **Alpha shape** (optional) - Tighter boundary excluding interior gaps

**Output:** `data/geojson/Farmers_Boundary.geojson`

**Run standalone:**
```bash
# Convex hull (simpler)
python generate_boundary.py

# Alpha shape (tighter boundary)
python generate_boundary.py alpha_shape 0.05
```

## Advanced Usage

### Run Specific Pipeline Stages

```bash
# Feature engineering only
python run_pipeline.py --features-only

# Training only (requires prepared data)
python run_pipeline.py --train-only --model xgboost

# Interpolation only (requires trained models)
python run_pipeline.py --interpolate-only --resolution 0.01
```

### Customize Model & Grid Parameters

```bash
# Use XGBoost with fine grid
python run_pipeline.py --model xgboost --resolution 0.002

# RandomForest with coarse grid (fastest)
python run_pipeline.py --model random_forest --resolution 0.01

# Alpha shape boundary
python run_pipeline.py --boundary alpha_shape
```

## Data Pipeline Flow

### Input Data Sources

**Canonical GeoJSON** (`data/geojson/canonical/`):
- `Water.canonical.geojson` - 57 responses (irrigation, water sources, scarcity)
- `Energy.canonical.geojson` - 59 responses (energy mix, consumption, solar adoption)
- `Food.canonical.geojson` - 58 responses (crops, production, livestock)
- `General_Info.canonical.geojson` - 58 responses (farm size, soil, climate awareness)
- `Regenerative_Agriculture.canonical.geojson` - 55 responses (techniques, chemical reliance)

**Total:** 287 farmer survey responses, 48 unique properties, bilingual (Arabic/English)

### Feature Engineering Details

**Spatial Features:**
- Latitude, longitude (WGS84)
- Village clustering (sample size per village)

**Water Features:**
- Water scarcity months (numeric 0-12)
- Water sufficiency score (ordinal 0-4)

**Energy Features:**
- Energy diversity (count of sources)
- Solar adoption (binary)
- Manual labor percentage (0-100)

**Production Features:**
- Crop diversity (count)
- Production level (ordinal 0-2)
- Animal husbandry (binary)

**Farm Characteristics:**
- Farm size score (ordinal 0-4)
- Climate awareness (binary)

**Regenerative Agriculture:**
- Technique count (0-10+)
- Fertilizer reliance (0-2)
- Pesticide reliance (0-2)
- Resource intensity (composite 0-3)

**Categorical Encodings:**
- Water source (one-hot, 5 categories)
- Soil type (one-hot, 5 categories)
- Energy source (one-hot, 5 categories)

### Target Variable Definitions

| Target | Definition | Positive Class Criteria |
|--------|------------|------------------------|
| **target_regen_adoption** | Current regenerative practices | ≥2 regen techniques AND low fertilizer/pesticide use |
| **target_water_risk** | Water shortage vulnerability | ≥3 scarcity months OR low sufficiency score |
| **target_economic_vuln** | Economic vulnerability | Small farm + low production + high resource intensity |
| **target_labor_shortage** | Labor shortage indicator | High manual labor % on medium/large farm |
| **target_climate_vuln** | Climate vulnerability | Climate aware + water risk + no regen adoption |

**Note:** Targets are derived from survey data, not external ground truth. Validation shows these are reasonable proxies but should be refined with longitudinal data.

## Model Performance

### Expected Accuracy Ranges

Based on training with 287 samples:

| Model | Accuracy | F1-Score | Notes |
|-------|----------|----------|-------|
| ai-regen | 60-70% | 0.55-0.65 | Limited positive samples (~15%) |
| ai-water | 75-85% | 0.70-0.80 | Strongest predictor (clear signal) |
| ai-econ | 65-75% | 0.60-0.70 | Requires additional features |
| ai-labor | 60-70% | 0.55-0.65 | Proxy target (no direct survey question) |
| ai-climate | 70-80% | 0.65-0.75 | Multi-factor composite |

**Stated UI accuracies (61-98%) are aspirational targets.** Actual cross-validated performance will be lower due to small sample size and spatial correlation.

### Validation Strategy

- **Spatial Cross-Validation** (leave-one-village-out) prevents overfitting
- **5-fold CV** when ≥5 villages in positive class
- **F1-score** as primary metric (handles class imbalance)
- **Feature importance** validates stated prediction factors

## Limitations & Future Work

### Current Limitations

1. **Small Sample Size** (287 responses)
   - Risk of overfitting
   - Limited geographic coverage
   - Some villages underrepresented

2. **Single Time Point**
   - No temporal validation
   - Cannot model seasonal variations
   - Predictions are static

3. **Proxy Targets**
   - Economic vulnerability: missing "Marketing Challenges", "Coop Member" properties
   - Labor shortage: missing "Main Workers", "Machinery" properties
   - Targets defined from survey, not external validation data

4. **Spatial Interpolation Uncertainty**
   - Predictions far from survey points have high uncertainty
   - Distance-based weighting attempts to quantify this
   - Edge effects at study area boundaries

### Recommendations for Improvement

**Phase 1: Data Expansion (Priority High)**
- [ ] Collect additional survey responses (target: 500-1000 samples)
- [ ] Add missing properties (marketing challenges, cooperative membership, labor details)
- [ ] Multi-season data collection (track changes over time)

**Phase 2: External Validation (Priority High)**
- [ ] Link predictions to ground truth outcomes (e.g., actual regen adoption verified by field visits)
- [ ] Integrate external data: weather stations, market prices, policy changes
- [ ] Validate spatial interpolation with holdout villages

**Phase 3: Advanced Analytics (Priority Medium)**
- [ ] Causal inference: Does solar → reduced water stress? Does regen → economic resilience?
- [ ] Network analysis: Crop-village associations, farmer typology clusters
- [ ] Anomaly detection: Identify outlier farms for case studies
- [ ] Time-series forecasting: Project trends forward 5-10 years

**Phase 4: Interactive Tools (Priority Low)**
- [ ] What-if scenario modeling in UI (e.g., "Show impact of 50% fertilizer reduction")
- [ ] Uncertainty visualization (confidence intervals on predictions)
- [ ] Multi-objective optimization (maximize regen + economic + climate resilience)

## Troubleshooting

### Pipeline Fails at Feature Engineering

**Error:** `FileNotFoundError: data/geojson/canonical/Water.canonical.geojson not found`

**Solution:** Ensure canonical GeoJSON files exist. Regenerate with:
```bash
cd scripts
python generate_canonical_geojson.py
```

### Low Model Performance (F1 < 0.4)

**Possible causes:**
- Insufficient positive samples in target (check class balance)
- Target definition too strict or too loose
- Missing critical features

**Solutions:**
- Adjust target definition criteria in `feature_engineering.py`
- Collect more survey data
- Try simpler models (logistic regression)

### Grid File Too Large (>5MB)

**Cause:** High grid resolution

**Solution:** Use coarser grid:
```bash
python run_pipeline.py --resolution 0.01  # 1km spacing
```

### XGBoost Not Found

**Cause:** XGBoost not installed

**Solution:** Install or use RandomForest:
```bash
pip install xgboost
# OR
python run_pipeline.py --model random_forest
```

### Shapely Not Found (Boundary Generation)

**Cause:** Shapely not installed

**Solution:** Falls back to scipy ConvexHull automatically
```bash
pip install shapely  # Optional
```

## File Structure

```
scripts/ml_pipeline/
├── __init__.py                  # Package init
├── feature_engineering.py       # Data preparation
├── train_models.py              # Model training
├── interpolate_grid.py          # Spatial interpolation
├── generate_boundary.py         # Boundary generation
├── run_pipeline.py              # Orchestrator
└── README.md                    # This file

data/
├── ml_prepared_data.csv         # Engineered features (generated)
├── models/                      # Trained models (generated)
│   ├── target_*_model.joblib
│   ├── training_metrics.json
│   ├── training_report.txt
│   └── feature_list.json
└── geojson/
    ├── AI_Grid_Predictions.geojson      # Grid heatmap (generated)
    ├── Farmers_Boundary.geojson         # Boundary polygon (generated)
    └── canonical/                       # Input data
        ├── Water.canonical.geojson
        ├── Energy.canonical.geojson
        ├── Food.canonical.geojson
        ├── General_Info.canonical.geojson
        └── Regenerative_Agriculture.canonical.geojson
```

## Contact & Support

For questions about the ML pipeline:
1. Review `data/models/training_report.txt` for model diagnostics
2. Check `training_metrics.json` for detailed performance metrics
3. Inspect feature importance rankings to understand predictions

## License

Part of the Mount Lebanon Agricultural Mapping project.
