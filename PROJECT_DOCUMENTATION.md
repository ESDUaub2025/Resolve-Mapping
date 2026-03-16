# ResolveMap - Agricultural Data Mapping Platform
## Lebanon Agricultural Resource & Production Mapping System

**Version:** 2.2.0  
**Last Updated:** February 17, 2026  
**Coverage:** Mount Lebanon, Chouf District & Bekaa Valley  
**Total Features:** 432 farmer survey responses across 5 thematic data layers

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Data Structure](#data-structure)
4. [Features & Capabilities](#features--capabilities)
5. [Technology Stack](#technology-stack)
6. [File Structure](#file-structure)
7. [Data Pipeline](#data-pipeline)
8. [Deployment](#deployment)
9. [Usage Guide](#usage-guide)
10. [Development](#development)
11. [Maintenance](#maintenance)

---

## Project Overview

### Purpose
Interactive web-based mapping platform visualizing agricultural data from farmer surveys across Lebanon. Designed to support agricultural planning, resource management, and policy decisions through geospatial analysis of water-energy-food nexus data.

### Geographic Coverage
- **Mount Lebanon & Chouf District:** 287 original survey responses
- **Bekaa Valley:** 145 additional survey responses (29 farmers × 5 themes)
- **Total Coverage:** 432 features across 38+ villages

### Key Statistics
```
📊 Data Summary:
   • Total Survey Responses: 29 farmers
   • Data Points (5 themes): 432 features
   • Villages Covered: 38+
   • Survey Questions: 200+ per response
   • Property Mappings: 89 bilingual labels
   • Languages: Arabic (primary) + English (transliteration)
```

---

## System Architecture

### Design Philosophy
**Static-First, Browser-Based, No Backend**

```
┌─────────────────────────────────────────────────────────────┐
│                    USER'S BROWSER                            │
├─────────────────────────────────────────────────────────────┤
│  HTML/CSS/JS (Static Files)                                 │
│    ↓                                                         │
│  MapLibre GL (3.6.2) - Map Rendering                        │
│    ↓                                                         │
│  IndexedDB - Client-Side Caching (7-day TTL)                │
│    ↓                                                         │
│  Fetch API - Load GeoJSON from GitHub Pages/CDN            │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│              DATA SOURCES (Static Files)                     │
├─────────────────────────────────────────────────────────────┤
│  • Canonical Bilingual GeoJSON Files                        │
│  • AI/ML Prediction Layers                                  │
│  • Fire Data Layer                                          │
│  • Preservation Boundaries                                  │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. **Frontend Application** (`app.js` - 3,216 lines)
- Map initialization and control
- Layer management (clustering, styling, interaction)
- User interface (sidebar, details panel, filters)
- Language switching (Arabic ↔ English with RTL support)
- Event handling (clicks, hovers, toggles)

#### 2. **Modular Data Layer** (`app/modules/`)
```
app/modules/
├── data/
│   └── loader.js          # IndexedDB caching, GeoJSON loading
├── state/
│   └── store.js           # Immutable state management
├── i18n/
│   └── property-schemas.js # 89 bilingual property mappings
└── filters/
    └── filter-engine.js   # Dynamic filtering (planned)
```

#### 3. **Data Processing Pipeline** (`scripts/`)
- CSV → Canonical GeoJSON conversion
- Bilingual data merging (Arabic + English row-aligned)
- Coordinate validation and staggering
- ML feature engineering and prediction
- Data integrity auditing

---

## Data Structure

### Canonical Bilingual Architecture

**Single File Per Theme** - Language as presentation layer, not data duplication

```json
{
  "type": "FeatureCollection",
  "features": [{
    "id": "Water_2_a3f8b9c1",
    "type": "Feature",
    "geometry": {
      "type": "Point",
      "coordinates": [35.5123, 33.7456]
    },
    "properties": {
      "featureId": "Water_2_a3f8b9c1",
      "theme": "water",
      "values": {
        "ar": {
          "القرية": "مروستي",
          "المحصول": "تفاح",
          "مصدر المياه": "بئر جوفي"
        },
        "en": {
          "القرية": "Mrosti",
          "المحصول": "Apple",
          "مصدر المياه": "Underground Well"
        }
      }
    }
  }]
}
```

**Key Features:**
- **Stable Feature IDs:** `{theme}_{row}_{coordinateHash8}` (reproducible, non-colliding)
- **Bilingual Properties:** Nested `values.ar` and `values.en` objects
- **Village-First Keys:** Arabic property names used as keys (e.g., `"القرية"`, `"المحصول"`)
- **Coordinate Staggering:** Circular offset pattern for overlapping points (+10-20m radius)

### Data Themes (5 Categories)

#### 1. **Water Resources** 
```
Files: Water.canonical.geojson (55) + Water_new.canonical.geojson (29) = 84 features
Properties (9):
  • Village name
  • Main crops (2)
  • Crop cultivation months
  • Irrigation frequency
  • Water source (rain/well/river/tanker)
  • Water availability assessment
  • Water scarcity months
  • Irrigation needs change (10-year trend)
```

#### 2. **Energy Sources**
```
Files: Energy.canonical.geojson (57) + Energy_new.canonical.geojson (29) = 86 features
Properties (15):
  • Village name
  • Primary energy source
  • Peak season energy consumption
  • Energy mix percentages:
    - Manual labor (%)
    - Diesel generator (%)
    - Grid electricity (%)
    - Gasoline (%)
    - Solar power (%)
  • Weekly fuel consumption (L/week)
  • Weekly electricity usage (kW/week)
```

#### 3. **Food Production**
```
Files: Food.canonical.geojson (56) + Food_new.canonical.geojson (29) = 85 features
Properties (17):
  • Village name
  • Main crops
  • Crop timing/seasonality
  • Production level (home/small/commercial)
  • Cooperative membership
  • Traditional products (olive oil, preserves, dairy, honey)
  • Village participation rate
  • Livestock/poultry types
  • Number of birds
  • Feed types
```

#### 4. **General Information**
```
Files: General_Info.canonical.geojson (56) + General_Info_new.canonical.geojson (29) = 85 features
Properties (24):
  • Village name
  • Farmer age group
  • Gender
  • Farmland ownership
  • Land location
  • Farm size (< 5 dunums to > 1 hectare)
  • Soil type (sandy/limestone/clay/loamy)
  • Climate change observations
  • Climate change types (temperature, rainfall, heatwaves, frost)
  • Production impact from climate
  • Labor shortage indicators
  • Labor shortage reasons
```

#### 5. **Regenerative Agriculture**
```
Files: Regenerative_Agriculture.canonical.geojson (63) + Regenerative_Agriculture_new.canonical.geojson (29) = 92 features
Properties (24):
  • Village name
  • Regenerative techniques applied:
    - No-till/reduced tillage
    - Organic amendments
    - Biofertilizers
    - Composting
    - Cover crops
    - Mulching
    - Crop rotation
  • Seed selection criteria
  • Seed sources
  • Seed acquisition challenges
  • Soil enhancer types
  • Chemical fertilizer dependence
  • Fertilizer cost percentage
  • Pest control methods
  • Pesticide dependence
  • Pesticide cost percentage
  • Poultry raising practices
```

---

## Features & Capabilities

### 1. **Interactive Map Visualization**
- **Base Map:** MapLibre GL with custom styling
- **Clustering:** Native MapLibre clustering (radius: 40px, maxZoom: 14)
- **Zoom Levels:** 6 (country view) to 18 (field-level detail)
- **Coordinate System:** WGS84 (EPSG:4326)
- **Bounds:** Lebanon 33.5-34.1°N, 35.4-36.2°E

### 2. **Layer Management**
**Point Layers (Clustered):**
- 🔵 Water Resources (84 points)
- 🟡 Energy Sources (86 points)
- 🔴 Food Production (85 points)
- 🔵 General Information (85 points)
- 🟢 Regenerative Agriculture (92 points)

**Special Layers:**
- 🔥 Fire Data (heatmap + clustered points)
- 🏛️ Preservation Areas (polygons with hover effects)
- 🤖 AI Prediction Layers (5 heatmaps - regenerative adoption, water risk, production capacity, climate vulnerability)

**Layer Features:**
- Toggle visibility (checkbox controls)
- Color-coded by theme
- Dynamic clustering with count badges
- Custom icon system (SVG-based)

### 3. **Details Panel**
**Click any feature to view:**
- Village name (bilingual)
- All survey responses (3-24 properties per theme)
- Coordinates (latitude/longitude)
- Feature ID (for reference)

**Panel Features:**
- Smooth slide-in animation
- Scrollable content (unlimited properties)
- Close button (X)
- Language-sensitive display (AR/EN toggle)

### 4. **Bilingual Support**
**Languages:**
- Arabic (primary, right-to-left layout)
- English (transliteration, left-to-right)

**Toggle Behavior:**
```
User clicks language button:
  ↓
Update UI labels (sidebar, buttons, instructions)
  ↓
Re-render details panel with new language properties
  ↓
Update HTML attribute: <html lang="ar" dir="rtl">
  ↓
No data reload (language is presentation-only)
```

**RTL Support:**
- Automatic text-align: right
- Sidebar position flip
- Icon positioning adjustments
- Scrollbar on left side

### 5. **Dynamic Filtering** (UI Ready, Engine Planned)
**Filter UI Elements:**
- Village name dropdown (multiselect)
- Crop type checkboxes
- Farm size ranges
- Energy source selection
- Production level radio buttons

**Filter Logic (Planned in `filter-engine.js`):**
```javascript
// Apply filters → Update map layer → Re-cluster
filterFeatures(theme, filters) {
  const filtered = features.filter(f => 
    filters.village.includes(f.properties.values[lang]['القرية']) &&
    filters.crop.some(c => f.properties.values[lang]['المحصول'].includes(c))
  );
  updateMapLayer(theme, filtered);
}
```

### 6. **Performance Optimizations**
**IndexedDB Caching:**
```
First Load:  Fetch GeoJSON from network (2-5 seconds)
             ↓
             Store in browser IndexedDB
             ↓
             Cache key: "canonical-{theme}"
             Version: DATA_VERSION constant
             Expiry: 7 days

Subsequent Loads: Read from cache (50-200ms) ⚡️
                 ↓
                 Validate version & expiry
                 ↓
                 If stale → fetch new data
```

**Benefits:**
- 95% faster load times after first visit
- Offline-capable (7-day cache window)
- Automatic version invalidation
- No server-side caching needed

**Coordinate Staggering:**
```python
# For features with identical coordinates (same village)
def stagger_coordinates(centroid, index, offset=0.001):
    """
    Circular offset pattern:
    - Point 0: Centroid
    - Points 1-8: Ring 1 (111m radius)
    - Points 9-16: Ring 2 (222m radius)
    - Points 17+: Ring 3+ (333m+ radius)
    """
    ring = (index - 1) // 8 + 1
    angle = ((index - 1) % 8) * (2 * π / 8)
    offset_lon = offset * ring * cos(angle)
    offset_lat = offset * ring * sin(angle)
    return (centroid.x + offset_lon, centroid.y + offset_lat)
```

---

## Technology Stack

### Frontend
```
Core Libraries:
  • MapLibre GL JS 3.6.2 - Map rendering engine
  • Vanilla JavaScript (ES6+) - No framework dependencies
  • CSS3 - Styling with RTL support
  
Browser APIs:
  • IndexedDB - Client-side data caching
  • Fetch API - Asynchronous data loading
  • Geolocation API - User location (optional)
  
Features:
  • No build tools required
  • No transpilation needed
  • Direct file:// serving NOT supported (CORS issues)
  • Requires HTTP server for local testing
```

### Backend (Data Processing)
```
Python 3.12+ with libraries:
  • pandas 2.x - Data manipulation
  • numpy 1.26+ - Numerical operations
  • shapely 2.x - Geometry operations
  • geopandas 0.14+ - Geospatial data handling
  • scikit-learn 1.4+ - ML modeling
  • xgboost 2.0+ - Gradient boosting (optional)
  • joblib - Model serialization

Virtual Environment:
  Location: .venv/
  Activation: .venv\Scripts\activate (Windows)
  Requirements: requirements.txt
```

### Development Tools
```
Version Control:
  • Git + GitHub
  • GitHub Pages for hosting

Editor/IDE:
  • VS Code (recommended)
  • Extensions: Python, JavaScript, GitHub Copilot

Testing:
  • Python built-in http.server module
  • Browser DevTools (Chrome/Firefox)
  • No automated test suite (manual QA)
```

---

## File Structure

```
ResolveMaping_final2/
│
├── 📄 index.html                    # Main entry point (HTML structure)
├── 📄 app.js                        # Core application logic (3,216 lines)
├── 📄 style.css                     # Styles with RTL support
├── 📄 verify_villages.html          # Village coordinate verification tool
├── 📄 requirements.txt              # Python dependencies
├── 📄 REFACTORING_GUIDE.md          # Technical architecture documentation
├── 📄 PROJECT_DOCUMENTATION.md      # This file (comprehensive guide)
│
├── 📁 app/modules/                  # Modular JavaScript architecture
│   ├── data/
│   │   └── loader.js                # IndexedDB caching + GeoJSON loading
│   ├── state/
│   │   └── store.js                 # Immutable state management
│   ├── i18n/
│   │   └── property-schemas.js      # 89 bilingual property mappings
│   └── filters/
│       └── filter-engine.js         # Dynamic filtering logic (planned)
│
├── 📁 data/                         # All data files
│   ├── geojson/
│   │   ├── canonical/               # ⭐ PRIMARY DATA SOURCE
│   │   │   ├── Water.canonical.geojson              (55 features)
│   │   │   ├── Water_new.canonical.geojson          (29 features)
│   │   │   ├── Energy.canonical.geojson             (57 features)
│   │   │   ├── Energy_new.canonical.geojson         (29 features)
│   │   │   ├── Food.canonical.geojson               (56 features)
│   │   │   ├── Food_new.canonical.geojson           (29 features)
│   │   │   ├── General_Info.canonical.geojson       (56 features)
│   │   │   ├── General_Info_new.canonical.geojson   (29 features)
│   │   │   ├── Regenerative_Agriculture.canonical.geojson     (63 features)
│   │   │   └── Regenerative_Agriculture_new.canonical.geojson (29 features)
│   │   │
│   │   ├── Water.geojson / Water_ar.geojson         # Legacy dual-file format
│   │   ├── Energy.geojson / Energy_ar.geojson       # (Being phased out)
│   │   ├── Food.geojson / Food_ar.geojson
│   │   ├── General_Info.geojson / General_Info_ar.geojson
│   │   ├── Regenerative_Agriculture.geojson / _ar.geojson
│   │   │
│   │   ├── AI_Grid_Predictions.geojson              # ML prediction grid (21k points)
│   │   ├── Model_Predictions.geojson                # Survey data with predictions
│   │   ├── Farmers_Boundary.geojson                 # Study area boundary
│   │   ├── fire.geojson                             # Fire incident data
│   │   └── Preservations.geojson                    # Protected area polygons
│   │
│   ├── layers/                      # Source CSV files (Arabic + English)
│   │   ├── Arabic/
│   │   │   ├── Water.csv
│   │   │   ├── Energy.csv
│   │   │   ├── Food.csv
│   │   │   ├── General_Info.csv
│   │   │   └── Regenerative_Agriculture.csv
│   │   └── English/
│   │       └── (Mirror structure with transliterated content)
│   │
│   ├── survey_by_theme/             # Survey responses split by theme
│   ├── canonical_audit/             # Audit trails for canonical generation
│   ├── conversion_audit/            # Legacy conversion logs
│   ├── models/                      # ML models (*.joblib files)
│   │   ├── rf_regen_adoption.joblib
│   │   ├── rf_water_risk.joblib
│   │   ├── rf_production_level.joblib
│   │   ├── rf_climate_vulnerability.joblib
│   │   └── training_report.txt
│   │
│   ├── MZSurvey farmers ENGLISH.csv              # Original survey data (29 responses)
│   ├── MZSurvey farmers ENGLISH_with_coords.csv  # + coordinates added
│   ├── Original_Survey_Data_Complete.xlsx        # Raw Excel survey export
│   ├── ml_prepared_data.csv                      # Engineered features for ML
│   ├── verified_village_coordinates.csv          # Village → coordinate mapping
│   └── (Other temporary JSON files)
│
├── 📁 scripts/                      # Data processing pipeline
│   ├── generate_canonical_geojson.py            # ⭐ PRIMARY: CSV → Canonical GeoJSON
│   ├── csvs_to_geojson_complete.py              # Legacy: CSV → Dual GeoJSON files
│   ├── generate_canonical_new_data.py           # Survey → Canonical conversion
│   ├── integrate_survey_data.py                 # Merge survey with coordinates
│   │
│   ├── translate_csv_gold_standard.py           # CSV translation pipeline
│   ├── transliterate_village_names.py           # Arabic → English village names
│   ├── verify_transliterations.py               # Validate transliterations
│   ├── audit_villages.py                        # Village consistency check
│   │
│   ├── fix_theme_coordinates.py                 # Add/fix coordinates in CSVs
│   ├── research_village_coordinates.py          # Coordinate lookup automation
│   ├── add_coordinates_to_survey.py             # Survey coordinate enrichment
│   │
│   └── ml_pipeline/                             # Machine learning workflow
│       ├── run_pipeline.py                      # Execute full ML pipeline
│       ├── feature_engineering.py               # Engineer 60+ features
│       ├── train_models.py                      # Train 5 classification models
│       ├── interpolate_grid.py                  # Generate prediction grid
│       └── generate_boundary.py                 # Create study area boundary
│
├── 📁 .github/                      # GitHub configuration
│   ├── workflows/                   # GitHub Actions (if any)
│   └── copilot-instructions.md      # AI agent context (423 lines)
│
└── 📁 .venv/                        # Python virtual environment (gitignored)
```

---

## Data Pipeline

### Complete Workflow: CSV → GeoJSON → Browser

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: Source Data Collection                                 │
└─────────────────────────────────────────────────────────────────┘
   Field Surveys (200+ questions per farmer)
        ↓
   Excel Export (KoboToolbox/ODK)
        ↓
   Manual QA (remove duplicates, validate responses)
        ↓
   Store: data/Original_Survey_Data_Complete.xlsx

┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: Data Cleaning & Enrichment                            │
└─────────────────────────────────────────────────────────────────┘
   Excel → CSV conversion
        ↓
   Coordinate Addition (scripts/add_coordinates_to_survey.py)
        ├── Manual lookup: Google Maps / OpenStreetMap
        ├── Coordinate validation (Lebanon bounds check)
        └── Staggering for identical coordinates
        ↓
   Output: data/MZSurvey farmers ENGLISH_with_coords.csv

┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: Translation & Alignment                                │
└─────────────────────────────────────────────────────────────────┘
   English → Arabic CSV Generation
        ├── Column header translation
        ├── Village name transliteration (phonetic, not literal)
        │   Example: "Mrosti" not "My Lady" (for مروستي)
        ├── Row-by-row alignment verification
        └── Property key normalization (remove colons, trim spaces)
        ↓
   Output: data/layers/Arabic/*.csv + data/layers/English/*.csv

┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: Theme Splitting                                        │
└─────────────────────────────────────────────────────────────────┘
   Survey CSV → 5 Theme-Specific CSVs
        ├── Water: Irrigation, water sources, scarcity
        ├── Energy: Power sources, fuel consumption
        ├── Food: Crops, production, livestock
        ├── General Info: Demographics, farm size, climate
        └── Regenerative Agriculture: Techniques, fertilizers, pests
        ↓
   Arabic CSVs: data/layers/Arabic/
   English CSVs: data/layers/English/

┌─────────────────────────────────────────────────────────────────┐
│ STAGE 5: Canonical GeoJSON Generation ⭐ PRIMARY STEP           │
└─────────────────────────────────────────────────────────────────┘
   Command: python scripts/generate_canonical_geojson.py
   
   Process:
   1. Load paired CSVs (Arabic + English)
   2. Validate row counts match
   3. For each row (i):
        a. Extract coordinates (X, Y)
        b. Generate stable ID: {theme}_{row}_{coordHash8}
        c. Merge Arabic + English properties:
           {
             "values": {
               "ar": {...},  // Arabic row i
               "en": {...}   // English row i
             }
           }
        d. Create Point geometry
   4. Validate all features within Lebanon bounds
   5. Write canonical GeoJSON
   6. Generate audit trail JSON
   
   Output: data/geojson/canonical/*.canonical.geojson (10 files)

┌─────────────────────────────────────────────────────────────────┐
│ STAGE 6: Machine Learning Pipeline (Optional)                   │
└─────────────────────────────────────────────────────────────────┘
   Command: cd scripts/ml_pipeline && python run_pipeline.py
   
   Stages:
   1. Feature Engineering (60+ derived features)
   2. Model Training (5 RandomForest classifiers)
   3. Spatial Grid Interpolation (21k prediction points)
   4. Boundary Generation (convex hull / alpha shape)
   
   Output:
   - data/models/*.joblib (trained models)
   - data/geojson/AI_Grid_Predictions.geojson
   - data/geojson/Farmers_Boundary.geojson

┌─────────────────────────────────────────────────────────────────┐
│ STAGE 7: Browser Deployment                                     │
└─────────────────────────────────────────────────────────────────┘
   User opens: https://yourusername.github.io/ResolveMaping_final2/
        ↓
   app.js loads → app/modules/data/loader.js executes
        ↓
   Load all themes (5 × 2 files = 10 GeoJSON files)
        ├── Check IndexedDB cache first
        ├── If cache miss → Fetch from network
        ├── Merge original + _new files per theme
        └── Cache result for 7 days
        ↓
   Render map with 432 features
        ↓
   User interaction (click, filter, toggle layers)
```

### Key Scripts Explained

#### `generate_canonical_geojson.py` (PRIMARY)
```python
"""
Purpose: Merge paired Arabic + English CSVs into single bilingual GeoJSON per theme
Input: data/layers/Arabic/*.csv + data/layers/English/*.csv
Output: data/geojson/canonical/*.canonical.geojson

Key Functions:
- generate_stable_id(theme, row, coords): Create deterministic feature IDs
- merge_ar_en_row(ar_row, en_row): Combine bilingual properties
- validate_coordinates(lon, lat): Check Lebanon bounds (33.5-34.1°N, 35.4-36.2°E)
- generate_canonical_geojson(theme_config): Main orchestration

Configuration (THEMES dict):
- Theme name (water, energy, food, general, regen)
- Arabic CSV path
- English CSV path
- Color hex code

Example Output Structure:
{
  "type": "FeatureCollection",
  "features": [{
    "id": "Water_2_a3f8b9c1",
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [35.5, 33.7]},
    "properties": {
      "featureId": "Water_2_a3f8b9c1",
      "theme": "water",
      "values": {
        "ar": {"القرية": "مروستي", "المحصول": "تفاح"},
        "en": {"القرية": "Mrosti", "المحصول": "Apple"}
      }
    }
  }]
}
"""
```

#### `ml_pipeline/run_pipeline.py`
```python
"""
Purpose: Generate AI prediction heatmap layers

Pipeline Stages:
1. Feature Engineering (feature_engineering.py):
   - Merge 5 theme GeoJSON files
   - Engineer 60+ features from survey data
   - Create 5 binary target variables:
     * target_regen_adoption (regenerative agriculture likelihood)
     * target_water_risk (water scarcity vulnerability)
     * target_production_level (economic resilience)
     * target_climate_vulnerability (climate impact susceptibility)
     * target_labor_shortage (SKIPPED - insufficient data)
   - Output: data/ml_prepared_data.csv

2. Model Training (train_models.py):
   - RandomForest classifiers (default) or XGBoost
   - Spatial cross-validation (GroupKFold by village)
   - Hyperparameter tuning via GridSearchCV
   - Model evaluation (F1-score, ROC-AUC, confusion matrix)
   - Output: data/models/*.joblib + training_report.txt

3. Grid Interpolation (interpolate_grid.py):
   - Predict at survey points (287 original features)
   - Interpolate to regular grid (default 0.005° ≈ 500m spacing)
   - Methods: IDW (Inverse Distance Weighting) or Kriging
   - Clip to Lebanon bounds
   - Output: data/geojson/AI_Grid_Predictions.geojson (21k points)

4. Boundary Generation (generate_boundary.py):
   - Compute convex hull or alpha shape around survey points
   - Buffer boundary by 5km
   - Output: data/geojson/Farmers_Boundary.geojson

Execution:
cd scripts/ml_pipeline
python run_pipeline.py              # Run all stages
python run_pipeline.py --skip-train # Skip training (use existing models)
"""
```

---

## Deployment

### GitHub Pages (Production)

**Automatic Deployment:**
```bash
# 1. Commit changes
git add .
git commit -m "Update data layers / Fix bug / Add feature"

# 2. Push to GitHub
git push origin main

# 3. GitHub Pages auto-deploys (2-3 minutes)
# No build step required - serves static files directly
```

**Configuration:**
- Repository Settings → Pages → Source: main branch / root
- Custom domain (optional): Add CNAME file
- HTTPS: Automatically enabled by GitHub

**URL Structure:**
```
Production:  https://yourusername.github.io/ResolveMaping_final2/
Dev Branch:  https://yourusername.github.io/ResolveMaping_final2/index.html?dev=true
```

### Local Development Server

**Method 1: Python HTTP Server (Recommended)**
```bash
# From project root
python -m http.server 8000

# Open browser
http://localhost:8000/

# Pros: Built-in, no installation, supports CORS
# Cons: No auto-reload on file changes
```

**Method 2: VS Code Live Server Extension**
```bash
# Install: VS Code → Extensions → "Live Server"
# Right-click index.html → "Open with Live Server"

# Pros: Auto-reload on file save
# Cons: Requires VS Code extension
```

**Method 3: Node.js http-server**
```bash
# Install globally
npm install -g http-server

# Run
http-server -p 8000 -c-1

# Pros: Fast, cross-platform, disable cache with -c-1
# Cons: Requires Node.js installed
```

**⚠️ NEVER use `file://` protocol**
```
❌ file:///d:/Programing/ResolveMaping_final2/index.html
   → CORS errors when loading GeoJSON files
   → IndexedDB may not work properly
   → Fetch API blocked by browser security

✅ http://localhost:8000/
   → Proper HTTP server required
```

### Production Data Hosting (Optional)

**For Large Data Files (> 100MB):**
```javascript
// app.js configuration
const PRODUCTION_DATA_URL = 'https://pub-xxxxx.r2.dev/my-project/';

// Routes data/ and output/ paths to CDN
function fromRoot(path) {
    if (path.startsWith('data/') || path.startsWith('output/')) {
        return PRODUCTION_DATA_URL + path;
    }
    return path; // Local assets (index.html, style.css, etc.)
}
```

**CDN Options:**
- Cloudflare R2 (S3-compatible, zero egress fees)
- AWS S3 + CloudFront
- Netlify Large Media
- Azure Blob Storage

---

## Usage Guide

### For End Users (Map Viewers)

#### Opening the Map
1. Navigate to: `https://yourusername.github.io/ResolveMaping_final2/`
2. Wait 2-5 seconds for initial data load
3. Map centers on Lebanon (Beirut)

#### Exploring Data
```
🖱️ Mouse Controls:
• Left Click + Drag:  Pan map
• Scroll Wheel:       Zoom in/out
• Right Click + Drag: Tilt map (3D)
• Double Click:       Zoom in (centered)

🎛️ Sidebar Controls:
• Layer Toggles: Check/uncheck to show/hide themes
• Language Toggle: Switch between Arabic (AR) and English (EN)
• Zoom Controls: + / - buttons to zoom

📍 Interacting with Features:
• Click any point: View details panel on right
• Hover polygon: Highlight preservation area
• Click cluster: Zoom to expand cluster

ℹ️ Details Panel:
• Scrollable: Unlimited properties shown
• Village name: Always at top
• Coordinates: Bottom of panel
• Close: Click X or click map background
```

#### Language Switching
```
Current Language: English
   ↓ Click "AR" button
   ↓
Layout flips to RTL (right-to-left)
Sidebar moves to right side
Property labels in Arabic
Details panel shows Arabic values
   ↓ Click "EN" button
   ↓
Layout flips to LTR
Back to English labels and values
```

#### Filtering Data (UI Present, Logic Pending)
```
1. Open filter panel for a theme
2. Select village names (multiselect dropdown)
3. Choose crop types (checkboxes)
4. Set farm size range (slider)
5. Click "Apply Filters"
   → Map updates to show only matching features
6. Click "Clear Filters" to reset
```

### For Data Managers

#### Adding New Survey Data

**Scenario:** You collected 15 new farmer surveys in Zahle.

**Steps:**
```bash
# 1. Prepare CSV with coordinates
#    Columns: All survey questions + X (longitude) + Y (latitude)
#    Save as: data/NewSurvey_2026_Zahle.csv

# 2. Split by theme (manual or script)
#    Extract relevant columns for each theme
#    Save to: data/layers/Arabic/ThemeName_new.csv

# 3. Translate to English
#    Create: data/layers/English/ThemeName_new.csv
#    Ensure row order matches Arabic file exactly

# 4. Generate canonical GeoJSON
cd scripts
python generate_canonical_geojson.py

# 5. Update loader configuration
#    Edit: app/modules/data/loader.js
#    Add new file to THEMES config:
#    water: {
#        files: [
#            'data/geojson/canonical/Water.canonical.geojson',
#            'data/geojson/canonical/Water_new.canonical.geojson',
#            'data/geojson/canonical/Water_zahle_2026.canonical.geojson'  ← Add this
#        ]
#    }

# 6. Increment DATA_VERSION
#    Edit: app/modules/data/loader.js line 24
#    Change: DATA_VERSION: '2.2.0' → DATA_VERSION: '2.3.0'

# 7. Test locally
python -m http.server 8000
#    Open http://localhost:8000/
#    Check console: "✓ Loaded water: XX features" (should increase by 15)

# 8. Deploy
git add .
git commit -m "Add Zahle 2026 survey data (15 farmers)"
git push origin main
```

#### Updating Existing Data

**Scenario:** Farmer in Mrosti updated their energy source from diesel to solar.

**Steps:**
```bash
# 1. Edit source CSV
#    File: data/layers/Arabic/Energy.csv
#    Find row: القرية = "مروستي"
#    Update: مصدر الطاقة = "الطاقة الشمسية"

# 2. Edit English CSV (keep row alignment!)
#    File: data/layers/English/Energy.csv
#    Same row number
#    Update: Energy Source = "Solar"

# 3. Regenerate canonical GeoJSON
python scripts/generate_canonical_geojson.py

# 4. Increment DATA_VERSION (force cache refresh)
#    app/modules/data/loader.js: '2.2.0' → '2.2.1'

# 5. Deploy
git add data/layers/ data/geojson/canonical/ app/modules/data/loader.js
git commit -m "Fix: Update Mrosti energy source to solar"
git push origin main
```

#### Adding New Property Mappings

**Scenario:** Survey added question "57. Do you use drip irrigation?" and you want it displayed in details panel.

**Steps:**
```bash
# 1. Ensure property exists in canonical GeoJSON
#    Open: data/geojson/canonical/Water_new.canonical.geojson
#    Check: properties.values.ar contains "57. هل تستخدم الري بالتنقيط؟"
#    Check: properties.values.en contains "57. Do you use drip irrigation?"

# 2. Add mapping to PropertySchemas
#    Edit: app/modules/i18n/property-schemas.js
#    Find: water: { ... }
#    Add:
#    '57. Do you use drip irrigation?': { en: 'Drip Irrigation', ar: 'الري بالتنقيط' },
#    '57. هل تستخدم الري بالتنقيط؟': { en: 'Drip Irrigation', ar: 'الري بالتنقيط' },

# 3. Test
python -m http.server 8000
#    Click water feature
#    Verify "Drip Irrigation" appears in details panel

# 4. Deploy
git add app/modules/i18n/property-schemas.js
git commit -m "Add drip irrigation property mapping"
git push origin main
```

### For Developers

#### Code Structure
```javascript
// app.js - Monolithic legacy code (3,216 lines)
// Being gradually refactored to modules

// Entry point
async function init() {
    await map.load();
    await DataLoader.loadAllThemes(progressCallback);
    StateStore.setState({ themes: loadedData });
    attachEventListeners();
}

// Key functions
addGeoJsonLayer(id, url, color)  // Legacy: Load + render layer
refreshDetailsPanel(featureId)   // Display feature properties
i18n.setLang(lang)               // Switch language, update UI
applyFilters(theme, filters)     // Filter features (legacy, rebuilds layers)

// New modular approach (app/modules/)
DataLoader.loadGeoJSON(key, url)             // IndexedDB + fetch
StateStore.setState({ key: value })          // Immutable updates
PropertySchemas.buildDetailsPanel(feature)   // Map properties to labels
```

#### Adding a New Layer

**Example: Add "Soil Quality" layer**

```javascript
// 1. Prepare data
//    Create: data/geojson/canonical/Soil_Quality.canonical.geojson
//    Structure: Same as other canonical files (bilingual, stable IDs)

// 2. Update loader.js THEMES config
// File: app/modules/data/loader.js
const THEMES = {
    // ... existing themes ...
    soilQuality: {
        id: 'soil-quality-points',
        file: 'data/geojson/canonical/Soil_Quality.canonical.geojson',
        color: '#8e44ad'  // Purple
    }
};

// 3. Update app.js clusterColors
// File: app.js lines 3-11
const clusterColors = {
    // ... existing colors ...
    soilQuality: '#8e44ad'
};

// 4. Add i18n strings
// File: app.js lines 13-80
const i18n = {
    strings: {
        en: {
            layerNames: {
                // ... existing ...
                soilQuality: 'Soil Quality'
            }
        },
        ar: {
            layerNames: {
                // ... existing ...
                soilQuality: 'جودة التربة'
            }
        }
    }
};

// 5. Add PropertySchemas mappings
// File: app/modules/i18n/property-schemas.js
const SCHEMAS = {
    // ... existing schemas ...
    soilQuality: {
        'القرية': { en: 'Village', ar: 'القرية' },
        'pH_Value': { en: 'pH Level', ar: 'مستوى الحموضة' },
        'Organic_Matter': { en: 'Organic Matter %', ar: 'نسبة المادة العضوية' },
        // ... more properties ...
    }
};

// 6. Add checkbox to sidebar
// File: index.html (find sidebar layer toggles section)
<label>
    <input type="checkbox" class="layer-toggle" data-layer="soil-quality-points" checked>
    <span class="layer-name" data-i18n="layerNames.soilQuality">Soil Quality</span>
</label>

// 7. Test locally
// python -m http.server 8000
// Check: Layer toggle, clustering, details panel, bilingual display

// 8. Deploy
// git add .
// git commit -m "Add Soil Quality layer"
// git push origin main
```

#### Debugging Tips

**Console Logging:**
```javascript
// Check what's loaded
console.log(StateStore.getState());  // Current app state
console.log(StateStore.getThemeData('water'));  // Specific theme data

// Trace data loading
// app/modules/data/loader.js has verbose logging:
// "Fetching canonical-water from network..."
// "✓ Cached: canonical-water"
// "✓ Loaded water: 84 features"

// Check property mappings
const schema = PropertySchemas.SCHEMAS.water;
console.log(schema);  // All mapped properties for water theme
```

**Common Issues:**

| Error | Cause | Solution |
|-------|-------|----------|
| CORS error loading GeoJSON | Using file:// protocol | Use HTTP server (python -m http.server 8000) |
| Layer not showing | Checkbox unchecked or wrong layer ID | Check data-layer attribute matches THEMES.id |
| Details panel empty | Missing PropertySchemas mappings | Add property keys to property-schemas.js |
| Wrong translation | Misaligned Arabic/English CSV rows | Verify row counts match, regenerate canonical |
| Features at (0, 0) | Missing X/Y columns in CSV | Add coordinates before generating canonical |
| Cluster counts wrong | Cache not invalidated | Increment DATA_VERSION in loader.js |

---

## Maintenance

### Regular Tasks

#### Weekly
- ✅ Check GitHub Pages deployment status
- ✅ Review browser console for JavaScript errors
- ✅ Verify map loads within 5 seconds

#### Monthly
- ✅ Update Python dependencies: `pip install --upgrade -r requirements.txt`
- ✅ Review IndexedDB cache size (browser DevTools → Application → IndexedDB)
- ✅ Check for broken external links (if any documentation)

#### Quarterly
- ✅ Audit canonical GeoJSON files for data quality
- ✅ Review PropertySchemas for missing mappings
- ✅ Test cross-browser compatibility (Chrome, Firefox, Safari, Edge)
- ✅ Verify RTL layout on Arabic display

#### Annually
- ✅ Re-run ML pipeline with updated data
- ✅ Update MapLibre GL version (check changelog for breaking changes)
- ✅ Review and clean up legacy code (app.js refactoring to modules)

### Data Quality Checks

**Before Regenerating Canonical GeoJSON:**
```bash
# 1. Verify row alignment
python -c "
import pandas as pd
ar = pd.read_csv('data/layers/Arabic/Water.csv')
en = pd.read_csv('data/layers/English/Water.csv')
print(f'Arabic rows: {len(ar)}')
print(f'English rows: {len(en)}')
assert len(ar) == len(en), 'ROW COUNT MISMATCH!'
print('✓ Row counts match')
"

# 2. Check coordinate validity
python -c "
import pandas as pd
df = pd.read_csv('data/layers/Arabic/Water.csv')
invalid = df[(df['X'] < 35.0) | (df['X'] > 36.5) | (df['Y'] < 33.0) | (df['Y'] > 34.5)]
if len(invalid) > 0:
    print(f'⚠️ {len(invalid)} features outside Lebanon bounds')
    print(invalid[['القرية', 'X', 'Y']])
else:
    print('✓ All coordinates valid')
"

# 3. Check for duplicates
python -c "
import pandas as pd
df = pd.read_csv('data/layers/Arabic/Water.csv')
dupes = df[df.duplicated(subset=['القرية', 'X', 'Y'], keep=False)]
if len(dupes) > 0:
    print(f'⚠️ {len(dupes)} duplicate entries found')
    print(dupes[['القرية', 'X', 'Y']])
else:
    print('✓ No duplicates')
"

# 4. Regenerate if checks pass
python scripts/generate_canonical_geojson.py
```

### Backup Strategy

**Critical Files to Backup (Outside Git):**
```
📦 Backup Package (Monthly):
│
├── data/
│   ├── MZSurvey farmers ENGLISH_with_coords.csv  # Source of truth
│   ├── Original_Survey_Data_Complete.xlsx        # Raw survey data
│   ├── layers/Arabic/*.csv                       # Processed theme CSVs
│   └── layers/English/*.csv                      # Translated CSVs
│
└── data/geojson/canonical/*.canonical.geojson    # Generated canonical files

Backup Method:
1. Compress: zip -r ResolveMaping_backup_2026-02-17.zip data/
2. Store: Cloud (Google Drive, Dropbox, OneDrive)
3. Rotate: Keep last 12 monthly backups
```

**Git is NOT a backup** - Use for version control only. Store critical data externally.

### Performance Monitoring

**Key Metrics:**
```javascript
// Add to app.js init() function for production monitoring
const startTime = performance.now();

await DataLoader.loadAllThemes((loaded, total, theme) => {
    console.log(`Loading ${theme}: ${loaded}/${total}`);
});

const loadTime = performance.now() - startTime;
console.log(`⏱️ Total load time: ${loadTime.toFixed(0)}ms`);

// Expected benchmarks:
// First load (network): 2000-5000ms
// Cached load: 50-200ms
// Target: < 3000ms for first load
```

**Monitor IndexedDB Size:**
```javascript
// Browser DevTools → Application → Storage → IndexedDB → ResolveMapDB
// Expected size: 500KB - 1MB for all themes
// Alert if > 5MB (indicates cache bloat)
```

---

## Appendix

### Property Schema Reference

**All 89 Bilingual Property Mappings:**

<details>
<summary>Click to expand</summary>

#### Water Theme (18 properties)
- `القرية` / `4.القرية` / `4.القرية:` → Village / القرية
- `X` → Longitude / خط الطول
- `Y` → Latitude / خط العرض
- `المحصول` / `10.ما هما المحصولان...` → Crops / المحصول
- `_4` → Cultivation Months / اشهر الزراعة
- `_5` → Crop Irrigation / ريّ المحصول
- `_6` / `13.ما هو المصدر الرئيسي...` → Main Water Source / مصدر مياه الريّ
- `_7` / `16.كيف تقيّم توفر المياه...` → Water Availability / توفر المياه
- `_8` / `17.هل هناك أشهر...` → Water Shortage Months / أشهر شح المياه
- `18.هل لاحظت أي تغيير...` → Irrigation Needs Change / تغير احتياجات الري

#### Energy Theme (17 properties)
- Village, X, Y (same as above)
- `_3` / `14.ما هو مصدر الطاقة...` → Energy Source / مصدر الطاقة
- `_4` / `15.كمية الطاقة المستخدمة...` → Peak Season Energy Use / كمية الطاقة
- `_5` → Manual % / يدويا%
- `_6` → Diesel % / ديزل%
- `_7` → Grid % / شبكة%
- `_8` → Gasoline % / بنزين%
- `_9` → Solar % / شمسية%
- `_10` → Diesel L/Week / ديزل لتر/أسبوع
- `_11` → Gasoline L/Week / بنزين لتر/أسبوع
- `_12` → kW/Week / كيلوواط/أسبوع

#### Food Theme (20 properties)
- Village, X, Y
- `_3` → Main Crops / المحاصيل الرئيسية
- `_4` → Crop Timing / توقيت المحاصيل
- `_5` / `19.كيف تصف مستوى إنتاج...` → Production Level / مستوى الانتاج
- `_6` → Traditional Products / المنتجات التقليدية
- `_7` / `24. ما هي نسبة المنازل...` → Village Participation % / نسبة المشاركة
- `_8` → Animal Types / انواع الحيوانات
- `_9` → Number of Birds / عدد الطيور
- `_10` → Feed Type / نوع العلف
- `20. هل أنت عضو في تعاونية...` → Cooperative Member / عضو في تعاونية
- `إذا كانت الإجابة نعم: ما هو العدد...` → Active Coop Members / عدد الأعضاء

#### General Info Theme (24 properties)
- Village, X, Y
- `2. الفئة العمرية` / `2.الفئة العمرية:` → Age Group / الفئة العمرية
- `3. الجنس` / `3.الجنس:` → Gender / الجنس
- `_3` / `8.ما هو حجم الحيازة...` → Farm Size / حجم الزراعة
- `_4` / `9.ما هو نوع التربة...` → Soil Type / نوع التربة
- `_5` / `53. إذا كانت الإجابة "نعم"...` → Climate Changes / التغيرات المناخية
- `_6` / `54.كيف أثرت هذه التغيرات...` → Production Impact / تأثير على الإنتاج
- `5. Own Farmland?` / `5.هل تمتلك أرضاً...` → Farmland Ownership / ملكية الأرض
- `6. Land Location` / `6.موقع أرضك:` → Land Location / موقع الأرض
- `52. Climate Change Noticed?` / `52. هل لاحظت تغيرات...` → Climate Observed / ملاحظة التغير
- `55. هل تواجه صعوبة في العثور...` → Labor Shortage / نقص العمالة
- `56. إذا كانت الإجابة "نعم"...` → Labor Shortage Reasons / أسباب نقص العمالة

#### Regenerative Agriculture Theme (30 properties)
- Village, X, Y
- `_3` → Regenerative Techniques / تقنيات الزراعة التجديدية
- `_4` / `38.ما هي أنواع المحسنات...` → Soil Amendment Types / أنواع محسنات التربة
- `_5` / `39.ما مدى اعتمادك...` → Chemical Fertilizer Dependence / الاعتماد على الأسمدة
- `_6` / `43.كيف تقوم بمكافحة الآفات؟` → Pest Control Method / طريقة مكافحة الآفات
- `34. Seed Selection Criteria` / `34.ما هي المعايير...` → Seed Selection / معايير اختيار البذور
- `35. Seed Source` / `35.كيف تحصل على البذور...` → Seed Source / مصدر البذور
- `36. Seed Challenges` / `36.ما هو التحدي الأكبر...` → Seed Acquisition Challenges / تحديات الحصول
- `40. Fertilizer Cost %` / `40.ما هي نسبة تكلفة...` → Fertilizer Cost % / نسبة تكلفة الأسمدة
- `44. Pesticide Reliance` / `44.ما مدى اعتمادك على المبيدات...` → Pesticide Dependence / الاعتماد على المبيدات
- `45. Pesticide Cost %` / `45.ما هي نسبة تكلفة المبيدات...` → Pesticide Cost % / نسبة تكلفة المبيدات
- `63. Raise Poultry?` / `63.هل تربي الدواجن...` → Poultry Raising / تربية الدواجن

</details>

### Village Coverage Map

**38+ Villages with Survey Data:**

| Village (Arabic) | Village (English) | Responses | Region |
|------------------|-------------------|-----------|---------|
| مشغرة | Meshghara | 15 | Mount Lebanon |
| مروستي | Mrosti | 12 | Mount Lebanon |
| رياق | Riyaq | 4 | Bekaa Valley |
| تربل | Terbol | 2 | Bekaa Valley |
| زحلة | Zahlé | 1 | Bekaa Valley |
| ماسما | Masma | 1 | Mount Lebanon |
| دلهامية | Dalhamieh | 1 | Mount Lebanon |
| الفاكهة | Al-Fakiha | 1 | Mount Lebanon |
| علي النهري | Ali Al-Nahri | 1 | Mount Lebanon |
| حارة الفيكاني | Harat Al-Fikani | 1 | Mount Lebanon |
| نبي شيت | Nabi Chit | 1 | Mount Lebanon |
| اللبوة | Al-Labwa | 1 | Mount Lebanon |
| ... | (26 more villages) | ... | ... |

---

## Contact & Support

**Project Maintainer:** [Your Name/Organization]  
**Email:** [your-email@domain.com]  
**Repository:** https://github.com/yourusername/ResolveMaping_final2  
**Issues:** https://github.com/yourusername/ResolveMaping_final2/issues

**Documentation Version:** 1.0  
**Last Review:** February 17, 2026

---

*This documentation is maintained alongside the codebase. For technical implementation details, see [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md). For AI agent context, see [.github/copilot-instructions.md](.github/copilot-instructions.md).*
