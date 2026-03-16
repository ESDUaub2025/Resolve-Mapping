## Copilot instructions for this repository

### Project Overview
Static, browser-based interactive map for agricultural data in Mount Lebanon & Chouf District, Lebanon. Built with MapLibre GL + native heatmaps (not deck.gl overlays). **Canonical bilingual architecture** loads single GeoJSON files with nested EN/AR properties, eliminating dual-file loading.

**Architecture:** No backend, no build step — serve static files with `python -m http.server 8000` from repo root. Data pipeline: CSV sources → Python preprocessing → Canonical GeoJSON → IndexedDB caching → client-side rendering.

**Critical Context:** Hybrid architecture with **both legacy (dual-file) and new (canonical) systems** coexisting. Use canonical approach for all new features. Legacy code being phased out but still active in parts of `app.js`.

### Core Components & File Structure
- **`app.js`** (3216 lines): Main client logic, layer initialization, legacy dual-file code (being phased out)
- **`app/modules/`**: Modular architecture for canonical bilingual system:
  - **`data/loader.js`**: Loads canonical GeoJSON with IndexedDB caching, handles cache invalidation
  - **`state/store.js`**: Immutable state management, observer pattern for reactivity
  - **`i18n/property-schemas.js`**: Bilingual property mappings (48 properties across 5 themes)
  - **`filters/filter-engine.js`**: Filter logic (not yet implemented)
- **`index.html`**: Sidebar controls with `data-layer` attributes mapping to layer IDs
- **`style.css`**: Sidebar, details panel, RTL support for Arabic
- **`data/geojson/`**: Legacy dual-file GeoJSON (Water.geojson, Water_ar.geojson)
- **`data/geojson/canonical/`**: **New canonical format** — single bilingual files per theme (287 features):
  - `Water.canonical.geojson`, `Energy.canonical.geojson`, `Food.canonical.geojson`, `General_Info.canonical.geojson`, `Regenerative_Agriculture.canonical.geojson`
  - Structure: `{id: "Water_2_a3f8b9c1", properties: {featureId, theme, values: {ar: {...}, en: {...}}}}`
- **`data/layers/{English,Arabic}/`**: CSV sources (5 themes: Energy, Food, General Info, Regenerative Agriculture, Water)
- **`scripts/`**: Data processing pipeline
  - `generate_canonical_geojson.py`: **Primary script** — merges AR/EN CSVs into canonical format with stable IDs
  - `csvs_to_geojson_complete.py`: Legacy converter (creates dual AR/EN files)
  - Supporting scripts: `transliterate_village_names.py`, `audit_villages.py`, `verify_transliterations.py`

### Layer System (Critical Pattern)
**Point layers** in `app.js` and `index.html`:
- Clustered point layers: `water-points`, `energy-points`, `food-points`, `general-points`, `regen-points`, `farmers-points`, `fire-points`
- Non-clustered fire layer: `fire-points-raw` (used as heatmap source, visual display uses clustered `fire-points`)
- Native heatmap: `fire-heatmap` (MapLibre heatmap layer using `fire-points-raw` source)
- Polygon layer: `preservations-poly` (uses `bindPolygonInteraction()` for hover states)
- AI heatmap layers (native MapLibre): `ai-regen`, `ai-water`, `ai-econ`, `ai-labor`, `ai-climate`
  - **Status**: Implemented in code but **non-functional** - missing `AI_Grid_Predictions.geojson` source file
  - Source: `ai-grid` from `AI_Grid_Predictions.geojson` (21k grid points with probability properties)
- Boundary layer: `farmers-boundary` (outline layer, missing source file `Farmers_Boundary.geojson`)

**Adding a layer requires 5 changes:**
1. Generate canonical GeoJSON: `python scripts/generate_canonical_geojson.py` (if new theme)
2. Add to `DataLoader.THEMES` in [loader.js](../app/modules/data/loader.js) with file path, color
3. Add to `clusterColors` in [app.js](../app.js) (lines 3-11) with matching theme key and color
4. Add checkbox in [index.html](../index.html): `<input type="checkbox" class="layer-toggle" data-layer="new-layer-id">`
5. Add i18n strings to `i18n.strings.en` and `i18n.strings.ar` in [app.js](../app.js) (lines 13-80)
6. Add property schema to `SCHEMAS` in [property-schemas.js](../app/modules/i18n/property-schemas.js)

**Legacy layer addition** (old dual-file approach, being phased out):
- Call `addGeoJsonLayer('new-layer-id', fromRoot('data/geojson/File.geojson'), '#hexcolor')` in [app.js](../app.js) initialization (~line 2770-2850)

### Key Functions & Patterns
- **`fromRoot(path)`**: Path resolver — checks `PRODUCTION_DATA_URL` (line 167) for data/output paths, else uses local relative URLs
- **`addGeoJsonLayer(id, url, color)`**: **Legacy function** — Adds source + 4 layers per source: base circle (invisible), bubble underlay, icon symbols, clusters + cluster-count (lines 371-550). Sets `pixelOffsets` for visual separation.
- **`addPolygonLayer(id, url, fillColor)`**: Polygon fill + outline layers
- **`bindPolygonInteraction(id)`**: Hover state management for polygons (feature-state)
- **`ensureMapImage(map, key, svg)`**: Converts inline SVG to rasterized map image (called for each icon)
- **Cluster icons**: Dynamic images generated per cluster using `'cluster-{theme}-{count}'` image IDs (not text glyphs) — see cluster icon handler starting ~line 561
- **`staggerDuplicateCoordinates(features)`**: Applies circular offset pattern to prevent overlapping farmer survey points at identical coordinates (lines 560-600)

**New Modular Functions** (canonical architecture):
- **`DataLoader.loadAllThemes()`**: Loads all canonical GeoJSON files with IndexedDB caching (7-day TTL), returns theme objects
- **`DataLoader.getCached(key)`**: Retrieves cached data from IndexedDB, validates version + expiry
- **`StateStore.setState(updates)`**: Immutable state updates with observer notification
- **`StateStore.getThemeData(themeKey)`**: Retrieve specific theme data from state
- **`PropertySchemas.buildDetailsPanel(feature, theme, lang)`**: Maps bilingual properties to display labels (48 properties)
- **`PropertySchemas.getPropertyLabel(theme, key, lang)`**: Get localized label for property key

### Canonical Data Architecture (NEW)
**Stable Feature IDs**: Each feature has deterministic ID: `{theme}_{row}_{coordinateHash8}` (e.g., `Water_2_a3f8b9c1`)

**Bilingual Structure** (single file per theme):
```json
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
```

**Language as Presentation**: Language switching updates UI labels only, **no data reloading**. Property access uses `feature.properties.values[lang][key]`.

**IndexedDB Caching**: 
- Cache key: `canonical-{theme}` (e.g., `canonical-water`)
- Version: `DATA_VERSION` constant in loader.js (increment to bust caches)
- Expiry: 7 days (configurable via `CACHE_EXPIRY_DAYS`)
- Storage: Browser IndexedDB (`ResolveMapDB` database)

### Clustering Strategy
Most point layers use MapLibre's built-in GeoJSON clustering (`cluster: true`, `clusterRadius: 40`, `clusterMaxZoom: 14`). **Exception:** `fire-points-raw` is non-clustered to serve as heatmap data source. Cluster visualization uses circles + dynamic icon images (not text labels).

### I18N (Bilingual Support)
- Language stored in `localStorage.uiLang` (default: `'en'`)
- Central object: `i18n` (~lines 13-164) with nested `strings.en` and `strings.ar`
- Toggle button triggers `i18n.setLang()` which updates DOM (via `i18n.apply()`)
- **RTL switching:** `<html lang="ar" dir="rtl">` set dynamically
- **Legacy dual-file system** (being phased out): Loads separate `Water.geojson` vs `Water_ar.geojson` per language
- **New canonical system**: Single bilingual file, language only affects display via `PropertySchemas`

**Property display workflow**:
1. User clicks feature → `refreshDetailsPanel(featureId, lang)` called
2. Find feature in `StateStore.themes[themeKey].data`
3. Call `PropertySchemas.buildDetailsPanel(feature, themeKey, lang)`
4. Schema maps Arabic property keys (e.g., `'القرية'`) to localized labels
5. Returns array of `{label, value}` pairs for rendering

**Village name transliteration**: English CSVs use phonetic transliteration (e.g., "Mrosti") NOT literal translation ("My lady")

### Data Pipeline & Preprocessing
**Canonical GeoJSON generation (NEW):**
```bash
# Install dependencies
pip install -r requirements.txt

# Generate canonical bilingual GeoJSON (merges AR + EN CSVs)
python scripts/generate_canonical_geojson.py
```

**Output**: Single `{Theme}.canonical.geojson` file with nested bilingual properties
- **Stable IDs**: `{theme}_{row}_{coordinateHash8}` (e.g., `Water_2_a3f8b9c1`)
- **Structure**: `properties: {featureId, theme, values: {ar: {...}, en: {...}}}`
- **Metadata**: Row numbers, coordinate hash, source file references
- **Audit trail**: Generates `data/canonical_audit/{Theme}_canonical_audit.json`

**Legacy CSV → GeoJSON workflow (dual files):**
```bash
# Convert all CSVs to dual GeoJSON files (or specify --theme Energy)
python scripts/csvs_to_geojson_complete.py --all
```

**Key facts about data conversion:**
- **Source**: Arabic CSV files in `data/layers/Arabic/` contain the actual data
- **Output**: 2 identical GeoJSON files per theme: `{Theme}.geojson` and `{Theme}_ar.geojson`
- **Property names**: Both versions use **Arabic property names** (e.g., `القرية`, `مصدر الطاقة`)
- **Translation**: Property names are translated to EN/AR in `app.js` via `i18n.detailsLabels`
- **Language selection**: The appropriate GeoJSON file is loaded based on user's UI language setting

**Column normalization:** Script removes trailing colons and spaces from CSV headers (e.g., `القرية:` → `القرية`).

**Data integrity verification:**
- All CSV columns are preserved in GeoJSON properties
- Coordinates: X (longitude), Y (latitude) from CSV
- Metadata added: `theme`, `coords_source`, `source_file`, `source_row`
- Audit trail: Each generation creates `data/canonical_audit/{Theme}_canonical_audit.json` with source paths, row counts, column lists, and sample IDs

### ML Pipeline (AI Prediction Layers)
**Purpose:** Generate AI prediction heatmap layers from 287 farmer survey responses.

**Complete pipeline workflow:**
```bash
# From project root
cd scripts/ml_pipeline
python run_pipeline.py  # Runs all 4 stages (see below)
```

**Pipeline stages:**
1. **Feature Engineering** (`feature_engineering.py`): Merges 5 theme GeoJSON files → engineers 60+ features → creates 5 binary target variables → outputs `data/ml_prepared_data.csv`
2. **Model Training** (`train_models.py`): Trains 5 RandomForest/XGBoost classifiers with spatial cross-validation → outputs `data/models/*.joblib` + performance report
3. **Spatial Interpolation** (`interpolate_grid.py`): Predicts probabilities at survey points → interpolates to regular grid (default 0.005° ≈ 500m) → outputs `data/geojson/AI_Grid_Predictions.geojson`
4. **Boundary Generation** (`generate_boundary.py`): Computes convex hull from survey points → outputs `data/geojson/Farmers_Boundary.geojson`

**Standalone execution:**
```bash
python feature_engineering.py              # Stage 1 only
python train_models.py xgboost            # Stage 2 with XGBoost
python interpolate_grid.py 0.002          # Stage 3 with fine resolution (200m)
python generate_boundary.py alpha_shape   # Stage 4 with alpha shape
```

**Output validation:**
- Check `data/models/training_report.txt` for model performance (F1-scores, ROC-AUC)
- Verify grid file size: 50-500KB depending on resolution (default ~150KB)
- Test in browser: AI layer toggles should be functional after pipeline completion

**Target variables (5 binary classifications):**
- `target_regen_adoption`: Regenerative agriculture adoption likelihood
- `target_water_risk`: Water scarcity vulnerability
- `target_production_level`: Economic resilience proxy
- `target_labor_shortage`: Agricultural labor availability
- `target_climate_vulnerability`: Climate change impact susceptibility

**Critical dependencies:** pandas, numpy, scikit-learn, xgboost (optional), scipy, shapely, joblib

### AI/ML Layers (Heatmaps)
5 AI prediction layers visualize probabilities using **MapLibre native circle layers** (not deck.gl, despite CDN imports):
- `ai-regen`: Regenerative agriculture adoption (discrete: 0=unlikely red, 1=likely green)
- `ai-water`: Water risk (discrete: 0=low green, 1=high red, inverted logic)
- `ai-econ`: Production capacity (ternary: 0=low red, 1=medium yellow, 2=high green)
- `ai-labor`: Labor availability (SKIPPED - insufficient training data, only 4 positive samples)
- `ai-climate`: Climate resilience proxy (ternary: 0=low blue, 1=medium purple, 2=high teal)

**Implementation:** Function `addAiHeatmapLayer(id, type)` at line ~2620 creates circle layers with categorical color mappings (not probability gradients).

**Data source:** Single shared GeoJSON source `ai-predictions` from `data/geojson/Model_Predictions.geojson` (204 farmer scenarios with discrete classification predictions: "0", "1", "2").

**Status:** AI layers are fully implemented but depend on ML pipeline output. Run `python scripts/ml_pipeline/run_pipeline.py` to generate required files.

### Filtering & Interactivity
- Each layer can have custom filters (village name, crop types, energy source, etc.) defined in `filterUIById` object
- Filters stored in `activeFiltersById` and applied via `applyFilters()` which regenerates GeoJSON data on the fly
- Point interactions: click handlers show details panel on right (popup with feature properties)
- Polygon interactions: hover effects via `feature-state` managed by `bindPolygonInteraction()`

### Deployment & Production Data
**Local dev:** `python -m http.server 8000` (do NOT use `file://` — CORS issues)

**Production:** Set `PRODUCTION_DATA_URL` (line 167) to S3/R2 bucket URL:
```javascript
const PRODUCTION_DATA_URL = 'https://pub-xxx.r2.dev/my-project/';
```
This routes all `data/` and `output/` paths to remote storage while keeping other assets local.

### Important Constraints
- **No file edits without approval:** Data files under `data/` should not be modified without user confirmation
- **No deck.gl overlays:** Despite CDN imports, project uses MapLibre native heatmaps (deck.gl code removed)
- **No build tools:** Static HTML/CSS/JS — no webpack, no transpilation
- **Coordinate system:** WGS84 (EPSG:4326), lat range 33.58-33.80°N, lon 35.40-35.70°E
- **Missing data files**: `AI_Grid_Predictions.geojson` and `Farmers_Boundary.geojson` are referenced in code but not present in repo

### Refactoring Status & Architecture Migration
**Current State**: Hybrid architecture with **both legacy and new canonical systems**

**Completed Components:**
- ✅ Canonical GeoJSON generation script (287 features across 5 themes)
- ✅ IndexedDB caching layer (`DataLoader` module)
- ✅ Immutable state management (`StateStore` module)
- ✅ Bilingual property schemas (48 properties mapped in `PropertySchemas`)
- ✅ Details panel updated to use canonical data

**Legacy Components (Still Active):**
- ⚠️ Main `app.js` still uses `addGeoJsonLayer()` for initialization
- ⚠️ Dual-file loading logic remains (Water.geojson + Water_ar.geojson)
- ⚠️ Language switching triggers layer reloading

**Migration Path** (from REFACTORING_GUIDE.md):
1. Replace `addGeoJsonLayer()` calls with canonical loader
2. Remove dual-file URL logic from layer initialization
3. Update language switching to skip data reload
4. Implement feature-state-based filtering (not layer rebuilding)
5. Remove legacy GeoJSON files after validation

**Critical Pattern for New Features**: Use **canonical architecture** (single bilingual files + PropertySchemas) for any new layers or data additions.

### Quick Reference Examples
**Add point layer (canonical approach - RECOMMENDED):**
```javascript
// 1. Update DataLoader.THEMES in app/modules/data/loader.js
newTheme: {
    id: 'new-theme-points',
    file: 'data/geojson/canonical/NewTheme.canonical.geojson',
    color: '#3498db'
}

// 2. Add property schema in app/modules/i18n/property-schemas.js
newtheme: {
    'القرية': { en: 'Village', ar: 'القرية' },
    'property_key': { en: 'English Label', ar: 'Arabic Label' }
}

// 3. Add i18n strings in app.js
layerNames: { ..., newTheme: 'New Theme' }  // in strings.en
layerNames: { ..., newTheme: 'الثيم الجديد' }  // in strings.ar

// 4. Add checkbox in index.html sidebar
<label><input type="checkbox" class="layer-toggle" data-layer="new-theme-points"> New Theme</label>

// 5. Generate canonical GeoJSON
python scripts/generate_canonical_geojson.py
```

**Add point layer (legacy approach - BEING PHASED OUT):**
```javascript
// 1. In app.js initialization (~line 2600)
addGeoJsonLayer('crop-points', fromRoot('data/geojson/Crops.geojson'), '#3498db');

// 2. In index.html sidebar
<label><input type="checkbox" class="layer-toggle" data-layer="crop-points"> Crops</label>

// 3. Add i18n strings (top of app.js)
layerNames: { ..., crop: 'Crops' }  // in strings.en
layerNames: { ..., crop: 'المحاصيل' }  // in strings.ar

// 4. Add icon to iconSvgs object and call installSidebarIcons()
```

**Add custom filter:**
- Define UI in HTML sidebar with `data-layer` matching layer ID
- Register in `filterUIById` object
- Implement filter logic in `applyFilters()` function

**Access bilingual properties:**
```javascript
// From canonical GeoJSON feature
const lang = StateStore.getLanguage();
const villageName = feature.properties.values[lang]['القرية'];

// Using PropertySchemas
const details = PropertySchemas.buildDetailsPanel(feature, 'water', lang);
// Returns: [{label: 'Village', value: 'Mrosti'}, ...]
```

### Files to Inspect for Changes
- **`app.js`**: Lines 1-100 (i18n strings), 3-11 (clusterColors), 167-190 (fromRoot/path config), 392-580 (addGeoJsonLayer), 580-625 (addCanonicalLayer), 625-665 (staggerDuplicateCoordinates), 2620-2700 (AI layers), 2879-2980 (loadAllData), 2067-2165 (refreshDetailsPanel)
- **`app/modules/data/loader.js`**: Lines 26-60 (THEMES configuration), 68-106 (IndexedDB init), 108-157 (cache get/set), 246-290 (loadAllThemes with progress callback)
- **`app/modules/state/store.js`**: Lines 18-51 (INITIAL_STATE structure), 66-83 (setState immutable updates), 185-230 (theme data getters), 265-303 (state persistence)
- **`app/modules/i18n/property-schemas.js`**: Lines 19-422 (SCHEMAS object with 48 bilingual property mappings), 292-372 (buildDetailsPanel function)
- **`index.html`**: Lines 40-110 (sidebar controls with data-layer attributes), 129-140 (script loading order)
- **`scripts/generate_canonical_geojson.py`**: Lines 24-47 (THEMES config), 52-73 (generate_stable_id), 79-108 (merge_ar_en_row), 161-241 (generate_canonical_geojson main function)
- **`scripts/ml_pipeline/run_pipeline.py`**: Lines 32-97 (pipeline orchestration), 100-140 (stage execution methods)
- **`scripts/csvs_to_geojson_complete.py`**: Lines 25-43 (legacy THEMES), 167-247 (column normalization and conversion logic)

### Testing Checklist
1. Test local: `python -m http.server 8000` → `http://localhost:8000/`
2. Toggle layers in sidebar — verify visibility and clustering
3. Switch language (AR ↔ EN) — check RTL layout + layer source updates
4. Click features — details panel should populate
5. Hover polygons — opacity/color changes via feature-state
6. Test filters — layer data should update dynamically

### Critical Hotspots & Common Pitfalls
**⚠️ THEMES Configuration Synchronization**
- THEMES defined in 3+ locations that MUST stay synchronized:
  - `app/modules/data/loader.js` (lines 26-60) - file paths and colors
  - `scripts/generate_canonical_geojson.py` (lines 24-45) - CSV source paths
  - `app.js` clusterColors (lines 3-11) - color mappings per theme
- Adding a theme requires updating all three + PropertySchemas + i18n strings

**⚠️ Arabic/English CSV Row Alignment**
- `generate_canonical_geojson.py` merges AR/EN CSVs by row index using `enumerate(zip(df_ar, df_en))`
- **CRITICAL**: Row order must match exactly between Arabic and English files
- Mismatch causes mismatched bilingual properties (Arabic village → English village different village)
- Script validates row counts but NOT row content alignment

**⚠️ Coordinate Staggering Algorithm**
- `staggerDuplicateCoordinates()` applies circular offset to prevent overlapping points at same coordinates
- Magic numbers: `offsetDistance = 0.0002` (~22 meters), radius increases for >8 duplicates
- Applied to farmers survey data where multiple responses share same village coordinates
- Changes display coordinates but preserves original in properties

**⚠️ IndexedDB Cache Invalidation**
- Cache key format: `canonical-{theme}` or `{themeKey}_{filePath}`
- Version controlled by `DATA_VERSION` in loader.js (currently '2.1.0')
- **To force reload**: Increment DATA_VERSION or clear browser storage
- Cache expires after 7 days automatically

**⚠️ Property Key Brittleness**
- PropertySchemas maps 48+ property keys (mix of Arabic text, numbered keys like `_3`, `_4`)
- Keys come from CSV column headers after normalization (strips `: ` suffixes)
- Adding/renaming CSV columns requires updating PropertySchemas.SCHEMAS
- Missing schema entry causes property to not display in details panel

**⚠️ Feature ID Stability**
- Canonical features use deterministic IDs: `{theme}_{row}_{coordinateHash8}`
- ID changes if: row order changes, coordinates change, or theme name changes
- Used for feature-state, details panel lookup, and caching
- Changing IDs breaks saved selections and cached references

**⚠️ Legacy vs Canonical Code Paths**
- Both `addGeoJsonLayer()` (legacy) and `addCanonicalLayer()` (new) coexist
- Language switching still has dual-file loading remnants (to be removed)
- When debugging, check which path is active: legacy uses URL loading, canonical uses direct data
- Prefer canonical architecture for all new development

### Error Handling Patterns
- **JavaScript**: try/catch with graceful degradation, console.warn for non-critical errors
- **Python**: ValidationError for data mismatches, FileNotFoundError with helpful messages
- **Caching**: Silent failures with fallback to network fetch
- **GeoJSON validation**: Checks FeatureCollection type and features array existence in loader.js

### Development Workflow Tips
```bash
# Start development server (REQUIRED - file:// causes CORS issues)
python -m http.server 8000

# Regenerate canonical GeoJSON after CSV changes
python scripts/generate_canonical_geojson.py

# Check data integrity
cat data/canonical_audit/Water_canonical_audit.json  # View audit trail

# Run ML pipeline for AI layers
cd scripts/ml_pipeline && python run_pipeline.py

# Clear browser cache if seeing stale data
# 1. Open DevTools → Application → IndexedDB → ResolveMapDB → Delete
# 2. Or increment DATA_VERSION in app/modules/data/loader.js
```

### Architecture Decision Records
**Why canonical bilingual architecture?**
- Eliminates duplicate data loading (was 2 files per theme)
- Language switch is instant (no network request)
- Single source of truth for feature data
- Simplifies state management

**Why IndexedDB caching?**
- GitHub Pages has no server-side caching
- Browser cache unreliable for large GeoJSON files
- Version-based invalidation prevents stale data
- 7-day expiry balances freshness vs performance

**Why coordinate staggering?**
- Multiple farmers in same village share exact coordinates
- Overlapping points invisible on map (only top one clickable)
- Circular offset pattern maintains visual clustering
- Applied at render time (original coordinates preserved)

**Why hybrid architecture exists?**
- Incremental migration from legacy dual-file system
- Risk mitigation: new canonical code validated before removing old
- Fire and farmers layers still use legacy path (static data)
- Full migration blocked on comprehensive testing
