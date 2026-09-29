/**
 * RESOLVE Map — Single Source of Truth
 * ======================================
 * Every theme color, layer ID, file path, and i18n key is defined HERE.
 * All other files (app.js, loader.js, Python scripts) read from this.
 *
 * To add a new theme:   add an entry to THEMES
 * To add a static layer: add an entry to STATIC_LAYERS
 * To add an AI layer:    add an entry to AI_LAYERS
 * Then run:  python scripts/validate_data.py
 */
(function () {
    'use strict';

    const MANIFEST = {

        // ── Version & caching ───────────────────────────────────────
        DATA_VERSION: '3.0.0',
        CACHE_EXPIRY_DAYS: 7,
        DB_NAME: 'ResolveMapDB',
        DB_VERSION: 1,
        DB_STORE: 'geojsonCache',

        // ── Production data URL (null = local) ──────────────────────
        // Set to e.g. 'https://pub-xxx.r2.dev/my-project/' for CDN
        PRODUCTION_DATA_URL: null,

        // ── Map defaults ────────────────────────────────────────────
        MAP_CENTER: [35.55, 33.72],   // [lng, lat]
        MAP_ZOOM: 10,
        MAP_MAX_ZOOM: 18,

        // ── Canonical survey themes ─────────────────────────────────
        // Each theme becomes a clustered point layer on the map.
        // Withdrawn 2026-09-29 (Stage 0 containment): survey-derived layers exposed
        // respondent-level records and small-village aggregates. They return as
        // disclosure-controlled aggregates in Stage 5 of the refactoring plan.
        THEMES: {},

        // ── Static layers (non-canonical) ───────────────────────────
        STATIC_LAYERS: {
            fire: {
                layerId: 'fire-points',
                rawLayerId: 'fire-points-raw',   // non-clustered for heatmap
                file: 'data/geojson/fire.geojson',
                color: '#e74c3c',
                pixelOffset: [0, 14],
                i18n: { en: 'Fire points', ar: 'نقاط الحرائق' },
                icon: 'fire'
            },
            preservations: {
                layerId: 'preservations-poly',
                file: 'data/geojson/Preservations.geojson',
                color: '#2ecc71',
                type: 'polygon',
                i18n: { en: 'Preservations', ar: 'المحميات' },
                icon: 'preservations'
            }
        },

        // ── AI prediction layers ────────────────────────────────────
        // Withdrawn 2026-09-29: models were not validated out-of-sample (see audit plan).
        AI_LAYERS: {},

        // ── Heatmap layer (special) ─────────────────────────────────
        HEATMAP: {
            layerId: 'fire-heatmap',
            sourceLayerId: 'fire-points-raw',
            i18n: { en: 'Fire Heatmap', ar: 'كثافة الحرائق' },
            icon: 'fire'
        },

        // AI_SOURCE and BOUNDARY withdrawn with the AI layers.
        AI_SOURCE: null,
        BOUNDARY: null
    };

    // ── Helper: build lookup maps from manifest ─────────────────
    // layerId → themeKey  (e.g. 'water-points' → 'water')
    MANIFEST._layerToTheme = {};
    for (const [key, cfg] of Object.entries(MANIFEST.THEMES)) {
        MANIFEST._layerToTheme[cfg.layerId] = key;
    }

    // themeKey → color  (includes static + ai)
    MANIFEST._colors = {};
    for (const [key, cfg] of Object.entries(MANIFEST.THEMES)) {
        MANIFEST._colors[key] = cfg.color;
    }
    for (const [key, cfg] of Object.entries(MANIFEST.STATIC_LAYERS)) {
        MANIFEST._colors[key] = cfg.color;
    }

    // Freeze after helpers are attached
    Object.freeze(MANIFEST);

    // Expose globally (consumed by loader.js, store.js, app.js)
    window.MANIFEST = MANIFEST;

})();
