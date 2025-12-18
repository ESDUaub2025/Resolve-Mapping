# App.js Refactoring Integration Guide

## Overview
This document outlines the integration of new modules into app.js for the canonical bilingual architecture.

## Key Changes

### 1. Remove Dual-File Loading
**OLD:** Separate AR/EN files with language-based URL swapping
```javascript
addGeoJsonLayer('water-points', fromRoot('data/geojson/Water.geojson'), '#1abc9c');
// On language switch: reload with Water_ar.geojson
```

**NEW:** Single canonical file loaded once
```javascript
// Load canonical data via DataLoader module
const themes = await DataLoader.loadAllThemes();
StateStore.setState({ themes, themesLoaded: true });
addCanonicalLayer('water-points', themes.water);
```

### 2. Use Stable Feature IDs
**OLD:** `generateId: true` creates ephemeral IDs
```javascript
map.addSource(id, { 
    type: 'geojson', 
    data: url, 
    generateId: true,  // ← EPHEMERAL
    cluster: true 
});
```

**NEW:** Use stable IDs from feature.id
```javascript
map.addSource(id, { 
    type: 'geojson', 
    data: geojson,
    promoteId: 'featureId',  // ← STABLE from canonical data
    cluster: true 
});
```

### 3. Language as Presentation
**OLD:** Reload layers on language switch
```javascript
i18n.setLang(next) {
    this.lang = next;
    this.apply();
    // Forces reload of all layers with new URLs
    reloadAllLayers();
}
```

**NEW:** Update display only, no data reload
```javascript
function setLanguage(lang) {
    StateStore.setLanguage(lang);
    updateUILabels();
    updateDetailsPanel();  // Refresh details if open
    // NO DATA RELOADING
}
```

### 4. Filter Without Rebuilding
**OLD:** Replace GeoJSON data on filter
```javascript
function applyFilters() {
    const filtered = originalData.features.filter(...);
    map.getSource(id).setData({ type: 'FeatureCollection', features: filtered });
    // ← LOSES CLUSTER STATE
}
```

**NEW:** Use feature-state for visibility
```javascript
function applyFilters(themeKey, filters) {
    const theme = StateStore.getThemeData(themeKey);
    const lang = StateStore.getLanguage();
    
    theme.data.features.forEach(feature => {
        const matches = FilterEngine.applyFilters([feature], filters, lang).length > 0;
        map.setFeatureState(
            { source: theme.id, id: feature.properties.featureId },
            { visible: matches }
        );
    });
    
    // Update paint property to hide non-matching features
    updateLayerFilters(theme.id);
}
```

### 5. Property Display
**OLD:** Direct property access with hardcoded keys
```javascript
const village = feature.properties['القرية'];  // ← Language-specific
```

**NEW:** Schema-based property access
```javascript
const lang = StateStore.getLanguage();
const village = PropertySchemas.getPropertyValue(feature, 'القرية', lang);
const label = PropertySchemas.getPropertyLabel('water', 'القرية', lang);
```

## Integration Steps

### Step 1: Initialize New Systems
Add after map initialization:
```javascript
maplibregl.Map.on('load', async () => {
    // Initialize state management
    StateStore.restoreState();
    
    // Initialize data loader with IndexedDB
    await DataLoader.init();
    
    // Show progress during load
    const themes = await DataLoader.loadAllThemes((loaded, total, key) => {
        console.log(`Loading ${loaded}/${total}: ${key}`);
    });
    
    // Store in state
    StateStore.setState({ themes, themesLoaded: true });
    
    // Load static layers
    const staticLayers = await DataLoader.loadStaticLayers();
    StateStore.setState({ staticLayers });
    
    // Add canonical layers to map
    addAllCanonicalLayers();
    
    // Subscribe to state changes
    StateStore.subscribe(onStateChange);
});
```

### Step 2: Replace addGeoJsonLayer
Create new function for canonical data:
```javascript
function addCanonicalLayer(layerId, themeData) {
    const { id, color, data } = themeData;
    
    // Add source with stable IDs
    map.addSource(id, {
        type: 'geojson',
        data: data,
        promoteId: 'featureId',  // Use stable IDs from data
        cluster: true,
        clusterRadius: 40,
        clusterMaxZoom: 14
    });
    
    // Add layers (same visualization logic, but use stable IDs)
    // ... existing layer creation code ...
}
```

### Step 3: Update Language Toggle
Replace i18n.setLang with:
```javascript
function toggleLanguage() {
    const currentLang = StateStore.getLanguage();
    const newLang = currentLang === 'en' ? 'ar' : 'en';
    
    // Update state (triggers UI updates via observers)
    StateStore.setLanguage(newLang);
    
    // Update UI labels
    updateUILabels(newLang);
    
    // Update details panel if open
    const selectedId = StateStore.getState().selectedFeatureId;
    if (selectedId) {
        refreshDetailsPanel(selectedId, newLang);
    }
    
    // NO DATA RELOADING!
}
```

### Step 4: Update Filter Functions
Replace filter logic with FilterEngine:
```javascript
function applyFiltersForLayer(layerId) {
    const theme = getThemeForLayer(layerId);
    if (!theme) return;
    
    const filters = StateStore.getFilters(theme.key);
    const lang = StateStore.getLanguage();
    
    // Use FilterEngine for two-stage filtering
    const allFeatures = theme.data.features;
    const matching = FilterEngine.applyFilters(allFeatures, filters, lang);
    const matchingIds = new Set(matching.map(f => f.properties.featureId));
    
    // Update feature states (not data replacement)
    allFeatures.forEach(feature => {
        const featureId = feature.properties.featureId;
        map.setFeatureState(
            { source: theme.id, id: featureId },
            { filtered: matchingIds.has(featureId) }
        );
    });
    
    // Update layer paint to hide filtered features
    updateLayerPaintForFilters(layerId);
}
```

### Step 5: Update Details Panel
Use PropertySchemas for display:
```javascript
function showDetailsPanel(featureId) {
    const theme = findThemeByFeatureId(featureId);
    if (!theme) return;
    
    const feature = theme.data.features.find(f => f.properties.featureId === featureId);
    if (!feature) return;
    
    const lang = StateStore.getLanguage();
    const details = PropertySchemas.buildDetailsPanel(feature, theme.key, lang);
    
    let html = '<div class="details-content">';
    details.forEach(({ label, value }) => {
        html += `
            <div class="detail-row">
                <span class="detail-label">${label}:</span>
                <span class="detail-value">${value}</span>
            </div>
        `;
    });
    html += '</div>';
    
    document.getElementById('details-panel').innerHTML = html;
    StateStore.selectFeature(featureId);
}
```

## State Observer Pattern

Subscribe to state changes for reactive updates:
```javascript
StateStore.subscribe((prevState, newState) => {
    // Language change
    if (prevState.language !== newState.language) {
        updateUILabels(newState.language);
        if (newState.selectedFeatureId) {
            refreshDetailsPanel(newState.selectedFeatureId, newState.language);
        }
    }
    
    // Layer visibility change
    if (prevState.visibleLayers !== newState.visibleLayers) {
        updateMapLayerVisibility();
    }
    
    // Filter change
    if (prevState.filters !== newState.filters) {
        Object.keys(newState.filters).forEach(theme => {
            if (prevState.filters[theme] !== newState.filters[theme]) {
                applyFiltersForLayer(getLayerIdForTheme(theme));
            }
        });
    }
});
```

## File Organization

```
app/
  modules/
    data/
      loader.js          ✓ Created
    state/
      store.js           ✓ Created
    filters/
      filter-engine.js   ✓ Created
    i18n/
      property-schemas.js ✓ Created
app.js                    ← Needs integration
index.html                ✓ Updated (script includes)
```

## Testing Checklist

1. ✓ Canonical GeoJSON files generated (287 features)
2. ✓ Modules loaded before app.js
3. ⏳ Language toggle updates UI only (no data reload)
4. ⏳ Filters use feature-state (maintain cluster membership)
5. ⏳ Details panel uses PropertySchemas
6. ⏳ Feature IDs stable across operations
7. ⏳ IndexedDB caching works
8. ⏳ State persists across page reloads

## Next Actions

1. Backup original app.js
2. Integrate DataLoader initialization
3. Replace addGeoJsonLayer with addCanonicalLayer
4. Update filter functions to use FilterEngine
5. Update language toggle to use StateStore
6. Update details panel to use PropertySchemas
7. Test incrementally after each change
